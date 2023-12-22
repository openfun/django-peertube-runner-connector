"""Tests for the "socket.py" file of the django_peertube_runner_connector app"""
from unittest import mock

from django.test import TestCase, override_settings

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

    @mock.patch("django_peertube_runner_connector.socket.logger")
    @mock.patch("django_peertube_runner_connector.socket.sio")
    async def test_socket_connect(self, _mock_sio, mock_logger):
        """Known runner should be able to connect to the server."""
        await connect(45115, None, {"runnerToken": self.runner.runnerToken})

        mock_logger.info.assert_called_with(
            "Runner with token %s connected with sid %s", self.runner.runnerToken, 45115
        )

    @mock.patch("django_peertube_runner_connector.socket.logger")
    @mock.patch(
        "django_peertube_runner_connector.socket.sio", new_callable=mock.AsyncMock
    )
    async def test_socket_connect_wrong_runner_token(self, mock_sio, mock_logger):
        """Known runner should be able to connect to the server."""
        await connect(45115, None, {"runnerToken": "Wrong Runner Token"})

        mock_logger.info.assert_called_with(
            "Runner with token %s not found", "Wrong Runner Token"
        )
        mock_sio.disconnect.assert_called_with(45115, namespace="/runners")

    @mock.patch("django_peertube_runner_connector.socket.logger")
    @mock.patch(
        "django_peertube_runner_connector.socket.sio", new_callable=mock.AsyncMock
    )
    async def test_socket_disconnect(self, _mock_sio, mock_logger):
        """Known runner should be able to connect to the server."""
        await disconnect(45115)

        mock_logger.info.assert_called_with("%s disconnected", 45115)

    @mock.patch(
        "django_peertube_runner_connector.socket.sio", new_callable=mock.AsyncMock
    )
    async def test_socket_send_available_jobs_ping_with_no_manager(self, mock_sio):
        """server with no manager should directly use sio to emit a message."""
        await send_available_jobs_ping_to_runners()

        mock_sio.emit.assert_called_with("available-jobs", namespace="/runners")

    @mock.patch(
        "django_peertube_runner_connector.socket.sio", new_callable=mock.AsyncMock
    )
    @override_settings(
        DJANGO_PEERTUBE_RUNNER_CONNECTOR_SENTINELS=[("localhost", 26379)]
    )
    @override_settings(DJANGO_PEERTUBE_RUNNER_CONNECTOR_SENTINELS_MASTER="mymaster")
    async def test_socket_send_available_jobs_ping_with_sentinel_manager(
        self, _mock_sio
    ):
        """
        When a sentinel is used as client manager, this one should be used to emit a message
        """
        mock_manager = mock.AsyncMock()
        mock_manager.emit = mock.AsyncMock()

        with mock.patch(
            "django_peertube_runner_connector.socketio.manager.AsyncSentinelRedisManager",
            return_value=mock_manager,
        ):
            await send_available_jobs_ping_to_runners()

        mock_manager.emit.assert_awaited_once_with(
            "available-jobs", data=None, namespace="/runners"
        )

    @mock.patch(
        "django_peertube_runner_connector.socket.sio", new_callable=mock.AsyncMock
    )
    @override_settings(
        DJANGO_PEERTUBE_RUNNER_CONNECTOR_REDIS="redis://localhost:6379/0"
    )
    async def test_socket_send_available_jobs_ping_with_redis_manager(self, _mock_sio):
        """When redis is used as client manager, this one should be used to emit a message"""
        mock_manager = mock.AsyncMock()
        mock_manager.emit = mock.AsyncMock()

        with mock.patch(
            "django_peertube_runner_connector.socketio.manager.AsyncRedisManager",
            return_value=mock_manager,
        ):
            await send_available_jobs_ping_to_runners()

        mock_manager.emit.assert_awaited_once_with(
            "available-jobs", data=None, namespace="/runners"
        )
