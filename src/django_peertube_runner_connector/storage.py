"""Video storage for the Django Peertube Runner Connector app."""
from django.conf import settings
from django.core.files import storage
from django.utils.functional import LazyObject


class ConfiguredStorage(LazyObject):
    """Lazy object for the video storage."""

    def _setup(self):
        self._wrapped = storage.get_storage_class(
            settings.STORAGES["videos"]["BACKEND"]
        )()


video_storage = ConfiguredStorage()
