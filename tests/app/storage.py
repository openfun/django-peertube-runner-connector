"""Custom storage class for testing."""
from storages.backends.s3boto3 import S3Boto3Storage


class MyVideoStorage(S3Boto3Storage):
    """Custom S3 storage class."""

    bucket_name = "my-bucket"
