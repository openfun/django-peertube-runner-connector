"""Test the job handlers utils file."""

from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from django_peertube_runner_connector.factories import (
    RunnerJobFactory,
    VideoFactory,
    VideoJobInfoFactory,
)
from django_peertube_runner_connector.utils.job_handlers.utils import (
    is_transcription_language_valid,
    load_runner_video,
    on_transcoding_ended,
    on_transcription_ended,
    on_transcription_error,
)


mock_transcription_ended_callback = Mock()
mock_transcription_error_callback = Mock()


class TestJobHandlersUtils(TestCase):
    """Test the job handlers utils file."""

    def setUp(self):
        """Mock the transcription ended callback."""
        mock_transcription_ended_callback.reset_mock()

    def test_load_runner_video(self):
        """Should be able to load a transcoding runner video from payload."""
        video = VideoFactory(uuid="123e4567-e89b-12d3-a456-426655440002")

        runner_job = RunnerJobFactory(
            privatePayload={"videoUUID": "123e4567-e89b-12d3-a456-426655440002"}
        )

        result = load_runner_video(runner_job)

        self.assertEqual(result, video)

    def test_load_runner_video_video_does_not_exist(self):
        """Should return None if the video does not exist."""
        VideoFactory(uuid="123e4567-e89b-12d3-a456-426655440002")

        runner_job = RunnerJobFactory(
            privatePayload={"videoUUID": "123e4567-e89b-12d3-a456-426655440001"}
        )

        result = load_runner_video(runner_job)

        self.assertIsNone(result)

    @patch(
        "django_peertube_runner_connector.utils.job_handlers.utils.move_to_next_state"
    )
    def test_on_transcoding_ended_move_to_next_state(self, mock_move_to_next_state):
        """Should be able to move video to the next state and decrease pendingTranscode column."""
        video = VideoFactory(uuid="123e4567-e89b-12d3-a456-426655440002")
        job_info = VideoJobInfoFactory(video=video, pendingTranscode=1)

        on_transcoding_ended(video, True)
        job_info.refresh_from_db()

        self.assertEqual(job_info.pendingTranscode, 0)
        mock_move_to_next_state.assert_called_once_with(video=video)

    @patch(
        "django_peertube_runner_connector.utils.job_handlers.utils.move_to_next_state"
    )
    def test_on_transcoding_ended(self, mock_move_to_next_state):
        """Should decrease pendingTranscode column."""
        video = VideoFactory(uuid="123e4567-e89b-12d3-a456-426655440002")
        job_info = VideoJobInfoFactory(video=video, pendingTranscode=1)

        on_transcoding_ended(video, False)
        job_info.refresh_from_db()

        self.assertEqual(job_info.pendingTranscode, 0)
        mock_move_to_next_state.assert_not_called()

    def test_is_transcription_language_valid_all_language_settings(self):
        """
        Should check if a transcription language is valid using ALL_LANGUAGES settings.
        """

        with self.settings(ALL_LANGUAGES=(("en", "English"), ("fr", "French"))):
            self.assertTrue(is_transcription_language_valid("en"))
            self.assertTrue(is_transcription_language_valid("fr"))
            self.assertFalse(is_transcription_language_valid("es"))

    def test_is_transcription_language_valid_languages_settings(self):
        """
        Should check if a transcription language is valid using LANGUAGES settings.
        """
        with self.settings(LANGUAGES=(("en", "English"), ("fr", "French"))):
            self.assertTrue(is_transcription_language_valid("en"))
            self.assertTrue(is_transcription_language_valid("fr"))
            self.assertFalse(is_transcription_language_valid("es"))

    @override_settings(
        TRANSCRIPTION_ENDED_CALLBACK_PATH="tests_django_peertube_runner_connector."
        "utils.job_handlers.test_utils.mock_transcription_ended_callback"
    )
    @patch("django_peertube_runner_connector.utils.job_handlers.utils.logger")
    def test_on_transcription_ended(self, mock_logger):
        """Should be able to handle transcription ended event."""
        video = VideoFactory()
        language = "en"
        vtt_path = "/path/to/file.vtt"

        on_transcription_ended(video, language, vtt_path)

        mock_transcription_ended_callback.assert_called_once_with(
            video, language, vtt_path
        )

        video.refresh_from_db()
        self.assertEqual(video.language, language)
        self.assertEqual(video.transcriptFileName, vtt_path)

        mock_logger.info.assert_called_once_with(
            "Transcription ended for %s.", str(video.uuid)
        )

    @override_settings(
        TRANSCRIPTION_ERROR_CALLBACK_PATH="tests_django_peertube_runner_connector."
        "utils.job_handlers.test_utils.mock_transcription_error_callback"
    )
    @patch("django_peertube_runner_connector.utils.job_handlers.utils.logger")
    def test_on_transcription_error(self, mock_logger):
        """Should be able to handle transcription error event."""
        video = VideoFactory()

        on_transcription_error(video)

        mock_transcription_error_callback.assert_called_once_with(video)
        mock_logger.error.assert_called_once_with(
            "Transcription error for %s.", str(video.uuid)
        )

    @override_settings(TRANSCRIPTION_ENDED_CALLBACK_PATH=None)
    @patch("django_peertube_runner_connector.utils.job_handlers.utils.logger")
    def test_on_transcription_error_no_callback(self, mock_logger):
        """Should be able to handle transcription ended event without callback."""
        video = VideoFactory()

        on_transcription_error(video)

        mock_logger.info.assert_called_with(
            "No transcription_error callback defined for video %s.", str(video.uuid)
        )
        mock_transcription_ended_callback.assert_not_called()
