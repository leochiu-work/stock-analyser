from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    FINNHUB_API_KEY: str
    AWS_ENDPOINT_URL: str = "http://localstack:4566"
    AWS_REGION: str = "us-east-1"
    SQS_NEW_SYMBOL_QUEUE_URL: str = "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/stock-news-service-queue"

    model_config = {"env_file": ".env"}


settings = Settings()
