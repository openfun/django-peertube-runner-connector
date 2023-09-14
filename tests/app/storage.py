"""Custom storage class for testing."""
from django.core.files.storage import FileSystemStorage

from storages.backends.s3boto3 import S3Boto3Storage


class MyS3VideoStorage(S3Boto3Storage):
    """Custom S3 storage class."""

    bucket_name = "my-bucket"


class MyCustomFileSystemVideoStorage(FileSystemStorage):
    """Custom FileSystemStorage class."""

    def url(self, name):
        return self.path(name)
