import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError
from typing import Union, Tuple, Dict

BUCKET_NAME = os.environ["BUCKET_NAME"]
BUCKET_PREFIX = os.environ["BUCKET_PREFIX"]

s3 = boto3.client("s3")


class QSException(Exception):
    pass


def get_query_string(
    event: Dict, query_string: str
) -> Tuple[Union[QSException, None], Union[None, str]]:
    error = QSException()
    if not "queryStringParameters" in event:
        return (error, None)
    if event["queryStringParameters"] is None:
        return (error, None)
    if not query_string in event["queryStringParameters"]:
        return (error, None)
    if str(event["queryStringParameters"][query_string]) == "":
        return (error, None)
    return (None, event["queryStringParameters"][query_string])


def get_list(event: Dict, context: Dict) -> Dict:
    current_date = datetime.now().strftime("%Y/%m/%d")
    err, file_pattern = get_query_string(event, "date")
    if err is not None:
        file_pattern = current_date

    aws_response = s3.list_objects_v2(
        Bucket=BUCKET_NAME, Prefix=f"{BUCKET_PREFIX}{file_pattern}"
    )

    if not "Contents" in aws_response:
        message = {"message": "No files found."}
        return {"statusCode": 404, "body": json.dumps(message)}

    body = {
        "files": [
            {"file": item["Key"].removeprefix(BUCKET_PREFIX), "size": item["Size"]}
            for item in aws_response["Contents"]
            if item["Key"][-1] != "/"
        ]
    }

    return {"statusCode": 200, "body": json.dumps(body, separators=None)}


def get_file(event: Dict, context: Dict) -> Dict:
    err, file_path = get_query_string(event, "file")
    if err is not None:
        message = {"message": "No file specified."}
        return {"statusCode": 403, "body": json.dumps(message)}

    assert file_path is not None
    file_name = file_path.split("/")[-1]

    try:
        aws_response = s3.get_object(
            Bucket=BUCKET_NAME, Key=f"{BUCKET_PREFIX}{file_name}"
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
