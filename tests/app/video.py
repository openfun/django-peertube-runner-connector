"""Example viewset to start a transcoding using the Django Peertube Runner Connector."""

import logging
import os
from uuid import uuid4

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django_peertube_runner_connector.models import Video
from django_peertube_runner_connector.serializers import RunnerJobSerializer
from django_peertube_runner_connector.storage import VideoNotFoundError, video_storage
from django_peertube_runner_connector.transcode import transcode_video
from django_peertube_runner_connector.transcript import transcript_video
from django_peertube_runner_connector.utils.files import get_lower_case_extension


logger = logging.getLogger(__name__)


class TestVideoViewSet(viewsets.GenericViewSet):
    """Viewset example to start a video transcoding."""

    queryset = Video.objects.all()
    serializer_class = RunnerJobSerializer

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """Endpoint to upload a video file and start transcoding it."""
        uploaded_video_file = request.FILES["videoFile"]
        extension = get_lower_case_extension(uploaded_video_file.name)

        filename = video_storage.save(
            f"video-{uuid4()}/base_video{extension}",
            uploaded_video_file,
        )

        file_name = os.path.basename(filename)  # myvideo.mp4
        file = os.path.splitext(file_name)[0]  # myvideo
        destination = f"{os.path.dirname(filename)}/{file}"
        domain = f"{request.scheme}://{request.get_host()}"

        video = transcode_video(filename, destination, domain)

        return Response(
            {
                "video": {
                    "id": video.id,
                    "uuid": video.uuid,
                }
            }
        )

    @action(detail=False, methods=["post"], url_path="transcode")
    def transcode(self, request):
        """Endpoint to transcode a video file."""
        video_filename = request.data.get("path")
        destination = request.data.get("destination")
        domain = f"{request.scheme}://{request.get_host()}"

        try:
            video = transcode_video(video_filename, destination, domain)
        except VideoNotFoundError:
            return Response(status=404)

        return Response(
            {
                "video": {
                    "id": video.id,
                    "uuid": video.uuid,
                }
            }
        )

    @action(detail=True, methods=["post"], url_path="transcript")
    # pylint: disable=unused-argument
    def transcript(self, request, pk=None):
        """Endpoint to transcript a video file."""
        video = self.get_object()
        destination = request.data.get("destination")
        domain = f"{request.scheme}://{request.get_host()}"

        try:
            transcript_video(destination, domain)
        except VideoNotFoundError:
            return Response(status=404)

        return Response(
            {
                "video": {
                    "id": video.id,
                    "uuid": video.uuid,
                }
            }
        )
