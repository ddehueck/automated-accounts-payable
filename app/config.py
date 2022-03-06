from pydantic import BaseSettings


class GlobalConfig(BaseSettings):
    aws_access_key: str = None
    aws_secret_key: str = None
    aws_region_name: str = "us-east-1"
    in_deployment: bool = False
    session_secret: str = None
    base_domain: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = False


config = GlobalConfig()
