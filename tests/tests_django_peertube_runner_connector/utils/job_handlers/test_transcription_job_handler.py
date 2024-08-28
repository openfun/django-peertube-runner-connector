"""Test the transcription_job_handler."""

from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from django_peertube_runner_connector.factories import (
    RunnerJobFactory,
    VideoFactory,
    VideoJobInfoFactory,
)
from django_peertube_runner_connector.models import RunnerJobState, RunnerJobType
from django_peertube_runner_connector.utils.job_handlers.transcription_job_handler import (
    TranscriptionJobHandler,
)


class TestTranscriptionJobHandler(TestCase):
    """Test the transcription_job_handler."""

    maxDiff = None

    def setUp(self):
        """Create a video, a runner job and a video job."""
        # Create a Video object to use in the tests
        self.video = VideoFactory(
            uuid="123e4567-e89b-12d3-a456-426655440002",
        )

        self.job_info = VideoJobInfoFactory(video=self.video, pendingTranscript=1)

        # Create a RunnerJob object to use in the tests
        self.runner_job = RunnerJobFactory(
            type=RunnerJobType.VIDEO_TRANSCRIPTION,
            progress=50,
            payload={
                "input": {
                    "videoFileUrl": "http://example.com/test.mp4",
                },
            },
            privatePayload={
                "videoUUID": "123e4567-e89b-12d3-a456-426655440002",
            },
            failures=4,
            priority=0,
        )

    def test_specific_error(self):
        """Should decrease pendingTranscript."""
        handler = TranscriptionJobHandler()

        handler.specific_error(
            runner_job=self.runner_job,
            message="Test",
            next_state=RunnerJobState.ERRORED,
        )

        self.job_info.refresh_from_db()
        self.assertEqual(self.job_info.pendingTranscript, 0)

    def test_specific_cancel(self):
        """Should decrease pendingTranscript."""
        handler = TranscriptionJobHandler()

        handler.specific_cancel(runner_job=self.runner_job)

        self.job_info.refresh_from_db()
        self.assertEqual(self.job_info.pendingTranscript, 0)

    def test_create(self):
        """Should be able to create a VIDEO_TRANSCRIPTION runner job."""
        handler = TranscriptionJobHandler()
        runner_job = handler.create(self.video, "test_url")

        self.video.refresh_from_db()
        self.assertEqual(runner_job.type, RunnerJobType.VIDEO_TRANSCRIPTION)
        self.assertEqual(
            runner_job.payload,
            {
                "input": {
                    "videoFileUrl": (
                        "test_url/api/v1/runners/jobs/files/videos/123e4567-e89b-"
                        f"12d3-a456-426655440002/{runner_job.uuid}/max-quality"
                    ),
                },
            },
        )

        self.assertEqual(
            runner_job.privatePayload,
            {
                "videoUUID": str(self.video.uuid),
            },
        )
        self.assertEqual(self.video.jobInfo.pendingTranscript, 2)

    @patch(
        "django_peertube_runner_connector.utils.job_handlers."
        "transcription_job_handler.on_transcription_ended"
    )
    @patch(
        "django_peertube_runner_connector.utils.job_handlers."
        "transcription_job_handler.generate_transcription_filename",
    )
    @patch(
        "django_peertube_runner_connector.utils.job_handlers."
        "transcription_job_handler.get_video_directory",
    )
    def test_specific_complete(
        self,
        mock_get_video_directory,
        mock_gen_transcript_filename,
        mock_on_transcription_ended,
    ):
        """Should be able to complete a VIDEO_TRANSCRIPTION runner job."""
        language = "fr"
        vtt_filename = "c0412e42-2913-4537-af29-e734d152e5af-fr.vtt"
        vtt_path = f"video-123e4567-e89b-12d3-a456-426655440002/{vtt_filename}"

        mock_get_video_directory.return_value = vtt_path
        mock_gen_transcript_filename.return_value = vtt_filename
        generated_vtt_file = SimpleUploadedFile(
            "file.vtt", b"file_content", content_type="text/vtt"
        )
        result_payload = {"inputLanguage": language, "vttFile": generated_vtt_file}
        handler = TranscriptionJobHandler()

        handler.specific_complete(self.runner_job, result_payload=result_payload)

        mock_gen_transcript_filename.assert_called_once_with(language, None)
        mock_get_video_directory.assert_called_once_with(self.video, vtt_filename)

        self.video.refresh_from_db()
        self.assertEqual(self.video.language, language)
        self.assertEqual(self.video.transcriptFileName, vtt_path)

        mock_on_transcription_ended.assert_called_once_with(
            self.video, language, vtt_path
        )
