"""Tests for the Runner register API."""
from django.test import TestCase

from django_peertube_runner_connector.factories import RunnerRegistrationTokenFactory
from django_peertube_runner_connector.models import Runner


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


class RegisterRunnerAPITest(TestCase):
    """Test for the Runner register API."""

    maxDiff = None

    def setUp(self):
        """Create a registration token."""
        RunnerRegistrationTokenFactory(registrationToken="registrationToken")

    def test_register_fail_no_name_and_no_token(self):
        """Should fail because of missing name and registration token."""
        response = self.client.post("/api/v1/runners/register")

        self.assertEqual(response.status_code, 400)

    def test_register_fail_token_not_found(self):
        """Should fail because of incorrect registration token."""
        response = self.client.post(
            "/api/v1/runners/register",
            data={
                "name": "New Runner",
                "registrationToken": "unknown_registrationToken",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn(response.json()["message"], "Registration token is invalid")

    def test_register_success(self):
        """Should be able to register a runner."""
        response = self.client.post(
            "/api/v1/runners/register",
            data={
                "name": "New Runner",
                "registrationToken": "registrationToken",
            },
        )

        self.assertEqual(response.status_code, 200)
        created_runner = Runner.objects.get(name="New Runner")
        self.assertEqual(
            response.json(),
            {
                "id": str(created_runner.id),
                "name": "New Runner",
                "runnerToken": created_runner.runnerToken,
            },
        )
