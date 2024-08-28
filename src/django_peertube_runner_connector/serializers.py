"""Serializers for the Django Peertube Runner Connector app."""

from rest_framework import serializers

from django_peertube_runner_connector.models import Runner, RunnerJob, RunnerJobState


# pylint: disable=missing-class-docstring


class RunnerSerializer(serializers.ModelSerializer):
    """Serializer for the Runner model."""

    class Meta:
        model = Runner
        fields = (
            "id",
            "name",
            "runnerToken",
        )
        read_only_fields = (
            "runnerRegistrationToken",
            "lastContact",
            "ip",
        )


class SimpleRunnerJobSerializer(serializers.ModelSerializer):
    """Simple Serializer for the RunnerJob model."""

    class Meta:
        model = RunnerJob
        fields = (
            "uuid",
            "type",
            "payload",
        )


class BaseRunnerJobSerializer(serializers.ModelSerializer):
    """Base Serializer for the RunnerJob model."""

    state = serializers.SerializerMethodField(read_only=True)

    def get_state(self, obj):
        """Get a formatted state of the RunnerJob."""
        return {
            "id": obj.state,
            "label": RunnerJobState(obj.state).label,
        }


class ParentRunnerJobSerializer(BaseRunnerJobSerializer):
    """Serializer for the a parent RunnerJob model."""

    class Meta:
        model = RunnerJob
        fields = (
            "id",
            "uuid",
            "type",
            "state",
        )


class RunnerJobSerializer(BaseRunnerJobSerializer):
    """Serializer for the a RunnerJob model."""

    jobToken = serializers.CharField(source="processingJobToken", read_only=True)
    runner = RunnerSerializer()
    parent = ParentRunnerJobSerializer(source="dependsOnRunnerJob")

    class Meta:
        model = RunnerJob
        fields = (
            "uuid",
            "type",
            "state",
            "progress",
            "priority",
            "failures",
            "error",
            "payload",
            "startedAt",
            "finishedAt",
            "jobToken",
            "runner",
            "parent",
        )
