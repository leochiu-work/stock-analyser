#!/bin/bash
set -e

echo "Creating SNS topic: stock-events"
TOPIC_ARN=$(awslocal sns create-topic --name stock-events --query TopicArn --output text)
echo "Topic ARN: $TOPIC_ARN"

echo "Creating SQS queue: stock-events-queue"
QUEUE_URL=$(awslocal sqs create-queue --queue-name stock-events-queue --query QueueUrl --output text)
echo "Queue URL: $QUEUE_URL"

QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names QueueArn \
  --query Attributes.QueueArn \
  --output text)

echo "Subscribing queue to SNS topic"
awslocal sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$QUEUE_ARN"

echo "Creating SNS topic: new-symbol-added"
NEW_SYMBOL_TOPIC_ARN=$(awslocal sns create-topic --name new-symbol-added --query TopicArn --output text)
echo "Topic ARN: $NEW_SYMBOL_TOPIC_ARN"

echo "Creating SQS queue: stock-news-new-symbol-queue"
NEWS_QUEUE_URL=$(awslocal sqs create-queue --queue-name stock-news-new-symbol-queue --query QueueUrl --output text)
echo "Queue URL: $NEWS_QUEUE_URL"

echo "Creating SQS queue: stock-price-new-symbol-queue"
PRICE_QUEUE_URL=$(awslocal sqs create-queue --queue-name stock-price-new-symbol-queue --query QueueUrl --output text)
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

echo "LocalStack SNS/SQS setup complete"
