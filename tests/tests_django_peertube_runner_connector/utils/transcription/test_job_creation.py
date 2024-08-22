"""Test the transcription job creation file."""
from unittest.mock import Mock, patch

from django.test import TestCase

from django_peertube_runner_connector.factories import VideoFactory
from django_peertube_runner_connector.utils.transcription.job_creation import (
    create_transcription_job,
)


class TranscriptionJobCreationTestCase(TestCase):
    """Test the transcription job creation utils file."""

    @patch(
        "django_peertube_runner_connector.utils.transcription."
        "job_creation.TranscriptionJobHandler"
    )
    def test_create_transcription_jobs(self, mock_job_handler):
        """Should call TranscriptionJobHandler to create transcription jobs."""
        mocked_class = Mock()
        mock_job_handler.return_value = mocked_class
        video = VideoFactory()
        domain = "example.com"

        create_transcription_job(video=video, domain=domain)

        mocked_class.create.assert_called_with(video=video, domain=domain)
