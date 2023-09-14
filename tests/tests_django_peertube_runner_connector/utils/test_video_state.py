"""Test the video state file."""
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from django_peertube_runner_connector.factories import VideoFactory
from django_peertube_runner_connector.models import VideoState
from django_peertube_runner_connector.utils.video_state import (
    build_next_video_state,
    move_to_failed_transcoding_state,
    move_to_next_state,
    move_to_published_state,
    video_is_published,
)


mock_callback_video_published = Mock()


class VideoStateTestCase(TestCase):
    """Test the video state utils file."""

    def setUp(self):
        """Create a video."""
        self.video = VideoFactory()
        mock_callback_video_published.reset_mock()

    def test_build_next_video_state(self):
        """Should return the next video state depending on the current."""
        with self.assertRaises(ValueError):
            build_next_video_state(VideoState.PUBLISHED)

        self.assertEqual(
            build_next_video_state(VideoState.TO_TRANSCODE), VideoState.PUBLISHED
        )
        self.assertEqual(
            build_next_video_state(VideoState.TO_IMPORT), VideoState.TO_TRANSCODE
        )
        self.assertEqual(
            build_next_video_state(VideoState.WAITING_FOR_LIVE),
            VideoState.TO_TRANSCODE,
        )
        self.assertEqual(
            build_next_video_state(VideoState.LIVE_ENDED), VideoState.TO_TRANSCODE
        )

        self.assertEqual(
            build_next_video_state(VideoState.TO_MOVE_TO_EXTERNAL_STORAGE),
            VideoState.PUBLISHED,
        )

        self.assertEqual(
            build_next_video_state(VideoState.TRANSCODING_FAILED),
            VideoState.TO_TRANSCODE,
        )

        self.assertEqual(
            build_next_video_state(VideoState.TO_MOVE_TO_EXTERNAL_STORAGE_FAILED),
            VideoState.TO_TRANSCODE,
        )

        self.assertEqual(
            build_next_video_state(VideoState.TO_EDIT), VideoState.PUBLISHED
        )

    @patch("django_peertube_runner_connector.utils.video_state.video_is_published")
    def test_move_to_next_state(self, mock_is_published):
        """If video is published, should call the video_is_published function"""
        self.video.state = VideoState.PUBLISHED
        self.video.save()
        mock_is_published(self.video)
        mock_is_published.assert_called_once_with(self.video)

    @patch("django_peertube_runner_connector.utils.video_state.build_next_video_state")
    @patch("django_peertube_runner_connector.utils.video_state.move_to_published_state")
    def test_move_to_next_state_will_be_a_published_video(self, mock_move, mock_build):
        """If next video state is published, should call move_to_published_state."""
        self.video.state = VideoState.TO_TRANSCODE
        self.video.save()
        mock_build.return_value = VideoState.PUBLISHED
        move_to_next_state(self.video)
        mock_build.assert_called_once_with(VideoState.TO_TRANSCODE)
        mock_move.assert_called_once_with(self.video)

    @patch("django_peertube_runner_connector.utils.video_state.build_next_video_state")
    @patch("django_peertube_runner_connector.utils.video_state.move_to_published_state")
    def test_move_to_next_state_on_to_import_video(self, mock_move, mock_build):
        """If next video state is not published, should do nothing."""
        self.video.state = VideoState.TO_TRANSCODE
        self.video.save()
        mock_build.return_value = VideoState.TO_IMPORT
        move_to_next_state(self.video)
        mock_build.assert_called_once_with(VideoState.TO_TRANSCODE)
        mock_move.assert_not_called()

    def test_move_to_failed_transcoding_state(self):
        """Should  move to a failed transcoding state."""
        self.video.state = VideoState.TO_TRANSCODE
        self.video.save()

        move_to_failed_transcoding_state(self.video)

        self.assertEqual(self.video.state, VideoState.TRANSCODING_FAILED)

    def test_move_to_failed_transcoding_state_already_failed(self):
        """If the video is already in a failed transcoding state, do nothing."""
        self.video.state = VideoState.TRANSCODING_FAILED
        self.video.save()

        move_to_failed_transcoding_state(self.video)

        self.assertEqual(self.video.state, VideoState.TRANSCODING_FAILED)

    @patch("django_peertube_runner_connector.utils.video_state.video_is_published")
    def test_move_to_published_state(self, mock_video_is_published):
        """Should move to a published state."""
        move_to_published_state(self.video)

        self.assertEqual(self.video.state, VideoState.PUBLISHED)
        mock_video_is_published.assert_called_once_with(self.video)

    @override_settings(
        TRANSCODING_VIDEO_IS_PUBLISHED_CALLBACK_PATH="tests_django_peertube_runner_connector."
        "utils.test_video_state.mock_callback_video_published"
    )
    def test_video_is_published(self):
        """Should call the video callback defined in settings."""
        video_is_published(self.video)

        mock_callback_video_published.assert_called_once_with(self.video)
        mock_callback_video_published.reset_mock()

    @override_settings(TRANSCODING_VIDEO_IS_PUBLISHED_CALLBACK_PATH="")
    @patch("django_peertube_runner_connector.utils.video_state.logger")
    def test_video_is_published_no_callback(self, mock_logger):
        """Should do nothing."""
        video_is_published(self.video)

        mock_logger.assert_not_called()
        mock_callback_video_published.assert_not_called()

    @override_settings(TRANSCODING_VIDEO_IS_PUBLISHED_CALLBACK_PATH="fakecallback.test")
    @patch("django_peertube_runner_connector.utils.video_state.logger")
    def test_video_is_published_wrong_callback(self, mock_logger):
        """Should do nothing and raise a warning."""
        video_is_published(self.video)

        mock_logger.error.assert_called_with(
            "Error importing video_is_published callback.",
        )
        mock_callback_video_published.assert_not_called()
