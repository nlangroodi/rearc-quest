import requests
import boto3
import json

bucket_name = "rearc-quest-bls"

if __name__ == "__main__":

    response = requests.get(f"https://honolulu-api.datausa.io/tesseract/data.jsonrecords?cube=acs_yg_total_population_1&drilldowns=Year%2CNation&locale=en&measures=Population")
    s3 = boto3.client("s3")
    
    if response.status_code == 200:
        formatted_json = json.dumps(response.json(), indent=4)
        s3.put_object(
            Bucket=bucket_name,
            Key="datausa-results.json",
            Body=formatted_json,
            ContentType= "application/json"
        )
    else:
        print(f'Unsuccessful API call, returned with status {response.status_code}')
        raise