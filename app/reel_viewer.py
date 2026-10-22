"""Reusable raster layers for the Reel Viewer, shared by preview and export."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFont


_ASSETS = Path(__file__).resolve().parents[1] / "static" / "assets"
_LATIN_FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
_LATIN_BOLD_FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
_ARABIC_FONT = _ASSETS / "fonts" / "NotoNaskhArabic-Regular.ttf"

REEL_VIEWER_TEMPLATES = {
    "cinematic_nature": {"name": "Cinematic Nature", "theme": "misty_forest", "caption_style": "soft_white", "caption_color": "white", "font_id": "naskh", "caption_position": "center", "show_viewer_title": True, "title_template": "dark_pill", "title_color": "#ffffff", "title_accent": "#edc85f", "title_opacity": .88, "show_surah_arabic": True, "show_ayah_number": True, "show_quran_text": True, "show_translation": False, "translation_color": "#ffffff", "translation_size": .026, "show_waveform": True, "waveform_style": "gold", "waveform_color": "#f0c64b", "waveform_count": 13, "waveform_speed": 1, "show_reciter_badge": True, "reciter_color": "#ffffff", "reciter_background": "#10161d", "reciter_opacity": .88, "show_progress": True, "progress_color": "#edbd36", "progress_track_color": "#d1d5db", "progress_height": 6},
    "golden_quran": {"name": "Golden Quran", "theme": "copper_dusk", "caption_style": "golden_illuminated", "caption_color": "gold", "font_id": "naskh", "caption_position": "center", "show_viewer_title": True, "title_template": "gold_ornament", "title_color": "#fff7e7", "title_accent": "#f2c14e", "title_opacity": .94, "show_surah_arabic": True, "show_ayah_number": True, "show_quran_text": True, "show_translation": False, "translation_color": "#fff2cf", "translation_size": .024, "show_waveform": True, "waveform_style": "glow", "waveform_color": "#ffc84a", "waveform_count": 13, "waveform_speed": .85, "show_reciter_badge": True, "reciter_color": "#ffe5a7", "reciter_background": "#21190b", "reciter_opacity": .92, "show_progress": True, "progress_color": "#ffc84a", "progress_track_color": "#6b6250", "progress_height": 7},
    "minimalist_white": {"name": "Minimalist White", "theme": "pearl_dawn", "caption_style": "subtle_outline", "caption_color": "ink", "font_id": "naskh", "caption_position": "center", "show_viewer_title": True, "title_template": "minimal_white", "title_color": "#18212b", "title_accent": "#006aff", "title_opacity": .94, "show_surah_arabic": False, "show_ayah_number": True, "show_quran_text": True, "show_translation": False, "translation_color": "#ffffff", "translation_size": .023, "show_waveform": True, "waveform_style": "minimal", "waveform_color": "#ffffff", "waveform_count": 9, "waveform_speed": .8, "show_reciter_badge": False, "reciter_color": "#ffffff", "reciter_background": "#10161d", "reciter_opacity": .6, "show_progress": True, "progress_color": "#006aff", "progress_track_color": "#ffffff", "progress_height": 4},
    "emerald_luxury": {"name": "Emerald Islamic Luxury", "theme": "jade_courtyard", "caption_style": "quranic", "caption_color": "ivory", "font_id": "naskh_bold", "caption_position": "center", "show_viewer_title": True, "title_template": "gold_ornament", "title_color": "#f7efdd", "title_accent": "#d2b15d", "title_opacity": .94, "show_surah_arabic": True, "show_ayah_number": True, "show_quran_text": True, "show_translation": False, "translation_color": "#f7efdd", "translation_size": .024, "show_waveform": True, "waveform_style": "gold", "waveform_color": "#d8c06e", "waveform_count": 13, "waveform_speed": .9, "show_reciter_badge": True, "reciter_color": "#f7efdd", "reciter_background": "#12372c", "reciter_opacity": .94, "show_progress": True, "progress_color": "#d8c06e", "progress_track_color": "#637568", "progress_height": 6},
    "night_sky": {"name": "Night Sky", "theme": "sahara_moon", "caption_style": "soft_white", "caption_color": "white", "font_id": "naskh", "caption_position": "center", "show_viewer_title": True, "title_template": "dark_pill", "title_color": "#ffffff", "title_accent": "#9bcfff", "title_opacity": .8, "show_surah_arabic": True, "show_ayah_number": True, "show_quran_text": True, "show_translation": False, "translation_color": "#ffffff", "translation_size": .024, "show_waveform": True, "waveform_style": "white", "waveform_color": "#d9edff", "waveform_count": 17, "waveform_speed": 1.1, "show_reciter_badge": True, "reciter_color": "#ffffff", "reciter_background": "#0b1930", "reciter_opacity": .82, "show_progress": True, "progress_color": "#9bcfff", "progress_track_color": "#5f6c82", "progress_height": 6},
    "soft_light": {"name": "Soft Light", "theme": "golden_dunes", "caption_style": "subtle_shadow", "caption_color": "ivory", "font_id": "naskh", "caption_position": "center", "show_viewer_title": True, "title_template": "minimal_white", "title_color": "#18212b", "title_accent": "#c99a3b", "title_opacity": .9, "show_surah_arabic": True, "show_ayah_number": False, "show_quran_text": True, "show_translation": False, "translation_color": "#ffffff", "translation_size": .024, "show_waveform": True, "waveform_style": "gold", "waveform_color": "#d4a943", "waveform_count": 9, "waveform_speed": .75, "show_reciter_badge": True, "reciter_color": "#ffffff", "reciter_background": "#302516", "reciter_opacity": .72, "show_progress": True, "progress_color": "#d4a943", "progress_track_color": "#f4e8c8", "progress_height": 5},
    "traditional_calligraphy": {"name": "Traditional Calligraphy", "theme": "olive_garden", "caption_style": "quranic", "caption_color": "ivory", "font_id": "naskh_bold", "caption_position": "center", "show_viewer_title": True, "title_template": "gold_ornament", "title_color": "#fff2ca", "title_accent": "#c8a557", "title_opacity": .92, "show_surah_arabic": True, "show_ayah_number": True, "show_quran_text": True, "show_translation": False, "translation_color": "#fff2ca", "translation_size": .023, "show_waveform": True, "waveform_style": "gold", "waveform_color": "#e7c56c", "waveform_count": 13, "waveform_speed": .82, "show_reciter_badge": True, "reciter_color": "#fff2ca", "reciter_background": "#222015", "reciter_opacity": .9, "show_progress": True, "progress_color": "#e7c56c", "progress_track_color": "#68604a", "progress_height": 6},
    "modern_translation": {"name": "Modern Translation", "theme": "sapphire_horizon", "caption_style": "clean_subtitle", "caption_color": "white", "font_id": "naskh", "caption_position": "upper", "show_viewer_title": True, "title_template": "dark_pill", "title_color": "#ffffff", "title_accent": "#73cbff", "title_opacity": .82, "show_surah_arabic": False, "show_ayah_number": True, "show_quran_text": True, "show_translation": True, "translation_color": "#ffffff", "translation_size": .026, "show_waveform": True, "waveform_style": "white", "waveform_color": "#73cbff", "waveform_count": 13, "waveform_speed": 1.2, "show_reciter_badge": True, "reciter_color": "#ffffff", "reciter_background": "#08213a", "reciter_opacity": .86, "show_progress": True, "progress_color": "#55bdff", "progress_track_color": "#637488", "progress_height": 5},
    "elegant_dark": {"name": "Elegant Dark", "theme": "midnight_blue", "caption_style": "soft_white", "caption_color": "white", "font_id": "naskh", "caption_position": "center", "show_viewer_title": True, "title_template": "dark_pill", "title_color": "#ffffff", "title_accent": "#e5c16e", "title_opacity": .9, "show_surah_arabic": True, "show_ayah_number": True, "show_quran_text": True, "show_translation": False, "translation_color": "#ffffff", "translation_size": .024, "show_waveform": True, "waveform_style": "glow", "waveform_color": "#e5c16e", "waveform_count": 13, "waveform_speed": .9, "show_reciter_badge": True, "reciter_color": "#ffffff", "reciter_background": "#10161d", "reciter_opacity": .9, "show_progress": True, "progress_color": "#e5c16e", "progress_track_color": "#64646b", "progress_height": 6},
    "clean_arabic": {"name": "Clean Arabic", "theme": "marble_arch", "caption_style": "minimal", "caption_color": "white", "font_id": "naskh", "caption_position": "center", "show_viewer_title": False, "title_template": "dark_pill", "title_color": "#ffffff", "title_accent": "#e5c16e", "title_opacity": .8, "show_surah_arabic": False, "show_ayah_number": False, "show_quran_text": True, "show_translation": False, "translation_color": "#ffffff", "translation_size": .024, "show_waveform": False, "waveform_style": "minimal", "waveform_color": "#ffffff", "waveform_count": 9, "waveform_speed": 1, "show_reciter_badge": False, "reciter_color": "#ffffff", "reciter_background": "#10161d", "reciter_opacity": .8, "show_progress": True, "progress_color": "#ffffff", "progress_track_color": "#505050", "progress_height": 4},
}

# The route layer and the older visual presets share their caption renderer.
# Supply its required defaults here so the ten viewer templates are complete
# presets for the existing render pipeline as well as for the new viewer layer.
_TEMPLATE_DESCRIPTIONS = {
    "cinematic_nature": "Soft white Naskh, a quiet surah pill, and gold playback details.",
    "golden_quran": "Gold calligraphy and warm ornamental accents over copper dusk.",
    "minimalist_white": "Clean outlined verse, blue timeline, and a light title treatment.",
    "emerald_luxury": "Ivory calligraphy with coordinated emerald and antique-gold badges.",
    "night_sky": "Luminous white verse and cool blue indicators on a moonlit scene.",
    "soft_light": "Gentle cream typography and restrained gold playback markers.",
    "traditional_calligraphy": "Traditional Naskh with measured gold labels and waveform.",
    "modern_translation": "Upper Arabic caption with space for a supplied English translation.",
    "elegant_dark": "Dark cinematic background, glowing verse, and a warm gold timeline.",
    "clean_arabic": "A pared-back Arabic composition with progress only.",
}
for _preset_id, _preset in REEL_VIEWER_TEMPLATES.items():
    _preset["description"] = _TEMPLATE_DESCRIPTIONS[_preset_id]
    _preset.setdefault("show_surah_title", _preset.get("show_surah_arabic", True))
    _preset.setdefault("surah_color", _preset.get("title_accent", "#edc85f"))
    _preset.setdefault("surah_template", "ornamental_gold")
    _preset.setdefault("ayah_number_template", "gold_medallion")
    _preset.setdefault("glow_type", "none")
    _preset.setdefault("text_bg_enabled", False)
    _preset.setdefault("text_bg_color", "#000000")
    _preset.setdefault("text_bg_opacity", 0)
    _preset.setdefault("corner_radius", 24)
    _preset.setdefault("show_title_icon", True)
    _preset.setdefault("title_size", .027)
    _preset.setdefault("title_position", "top")
    _preset.setdefault("translation_bg_enabled", False)
    _preset.setdefault("translation_bg_color", "#10161d")
    _preset.setdefault("translation_bg_opacity", .4)
    _preset.setdefault("show_header_surah", _preset.get("show_viewer_title", True))
    _preset.setdefault("header_surah_language", "english")
    _preset.setdefault("show_ayah_range", _preset.get("show_viewer_title", True))
    _preset.setdefault("ayah_range_language", "english")
    _preset.setdefault("ayah_range_format", "label")
    _preset.setdefault("show_qari_in_header", _preset.get("show_viewer_title", True))
    # The selected qari appears once in the header by default. Users can opt in
    # to the separate lower badge as a second, intentional display.
    _preset["show_reciter_badge"] = False


def _rgba(color: str, opacity: float = 1.0) -> tuple[int, int, int, int]:
    try:
        rgb = ImageColor.getrgb(color)
    except (ValueError, TypeError):
        rgb = (255, 255, 255)
    return (*rgb[:3], round(255 * max(0.0, min(1.0, float(opacity)))))


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if path.is_file():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _arabic_text(text: str) -> bool:
    return any("\u0600" <= char <= "\u06ff" for char in text)


def _measure(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int, int, int]:
    try:
        return draw.textbbox((0, 0), text, font=font,
                             direction="rtl" if _arabic_text(text) else "ltr")
    except (TypeError, ValueError):
        return draw.textbbox((0, 0), text, font=font)


def _draw_text(draw: ImageDraw.ImageDraw, position, text: str, *, font, fill) -> None:
    try:
        draw.text(position, text, font=font, fill=fill,
                  direction="rtl" if _arabic_text(text) else "ltr")
    except (TypeError, ValueError):
        draw.text(position, text, font=font, fill=fill)


def _arabic_digits(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))


def format_ayah_range(start: int, end: int, *, language: str = "english",
                      style: str = "label") -> str:
    """Format an inclusive ayah range for the header in either supported script."""
    start, end = sorted((int(start), int(end)))
    digits = _arabic_digits if language == "arabic" else str
    bounds = digits(start) if start == end else f"{digits(start)}–{digits(end)}"
    if style == "compact":
        return bounds
    if language == "arabic":
        return f"الآية {bounds}" if start == end else f"الآيات {bounds}"
    return f"Ayah {bounds}" if start == end else f"Ayahs {bounds}"


def _wrap(text: str, font, draw: ImageDraw.ImageDraw, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def render_static_layer(size: tuple[int, int], *, surah_name: str, surah_number: int,
                        ayah_number: int, reciter_name: str, translation: str = "",
                        options: dict | None = None) -> Image.Image:
    """Render optional top, translation, and reciter elements as one transparent layer."""
    options = options or {}
    width, height = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    if options.get("show_viewer_title", True):
        title_override = str(options.get("viewer_title_text", "")).strip()
        language = options.get("header_surah_language", "english")
        arabic_name = str(options.get("header_surah_arabic", "")).strip()
        primary_lines: list[tuple[str, bool]] = []
        if options.get("show_header_surah", True):
            if title_override:
                primary_lines.append((title_override, _arabic_text(title_override)))
            elif language in {"english", "both"}:
                primary_lines.append((f"Surah {surah_name}", False))
            if language in {"arabic", "both"} and arabic_name:
                primary_lines.append((arabic_name, True))

        start = int(options.get("ayah_range_start", ayah_number))
        end = int(options.get("ayah_range_end", ayah_number))
        range_text = ""
        if options.get("show_ayah_range", True):
            range_text = format_ayah_range(
                start, end,
                language=options.get("ayah_range_language", "english"),
                style=options.get("ayah_range_format", "label"),
            )
        qari_text = ""
        if options.get("show_qari_in_header", True) and reciter_name:
            qari_text = str(options.get("reciter_label", "")).strip() or f"Sheikh {reciter_name}"
        detail_lines = [text for text in (range_text, qari_text) if text]
        rows: list[tuple[str, bool, bool]] = (
            [(text, is_arabic, True) for text, is_arabic in primary_lines]
            + [(text, _arabic_text(text), False) for text in detail_lines]
        )
        show_icon = options.get("show_title_icon", True)
        if rows or show_icon:
            title_font_size = max(13, int(width * float(options.get("title_size", .027))))
            meta_font_size = max(11, int(width * .020))
            max_width = int(width * .82)
            fonts = []
            boxes = []
            for text, is_arabic, is_primary in rows:
                font_size = title_font_size if is_primary else meta_font_size
                font_path = _ARABIC_FONT if is_arabic and _ARABIC_FONT.is_file() else (
                    _LATIN_BOLD_FONT if is_primary else _LATIN_FONT
                )
                font = _font(font_path, font_size)
                box = _measure(draw, text, font)
                while box[2] - box[0] > max_width and font_size > 10:
                    font_size -= 1
                    font = _font(font_path, font_size)
                    box = _measure(draw, text, font)
                fonts.append(font)
                boxes.append(box)

            icon_size = max(18, int(width * .035)) if show_icon else 0
            gap = max(8, int(width * .012)) if show_icon else max(5, int(width * .008))
            padx, pady = int(width * .045), max(6, int(height * .009))
            row_heights = [max(1, box[3] - box[1]) for box in boxes]
            row_gap = max(2, int(width * .006))
            text_height = sum(row_heights) + row_gap * max(0, len(rows) - 1)
            box_height = max(text_height, icon_size) + 2 * pady
            text_width = max((box[2] - box[0] for box in boxes), default=0)
            box_width = min(int(width * .9), text_width + icon_size + 3 * gap + 2 * padx)
            x = (width - box_width) // 2
            y = int(height * (.10 if options.get("title_position") == "upper" else .055))
            style = options.get("title_template", "dark_pill")
            background = {"dark_pill": "#10161d", "gold_ornament": "#21190b", "minimal_white": "#ffffff"}.get(style, "#10161d")
            border = {"dark_pill": "#69727b", "gold_ornament": "#d6b86f", "minimal_white": "#ffffff"}.get(style, "#69727b")
            foreground = options.get("title_color") or ("#18212b" if style == "minimal_white" else "#ffffff")
            draw.rounded_rectangle((x, y, x + box_width, y + box_height), radius=box_height // 2,
                                   fill=_rgba(background, float(options.get("title_opacity", .88))),
                                   outline=_rgba(border, .72), width=max(1, width // 700))
            content_left = x + padx + icon_size + (gap if show_icon else 0)
            content_width = box_width - (content_left - x) - padx
            top = y + (box_height - text_height) // 2
            for index, ((text, _is_arabic, is_primary), font, box, line_height) in enumerate(
                    zip(rows, fonts, boxes, row_heights)):
                line_width = box[2] - box[0]
                text_x = content_left + (content_width - line_width) // 2 - box[0]
                text_y = top - box[1]
                color = foreground if is_primary else options.get("title_accent", "#edc85f")
                _draw_text(draw, (text_x, text_y), text, font=font, fill=_rgba(color, 1))
                top += line_height + row_gap
            # Simple open-book mark; no external icon asset or font glyph required.
            if show_icon:
                ix, iy = x + padx, y + (box_height - icon_size) // 2
                icon_color = _rgba(options.get("title_accent", "#edc85f"), 1)
                draw.polygon([(ix, iy + 2), (ix + icon_size // 2, iy + 5),
                              (ix + icon_size // 2, iy + icon_size - 2), (ix, iy + icon_size - 5)],
                             fill=None, outline=icon_color)
                draw.polygon([(ix + icon_size, iy + 2), (ix + icon_size // 2, iy + 5),
                              (ix + icon_size // 2, iy + icon_size - 2), (ix + icon_size, iy + icon_size - 5)],
                             fill=None, outline=icon_color)

    if options.get("show_translation") and translation.strip():
        font_size = max(15, int(width * float(options.get("translation_size", .026))))
        font = _font(_LATIN_FONT, font_size)
        text_width = int(width * .84)
        lines = _wrap(translation.strip(), font, draw, text_width)
        line_height = int(font_size * 1.42)
        box_height = len(lines) * line_height
        y = int(height * float(options.get("translation_y", .62)))
        y = min(y, int(height * .685) - box_height)
        color = _rgba(options.get("translation_color", "#ffffff"),
                      float(options.get("translation_opacity", .96)))
        shadow = _rgba("#000000", .84)
        if options.get("translation_bg_enabled"):
            widest = max((draw.textbbox((0, 0), line, font=font)[2] for line in lines), default=0)
            pad = max(6, int(width * .018))
            draw.rounded_rectangle(((width - widest) // 2 - pad, y - pad,
                                    (width + widest) // 2 + pad, y + box_height + pad),
                                   radius=max(6, int(font_size * .35)),
                                   fill=_rgba(options.get("translation_bg_color", "#10161d"),
                                              float(options.get("translation_bg_opacity", .4))))
        for index, line in enumerate(lines):
            bounds = draw.textbbox((0, 0), line, font=font)
            x = (width - (bounds[2] - bounds[0])) // 2 - bounds[0]
            line_y = y + index * line_height - bounds[1]
            draw.text((x + 1, line_y + 2), line, font=font, fill=shadow)
            draw.text((x, line_y), line, font=font, fill=color)

    if options.get("show_reciter_badge", True) and reciter_name:
        label = str(options.get("reciter_label", "")).strip() or f"Sheikh {reciter_name}"
        font = _font(_LATIN_FONT, max(13, int(width * .022)))
        bounds = draw.textbbox((0, 0), label, font=font)
        text_width, text_height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        padx, pady = int(width * .035), int(height * .008)
        box_width = min(int(width * .88), text_width + 2 * padx + int(width * .022))
        box_height = text_height + 2 * pady
        x, y = (width - box_width) // 2, int(height * .75)
        draw.rounded_rectangle((x, y, x + box_width, y + box_height), radius=box_height // 2,
                               fill=_rgba(options.get("reciter_background", "#10161d"),
                                          float(options.get("reciter_opacity", .88))),
                               outline=_rgba(options.get("reciter_color", "#e8ca7a"), .7),
                               width=max(1, width // 900))
        mark_x = x + padx
        center_y = y + box_height // 2
        radius = max(4, int(width * .006))
        draw.ellipse((mark_x - radius, center_y - radius, mark_x + radius, center_y + radius),
                     outline=_rgba(options.get("reciter_color", "#e8ca7a"), 1), width=max(1, width // 900))
        draw.text((mark_x + radius + int(width * .014), y + pady - bounds[1]), label,
                  font=font, fill=_rgba(options.get("reciter_color", "#ffffff"), 1))
    return layer


def render_playback_layer(time_seconds: float, duration: float, size: tuple[int, int],
                          options: dict | None = None) -> np.ndarray:
    """Return accurate playback progress and an animated, non-amplitude waveform."""
    options = options or {}
    width, height = size
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    time_seconds = max(0.0, float(time_seconds))
    duration = max(.001, float(duration))
    if options.get("show_waveform", True):
        count = max(5, min(31, int(options.get("waveform_count", 13))))
        bar_width = max(3, int(width * .008))
        spacing = max(3, int(width * .008))
        heights = [0.25, .42, .68, .42, .82, .55, 1, .5, .74, .35, .65, .4, .26]
        speed = max(.25, min(2.5, float(options.get("waveform_speed", 1.0))))
        baseline = int(height * .695)
        max_height = int(height * .030)
        total_width = count * bar_width + (count - 1) * spacing
        start_x = (width - total_width) // 2
        style = options.get("waveform_style", "gold")
        color = "#ffffff" if style == "white" else options.get("waveform_color", "#f0c64b")
        for index in range(count):
            base = heights[index % len(heights)]
            pulse = .68 + .32 * math.sin(time_seconds * 4.2 * speed + index * .71)
            bar_height = max(3, round(max_height * base * pulse))
            x = start_x + index * (bar_width + spacing)
            draw.rounded_rectangle((x, baseline - bar_height, x + bar_width,
                                    baseline + bar_height // 2), radius=bar_width // 2,
                                   fill=_rgba(color, .75 if style == "minimal" else .95))
        if style == "glow":
            from PIL import ImageFilter
            sharp_bars = image.copy()
            image.alpha_composite(image.filter(ImageFilter.GaussianBlur(max(2, width // 100))))
            image.alpha_composite(sharp_bars)
            draw = ImageDraw.Draw(image)

    if options.get("show_progress", True):
        bar_height = max(2, min(16, int(options.get("progress_height", 6))))
        margin = int(width * .05)
        x0, x1 = margin, width - margin
        y0 = int(height * .976)
        y1 = min(height - 2, y0 + bar_height)
        radius = max(1, bar_height // 2)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=radius,
                               fill=_rgba(options.get("progress_track_color", "#d1d5db"),
                                          float(options.get("progress_track_opacity", .54))))
        progress = max(0.0, min(1.0, time_seconds / duration))
        fill_end = x0 + round((x1 - x0) * progress)
        if fill_end > x0:
            draw.rounded_rectangle((x0, y0, max(x0, fill_end), y1), radius=radius,
                                   fill=_rgba(options.get("progress_color", "#edbd36"),
                                              float(options.get("progress_opacity", 1))))
    return np.asarray(image)


def translation_for_ayah(translation_lines: list[str], ayah_number: int, ayah_start: int) -> str:
    """Return the optional user-supplied translation aligned to an ayah number."""
    index = int(ayah_number) - int(ayah_start)
    return translation_lines[index].strip() if 0 <= index < len(translation_lines) else ""
