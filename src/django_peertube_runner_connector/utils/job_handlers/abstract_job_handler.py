"""Base class for job handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from uuid import UUID

from django.conf import settings
from django.utils import timezone

from asgiref.sync import async_to_sync

from django_peertube_runner_connector.models import (
    RunnerJob,
    RunnerJobState,
    RunnerJobType,
)
from django_peertube_runner_connector.socket import send_available_jobs_ping_to_runners


logger = logging.getLogger(__name__)

# https://github.com/Chocobozzz/PeerTube/blob/develop/server/server/lib/runners/job-handlers/abstract-job-handler.ts


class AbstractJobHandler(ABC):
    """Base class for job handlers."""

    @abstractmethod
    # pylint: disable=arguments-differ
    def create(self, *args, **kwargs):
        """This method should be implemented by subclasses."""

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def create_runner_job(
        self,
        domain: str,
        job_type: RunnerJobType,
        job_uuid: UUID,
        payload: dict,
        private_payload: dict,
        priority: int,
        depends_on_runner_job: RunnerJob | None,
    ):
        """This method creates a RunnerJob and send a ping to the runners."""
        runner_job = RunnerJob.objects.create(
            type=job_type,
            domain=domain,
            payload=payload,
            privatePayload=private_payload,
            uuid=job_uuid,
            state=(
                RunnerJobState.WAITING_FOR_PARENT_JOB
                if depends_on_runner_job
                else RunnerJobState.PENDING
            ),
            dependsOnRunnerJob=depends_on_runner_job,
            priority=priority,
        )

        if runner_job.state == RunnerJobState.PENDING:
            async_to_sync(send_available_jobs_ping_to_runners)()

        return runner_job

    @abstractmethod
    def specific_update(
        self,
        runner_job: RunnerJob,
        update_payload=None,
    ):
        """This method should be implemented by subclasses."""

    def update(
        self,
        runner_job: RunnerJob,
        progress: int | None = None,
        update_payload=None,
    ):
        """This method updates a RunnerJob progress."""
        self.specific_update(runner_job, update_payload)

        if progress is not None:
            runner_job.progress = progress

        runner_job.save()

    @abstractmethod
    def specific_complete(self, runner_job: RunnerJob, result_payload):
        """This method should be implemented by subclasses."""

    def complete(self, runner_job: RunnerJob, result_payload):
        """
        This method will set the job to completed state
        and update its dependant to be put them in the pending state.
        """
        runner_job.state = RunnerJobState.COMPLETING
        runner_job.save()

        try:
            self.specific_complete(runner_job, result_payload)
            runner_job.state = RunnerJobState.COMPLETED
        except Exception as err:  # pylint: disable=broad-except
            runner_job.state = RunnerJobState.ERRORED
            runner_job.error = str(err)

        runner_job.progress = None
        runner_job.finishedAt = timezone.now()

        runner_job.save()

        affected_count = runner_job.update_dependant_jobs()
        if affected_count != 0:
            async_to_sync(send_available_jobs_ping_to_runners)()

    @abstractmethod
    def specific_cancel(self, runner_job: RunnerJob):
        """This method should be implemented by subclasses."""

    def cancel(self, runner_job: RunnerJob, from_parent: bool = False):
        """This method will set the job and its dependant to a cancelled state."""
        self.specific_cancel(runner_job)

        cancel_state = (
            RunnerJobState.PARENT_CANCELLED if from_parent else RunnerJobState.CANCELLED
        )
        runner_job.set_to_error_or_cancel(cancel_state)

        runner_job.save()

        children = runner_job.children.all()
        for child in children:
            self.cancel(child, from_parent=True)

    @abstractmethod
    def is_abort_supported(self):
        """This method should be implemented by subclasses."""

    def abort(self, runner_job: RunnerJob):
        """
        This method try to abort a job and reset to the pending state.
        If the job can not be aborted, it will be set to errored.
        """
        if not self.is_abort_supported():
            self.error(
                runner_job,
                "Job has been aborted but it is not supported by this job type",
            )
            return

        self.specific_abort(runner_job)
        runner_job.reset_to_pending()
        runner_job.save()

    @abstractmethod
    def specific_abort(self, runner_job: RunnerJob):
        """This method should be implemented by subclasses."""

    def error(self, runner_job: RunnerJob, message: str, from_parent: bool = False):
        """
        This method try to reset the job to the pending state.
        If the job has failed too many times, it will be set to errored.
        """
        error_state = (
            RunnerJobState.PARENT_ERRORED if from_parent else RunnerJobState.ERRORED
        )
        next_state = (
            error_state
            if runner_job.failures >= settings.TRANSCODING_RUNNER_MAX_FAILURE
            or not self.is_abort_supported()
            else RunnerJobState.PENDING
        )

        self.specific_error(runner_job, message, next_state)

        if next_state == error_state:
            runner_job.set_to_error_or_cancel(error_state)
            runner_job.error = message
        else:
            runner_job.reset_to_pending()

        runner_job.save()

        if runner_job.state == error_state:
            children = runner_job.children.all()
            for child in children:
                self.error(child, "Parent error", from_parent=True)

    @abstractmethod
    def specific_error(
        self, runner_job: RunnerJob, message: str, next_state: RunnerJobState
    ):
        """This method should be implemented by subclasses."""
