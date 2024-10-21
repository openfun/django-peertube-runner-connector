"""Job handler for vod hls transcoding jobs."""

from __future__ import annotations

import logging
import os
import uuid

from django.urls import reverse

from django_peertube_runner_connector.models import RunnerJob, RunnerJobType, Video
from django_peertube_runner_connector.storage import video_storage
from django_peertube_runner_connector.utils.files import (
    build_new_file,
    generate_hls_video_filename,
    get_hls_resolution_playlist_filename,
    get_video_directory,
)
from django_peertube_runner_connector.utils.transcoding.hls_playlist import (
    on_hls_video_file_transcoding,
    rename_video_file_in_playlist,
)

from .abstract_vod_transcoding_job_handler import AbstractVODTranscodingJobHandler
from .utils import load_runner_video, on_transcoding_ended


logger = logging.getLogger(__name__)

# https://github.com/Chocobozzz/PeerTube/blob/develop/server/core/lib/runners/job-handlers/vod-hls-transcoding-job-handler.ts


class VODHLSTranscodingJobHandler(AbstractVODTranscodingJobHandler):
    """Handler for vod hls transcoding jobs."""

    # pylint: disable=arguments-differ,too-many-positional-arguments
    def create(self, video: Video, resolution, fps, depends_on_runner_job, domain: str):
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
            "output": {
                "resolution": resolution,
                "fps": fps,
            },
        }

        private_payload = {
            "isNewVideo": False,
            "deleteWebVideoFiles": False,
            "videoUUID": str(video.uuid),
        }

        job = self.create_runner_job(
            domain=domain,
            job_type=RunnerJobType.VOD_HLS_TRANSCODING,
            job_uuid=job_uuid,
            payload=payload,
            private_payload=private_payload,
            priority=0,
            depends_on_runner_job=depends_on_runner_job,
        )

        video.increase_or_create_job_info("pendingTranscode")

        return job

    def specific_complete(self, runner_job: RunnerJob, result_payload):
        video = load_runner_video(runner_job)
        if not video:
            return

        # Saving the mp4 file in the video folder and creating the VideoFile object
        uploaded_video_file = result_payload["video_file"]
        resolution = runner_job.payload["output"]["resolution"]

        filename = video_storage.save(
            get_video_directory(
                video,
                generate_hls_video_filename(resolution, video.baseFilename),
            ),
            uploaded_video_file,
        )

        video_file = build_new_file(video=video, filename=filename)

        # Saving the associated m3u8 file
        resolution_playlist_file = result_payload["resolution_playlist_file"]
        resolution_playlist_filename = video_storage.save(
            get_hls_resolution_playlist_filename(video_file.filename),
            resolution_playlist_file,
        )

        # The content of the m3u8 file is not correct, we need to replace the video filename
        # because we gave it a new name
        rename_video_file_in_playlist(
            resolution_playlist_filename, os.path.basename(video_file.filename)
        )

        on_hls_video_file_transcoding(
            video=video,
            video_file=video_file,
        )

        on_transcoding_ended(
            move_video_to_next_state=True,
            video=video,
        )
        logger.info(
            "Runner VOD HLS job %s for %s ended.",
            runner_job.uuid,
            video.uuid,
        )
