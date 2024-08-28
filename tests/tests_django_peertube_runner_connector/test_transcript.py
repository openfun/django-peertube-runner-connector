"""Tests for the "transcript.py" file of the django_peertube_runner_connector app"""

from unittest.mock import patch

from django.test import TestCase

from django_peertube_runner_connector.factories import VideoFactory
from django_peertube_runner_connector.models import Video
from django_peertube_runner_connector.transcript import transcript_video


class TestTranscript(TestCase):
    """Test the transcript file."""

    def test_transcript_video_video_does_not_exist(self):
        """Should raise a VideoNotFoundError exception."""
        with self.assertRaises(Video.DoesNotExist):
            transcript_video("test_directory", "https://example.com")

    @patch("django_peertube_runner_connector.transcript.create_transcription_job")
    def test_transcript_video(self, mock_create_transcription_job):
        """Should be able to transcribe a video."""
        video = VideoFactory()
        domain = "https://example.com"

        transcript_video(destination=video.directory, domain=domain)

        mock_create_transcription_job.assert_called_with(video=video, domain=domain)
