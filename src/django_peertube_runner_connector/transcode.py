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


def _process_transcoding(video: Video, video_path: str, build_video_url):
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
        build_video_url=build_video_url,
    )


def transcode_video(filename: str, request):
    """
    Transcodes a video file.

    Args:
        filename (str): The name of the video file.
        request: The HTTP request associated with the transcoding process.

    Returns:
        Video: The transcoded video object.

    Raises:
        VideoNotFoundError: If the video file does not exist.
    """
    if not video_storage.exists(filename):
        raise VideoNotFoundError("Video file does not exist.")

    video = Video.objects.create(
        state=build_next_video_state(),
        directory=os.path.dirname(filename),
    )

    def build_video_url(job_uuid, video_uuid):
        """Return an api endpoint to download the video file."""
        return request.build_absolute_uri(
            reverse("runner-jobs-download_video_file", args=(job_uuid, video_uuid))
        )

    _process_transcoding(
        video=video, video_path=filename, build_video_url=build_video_url
    )

    return video
