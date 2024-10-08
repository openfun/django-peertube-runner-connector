"""Tests for the Runner Job success API."""

from datetime import datetime, timezone as tz
import logging
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

import ffmpeg
from tests_django_peertube_runner_connector.probe_response import probe_response

from django_peertube_runner_connector.factories import (
    RunnerFactory,
    RunnerJobFactory,
    VideoFactory,
)
from django_peertube_runner_connector.models import RunnerJobState, RunnerJobType
from django_peertube_runner_connector.storage import video_storage


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


class SuccessRunnerJobAPITest(TestCase):
    """Test for the Runner Job success API."""

    maxDiff = None

    def setUp(self):
        """Create a runner and a video."""
        self.runner = RunnerFactory(name="New Runner", runnerToken="runnerToken")
        self.video = VideoFactory(uuid="02404b18-3c50-4929-af61-913f4df65e99")
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """restore logging"""
        logging.disable(logging.NOTSET)

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

    def test_success_with_an_invalid_job_uuid(self):
        """Should not be able to success with an invalid job uuid."""
        self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)
        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e01/success",
            data={
                "runnerToken": "runnerToken",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_success_with_an_invalid_runner_token(self):
        """Should not be able to success with an invalid runner token."""
        self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)
        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/success",
            data={
                "runnerToken": "invalid_token",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_success_hls_job_with_a_valid_runner_token(self):
        """Should be able to abort and reset the processing HLS job."""
        runner_job = self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)

        uploaded_video = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )
        SimpleUploadedFile("file.m3u8", b"file_content", content_type="video/mp4")

        now = datetime(2018, 8, 8, tzinfo=tz.utc)

        with patch.object(timezone, "now", return_value=now), patch.object(
            ffmpeg, "probe", return_value=probe_response
        ):
            response = self.client.post(
                "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/success",
                data={
                    "runnerToken": "runnerToken",
                    "payload[videoFile]": uploaded_video,
                    "payload[resolutionPlaylistFile]": uploaded_video,
                },
            )
            self.assertEqual(response.status_code, 204)

            runner_job.refresh_from_db()
            self.video.refresh_from_db()

            self.assertEqual(runner_job.state, 3)  # COMPLETED
            self.assertEqual(runner_job.failures, 0)  # should have been OK

            self.assertIsNotNone(
                self.video.streamingPlaylist
            )  # playlist should have been created

            self.assertEqual(self.video.state, 1)  # VideoState.PUBLISHED

            _, video_files = video_storage.listdir(f"video-{self.video.uuid}")
            # video, playlist, master playlist
            self.assertEqual(len(video_files), 3)
            self.assertIn("master.m3u8", video_files)
            self.assertTrue(
                video_storage.exists(self.video.streamingPlaylist.playlistFilename)
            )

            self.assertEqual(self.video.streamingPlaylist.videoFiles.count(), 1)
            self.assertTrue(
                video_storage.exists(
                    self.video.streamingPlaylist.videoFiles.first().filename
                )
            )

    def test_success_transcript_job_with_a_valid_runner_token(self):
        """Should be able to abort and reset the processing HLS job."""
        vtt_file = SimpleUploadedFile(
            "file.vtt", b"file_content", content_type="text/vtt"
        )
        runner_job = self.create_processing_job(RunnerJobType.VIDEO_TRANSCRIPTION)

        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/success",
            data={
                "runnerToken": "runnerToken",
                "payload[inputLanguage]": "fr",
                "payload[vttFile]": vtt_file,
            },
        )
        self.assertEqual(response.status_code, 204)

        runner_job.refresh_from_db()
        self.video.refresh_from_db()

        self.assertEqual(runner_job.state, RunnerJobState.COMPLETED)
        self.assertEqual(runner_job.failures, 0)  # should have been OK

        vtt_file.seek(0)
        self.assertEqual(
            video_storage.open(self.video.transcriptFileName).read(), vtt_file.read()
        )
        self.assertEqual(self.video.language, "fr")
