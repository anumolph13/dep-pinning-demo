"""Tiny S3-backed key/value store used to exercise boto3 + python-dotenv."""

import os

import boto3
from dotenv import load_dotenv

load_dotenv()


class S3Store:
    def __init__(self, bucket: str | None = None, region: str | None = None):
        self.bucket = bucket or os.getenv("APP_BUCKET", "demo-bucket")
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.client = boto3.client("s3", region_name=self.region)

    def put(self, key: str, value: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=value.encode())

    def get(self, key: str) -> str:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read().decode()

    def keys(self) -> list[str]:
        resp = self.client.list_objects_v2(Bucket=self.bucket)
        return [o["Key"] for o in resp.get("Contents", [])]
