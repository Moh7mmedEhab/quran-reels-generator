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
}


def render_frame(base: Image.Image, preset: str, intensity: float, phase: float) -> bytes:
    zoom, crop_x, crop_y = image_motion_values(preset, phase, intensity)
    width, height = max(WIDTH, round(WIDTH * zoom)), max(HEIGHT, round(HEIGHT * zoom))
    scaled = base.resize((width, height), Image.Resampling.BICUBIC)
    x = min(width - WIDTH, max(0, round((width - WIDTH) * crop_x)))
    y = min(height - HEIGHT, max(0, round((height - HEIGHT) * crop_y)))
    frame = scaled.crop((x, y, x + WIDTH, y + HEIGHT))
    frame = ImageEnhance.Brightness(frame).enhance(.84)
    return np.asarray(frame, dtype=np.uint8).tobytes()


def build(template_id: str, template: dict) -> Path:
    source = ROOT / "static" / "assets" / "backgrounds" / f"{template['theme']}.jpg"
    output = ROOT / "static" / "assets" / "background-videos" / template["filename"]
    output.parent.mkdir(parents=True, exist_ok=True)
    duration = float(template["duration"])
    frame_count = round(duration * FPS)
    base = ImageOps.fit(Image.open(source).convert("RGB"), (WIDTH, HEIGHT),
                        method=Image.Resampling.LANCZOS)
    preset, intensity = PRESETS[template_id]
    ffmpeg = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}",
        "-framerate", str(FPS), "-i", "pipe:0", "-frames:v", str(frame_count), "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-metadata", f"title={template['name']}", str(output),
    ]
    process = subprocess.Popen(ffmpeg, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE)
    try:
        for index in range(frame_count):
            phase = image_animation_phase(index / FPS, duration, speed=1, start_time=0)
            process.stdin.write(render_frame(base, preset, intensity, phase))
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
