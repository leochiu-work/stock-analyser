"""
SQS worker for stock-ta-service.

Polls the stock-ta-service-queue and handles PRICES_FETCHED events.
Run with: uv run python worker.py
"""

import json
import logging

import boto3

from app.config import settings
from app.database import SessionLocal
from app.services.ta_service import compute_and_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

POLL_WAIT_SECONDS = 20


def process_message(message: dict) -> None:
    try:
        outer = json.loads(message["Body"])
        payload = json.loads(outer["Message"])
        event = payload.get("event")

        if event == "PRICES_FETCHED":
            symbol = payload["symbol"]
            db = SessionLocal()
            try:
                count = compute_and_store(db, symbol)
                logger.info("Computed and stored %d TA rows for %s", count, symbol)
            finally:
                db.close()
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
    queue_url = settings.sqs_prices_fetched_queue_url
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
