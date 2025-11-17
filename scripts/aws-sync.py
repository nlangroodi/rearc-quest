import boto3
import hashlib
import requests
from bs4 import BeautifulSoup

# define variables
source_url = "https://download.bls.gov/pub/time.series/pr/"
source_headers = {
            'Accept': '*/*', 
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15'
          }
bucket_name = "rearc-quest-bls"

def get_remote_files(source_url, source_headers):
    response = requests.get(source_url, headers=source_headers)
    soup = BeautifulSoup(response.text, "html.parser")
    files = []

    for link in soup.find_all("a"):
        file_name = link["href"]
        if 'pr/' in file_name:
            files.append(file_name.split('/')[-1])
    return files

def file_checksum(content):
    return hashlib.md5(content).hexdigest()

def upload_file(source_url, file_name, upload_type):
    response = requests.get(source_url + file_name, headers=source_headers)
    content = response.content
    checksum = file_checksum(content)

    if upload_type =='replace':
        obj = s3.head_object(Bucket=bucket_name, Key=file_name)
        if obj.get("Metadata", {}).get("checksum") == checksum:
            print(f"Skipping file - unchanged: {file_name}")
            return

    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=content,
        Metadata={"checksum": checksum}
    )
    print(f"Uploaded: {file_name}")
    return True

def update_index_file(bucket_name, file_list):
    print('Updating index file...')
    with open('../templates/index_template.html','r') as f:
        index_file = f.read()
    html_lines=""
    for file_name in file_list:
        html_lines += f"""      <li><a href="{file_name}">{file_name}</a></li>\n"""

    index_file = index_file.replace('{file_list}', html_lines)
    s3.put_object(
        Bucket=bucket_name,
        Key="index.html",
        Body=index_file,
        ContentType= "text/html"
    )

if __name__ == "__main__":
    # get files in s3 storage bucket
    s3 = boto3.client("s3")
    s3_objects = s3.list_objects_v2(Bucket=bucket_name).get("Contents", [])
    s3_files = [obj["Key"] for obj in s3_objects]

    # get files from source url
    source_files = get_remote_files(source_url, source_headers)

    # upload files in source that aren't in s3 or have changes
    change_index=False
    for source_fname in source_files:
        if source_fname in s3_files:
            upload_type = 'replace'
        else:
            upload_type = 'upload'
        uploaded = upload_file(source_url, source_fname, upload_type)
        if uploaded:
            change_index=True

    # cleanup files in s3 that aren't in source
    for s3_fname in s3_files:
        if s3_fname not in source_files and s3_fname not in ['index.html','datausa-results.json']:
            s3.delete_object(Bucket=bucket_name, Key=s3_fname)
            print(f"Removed from S3 (no longer in source): {s3_fname}")
            change_index=True

    # update index file for static website hosting
    if change_index:
        update_index_file(bucket_name, source_files)