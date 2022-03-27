import io
import time

import boto3
from loguru import logger as log

from app.config import config as global_config

from .config import config

s3_client = boto3.client(
    "s3",
    aws_access_key_id=global_config.aws_access_key,
    aws_secret_access_key=global_config.aws_secret_key,
    region_name=global_config.aws_region_name,
)


def get_image_uri(image_name: str, extension: str):
    return f"https://{config.s3_bucket_name}.s3.amazonaws.com/{image_name}.{extension}"


def upload_image_obj(object: bytes, image_name: str, extension: str) -> str:
    start = time.time()
    s3_client.upload_fileobj(io.BytesIO(object), config.s3_bucket_name, f"{image_name}.{extension}")
    log.debug(f"Uploaded image to s3 in {round(time.time() - start, ndigits=2)}")
    return get_image_uri(image_name, extension)
