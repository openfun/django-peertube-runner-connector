"""Base class for VOD transcoding job handlers."""

from __future__ import annotations

import logging

from django_peertube_runner_connector.models import RunnerJob, RunnerJobState
from django_peertube_runner_connector.utils.job_handlers.abstract_job_handler import (
    AbstractJobHandler,
)
from django_peertube_runner_connector.utils.job_handlers.utils import load_runner_video
from django_peertube_runner_connector.utils.video_state import (
    move_to_failed_transcoding_state,
    move_to_next_state,
)


logger = logging.getLogger(__name__)


class AbstractVODTranscodingJobHandler(AbstractJobHandler):
    """Base class for VOD transcoding job handlers."""

    def is_abort_supported(self):
        """Abort is supported for VOD transcoding jobs."""
        return True

    def specific_update(
        self,
        runner_job: RunnerJob,
        update_payload=None,
    ):
        """No specific update for VOD transcoding jobs."""

    def specific_abort(self, runner_job: RunnerJob):
        """No specific abort for VOD transcoding jobs."""

    def specific_error(self, runner_job, message, next_state):
        """Update related video job info to register the error state."""
        if next_state != RunnerJobState.ERRORED:
            return

        video = load_runner_video(runner_job)
        if not video:
            return

        move_to_failed_transcoding_state(video)
        video.decrease_job_info("pendingTranscode")

    def specific_cancel(self, runner_job):
        """
        Checking if all related video job info has been ended and if so,
        move it to its next state.
        """
        video = load_runner_video(runner_job)
        if not video:
            return

        pending = video.decrease_job_info("pendingTranscode")

        logger.debug("Pending transcode decreased to %s after cancel", pending)

        if pending == 0:
            logger.info(
                "All transcoding jobs of %s have been "
                "processed or canceled, moving it to its next state",
                video.uuid,
            )

            move_to_next_state(video=video)
