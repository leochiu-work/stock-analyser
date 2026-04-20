"""
SQS worker for stock-price-service.

Polls the stock-price-new-symbol-queue and handles NEW_SYMBOL_ADDED events.
Run with: uv run python worker.py
"""

import json
import logging

import boto3

from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

POLL_WAIT_SECONDS = 20  # long-polling interval


def handle_new_symbol_added(symbol: str) -> None:
    # TODO: trigger price fetch for the newly added symbol
    logger.info("Received NEW_SYMBOL_ADDED for %s — TODO: implement action", symbol)


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
