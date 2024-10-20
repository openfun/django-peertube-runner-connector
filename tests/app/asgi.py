"""
ASGI config for api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

# pylint: disable=wrong-import-position

import os


os.environ.setdefault("DJANGO_CONFIGURATION", "Development")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

from configurations.asgi import get_asgi_application  # noqa


django_asgi_app = get_asgi_application()


# its important to make all other imports below this comment
import socketio  # noqa

from django_peertube_runner_connector.socket import sio  # noqa


application = socketio.ASGIApp(sio, django_asgi_app)
