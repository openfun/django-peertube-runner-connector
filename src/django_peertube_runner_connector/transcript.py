"""Base function to start the transcription process."""
import logging

from django_peertube_runner_connector.models import Video
from django_peertube_runner_connector.utils.transcription.job_creation import (
    create_transcription_job,
)


logger = logging.getLogger(__name__)


def transcript_video(destination: str, domain: str):
    """
    Transcripts a video file to a specified destination.

    Parameters:
        destination (str): The destination directory used to find the video file,
            and to store the transcription file.
        domain (str): The domain name used to construct the download URL

    Raises:
        VideoNotFoundError: If the video file does not exist.
    """

    video = Video.objects.get(directory=destination)

    return create_transcription_job(video=video, domain=domain)
