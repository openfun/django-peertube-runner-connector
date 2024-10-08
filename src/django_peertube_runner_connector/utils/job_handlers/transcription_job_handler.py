"""Job handler for transcription jobs."""

import logging
import uuid

from django.urls import reverse

from django_peertube_runner_connector.models import (
    RunnerJob,
    RunnerJobState,
    RunnerJobType,
    Video,
    VideoJobInfoColumnType,
)
from django_peertube_runner_connector.storage import video_storage
from django_peertube_runner_connector.utils.files import (
    generate_transcription_filename,
    get_video_directory,
)

from .abstract_job_handler import AbstractJobHandler
from .utils import (
    is_transcription_language_valid,
    load_runner_video,
    on_transcription_ended,
    on_transcription_error,
)


logger = logging.getLogger(__name__)

# https://github.com/Chocobozzz/PeerTube/blob/develop/server/core/lib/runners/job-handlers/transcription-job-handler.ts


class TranscriptionJobHandler(AbstractJobHandler):
    """Handler for transcription jobs."""

    def is_abort_supported(self):
        """Return True if the job supports aborting."""
        return True

    def specific_abort(self, runner_job: RunnerJob):
        """Abort the runner job."""

    def specific_update(self, runner_job: RunnerJob, update_payload=None):
        """Update the runner job with the payload."""

    def specific_error(
        self, runner_job: RunnerJob, message: str, next_state: RunnerJobState
    ):
        """Handle the error."""
        if next_state != RunnerJobState.ERRORED:
            return

        video = load_runner_video(runner_job)
        if not video:
            return

        video.decrease_job_info(VideoJobInfoColumnType.PENDING_TRANSCRIPT)
        on_transcription_error(video)

    def specific_cancel(self, runner_job: RunnerJob):
        """Cancel the runner job."""
        video = load_runner_video(runner_job)
        if not video:
            return

        video.decrease_job_info(VideoJobInfoColumnType.PENDING_TRANSCRIPT)

    # pylint: disable=arguments-differ
    def create(self, video: Video, domain: str, video_url: str = None):
        """Create a transcription job."""
        job_uuid = uuid.uuid4()

        payload = {
            "input": {
                "videoFileUrl": domain
                + reverse(
                    "runner-jobs-download_video_file",
                    args=(
                        video.uuid,
                        job_uuid,
                    ),
                ),
            },
        }

        if video_url:
            payload["input"]["videoFileUrl"] = video_url

        private_payload = {
            "videoUUID": str(video.uuid),
        }

        job = self.create_runner_job(
            domain=domain,
            job_type=RunnerJobType.VIDEO_TRANSCRIPTION,
            job_uuid=job_uuid,
            payload=payload,
            private_payload=private_payload,
            priority=0,
            depends_on_runner_job=None,
        )

        video.increase_or_create_job_info(VideoJobInfoColumnType.PENDING_TRANSCRIPT)

        return job

    def specific_complete(self, runner_job: RunnerJob, result_payload):
        # https://github.com/Chocobozzz/PeerTube/blob/develop/server/core/lib/runners/job-handlers/transcription-job-handler.ts
        video = load_runner_video(runner_job)
        if not video:
            return

        language = result_payload["inputLanguage"]

        if not is_transcription_language_valid(language):
            logger.error(
                "Invalid transcription language %s for video %s.", language, video.uuid
            )
            return

        filename = video_storage.save(
            get_video_directory(
                video,
                generate_transcription_filename(language, video.baseFilename),
            ),
            result_payload["vttFile"],
        )

        video.language = language
        video.transcriptFileName = filename
        video.save()

        on_transcription_ended(video, language, filename)
