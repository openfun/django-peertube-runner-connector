"""Test the list_runner_registration_token management command."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from django_peertube_runner_connector.factories import RunnerRegistrationTokenFactory


class GenerateTokenTestCase(TestCase):
    """Test the list_runner_registration_token management command."""

    def test_list_token(self):
        """Should list runner registration tokens."""
        token_list = RunnerRegistrationTokenFactory.create_batch(3)
        out = StringIO()
        call_command("list_runner_registration_token", stdout=out)
        output = out.getvalue().strip()
        for token in token_list:
            self.assertIn(token.registrationToken, output)
