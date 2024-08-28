"""Base function to start the transcription process."""

import logging

from django_peertube_runner_connector.models import Video, VideoState
from django_peertube_runner_connector.utils.transcription.job_creation import (
    create_transcription_job,
)


logger = logging.getLogger(__name__)


def transcript_video(destination: str, domain: str, video_url: str = None):
    """
    Transcripts a video file to a specified destination.

    Parameters:
        destination (str): The destination directory used to find the video file,
            and to store the transcription file.
        domain (str): The domain name used to construct the download URL.
        video_url (str): The video URL to transcript.
    """

    video, _ = Video.objects.get_or_create(
        directory=destination,
        defaults={
            "state": VideoState.PUBLISHED,
        },
    )

    transcript_args = {"video": video, "domain": domain}
    if video_url:
        transcript_args["video_url"] = video_url
    return create_transcription_job(**transcript_args)
