import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

BUCKET_NAME='prod-bkhu-breeze'
BUCKET_PREFIX="error_log/v1/"

s3 = boto3.client('s3')


def get_list(event, context):
  current_date=datetime.now().strftime("%Y/%m/%d")
  if not 'queryStringParameters' in event or event['queryStringParameters'] is None or not 'date' in event['queryStringParameters']:
    file_key=current_date
  else:
    file_key=str(event['queryStringParameters']['date'])
    if file_key == '':
      file_key=current_date

  aws_response = s3.list_objects_v2(
    Bucket=BUCKET_NAME,
    Prefix=f"{BUCKET_PREFIX}{file_key}"
  )

  if not 'Contents' in aws_response:
    message = { "message": "No files found." }
    return { "statusCode": 404, "body": json.dumps(message) }

  body = {
    "files": [
      {
        "file": item["Key"].removeprefix(BUCKET_PREFIX),
        "size": item["Size"]
      }
      for item in aws_response['Contents'] if item["Key"][-1] != '/'
    ]
  }

  return {
    "statusCode": 200,
    "body": json.dumps(body,separators=None)
  }


def get_file(event, context):
  if not 'queryStringParameters' in event or event['queryStringParameters'] is None or not 'file' in event['queryStringParameters']:
    message = { "message": "No file specified." }
    return { "statusCode": 403, "body": json.dumps(message) }

  file = event['queryStringParameters']['file']
  file_name = file.split('/')[-1]
  if file == '':
    message = { "message": "No file specified." }
    return { "statusCode": 403, "body": json.dumps(message)}

  try:
    aws_response = s3.get_object(
      Bucket=BUCKET_NAME,
      Key=f"{BUCKET_PREFIX}{file}"
    )
    blob = aws_response['Body'].read()
  except ClientError as ex:
    if ex.response['Error']['Code'] == 'NoSuchKey':
      message = { "message": "File not found." }
      return { "statusCode": 404, "body": json.dumps(message) }
    else:
      raise

  response = {
    "statusCode": 200,
    "headers": { 
      "Content-Type": "application/octet-stream",
      "Content-Disposition": "inline; filename=\""+file_name+"\"",
    },
    "body": blob
  }
  return response
