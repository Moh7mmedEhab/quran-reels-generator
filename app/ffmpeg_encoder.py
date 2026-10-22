"""FFmpeg hardware-encoder discovery and MoviePy-to-hardware frame bridge."""
from __future__ import annotations

from functools import lru_cache
import math
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time


def hardware_encoder_status(*, refresh: bool = False) -> dict:
    """Return cached device probes, optionally rechecking newly attached GPUs."""
    if refresh:
        _probe_hardware_encoder_status.cache_clear()
    return _probe_hardware_encoder_status()


@lru_cache(maxsize=1)
def _probe_hardware_encoder_status() -> dict:
    """Probe NVIDIA NVENC and Intel Quick Sync on the configured system FFmpeg."""
    ffmpeg = os.environ.get("QURAN_REELS_FFMPEG") or shutil.which("ffmpeg")
    if not ffmpeg:
        missing = "System FFmpeg was not found; CPU rendering remains available."
        return {"ffmpeg": None, "nvidia": {"available": False, "name": "NVIDIA NVENC", "reason": missing},
                "intel": {"available": False, "name": "Intel Quick Sync", "reason": missing}}
    try:
        encoders = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"], capture_output=True,
            text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        unavailable = "Could not inspect the configured system FFmpeg."
        return {"ffmpeg": ffmpeg, "nvidia": {"available": False, "name": "NVIDIA NVENC", "reason": unavailable},
                "intel": {"available": False, "name": "Intel Quick Sync", "reason": unavailable}}
    listed = encoders.stdout if not encoders.returncode else ""
    try:
        detected = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=3, check=False,
        )
        nvidia_gpus = [line.strip() for line in detected.stdout.splitlines()] if detected.returncode == 0 else []
    except (OSError, subprocess.TimeoutExpired):
        nvidia_gpus = []

    # Prefer the Quadro T2000 when several NVIDIA cards are present. NVENC's
    # -gpu selector is an ordinal; nvidia-smi exposes the matching device index.
    preferred_gpu = os.environ.get("QURAN_REELS_NVIDIA_GPU")
    if preferred_gpu is None:
        quadro = next((line for line in nvidia_gpus if "quadro t2000" in line.casefold()), None)
        try:
            preferred_gpu = quadro.split(",", 1)[0].strip() if quadro else "0"
        except (AttributeError, ValueError):
            preferred_gpu = "0"
    try:
        preferred_gpu_index = int(preferred_gpu)
    except (TypeError, ValueError):
        preferred_gpu_index = 0

    results = {"ffmpeg": ffmpeg}
    for key, codec, display_name in (("nvidia", "h264_nvenc", "NVIDIA NVENC"),
                                      ("intel", "h264_qsv", "Intel UHD · Quick Sync")):
        if codec not in listed:
            results[key] = {"available": False, "name": display_name,
                            "reason": f"System FFmpeg does not include {codec}."}
            continue
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                   "color=c=black:s=64x64:r=30:d=1", "-frames:v", "1", "-an",
                   "-c:v", codec]
        if key == "nvidia":
            command.extend(["-gpu", str(preferred_gpu_index)])
        if key == "intel":
            command.extend(["-global_quality", "25"])
        command.extend(["-f", "null", "-"])
        try:
            probe = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
            available = probe.returncode == 0
            details = (probe.stderr or "").casefold()
            reason = None if available else (
                "NVIDIA NVENC cannot access a CUDA device. Check that the NVIDIA driver is active."
                if key == "nvidia" and ("cuda_error_no_device" in details or "no cuda-capable device" in details)
                else "Intel Quick Sync cannot access an Intel media device. Check the graphics driver and /dev/dri permissions."
                if key == "intel" else (probe.stderr.strip().splitlines()[-1][:240] if probe.stderr.strip() else "Hardware encoder probe failed.")
            )
        except (OSError, subprocess.TimeoutExpired):
            available, reason = False, "Hardware encoder probe did not complete."
        name = display_name
        if key == "nvidia" and nvidia_gpus:
            try:
                selected_gpu = next(
                    (line for line in nvidia_gpus
                     if line.split(",", 1)[0].strip() == str(preferred_gpu_index)),
                    nvidia_gpus[0],
                )
                _, name = selected_gpu.split(",", 1)
                name = name.strip()
            except ValueError:
                name = selected_gpu
        results[key] = {"available": available, "name": name, "reason": reason,
                        "ffmpeg_encoder": codec}
        if key == "nvidia":
            results[key]["gpu_index"] = preferred_gpu_index
    return results


def nvenc_status() -> dict:
    """Backward-compatible NVIDIA capability view."""
    status = hardware_encoder_status()
    return {**status["nvidia"], "ffmpeg": status.get("ffmpeg"),
            "gpu_name": status["nvidia"].get("name")}


def build_nvenc_command(ffmpeg: str, *, width: int, height: int, fps: int,
                        output_path: str | Path, audio_path: str | Path | None,
                        crf: int, audio_bitrate: str, audio_fps: int,
                        gpu_index: int | None = None) -> list[str]:
    """Build the raw-RGB input command used to encode a MoviePy composition."""
    command = [
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-video_size", f"{width}x{height}",
        "-framerate", str(fps), "-i", "pipe:0",
    ]
    if audio_path:
        command.extend(["-i", str(audio_path)])
    command.extend(["-map", "0:v:0", "-c:v", "h264_nvenc"])
    if gpu_index is not None:
        command.extend(["-gpu", str(gpu_index)])
    command.extend([
        "-preset", "p4",
        "-rc", "vbr", "-cq", str(crf), "-b:v", "0", "-pix_fmt", "yuv420p",
    ])
    if audio_path:
        command.extend(["-map", "1:a:0", "-c:a", "aac", "-b:a", audio_bitrate,
                        "-ar", str(audio_fps), "-shortest"])
    else:
        command.append("-an")
    command.extend(["-movflags", "+faststart", str(output_path)])
    return command


def build_qsv_command(ffmpeg: str, *, width: int, height: int, fps: int,
                      output_path: str | Path, audio_path: str | Path | None,
                      crf: int, audio_bitrate: str, audio_fps: int) -> list[str]:
    """Build a raw-RGB input command for Intel Quick Sync H.264 encoding."""
    command = [str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-video_size", f"{width}x{height}",
               "-framerate", str(fps), "-i", "pipe:0"]
    if audio_path:
        command.extend(["-i", str(audio_path)])
    command.extend(["-map", "0:v:0", "-vf", "format=nv12", "-c:v", "h264_qsv",
                    "-global_quality", str(crf), "-pix_fmt", "nv12"])
    if audio_path:
        command.extend(["-map", "1:a:0", "-c:a", "aac", "-b:a", audio_bitrate,
                        "-ar", str(audio_fps), "-shortest"])
    else:
        command.append("-an")
    command.extend(["-movflags", "+faststart", str(output_path)])
    return command


def write_hardware_video(clip, output_path: str | Path, *, fps: int, ffmpeg: str,
                         encoder: str, crf: int, audio_bitrate: str, audio_fps: int,
                         progress_callback=None, cancel_event=None,
                         gpu_index: int | None = None) -> None:
    """Pipe MoviePy-composited frames to a hardware H.264 encoder.

    Frame composition remains in MoviePy/Python; NVENC performs the H.264
    encoding step. A temporary PCM file carries the already mixed MoviePy audio.
    """
    from .job_errors import JobCancelled

    output_path = Path(output_path)
    width, height = map(int, clip.size)
    audio = getattr(clip, "audio", None)
    audio_path = output_path.with_name(f"{output_path.stem}_{encoder}_audio.wav") if audio else None
    if audio_path:
        try:
            audio.write_audiofile(str(audio_path), fps=audio_fps, codec="pcm_s16le",
                                  nbytes=2, logger=None)
        except Exception:
            audio_path.unlink(missing_ok=True)
            raise
    command_builder = build_nvenc_command if encoder == "nvidia" else build_qsv_command
    command = command_builder(ffmpeg, width=width, height=height, fps=fps,
                              output_path=output_path, audio_path=audio_path, crf=crf,
                              audio_bitrate=audio_bitrate, audio_fps=audio_fps,
                              **({"gpu_index": gpu_index} if encoder == "nvidia" else {}))
    encoder_name = "NVIDIA NVENC" if encoder == "nvidia" else "Intel Quick Sync"
    process = None
    stderr_lines: list[str] = []
    reader = None
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        def drain_stderr():
            for line in process.stderr:
                stderr_lines.append(line.decode("utf-8", errors="replace").rstrip())

        reader = threading.Thread(target=drain_stderr, daemon=True)
        reader.start()
        frame_count = max(1, math.ceil(float(clip.duration) * fps))
        started = time.monotonic()
        for index, frame in enumerate(clip.iter_frames(fps=fps, dtype="uint8", logger=None)):
            if cancel_event is not None and cancel_event.is_set():
                process.terminate()
                process.wait(timeout=5)
                raise JobCancelled()
            process.stdin.write(frame.tobytes())
            if progress_callback and (index == 0 or (index + 1) % max(1, fps // 2) == 0):
                done = index + 1
                elapsed = max(time.monotonic() - started, .001)
                speed = done / elapsed
                eta = max(0.0, (frame_count - done) / speed) if speed > .01 else None
                fraction = min(1.0, done / frame_count)
                try:
                    progress_callback(fraction, render_speed_fps=speed,
                                      estimated_remaining_seconds=eta)
                except TypeError:
                    progress_callback(fraction)
        process.stdin.close()
        return_code = process.wait()
        reader.join(timeout=2)
        if return_code:
            detail = "\n".join(stderr_lines[-8:]) or f"FFmpeg exited with code {return_code}."
            raise RuntimeError(f"{encoder_name} video encoding failed: {detail}")
        if progress_callback:
            progress_callback(1.0)
    except BrokenPipeError as exc:
        if process is not None:
            process.wait(timeout=5)
        detail = "\n".join(stderr_lines[-8:]) or "FFmpeg closed its video input unexpectedly."
        raise RuntimeError(f"{encoder_name} video encoding failed: {detail}") from exc
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        if process is not None and process.stdin and not process.stdin.closed:
            process.stdin.close()
        if reader is not None:
            reader.join(timeout=2)
        if audio_path:
            audio_path.unlink(missing_ok=True)


def write_nvenc_video(clip, output_path: str | Path, **kwargs) -> None:
    """Backward-compatible NVIDIA-specific wrapper."""
    write_hardware_video(clip, output_path, encoder="nvidia", **kwargs)
