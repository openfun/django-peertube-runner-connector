"""Video storage for the Django Peertube Runner Connector app."""

from django.core.files.storage import storages
from django.utils.functional import LazyObject


class VideoNotFoundError(Exception):
    """Exception class for video not found error."""


class ConfiguredStorage(LazyObject):
    """Lazy object for the video storage."""

    def _setup(self):
        """Setup the video storage."""
        self._wrapped = storages["videos"]


video_storage = ConfiguredStorage()
