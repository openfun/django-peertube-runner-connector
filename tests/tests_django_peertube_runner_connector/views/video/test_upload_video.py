"""Tests for the video upload API."""

from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

import ffmpeg
from tests_django_peertube_runner_connector.probe_response import probe_response

from django_peertube_runner_connector.factories import RunnerFactory
from django_peertube_runner_connector.models import (
    RunnerJob,
    RunnerJobState,
    RunnerJobType,
    Video,
)
from django_peertube_runner_connector.storage import video_storage


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


class UploadVideoAPITest(TestCase):
    """Test for the Video upload API."""

    maxDiff = None

    def setUp(self):
        """Create a runner."""
        self.runner = RunnerFactory(name="New Runner", runnerToken="runnerToken")

    def test_upload_video(self):
        """Should be able to upload a video a create corresponding job."""
        uploaded_video = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )

        with patch.object(ffmpeg, "probe", return_value=probe_response), patch.object(
            ffmpeg, "run"
        ), patch(
            "django_peertube_runner_connector.utils.job_handlers."
            "abstract_job_handler.send_available_jobs_ping_to_runners",
        ) as ping_mock:
            list_dir, _ = video_storage.listdir("")
            dir_num = len(list_dir)

            response = self.client.post(
                "/videos/upload",
                data={"name": "New_Video", "videoFile": uploaded_video},
            )

            self.assertEqual(response.status_code, 200)

            self.assertEqual(RunnerJob.objects.count(), 3)
            self.assertEqual(
                RunnerJob.objects.filter(
                    type=RunnerJobType.VOD_HLS_TRANSCODING
                ).count(),
                3,
            )
            self.assertEqual(
                RunnerJob.objects.filter(state=RunnerJobState.PENDING).count(), 1
            )
            self.assertEqual(
                RunnerJob.objects.filter(
                    state=RunnerJobState.WAITING_FOR_PARENT_JOB
                ).count(),
                2,
            )

            list_dir, _ = video_storage.listdir("")
            self.assertEqual(len(list_dir), dir_num + 1)

            created_video = Video.objects.first()

            _, video_files = video_storage.listdir(created_video.directory)
            self.assertEqual(len(video_files), 1)  # thumbnail
            self.assertEqual(Video.objects.count(), 1)

            created_video = Video.objects.first()
            self.assertTrue(video_storage.exists(created_video.thumbnailFilename))
            self.assertEqual(created_video.files.count(), 1)
            self.assertTrue(video_storage.exists(created_video.files.first().filename))

            ping_mock.assert_called_once()

            runner_job = RunnerJob.objects.first()
            self.assertEqual(
                runner_job.payload["input"]["videoFileUrl"],
                "http://testserver/api/v1/runners/jobs/"
                f"files/videos/{created_video.uuid}/{runner_job.uuid}/max-quality",
            )
