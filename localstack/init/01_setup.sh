#!/bin/bash
set -e

echo "Creating SNS topic: new-symbol-added"
NEW_SYMBOL_TOPIC_ARN=$(awslocal sns create-topic --name new-symbol-added --query TopicArn --output text)
echo "Topic ARN: $NEW_SYMBOL_TOPIC_ARN"

echo "Creating SQS queue: stock-news-service-queue"
NEWS_QUEUE_URL=$(awslocal sqs create-queue --queue-name stock-news-service-queue --query QueueUrl --output text)
echo "Queue URL: $NEWS_QUEUE_URL"

echo "Creating SQS queue: stock-price-service-queue"
PRICE_QUEUE_URL=$(awslocal sqs create-queue --queue-name stock-price-service-queue --query QueueUrl --output text)
echo "Queue URL: $PRICE_QUEUE_URL"

NEWS_QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "$NEWS_QUEUE_URL" \
  --attribute-names QueueArn \
  --query Attributes.QueueArn \
  --output text)

PRICE_QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "$PRICE_QUEUE_URL" \
  --attribute-names QueueArn \
  --query Attributes.QueueArn \
  --output text)

echo "Subscribing stock-news queue to new-symbol-added topic"
awslocal sns subscribe \
  --topic-arn "$NEW_SYMBOL_TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$NEWS_QUEUE_ARN"

echo "Subscribing stock-price queue to new-symbol-added topic"
awslocal sns subscribe \
  --topic-arn "$NEW_SYMBOL_TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$PRICE_QUEUE_ARN"

echo "Creating SNS topic: prices-fetched"
PRICES_FETCHED_TOPIC_ARN=$(awslocal sns create-topic --name prices-fetched --query TopicArn --output text)
echo "Topic ARN: $PRICES_FETCHED_TOPIC_ARN"

echo "Creating SQS queue: stock-ta-service-queue"
TA_QUEUE_URL=$(awslocal sqs create-queue --queue-name stock-ta-service-queue --query QueueUrl --output text)
echo "Queue URL: $TA_QUEUE_URL"

TA_QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "$TA_QUEUE_URL" \
  --attribute-names QueueArn \
  --query Attributes.QueueArn \
  --output text)

echo "Subscribing stock-ta queue to prices-fetched topic"
awslocal sns subscribe \
  --topic-arn "$PRICES_FETCHED_TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$TA_QUEUE_ARN"

echo "LocalStack SNS/SQS setup complete"
