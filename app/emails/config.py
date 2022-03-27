from pydantic import BaseModel, BaseSettings


class EmailConfig(BaseSettings):
    sendgrid_api_key: str = None

    class Config:
        env_file = ".env"


config = EmailConfig()
