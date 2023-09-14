"""Tests for the Runner unregister API."""
from django.test import TestCase

from django_peertube_runner_connector.factories import RunnerFactory


class UnregisterRunnerAPITest(TestCase):
    """Test for the Unregister Runner API."""

    maxDiff = None

    def setUp(self):
        """Create a runner and a registration token."""
        RunnerFactory(
            runnerToken="runnerToken",
            runnerRegistrationToken__registrationToken="registrationToken",
        )

    def test_unregister_fail_no_token(self):
        """Should fail because of missing registration token."""
        response = self.client.post("/api/v1/runners/unregister")

        self.assertEqual(response.status_code, 404)
        self.assertIn(response.json()["message"], "Registration token is invalid")

    def test_unregister_fail_token_not_found(self):
        """Should fail because of incorrect registration token."""
        response = self.client.post(
            "/api/v1/runners/unregister",
            data={
                "runnerToken": "unknown_registrationToken",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn(response.json()["message"], "Registration token is invalid")

    def test_register_success(self):
        """Should be able to delete a runner."""
        response = self.client.post(
            "/api/v1/runners/unregister",
            data={
                "runnerToken": "runnerToken",
            },
        )

        self.assertEqual(response.status_code, 204)
