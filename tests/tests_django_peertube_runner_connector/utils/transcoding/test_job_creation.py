"""Test the transcoding job creation file."""

from unittest.mock import Mock, call, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from django_peertube_runner_connector.factories import (
    RunnerJobFactory,
    VideoFactory,
    VideoFileFactory,
)
from django_peertube_runner_connector.models import RunnerJob, VideoResolution
from django_peertube_runner_connector.storage import video_storage
from django_peertube_runner_connector.utils.transcoding.job_creation import (
    build_lower_resolution_job_payloads,
    compute_output_fps,
    create_transcoding_jobs,
    get_closest_framerate_standard,
)

from ...probe_response import probe_response


class TranscodingJobCreationTestCase(TestCase):
    """Test the transcoding job creation utils file."""

    def setUp(self):
        """Create a video , a related video file and a file."""
        new_file = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )

        self.filename = video_storage.save("test.mp4", new_file)
        self.video = VideoFactory()
        self.video_file = VideoFileFactory(
            video=self.video,
            filename=self.filename,
            resolution=VideoResolution.H_1440P,
        )

    @override_settings(
        TRANSCODING_FPS_MIN=2,
        TRANSCODING_FPS_MAX=60,
        TRANSCODING_FPS_AVERAGE=30,
        TRANSCODING_FPS_KEEP_ORIGIN_FPS_RESOLUTION_MIN=720,
    )
    def test_compute_output_fps(self):
        """Should compute the output fps depending on the resolution and settings."""
        fps = 30
        resolution = 480
        output_fps = compute_output_fps(resolution, fps)
        self.assertEqual(output_fps, 30)

        fps = 31
        resolution = 1080
        output_fps = compute_output_fps(resolution, fps)
        self.assertEqual(output_fps, 31)

        fps = 60
        resolution = 1080
        output_fps = compute_output_fps(resolution, fps)
        self.assertEqual(output_fps, 60)

        fps = 120
        resolution = 2160
        output_fps = compute_output_fps(resolution, fps)
        self.assertEqual(output_fps, 60)

        fps = 1
        resolution = 240
        with self.assertRaises(ValueError):
            compute_output_fps(resolution, fps)

    @override_settings(
        TRANSCODING_FPS_MIN=1,
        TRANSCODING_FPS_STANDARD=[20, 25, 30],
        TRANSCODING_FPS_HD_STANDARD=[50, 60],
    )
    def test_get_closest_framerate_standard(self):
        """Should return the closest framerate standard depending on the settings."""
        fps = 23.976
        standard_fps = get_closest_framerate_standard(fps, "STANDARD")
        self.assertEqual(standard_fps, 20)

        fps = 29.97
        standard_fps = get_closest_framerate_standard(fps, "STANDARD")
        self.assertEqual(standard_fps, 25)

        fps = 59.94
        standard_fps = get_closest_framerate_standard(fps, "STANDARD")
        self.assertEqual(standard_fps, 25)

        fps = 23.976
        hd_standard_fps = get_closest_framerate_standard(fps, "HD_STANDARD")
        self.assertEqual(hd_standard_fps, 50)

        fps = 59
        hd_standard_fps = get_closest_framerate_standard(fps, "HD_STANDARD")
        self.assertEqual(hd_standard_fps, 50)

        fps = 61
        hd_standard_fps = get_closest_framerate_standard(fps, "HD_STANDARD")
        self.assertEqual(hd_standard_fps, 60)

    @override_settings(
        TRANSCODING_RESOLUTIONS_144P=False,
        TRANSCODING_RESOLUTIONS_240P=False,
        TRANSCODING_RESOLUTIONS_360P=True,
        TRANSCODING_RESOLUTIONS_480P=True,
        TRANSCODING_RESOLUTIONS_720P=False,
        TRANSCODING_RESOLUTIONS_1080P=False,
        TRANSCODING_RESOLUTIONS_1440P=False,
        TRANSCODING_RESOLUTIONS_2160P=False,
    )
    def test_create_transcoding_jobs(self):
        """Should create all runner jobs needed to transcode the video."""
        self.assertEqual(RunnerJob.objects.count(), 0)
        self.assertEqual(probe_response.get("streams")[0].get("height"), 540)
        create_transcoding_jobs(self.video, self.video_file, "domain", probe_response)

        runner_jobs = RunnerJob.objects.all().order_by(
            "createdAt", "dependsOnRunnerJob"
        )

        # First job does not depend on any other job
        self.assertIsNone(runner_jobs[0].dependsOnRunnerJob)
        self.assertEqual(runner_jobs[0].payload.get("output").get("resolution"), 480)

        # Second job depends on the first job
        self.assertEqual(runner_jobs[1].dependsOnRunnerJob, runner_jobs[0])
        self.assertEqual(runner_jobs[1].payload.get("output").get("resolution"), 360)

        self.assertEqual(len(runner_jobs), 2)

    @patch(
        "django_peertube_runner_connector.utils."
        "transcoding.job_creation.VODHLSTranscodingJobHandler"
    )
    def test_build_lower_resolution_job_payloads(self, mock_job_handler):
        """Should create 2 transcoding jobs for parent and child."""
        mocked_class = Mock()
        mock_job_handler.return_value = mocked_class

        main_runner_job = RunnerJobFactory(type="vod-hls-transcoding")

        build_lower_resolution_job_payloads(
            video=self.video,
            input_video_resolution=540,
            input_video_fps=30,
            has_audio=True,
            main_runner_job=main_runner_job,
            domain="domain",
        )

        mocked_class.create.assert_has_calls(
            [
                call(
                    video=self.video,
                    resolution=360,
                    fps=30,
                    depends_on_runner_job=main_runner_job,
                    domain="domain",
                ),
                call(
                    video=self.video,
                    resolution=480,
                    fps=30,
                    depends_on_runner_job=main_runner_job,
                    domain="domain",
                ),
            ]
        )
