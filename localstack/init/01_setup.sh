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

echo "LocalStack SNS/SQS setup complete"
