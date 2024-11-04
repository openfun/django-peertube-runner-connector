"""API Endpoints for Runner Jobs with Django RestFramework viewsets."""

import logging
from urllib.parse import urlparse
from uuid import uuid4

from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django_peertube_runner_connector.models import (
    Runner,
    RunnerJob,
    RunnerJobState,
    Video,
)
from django_peertube_runner_connector.serializers import (
    RunnerJobSerializer,
    SimpleRunnerJobSerializer,
)
from django_peertube_runner_connector.storage import video_storage
from django_peertube_runner_connector.utils.job_handlers.get_job_handler import (
    get_runner_job_handler_class,
)
from django_peertube_runner_connector.utils.request import get_client_ip


logger = logging.getLogger(__name__)


class RunnerJobViewSet(viewsets.GenericViewSet):
    """Viewset for the API of the runner job object."""

    queryset = RunnerJob.objects.all()
    serializer_class = RunnerJobSerializer
    lookup_field = "uuid"

    def _get_runner_from_token(self, request):
        """Get the runner from the request."""
        try:
            runner = Runner.objects.get(runnerToken=request.data.get("runnerToken", ""))
        except Runner.DoesNotExist as runner_not_found:
            raise Http404("Unknown runner token") from runner_not_found
        return runner

    def _get_job_from_uuid(self, uuid):
        """Get the job from the uuid."""
        try:
            runner = self.get_queryset().get(uuid=uuid)
        except RunnerJob.DoesNotExist as job_not_found:
            raise Http404("Unknown job uuid") from job_not_found
        return runner

    def _get_video_from_uuid(self, uuid):
        """Get the video from the uuid."""
        try:
            runner = Video.objects.get(uuid=uuid)
        except Video.DoesNotExist as video_not_found:
            raise Http404("Unknown video uuid") from video_not_found
        return runner

    @action(detail=False, methods=["post"], url_path="request")
    def request_runner_job(self, request):
        """Endpoint returning a list of available jobs."""
        runner = self._get_runner_from_token(request)
        jobs = RunnerJob.objects.list_available_jobs(request.data.get("jobTypes"))

        runner.update_last_contact(get_client_ip(request))

        serializer = SimpleRunnerJobSerializer(jobs, many=True)

        logger.debug("Runner %s requests for a job.", runner.name)
        return Response({"availableJobs": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="accept")
    def accept_runner_job(self, request, uuid=None):
        """Endpoint attributing a job to a runner."""
        runner = self._get_runner_from_token(request)
        job = self._get_job_from_uuid(uuid)
        updated_rows = RunnerJob.objects.filter(
            uuid=uuid, state=RunnerJobState.PENDING
        ).update(state=RunnerJobState.PROCESSING)

        if updated_rows == 0:
            return Response(
                "This job is not in pending state anymore",
                status=status.HTTP_409_CONFLICT,
            )

        job.refresh_from_db()
        job.processingJobToken = "ptrjt-" + str(uuid4())
        job.startedAt = timezone.now()
        job.runner = runner
        job.save()

        runner.update_last_contact(get_client_ip(request))

        logger.info(
            "Remote runner %s has accepted job %s (%s)",
            runner.name,
            job.uuid,
            job.type,
        )

        serializer = self.get_serializer(job)
        return Response({"job": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="abort")
    def abort_runner_job(self, request, uuid=None):
        """Endpoint to aborting a job."""
        runner = self._get_runner_from_token(request)
        job = self._get_job_from_uuid(uuid)
        job.failures += 1

        logger.info(
            "Remote runner %s  is aborting job %s (%s)", runner.name, job.uuid, job.type
        )

        runner_job_handler = get_runner_job_handler_class(job)
        runner_job_handler().abort(runner_job=job)

        runner.update_last_contact(get_client_ip(request))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="error")
    def error_runner_job(self, request, uuid=None):
        """Endpoint to signal an error with a job."""
        runner = self._get_runner_from_token(request)
        message = request.data.get("message")
        job = self._get_job_from_uuid(uuid)
        job.failures += 1

        logger.error(
            "Remote runner %s had an error with job %s (%s): %s",
            runner.name,
            job.uuid,
            job.type,
            message,
        )

        runner_job_handler = get_runner_job_handler_class(job)
        runner_job_handler().error(runner_job=job, message=message)

        runner.update_last_contact(get_client_ip(request))

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="update")
    def update_runner_job(self, request, uuid=None):
        """Endpoint to update a job."""
        runner = self._get_runner_from_token(request)
        job = self._get_job_from_uuid(uuid)

        runner_job_handler = get_runner_job_handler_class(job)

        runner_job_handler().update(
            runner_job=job, progress=request.data.get("progress")
        )

        runner.update_last_contact(get_client_ip(request))

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="success")
    def success_runner_job(self, request, uuid=None):
        """Endpoint to signal the job as successfully completed."""
        runner = self._get_runner_from_token(request)
        job = self._get_job_from_uuid(uuid)

        runner_job_handler = get_runner_job_handler_class(job)

        if "transcription" in job.type:
            result = {
                "inputLanguage": request.data.get("payload[inputLanguage]", None),
                "vttFile": request.data.get("payload[vttFile]", None),
            }
        else:
            result = {
                "video_file": request.data.get("payload[videoFile]", None),
                "resolution_playlist_file": request.data.get(
                    "payload[resolutionPlaylistFile]", None
                ),
            }

        runner_job_handler().complete(runner_job=job, result_payload=result)

        runner.update_last_contact(get_client_ip(request))

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["post"],
        url_path="files/videos/(?P<video_id>[^/.]+)/(?P<job_id>[^/.]+)/max-quality",
        url_name="download_video_file",
    )
    def download_video_file(self, request, video_id=None, job_id=None):
        """Endpoint to download a video file."""
        runner = self._get_runner_from_token(request)
        video = self._get_video_from_uuid(video_id)
        job = self._get_job_from_uuid(job_id)

        logger.info(
            "Get max quality file of video %s for runner %s",
            video.uuid,
            runner.name,
        )

        video_file = video.get_max_quality_file()
        video_url = video_storage.url(video_file.filename)
        if not urlparse(video_url).scheme and job.domain:
            video_url = job.domain + video_url
        return redirect(video_url, permanent=True)
