"""Test the abstract_vod_transcoding_job_handler."""

from unittest.mock import patch

from django.test import TestCase

from django_peertube_runner_connector.factories import (
    RunnerJobFactory,
    VideoFactory,
    VideoJobInfoFactory,
)
from django_peertube_runner_connector.models import RunnerJobState, RunnerJobType
from django_peertube_runner_connector.utils.job_handlers.vod_hls_transcoding_job_handler import (
    VODHLSTranscodingJobHandler,
)


class TestAbstractVODTranscodingJobHandler(TestCase):
    """Test the abstract_vod_transcoding_job_handler handler."""

    def setUp(self):
        """Create a video, a runner job and a video job."""
        # Create a Video object to use in the tests
        self.video = VideoFactory(
            uuid="123e4567-e89b-12d3-a456-426655440002",
        )

        self.job_info = VideoJobInfoFactory(video=self.video, pendingTranscode=1)

        # Create a RunnerJob object to use in the tests
        self.runner_job = RunnerJobFactory(
            type=RunnerJobType.VOD_HLS_TRANSCODING,
            progress=50,
            payload={
                "input": {
                    "videoFileUrl": "http://example.com/test.mp4",
                },
                "output": {
                    "resolution": "720p",
                    "fps": 30,
                },
            },
            privatePayload={
                "isNewVideo": False,
                "deleteWebVideoFiles": False,
                "videoUUID": "123e4567-e89b-12d3-a456-426655440002",
            },
            failures=4,
            priority=0,
        )

    @patch(
        "django_peertube_runner_connector.utils.job_handlers."
        "abstract_vod_transcoding_job_handler.move_to_failed_transcoding_state"
    )
    def test_specific_error(self, mock_move):
        """Should move the job to the failed state and decrease pendingTranscode."""
        handler = VODHLSTranscodingJobHandler()
        handler.specific_error(
            runner_job=self.runner_job,
            message="Test",
            next_state=RunnerJobState.ERRORED,
        )
        mock_move.assert_called_once_with(self.video)
        self.job_info.refresh_from_db()
        self.assertEqual(self.job_info.pendingTranscode, 0)

    @patch(
        "django_peertube_runner_connector.utils.job_handlers."
        "abstract_vod_transcoding_job_handler.move_to_next_state"
    )
    def test_specific_cancel(self, mock_move):
        """Should move the job to the next state and decrease pendingTranscode."""
        handler = VODHLSTranscodingJobHandler()
        handler.specific_cancel(runner_job=self.runner_job)
        mock_move.assert_called_once_with(video=self.video)
        self.job_info.refresh_from_db()
        self.assertEqual(self.job_info.pendingTranscode, 0)
