"""Tests for the Runner Job Accept API."""

from datetime import datetime, timezone as tz
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from django_peertube_runner_connector.factories import RunnerFactory, RunnerJobFactory
from django_peertube_runner_connector.models import RunnerJobState


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


class AcceptRunnerJobAPITest(TestCase):
    """Test for the Runner Job Accept API."""

    maxDiff = None

    def setUp(self):
        """Create a runner and a related runner job."""
        self.runner = RunnerFactory(name="New Runner", runnerToken="runnerToken")
        self.other_runner = RunnerFactory(
            name="Other Runner", runnerToken="otherRunnerToken"
        )
        self.runner_job = RunnerJobFactory(
            runner=None,
            type="vod-hls-transcoding",
            uuid="02404b18-3c50-4929-af61-913f4df65e00",
            payload={"foo": "bar"},
            privatePayload={"foo": "bar"},
        )

    def test_accept_with_an_invalid_job_uuid(self):
        """Should not be able to accept with an invalid job uuid."""
        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e01/accept",
            data={
                "runnerToken": "runnerToken",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_accept_with_an_invalid_runner_token(self):
        """Should not be able to accept with an invalid runner token."""
        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/accept",
            data={
                "runnerToken": "invalid_token",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_accept_with_a_valid_runner_token(self):
        """Should be able to accept a job."""
        now = datetime(2018, 8, 8, tzinfo=tz.utc)

        with patch.object(timezone, "now", return_value=now):
            response = self.client.post(
                "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/accept",
                data={
                    "runnerToken": "runnerToken",
                },
            )

            other_response = self.client.post(
                "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/accept",
                data={
                    "runnerToken": "otherRunnerToken",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(other_response.status_code, 409)
        self.runner_job.refresh_from_db()

        self.assertEqual(
            response.json()["job"],
            {
                "error": None,
                "failures": 0,
                "finishedAt": None,
                "jobToken": self.runner_job.processingJobToken,
                "parent": None,
                "payload": {"foo": "bar"},
                "priority": 1,
                "progress": 0.0,
                "runner": {
                    "id": str(self.runner.id),
                    "name": "New Runner",
                    "runnerToken": "runnerToken",
                },
                "startedAt": "2018-08-08T00:00:00Z",
                "state": {"id": 2, "label": "Processing"},
                "type": "vod-hls-transcoding",
                "uuid": "02404b18-3c50-4929-af61-913f4df65e00",
            },
        )

    def test_accept_an_already_processing_job(self):
        """Should not be able to accept an already processing job."""
        self.runner_job.state = RunnerJobState.PROCESSING
        self.runner_job.save()

        response = self.client.post(
            "/api/v1/runners/jobs/02404b18-3c50-4929-af61-913f4df65e00/accept",
            data={
                "runnerToken": "runnerToken",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data, "This job is not in pending state anymore")
