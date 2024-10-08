"""FFprobe utils."""

import logging

import ffmpeg

from ..models import VideoResolution


logger = logging.getLogger(__name__)


def get_video_stream_duration(path: str, existing_probe=None):
    """Return the duration of a video stream."""
    metadata = existing_probe or ffmpeg.probe(path)

    return round(float(metadata["format"]["duration"]))


def get_video_stream(path: str, existing_probe=None):
    """Return the video stream."""
    probe = existing_probe or ffmpeg.probe(path)
    return next(
        (stream for stream in probe["streams"] if stream["codec_type"] == "video"), None
    )


def get_video_stream_dimensions_info(path: str, existing_probe=None):
    """Return the video stream dimensions info."""

    if video_stream := get_video_stream(path=path, existing_probe=existing_probe):
        min_dimension = min(video_stream["height"], video_stream["width"])
        max_dimension = max(video_stream["height"], video_stream["width"])

        return {
            "width": video_stream["width"],
            "height": video_stream["height"],
            "ratio": max_dimension / min_dimension if min_dimension > 0 else 0,
            "resolution": min_dimension,
            "isPortraitMode": video_stream["height"] > video_stream["width"],
        }

    return {
        "width": 0,
        "height": 0,
        "ratio": 0,
        "resolution": VideoResolution.H_NOVIDEO,
        "isPortraitMode": False,
    }


def get_video_stream_fps(probe):
    """Return the video stream fps."""
    video_stream = get_video_stream(path="", existing_probe=probe)
    if not video_stream:
        return 0

    for key in ["avg_frame_rate", "r_frame_rate"]:
        values_text = video_stream.get(key)
        if not values_text:
            continue

        frames, seconds = values_text.split("/")
        if not frames or not seconds:
            continue
        frames_int = int(frames, 10)
        seconds_int = int(seconds, 10)
        if frames_int > 0 and seconds_int > 0:
            result = frames_int / seconds_int
            if result > 0:
                return round(result)

    return 0


IMAGE_CODECS = {
    "ansi",
    "apng",
    "bintext",
    "bmp",
    "brender_pix",
    "dpx",
    "exr",
    "fits",
    "gem",
    "gif",
    "jpeg2000",
    "jpgls",
    "mjpeg",
    "mjpegb",
    "msp2",
    "pam",
    "pbm",
    "pcx",
    "pfm",
    "pgm",
    "pgmyuv",
    "pgx",
    "photocd",
    "pictor",
    "png",
    "ppm",
    "psd",
    "sgi",
    "sunrast",
    "svg",
    "targa",
    "tiff",
    "txd",
    "webp",
    "xbin",
    "xbm",
    "xface",
    "xpm",
    "xwd",
}


def is_audio_file(probe):
    """Return True if the file is an audio file."""
    video_stream = get_video_stream(path="", existing_probe=probe)
    return not video_stream or video_stream["codec_name"] in IMAGE_CODECS


def has_audio_stream(probe):
    """Return True if the file has an audio stream."""
    audio_stream = get_audio_stream(path="", existing_probe=probe)

    return bool(audio_stream.get("audio_stream"))


def get_audio_stream(path, existing_probe=None):
    """Return the audio stream."""
    probe = existing_probe or ffmpeg.probe(path)

    audio_streams = probe.get("streams", [])
    audio_stream = next(
        (stream for stream in audio_streams if stream.get("codec_type") == "audio"),
        None,
    )
    if audio_stream:
        return {
            "absolute_path": probe["format"]["filename"],
            "audio_stream": audio_stream,
            "bitrate": int(audio_stream.get("bit_rate", 0)),
        }

    return {"absolute_path": probe["format"]["filename"]}


def build_file_metadata(probe):
    """Return the file metadata."""
    return {
        "chapter": probe.get("chapter", ""),
        "format": probe.get("format", ""),
        "streams": probe.get("streams", ""),
    }
