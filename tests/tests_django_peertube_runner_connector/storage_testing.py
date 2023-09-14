"""A TestStorage class that uses a temporary directory for storing files"""
import tempfile

from django.core.files.storage import FileSystemStorage


class TestStorage(FileSystemStorage):
    """A test storage class that uses a temporary directory for storing files"""

    temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
    location = temp_dir.name
