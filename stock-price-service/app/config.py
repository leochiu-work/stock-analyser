from datetime import date

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    default_start_date: date = date(2020, 1, 1)
    aws_endpoint_url: str = "http://localstack:4566"
    aws_region: str = "us-east-1"
    sqs_new_symbol_queue_url: str = "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/stock-price-new-symbol-queue"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
