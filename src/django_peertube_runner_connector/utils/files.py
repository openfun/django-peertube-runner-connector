"""File utilities for the django-peertube-runner-connector app."""

import logging
import os
import re
from uuid import uuid4

import ffmpeg

from django_peertube_runner_connector.models import (
    Video,
    VideoFile,
    VideoJobInfo,
    VideoResolution,
)
from django_peertube_runner_connector.storage import video_storage

from .ffprobe import (
    build_file_metadata,
    get_video_stream_dimensions_info,
    get_video_stream_fps,
    is_audio_file,
)


logger = logging.getLogger(__name__)


def get_video_directory(video: Video, suffix: str = ""):
    """Return a video directory."""
    return f"{video.directory}/{suffix}"


def get_lower_case_extension(path: str):
    """Return the lower case extension of a file."""
    return os.path.splitext(path)[1].lower()


def generate_web_video_filename(resolution: int, extname: str):
    """Generate a filename for a web video."""
    return str(uuid4()) + "-" + str(resolution) + extname


def generate_hls_video_filename(resolution: int, basename: str = None):
    """Generate a filename for a hls video."""
    basename = basename or str(uuid4())

    return f"{basename}-{str(resolution)}-fragmented.mp4"


def generate_transcription_filename(language: str, basename: str = None):
    """Generate a filename for a transcription."""
    basename = basename or str(uuid4())

    return f"{basename}-{language}.vtt"


def get_hls_resolution_playlist_filename(video_filename: str):
    """Return the hls resolution playlist filename."""
    return (
        re.sub(r"-fragmented\.mp4$", "", video_filename, flags=re.IGNORECASE) + ".m3u8"
    )


def generate_hls_master_playlist_filename(is_live: bool = False):
    """Return the hls master playlist filename."""
    if is_live:
        return "master.m3u8"

    return str(uuid4()) + "-master.m3u8"


def build_new_file(video: Video, filename: str, existing_probe=None):
    """Create a new video_file associated to a file."""
    if not existing_probe:
        url = video_storage.url(filename)
        probe = ffmpeg.probe(url)
    else:
        url = ""
        probe = existing_probe

    size = int(probe["format"]["size"])

    if is_audio_file(probe):
        fps = -1
        resolution = VideoResolution.H_NOVIDEO
    else:
        fps = get_video_stream_fps(probe)
        resolution = get_video_stream_dimensions_info(url, probe)["resolution"]

    video_file = VideoFile.objects.create(
        extname=get_lower_case_extension(filename),
        size=size,
        metadata=build_file_metadata(probe=probe),
        resolution=resolution,
        filename=filename,
        fps=fps,
        video=video,
    )

    return video_file


def delete_temp_file(video: Video, filename: str):
    """Delete a temporary file."""
    # check if the temp file is still needed by a transcoding job
    if VideoJobInfo.objects.filter(video=video, pendingTranscode__gt=0).exists():
        return

    try:
        temp_video_file = VideoFile.objects.get(
            video=video,
            streamingPlaylist=None,
            extname="",
            filename=filename,
        )

        temp_video_file.remove_web_video_file()
        temp_video_file.delete()
    except VideoFile.DoesNotExist:
        logger.warning(
            "No video file found for video %s with filename %s",
            video.id,
            filename,
        )
