"""Tests for the "socket.py" file of the django_peertube_runner_connector app"""
from unittest.mock import AsyncMock, patch

from django.test import TestCase

from django_peertube_runner_connector.factories import RunnerFactory
from django_peertube_runner_connector.socket import (
    connect,
    disconnect,
    send_available_jobs_ping_to_runners,
)


class TestSocket(TestCase):
    """Test class for the "socket.py" file."""

    def setUp(self):
        """Create a video."""
        self.runner = RunnerFactory()

    @patch("django_peertube_runner_connector.socket.logger")
    @patch("django_peertube_runner_connector.socket.sio")
    async def test_socket_connect(self, _mock_sio, mock_logger):
        """Known runner should be able to connect to the server."""
        await connect(45115, None, {"runnerToken": self.runner.runnerToken})

        mock_logger.info.assert_called_with(
            "Runner with token %s connected with sid %s", self.runner.runnerToken, 45115
        )

    @patch("django_peertube_runner_connector.socket.logger")
    @patch("django_peertube_runner_connector.socket.sio", new_callable=AsyncMock)
    async def test_socket_connect_wrong_runner_token(self, mock_sio, mock_logger):
        """Known runner should be able to connect to the server."""
        await connect(45115, None, {"runnerToken": "Wrong Runner Token"})

        mock_logger.info.assert_called_with(
            "Runner with token %s not found", "Wrong Runner Token"
        )
        mock_sio.disconnect.assert_called_with(45115, namespace="/runners")

    @patch("django_peertube_runner_connector.socket.logger")
    @patch("django_peertube_runner_connector.socket.sio", new_callable=AsyncMock)
    async def test_socket_disconnect(self, _mock_sio, mock_logger):
        """Known runner should be able to connect to the server."""
        await disconnect(45115)

        mock_logger.info.assert_called_with("%s disconnected", 45115)

    @patch("django_peertube_runner_connector.socket.sio", new_callable=AsyncMock)
    async def test_socket_send_available_jobs_ping(self, mock_sio):
        """Known runner should be able to connect to the server."""
        await send_available_jobs_ping_to_runners()

        mock_sio.emit.assert_called_with("available-jobs", namespace="/runners")
