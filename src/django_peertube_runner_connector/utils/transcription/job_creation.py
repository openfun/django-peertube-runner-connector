"""Job creation transcription utils"""

from django_peertube_runner_connector.models import Video
from django_peertube_runner_connector.utils.job_handlers.transcription_job_handler import (
    TranscriptionJobHandler,
)


def create_transcription_job(video: Video, domain: str, video_url: str = None):
    """Create a transcription job for a video."""
    transcript_args = {"video": video, "domain": domain}
    if video_url:
        transcript_args["video_url"] = video_url
    TranscriptionJobHandler().create(**transcript_args)
