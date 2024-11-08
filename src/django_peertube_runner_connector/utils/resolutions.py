"""Utils function related to resolutions."""

from django.conf import settings

from django_peertube_runner_connector.models import VideoResolution


AVAILABLE_RESOLUTIONS = [
    resolution.value
    for resolution in [
        VideoResolution.H_NOVIDEO,
        VideoResolution.H_144P,
        VideoResolution.H_240P,
        VideoResolution.H_360P,
        VideoResolution.H_480P,
        VideoResolution.H_720P,
        VideoResolution.H_1080P,
        VideoResolution.H_1440P,
        VideoResolution.H_4K,
    ]
]


def _get_config_resolutions():
    """Return a map of resolutions enabled in the settings."""
    return {
        "144p": settings.TRANSCODING_RESOLUTIONS_144P,
        "240p": settings.TRANSCODING_RESOLUTIONS_240P,
        "360p": settings.TRANSCODING_RESOLUTIONS_360P,
        "480p": settings.TRANSCODING_RESOLUTIONS_480P,
        "720p": settings.TRANSCODING_RESOLUTIONS_720P,
        "1080p": settings.TRANSCODING_RESOLUTIONS_1080P,
        "1440p": settings.TRANSCODING_RESOLUTIONS_1440P,
        "2160p": settings.TRANSCODING_RESOLUTIONS_2160P,
    }


def to_even(num: int):
    """Return the next even number."""
    if is_odd(num):
        return num + 1

    return num


def is_odd(num: int):
    """Return True if the number is odd."""
    return num % 2 != 0


def compute_max_resolution_to_transcode(
    input_resolution: int,
):
    """Compute the maximum resolution to transcode."""
    config_resolutions = _get_config_resolutions()
    available_resolutions = sorted(AVAILABLE_RESOLUTIONS, reverse=True)

    for resolution in available_resolutions:
        if not config_resolutions.get(f"{resolution}p", None):
            continue
        if input_resolution < resolution:
            continue

        return resolution

    return VideoResolution.H_NOVIDEO


def compute_resolutions_to_transcode(
    input_resolution: int,
    include_input: bool,
    strict_lower: bool,
    has_audio: bool,
):
    """Compute the possible resolutions to transcode related to settings."""
    config_resolutions = _get_config_resolutions()

    resolutions_enabled = set()
    for resolution in AVAILABLE_RESOLUTIONS:
        if not config_resolutions.get(f"{resolution}p", None):
            continue
        if input_resolution < resolution:
            continue
        if strict_lower and input_resolution == resolution:
            continue
        if resolution == VideoResolution.H_NOVIDEO and not has_audio:
            continue

        resolutions_enabled.add(resolution)

    if include_input:
        resolutions_enabled.add(to_even(input_resolution))

    return sorted(resolutions_enabled)
