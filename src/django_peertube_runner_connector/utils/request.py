"""Utils functions for request."""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Return the client ip even with a reverse proxy.
    This function is dangerous. With many setups a malicious user could easily cause
    this function to return any address they want (instead of their real one).
    See https://esd.io/blog/flask-apps-heroku-real-ip-spoofing.html.
    This won't be a problem for us because only runners are using this function.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0]
    else:
        client_ip = request.META.get("REMOTE_ADDR")
    return client_ip
