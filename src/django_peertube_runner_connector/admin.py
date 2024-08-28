"""Admin of django-peertube-runner-connector app."""

from django.contrib import admin

from django_peertube_runner_connector.models import (
    Runner,
    RunnerJob,
    RunnerRegistrationToken,
    Video,
    VideoFile,
    VideoJobInfo,
    VideoStreamingPlaylist,
)


@admin.register(RunnerRegistrationToken)
class RunnerRegistrationTokenAdmin(admin.ModelAdmin):
    """Base admin class for RunnerRegistrationToken."""

    list_display = ("registrationToken", "createdAt", "updatedAt")


@admin.register(Runner)
class RunnerAdmin(admin.ModelAdmin):
    """Base admin class for Runner."""

    list_display = (
        "name",
        "description",
        "lastContact",
        "ip",
        "createdAt",
        "updatedAt",
        "runnerRegistrationToken",
    )

    search_fields = ("name", "runnerRegistrationToken__registrationToken")


@admin.register(RunnerJob)
class RunnerJobAdmin(admin.ModelAdmin):
    """Base admin class for RunnerJob."""

    list_display = (
        "uuid",
        "type",
        "state",
        "failures",
        "error",
        "priority",
        "processingJobToken",
        "progress",
        "startedAt",
        "finishedAt",
        "dependsOnRunnerJob",
        "runner",
        "createdAt",
        "updatedAt",
    )

    search_fields = ("type", "state", "uuid")
    list_filter = ("type", "state")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Base admin class for Video."""

    list_display = ("uuid", "state", "duration", "thumbnailFilename", "directory")


@admin.register(VideoStreamingPlaylist)
class VideoStreamingPlaylistAdmin(admin.ModelAdmin):
    """Base admin class for VideoStreamingPlaylist."""

    list_display = ("id", "playlistFilename", "video")

    list_filter = ("playlistFilename", "video")

    search_fields = ("id", "playlistFilename", "video__id")


@admin.register(VideoFile)
class VideoFileAdmin(admin.ModelAdmin):
    """Base admin class for VideoFile."""

    list_display = (
        "id",
        "filename",
        "video",
        "resolution",
        "size",
        "extname",
        "fps",
        "createdAt",
        "updatedAt",
    )

    list_filter = ("resolution", "createdAt", "updatedAt")
    search_fields = ("id", "filename", "video__id")


@admin.register(VideoJobInfo)
class VideoJobInfoAdmin(admin.ModelAdmin):
    """Base admin class for VideoJobInfo."""

    list_display = (
        "id",
        "createdAt",
        "updatedAt",
        "pendingMove",
        "pendingTranscode",
        "video",
    )
    list_filter = ("createdAt", "updatedAt")
    search_fields = ("id", "video__id")
