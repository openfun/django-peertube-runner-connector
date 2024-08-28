"""Test the create_runner_registration_token management command."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from django_peertube_runner_connector.models import RunnerRegistrationToken


class CreateTokenTestCase(TestCase):
    """Test the create_runner_registration_token management command."""

    def test_create_token(self):
        """Should create a new RunnerRegistrationToken."""
        out = StringIO()
        call_command("create_runner_registration_token", stdout=out)
        token_str = out.getvalue().strip().split()[-1]
        token = RunnerRegistrationToken.objects.get(registrationToken=token_str)
        self.assertIsNotNone(token)
