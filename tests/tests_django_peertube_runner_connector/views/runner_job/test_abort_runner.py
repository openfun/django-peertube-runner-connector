"""Tests for the Runner Job Abort API."""
from datetime import datetime, timezone as tz
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from django_peertube_runner_connector.factories import RunnerFactory, RunnerJobFactory
from django_peertube_runner_connector.models import RunnerJobState, RunnerJobType


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


class AbortRunnerJobAPITest(TestCase):
    """Test for the Runner Job Abort API."""

    maxDiff = None

    def setUp(self):
        """Create a runner."""
        self.runner = RunnerFactory(name="New Runner", runnerToken="runnerToken")

    def create_processing_job(self, job_type: RunnerJobType):
        """Create a processing job."""
        return RunnerJobFactory(
            runner=self.runner,
            type=job_type,
            uuid="02404b18-3c50-4929-af61-913f4df65e00",
            payload={"foo": "bar"},
            privatePayload={"foo": "bar"},
            state=RunnerJobState.PROCESSING,
        )

    def test_abort_with_an_invalid_job_uuid(self):
        """Should not be able to abort with an invalid job uuid."""
        self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)
        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e01/abort",
            data={
                "runnerToken": "runnerToken",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_abort_with_an_invalid_runner_token(self):
        """Should not be able to abort with an invalid runner token."""
        self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)
        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/abort",
            data={
                "runnerToken": "invalid_token",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_abort_hls_job_with_a_valid_runner_token(self):
        """Should be able to abort and reset the processing HLS job."""
        runner_job = self.create_processing_job(RunnerJobType.VOD_HLS_TRANSCODING)

        now = datetime(2018, 8, 8, tzinfo=tz.utc)

        with patch.object(timezone, "now", return_value=now):
            response = self.client.post(
                "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/abort",
                data={
                    "runnerToken": "runnerToken",
                },
            )

        self.assertEqual(response.status_code, 204)
        runner_job.refresh_from_db()

        self.assertEqual(runner_job.state, 1)  # back to pending
        self.assertEqual(runner_job.failures, 1)  # has been increased by 1
        self.assertEqual(runner_job.finishedAt, None)
        self.assertEqual(runner_job.startedAt, None)
        self.assertEqual(runner_job.processingJobToken, None)
        self.assertEqual(runner_job.progress, None)
