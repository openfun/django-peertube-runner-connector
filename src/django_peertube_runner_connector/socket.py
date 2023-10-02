"""SocketIO server for the Django Peertube Runner Connector app."""
import logging

from asgiref.sync import sync_to_async
import socketio

from django_peertube_runner_connector.models import Runner


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

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
    await sio.emit("available-jobs", namespace="/runners")
