# Purpose
Complete the Rearc Data Quest as defined in https://github.com/rearc-data/quest.

# Walkthrough
## Part 1: AWS S3 & Sourcing Datasets
Bucket URL: `http://rearc-quest-bls.s3-website.us-east-2.amazonaws.com` 
Python script: `scripts/aws-sync.py`

Ensure your environment is set up with the AWS CLI. 
Install the CLI and run through the `aws configure` command.
Install requirements.txt.

The `aws-sync.py` script will:
- Take inventory of the files in the S3 bucket. 
- Grab the files currently uploaded to the source website, `https://download.bls.gov/pub/time.series/pr/`. This is done through the `get_remote_files()` function. The User-Agent flag must be passed in through the headers of the request to the source website to gain access to fetching the data.
- Loop through the source files and determine if they should be added or replaced from the S3 bucket. This is accomplished by first checking if the file is in the S3 bucket, and the variable `upload_type` will keep track on if it is a new upload or a potential file replacement. Then, the `upload_file()` function will determine if there are any changes in the file. This is accomplished by comparing the hashed contents of the files. If there are changes to the file, the function will replace the file in the S3 bucket, else it will move skip the file upload.
- Loop through the S3 files to determine if any need to be removed to sync back to the source website. Skip the `index.html` file and the `datausa-results.json` that will be discussed in later steps.
- Sync the `index.html` file to be in line with the updated list of files from the source website.

Static website hosting has been enabled on the bucket with a public access bucket policy. This will allow for the bucket to be browsable as a website. An `index.html` file has been created and added to the bucket to specify the front end of this website. An example of this index.html file can be found in `templates/index_template.html`, where there is a placeholder variable `{file_list}` that will be replaced with the list of file names in the bucket.

Bucket Policy:
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::rearc-quest-bls/*"
        }
    ]
}
```

## Part 2: APIs
Python script: `scripts/datausa-api-fetch.py`
S3 Link: `http://rearc-quest-bls.s3-website.us-east-2.amazonaws.com/datausa-results.json`

- Ping the desired API endpoint.
- If the response was fetched successfully with status code 200, format the resulting json response as a string and upload it to S3 bucket.
- If API was not called successfully, print a message with the returned status code and raise an error.

## Part 3: Data Analytics
Python notebook: `data-analysis.ipynb`

- Load the BLS file `pr.data.0.Current` into a python variable.
- Load the variable into a pandas dataframe through `pd.read_csv()` by streaming the variable using StringIO and specifying the tab separated file format. Clean up any whitespaces from the column names and row values.
- Load the `datausa-results.json` from Part 2 from S3 bucket and format it as a JSON. Grab the values from the `Data` key of the JSON. This is the data we want to format and work with. Store into a python variable as a string.
- Load the variable into a pandas dataframe through `pd.read_json()` by streaming the variable using StringIO.
- Walk through the analyses requested in the Quest docs.

# AI Assistance
gpt-4o was used a few times for support in this project.

## Hashing file contents for easy content comparison
Prompt 1: I have a dataset at a source website that I am syncing with an S3 bucket. I am adding and replacing changed files, or deleting files that are no longer in the source dataset to keep my S3 bucket in sync with this website. What is the best way to check if one of the files have changed and need to be replaced? I want this check so I can avoid replacing a file that hasn't changed

Answer 1: TL;DR Use MD5 comparison, but store your own MD5 in S3 metadata to avoid double downloads.

## Static website hosting
Prompt 2: I want to create a public URL to show what is in my S3 bucket.

Answer 2: TL;DR 1. Allow public access at the bucket level 
2. Add a public-read bucket policy
3. Make the entire bucket browsable as a website (list all files in browser)

Terraform
