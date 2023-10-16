"""Base function to start the transcoding process."""
import logging
import os

from django.urls import reverse

import ffmpeg

from django_peertube_runner_connector.models import Video
from django_peertube_runner_connector.storage import video_storage
from django_peertube_runner_connector.utils.ffprobe import get_video_stream_duration
from django_peertube_runner_connector.utils.files import build_new_file
from django_peertube_runner_connector.utils.thumbnail import build_video_thumbnails
from django_peertube_runner_connector.utils.transcoding.job_creation import (
    create_transcoding_jobs,
)
from django_peertube_runner_connector.utils.video_state import build_next_video_state


logger = logging.getLogger(__name__)


class VideoNotFoundError(Exception):
    """Exception class for when transcoding cannot find a video in the storage."""


def _process_transcoding(video: Video, video_path: str, video_url):
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
        video_url=video_url,
    )


def transcode_video(file_path: str, domain: str):
    """
    Transcodes a video file.

    Args:
        file_path (str): The name of the video file.
        domain (str): The domain that will be used to download the video.

    Returns:
        Video: The transcoded video object.

    Raises:
        VideoNotFoundError: If the video file does not exist.
    """
    if not video_storage.exists(file_path):
        raise VideoNotFoundError("Video file does not exist.")


    video = Video.objects.create(
        state=build_next_video_state(),
        # myvideo-1696602697/
        directory=os.path.dirname(file_path)
    )

    video_url = domain + reverse("runner-jobs-download_video_file", args=(video.uuid,))

    _process_transcoding(video=video, video_path=file_path, video_url=video_url)

    return video
