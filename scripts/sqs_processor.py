import boto3
import json

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    for record in event['Records']:
        # Process the SQS message
        message_body = record['body']
        print(f"Received message: {message_body}")

        # Invoke the data-pipeline-lambda function
        response = lambda_client.invoke(
            FunctionName='data-pipeline-lambda',
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps({"message": message_body})
        )
        print(f"Invoked data-pipeline-lambda: {response}")