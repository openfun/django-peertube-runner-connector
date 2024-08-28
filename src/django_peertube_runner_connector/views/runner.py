"""API Endpoints for Runners with Django RestFramework viewsets."""

from datetime import timezone as tz
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django_peertube_runner_connector.forms import RunnerForm
from django_peertube_runner_connector.models import Runner, RunnerRegistrationToken
from django_peertube_runner_connector.serializers import RunnerSerializer
from django_peertube_runner_connector.utils.request import get_client_ip


class RunnerViewSet(viewsets.GenericViewSet):
    """Viewset for the API of the runner object."""

    queryset = Runner.objects.all()
    serializer_class = RunnerSerializer

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        """Register a PeerTube runner."""
        try:
            form = RunnerForm(request.data)
            runner = form.save(commit=False)
        except ValueError:
            return Response({"errors": [dict(form.errors)]}, status=400)

        try:
            registration_token = RunnerRegistrationToken.objects.get(
                registrationToken=request.data.get("registrationToken", "")
            )
        except ObjectDoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"message": "Registration token is invalid"},
            )

        runner.runnerToken = f"ptrt-{str(uuid.uuid4())}"
        runner.ip = get_client_ip(request)
        runner.runnerRegistrationToken = registration_token
        runner.lastContact = timezone.datetime.now(tz=tz.utc)
        runner.save()

        serializer = self.get_serializer(runner)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="unregister")
    def unregister(self, request):
        """Unregister a PeerTube runner."""
        try:
            runner = Runner.objects.get(runnerToken=request.data.get("runnerToken", ""))
        except ObjectDoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"message": "Registration token is invalid"},
            )
        runner.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
