"""Validate rendered media by opening and decoding real audio/video samples."""

from pathlib import Path

import numpy as np


def validate_rendered_output(path, *, expected_size, require_audio=True):
    """Decode the first/last video frames and an audio sample before export is marked ready."""
    try:
        from moviepy import VideoFileClip
    except ImportError:
        from moviepy.editor import VideoFileClip

    path = Path(path)
    clip = None
    try:
        clip = VideoFileClip(str(path))
        duration = float(clip.duration or 0)
        if duration <= 0 or clip.w <= 0 or clip.h <= 0:
            raise ValueError("The encoded MP4 has no playable video stream.")
        if (int(clip.w), int(clip.h)) != tuple(expected_size):
            raise ValueError("The encoded MP4 dimensions do not match the selected export settings.")
        frame_times = sorted({0.0, max(0.0, duration - 1 / max(float(clip.fps or 1), 1))})
        for timestamp in frame_times:
            frame = np.asarray(clip.get_frame(timestamp))
            if frame.ndim != 3 or frame.shape[0] != clip.h or frame.shape[1] != clip.w:
                raise ValueError("The encoded MP4 contains an unreadable video frame.")

        audio_duration = None
        if require_audio:
            if clip.audio is None:
                raise ValueError("The rendered MP4 is missing its Quran recitation audio stream.")
            audio_duration = float(clip.audio.duration or 0)
            if audio_duration <= 0:
                raise ValueError("The rendered MP4 audio stream is empty.")
            sample = np.asarray(clip.audio.get_frame(min(.1, audio_duration / 2)))
            if sample.size == 0 or not np.isfinite(sample).all():
                raise ValueError("The rendered MP4 audio stream could not be decoded.")
        return {"playable": True, "video_duration": duration, "audio_duration": audio_duration}
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"The exported MP4 failed playback validation: {exc}") from exc
    finally:
        if clip is not None:
            clip.close()
