"""Custom storage class for testing."""

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from storages.backends.s3boto3 import S3Boto3Storage


class MyS3VideoStorage(S3Boto3Storage):
    """Custom S3 storage class."""

    bucket_name = "my-bucket"


class MyCustomFileSystemVideoStorage(FileSystemStorage):
    """Custom FileSystemStorage class."""

    location = settings.VIDEO_URL
    base_url = f"http://localhost:8000/{settings.VIDEO_URL}/"
