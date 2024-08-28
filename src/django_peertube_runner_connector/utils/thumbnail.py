"""Thumbnail utilities."""

import tempfile

import ffmpeg

from django_peertube_runner_connector.models import Video, VideoFile
from django_peertube_runner_connector.storage import video_storage

from .files import get_video_directory


def build_video_thumbnails(video=Video, video_file=VideoFile):
    """Create a video thumbnails with ffmpeg and save it to a file."""
    video_url = video_storage.url(video_file.filename)
    thumbnail_filename = get_video_directory(video, "thumbnail.jpg")

    with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
        output_path = temp_file.name

        input_stream = ffmpeg.input(video_url)

        output_stream = ffmpeg.filter(
            input_stream,
            "select",
            "gte(n, 0)",
        ).output(output_path, vframes=1)

        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        with open(output_path, "rb") as thumbnail_file:
            thumbnail_filename = video_storage.save(thumbnail_filename, thumbnail_file)

        return thumbnail_filename
