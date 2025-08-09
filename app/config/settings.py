from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    env: str = "dev"
    s3_faq_bucket: str = "pelvis-therapy-faq-dev"
    dynamodb_table: str = "pelvis-therapy-state-dev"
    owner_phone_e164: str = ""  # +593...
    google_sa_secret_name: str = "pelvis/google/service-account"  # Secrets Manager

    class Config:
        env_file = ".env"


settings = Settings()
