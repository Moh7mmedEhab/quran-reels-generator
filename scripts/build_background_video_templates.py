"""Build the small, silent MP4 loops used by the bundled Video gallery.

All inputs are existing, locally bundled project backgrounds. This script does
not fetch media from the internet. Run it from any directory with:
    python scripts/build_background_video_templates.py
"""
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.background_motion import image_animation_phase, image_motion_values  # noqa: E402
from app.background_video_templates import BACKGROUND_VIDEO_TEMPLATES  # noqa: E402


WIDTH, HEIGHT, FPS = 360, 640, 24
PRESETS = {
    "misty_forest_drift": ("gentle_movement", .6),
    "marble_arch_glow": ("cinematic_zoom", .75),
    "moonlit_horizon": ("floating_camera", .5),
    "midnight_coast_drift": ("floating_camera", .16),
}


def render_frame(base: Image.Image, preset: str, intensity: float, phase: float,
                 width: int = WIDTH, height: int = HEIGHT) -> bytes:
    zoom, crop_x, crop_y = image_motion_values(preset, phase, intensity)
    scaled_width, scaled_height = max(width, round(width * zoom)), max(height, round(height * zoom))
    scaled = base.resize((scaled_width, scaled_height), Image.Resampling.BICUBIC)
    x = min(scaled_width - width, max(0, round((scaled_width - width) * crop_x)))
    y = min(scaled_height - height, max(0, round((scaled_height - height) * crop_y)))
    frame = scaled.crop((x, y, x + width, y + height))
    frame = ImageEnhance.Brightness(frame).enhance(.84)
    return np.asarray(frame, dtype=np.uint8).tobytes()


def build(template_id: str, template: dict) -> Path:
    source = ROOT / "static" / "assets" / "backgrounds" / f"{template['theme']}.jpg"
    output = ROOT / "static" / "assets" / "background-videos" / template["filename"]
    output.parent.mkdir(parents=True, exist_ok=True)
    duration = float(template["duration"])
    width, height = int(template.get("width", WIDTH)), int(template.get("height", HEIGHT))
    fps = int(template.get("fps", FPS))
    frame_count = round(duration * fps)
    base = ImageOps.fit(Image.open(source).convert("RGB"), (width, height),
                        method=Image.Resampling.LANCZOS)
    preset, intensity = PRESETS[template_id]
    ffmpeg = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-video_size", f"{width}x{height}",
        "-framerate", str(fps), "-i", "pipe:0", "-frames:v", str(frame_count), "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-metadata", f"title={template['name']}", str(output),
    ]
    process = subprocess.Popen(ffmpeg, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE)
    try:
        for index in range(frame_count):
            phase = image_animation_phase(index / fps, duration, speed=1, start_time=0)
            process.stdin.write(render_frame(base, preset, intensity, phase, width, height))
        process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace")
        return_code = process.wait()
    except Exception:
        process.kill()
        process.wait()
        output.unlink(missing_ok=True)
        raise
    if return_code:
        output.unlink(missing_ok=True)
        raise RuntimeError(f"FFmpeg could not build {template['name']}: {stderr[-1200:]}")
    return output


if __name__ == "__main__":
    for key, item in BACKGROUND_VIDEO_TEMPLATES.items():
        target = build(key, item)
        print(f"Built {item['name']}: {target.relative_to(ROOT)} ({target.stat().st_size:,} bytes)")
