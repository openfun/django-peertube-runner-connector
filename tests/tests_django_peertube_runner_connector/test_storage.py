"""Test the storage file."""
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from django_peertube_runner_connector.storage import ConfiguredStorage


class TestStorage(TestCase):
    """Test the storage file."""

    tempdir = tempfile.gettempdir()

    @override_settings(
        STORAGES={
            "videos": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
                "OPTIONS": {"location": tempdir},
            }
        }
    )
    def test_storage_configuration(self):
        """Calling several times the storage should not affect his options ."""
        simple_file = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )
        storage = ConfiguredStorage()

        storage.save("random_file", simple_file)
        self.assertTrue(storage.exists("random_file"))
        self.assertEqual(storage.path("random_file"), f"{self.tempdir}/random_file")

        storage = ConfiguredStorage()
        self.assertTrue(storage.exists("random_file"))
        self.assertEqual(storage.path("random_file"), f"{self.tempdir}/random_file")
