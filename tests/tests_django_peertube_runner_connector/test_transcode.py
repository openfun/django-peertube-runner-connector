"""Tests for the "transcode.py" file of the django_peertube_runner_connector app"""

from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

import ffmpeg

from django_peertube_runner_connector.factories import VideoFactory, VideoFileFactory
from django_peertube_runner_connector.storage import VideoNotFoundError, video_storage
from django_peertube_runner_connector.transcode import (
    _process_transcoding,
    transcode_video,
)


class TestTranscode(TestCase):
    """Test class for the "transcode.py" file."""

    @patch("django_peertube_runner_connector.transcode._process_transcoding")
    def test_transcode_a_not_found_video(self, mock_process):
        """Should throw a VideoNotFoundError exception."""
        with self.assertRaises(VideoNotFoundError):
            transcode_video(
                "test.mp4",
                "video/new_video",
                "https://example.com",
            )

        mock_process.assert_not_called()

    @patch("django_peertube_runner_connector.transcode._process_transcoding")
    def test_transcode(self, mock_process):
        """Should start the transcoding process."""
        simple_file = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )
        video_url = video_storage.save("test_directory/file.mp4", simple_file)

        created_video = transcode_video(
            video_url,
            "test_directory",
            "https://example.com",
        )

        self.assertEqual(created_video.directory, "test_directory")

        mock_process.assert_called_with(
            video=created_video,
            video_path=video_url,
            domain="https://example.com",
        )

    @patch.object(ffmpeg, "probe")
    @patch("django_peertube_runner_connector.transcode.build_new_file")
    @patch("django_peertube_runner_connector.transcode.get_video_stream_duration")
    @patch("django_peertube_runner_connector.transcode.build_video_thumbnails")
    @patch("django_peertube_runner_connector.transcode.create_transcoding_jobs")
    def test_process_transcoding(
        self, mock_transcoding, mock_thumbnails, mock_duration, mock_build, mock_probe
    ):
        """Should start the transcoding process."""
        simple_file = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )
        video_url = video_storage.save("test_directory/file.mp4", simple_file)
        video = VideoFactory(directory="test_directory")
        video_file = VideoFileFactory(filename=video_url, video=video)
        mock_thumbnails.return_value = "thumbnail.jpg"
        mock_duration.return_value = 900
        mock_build.return_value = video_file

        _process_transcoding(
            video=video,
            video_path=video_url,
            domain="domain",
        )

        mock_probe.assert_called_with("/test_directory/file.mp4")
        mock_build.assert_called_with(
            video=video, filename=video_url, existing_probe=mock_probe.return_value
        )
        mock_duration.assert_called_with(
            video_url, existing_probe=mock_probe.return_value
        )
        mock_thumbnails.assert_called_with(video=video, video_file=video_file)
        mock_transcoding.assert_called_with(
            video=video,
            video_file=video_file,
            existing_probe=mock_probe.return_value,
            domain="domain",
        )

        self.assertEqual(video.duration, 900)
        self.assertEqual(video.thumbnailFilename, "thumbnail.jpg")
