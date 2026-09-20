import json
import boto3
import os

sns = boto3.client('sns')
TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])

        alarm_name = message.get('AlarmName', 'Unknown')
        alarm_description = message.get('AlarmDescription', '')
        state = message.get('NewStateValue', '')
        reason = message.get('NewStateReason', '')
        timestamp = message.get('StateChangeTime', '')

        formatted = (
            f"SECURITY ALERT\n\n"
            f"Alarm:       {alarm_name}\n"
            f"Description: {alarm_description}\n"
            f"State:       {state}\n"
            f"Time:        {timestamp}\n\n"
            f"Details: {reason}\n\n"
            f"Check CloudTrail for the full event details."
        )

        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject=f"[AWS Security Alert] {alarm_name}",
            Message=formatted
        )
