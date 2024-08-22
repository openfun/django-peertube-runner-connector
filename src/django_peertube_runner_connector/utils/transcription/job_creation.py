"""Job creation transcription utils"""
from django_peertube_runner_connector.models import Video
from django_peertube_runner_connector.utils.job_handlers.transcription_job_handler import (
    TranscriptionJobHandler,
)


def create_transcription_job(video: Video, domain: str):
    """Create a transcription job for a video."""
    TranscriptionJobHandler().create(video=video, domain=domain)
