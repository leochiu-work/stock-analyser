from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    price_service_base_url: str = "http://stock-price-service:8000"
    aws_endpoint_url: str = "http://localstack:4566"
    aws_region: str = "us-east-1"
    sqs_prices_fetched_queue_url: str = "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/stock-ta-service-queue"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
