"""Module to manage a sentinel redis manager sor adyncio."""

from django.conf import settings

from redis.asyncio.sentinel import Sentinel
from socketio import AsyncRedisManager


def get_client_manager(write_only=False):
    """
    A factory responsible a correct redis manager based on the settings defined in the project.

    To return a sentinel redis manager, the settings DJANGO_PEERTUBE_RUNNER_CONNECTOR_SENTINELS
    and DJANGO_PEERTUBE_RUNNER_CONNECTOR_SENTINELS_MASTER must be defined.

    To return a redis manager, the settings DJANGO_PEERTUBE_RUNNER_CONNECTOR_REDIS must be defined.

    If none of these settings are defined, no manager will be created and the value None
    will be return.
    """
    client_manager = None
    if hasattr(settings, "DJANGO_PEERTUBE_RUNNER_CONNECTOR_SENTINELS"):
        client_manager = AsyncSentinelRedisManager(
            sentinels=settings.DJANGO_PEERTUBE_RUNNER_CONNECTOR_SENTINELS,
            master=settings.DJANGO_PEERTUBE_RUNNER_CONNECTOR_SENTINELS_MASTER,
            write_only=write_only,
        )

    if hasattr(settings, "DJANGO_PEERTUBE_RUNNER_CONNECTOR_REDIS"):
        client_manager = AsyncRedisManager(
            settings.DJANGO_PEERTUBE_RUNNER_CONNECTOR_REDIS, write_only=write_only
        )

    return client_manager


class AsyncSentinelRedisManager(AsyncRedisManager):
    """Redis sentinel based client manager for asyncio servers.

    This class implements a Redis sentinel backend for event sharing across multiple
    processes.

    To use a Redis backend, initialize the :class:`AsyncServer` instance as
    follows::

        sentinels = [('localhost', 26379)]
        master = 'mymaster'
        client_manager = AsyncSentinelRedisManager(
            sentinels=sentinels,
            master=master
        )
        server = socketio.AsyncServer(client_manager=client_manager)

    :param sentinels: A list of sentinel nodes.
                      Each node is represented by a pair (hostname, port).
                      Default: [('localhost', 26379)]
    :param master: The master sentinel name. Default: mymaster
    :param channel: The channel name on which the server sends and receives
                    notifications. Must be the same in all the servers.
    :param write_only: If set to ``True``, only initialize to emit events. The
                       default of ``False`` initializes the class for emitting
                       and receiving.
    :param logger: To enable logging set to ``True`` or pass a logger object to
                   use. To disable logging set to ``False``. Note that fatal
                   errors are logged even when ``logger`` is ``False``.
    :param redis_options: additional keyword arguments to be passed to
                          ``aioredis.from_url()``.
    """

    name = "aioredis"

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        sentinels=None,
        master="mymaster",
        channel="socketio",
        write_only=False,
        logger=None,
        redis_options=None,
    ):
        if sentinels is None:
            sentinels = [("localhost", 26379)]
        self.sentinels = sentinels
        self.master = master
        self.redis_options = redis_options
        self._redis_connect()
        super().__init__(channel=channel, write_only=write_only, logger=logger)

    def _redis_connect(self):
        sentinel = Sentinel(self.sentinels, sentinel_kwargs=self.redis_options)
        self.redis = sentinel.master_for(self.master)
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
