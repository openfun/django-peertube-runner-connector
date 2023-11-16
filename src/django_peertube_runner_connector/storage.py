"""Video storage for the Django Peertube Runner Connector app."""
from django.conf import settings
from django.core.files import storage
from django.utils.functional import LazyObject


class ConfiguredStorage(LazyObject):
    """Lazy object for the video storage."""

    def _setup(self):
        """Setup the video storage."""
        params = settings.STORAGES["videos"]
        backend = params.get("BACKEND")
        options = params.get("OPTIONS", {})
        self._wrapped = storage.get_storage_class(backend)(**options)


video_storage = ConfiguredStorage()
