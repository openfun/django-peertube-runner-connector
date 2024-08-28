"""Utils functions related to job handlers."""

from __future__ import annotations

import logging

from django.conf import settings
from django.utils.module_loading import import_string

from django_peertube_runner_connector.models import RunnerJob, Video
from django_peertube_runner_connector.utils.video_state import move_to_next_state


logger = logging.getLogger(__name__)


def load_runner_video(runner_job: RunnerJob):
    """Get a Video object from a payload return by the PeerTube runner."""
    video_uuid = runner_job.privatePayload["videoUUID"]

    try:
        video = Video.objects.get(uuid=video_uuid)
    except Video.DoesNotExist:
        logger.info(
            "Video %s does not exist anymore after transcoding runner job.", video_uuid
        )
        return None

    return video


def on_transcoding_ended(video: Video, move_video_to_next_state: bool):
    """Handle transcoding ended event."""
    video.decrease_job_info("pendingTranscode")

    if move_video_to_next_state:
        move_to_next_state(video=video)


def is_transcription_language_valid(language):
    """Check if a transcription language is valid."""
    languages = getattr(settings, "ALL_LANGUAGES", settings.LANGUAGES)
    return language in dict(languages)


def on_transcription_ended(video: Video, language: str, vtt_path: str):
    """Handle transcription ended event."""

    logger.info("Transcription ended for %s.", video.uuid)

    if not is_transcription_language_valid(language):
        logger.error(
            "Invalid transcription language %s for video %s.", language, video.uuid
        )
        return

    if not video.language:
        video.language = language

    video.transcriptFileName = vtt_path
    video.save()

    if callback_path := settings.TRANSCRIPTION_ENDED_CALLBACK_PATH:
        try:
            callback = import_string(callback_path)
            callback(video, language, vtt_path)
        except ImportError:
            logger.error("Error importing transcription_ended callback.")
    else:
        logger.info("No transcription_ended callback defined for video %s.", video.uuid)


def on_transcription_error(video: Video):
    """Handle transcription error event."""

    logger.error("Transcription error for %s.", video.uuid)

    if callback_path := settings.TRANSCRIPTION_ERROR_CALLBACK_PATH:
        try:
            callback = import_string(callback_path)
            callback(video)
        except ImportError:
            logger.info("Error importing transcription_error callback.")
    else:
        logger.info("No transcription_error callback defined for video %s.", video.uuid)


# def on_vod_web_video_or_audio_merge_transcoding_job(
#     video: Video, video_file_path, private_payload
# ):
#     video_file = build_new_file(video=video, path=video_file_path, mode="web-video")

#     video_output_path = join(dirname(video_file_path), video_file.filename)
#     move(video_file_path, video_output_path)

#     on_web_video_file_transcoding(
#         video=video, video_file=video_file, video_output_path=video_output_path
#     )

#     on_transcoding_ended(
#         is_new_video=private_payload["isNewVideo"],
#         move_video_to_next_state=True,
#         video=video,
#     )

#     logger.info(
#         "VOD web video or audio merge transcoding job completed for video %s.",
#         video.uuid,
#     )


# def on_web_video_file_transcoding(
#     video: Video, video_file: VideoFile, video_output_path, was_audio_file=False
# ):
#     video.refresh_from_db()

#     output_path = "get_fs_video_file_output_path(video_file)"

#     probe = ffmpeg.probe(video_output_path)

#     stats = os.stat(video_output_path)

#     fps = get_video_stream_fps(probe)
#     metadata = build_file_metadata(probe=probe)

#     move(video_output_path, output_path)

#     video_file.size = stats.st_size
#     video_file.fps = fps
#     video_file.metadata = metadata

#     old_file = VideoFile.objects.filter(
#         video=video, fps=video_file.fps, resolution=video_file.resolution
#     ).first()
#     if old_file:
#         old_file.remove_web_video_file()

#     video_file.save()

#     return {"video": video, "videoFile": video_file}
