"""Test the codecs file."""

from unittest.mock import patch

from django.test import TestCase

from django_peertube_runner_connector.storage import video_storage
from django_peertube_runner_connector.utils.transcoding.codecs import (
    get_audio_stream_codec,
    get_video_stream_codec,
)


class CodecsTestCase(TestCase):
    """Test the codecs utils file."""

    def setUp(self):
        """Create a file path."""
        self.file_path = video_storage.url("test.mp4")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_video_stream")
    def test_get_video_stream_codec_vp09(self, mock_get_video_stream):
        """Should return vp09."""
        mock_get_video_stream.return_value = {"codec_tag_string": "vp09"}

        codec = get_video_stream_codec(self.file_path)

        self.assertEqual(codec, "vp09.00.50.08")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_video_stream")
    def test_get_video_stream_codec_hev1(self, mock_get_video_stream):
        """Should return hev1."""
        mock_get_video_stream.return_value = {"codec_tag_string": "hev1"}

        codec = get_video_stream_codec(self.file_path)

        self.assertEqual(codec, "hev1.1.6.L93.B0")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_video_stream")
    def test_get_video_stream_codec_avc1_high(self, mock_get_video_stream):
        """Should return avc1."""
        mock_get_video_stream.return_value = {
            "codec_tag_string": "avc1",
            "profile": "High",
            "level": "42",
        }

        codec = get_video_stream_codec(self.file_path)

        self.assertEqual(codec, "avc1.64002a")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_video_stream")
    def test_get_video_stream_codec_avc1_main(self, mock_get_video_stream):
        """Should return avc1."""
        mock_get_video_stream.return_value = {
            "codec_tag_string": "avc1",
            "profile": "Main",
            "level": "31",
        }

        codec = get_video_stream_codec(self.file_path)

        self.assertEqual(codec, "avc1.4D401f")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_video_stream")
    def test_get_video_stream_codec_avc1_baseline(self, mock_get_video_stream):
        """Should return avc1."""
        mock_get_video_stream.return_value = {
            "codec_tag_string": "avc1",
            "profile": "Baseline",
            "level": "1",
        }

        codec = get_video_stream_codec(self.file_path)

        self.assertEqual(codec, "avc1.42E001")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_video_stream")
    def test_get_video_stream_codec_av01_high(self, mock_get_video_stream):
        """Should return av01 with the right hexa level."""
        mock_get_video_stream.return_value = {
            "codec_tag_string": "av01",
            "profile": "High",
            "level": 2,
        }

        codec = get_video_stream_codec(self.file_path)

        self.assertEqual(codec, "av01.1.02M.08")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_video_stream")
    def test_get_video_stream_codec_av01_main(self, mock_get_video_stream):
        """Should return av01 with the right hexa level."""
        mock_get_video_stream.return_value = {
            "codec_tag_string": "av01",
            "profile": "Main",
            "level": 1,
        }

        codec = get_video_stream_codec(self.file_path)

        self.assertEqual(codec, "av01.0.01M.08")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_video_stream")
    def test_get_video_stream_codec_av01_professional(self, mock_get_video_stream):
        """Should return av01 with the right hexa level."""
        mock_get_video_stream.return_value = {
            "codec_tag_string": "av01",
            "profile": "Professional",
            "level": 6,
        }

        codec = get_video_stream_codec(self.file_path)

        self.assertEqual(codec, "av01.2.06M.08")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.logger")
    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_video_stream")
    def test_get_video_stream_codec_unknown_codec(
        self, mock_get_video_stream, mock_logger
    ):
        """Should log a warning."""
        mock_get_video_stream.return_value = {"codec_tag_string": "unknown"}

        codec = get_video_stream_codec(self.file_path)

        self.assertEqual(codec, "")
        mock_logger.warning.assert_called_once_with(
            "Cannot get video codec of %s.", self.file_path
        )

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_video_stream")
    def test_get_video_stream_codec_no_video_stream(self, mock_get_video_stream):
        """Should return an empty string."""
        mock_get_video_stream.return_value = {}

        codec = get_video_stream_codec(self.file_path)

        self.assertEqual(codec, "")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_audio_stream")
    def test_get_audio_stream_codec_opus(self, mock_get_audio_stream):
        """Should return opus."""
        mock_get_audio_stream.return_value = {"audio_stream": {"codec_name": "opus"}}

        codec = get_audio_stream_codec(self.file_path)

        self.assertEqual(codec, "opus")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_audio_stream")
    def test_get_audio_stream_codec_vorbis(self, mock_get_audio_stream):
        """Should return vorbis."""
        mock_get_audio_stream.return_value = {"audio_stream": {"codec_name": "vorbis"}}

        codec = get_audio_stream_codec(self.file_path)

        self.assertEqual(codec, "vorbis")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_audio_stream")
    def test_get_audio_stream_codec_aac(self, mock_get_audio_stream):
        """Should return mp4a.40.2."""
        mock_get_audio_stream.return_value = {"audio_stream": {"codec_name": "aac"}}

        codec = get_audio_stream_codec(self.file_path)

        self.assertEqual(codec, "mp4a.40.2")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_audio_stream")
    def test_get_audio_stream_codec_mp3(self, mock_get_audio_stream):
        """Should return mp4a.40.34."""
        mock_get_audio_stream.return_value = {"audio_stream": {"codec_name": "mp3"}}

        codec = get_audio_stream_codec(self.file_path)

        self.assertEqual(codec, "mp4a.40.34")

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.logger")
    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_audio_stream")
    def test_get_audio_stream_codec_unknown(self, mock_get_audio_stream, mock_logger):
        """Should log a warning."""
        mock_get_audio_stream.return_value = {"audio_stream": {"codec_name": "unknown"}}

        codec = get_audio_stream_codec(self.file_path)

        self.assertEqual(codec, "mp4a.40.2")

        mock_logger.warning.assert_called_once_with(
            "Cannot get audio codec of %s.", self.file_path
        )

    @patch("django_peertube_runner_connector.utils.transcoding.codecs.get_audio_stream")
    def test_get_audio_stream_codec_no_audio_stream(self, mock_get_audio_stream):
        """Should return an empty string."""
        mock_get_audio_stream.return_value = {}

        codec = get_audio_stream_codec(self.file_path)

        self.assertEqual(codec, "")
