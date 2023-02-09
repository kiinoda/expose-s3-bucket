import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError
from typing import Dict

BUCKET_NAME = os.environ["BUCKET_NAME"]
BUCKET_PREFIX = os.environ["BUCKET_PREFIX"]

s3 = boto3.client("s3")


class QSException(Exception):
    pass


def get_query_string(event: Dict, query_string: str) -> str:
    qsp = event.get("queryStringParameters")
    if qsp is None or query_string not in qsp or not qsp[query_string]:
        raise QSException()
    return qsp[query_string]


def get_list(event: Dict, context: Dict) -> Dict:
    current_date = datetime.now().strftime("%Y/%m/%d")
    try:
        file_pattern = get_query_string(event, "date")
    except QSException:
        file_pattern = current_date

    aws_response = s3.list_objects_v2(
        Bucket=BUCKET_NAME, Prefix=f"{BUCKET_PREFIX}{file_pattern}"
    )

    if not "Contents" in aws_response:
        message = {"message": "No files found."}
        return {"statusCode": 404, "body": json.dumps(message)}

    items = sorted(aws_response["Contents"], key=lambda item: item["LastModified"], reverse=True)

    body = {
        "files": [
            {"file": item["Key"].removeprefix(BUCKET_PREFIX), "size": item["Size"]}
            for item in items
            if item["Key"][-1] != "/"
        ]
    }

    return {"statusCode": 200, "body": json.dumps(body, separators=None)}


def get_file(event: Dict, context: Dict) -> Dict:
    try:
        file_path = get_query_string(event, "file")
    except QSException:
        message = {"message": "No file specified."}
        return {"statusCode": 403, "body": json.dumps(message)}

    file_name = file_path.split("/")[-1]

    try:
        aws_response = s3.get_object(
            Bucket=BUCKET_NAME, Key=f"{BUCKET_PREFIX}{file_path}"
        )
        blob = aws_response["Body"].read()
    except ClientError as ex:
        if ex.response["Error"]["Code"] == "NoSuchKey":
            message = {"message": "File not found."}
            return {"statusCode": 404, "body": json.dumps(message)}
        else:
            raise

    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/octet-stream",
            "Content-Disposition": 'inline; filename="' + file_name + '"',
        },
        "body": blob,
    }
    return response
