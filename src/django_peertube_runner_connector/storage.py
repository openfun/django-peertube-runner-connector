"""Video storage for the Django Peertube Runner Connector app."""
from django.core.files.storage import storages
from django.urls import reverse
from django.utils.functional import LazyObject

from storages.backends.s3boto3 import S3Boto3Storage


def get_video_storage_upload_url(key: str, domain: str):
    """
    Get the upload url for the given path.
    It will use the settings callback if defined.
    If the storage inherits from S3Boto3Storage, it will use the boto3 client.
    The default generated upload url use this app as backend.

    The return value is a dict with the following keys:
    - url: the upload url
    - fields: the form fields (it should always contains he 'key' field)
    """

    # pylint: disable=protected-access
    if issubclass(type(video_storage._wrapped), S3Boto3Storage):
        # Use the boto3 client to generate the upload url.
        s3_client = video_storage.connection.meta.client
        return s3_client.generate_presigned_post(
            video_storage.bucket_name,
            key,
            Fields={"acl": "private"},
            Conditions=[
                [{"acl": "private"}],
                ["content-length-range", 0, 2**30],
            ],
            ExpiresIn=24 * 60 * 60 * 7,  # 7 days
        )

    # Use this app to generate the upload url.
    return {
        "url": domain + reverse("runner-jobs-upload_video_file"),
        "fields": {"key": key},
    }


class ConfiguredStorage(LazyObject):
    """Lazy object for the video storage."""

    def _setup(self):
        """Setup the video storage."""
        self._wrapped = storages["videos"]


video_storage = ConfiguredStorage()
