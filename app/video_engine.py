"""MoviePy composition for timed Quran reel captions and backgrounds."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZES = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}
TRANSITIONS = {"crossfade", "cut"}
THEMES = {
    "misty_forest": {"name": "Misty Forest", "top": (19, 31, 40), "bottom": (55, 85, 75), "accent": (208, 190, 139)},
    "desert_dawn": {"name": "Desert Dawn", "top": (48, 40, 68), "bottom": (202, 130, 89), "accent": (255, 216, 155)},
    "masjid_night": {"name": "Masjid at Night", "top": (7, 16, 44), "bottom": (35, 60, 83), "accent": (228, 197, 122)},
    "ocean_calm": {"name": "Ocean Calm", "top": (10, 45, 65), "bottom": (42, 118, 126), "accent": (195, 223, 205)},
    "aurora_drift": {"name": "Aurora Drift", "top": (11, 24, 47), "bottom": (76, 79, 112), "accent": (165, 255, 219)},
    "olive_garden": {"name": "Olive Garden", "top": (26, 43, 39), "bottom": (106, 126, 83), "accent": (227, 205, 133)},
    "golden_dunes": {"name": "Golden Dunes", "top": (72, 51, 54), "bottom": (229, 173, 104), "accent": (255, 229, 169)},
    "marble_arch": {"name": "Marble Arch", "top": (28, 47, 61), "bottom": (111, 139, 143), "accent": (238, 219, 170)},
    "sapphire_horizon": {"name": "Sapphire Horizon", "top": (12, 31, 72), "bottom": (69, 135, 190), "accent": (202, 228, 255), "pattern": "waves"},
    "rose_sand": {"name": "Rose Sand", "top": (68, 39, 55), "bottom": (205, 129, 123), "accent": (255, 213, 190), "pattern": "dunes"},
    "jade_courtyard": {"name": "Jade Courtyard", "top": (13, 48, 44), "bottom": (65, 130, 105), "accent": (201, 228, 174), "pattern": "arches"},
    "lavender_twilight": {"name": "Lavender Twilight", "top": (42, 35, 69), "bottom": (132, 103, 157), "accent": (232, 215, 255), "pattern": "stars"},
    "copper_dusk": {"name": "Copper Dusk", "top": (54, 37, 45), "bottom": (190, 105, 70), "accent": (255, 204, 148), "pattern": "dunes"},
    "cloud_morning": {"name": "Cloud Morning", "top": (69, 108, 135), "bottom": (177, 201, 202), "accent": (255, 244, 216), "pattern": "clouds"},
    "crescent_garden": {"name": "Crescent Garden", "top": (13, 41, 52), "bottom": (70, 115, 84), "accent": (235, 226, 175), "pattern": "arches"},
    "sahara_moon": {"name": "Sahara Moon", "top": (35, 37, 54), "bottom": (117, 102, 98), "accent": (244, 223, 183), "pattern": "dunes"},
    "turquoise_mosaic": {"name": "Turquoise Mosaic", "top": (12, 61, 72), "bottom": (62, 150, 155), "accent": (197, 241, 228), "pattern": "mosaic"},
    "plum_evening": {"name": "Plum Evening", "top": (47, 30, 52), "bottom": (131, 73, 104), "accent": (246, 202, 222), "pattern": "stars"},
    "pearl_dawn": {"name": "Pearl Dawn", "top": (62, 69, 82), "bottom": (197, 185, 167), "accent": (255, 240, 207), "pattern": "clouds"},
    "midnight_blue": {"name": "Midnight Blue", "top": (16, 25, 64), "bottom": (63, 84, 143), "accent": (214, 223, 255), "pattern": "stars"},
}
CAPTION_COLORS = {
    "white": "#ffffff", "ivory": "#fff3d2", "gold": "#ffd166", "amber": "#ffb703",
    "sky": "#75d5ff", "blue": "#006aff", "cyan": "#63f3e8", "mint": "#91f2c3",
    "lime": "#c7f464", "rose": "#ff8fa3", "coral": "#ff8066", "lavender": "#d6b8ff",
    "silver": "#dbeafe", "emerald": "#34d399", "orange": "#ff9f43", "pink": "#ff6fb5",
}


def caption_render_options(caption_style, caption_color):
    """Return the shared text-renderer settings for preview and final video."""
    options = {
        "karaoke": {"stroke_width": 3, "stroke_fill": (0, 0, 0, 225),
                    "backdrop_fill": (0, 0, 0, 125), "glow_radius": 11},
        "minimal": {"stroke_width": 1, "stroke_fill": (0, 0, 0, 190),
                    "backdrop_fill": (0, 0, 0, 95), "padding": 20},
        "classic": {"stroke_width": 3, "stroke_fill": (0, 0, 0, 235),
                    "backdrop_fill": (5, 8, 13, 165), "padding": 32},
        "arabic_only": {"stroke_width": 3, "stroke_fill": (0, 0, 0, 230),
                        "backdrop_fill": None},
    }
    if caption_style not in options:
        raise ValueError("Unsupported caption style.")
    if caption_color not in CAPTION_COLORS:
        raise ValueError("Unsupported caption color.")
    settings = dict(options[caption_style])
    hex_color = CAPTION_COLORS[caption_color].lstrip("#")
    rgb = tuple(int(hex_color[index:index + 2], 16) for index in (0, 2, 4))
    if caption_style == "karaoke":
        settings["glow_fill"] = (*rgb, 115)
    return (*rgb, 255), settings


def _moviepy():
    try:
        from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, VideoClip, vfx
        from moviepy import concatenate_videoclips
    except ImportError:
        from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, VideoClip, concatenate_videoclips, vfx
    return AudioFileClip, CompositeVideoClip, ImageClip, VideoClip, concatenate_videoclips, vfx


def _call(clip, old_name, new_name, *args, **kwargs):
    method = getattr(clip, new_name, None) or getattr(clip, old_name)
    return method(*args, **kwargs)


def _gradient_background(size, theme):
    """Create a cinematic, low-detail backdrop with safe space for Arabic text."""
    import hashlib
    import random

    target_width, target_height = size
    # Keep the requested aspect ratio at every preview/export size so both use
    # the same scene composition when the preview is scaled to the final frame.
    width, height = max(180, target_width // 2), max(320, target_height // 2)
    palette = THEMES[theme]
    seed = int.from_bytes(hashlib.sha256(theme.encode()).digest()[:4], "big")
    rng = random.Random(seed)
    top = np.array(palette["top"], dtype=np.float32)
    bottom = np.array(palette["bottom"], dtype=np.float32)
    blend = np.linspace(0, 1, height, dtype=np.float32)[:, None, None]
    rows = top[None, None, :] * (1 - blend) + bottom[None, None, :] * blend
    pixels = np.repeat(rows, width, axis=1)

    # Broad off-center light gives depth while the central caption field stays calm.
    yy, xx = np.mgrid[0:height, 0:width]
    glow_x = width * (.22 + (seed % 55) / 100)
    glow_y = height * (.18 + (seed % 31) / 100)
    glow = np.exp(-(((xx-glow_x)/(width*.62))**2 + ((yy-glow_y)/(height*.34))**2) * 2.4)[..., None]
    pixels += glow * np.array(palette["accent"], dtype=np.float32)[None, None, :] * .19
    image = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))

    # Soft atmospheric haze, deliberately blurred to avoid hard graphic circles.
    lights = Image.new("RGBA", image.size, (0, 0, 0, 0))
    light_draw = ImageDraw.Draw(lights)
    accent = palette["accent"]
    for _ in range(7):
        x = int(width * (.05 + rng.random() * .9))
        y = int(height * (.05 + rng.random() * .43))
        rw = int(width * (.12 + rng.random() * .24))
        rh = int(height * (.025 + rng.random() * .055))
        light_draw.ellipse((x-rw, y-rh, x+rw, y+rh), fill=(*accent, rng.randint(9, 22)))
    lights = lights.filter(ImageFilter.GaussianBlur(max(8, width // 22)))
    image = Image.alpha_composite(image.convert("RGBA"), lights).convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")

    night = theme in {"masjid_night", "aurora_drift", "lavender_twilight", "crescent_garden", "sahara_moon", "plum_evening", "midnight_blue", "turquoise_mosaic"}
    if night:
        for _ in range(95):
            x, y = rng.randrange(width), rng.randrange(max(1, int(height*.49)))
            r = rng.choice((1, 1, 1, 2))
            draw.ellipse((x-r, y-r, x+r, y+r), fill=(*palette["accent"], rng.randint(45, 145)))
        cx, cy = int(width*.77), int(height*.22)
        r = max(1, int(width*.045))
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(*palette["accent"], 185))
        draw.ellipse((cx-r*.42, cy-r*1.12, cx+r*1.18, cy+r*.55), fill=(*palette["top"], 255))
    else:
        sun = Image.new("RGBA", image.size, (0,0,0,0))
        sun_draw = ImageDraw.Draw(sun)
        cx, cy, r = int(width*.76), int(height*.26), max(1, int(width*.07))
        sun_draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(*palette["accent"], 100))
        image = Image.alpha_composite(image.convert("RGBA"), sun.filter(ImageFilter.GaussianBlur(r*.75))).convert("RGB")

    # Layered smooth terrain anchors the frame without jagged polygon peaks.
    silhouette = Image.new("RGBA", image.size, (0,0,0,0))
    land = ImageDraw.Draw(silhouette)
    land_color = tuple(int(c*.42) for c in palette["bottom"])
    xs = range(0, width + 1)
    kind = "dunes" if theme in {"desert_dawn", "golden_dunes", "rose_sand", "copper_dusk", "sahara_moon"} else "waves" if theme in {"ocean_calm", "sapphire_horizon"} else "hills"
    def contour(base, amp, phase):
        return [(x, int(base + amp*(.62*np.sin(x/width*2*np.pi + phase) + .25*np.sin(x/width*4.5*np.pi + phase*1.7)))) for x in xs]
    distant = contour(height*.72, height*.075, (seed % 360)/57)
    land.polygon([(0,height), *distant, (width,height)], fill=(*land_color, 115 if night else 105))
    foreground = contour(height*.84, height*.045, (seed % 290)/43 + 1.2)
    land.polygon([(0,height), *foreground, (width,height)], fill=(*tuple(int(c*.27) for c in palette["top"]), 185))
    if kind == "dunes":
        highlight = (*palette["accent"], 42)
        land.line(contour(height*.77, height*.06, (seed % 150)/35 + 1.5), fill=highlight, width=max(1, width//250))
        land.line(contour(height*.89, height*.035, (seed % 180)/39 + 2.4), fill=(*palette["accent"], 30), width=max(1, width//300))
    elif kind == "waves":
        for offset, alpha in ((.67, 42), (.72, 30), (.77, 23)):
            land.line(contour(height*offset, height*.012, offset*8), fill=(*palette["accent"], alpha), width=max(1,width//320))

    # On selected themes, a tiny distant mosque provides context without filling the frame.
    if theme in {"masjid_night", "marble_arch", "jade_courtyard", "crescent_garden", "turquoise_mosaic"}:
        base = int(height*.89)
        center = int(width*(.17 + (seed % 17)/100))
        bw, bh = int(width*.18), int(height*.17)
        color = (*tuple(int(c*.24) for c in palette["top"]), 215)
        land.rectangle((center-bw//2, base-bh//2, center+bw//2, base), fill=color)
        land.ellipse((center-bw*.32, base-bh, center+bw*.32, base-bh*.22), fill=color)
        for mx in (center-bw*.55, center+bw*.55):
            land.rectangle((mx-2, base-bh*1.2, mx+2, base), fill=color)
            land.polygon([(mx-5, base-bh*1.2), (mx, base-bh*1.43), (mx+5, base-bh*1.2)], fill=color)
    image = Image.alpha_composite(image.convert("RGBA"), silhouette)

    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    yv, xv = np.mgrid[0:height, 0:width]
    nx, ny = (xv-width/2)/(width/2), (yv-height/2)/(height/2)
    vignette = np.clip(1 - .20*(nx*nx + ny*ny), .72, 1)[..., None]
    noise = np.random.default_rng(seed).normal(0, 1.3, (height, width, 1))
    finished = Image.fromarray(np.clip(arr*vignette + noise, 0, 255).astype(np.uint8))
    return finished.resize(size, Image.Resampling.LANCZOS)


def _background(path, size, theme="misty_forest"):
    if theme not in THEMES:
        raise ValueError(f"Unsupported background theme: {theme}")
    if path:
        image = Image.open(path).convert("RGB")
        scale = max(size[0] / image.width, size[1] / image.height)
        image = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
        left = (image.width - size[0]) // 2
        top = (image.height - size[1]) // 2
        return image.crop((left, top, left + size[0], top + size[1]))
    return _gradient_background(size, theme)


def _motion_frames(background, steps=12):
    """Pre-render a subtle Ken Burns sequence once instead of resizing every encoded frame."""
    width, height = background.size
    frames = []
    for step in range(steps):
        zoom = 1.0 + 0.035 * step / max(1, steps - 1)
        scaled_width, scaled_height = int(width * zoom), int(height * zoom)
        scaled = background.resize((scaled_width, scaled_height), Image.Resampling.BICUBIC)
        x, y = (scaled_width - width) // 2, (scaled_height - height) // 2
        frames.append(np.asarray(scaled.crop((x, y, x + width, y + height))))
    return frames


def render_reel(*, ayahs, output_path, aspect_ratio="9:16", audio_path=None,
                audio_start=None, audio_end=None, ayah_durations=None,
                background_path=None, theme="misty_forest", transition="crossfade",
                duration_per_ayah=3.0, fps=24, font_path=None, caption_style="classic", speed=1.0,
                caption_color="white", wrap_width=85):
    """Render every supplied ayah with synced text and optional reciter audio."""
    if aspect_ratio not in SIZES:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
    if transition not in TRANSITIONS:
        raise ValueError(f"Unsupported transition: {transition}")
    if theme not in THEMES:
        raise ValueError(f"Unsupported background theme: {theme}")
    if not ayahs or any(not str(ayah).strip() for ayah in ayahs):
        raise ValueError("At least one non-empty ayah is required")
    if caption_style not in {"karaoke", "minimal", "classic", "arabic_only"}:
        raise ValueError(f"Unsupported caption style: {caption_style}")
    if caption_color not in CAPTION_COLORS:
        raise ValueError(f"Unsupported caption color: {caption_color}")
    if int(wrap_width) not in {65, 75, 85, 95}:
        raise ValueError("Text wrap width must be 65, 75, 85, or 95 percent.")
    if float(speed) not in {0.9, 1.0, 1.15}:
        raise ValueError("Speed must be 0.9, 1.0, or 1.15.")

    from .text_renderer import render_arabic_text

    AudioFileClip, CompositeVideoClip, ImageClip, VideoClip, _concatenate, vfx = _moviepy()
    width, height = SIZES[aspect_ratio]
    audio_source = None
    audio_segment = None
    audio_clips = []
    output = None
    background_clip = None
    caption_clips = []
    try:
        if audio_path:
            audio_source = AudioFileClip(str(audio_path))
            audio_clips.append(audio_source)
            if audio_start is not None and audio_end is not None:
                audio_segment = _call(audio_source, "subclip", "subclipped", float(audio_start), float(audio_end))
                audio_clips.append(audio_segment)
            else:
                audio_segment = audio_source
            if float(speed) != 1.0:
                if hasattr(audio_segment, "with_speed_scaled"):
                    audio_segment = audio_segment.with_speed_scaled(float(speed))
                else:
                    audio_segment = audio_segment.fx(vfx.speedx, factor=float(speed))
                audio_clips.append(audio_segment)

        if ayah_durations is not None:
            durations = [float(duration) / float(speed) for duration in ayah_durations]
            if len(durations) != len(ayahs) or any(duration <= 0 for duration in durations):
                raise ValueError("Audio timing must provide one positive duration for each ayah.")
        elif audio_segment is not None:
            each_duration = audio_segment.duration / len(ayahs)
            durations = [each_duration] * len(ayahs)
        else:
            durations = [float(duration_per_ayah)] * len(ayahs)
        if any(duration <= 0 for duration in durations):
            raise ValueError("Ayah duration must be positive.")

        total_duration = sum(durations)
        text_color, caption_options = caption_render_options(caption_style, caption_color)

        wallpaper = _background(background_path, (width, height), theme)
        # A light darkening layer improves contrast over bright uploaded images,
        # and one full-frame background prevents edge gaps in encoded output.
        wallpaper = Image.blend(wallpaper, Image.new("RGB", wallpaper.size, (0, 0, 0)), 0.16)
        motion_frames = _motion_frames(wallpaper)

        def make_background_frame(time):
            position = min(1.0, max(0.0, time / max(total_duration, 0.01)))
            frame_index = min(len(motion_frames) - 1, int(position * len(motion_frames)))
            return motion_frames[frame_index]

        try:
            background_clip = VideoClip(frame_function=make_background_frame, duration=total_duration)
        except TypeError:
            background_clip = VideoClip(make_frame=make_background_frame, duration=total_duration)

        timeline = 0.0
        for index, (ayah, verse_duration) in enumerate(zip(ayahs, durations)):
            caption_image = render_arabic_text(
                str(ayah), font_path=font_path, font_size=max(50, int(width * 0.07)),
                max_width=int(width * int(wrap_width) / 100), max_height=int(height * 0.44),
                color=text_color, **caption_options,
            )
            caption_clip = ImageClip(np.asarray(caption_image))
            caption_clip = _call(caption_clip, "set_duration", "with_duration", verse_duration)
            caption_clip = _call(caption_clip, "set_start", "with_start", timeline)
            if transition == "crossfade" and index:
                fade_in = getattr(vfx, "CrossFadeIn", None) or vfx.FadeIn
                caption_clip = caption_clip.with_effects([fade_in(min(0.2, verse_duration * 0.15))])
            caption_y = max(int(height * 0.2), min(int(height * 0.57 - caption_image.height / 2), height - caption_image.height - int(height * 0.12)))
            caption_clip = _call(caption_clip, "set_position", "with_position", ("center", caption_y))
            caption_clips.append(caption_clip)
            timeline += verse_duration

        output = CompositeVideoClip([background_clip, *caption_clips], size=(width, height)).with_duration(total_duration)
        if audio_segment is not None:
            audio_for_video = _call(audio_segment, "subclip", "subclipped", 0, min(audio_segment.duration, total_duration))
            output = _call(output, "set_audio", "with_audio", audio_for_video)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        output.write_videofile(
            str(output_path), fps=fps, codec="libx264", audio_codec="aac" if audio_segment else None,
            # MoviePy otherwise places its intermediate AAC file in the process
            # working directory, which can be read-only in deployed setups.
            temp_audiofile=str(Path(output_path).resolve().with_name(f"{Path(output_path).stem}_temp-audio.m4a")),
            remove_temp=True, preset="ultrafast", threads=4, logger=None,
        )
        return {"path": str(output_path), "duration": float(output.duration), "width": width,
                "height": height, "has_audio": audio_segment is not None}
    finally:
        if output is not None:
            output.close()
        if background_clip is not None:
            background_clip.close()
        for clip in caption_clips:
            clip.close()
        for clip in audio_clips:
            clip.close()
