"""
SQS worker for stock-price-service.

Polls the stock-price-service-queue and handles NEW_SYMBOL_ADDED events.
Run with: uv run python worker.py
"""

import json
import logging
from datetime import date, timedelta

import boto3

from app.config import settings
from app.database import SessionLocal
from app.repositories.stock_price_repository import StockPriceRepository
from app.repositories.ticker_repository import TickerRepository
from app.services.fetch_service import FetchService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

POLL_WAIT_SECONDS = 20  # long-polling interval


def _save_prices_to_s3(symbol: str, records: list) -> str:
    s3_key = f"prices/{symbol}/{date.today().isoformat()}.json"
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.aws_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    s3.put_object(
        Bucket=settings.s3_prices_bucket,
        Key=s3_key,
        Body=json.dumps(records, default=str),
        ContentType="application/json",
    )
    logger.info("Saved %d records to s3://%s/%s", len(records), settings.s3_prices_bucket, s3_key)
    return s3_key


def _publish_prices_fetched(symbol: str, s3_bucket: str, s3_key: str) -> None:
    if not settings.sns_prices_fetched_topic_arn:
        return
    try:
        sns = boto3.client(
            "sns",
            endpoint_url=settings.aws_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
        sns.publish(
            TopicArn=settings.sns_prices_fetched_topic_arn,
            Message=json.dumps({
                "event": "PRICES_FETCHED",
                "symbol": symbol,
                "s3_bucket": s3_bucket,
                "s3_key": s3_key,
            }),
        )
        logger.info("Published PRICES_FETCHED event for %s", symbol)
    except Exception:
        logger.warning("Failed to publish PRICES_FETCHED event for %s", symbol, exc_info=True)


def handle_new_symbol_added(symbol: str) -> None:
    start_date = date.today() - timedelta(days=5 * 365)
    end_date = date.today()
    db = SessionLocal()
    try:
        TickerRepository(db).get_or_create(symbol)
        records = FetchService().fetch_prices(symbol, start_date, end_date)
        StockPriceRepository(db).upsert_many(records)
        db.commit()
        logger.info("Upserted %d records for %s", len(records), symbol)
        try:
            s3_key = _save_prices_to_s3(symbol, records)
        except Exception:
            logger.warning("Failed to save prices to S3 for %s — skipping publish", symbol, exc_info=True)
            return
        _publish_prices_fetched(symbol, settings.s3_prices_bucket, s3_key)
    except Exception:
        logger.exception("Failed to fetch/save prices for %s", symbol)
    finally:
        db.close()


def process_message(message: dict) -> None:
    try:
        # SNS wraps the original payload inside Message
        outer = json.loads(message["Body"])
        payload = json.loads(outer["Message"])
        event = payload.get("event")

        if event == "NEW_SYMBOL_ADDED":
            handle_new_symbol_added(payload["symbol"])
        else:
            logger.warning("Unknown event type: %s", event)
    except Exception:
        logger.exception("Failed to process message: %s", message.get("MessageId"))


def run() -> None:
    sqs = boto3.client(
        "sqs",
        endpoint_url=settings.aws_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    queue_url = settings.sqs_new_symbol_queue_url
    logger.info("Starting worker, polling %s", queue_url)

    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=POLL_WAIT_SECONDS,
        )
        messages = response.get("Messages", [])
        for msg in messages:
            process_message(msg)
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])


if __name__ == "__main__":
    run()
