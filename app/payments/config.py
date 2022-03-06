from pydantic import BaseSettings


class PaymentSettings(BaseSettings):
    stripe_publishable_key: str = None
    stripe_secret_key: str = None
    stripe_webhook_secret: str = None

    class Config:
        env_file = ".env"
        case_sensitive = False


config = PaymentSettings()
