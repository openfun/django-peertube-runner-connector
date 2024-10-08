"""Base function to start the transcoding process."""

import logging

import ffmpeg

from django_peertube_runner_connector.models import Video
from django_peertube_runner_connector.storage import VideoNotFoundError, video_storage
from django_peertube_runner_connector.utils.ffprobe import get_video_stream_duration
from django_peertube_runner_connector.utils.files import build_new_file
from django_peertube_runner_connector.utils.thumbnail import build_video_thumbnails
from django_peertube_runner_connector.utils.transcoding.job_creation import (
    create_transcoding_jobs,
)
from django_peertube_runner_connector.utils.video_state import build_next_video_state


logger = logging.getLogger(__name__)


def _process_transcoding(video: Video, video_path: str, domain: str):
    """
    Create a video_file, thumbnails and transcoding jobs for a video.
    The request will be used to build the video download url.
    """
    url = video_storage.url(video_path)
    probe = ffmpeg.probe(url)

    video_file = build_new_file(video=video, filename=video_path, existing_probe=probe)

    video.duration = get_video_stream_duration(video_path, existing_probe=probe)

    video.thumbnailFilename = build_video_thumbnails(video=video, video_file=video_file)
    video.save()

    logger.info("Video at %s and uuid %s created.", video_path, video.uuid)

    create_transcoding_jobs(
        video=video,
        video_file=video_file,
        existing_probe=probe,
        domain=domain,
    )


def transcode_video(
    file_path: str, destination: str, domain: str, base_name: str = None
):
    """
    Transcodes a video file to a specified destination.

    Parameters:
        file_path (str): The path to the video file.
        destination (str): The destination directory for the transcoded video.
        domain (str): The domain name used to construct the download URL for peerTube runners.
        base_name (str, optional): The base name for the transcoded video.

    Returns:
        Video: The transcoded video object.

    Raises:
        VideoNotFoundError: If the video file does not exist.
    """
    if not video_storage.exists(file_path):
        raise VideoNotFoundError("Video file does not exist.")

    video = Video.objects.create(
        state=build_next_video_state(),
        directory=destination,
        baseFilename=base_name,
    )

    _process_transcoding(video=video, video_path=file_path, domain=domain)

    return video
