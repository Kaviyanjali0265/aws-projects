import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE_NAME = os.environ['TABLE_NAME']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
TEMP_THRESHOLD = float(os.environ.get('TEMP_THRESHOLD', '35'))

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    for record in event['Records']:
        message = json.loads(record['body'])

        table.put_item(Item={
            'sensor_id': message['sensor_id'],
            'timestamp': message['timestamp'],
            'temperature': str(message['temperature']),
            'humidity': str(message.get('humidity', '')),
            'message_id': message['message_id']
        })

        if message['temperature'] > TEMP_THRESHOLD:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"[IoT Alert] High Temperature from {message['sensor_id']}",
                Message=(
                    f"High temperature detected!\n\n"
                    f"Sensor:      {message['sensor_id']}\n"
                    f"Temperature: {message['temperature']}C\n"
                    f"Threshold:   {TEMP_THRESHOLD}C\n"
                    f"Time:        {message['timestamp']}"
                )
            )
