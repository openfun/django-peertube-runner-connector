"""Utils functions to handle video states."""

from __future__ import annotations

import logging

from django.conf import settings
from django.utils.module_loading import import_string

from django_peertube_runner_connector.models import Video, VideoState


logger = logging.getLogger(__name__)


def transcoding_ended(video: Video):
    """Call the transcoding_ended callback if it exists."""
    if callback_path := settings.TRANSCODING_ENDED_CALLBACK_PATH:
        try:
            callback = import_string(callback_path)
            callback(video)
        except ImportError:
            logger.error("Error importing transcoding_ended callback.")


def build_next_video_state(current_state: VideoState = None):
    """Build the next video state."""
    if current_state == VideoState.PUBLISHED:
        raise ValueError("Video is already in its final state")

    if current_state not in [
        VideoState.TO_EDIT,
        VideoState.TO_TRANSCODE,
        VideoState.TO_MOVE_TO_EXTERNAL_STORAGE,
    ]:
        return VideoState.TO_TRANSCODE

    return VideoState.PUBLISHED


def move_to_next_state(video: Video):
    """Move video to the next state."""
    # Maybe the video changed in database, refresh it
    video.refresh_from_db()

    # Already in its final state
    if video.state == VideoState.PUBLISHED:
        transcoding_ended(video)
        return

    if build_next_video_state(video.state) == VideoState.PUBLISHED:
        move_to_published_state(video)


def move_to_failed_transcoding_state(video: Video):
    """Move video to the failed transcoding state."""
    if video.state != VideoState.TRANSCODING_FAILED:
        video.state = VideoState.TRANSCODING_FAILED
        video.save()
        transcoding_ended(video)


def move_to_published_state(video: Video):
    """Move video to the published state."""
    logger.info("Publishing video %s.", video.uuid)

    video.state = VideoState.PUBLISHED
    video.save()
    transcoding_ended(video)
