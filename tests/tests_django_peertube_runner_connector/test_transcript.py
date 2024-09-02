"""Tests for the "transcript.py" file of the django_peertube_runner_connector app"""
from unittest.mock import patch

from django.test import TestCase

from django_peertube_runner_connector.factories import VideoFactory
from django_peertube_runner_connector.models import Video
from django_peertube_runner_connector.transcript import transcript_video


class TestTranscript(TestCase):
    """Test the transcript file."""

    @patch("django_peertube_runner_connector.transcript.create_transcription_job")
    def test_transcript_video_video_does_not_exist(self, mock_create_transcription_job):
        """A video should be created if it does not exist."""
        destination = "test_directory"
        domain = "https://example.com"
        transcript_video(destination, domain)

        video = Video.objects.get(directory=destination)
        self.assertIsNotNone(video)

        mock_create_transcription_job.assert_called_with(video=video, domain=domain)

    @patch("django_peertube_runner_connector.transcript.create_transcription_job")
    def test_transcript_video(self, mock_create_transcription_job):
        """Should be able to transcribe a video."""
        video = VideoFactory()
        domain = "https://example.com"

        transcript_video(destination=video.directory, domain=domain)

        mock_create_transcription_job.assert_called_with(video=video, domain=domain)

    @patch("django_peertube_runner_connector.transcript.create_transcription_job")
    def test_transcript_video_with_video_url(self, mock_create_transcription_job):
        """Should be able to transcribe a video."""
        video = VideoFactory()
        domain = "https://example.com"

        transcript_video(
            destination=video.directory,
            domain=domain,
            video_url="https://example.com/video.mp4",
        )

        mock_create_transcription_job.assert_called_with(
            video=video, domain=domain, video_url="https://example.com/video.mp4"
        )
