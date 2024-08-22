"""Tests for the Video transcript API."""
from unittest.mock import patch

from django.test import TestCase

from django_peertube_runner_connector.factories import RunnerFactory, VideoFactory
from django_peertube_runner_connector.models import (
    RunnerJob,
    RunnerJobState,
    RunnerJobType,
)


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


class TranscriptVideoAPITest(TestCase):
    """Test for the Transcript Video API."""

    maxDiff = None

    def setUp(self):
        """Create a runner."""
        self.runner = RunnerFactory(name="New Runner", runnerToken="runnerToken")

    def test_transcript_video_with_invalid_path(self):
        """Should not be able to transcript a video with an invalid path."""

        response = self.client.post(
            "/videos/transcript",
            data={"path": "invalid/path"},
        )

        self.assertEqual(response.status_code, 404)

    def test_transcript_video_with_invalid_video(self):
        """Should not be able to transcript a video with an invalid video."""
        response = self.client.post(
            "/videos/1/transcript",
        )

        self.assertEqual(response.status_code, 404)

    def test_transcript_video(self):
        """Should be able to transcript a video."""
        video = VideoFactory()

        with patch(
            "django_peertube_runner_connector.utils.job_handlers."
            "abstract_job_handler.send_available_jobs_ping_to_runners",
        ) as ping_mock:
            response = self.client.post(
                f"/videos/{video.pk}/transcript",
                data={
                    "destination": video.directory,
                },
            )
            self.assertEqual(response.status_code, 200)

            self.assertEqual(RunnerJob.objects.count(), 1)

            ping_mock.assert_called_once()

            runner_job = RunnerJob.objects.first()
            self.assertEqual(runner_job.privatePayload["videoUUID"], video.uuid)
            self.assertEqual(runner_job.type, RunnerJobType.VIDEO_TRANSCRIPTION)
            self.assertEqual(runner_job.state, RunnerJobState.PENDING)
            self.assertIsNone(runner_job.dependsOnRunnerJob)
            self.assertEqual(
                runner_job.payload["input"]["videoFileUrl"],
                "http://testserver/api/v1/runners/jobs/"
                f"files/videos/{video.uuid}/{runner_job.uuid}/max-quality",
            )
