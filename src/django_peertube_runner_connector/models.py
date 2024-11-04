"""Models for the django-peertube-runner-connector app."""

from datetime import timedelta
import logging
from uuid import uuid4

from django.db import models
from django.utils import timezone

from django_peertube_runner_connector.storage import video_storage


logger = logging.getLogger(__name__)


class RunnerRegistrationToken(models.Model):
    """Model representing a PeerTube runner registration token."""

    id = models.UUIDField(
        verbose_name="id",
        help_text="primary key for the record as UUID",
        primary_key=True,
        default=uuid4,
        editable=False,
    )
    registrationToken = models.CharField(
        max_length=255, unique=True, help_text="A unique token to be used by runners"
    )
    createdAt = models.DateTimeField(auto_now_add=True, help_text="Created at")
    updatedAt = models.DateTimeField(auto_now=True, help_text="Updated at")


class Runner(models.Model):
    """Model representing a PeerTube runner."""

    id = models.UUIDField(
        verbose_name="id",
        help_text="primary key for the record as UUID",
        primary_key=True,
        default=uuid4,
    )
    runnerToken = models.CharField(max_length=255, help_text="Runner token")
    name = models.CharField(max_length=255, unique=True, help_text="Runner name")
    description = models.CharField(
        max_length=255, null=True, help_text="Runner description"
    )
    lastContact = models.DateTimeField(help_text="Last time a runner contacted us")
    ip = models.CharField(max_length=255, help_text="IP address of the runner")
    runnerRegistrationToken = models.ForeignKey(
        RunnerRegistrationToken,
        on_delete=models.CASCADE,
        help_text="Runner registration token",
    )
    createdAt = models.DateTimeField(auto_now_add=True, help_text="Created at")
    updatedAt = models.DateTimeField(auto_now=True, help_text="Updated at")

    def update_last_contact(self, ip_address):
        """Update last time a runner contacted us."""
        if timezone.now() - self.lastContact < timedelta(minutes=5):
            return
        # pylint: disable=invalid-name
        self.lastContact = timezone.now()
        self.ip = ip_address
        self.save()


class RunnerJobState(models.IntegerChoices):
    """State of runner job."""

    PENDING = 1, "Pending"
    PROCESSING = 2, "Processing"
    COMPLETED = 3, "Completed"
    ERRORED = 4, "Errored"
    WAITING_FOR_PARENT_JOB = 5, "Waiting for parent job"
    CANCELLED = 6, "Cancelled"
    PARENT_ERRORED = 7, "Parent errored"
    PARENT_CANCELLED = 8, "Parent cancelled"
    COMPLETING = 9, "Completing"


class RunnerJobType(models.TextChoices):
    """Type of runner job."""

    VOD_WEB_VIDEO_TRANSCODING = "vod-web-video-transcoding"
    VOD_HLS_TRANSCODING = "vod-hls-transcoding"
    VOD_AUDIO_MERGE_TRANSCODING = "vod-audio-merge-transcoding"
    LIVE_RTMP_HLS_TRANSCODING = "live-rtmp-hls-transcoding"
    VIDEO_STUDIO_TRANSCODING = "video-studio-transcoding"
    VIDEO_TRANSCRIPTION = "video-transcription"


class RunnerJobQuerySet(models.QuerySet):
    """Queryset for RunnerJob."""

    def list_available_jobs(self, types=None):
        """List available jobs."""
        available_jobs = self.filter(state=RunnerJobState.PENDING)
        if types:
            available_jobs = available_jobs.filter(type__in=types)
        return available_jobs.order_by("priority")[:10]


class RunnerJob(models.Model):
    """Model representing a runner job."""

    objects = RunnerJobQuerySet.as_manager()

    id = models.UUIDField(
        verbose_name="id",
        help_text="primary key for the record as UUID",
        primary_key=True,
        default=uuid4,
    )
    uuid = models.UUIDField(unique=True, default=uuid4, help_text="Job UUID")
    domain = models.CharField(
        max_length=255, null=True, blank=True, help_text="Job domain"
    )
    type = models.CharField(
        max_length=255, choices=RunnerJobType.choices, help_text="Job type"
    )
    payload = models.JSONField(help_text="Job payload (metadata given to the runner)")
    privatePayload = models.JSONField(
        help_text="Job private payload (metadata given to the runner)"
    )
    state = models.IntegerField(choices=RunnerJobState.choices, help_text="Job state")
    failures = models.IntegerField(default=0, help_text="Number of failures")
    error = models.TextField(null=True, blank=True, help_text="Error message")
    priority = models.IntegerField(help_text="Job priority")
    processingJobToken = models.CharField(
        max_length=255, null=True, blank=True, help_text="Processing job token"
    )
    progress = models.FloatField(null=True, blank=True, help_text="Job progress")
    startedAt = models.DateTimeField(null=True, blank=True, help_text="Job started at")
    finishedAt = models.DateTimeField(
        null=True, blank=True, help_text="Job finished at"
    )
    dependsOnRunnerJob = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        help_text="job that depends on this one",
    )
    runner = models.ForeignKey(
        Runner,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Runner processing the job",
    )

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def set_to_error_or_cancel(self, state):
        """Set the job to the errored or cancelled state."""
        # pylint: disable=invalid-name
        self.state = state
        self.processingJobToken = None
        self.finishedAt = timezone.now()
        self.save()

    def reset_to_pending(self):
        """Reset the job to the pending state."""
        # pylint: disable=invalid-name
        self.state = RunnerJobState.PENDING
        self.processingJobToken = None
        self.progress = None
        self.finishedAt = None
        self.startedAt = None

    def update_dependant_jobs(self):
        """Update the dependant jobs to the pending state."""
        num_updated = self.children.update(state=RunnerJobState.PENDING)
        return num_updated


class VideoJobInfoColumnType(models.TextChoices):
    """Possible video job info column types."""

    PENDING_MOVE = "pendingMove"
    PENDING_TRANSCODE = "pendingTranscode"
    PENDING_TRANSCRIPT = "pendingTranscript"


class VideoState(models.IntegerChoices):
    """Possible video state list."""

    PUBLISHED = 1, "Published"
    TO_TRANSCODE = 2, "To transcode"
    TO_IMPORT = 3, "To import"
    WAITING_FOR_LIVE = 4, "Waiting for live"
    LIVE_ENDED = 5, "Live ended"
    TO_MOVE_TO_EXTERNAL_STORAGE = 6, "To move to external storage"
    TRANSCODING_FAILED = 7, "Transcoding failed"
    TO_MOVE_TO_EXTERNAL_STORAGE_FAILED = 8, "To move to external storage failed"
    TO_EDIT = 9, "To edit"


class Video(models.Model):
    """Model representing a video."""

    id = models.UUIDField(
        verbose_name="id",
        help_text="primary key for the record as UUID",
        primary_key=True,
        default=uuid4,
    )
    uuid = models.UUIDField(unique=True, default=uuid4, help_text="UUID of the video")
    state = models.IntegerField(
        choices=VideoState.choices, help_text="State of the video"
    )
    duration = models.IntegerField(
        null=True, blank=True, help_text="Duration of the video"
    )
    directory = models.CharField(
        max_length=255, help_text="Directory of the video on the storage"
    )
    thumbnailFilename = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Thumbnail filename on the storage",
    )
    transcriptFileName = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Transcript filename on the storage",
    )
    language = models.CharField(
        max_length=255, null=True, blank=True, help_text="Language of the video"
    )
    baseFilename = models.CharField(
        max_length=255,
        help_text="File used for new files related to the video",
        null=True,
        blank=True,
    )
    createdAt = models.DateTimeField(auto_now_add=True, help_text="Creation At")
    updatedAt = models.DateTimeField(auto_now=True, help_text="Update At")

    def get_max_quality_file(self):
        """Get the highest quality video file."""
        if not self.files.count():
            return None
        return max(self.files.all(), key=lambda f: f.resolution)

    def remove_all_web_video_files(self):
        """Remove all related video files."""
        for file in self.files.all():
            file.remove_web_video_file()
            file.delete()

    def get_bandwidth_bits(self, video_file: "VideoFile"):
        """Get the bandwidth bits of a video file."""
        if not self.duration:
            return video_file.size

        return int((video_file.size * 8) / self.duration)

    def increase_or_create_job_info(
        self, column: VideoJobInfoColumnType, amount: int = 1
    ):
        """Increase a video job info column."""
        job_info, _ = VideoJobInfo.objects.get_or_create(video=self)
        setattr(job_info, column, getattr(job_info, column) + amount)
        job_info.save()
        return getattr(job_info, column)

    def decrease_job_info(self, column: VideoJobInfoColumnType):
        """Decrease a video job info column."""
        try:
            job_info = VideoJobInfo.objects.get(video=self)
            setattr(job_info, column, getattr(job_info, column) - 1)
            job_info.save()
            return getattr(job_info, column)
        except VideoJobInfo.DoesNotExist:
            return None


class VideoJobInfo(models.Model):
    """Model keeping track of video job completion."""

    id = models.UUIDField(
        verbose_name="id",
        help_text="primary key for the record as UUID",
        primary_key=True,
        default=uuid4,
    )

    pendingMove = models.IntegerField(
        default=0, help_text="Counter of pending move to an external storage operations"
    )
    pendingTranscode = models.IntegerField(
        default=0, help_text="Counter of pending transcoding operations"
    )
    pendingTranscript = models.IntegerField(
        default=0, help_text="Counter of pending transcript operations"
    )
    video = models.OneToOneField(
        "Video",
        on_delete=models.CASCADE,
        related_name="jobInfo",
        help_text="Video related to the job info",
    )
    createdAt = models.DateTimeField(auto_now_add=True, help_text="Creation At")
    updatedAt = models.DateTimeField(auto_now=True, help_text="Update At")


class VideoResolution(models.IntegerChoices):
    """Video resolution list."""

    H_NOVIDEO = 0
    H_144P = 144
    H_240P = 240
    H_360P = 360
    H_480P = 480
    H_720P = 720
    H_1080P = 1080
    H_1440P = 1440
    H_4K = 2160


class VideoStreamingPlaylist(models.Model):
    """Model representing a video master streaming playlist (.m3u8)."""

    id = models.UUIDField(
        verbose_name="id",
        help_text="primary key for the record as UUID",
        primary_key=True,
        default=uuid4,
    )
    playlistFilename = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Filename of the playlist in the storage",
    )
    video = models.OneToOneField(
        Video,
        on_delete=models.CASCADE,
        related_name="streamingPlaylist",
        help_text="Video related to the streaming playlist",
    )
    createdAt = models.DateTimeField(auto_now_add=True, help_text="Creation At")
    updatedAt = models.DateTimeField(auto_now=True, help_text="Update At")


class VideoFile(models.Model):
    """Model representing a video file."""

    id = models.UUIDField(
        verbose_name="id",
        help_text="primary key for the record as UUID",
        primary_key=True,
        default=uuid4,
    )
    resolution = models.IntegerField(
        choices=VideoResolution.choices, help_text="Resolution of the video"
    )
    size = models.BigIntegerField(help_text="Size of the video file")
    extname = models.CharField(max_length=255, help_text="Extension of the video file")
    fps = models.IntegerField(default=-1, help_text="Frame rate of the video")
    metadata = models.JSONField(
        null=True, blank=True, help_text="Metadata of the video"
    )
    filename = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Filename of the video on the storage",
    )
    video = models.ForeignKey(
        to="Video",
        on_delete=models.CASCADE,
        related_name="files",
        help_text="Video related to the video file",
    )
    streamingPlaylist = models.ForeignKey(
        VideoStreamingPlaylist,
        related_name="videoFiles",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Streaming playlist (.m3u8) related to the video file",
    )
    createdAt = models.DateTimeField(auto_now_add=True, help_text="Creation At")
    updatedAt = models.DateTimeField(auto_now=True, help_text="Update At")

    def remove_web_video_file(self):
        """Remove the video file from the storage."""
        video_storage.delete(self.filename)

    def is_audio(self):
        """Check if the file is an audio file."""
        return self.resolution == VideoResolution.H_NOVIDEO
