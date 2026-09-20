import json
import boto3
import os
import uuid
from datetime import datetime, timezone

sqs = boto3.client('sqs')
QUEUE_URL = os.environ['QUEUE_URL']
REQUIRED_FIELDS = ['sensor_id', 'temperature']

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
    except (json.JSONDecodeError, TypeError):
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid JSON'})}

    for field in REQUIRED_FIELDS:
        if field not in body:
            return {'statusCode': 400, 'body': json.dumps({'error': f'Missing field: {field}'})}

    message = {
        'sensor_id': body['sensor_id'],
        'temperature': float(body['temperature']),
        'humidity': body.get('humidity'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'message_id': str(uuid.uuid4())
    }

    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'queued', 'message_id': message['message_id']})
    }
