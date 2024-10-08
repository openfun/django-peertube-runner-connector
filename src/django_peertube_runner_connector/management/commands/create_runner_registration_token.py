""" Management command to generate a new RunnerRegistrationToken."""

import uuid

from django.core.management.base import BaseCommand

from django_peertube_runner_connector.models import RunnerRegistrationToken


class Command(BaseCommand):
    """Management command to generate a new RunnerRegistrationToken."""

    help = "Generates a new RunnerRegistrationToken"

    def handle(self, *args, **options):
        """Generate a new RunnerRegistrationToken and print it."""
        token = RunnerRegistrationToken.objects.create(
            registrationToken="ptrrt-" + str(uuid.uuid4())
        )
        self.stdout.write(f"Created token: {token.registrationToken}")
