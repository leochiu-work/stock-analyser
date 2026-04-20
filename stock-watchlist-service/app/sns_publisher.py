import json
import logging

import boto3

from app.config import settings

logger = logging.getLogger(__name__)


def publish_new_symbol_added(symbol: str) -> None:
    sns = boto3.client(
        "sns",
        endpoint_url=settings.aws_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    sns.publish(
        TopicArn=settings.sns_new_symbol_topic_arn,
        Message=json.dumps({"event": "NEW_SYMBOL_ADDED", "symbol": symbol}),
        Subject="NEW_SYMBOL_ADDED",
    )
    logger.info("Published NEW_SYMBOL_ADDED for %s", symbol)
