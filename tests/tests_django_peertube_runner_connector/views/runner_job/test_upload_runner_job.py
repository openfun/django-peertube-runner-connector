"""Tests for the Runner Job upload API."""
import logging

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from django_peertube_runner_connector.factories import RunnerFactory, VideoFactory
from django_peertube_runner_connector.storage import video_storage


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


class UploadRunnerJobAPITest(TestCase):
    """Test for the Runner Job upload API."""

    maxDiff = None

    def setUp(self):
        """Create a runner and a video."""
        self.runner = RunnerFactory(name="New Runner", runnerToken="runnerToken")
        self.video = VideoFactory(uuid="02404b18-3c50-4929-af61-913f4df65e99")
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """restore logging"""
        logging.disable(logging.NOTSET)

    def test_upload_with_an_invalid_runner_token(self):
        """Should not be able to upload with an invalid token."""
        response = self.client.post(
            "/api/v1/runners/jobs/upload_file",
            data={
                "runnerToken": "invalid_token",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_success_hls_job_with_a_valid_runner_token(self):
        """Should be able to upload a file."""
        uploaded_video = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )

        response = self.client.post(
            "/api/v1/runners/jobs/upload_file",
            data={
                "runnerToken": "runnerToken",
                "key": "video-02404b18-3c50-4929-af61-913f4df65e89/my_video_result.mp4",
                "file": uploaded_video,
            },
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue(
            video_storage.exists(
                "video-02404b18-3c50-4929-af61-913f4df65e89/my_video_result.mp4"
            )
        )
