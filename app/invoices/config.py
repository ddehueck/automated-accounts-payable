from pydantic import BaseSettings


class InvoiceSettings(BaseSettings):
    s3_bucket_name: str = "aap-invoice-images"

    class Config:
        env_file = ".env"
        case_sensitive = False


config = InvoiceSettings()
