import boto3
import pytest
from moto import mock_aws

from app.s3_store import S3Store


@pytest.fixture
def store(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="demo-bucket")
        yield S3Store(bucket="demo-bucket", region="us-east-1")


def test_put_and_get(store):
    store.put("greeting", "hello")
    assert store.get("greeting") == "hello"


def test_keys(store):
    store.put("a", "1")
    store.put("b", "2")
    assert sorted(store.keys()) == ["a", "b"]
