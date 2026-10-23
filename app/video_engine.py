"""MoviePy composition for timed Quran reel captions and backgrounds."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .background_motion import (IMAGE_ANIMATION_PRESETS, ambient_light_position,
                                image_animation_phase, image_motion_values)

SIZES = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}
RESOLUTION_PRESETS = {"480p": 480, "720p": 720, "1080p": 1080, "1440p": 1440, "4k": 2160}
QUALITY_PRESETS = {
    "fast": {"label": "Fast", "preset": "ultrafast", "crf": 29},
    "balanced": {"label": "Balanced", "preset": "veryfast", "crf": 23},
    "high": {"label": "High Quality", "preset": "medium", "crf": 19},
    "maximum": {"label": "Maximum Quality", "preset": "slow", "crf": 17},
}
TRANSITIONS = {"crossfade", "cut"}
BACKGROUND_TRANSITIONS = {"cut", "crossfade", "dissolve", "fade_black", "fade_color", "slide_left", "slide_right", "zoom"}
BACKGROUND_FIT_MODES = {"cover", "contain", "stretch", "blurred"}
BACKGROUND_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}
THEMES = {
    "sahara_moon": {"name": "Starlit Night Sky", "top": (10, 15, 30), "bottom": (25, 40, 65), "accent": (230, 210, 160)},
    "aurora_drift": {"name": "Cosmic Blue Nebula", "top": (11, 24, 47), "bottom": (35, 45, 90), "accent": (165, 230, 255)},
    "turquoise_mosaic": {"name": "Golden Islamic Mosaic", "top": (12, 40, 50), "bottom": (20, 65, 75), "accent": (235, 195, 100)},
    "copper_dusk": {"name": "Obsidian & Gold Minimal", "top": (15, 15, 18), "bottom": (35, 30, 25), "accent": (235, 195, 110)},
    "golden_dunes": {"name": "Moonlit Desert Dunes", "top": (20, 30, 50), "bottom": (45, 60, 85), "accent": (220, 235, 255)},
    "masjid_night": {"name": "Badshahi Mosque at Night", "top": (15, 20, 45), "bottom": (65, 50, 75), "accent": (255, 200, 120)},
    "cloud_morning": {"name": "Wadi Rum at Dawn", "top": (25, 45, 70), "bottom": (180, 120, 70), "accent": (255, 230, 170)},
    "olive_garden": {"name": "Palm Courtyard at Night", "top": (6, 30, 22), "bottom": (15, 55, 40), "accent": (225, 195, 100)},
    "rose_sand": {"name": "Flowing Golden Bokeh", "top": (25, 18, 22), "bottom": (55, 35, 40), "accent": (255, 215, 130)},
    "plum_evening": {"name": "Illuminated Mosque at Night", "top": (20, 15, 30), "bottom": (40, 25, 45), "accent": (240, 180, 120)},
    "midnight_blue": {"name": "Himalayan Starry Night", "top": (8, 12, 30), "bottom": (15, 25, 50), "accent": (214, 235, 255)},
    "desert_dawn": {"name": "White Sands at Golden Hour", "top": (50, 40, 70), "bottom": (180, 110, 85), "accent": (255, 220, 170)},
    "marble_arch": {"name": "Dark Gold-Veined Marble", "top": (20, 24, 30), "bottom": (15, 18, 24), "accent": (230, 190, 100)},
    "sapphire_horizon": {"name": "Calm Ocean Horizon at Dusk", "top": (10, 20, 45), "bottom": (30, 85, 160), "accent": (210, 235, 255)},
    "midnight_coast": {"name": "Midnight Coast", "top": (7, 17, 40), "bottom": (2, 9, 21), "accent": (170, 205, 235)},
    "pearl_dawn": {"name": "Ivory Arabesque Filigree", "top": (240, 235, 225), "bottom": (220, 210, 195), "accent": (180, 145, 80)},
    "ocean_calm": {"name": "Deep Ocean Light Shafts", "top": (15, 60, 100), "bottom": (8, 25, 50), "accent": (160, 235, 255)},
    "misty_forest": {"name": "Sunbeams Through Morning Mist", "top": (20, 32, 38), "bottom": (45, 68, 65), "accent": (200, 220, 210)},
    "lavender_twilight": {"name": "Ouarzazate at Blue Hour", "top": (30, 20, 50), "bottom": (75, 40, 95), "accent": (230, 190, 255)},
    "jade_courtyard": {"name": "Sheikh Zayed Mosque Interior", "top": (10, 25, 30), "bottom": (20, 55, 50), "accent": (235, 200, 120)},
    "crescent_garden": {"name": "Imperial Crescent & Stars", "top": (12, 16, 24), "bottom": (25, 30, 40), "accent": (240, 205, 110)},
    "lake_dawn": {"name": "Misty Lake at First Light", "top": (31, 56, 69), "bottom": (41, 65, 66), "accent": (218, 197, 147)},
    "haram_night": {"name": "Masjid al-Haram by Night", "top": (10, 14, 25), "bottom": (34, 35, 39), "accent": (231, 198, 128)},
    "misty_valley": {"name": "Sunrise Over a Misty Valley", "top": (94, 112, 115), "bottom": (36, 55, 49), "accent": (232, 211, 166)},
}
THEME_CATEGORIES = {
    "sahara_moon": "Night & Celestial", "aurora_drift": "Abstract & Light",
    "turquoise_mosaic": "Islamic Architecture", "copper_dusk": "Luxury & Minimal",
    "golden_dunes": "Nature & Landscapes", "masjid_night": "Islamic Architecture",
    "cloud_morning": "Nature & Landscapes", "olive_garden": "Islamic Architecture",
    "rose_sand": "Abstract & Light", "plum_evening": "Night & Celestial",
    "midnight_blue": "Night & Celestial", "desert_dawn": "Nature & Landscapes",
    "marble_arch": "Islamic Architecture", "sapphire_horizon": "Water & Atmosphere",
    "pearl_dawn": "Luxury & Minimal", "ocean_calm": "Water & Atmosphere",
    "misty_forest": "Nature & Landscapes", "lavender_twilight": "Abstract & Light",
    "midnight_coast": "Water & Atmosphere",
    "jade_courtyard": "Islamic Architecture", "crescent_garden": "Night & Celestial",
    "lake_dawn": "Water & Atmosphere", "haram_night": "Islamic Architecture",
    "misty_valley": "Nature & Landscapes",
}
CAPTION_COLORS = {
    "white": "#ffffff", "ivory": "#fff3d2", "gold": "#ffd166", "amber": "#ffb703",
    "sky": "#75d5ff", "blue": "#006aff", "cyan": "#63f3e8", "mint": "#91f2c3",
    "lime": "#c7f464", "rose": "#ff8fa3", "coral": "#ff8066", "lavender": "#d6b8ff",
    "silver": "#dbeafe", "emerald": "#34d399", "orange": "#ff9f43", "pink": "#ff6fb5",
    "ink": "#27241e",
}


def output_dimensions(aspect_ratio="9:16", resolution="1080p", custom_width=None, custom_height=None):
    """Resolve a social-video preset to even H.264 dimensions with strict bounds."""
    if aspect_ratio not in SIZES:
        raise ValueError("Aspect ratio must be 9:16, 16:9, or 1:1.")
    if str(resolution).lower() == "custom":
        try:
            width, height = int(custom_width), int(custom_height)
        except (TypeError, ValueError) as exc:
            raise ValueError("Custom resolution needs whole-number width and height values.") from exc
        if not (240 <= width <= 3840 and 240 <= height <= 3840):
            raise ValueError("Custom width and height must each be between 240 and 3840 pixels.")
        if width % 2 or height % 2:
            raise ValueError("Custom dimensions must be even numbers for H.264 compatibility.")
        expected = SIZES[aspect_ratio][0] / SIZES[aspect_ratio][1]
        if abs(width / height - expected) > 0.002:
            raise ValueError(f"Custom resolution must match the selected {aspect_ratio} aspect ratio.")
        return width, height
    short_edge = RESOLUTION_PRESETS.get(str(resolution).lower())
    if short_edge is None:
        raise ValueError("Resolution must be 480p, 720p, 1080p, 1440p, 4k, or custom.")
    if aspect_ratio == "9:16":
        width, height = short_edge, round(short_edge * 16 / 9)
    elif aspect_ratio == "16:9":
        width, height = round(short_edge * 16 / 9), short_edge
    else:
        width = height = short_edge
    return width - width % 2, height - height % 2

def _parse_color(color_val, default=(255, 255, 255)):
    if isinstance(color_val, (tuple, list)):
        return tuple(color_val[:3])
    if not color_val or not isinstance(color_val, str):
        return default
    c = color_val.strip()
    if c in CAPTION_COLORS:
        c = CAPTION_COLORS[c]
    hex_str = c.lstrip("#")
    if len(hex_str) == 6:
        try:
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    return default


def caption_render_options(caption_style, caption_color="white", **custom):
    """Return the shared text-renderer settings for preview and final video."""
    options = {
        "classic": {"stroke_width": 3, "stroke_fill": (0, 0, 0, 235),
                    "backdrop_fill": (5, 8, 13, 165), "padding_x": 32, "padding_y": 24, "corner_radius": 24},
        "quranic": {"stroke_width": 2, "stroke_fill": (15, 12, 5, 230),
                    "backdrop_fill": (10, 12, 18, 205), "padding_x": 36, "padding_y": 28, "corner_radius": 24,
                    "glow_radius": 8},
        "minimal": {"stroke_width": 1, "stroke_fill": (0, 0, 0, 190),
                    "backdrop_fill": None, "padding_x": 20, "padding_y": 14, "corner_radius": 0},
        "golden_illuminated": {"stroke_width": 2, "stroke_fill": (0, 0, 0, 230),
                               "backdrop_fill": (12, 10, 6, 175), "padding_x": 34, "padding_y": 24, "corner_radius": 24,
                               "glow_radius": 14},
        "soft_white": {"stroke_width": 1, "stroke_fill": (0, 0, 0, 200),
                       "backdrop_fill": (10, 15, 24, 150), "padding_x": 30, "padding_y": 22, "corner_radius": 22,
                       "glow_radius": 12},
        "bold_modern": {"stroke_width": 3, "stroke_fill": (0, 0, 0, 240),
                        "backdrop_fill": (15, 23, 42, 235), "padding_x": 34, "padding_y": 24, "corner_radius": 16},
        "subtle_shadow": {"stroke_width": 1, "stroke_fill": (0, 0, 0, 190),
                          "backdrop_fill": None, "padding_x": 20, "padding_y": 16, "corner_radius": 0, "glow_radius": 4},
        "frosted": {"stroke_width": 1, "stroke_fill": (0, 0, 0, 160),
                    "backdrop_fill": (255, 255, 255, 45), "padding_x": 36, "padding_y": 26, "corner_radius": 28},
        "clean_subtitle": {"stroke_width": 2, "stroke_fill": (0, 0, 0, 240),
                           "backdrop_fill": (0, 0, 0, 185), "padding_x": 24, "padding_y": 16, "corner_radius": 12},
        "subtle_outline": {"stroke_width": 3, "stroke_fill": (0, 0, 0, 255),
                           "backdrop_fill": None, "padding_x": 16, "padding_y": 12, "corner_radius": 0},
        "karaoke": {"stroke_width": 3, "stroke_fill": (0, 0, 0, 225),
                    "backdrop_fill": (0, 0, 0, 125), "glow_radius": 11, "corner_radius": 24},
        "arabic_only": {"stroke_width": 3, "stroke_fill": (0, 0, 0, 230),
                        "backdrop_fill": None, "corner_radius": 0},
    }

    style_key = str(caption_style).lower().replace(" ", "_").replace("-", "_")
    matched = None
    for k in options:
        if k in style_key or style_key in k:
            matched = k
            break
    if matched is None:
        matched = "classic"

    settings = dict(options[matched])
    rgb = _parse_color(caption_color)

    # Glow defaults by style
    if matched == "karaoke":
        settings["glow_fill"] = (*rgb, 115)
    elif matched == "golden_illuminated":
        settings["glow_fill"] = (255, 215, 0, 135)
    elif matched == "soft_white":
        settings["glow_fill"] = (255, 255, 255, 110)
    elif matched == "quranic":
        settings["glow_fill"] = (235, 195, 95, 90)
    elif matched == "subtle_shadow":
        settings["glow_fill"] = (0, 0, 0, 140)

    # Process custom overrides if provided
    if "text_bg_enabled" in custom:
        enabled = custom["text_bg_enabled"]
        if isinstance(enabled, str):
            enabled = enabled.lower() in ("true", "1", "yes", "on")
        if not enabled:
            settings["backdrop_fill"] = None
        else:
            bg_color = custom.get("text_bg_color", "#000000")
            bg_rgb = _parse_color(bg_color, (0, 0, 0))
            try:
                opacity = float(custom.get("text_bg_opacity", 0.65))
            except (ValueError, TypeError):
                opacity = 0.65
            settings["backdrop_fill"] = (*bg_rgb, int(255 * max(0.0, min(1.0, opacity))))

    if "corner_radius" in custom and custom["corner_radius"] is not None:
        try:
            settings["corner_radius"] = int(custom["corner_radius"])
        except (ValueError, TypeError):
            pass

    if "padding_x" in custom and custom["padding_x"] is not None:
        try:
            settings["padding_x"] = int(custom["padding_x"])
        except (ValueError, TypeError):
            pass

    if "padding_y" in custom and custom["padding_y"] is not None:
        try:
            settings["padding_y"] = int(custom["padding_y"])
        except (ValueError, TypeError):
            pass

    if "glow_type" in custom:
        g_type = str(custom["glow_type"]).lower()
        if g_type == "none":
            settings["glow_fill"] = None
            settings["glow_radius"] = 0
        else:
            preset_glows = {
                "white": (255, 255, 255),
                "gold": (255, 215, 0),
                "blue": (56, 189, 248),
                "emerald": (52, 211, 153),
            }
            g_rgb = preset_glows.get(g_type) or _parse_color(custom.get("glow_color", "#ffd166"), rgb)
            try:
                g_op = float(custom.get("glow_opacity", 0.6))
            except (ValueError, TypeError):
                g_op = 0.6
            try:
                g_rad = int(custom.get("glow_radius", 10))
            except (ValueError, TypeError):
                g_rad = 10
            settings["glow_fill"] = (*g_rgb, int(255 * max(0.0, min(1.0, g_op))))
            settings["glow_radius"] = max(0, min(40, g_rad))

    return (*rgb, 255), settings


def render_caption_image(text, *, aspect_ratio, font_path=None, caption_style="classic",
                         caption_color="white", wrap_width=85, caption_scale=1.0, show_surah_title=False,
                         surah_title=None, ayah_number=None, surah_color=None,
                         show_ayah_number=None, surah_template="ornamental_gold",
                         ayah_number_template="gold_medallion", ayah_color=None,
                         surah_scale=None, ayah_number_scale=None,
                         surah_align=None, ayah_number_align=None,
                         surah_position_x=0, surah_position_y=0,
                         ayah_number_position_x=0, ayah_number_position_y=0,
                         surah_font_path=None, ayah_number_font_path=None,
                         surah_opacity=None, ayah_number_opacity=None,
                         surah_placement=None, ayah_number_placement=None,
                         translation_text="", translation_options=None,
                         max_height_ratio=.44,
                         output_size=None,
                         **custom_options):
    """Render one caption identically for the live preview and exported video."""
    from .text_renderer import render_arabic_text
    if not str(text or "").strip():
        # An empty scene is an intentional blank display interval. Keep its
        # timeline and audio intact without asking Arabic shaping to rasterize
        # a string that contains no glyphs.
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    if aspect_ratio not in SIZES:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
    width, height = output_size or SIZES[aspect_ratio]
    if isinstance(caption_scale, bool):
        raise ValueError("Arabic caption size scale must be between 0.80 and 1.10.")
    try:
        caption_scale = float(caption_scale)
    except (TypeError, ValueError) as exc:
        raise ValueError("Arabic caption size scale must be between 0.80 and 1.10.") from exc
    if not np.isfinite(caption_scale) or not .80 <= caption_scale <= 1.10:
        raise ValueError("Arabic caption size scale must be between 0.80 and 1.10.")
    translation_options = translation_options or {}
    text_color, options = caption_render_options(caption_style, caption_color, **custom_options)
    surah_rgba = _parse_color(surah_color, (235, 205, 110)) + (255,)
    from .design_templates import AYAH_NUMBER_TEMPLATES, SURAH_NAME_TEMPLATES
    surah_config = dict(SURAH_NAME_TEMPLATES.get(surah_template, SURAH_NAME_TEMPLATES["ornamental_gold"]))
    number_config = dict(AYAH_NUMBER_TEMPLATES.get(ayah_number_template, AYAH_NUMBER_TEMPLATES["gold_medallion"]))
    if surah_color:
        surah_config["color"] = surah_color
    if ayah_color:
        number_config["color"] = ayah_color
    if surah_scale is not None:
        surah_config["font_scale"] = max(.25, min(.7, float(surah_scale)))
    if ayah_number_scale is not None:
        number_config["font_scale"] = max(.2, min(.6, float(ayah_number_scale)))
    if surah_align in {"left", "center", "right"}:
        surah_config["align"] = surah_align
    if ayah_number_align in {"left", "center", "right"}:
        number_config["align"] = ayah_number_align
    if surah_font_path is not None:
        surah_config["font_path"] = surah_font_path
    if ayah_number_font_path is not None:
        number_config["font_path"] = ayah_number_font_path
    if surah_opacity is not None:
        surah_config["opacity"] = max(0.0, min(1.0, float(surah_opacity)))
    if ayah_number_opacity is not None:
        number_config["opacity"] = max(0.0, min(1.0, float(ayah_number_opacity)))
    if surah_placement in {"above", "below"}:
        surah_config["placement"] = surah_placement
    if ayah_number_placement in {"above", "below"}:
        number_config["placement"] = ayah_number_placement
    return render_arabic_text(
        text, font_path=font_path, font_size=max(26, int(width * .07 * caption_scale)),
        max_width=int(width * int(wrap_width) / 100),
        max_height=int(height * max(.2, min(.5, float(max_height_ratio)))),
        color=text_color, show_surah_title=show_surah_title,
        surah_title=surah_title, ayah_number=ayah_number,
        surah_color=surah_rgba, show_ayah_number=show_ayah_number,
        surah_template=surah_config, ayah_number_template=number_config, **options,
        surah_font_path=surah_config.get("font_path"),
        ayah_number_font_path=number_config.get("font_path"),
        surah_position_x=surah_position_x, surah_position_y=surah_position_y,
        ayah_number_position_x=ayah_number_position_x, ayah_number_position_y=ayah_number_position_y,
        translation_text=translation_text,
        translation_font=translation_options.get("translation_font", "sans"),
        translation_font_size=max(6, int(width * float(translation_options.get("translation_size", .022)))),
        translation_color=translation_options.get("translation_color", "#ffffff"),
        translation_opacity=translation_options.get("translation_opacity", .96),
        translation_line_spacing=translation_options.get("translation_line_spacing", 1.35),
        translation_gap=int(width * float(translation_options.get("translation_gap", .012))),
        translation_align=translation_options.get("translation_align", "center"),
        translation_max_width=int(width * float(translation_options.get("translation_wrap_width", .84))),
        translation_bg_enabled=translation_options.get("translation_bg_enabled", False),
        translation_bg_color=translation_options.get("translation_bg_color", "#10161d"),
        translation_bg_opacity=translation_options.get("translation_bg_opacity", .4),
        output_size=(width, height),
    )


def _moviepy():
    try:
        from moviepy import AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip, VideoClip, VideoFileClip, afx, vfx
        from moviepy import concatenate_videoclips
    except ImportError:
        from moviepy.editor import AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip, VideoClip, VideoFileClip, concatenate_videoclips, afx, vfx
    return AudioFileClip, CompositeVideoClip, ImageClip, VideoClip, VideoFileClip, concatenate_videoclips, vfx, CompositeAudioClip, afx


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

    night = theme in {"masjid_night", "aurora_drift", "lavender_twilight", "crescent_garden", "sahara_moon", "plum_evening", "midnight_blue", "midnight_coast", "turquoise_mosaic"}
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
    kind = "dunes" if theme in {"desert_dawn", "golden_dunes", "rose_sand", "copper_dusk", "sahara_moon"} else "waves" if theme in {"ocean_calm", "sapphire_horizon", "midnight_coast"} else "hills"
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


def _fit_image(image, size, fit_mode="cover", crop_x=.5, crop_y=.5):
    """Fit an image without distortion, with an optional blurred fill or focal crop."""
    if fit_mode not in BACKGROUND_FIT_MODES:
        raise ValueError("Background fit must be cover, contain, stretch, or blurred.")
    width, height = size
    if fit_mode == "stretch":
        return image.resize(size, Image.Resampling.LANCZOS)

    cover_scale = max(width / image.width, height / image.height)
    contain_scale = min(width / image.width, height / image.height)
    if fit_mode == "cover":
        scaled = image.resize((int(image.width * cover_scale), int(image.height * cover_scale)), Image.Resampling.LANCZOS)
        left = int((scaled.width - width) * max(0.0, min(1.0, float(crop_x))))
        top = int((scaled.height - height) * max(0.0, min(1.0, float(crop_y))))
        return scaled.crop((left, top, left + width, top + height))

    scale = contain_scale if fit_mode == "contain" else cover_scale
    scaled = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
    if fit_mode == "contain":
        canvas = Image.new("RGB", size, (7, 12, 20))
        canvas.paste(scaled, ((width - scaled.width) // 2, (height - scaled.height) // 2))
        return canvas

    left, top = (scaled.width - width) // 2, (scaled.height - height) // 2
    background = scaled.crop((left, top, left + width, top + height))
    background = background.filter(ImageFilter.GaussianBlur(max(12, min(size) * .035)))
    background = Image.blend(background, Image.new("RGB", size, (0, 0, 0)), .22)
    foreground = image.resize((int(image.width * contain_scale), int(image.height * contain_scale)), Image.Resampling.LANCZOS)
    background.paste(foreground, ((width - foreground.width) // 2, (height - foreground.height) // 2))
    return background


def _fit_video_clip(clip, size, fit_mode, crop_x, crop_y, vfx):
    width, height = size
    if fit_mode == "stretch":
        resized = clip.resized(new_size=size) if hasattr(clip, "resized") else clip.resize(size)
        return resized, None
    cover_scale = max(width / clip.w, height / clip.h)
    contain_scale = min(width / clip.w, height / clip.h)
    if fit_mode == "cover":
        resized = clip.resized(new_size=(int(clip.w * cover_scale), int(clip.h * cover_scale))) if hasattr(clip, "resized") else clip.resize(cover_scale)
        x1 = int((resized.w - width) * max(0.0, min(1.0, float(crop_x))))
        y1 = int((resized.h - height) * max(0.0, min(1.0, float(crop_y))))
        if hasattr(resized, "with_effects"):
            fitted = resized.with_effects([vfx.Crop(x1=x1, y1=y1, x2=x1 + width, y2=y1 + height)])
        else:
            fitted = resized.fx(vfx.crop, x1=x1, y1=y1, x2=x1 + width, y2=y1 + height)
        return fitted, None
    resized = clip.resized(height=int(clip.h * contain_scale)) if hasattr(clip, "resized") else clip.resize(contain_scale)
    return resized, "contain"


def _adjust_background_frame(frame, *, background_brightness=1, background_contrast=1,
                            background_saturation=1, background_overlay_color="#000000",
                            background_overlay_opacity=0):
    """Apply the same lightweight color grade to still and video background frames."""
    pixels = np.asarray(frame)
    if pixels.ndim != 3 or pixels.shape[2] < 3:
        raise ValueError("Background frames must contain RGB image data.")
    pixels = pixels[:, :, :3].astype(np.float32)
    if np.issubdtype(np.asarray(frame).dtype, np.floating) and pixels.max(initial=0) <= 1:
        pixels *= 255
    brightness = float(background_brightness)
    contrast = float(background_contrast)
    saturation = float(background_saturation)
    overlay_opacity = float(background_overlay_opacity)
    red, green, blue = _parse_color(background_overlay_color, (0, 0, 0))
    pixels = (pixels - 127.5) * contrast + 127.5
    pixels *= brightness
    luminance = (pixels[:, :, 0:1] * .2126 + pixels[:, :, 1:2] * .7152 + pixels[:, :, 2:3] * .0722)
    pixels = luminance + (pixels - luminance) * saturation
    if overlay_opacity:
        overlay = np.asarray((red, green, blue), dtype=np.float32)
        pixels = pixels * (1 - overlay_opacity) + overlay * overlay_opacity
    return np.clip(pixels, 0, 255).astype(np.uint8)


def _adjust_background_video(clip, adjustments):
    if not adjustments or all(
        adjustments.get(key, default) == default for key, default in (
            ("background_brightness", 1), ("background_contrast", 1),
            ("background_saturation", 1), ("background_overlay_opacity", 0),
        )
    ):
        return clip
    return clip.image_transform(lambda frame: _adjust_background_frame(frame, **adjustments))


def _ambient_light_sprite(size, intensity):
    """Build one soft transparent golden light bloom for optional scene atmosphere."""
    width, height = size
    sprite_width = max(120, min(width, int(width * .9)))
    sprite_height = max(120, min(height, int(height * .56)))
    x = np.linspace(-1.0, 1.0, sprite_width, dtype=np.float32)[None, :]
    y = np.linspace(-1.0, 1.0, sprite_height, dtype=np.float32)[:, None]
    falloff = np.exp(-2.7 * ((x / .92) ** 2 + (y / .82) ** 2))
    alpha = np.clip(falloff * 44 * float(intensity), 0, 44).astype(np.uint8)
    rgba = np.empty((sprite_height, sprite_width, 4), dtype=np.uint8)
    rgba[:, :, :3] = (255, 224, 167)
    rgba[:, :, 3] = alpha
    return Image.fromarray(rgba)


def _ambient_light_layer(*, size, duration, intensity, cycle_duration, speed,
                         start_time, ImageClip):
    """Return an optional, low-contrast moving light overlay for MoviePy."""
    sprite = _ambient_light_sprite(size, intensity)
    sprite_clip = ImageClip(np.asarray(sprite), transparent=True).with_duration(duration)
    width, height = size
    free_x = max(0, width - sprite.width)
    free_y = max(0, height - sprite.height)

    def position(time):
        phase = image_animation_phase(time, cycle_duration, speed, start_time)
        x_fraction, y_fraction = ambient_light_position(phase)
        return int(free_x * x_fraction), int(free_y * y_fraction)

    return sprite_clip.with_position(position)


def _build_video_sequence(clip_specs, *, size, theme, total_duration, fit_mode,
                         crop_x, crop_y, default_speed, loop, fps,
                         VideoFileClip, ImageClip, CompositeVideoClip, vfx, sources,
                         include_audio=False, audio_volume=.08, afx=None, adjustments=None,
                         transitions_enabled=False, transition_color="#000000",
                         VideoClip=None, animation_enabled=False, animation_preset="static",
                         animation_intensity=.6, animation_duration=12, animation_speed=1,
                         animation_start_time=0):
    """Build a continuous background track from ordered images and trimmed videos."""
    width, height = size
    base_frame = _background(None, size, theme)
    base_frame = _adjust_background_frame(base_frame, **(adjustments or {}))
    base = ImageClip(np.asarray(base_frame)).with_duration(total_duration)
    sources.append(base)
    fitted_specs = []
    for spec in clip_specs:
        path = Path(spec["path"])
        if path.suffix.lower() in BACKGROUND_VIDEO_EXTENSIONS:
            source = VideoFileClip(str(path), audio=include_audio)
            sources.append(source)
            source_duration = float(source.duration or 0)
            trim_start = float(spec.get("start", 0))
            trim_end_raw = spec.get("end")
            trim_end = source_duration if trim_end_raw in (None, "") else float(trim_end_raw)
            if trim_start < 0 or trim_end <= trim_start or trim_end > source_duration + .05:
                raise ValueError("Each background clip needs a valid trim range within its media duration.")
            clip = _call(source, "subclip", "subclipped", trim_start, min(source_duration, trim_end))
            sources.append(clip)
            speed = float(spec.get("speed", default_speed))
            if not .5 <= speed <= 2:
                raise ValueError("Background clip speed must be between 0.5x and 2x.")
            if speed != 1:
                clip = clip.with_speed_scaled(speed) if hasattr(clip, "with_speed_scaled") else clip.fx(vfx.speedx, factor=speed)
                sources.append(clip)
            fitted, _alignment = _fit_video_clip(clip, size, fit_mode, crop_x, crop_y, vfx)
            if fitted is not clip:
                sources.append(fitted)
            adjusted = _adjust_background_video(fitted, adjustments or {})
            if adjusted is not fitted:
                sources.append(adjusted)
                fitted = adjusted
            clip_audio = fitted.audio
            if animation_enabled and animation_preset != "static":
                moved = _animated_video_clip(
                    fitted, size=size, preset_id=animation_preset, intensity=animation_intensity,
                    cycle_duration=animation_duration, speed=animation_speed,
                    start_time=animation_start_time, VideoClip=VideoClip,
                )
                sources.append(moved)
                fitted = moved
        else:
            with Image.open(path) as opened:
                still = opened.convert("RGB")
            fitted_image = _fit_image(still, size, fit_mode, crop_x, crop_y)
            fitted_image = Image.fromarray(_adjust_background_frame(np.asarray(fitted_image), **(adjustments or {})))
            image_duration = float(spec.get("duration", 4.0))
            if animation_enabled and animation_preset != "static":
                def image_frame_at(time, source=fitted_image, cycle_duration=animation_duration,
                                   movement_speed=animation_speed, start_time=animation_start_time,
                                   active_preset=animation_preset, amount=animation_intensity):
                    progress = image_animation_phase(time, cycle_duration, movement_speed, start_time)
                    return _motion_frame(source, active_preset, progress, amount)
                fitted = VideoClip(frame_function=image_frame_at, duration=image_duration)
            else:
                fitted = ImageClip(np.asarray(fitted_image)).with_duration(image_duration)
            sources.append(fitted)
            clip_audio = None
            if image_duration <= 0:
                raise ValueError("Image sequence duration must be greater than zero.")
        if float(fitted.duration or 0) <= 0:
            raise ValueError("A background clip has no usable frames after trimming.")
        transition = spec.get("transition", "cut")
        if not transitions_enabled:
            transition = "cut"
        if transition == "dissolve":
            transition = "crossfade"
        if transition not in BACKGROUND_TRANSITIONS:
            raise ValueError("Choose a supported background transition.")
        transition_duration = float(spec.get("transition_duration", .45))
        if not 0 <= transition_duration <= 2:
            raise ValueError("Background transition duration must be between 0 and 2 seconds.")
        fitted_specs.append((fitted, transition, transition_duration, clip_audio))

    layers = [base]
    audio_layers = []
    cursor = 0.0
    last_clip = None
    last_audio_index = None
    cycles = 0
    while cursor < total_duration and cycles < 10000:
        cycles += 1
        for clip, transition, requested_transition, clip_audio_source in fitted_specs:
            clip_duration = float(clip.duration)
            if clip_duration <= 0:
                continue
            overlap = 0.0
            if cursor > 0 and transition in {"crossfade", "slide_left", "slide_right", "zoom"}:
                previous_duration = float(last_clip.duration) if last_clip is not None else clip_duration
                overlap = min(requested_transition, clip_duration * .4, previous_duration * .4)
                if overlap and transition == "crossfade" and last_audio_index is not None and afx is not None:
                    previous_audio = audio_layers[last_audio_index]
                    audio_layers[last_audio_index] = previous_audio.with_effects([afx.AudioFadeOut(overlap)])
            start_at = max(0.0, cursor - overlap)
            placed = clip
            position = "center"
            if overlap > 0 and transition == "crossfade":
                effect = getattr(vfx, "CrossFadeIn", None) or vfx.FadeIn
                placed = placed.with_effects([effect(overlap)])
                sources.append(placed)
            elif transition in {"fade_black", "fade_color"} and requested_transition:
                color = (0, 0, 0) if transition == "fade_black" else _parse_color(transition_color, (0, 0, 0))
                edge = min(requested_transition, float(clip.duration) * .35)
                effects = []
                if cursor > 0:
                    effects.append(vfx.FadeIn(edge, initial_color=color))
                if loop or cursor + float(clip.duration) < total_duration:
                    effects.append(vfx.FadeOut(edge, final_color=color))
                if effects and hasattr(placed, "with_effects"):
                    placed = placed.with_effects(effects)
                    sources.append(placed)
            elif overlap > 0 and transition in {"slide_left", "slide_right"}:
                direction = -1 if transition == "slide_left" else 1
                position = lambda t, duration=overlap, direction=direction: (
                    int(direction * width * (1 - min(1.0, max(0.0, t / duration)))), 0)
                placed = placed.with_position(position)
                sources.append(placed)
            elif overlap > 0 and transition == "zoom":
                if hasattr(placed, "resized"):
                    placed = placed.resized(lambda t, duration=overlap:
                        1.10 - .10 * min(1.0, max(0.0, t / duration)))
                    placed = placed.with_position("center")
                    sources.append(placed)
            placed = _call(placed, "set_start", "with_start", start_at)
            layers.append(placed.with_position(position))
            clip_audio = clip_audio_source
            if include_audio and clip_audio is not None:
                if audio_volume != 1:
                    clip_audio = clip_audio.with_volume_scaled(float(audio_volume))
                if overlap and afx is not None:
                    clip_audio = clip_audio.with_effects([afx.AudioFadeIn(overlap)])
                clip_audio = _call(clip_audio, "set_start", "with_start", start_at)
                audio_layers.append(clip_audio)
                sources.append(clip_audio)
                last_audio_index = len(audio_layers) - 1
            else:
                last_audio_index = None
            cursor = start_at + clip_duration
            last_clip = clip
            if cursor >= total_duration:
                break
        if not loop:
            break

    if cursor < total_duration and last_clip is not None:
        freeze_duration = total_duration - cursor
        frame_time = max(0.0, float(last_clip.duration) - 1 / max(1, fps))
        still = ImageClip(last_clip.get_frame(frame_time)).with_duration(freeze_duration)
        still = _call(still, "set_start", "with_start", cursor)
        layers.append(still.with_position("center"))
        sources.append(still)

    # The theme frame is a full-size opaque base. Reuse it directly instead of
    # making MoviePy build a full-resolution transparency mask for every frame.
    composed = CompositeVideoClip(layers, size=(width, height), use_bgclip=True).with_duration(total_duration)
    sources.append(composed)
    shade = ImageClip(np.asarray(Image.new("RGBA", (width, height), (0, 0, 0, 41)))).with_duration(total_duration)
    sources.append(shade)
    result = CompositeVideoClip([composed, shade], size=(width, height), use_bgclip=True).with_duration(total_duration)
    sources.append(result)
    return result, audio_layers


def _background(path, size, theme="misty_forest", fit_mode="cover", crop_x=.5, crop_y=.5):
    if theme not in THEMES:
        raise ValueError(f"Unsupported background theme: {theme}")
    if fit_mode not in BACKGROUND_FIT_MODES:
        raise ValueError("Background fit must be cover, contain, stretch, or blurred.")
    if path:
        image = Image.open(path).convert("RGB")
        if fit_mode == "contain":
            canvas = _background(None, size, theme, "cover", crop_x, crop_y)
            scale = min(size[0] / image.width, size[1] / image.height)
            foreground = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
            canvas.paste(foreground, ((size[0] - foreground.width) // 2, (size[1] - foreground.height) // 2))
            return canvas
        return _fit_image(image, size, fit_mode, crop_x, crop_y)

    # Prefer the art-directed, text-safe grade; retain the original asset as a
    # fallback so older installations continue to render every preset.
    asset_dir = Path(__file__).resolve().parents[1] / "static" / "assets" / "backgrounds"
    for asset_path in (asset_dir / f"{theme}_cinematic.jpg", asset_dir / f"{theme}.jpg"):
        if asset_path.exists():
            image = Image.open(asset_path).convert("RGB")
            return _fit_image(image, size, fit_mode, crop_x, crop_y)

    return _gradient_background(size, theme)


def _motion_frames(background, preset_id="static", intensity=1.0, steps=48):
    """Pre-render a smooth, edge-safe optional camera move for a still image."""
    width, height = background.size
    if preset_id not in IMAGE_ANIMATION_PRESETS:
        raise ValueError("Choose a supported still-image animation preset.")
    if preset_id == "static" or float(intensity) <= 0:
        return [np.asarray(background)]
    frames = []
    for step in range(steps):
        # Store the camera path once, linearly. Frame selection applies the
        # eased ping-pong phase so each cycle starts and ends at the same crop.
        phase = step / max(1, steps - 1)
        zoom, crop_x, crop_y = image_motion_values(preset_id, phase, intensity)
        scaled_width, scaled_height = int(width * zoom), int(height * zoom)
        scaled = background.resize((scaled_width, scaled_height), Image.Resampling.BICUBIC)
        x = int((scaled_width - width) * crop_x)
        y = int((scaled_height - height) * crop_y)
        frames.append(np.asarray(scaled.crop((x, y, x + width, y + height))))
    return frames


def _motion_frame(background, preset_id, phase, intensity):
    """Render one edge-safe camera frame, avoiding full-video frame caching."""
    width, height = background.size
    zoom, crop_x, crop_y = image_motion_values(preset_id, phase, intensity)
    scaled_width = max(width, int(width * zoom))
    scaled_height = max(height, int(height * zoom))
    scaled = background.resize((scaled_width, scaled_height), Image.Resampling.BICUBIC)
    x = min(scaled_width - width, max(0, int((scaled_width - width) * crop_x)))
    y = min(scaled_height - height, max(0, int((scaled_height - height) * crop_y)))
    return np.asarray(scaled.crop((x, y, x + width, y + height)))


def _animated_video_clip(source, *, size, preset_id, intensity, cycle_duration,
                         speed, start_time, VideoClip):
    """Apply a subtle crop move per decoded video frame without reversing playback."""
    def frame_at(time):
        phase = image_animation_phase(time, cycle_duration, speed, start_time)
        frame = Image.fromarray(np.asarray(source.get_frame(time)).astype(np.uint8)).convert("RGB")
        if frame.size != size:
            frame = frame.resize(size, Image.Resampling.BICUBIC)
        return _motion_frame(frame, preset_id, phase, intensity)

    return VideoClip(frame_function=frame_at, duration=float(source.duration or 0))


def render_reel(*, ayahs, output_path, aspect_ratio="9:16", audio_path=None,
                audio_start=None, audio_end=None, ayah_durations=None,
                word_timings=None,
                background_path=None, theme="misty_forest", transition="crossfade",
                background_clips=None,
                duration_per_ayah=3.0, fps=30, font_path=None, caption_style="classic", speed=1.0,
                caption_color="white", wrap_width=85, ayah_start=1,
                caption_scale=1.0,
                show_surah_title=False, surah_title=None, surah_color=None,
                show_ayah_number=None, surah_template="ornamental_gold",
                ayah_number_template="gold_medallion", ayah_color=None,
                surah_scale=None, ayah_number_scale=None,
                surah_align=None, ayah_number_align=None,
                caption_x=50, caption_y=None,
                caption_position="center", max_lines=5, words_per_scene=8, scene_overrides=None,
                show_quran_text=True, viewer_surah_name="", viewer_surah_number=1, reciter_name="",
                translation_lines=None, viewer_options=None,
                background_fit="cover", crop_x=.5, crop_y=.5,
                background_speed=1.0, background_loop=True,
                background_audio_enabled=False, background_audio_volume=.08,
                background_brightness=1, background_contrast=1, background_saturation=1,
                background_overlay_color="#000000", background_overlay_opacity=0,
                background_animation_enabled=False, background_animation_preset="static",
                background_animation_intensity=.6, background_animation_duration=12,
                background_animation_speed=1.0, background_animation_start=0.0,
                background_atmosphere_enabled=False, background_atmosphere_intensity=.35,
                background_atmosphere_duration=36, background_atmosphere_speed=.7,
                background_atmosphere_start=0.0,
                transitions_enabled=False,
                background_transition_color="#000000",
                output_size=None, quality="fast", crf=None, audio_bitrate="192k", audio_fps=48000,
                progress_callback=None, cancel_event=None, encoder="auto",
                **custom_options):
    """Render every ayah with synced text and configurable Reel Viewer layers."""
    if aspect_ratio not in SIZES:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
    if quality not in QUALITY_PRESETS:
        raise ValueError("Quality must be fast, balanced, high, or maximum.")
    if encoder not in {"auto", "cpu", "nvidia", "intel"}:
        raise ValueError("Encoder must be auto, cpu, nvidia, or intel.")
    if isinstance(caption_scale, bool):
        raise ValueError("Arabic caption size scale must be between 0.80 and 1.10.")
    try:
        caption_scale = float(caption_scale)
    except (TypeError, ValueError) as exc:
        raise ValueError("Arabic caption size scale must be between 0.80 and 1.10.") from exc
    if not np.isfinite(caption_scale) or not .80 <= caption_scale <= 1.10:
        raise ValueError("Arabic caption size scale must be between 0.80 and 1.10.")
    requested_encoder = encoder
    selected_encoder = encoder
    hardware_encoder = None
    hardware_capabilities = None
    fallback_reason = None
    if encoder == "auto":
        from .ffmpeg_encoder import hardware_encoder_status
        hardware_capabilities = hardware_encoder_status()
        hardware_encoder = hardware_capabilities["nvidia"]
        if not hardware_encoder["available"]:
            fallback_reason = f"NVIDIA NVENC unavailable: {hardware_encoder['reason']}"
            selected_encoder = "cpu"
            hardware_encoder = None
        else:
            selected_encoder = "nvidia"
    elif encoder != "cpu":
        from .ffmpeg_encoder import hardware_encoder_status
        hardware_capabilities = hardware_encoder_status()
        hardware_encoder = hardware_capabilities[encoder]
        if not hardware_encoder["available"]:
            raise ValueError(f"{hardware_encoder['name']} is unavailable: {hardware_encoder['reason']}")
    profile = QUALITY_PRESETS[quality]
    try:
        crf = profile["crf"] if crf in (None, "") else int(crf)
        audio_fps = int(audio_fps)
    except (TypeError, ValueError) as exc:
        raise ValueError("CRF and audio sample rate must be valid numbers.") from exc
    if not 16 <= crf <= 34 or audio_bitrate not in {"128k", "192k", "256k", "320k"}:
        raise ValueError("CRF must be 16–34 and audio bitrate must be 128, 192, 256, or 320 kbps.")
    if audio_fps not in {44100, 48000}:
        raise ValueError("Audio sample rate must be 44100 or 48000 Hz.")
    if int(fps) not in {24, 25, 30, 60}:
        raise ValueError("Frame rate must be 24, 25, 30, or 60 FPS.")
    width, height = output_size or SIZES[aspect_ratio]
    if width % 2 or height % 2 or min(width, height) < 240 or max(width, height) > 3840:
        raise ValueError("Output dimensions must be even and between 240 and 3840 pixels.")
    from .job_errors import JobCancelled

    def check_cancelled():
        if cancel_event is not None and cancel_event.is_set():
            raise JobCancelled()

    check_cancelled()
    if transition not in TRANSITIONS:
        raise ValueError(f"Unsupported transition: {transition}")
    if theme not in THEMES:
        raise ValueError(f"Unsupported background theme: {theme}")
    if not ayahs or any(not str(ayah).strip() for ayah in ayahs):
        raise ValueError("At least one non-empty ayah is required")
    if int(wrap_width) not in {65, 75, 85, 95}:
        raise ValueError("Text wrap width must be 65, 75, 85, or 95 percent.")
    if float(speed) not in {0.9, 1.0, 1.15}:
        raise ValueError("Speed must be 0.9, 1.0, or 1.15.")
    if caption_position not in {"upper", "center", "lower"}:
        raise ValueError("Caption position must be upper, center, or lower.")
    try:
        caption_x = float(caption_x)
        caption_y = None if caption_y is None else float(caption_y)
    except (TypeError, ValueError) as exc:
        raise ValueError("Caption X and Y positions must be numbers from 0 to 100.") from exc
    if not 0 <= caption_x <= 100 or (caption_y is not None and not 0 <= caption_y <= 100):
        raise ValueError("Caption X and Y positions must be between 0 and 100 percent.")
    if background_fit not in BACKGROUND_FIT_MODES:
        raise ValueError("Background fit must be cover, contain, stretch, or blurred.")
    try:
        crop_x, crop_y, background_speed = float(crop_x), float(crop_y), float(background_speed)
    except (TypeError, ValueError) as exc:
        raise ValueError("Background crop and speed must be valid numbers.") from exc
    if not 0 <= crop_x <= 1 or not 0 <= crop_y <= 1 or not .5 <= background_speed <= 2:
        raise ValueError("Crop positions must be 0–1 and background speed must be 0.5–2.0.")
    if isinstance(background_loop, str):
        background_loop = background_loop.lower() in ("true", "1", "yes", "on")
    if isinstance(background_audio_enabled, str):
        background_audio_enabled = background_audio_enabled.lower() in ("true", "1", "yes", "on")
    if isinstance(background_animation_enabled, str):
        background_animation_enabled = background_animation_enabled.lower() in ("true", "1", "yes", "on")
    if isinstance(background_atmosphere_enabled, str):
        background_atmosphere_enabled = background_atmosphere_enabled.lower() in ("true", "1", "yes", "on")
    if isinstance(transitions_enabled, str):
        transitions_enabled = transitions_enabled.lower() in ("true", "1", "yes", "on")
    try:
        background_animation_intensity = float(background_animation_intensity)
        background_animation_duration = float(background_animation_duration)
        background_animation_speed = float(background_animation_speed)
        background_animation_start = float(background_animation_start)
    except (TypeError, ValueError) as exc:
        raise ValueError("Background animation intensity, duration, and speed must be valid numbers.") from exc
    if background_animation_preset not in IMAGE_ANIMATION_PRESETS:
        raise ValueError("Choose a supported still-image animation preset.")
    if (not 0 <= background_animation_intensity <= 1 or not 1 <= background_animation_duration <= 120
            or not .25 <= background_animation_speed <= 3 or not 0 <= background_animation_start <= 600):
        raise ValueError("Animation intensity must be 0–1, duration 1–120 seconds, speed 0.25–3x, and start time 0–600 seconds.")
    try:
        background_atmosphere_intensity = float(background_atmosphere_intensity)
        background_atmosphere_duration = float(background_atmosphere_duration)
        background_atmosphere_speed = float(background_atmosphere_speed)
        background_atmosphere_start = float(background_atmosphere_start)
    except (TypeError, ValueError) as exc:
        raise ValueError("Atmospheric light intensity, duration, speed, and start time must be valid numbers.") from exc
    if (not 0 <= background_atmosphere_intensity <= 1
            or not 8 <= background_atmosphere_duration <= 120
            or not .25 <= background_atmosphere_speed <= 3
            or not 0 <= background_atmosphere_start <= 600):
        raise ValueError("Atmospheric light intensity must be 0–1, duration 8–120 seconds, speed 0.25–3x, and start time 0–600 seconds.")
    if (not isinstance(background_transition_color, str) or len(background_transition_color) != 7
            or not background_transition_color.startswith("#")):
        raise ValueError("Transition color must be a six-digit hex color.")
    try:
        int(background_transition_color[1:], 16)
    except ValueError as exc:
        raise ValueError("Transition color must be a six-digit hex color.") from exc
    try:
        background_audio_volume = float(background_audio_volume)
    except (TypeError, ValueError) as exc:
        raise ValueError("Background audio volume must be a number from 0 to 0.5.") from exc
    if not 0 <= background_audio_volume <= .5:
        raise ValueError("Background audio volume must be between 0 and 0.5 to keep recitation clear.")
    try:
        background_brightness = float(background_brightness)
        background_contrast = float(background_contrast)
        background_saturation = float(background_saturation)
        background_overlay_opacity = float(background_overlay_opacity)
    except (TypeError, ValueError) as exc:
        raise ValueError("Background brightness, contrast, saturation, and overlay opacity must be numbers.") from exc
    if (not .5 <= background_brightness <= 1.5 or not .5 <= background_contrast <= 1.5
            or not 0 <= background_saturation <= 2 or not 0 <= background_overlay_opacity <= .5):
        raise ValueError("Background brightness and contrast must be 0.5–1.5, saturation 0–2, and overlay opacity 0–0.5.")
    if not isinstance(background_overlay_color, str) or len(background_overlay_color) != 7 or not background_overlay_color.startswith("#"):
        raise ValueError("Background overlay color must be a six-digit hex color.")
    try:
        int(background_overlay_color[1:], 16)
    except ValueError as exc:
        raise ValueError("Background overlay color must be a six-digit hex color.") from exc
    background_adjustments = {
        "background_brightness": background_brightness,
        "background_contrast": background_contrast,
        "background_saturation": background_saturation,
    }

    from .scenes import build_scene_plan, synchronize_scene_translations

    (AudioFileClip, CompositeVideoClip, ImageClip, VideoClip, VideoFileClip,
     _concatenate, vfx, CompositeAudioClip, afx) = _moviepy()
    from .reel_viewer import render_playback_layer, render_static_layer
    viewer_options = viewer_options or {
        "show_viewer_title": False, "show_translation": False,
        "show_waveform": False, "show_reciter_badge": False, "show_progress": False,
    }
    translation_lines = translation_lines or []
    audio_source = None
    audio_segment = None
    audio_clips = []
    output = None
    background_clip = None
    background_sources = []
    background_audio_layers = []
    caption_clips = []
    viewer_clips = []
    try:
        if audio_path:
            audio_source = AudioFileClip(str(audio_path))
            audio_clips.append(audio_source)
            if (audio_start is None) != (audio_end is None):
                raise ValueError("Selected recitation audio needs both an absolute start and end time.")
            source_duration = float(audio_source.duration or 0)
            if audio_start is not None and audio_end is not None:
                selected_source_start = float(audio_start)
                selected_source_end = float(audio_end)
                if (not np.isfinite(selected_source_start) or not np.isfinite(selected_source_end)
                        or selected_source_start < 0 or selected_source_end <= selected_source_start
                        or selected_source_start >= source_duration
                        or selected_source_end > source_duration + .05):
                    raise ValueError("Selected recitation boundaries fall outside the downloaded audio file.")
                selected_source_end = min(selected_source_end, source_duration)
                audio_segment = _call(audio_source, "subclip", "subclipped",
                                      selected_source_start, selected_source_end)
                audio_clips.append(audio_segment)
            else:
                selected_source_start = 0.0
                selected_source_end = source_duration
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
        scaled_word_timings = None
        if word_timings is not None:
            scaled_word_timings = [[
                {"start": float(row["start"]) / float(speed),
                 "end": float(row["end"]) / float(speed)}
                for row in ayah_rows
            ] for ayah_rows in word_timings]

        _, caption_options = caption_render_options(caption_style, caption_color, **custom_options)
        scene_plan = build_scene_plan(
            ayahs, ayah_start=ayah_start, durations=durations,
            word_timings=scaled_word_timings, aspect_ratio=aspect_ratio,
            wrap_width=wrap_width, max_lines=max_lines, font_path=font_path,
            show_surah_title=bool(show_surah_title or show_ayah_number),
            padding_y=caption_options.get("padding_y", 24),
            scene_overrides=scene_overrides, default_duration=duration_per_ayah,
            words_per_scene=words_per_scene,
            output_size=(width, height),
        )
        scene_plan = synchronize_scene_translations(
            scene_plan,
            translation_lines if viewer_options.get("show_translation") and show_quran_text else [],
            ayah_start=ayah_start,
        )
        if progress_callback:
            progress_callback(.05)
        # Keep audio selection and visual timing independent. The recitation
        # remains trimmed to the selected source range; a final caption may
        # extend the video with silence after that audio ends.
        audio_timeline_duration = sum(durations)
        recitation_audio_duration = (
            min(float(audio_segment.duration), audio_timeline_duration)
            if audio_segment is not None else None
        )
        scene_ends = [float(scene["end_time"]) for scene in scene_plan
                      if scene.get("end_time") is not None]
        video_duration = max(audio_timeline_duration, max(scene_ends, default=0.0))

        is_video_background = background_path and Path(background_path).suffix.lower() in BACKGROUND_VIDEO_EXTENSIONS
        if background_clips or (background_audio_enabled and is_video_background):
            video_specs = background_clips or [{"path": background_path, "start": 0, "end": None,
                                                "speed": background_speed, "transition": "cut"}]
            background_clip, background_audio_layers = _build_video_sequence(
                video_specs, size=(width, height), theme=theme,
                total_duration=video_duration, fit_mode=background_fit,
                crop_x=crop_x, crop_y=crop_y, default_speed=background_speed,
                loop=background_loop, fps=fps, VideoFileClip=VideoFileClip,
                ImageClip=ImageClip, CompositeVideoClip=CompositeVideoClip,
                vfx=vfx, sources=background_sources,
                include_audio=background_audio_enabled,
                audio_volume=background_audio_volume, afx=afx,
                adjustments=background_adjustments,
                transitions_enabled=transitions_enabled,
                transition_color=background_transition_color,
                VideoClip=VideoClip,
                animation_enabled=background_animation_enabled,
                animation_preset=background_animation_preset,
                animation_intensity=background_animation_intensity,
                animation_duration=background_animation_duration,
                animation_speed=background_animation_speed,
                animation_start_time=background_animation_start,
            )
        elif is_video_background:
            video_source = VideoFileClip(str(background_path), audio=False)
            background_sources.append(video_source)
            if background_speed != 1:
                video_source = video_source.with_speed_scaled(background_speed) if hasattr(video_source, "with_speed_scaled") else video_source.fx(vfx.speedx, factor=background_speed)
                background_sources.append(video_source)
            source_duration = float(video_source.duration)
            if source_duration <= 0:
                raise ValueError("The uploaded background video has no playable frames.")
            first_frame = Image.fromarray(video_source.get_frame(0)).convert("RGB")
            fitted_video, alignment = _fit_video_clip(video_source, (width, height), background_fit, crop_x, crop_y, vfx)
            if fitted_video is not video_source:
                background_sources.append(fitted_video)
            adjusted_video = _adjust_background_video(fitted_video, background_adjustments)
            if adjusted_video is not fitted_video:
                background_sources.append(adjusted_video)
                fitted_video = adjusted_video
            if background_animation_enabled and background_animation_preset != "static":
                moved_video = _animated_video_clip(
                    fitted_video, size=(width, height), preset_id=background_animation_preset,
                    intensity=background_animation_intensity,
                    cycle_duration=background_animation_duration,
                    speed=background_animation_speed, start_time=background_animation_start,
                    VideoClip=VideoClip,
                )
                background_sources.append(moved_video)
                fitted_video = moved_video
            base_clip = None
            if alignment == "contain":
                base_image = (_fit_image(first_frame, (width, height), "blurred") if background_fit == "blurred"
                              else _background(None, (width, height), theme))
                base_clip = ImageClip(np.asarray(base_image)).with_duration(video_duration)
                background_sources.append(base_clip)
            if background_loop:
                if float(fitted_video.duration) < video_duration:
                    fitted_video = fitted_video.with_effects([vfx.Loop(duration=video_duration)])
                    background_sources.append(fitted_video)
                else:
                    fitted_video = _call(fitted_video, "subclip", "subclipped", 0, video_duration)
                    background_sources.append(fitted_video)
                layers = ([base_clip] if base_clip else []) + [fitted_video.with_position("center")]
            else:
                moving_duration = min(float(fitted_video.duration), video_duration)
                fitted_video = _call(fitted_video, "subclip", "subclipped", 0, moving_duration)
                background_sources.append(fitted_video)
                layers = ([base_clip] if base_clip else []) + [fitted_video.with_position("center")]
                if moving_duration < video_duration:
                    still = ImageClip(fitted_video.get_frame(max(0, moving_duration - 1 / fps)))
                    still = _call(still, "set_start", "with_start", moving_duration)
                    still = _call(still, "set_duration", "with_duration", video_duration - moving_duration)
                    if alignment == "contain":
                        still = _call(still, "set_position", "with_position", "center")
                    background_sources.append(still)
                    layers.append(still)
            # MoviePy treats the first clip as the background when use_bgclip
            # is enabled, then computes the composite duration from the
            # remaining overlay clips. With a single video layer that list is
            # empty, and its max(ends) call raises ``max() iterable argument
            # is empty``. The fitted video already has the requested duration
            # in this case, so keep it as the scene directly.
            if len(layers) == 1:
                video_scene = _call(layers[0], "set_duration", "with_duration", video_duration)
            else:
                video_scene = CompositeVideoClip(
                    layers, size=(width, height), use_bgclip=True,
                ).with_duration(video_duration)
            background_sources.append(video_scene)
            dim_layer = ImageClip(np.asarray(Image.new("RGBA", (width, height), (0, 0, 0, 41)))).with_duration(video_duration)
            background_sources.append(dim_layer)
            background_clip = CompositeVideoClip([video_scene, dim_layer], size=(width, height), use_bgclip=True).with_duration(video_duration)
        else:
            wallpaper = _background(background_path, (width, height), theme, background_fit, crop_x, crop_y)
            wallpaper = Image.fromarray(_adjust_background_frame(wallpaper, **background_adjustments))
            wallpaper = Image.blend(wallpaper, Image.new("RGB", wallpaper.size, (0, 0, 0)), 0.16)
            def make_background_frame(time):
                check_cancelled()
                active_preset = (background_animation_preset
                                 if background_animation_enabled else "static")
                if active_preset == "static" or background_animation_intensity <= 0:
                    return np.asarray(wallpaper)
                position = image_animation_phase(time, background_animation_duration,
                                                 background_animation_speed, background_animation_start)
                return _motion_frame(wallpaper, active_preset, position,
                                     background_animation_intensity)

            try:
                background_clip = VideoClip(frame_function=make_background_frame, duration=video_duration)
            except TypeError:
                background_clip = VideoClip(make_frame=make_background_frame, duration=video_duration)

        if background_overlay_opacity:
            overlay_color = _parse_color(background_overlay_color, (0, 0, 0))
            overlay_image = Image.new("RGBA", (width, height), (*overlay_color, round(255 * background_overlay_opacity)))
            overlay_clip = ImageClip(np.asarray(overlay_image)).with_duration(video_duration)
            background_sources.append(overlay_clip)
            background_clip = CompositeVideoClip(
                [background_clip, overlay_clip], size=(width, height), use_bgclip=True
            ).with_duration(video_duration)
            background_sources.append(background_clip)

        if background_atmosphere_enabled and background_atmosphere_intensity > 0:
            light_layer = _ambient_light_layer(
                size=(width, height), duration=video_duration,
                intensity=background_atmosphere_intensity,
                cycle_duration=background_atmosphere_duration,
                speed=background_atmosphere_speed,
                start_time=background_atmosphere_start,
                ImageClip=ImageClip,
            )
            background_sources.append(light_layer)
            background_clip = CompositeVideoClip(
                [background_clip, light_layer], size=(width, height), use_bgclip=True
            ).with_duration(video_duration)
            background_sources.append(background_clip)

        timeline = 0.0
        for index, scene in enumerate(scene_plan):
            check_cancelled()
            current_ayah_num = scene["ayah_number"]
            verse_duration = float(scene["duration"])
            scene_start = (float(scene["start_time"])
                           if scene.get("start_time") is not None else timeline)
            if scene_start < timeline - .001:
                raise ValueError("Scene timing overlaps a previous caption interval.")
            scene_translation = scene.get("translation_text", "")
            scene_caption_y = None
            caption_image = None
            if show_quran_text:
                caption_image = render_caption_image(
                    scene["text"], aspect_ratio=aspect_ratio, font_path=font_path,
                    caption_style=caption_style, caption_color=caption_color,
                    wrap_width=wrap_width, caption_scale=caption_scale,
                    show_surah_title=show_surah_title,
                    surah_title=surah_title, ayah_number=current_ayah_num,
                    surah_color=surah_color, show_ayah_number=show_ayah_number,
                    surah_template=surah_template, ayah_number_template=ayah_number_template,
                    ayah_color=ayah_color, surah_scale=surah_scale,
                    ayah_number_scale=ayah_number_scale, surah_align=surah_align,
                    ayah_number_align=ayah_number_align,
                    translation_text=scene_translation,
                    translation_options=viewer_options,
                    max_height_ratio=.5 if scene_translation else .44,
                    output_size=(width, height), **custom_options,
                )
                caption_clip = ImageClip(np.asarray(caption_image))
                caption_clip = _call(caption_clip, "set_duration", "with_duration", verse_duration)
                caption_clip = _call(caption_clip, "set_start", "with_start", scene_start)
                if transition == "crossfade" and index:
                    fade_in = getattr(vfx, "CrossFadeIn", None) or vfx.FadeIn
                    caption_clip = caption_clip.with_effects([fade_in(min(0.2, verse_duration * 0.15))])
                anchor = {"upper": 0.34, "center": 0.50,
                          "lower": 0.72}[caption_position]
                horizontal_center = int(width * caption_x / 100)
                vertical_center = int(height * (caption_y / 100 if caption_y is not None else anchor))
                min_x = int(width * .03)
                max_x = width - caption_image.width - min_x
                if max_x < min_x:
                    min_x, max_x = 0, max(0, width - caption_image.width)
                caption_x_px = max(min_x, min(horizontal_center - caption_image.width // 2, max_x))
                min_y = int(height * .12)
                max_y = height - caption_image.height - min_y
                if max_y < min_y:
                    min_y, max_y = 0, max(0, height - caption_image.height)
                caption_y_px = max(min_y, min(vertical_center - caption_image.height // 2, max_y))
                scene_caption_y = caption_y_px
                caption_clip = _call(caption_clip, "set_position", "with_position", (caption_x_px, caption_y_px))
                caption_clips.append(caption_clip)

            scene_viewer_options = dict(viewer_options)
            # English is part of the Arabic caption raster above; never repeat
            # it in the separate viewer-layer translation panel.
            scene_viewer_options["show_translation"] = False
            static_image = render_static_layer(
                (width, height), surah_name=viewer_surah_name or str(surah_title or ""),
                surah_number=int(viewer_surah_number or 1), ayah_number=current_ayah_num,
                reciter_name=reciter_name, translation="", options=scene_viewer_options,
            )
            if static_image.getbbox():
                static_clip = ImageClip(np.asarray(static_image))
                static_clip = _call(static_clip, "set_duration", "with_duration", verse_duration)
                static_clip = _call(static_clip, "set_start", "with_start", scene_start)
                viewer_clips.append(static_clip)
            timeline = scene_start + verse_duration

        if viewer_options.get("show_waveform") or viewer_options.get("show_progress"):
            playback_layer = VideoClip(
                lambda time_seconds: render_playback_layer(time_seconds, video_duration,
                                                           (width, height), viewer_options),
                duration=video_duration,
            )
            viewer_clips.append(playback_layer)
        # A rendered video frame is always opaque. Giving MoviePy that invariant
        # prevents creation of a redundant output mask on every frame.
        output = CompositeVideoClip(
            [background_clip, *caption_clips, *viewer_clips],
            size=(width, height), bg_color=(0, 0, 0),
        ).with_duration(video_duration)
        if audio_segment is not None:
            audio_for_video = _call(audio_segment, "subclip", "subclipped", 0, recitation_audio_duration)
            if background_audio_layers:
                audio_for_video = CompositeAudioClip([audio_for_video, *background_audio_layers]).with_duration(video_duration)
            elif video_duration > recitation_audio_duration + .001:
                # Extend the muxed audio stream with silence. This keeps the
                # caption tail visible without reading beyond the selected
                # Quran interval or changing its playback rate.
                audio_for_video = CompositeAudioClip([audio_for_video]).with_duration(video_duration)
            output = _call(output, "set_audio", "with_audio", audio_for_video)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        if progress_callback:
            progress_callback(.15)

        from proglog import ProgressBarLogger

        class RenderProgressLogger(ProgressBarLogger):
            def __init__(self):
                super().__init__(logged_bars=False, min_time_interval=.15)
                self.last_progress = 0.0
                self.started = __import__("time").monotonic()

            def bars_callback(self, bar, attr, value, old_value=None):
                check_cancelled()
                if not progress_callback or attr != "index":
                    return
                state = self.bars.get(bar, {})
                total = state.get("total")
                if not total:
                    return
                fraction = min(1.0, max(0.0, float(value) / float(total)))
                if bar == "frame_index":
                    progress = .15 + .85 * fraction
                    elapsed = max(.001, __import__("time").monotonic() - self.started)
                    speed_fps = float(value) / elapsed
                    eta = max(0.0, (float(total) - float(value)) / speed_fps) if speed_fps > .01 else None
                elif bar in {"chunk", "audio_chunk"}:
                    progress = .01 + .13 * fraction
                    speed_fps = eta = None
                else:
                    return
                self.last_progress = max(self.last_progress, progress)
                if speed_fps is None:
                    progress_callback(self.last_progress)
                else:
                    try:
                        progress_callback(self.last_progress, render_speed_fps=speed_fps,
                                          estimated_remaining_seconds=eta)
                    except TypeError:
                        progress_callback(self.last_progress)

        def write_cpu_video():
            output.write_videofile(
                str(output_path), fps=fps, codec="libx264",
                audio_codec="aac" if audio_segment is not None or background_audio_layers else None,
                # Keep MoviePy's intermediate audio beside the target output,
                # which may be on a writable volume when the app cwd is read-only.
                temp_audiofile=str(Path(output_path).resolve().with_name(f"{Path(output_path).stem}_temp-audio.m4a")),
                remove_temp=True, preset=profile["preset"], threads=4,
                audio_bitrate=audio_bitrate, audio_fps=audio_fps,
                ffmpeg_params=["-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                logger=RenderProgressLogger(),
            )

        if selected_encoder != "cpu":
            from .ffmpeg_encoder import write_hardware_video
            try:
                write_hardware_video(
                    output, output_path, fps=int(fps), ffmpeg=hardware_capabilities["ffmpeg"],
                    encoder=selected_encoder, crf=crf, audio_bitrate=audio_bitrate, audio_fps=audio_fps,
                    progress_callback=progress_callback, cancel_event=cancel_event,
                    gpu_index=hardware_encoder.get("gpu_index") if selected_encoder == "nvidia" else None,
                )
            except JobCancelled:
                raise
            except Exception as exc:
                if requested_encoder != "auto" or selected_encoder != "nvidia":
                    raise
                fallback_reason = f"NVIDIA NVENC failed during encoding; used CPU x264 instead: {exc}"
                Path(output_path).unlink(missing_ok=True)
                hardware_encoder = None
                selected_encoder = "cpu"
                write_cpu_video()
        else:
            write_cpu_video()
        check_cancelled()
        return {"path": str(output_path), "duration": float(output.duration),
                "video_duration": float(output.duration),
                "recitation_audio_duration": recitation_audio_duration,
                "recitation_source_start": selected_source_start if audio_segment is not None else None,
                "recitation_source_end": selected_source_end if audio_segment is not None else None,
                "caption_audio_overrun_seconds": round(max(0.0, video_duration - (recitation_audio_duration or 0.0)), 3)
                if audio_segment is not None else 0.0,
                "caption_timing_warnings": [scene["timing_warning"] for scene in scene_plan
                                            if scene.get("timing_warning")],
                "width": width,
                "height": height, "fps": int(fps), "has_audio": audio_segment is not None or bool(background_audio_layers),
                "quality": quality, "encoder": selected_encoder,
                "requested_encoder": requested_encoder,
                "encoder_name": hardware_encoder["name"] if hardware_encoder else "CPU · x264",
                "gpu_name": hardware_encoder["name"] if hardware_encoder else None,
                "encoder_preset": ("NVENC p4" if selected_encoder == "nvidia" else "Intel Quick Sync")
                                  if selected_encoder != "cpu" else profile["preset"],
                "fallback_reason": fallback_reason, "crf": crf,
                "audio_bitrate": audio_bitrate, "audio_sample_rate": audio_fps,
                "background_audio_enabled": bool(background_audio_enabled),
                "background_audio_volume": background_audio_volume,
                "background_animation_enabled": bool(background_animation_enabled),
                "background_animation_preset": background_animation_preset if background_animation_enabled else "static",
                "background_atmosphere_enabled": bool(background_atmosphere_enabled),
                "background_atmosphere_intensity": background_atmosphere_intensity if background_atmosphere_enabled else 0,
                "scene_count": len(scene_plan),
                "split_ayah_count": len({scene["ayah_number"] for scene in scene_plan if scene["segment_count"] > 1}),
                "phrase_timing_approximate": any(
                    scene.get("timing_mode") == "weighted_estimate" for scene in scene_plan
                ),
                "phrase_timing_mode": (
                    "mixed" if any(scene.get("timing_mode") == "word_timestamp" for scene in scene_plan)
                    and any(scene.get("timing_mode") == "weighted_estimate" for scene in scene_plan)
                    else "word_timestamp" if any(scene.get("timing_mode") == "word_timestamp" for scene in scene_plan)
                    else "weighted_estimate" if any(scene.get("timing_mode") == "weighted_estimate" for scene in scene_plan)
                    else "ayah_boundary_fallback"
                )}
    finally:
        if output is not None:
            output.close()
        if background_clip is not None:
            background_clip.close()
        for clip in caption_clips:
            clip.close()
        for clip in viewer_clips:
            clip.close()
        for clip in audio_clips:
            clip.close()
        for clip in background_sources:
            clip.close()
        temporary_audio = Path(output_path).resolve().with_name(
            f"{Path(output_path).stem}_temp-audio.m4a")
        temporary_audio.unlink(missing_ok=True)
