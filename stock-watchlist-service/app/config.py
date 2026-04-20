from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    aws_endpoint_url: str = "http://localstack:4566"
    aws_region: str = "us-east-1"
    sns_new_symbol_topic_arn: str = "arn:aws:sns:us-east-1:000000000000:new-symbol-added"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
