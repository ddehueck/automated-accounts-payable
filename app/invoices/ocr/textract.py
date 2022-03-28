from typing import Any, Dict

import boto3
from loguru import logger as log
from result import Err, Ok, Result

from app.config import config as global_config
from app.invoices.ocr.models import RawInvoiceBody

textract_client = boto3.client(
    "textract",
    aws_access_key_id=global_config.aws_access_key,
    aws_secret_access_key=global_config.aws_secret_key,
    region_name=global_config.aws_region_name,
)


class InvoiceImageProcessor:
    def __init__(self, client: Any) -> None:
        self._client = client

    def apply(self, image_data: bytes) -> Result[RawInvoiceBody, str]:
        res = self._client.analyze_expense(Document={"Bytes": image_data})

        status_code = res["ResponseMetadata"]["HTTPStatusCode"]
        if status_code != 200:
            msg = f"Failed to parse with status code {status_code}"
            log.exception(msg)
            return Err(msg)

        # Only parse one document at a time
        summary_fields = res["ExpenseDocuments"][0]["SummaryFields"]

        invoice_body = self._parse_texract_summary_fields(summary_fields)
        if not invoice_body.is_complete_parse():
            log.warning(f"Not a complete parse: \n{invoice_body.dict()}\n \n{res}")

        return Ok(invoice_body)

    def _parse_texract_summary_fields(self, fields: Dict) -> RawInvoiceBody:
        """
        Args:
            fields (Dict): Example - {
               "Type":{
                  "Text":"VENDOR_NAME",
                  "Confidence":99.35572814941406
               },
               "ValueDetection":{
                  "Text":"ACME Industries",
                  "Geometry":{<bounding box, etc.>},
                  "Confidence":99.34666442871094
               },
               "PageNumber":1
            }
        """
        dict_to_parse = {f["Type"]["Text"]: f["ValueDetection"]["Text"] for f in fields}
        return RawInvoiceBody(**dict_to_parse)
