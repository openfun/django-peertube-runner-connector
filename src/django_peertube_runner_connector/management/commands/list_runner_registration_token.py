""" Management command to list all RunnerRegistrationTokens."""

from django.core.management.base import BaseCommand

from django_peertube_runner_connector.models import RunnerRegistrationToken


class Command(BaseCommand):
    """Management command to list all RunnerRegistrationTokens."""

    help = "Lists all RunnerRegistrationTokens"

    def handle(self, *args, **options):
        """Get all RunnerRegistrationTokens and print them."""
        tokens = RunnerRegistrationToken.objects.all()
        for token in tokens:
            self.stdout.write(
                f"Token: {token.registrationToken}, Created: {token.createdAt}"
            )
