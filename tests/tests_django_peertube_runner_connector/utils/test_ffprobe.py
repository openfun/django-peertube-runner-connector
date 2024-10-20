"""Test the "ffprobe.py" utils file."""

from django.test import TestCase

from tests_django_peertube_runner_connector.probe_response import probe_response

from django_peertube_runner_connector.utils.ffprobe import (
    build_file_metadata,
    get_audio_stream,
    get_video_stream,
    get_video_stream_dimensions_info,
    get_video_stream_duration,
    get_video_stream_fps,
    has_audio_stream,
    is_audio_file,
)


class TestFFProbe(TestCase):
    """Test the ffprobe utils file."""

    def test_get_video_stream_duration(self):
        """Should return the video stream duration."""
        duration = get_video_stream_duration(
            "/path/to/video.mp4", existing_probe=probe_response
        )

        self.assertEqual(duration, 22)

    def test_get_video_stream(self):
        """Should return the video stream."""

        stream = get_video_stream("/path/to/video.mp4", existing_probe=probe_response)
        self.assertEqual(stream, {**stream, **{"codec_type": "video"}})

    def test_get_video_stream_dimensions_info(self):
        """Should return the video stream dimensions info."""

        dimensions_info = get_video_stream_dimensions_info(
            "/path/to/video.mp4", existing_probe=probe_response
        )

        self.assertEqual(dimensions_info["width"], 960)
        self.assertEqual(dimensions_info["height"], 540)
        self.assertEqual(dimensions_info["ratio"], 1.7777777777777777)
        self.assertEqual(dimensions_info["resolution"], 540)
        self.assertFalse(dimensions_info["isPortraitMode"])

    def test_get_video_stream_dimensions_info_with_one_dimension(self):
        """Should return the video stream dimensions info."""

        dimensions_info = get_video_stream_dimensions_info(
            "/path/to/video.mp4",
            existing_probe={
                "streams": [
                    {
                        "codec_type": "video",
                        "height": 0,
                        "width": 1900,
                    }
                ]
            },
        )

        self.assertEqual(dimensions_info["width"], 1900)
        self.assertEqual(dimensions_info["height"], 0)
        self.assertEqual(dimensions_info["ratio"], 0)
        self.assertEqual(dimensions_info["resolution"], 0)
        self.assertFalse(dimensions_info["isPortraitMode"])

    def test_get_video_stream_fps(self):
        """Should return the video stream fps."""
        fps = get_video_stream_fps(probe_response)
        self.assertEqual(fps, 30)

    def test_get_video_stream_without_fps(self):
        """Should return the video stream fps."""
        fps = get_video_stream_fps(
            {
                "streams": [
                    {
                        "codec_type": "video",
                        "avg_frame_rate": "30/0",
                    }
                ]
            }
        )
        self.assertEqual(fps, 0)

    def test_is_audio_file(self):
        """Should return True if the file is an audio file."""
        is_audio = is_audio_file(probe_response)
        self.assertFalse(is_audio)

    def test_has_audio_stream(self):
        """Should return True if the file has an audio stream."""

        has_audio = has_audio_stream(probe_response)
        self.assertTrue(has_audio)

    def test_get_audio_stream(self):
        """Should return the audio stream."""

        audio_stream = get_audio_stream(
            "/path/to/audio.mp3", existing_probe=probe_response
        )

        self.assertEqual(
            audio_stream["audio_stream"],
            {
                "bit_rate": "1066073",
                "channels": 2,
                "codec_name": "aac",
                "codec_type": "audio",
                "duration": "00:01:00.00",
                "index": 1,
                "sample_rate": "48000 Hz",
                "tags": {"language": "eng"},
            },
        )
        self.assertEqual(audio_stream["absolute_path"], "/path/to/audio.mp3")
        self.assertEqual(audio_stream["bitrate"], 1066073)

    def test_get_audio_stream_without_bitrate(self):
        """Should return the audio stream with bitrate set to 0."""

        audio_stream = get_audio_stream(
            "/path/to/audio.mp3",
            existing_probe={
                "streams": [
                    {
                        "codec_type": "audio",
                        "channels": 2,
                        "codec_name": "aac",
                        "duration": "00:01:00.00",
                        "index": 1,
                        "sample_rate": "48000 Hz",
                        "tags": {"language": "eng"},
                    }
                ],
                "format": {
                    "filename": "/path/to/audio.mp3",
                },
            },
        )

        self.assertEqual(
            audio_stream["audio_stream"],
            {
                "channels": 2,
                "codec_name": "aac",
                "codec_type": "audio",
                "duration": "00:01:00.00",
                "index": 1,
                "sample_rate": "48000 Hz",
                "tags": {"language": "eng"},
            },
        )
        self.assertEqual(audio_stream["absolute_path"], "/path/to/audio.mp3")
        self.assertEqual(audio_stream["bitrate"], 0)

    def test_build_file_metadata(self):
        """Should return a dic with the file metadata."""

        metadata = build_file_metadata(probe_response)

        self.assertEqual(metadata["chapter"], "")
        self.assertEqual(metadata["format"], probe_response["format"])
        self.assertEqual(metadata["streams"], probe_response["streams"])
