"""Test the "thumbnail.py" utils file."""

from unittest.mock import patch

from django.test import TestCase

import ffmpeg
from tests_django_peertube_runner_connector.probe_response import (
    probe_response,
    probe_response_without_video_stream,
)

from django_peertube_runner_connector.factories import VideoFactory, VideoFileFactory
from django_peertube_runner_connector.storage import video_storage
from django_peertube_runner_connector.utils.thumbnail import build_video_thumbnails


class ThumbnailTestCase(TestCase):
    """Test the thumbnail utils file."""

    def setUp(self):
        """Create a video, video file and a video url."""
        self.video = VideoFactory()
        self.video_file = VideoFileFactory(video=self.video, filename="test.mp4")
        self.video_url = video_storage.url(self.video_file.filename)
        self.thumbnail_filename = f"video-{self.video.uuid}/thumbnail.jpg"

    def tearDown(self):
        """Delete the created thumbnail file."""
        video_storage.delete(self.thumbnail_filename)

    @patch.object(ffmpeg, "run")
    def test_build_video_thumbnails(self, mock_run):
        """Should create a thumbnail file."""
        thumbnail_filename = build_video_thumbnails(
            video=self.video,
            video_file=self.video_file,
            existing_probe=probe_response,
        )

        mock_run.assert_called_once()
        self.assertEqual(thumbnail_filename, self.thumbnail_filename)
        self.assertTrue(video_storage.exists(thumbnail_filename))

    @patch.object(ffmpeg, "run")
    def test_build_video_thumbnails_with_no_video_stream(self, mock_run):
        """Should create a thumbnail file."""
        thumbnail_filename = build_video_thumbnails(
            video=self.video,
            video_file=self.video_file,
            existing_probe=probe_response_without_video_stream,
        )

        mock_run.assert_not_called()
        self.assertIsNone(thumbnail_filename)
