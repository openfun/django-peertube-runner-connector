"""SocketIO server for the Django Peertube Runner Connector app."""

import logging

from asgiref.sync import sync_to_async
import socketio

from django_peertube_runner_connector.models import Runner
from django_peertube_runner_connector.socketio.manager import get_client_manager


sio_logger = logging.getLogger(f"{__name__}.asyncio")
engineio_logger = logging.getLogger(f"{__name__}.engineio")

client_manager = get_client_manager()

sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=client_manager,
    cors_allowed_origins="*",
    logger=sio_logger,
    engineio_logger=engineio_logger,
)

logger = logging.getLogger(__name__)


@sio.on("connect", namespace="/runners")
async def connect(sid, _env, auth):
    """Function called when a runner connects."""
    runner_token = auth.get("runnerToken", None)

    if (
        runner_token
        and await sync_to_async(
            Runner.objects.filter(runnerToken=runner_token).exists
        )()
    ):
        logger.info("Runner with token %s connected with sid %s", runner_token, sid)
    else:
        logger.info("Runner with token %s not found", runner_token)
        await sio.disconnect(sid, namespace="/runners")


@sio.on("disconnect", namespace="/runners")
async def disconnect(sid):
    """Function called when a runner disconnects."""
    logger.info("%s disconnected", sid)


async def send_available_jobs_ping_to_runners():
    """Send an "available jobs" ping to the runners."""
    logger.info("Available jobs ping sent to runners")
    manager = get_client_manager(write_only=True)
    if manager:
        await manager.emit("available-jobs", data=None, namespace="/runners")
    else:
        await sio.emit("available-jobs", namespace="/runners")
