import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from typing import Union, Tuple


BUCKET_NAME='prod-bkhu-breeze'
BUCKET_PREFIX="error_log/v1/"

s3 = boto3.client('s3')

class QSException(Exception):
  pass

def get_query_string(event: any, query_string: str) -> Tuple[Union[None, QSException], Union[None, str]]:
  error = QSException()
  if not 'queryStringParameters' in event:
    return (error, None)
  if event['queryStringParameters'] is None:
    return (error, None)
  if not query_string in event['queryStringParameters']:
    return (error, None)
  if str(event['queryStringParameters'][query_string]) == '':
    return (error, None)
  return (None, event['queryStringParameters'][query_string])

def get_list(event: any, context: any) -> dict:
  current_date=datetime.now().strftime("%Y/%m/%d")
  err, file_pattern = get_query_string(event, 'date')
  if err is not None:
    file_pattern = current_date

  aws_response = s3.list_objects_v2(
    Bucket=BUCKET_NAME,
    Prefix=f"{BUCKET_PREFIX}{file_pattern}"
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


def get_file(event: any, context: any) -> dict:
  err, file = get_query_string(event, 'file')
  if err is not None:
    message = { "message": "No file specified." }
    return { "statusCode": 403, "body": json.dumps(message) }

  file_name = file.split('/')[-1]

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
