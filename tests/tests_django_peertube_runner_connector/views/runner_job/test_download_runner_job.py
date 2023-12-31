"""Tests for the Runner Job download API."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from django_peertube_runner_connector.factories import (
    RunnerFactory,
    RunnerJobFactory,
    VideoFactory,
    VideoFileFactory,
)
from django_peertube_runner_connector.models import RunnerJobState, RunnerJobType
from django_peertube_runner_connector.storage import video_storage


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


class DownloadVideoRunnerJobAPITest(TestCase):
    """Test for the Runner Job download API."""

    maxDiff = None

    def setUp(self):
        """Create a runner and a video."""
        self.runner = RunnerFactory(name="New Runner", runnerToken="runnerToken")
        self.video = VideoFactory(uuid="02404b18-3c50-4929-af61-913f4df65e99")

    def create_processing_job(self, job_type: RunnerJobType):
        """Create a processing job."""
        return RunnerJobFactory(
            runner=self.runner,
            type=job_type,
            uuid="02404b18-3c50-4929-af61-913f4df65e00",
            payload={"output": {"resolution": "1080"}},
            privatePayload={
                "videoUUID": "02404b18-3c50-4929-af61-913f4df65e99",
                "isNewVideo": True,
            },
            state=RunnerJobState.PROCESSING,
        )

    def test_download_video_with_an_invalid_job_uuid(self):
        """Should not be able to download with an invalid job uuid."""
        self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)
        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e01/"
            "files/videos/02404b18-3c50-4929-af61-913f4df65e99/max-quality",
            data={
                "runnerToken": "runnerToken",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_download_video_with_an_invalid_video_uuid(self):
        """Should not be able to download with an invalid video uuid."""
        self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)
        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/"
            "files/videos/02404b18-3c50-4929-af61-913f4df69e99/max-quality",
            data={
                "runnerToken": "runnerToken",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_request_with_an_invalid_runner_token(self):
        """Should not be able to request the list."""
        self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)
        response = self.client.post(
            "/api/v1/runners/jobs/"
            "files/videos/02404b18-3c50-4929-af61-913f4df65e99/max-quality",
            data={
                "runnerToken": "invalid_token",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_download_video_with_a_valid_runner_token(self):
        """Should be able to download a video for a job."""
        self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)

        video_to_download = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )

        filename = video_storage.save(
            "video_test.mp4",
            video_to_download,
        )

        VideoFileFactory(video=self.video, filename=filename)

        response = self.client.post(
            "/api/v1/runners/jobs/"
            "files/videos/02404b18-3c50-4929-af61-913f4df65e99/"
            "02404b18-3c50-4929-af61-913f4df65e00/max-quality",
            data={
                "runnerToken": "runnerToken",
            },
        )

        self.assertEqual(response.status_code, 301)
