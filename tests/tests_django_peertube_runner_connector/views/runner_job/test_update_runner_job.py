"""Tests for the Runner Job update API."""

import logging

from django.test import TestCase

from django_peertube_runner_connector.factories import (
    RunnerFactory,
    RunnerJobFactory,
    VideoFactory,
)
from django_peertube_runner_connector.models import RunnerJobState, RunnerJobType


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


class UpdateRunnerJobAPITest(TestCase):
    """Test for the Runner Job update API."""

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

    def test_request_with_an_invalid_job_uuid(self):
        """Should not be able to update with an invalid job uuid."""
        self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)
        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e01/update",
            data={
                "runnerToken": "runnerToken",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_request_with_an_invalid_runner_token(self):
        """Should not be able to update with an invalid runner token."""
        self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)
        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/update",
            data={
                "runnerToken": "invalid_token",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_success_hls_job_with_a_valid_runner_token(self):
        """Should be able to update the processing HLS job."""
        runner_job = self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)

        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/update",
            data={
                "runnerToken": "runnerToken",
                "progress": 50,
            },
        )
        self.assertEqual(response.status_code, 204)

        runner_job.refresh_from_db()
        self.video.refresh_from_db()

        self.assertEqual(runner_job.progress, 50)
