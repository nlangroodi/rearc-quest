from aws_sync import main as aws_sync_main
from datausa_api_fetch import fetch_data

def lambda_handler(event, context):
    print("Starting AWS Sync...")
    aws_sync_main()

    print("Starting DataUSA API Fetch...")
    fetch_data()

    print("Pipeline completed successfully.")