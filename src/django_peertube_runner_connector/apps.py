"""Django app config for the connector app."""

from django.apps import AppConfig


class DjangoPeertubeRunnerConnectorConfig(AppConfig):
    """Django app config for the connector app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_peertube_runner_connector"
