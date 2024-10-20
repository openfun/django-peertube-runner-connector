"""Job handler for vod web video transcoding jobs."""

import logging

from .abstract_vod_transcoding_job_handler import AbstractVODTranscodingJobHandler


logger = logging.getLogger(__name__)

# https://github.com/Chocobozzz/PeerTube/blob/develop/server/server/lib/runners/job-handlers/vod-web-video-transcoding-job-handler.ts


class VODWebVideoTranscodingJobHandler(AbstractVODTranscodingJobHandler):
    """Job handler for vod web video transcoding jobs."""

    # def create(self, video, resolution, fps, depends_on_runner_job, priority):
    #     job_uuid = uuid.uuid4()
    #     payload = {
    #         "input": {
    #             "videoFileUrl": generate_runner_transcoding_video_input_file_url(
    #                 str(job_uuid), str(video.uuid)
    #             )
    #         },
    #         "output": {"resolution": resolution, "fps": fps},
    #     }

    #     private_payload = {
    #         "isNewVideo": True,
    #         "videoUUID": str(video.uuid),
    #     }

    #     job = self.create_runner_job(
    #         type="vod-web-video-transcoding",
    #         job_uuid=job_uuid,
    #         payload=payload,
    #         private_payload=private_payload,
    #         depends_on_runner_job=depends_on_runner_job,
    #         priority=priority,
    #     )

    #     VideoJobInfo.increase_or_create(video.uuid, "pendingTranscode")

    #     return job

    # def specific_complete(self, runner_job, result_payload):
    #     private_payload = runner_job.privatePayload

    #     video = load_transcoding_runner_video(runner_job)
    #     if not video:
    #         return

    #     video_file = result_payload["video_file"]

    #     with NamedTemporaryFile(delete=False) as f:
    #         f.write(video_file.read())
    #         video_file_path = f.name

    #     on_vod_web_video_or_audio_merge_transcoding_job(
    #         video=video,
    #         video_file_path=video_file_path,
    #         private_payload=private_payload,
    #     )

    #     logger.info(
    #         "Runner VOD web video transcoding job %s for %s ended.",
    #         runner_job.uuid,
    #         video.uuid,
    #     )
