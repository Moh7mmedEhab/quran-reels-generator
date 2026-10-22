"""Web routes for Quran text, reciters, and video generation."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import tempfile
import time
from io import BytesIO
from threading import Lock
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, render_template, request, send_file, send_from_directory, url_for
from PIL import Image, ImageColor
from werkzeug.utils import secure_filename

from .audio_sources import AudioSourceError, download_recitation, get_audio_url, get_recitation_timings
from .quraa_data import RECITERS, RECITERS_BY_ID
from .quran_data import SURAHS, SURAHS_BY_NUMBER, get_ayahs
from .video_engine import (BACKGROUND_FIT_MODES, BACKGROUND_VIDEO_EXTENSIONS,
                           CAPTION_COLORS, QUALITY_PRESETS, RESOLUTION_PRESETS, SIZES,
                           THEMES, THEME_CATEGORIES, _background, output_dimensions,
                           render_caption_image, render_reel)
from .video_templates import DEFAULT_VIDEO_TEMPLATE, VIDEO_TEMPLATES
from .background_motion import IMAGE_ANIMATION_PRESETS, MOTION_DIRECTIONS, resolve_motion_preset
from .background_sequence_templates import BACKGROUND_SEQUENCE_TEMPLATES
from .background_video_templates import (BACKGROUND_VIDEO_TEMPLATES,
                                         available_background_video_templates,
                                         background_video_template_path)
from .font_catalog import DEFAULT_FONT_ID, FONT_CATALOG, resolve_font
from .scenes import (build_scene_plan, edit_scene_text, merge_scene_with_previous,
                     compose_scene_plan_overrides, redistribute_scene_words, set_scene_lock,
                     split_scene_by_word_count)
from .media_validation import validate_rendered_output
from .ffmpeg_encoder import hardware_encoder_status
from .word_alignment import get_chapter_word_timing
from .design_templates import (AYAH_NUMBER_TEMPLATES, QURAN_TEXT_TEMPLATES,
                               SURAH_NAME_TEMPLATES, TRANSITION_TEMPLATES)
from .reel_viewer import (REEL_VIEWER_TEMPLATES, render_playback_layer,
                          render_static_layer)
from .youtube_metadata import generate_youtube_metadata
from .file_names import unique_download_filename
from .version import APP_VERSION, DISPLAY_VERSION

bp = Blueprint("main", __name__)
_AUDIO_PREVIEW_CACHE_LOCK = Lock()
CAPTION_STYLES = {
    "Dynamic Karaoke (Glow)": "karaoke",
    "Minimalist Subtitle Fade": "minimal",
    "Classic Calligraphic": "classic",
    "Arabic Only (No Translation)": "arabic_only",
    "Elegant Quranic Typography": "quranic",
    "Golden Illuminated": "golden_illuminated",
    "Soft Glowing White": "soft_white",
    "Bold Modern Captions": "bold_modern",
    "Elegant Subtle Shadow": "subtle_shadow",
    "Frosted Translucent Panel": "frosted",
    "Clean Subtitle Style": "clean_subtitle",
    "Cinematic Subtle Outline": "subtle_outline",
    "karaoke": "karaoke", "minimal": "minimal", "classic": "classic", "arabic_only": "arabic_only",
    "quranic": "quranic", "golden_illuminated": "golden_illuminated", "soft_white": "soft_white",
    "bold_modern": "bold_modern", "subtle_shadow": "subtle_shadow", "frosted": "frosted",
    "clean_subtitle": "clean_subtitle", "subtle_outline": "subtle_outline",
}
CAPTION_OPTION_KEYS = (
    "text_bg_enabled", "text_bg_color", "text_bg_opacity", "corner_radius",
    "padding_x", "padding_y", "glow_type", "glow_color", "glow_radius", "glow_opacity",
)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTENSIONS = BACKGROUND_VIDEO_EXTENSIONS


def _caption_options(template, overrides):
    """Merge the editor's caption controls once for preview and final rendering."""
    options = {key: template[key] for key in CAPTION_OPTION_KEYS if key in template}
    options.update({key: overrides[key] for key in CAPTION_OPTION_KEYS if key in overrides})
    return options


def _template_catalog():
    """Expose the complete viewer presets alongside older saved template IDs."""
    return {**VIDEO_TEMPLATES, **REEL_VIEWER_TEMPLATES}


def _viewer_layer_options(data, template=None):
    """Parse the independently configurable optional Reel Viewer elements."""
    template = template or {}
    def flag(key, default):
        value = data.get(key, default)
        return value if isinstance(value, bool) else str(value).lower() in {"true", "1", "yes", "on"}

    def number(key, default, low, high, cast=float):
        try:
            value = cast(data.get(key, default))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key.replace('_', ' ').capitalize()} must be a number.") from exc
        if not low <= value <= high:
            raise ValueError(f"{key.replace('_', ' ').capitalize()} must be between {low} and {high}.")
        return value

    options = {
        "show_viewer_title": flag("viewer_title_enabled", template.get("show_viewer_title", True)),
        "show_title_icon": flag("viewer_title_icon_enabled", template.get("show_title_icon", True)),
        "show_header_surah": flag("viewer_header_surah_enabled", template.get("show_header_surah", True)),
        "header_surah_language": data.get("viewer_header_surah_language", template.get("header_surah_language", "english")),
        "show_ayah_range": flag("viewer_header_range_enabled", template.get("show_ayah_range", True)),
        "ayah_range_language": data.get("viewer_header_range_language", template.get("ayah_range_language", "english")),
        "ayah_range_format": data.get("viewer_header_range_format", template.get("ayah_range_format", "label")),
        "show_qari_in_header": flag("viewer_header_qari_enabled", template.get("show_qari_in_header", True)),
        "viewer_title_text": str(data.get("viewer_title_text", "")).strip()[:48],
        "title_template": data.get("viewer_title_template", template.get("title_template", "dark_pill")),
        "title_color": "#18212b" if data.get("viewer_title_template", template.get("title_template")) == "minimal_white" else template.get("title_color", "#ffffff"),
        "title_accent": data.get("viewer_title_color", template.get("title_accent", "#edc85f")),
        "title_opacity": number("viewer_title_opacity", template.get("title_opacity", .88), 0, 1),
        "title_size": number("viewer_title_size", template.get("title_size", .027), .018, .034),
        "title_position": data.get("viewer_title_position", template.get("title_position", "top")),
        "show_translation": flag("show_translation", template.get("show_translation", False)),
        "translation_color": data.get("translation_color", template.get("translation_color", "#ffffff")),
        "translation_size": number("translation_size", template.get("translation_size", .026), .02, .036),
        "translation_bg_enabled": flag("translation_bg_enabled", template.get("translation_bg_enabled", False)),
        "translation_bg_color": data.get("translation_bg_color", template.get("translation_bg_color", "#10161d")),
        "translation_bg_opacity": number("translation_bg_opacity", template.get("translation_bg_opacity", .4), .1, .9),
        "show_waveform": flag("show_waveform", template.get("show_waveform", True)),
        "waveform_style": data.get("waveform_style", template.get("waveform_style", "gold")),
        "waveform_color": data.get("waveform_color", template.get("waveform_color", "#f0c64b")),
        "waveform_count": number("waveform_count", template.get("waveform_count", 13), 5, 31, int),
        "waveform_speed": number("waveform_speed", template.get("waveform_speed", 1), .25, 2.5),
        "show_reciter_badge": flag("show_reciter_badge", template.get("show_reciter_badge", True)),
        "reciter_label": str(data.get("reciter_label", "")).strip()[:60],
        "reciter_color": data.get("reciter_color", template.get("reciter_color", "#ffffff")),
        "reciter_background": data.get("reciter_background", template.get("reciter_background", "#10161d")),
        "reciter_opacity": number("reciter_opacity", template.get("reciter_opacity", .88), 0, 1),
        "show_progress": flag("show_progress", template.get("show_progress", True)),
        "progress_color": data.get("progress_color", template.get("progress_color", "#edbd36")),
        "progress_track_color": data.get("progress_track_color", template.get("progress_track_color", "#d1d5db")),
        "progress_height": number("progress_height", template.get("progress_height", 6), 2, 16, int),
        "progress_opacity": 1,
        "progress_track_opacity": .54,
    }
    if options["title_template"] not in {"dark_pill", "gold_ornament", "minimal_white"}:
        raise ValueError("Choose a supported Surah title badge style.")
    if options["title_position"] not in {"top", "upper"}:
        raise ValueError("Choose a supported Surah title position.")
    if options["header_surah_language"] not in {"english", "arabic", "both"}:
        raise ValueError("Choose English, Arabic, or both for the header Surah name.")
    if options["ayah_range_language"] not in {"english", "arabic"}:
        raise ValueError("Choose English or Arabic for the ayah range.")
    if options["ayah_range_format"] not in {"label", "compact"}:
        raise ValueError("Choose a supported ayah range label format.")
    if options["waveform_style"] not in {"gold", "white", "glow", "minimal"}:
        raise ValueError("Choose a supported waveform style.")
    if options["waveform_count"] not in {9, 13, 17}:
        raise ValueError("Waveform bar count must be 9, 13, or 17.")
    for key in ("title_color", "title_accent", "translation_color", "waveform_color",
                "reciter_color", "reciter_background", "progress_color", "progress_track_color",
                "translation_bg_color"):
        try:
            ImageColor.getrgb(options[key])
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{key.replace('_', ' ').capitalize()} is not a valid color.") from exc
    return options


def _label_style_options(data, default_font_id):
    """Validate independent Arabic title/number settings shared by preview and export."""
    try:
        surah_opacity = float(data["surah_opacity"]) if data.get("surah_opacity") not in (None, "") else None
        ayah_opacity = float(data["ayah_number_opacity"]) if data.get("ayah_number_opacity") not in (None, "") else None
    except (TypeError, ValueError) as exc:
        raise ValueError("Surah name and ayah number opacity must be valid numbers.") from exc
    if any(value is not None and not 0 <= value <= 1 for value in (surah_opacity, ayah_opacity)):
        raise ValueError("Surah name and ayah number opacity must be between 0 and 1.")
    surah_placement = data.get("surah_placement") or None
    ayah_placement = data.get("ayah_number_placement") or None
    if surah_placement not in (None, "above", "below") or ayah_placement not in (None, "above", "below"):
        raise ValueError("Surah name and ayah number placement must be above or below the Quran text.")
    return {
        "surah_font_path": resolve_font(data.get("surah_font_id", default_font_id)),
        "ayah_number_font_path": resolve_font(data.get("ayah_number_font_id", default_font_id)),
        "surah_opacity": surah_opacity,
        "ayah_number_opacity": ayah_opacity,
        "surah_placement": surah_placement,
        "ayah_number_placement": ayah_placement,
    }


def validate_background_upload(path, extension):
    """Decode uploaded media before accepting it as a background asset."""
    path = Path(path)
    if extension in IMAGE_EXTENSIONS:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
        if width < 16 or height < 16:
            raise ValueError("The background image is too small to use in a video.")
        return {"width": width, "height": height}
    if extension in VIDEO_EXTENSIONS:
        try:
            from moviepy import VideoFileClip
        except ImportError:
            from moviepy.editor import VideoFileClip
        clip = None
        try:
            clip = VideoFileClip(str(path), audio=False)
            duration = float(clip.duration or 0)
            if duration <= 0 or clip.w < 16 or clip.h < 16:
                raise ValueError("The background video has no usable frames.")
            return {"width": int(clip.w), "height": int(clip.h), "duration": duration}
        finally:
            if clip is not None:
                clip.close()
    raise ValueError("Use PNG, JPG, WEBP, MP4, MOV, WEBM, or M4V background media.")


def _surah_caption_title(surah_number):
    """Keep the title in Arabic so the Arabic-only Naskh font never gets Latin tofu."""
    chapter = SURAHS_BY_NUMBER.get(surah_number)
    if chapter:
        return chapter["name_arabic"]
    return f"سُورَةُ {surah_number}"


def _render_template_preview(template_id, ratio):
    """Compose a template card from the same raster layers used by MP4 export."""
    template = _template_catalog()[template_id]
    source_width, source_height = SIZES[ratio]
    scale = min(640 / max(source_width, source_height), 1)
    size = (max(1, round(source_width * scale)), max(1, round(source_height * scale)))
    width, height = size
    background = _background(None, size, template.get("theme", "misty_forest"), "cover")
    background = Image.blend(background, Image.new("RGB", size, (0, 0, 0)), .16).convert("RGBA")
    surah_number, ayah_number = 55, 13
    verse = get_ayahs(surah_number, ayah_number, ayah_number)[0]
    font_id = template.get("font_id", DEFAULT_FONT_ID)
    font_path = resolve_font(font_id, current_app.config.get("ARABIC_FONT"))
    caption = None
    if template.get("show_quran_text", True):
        caption = render_caption_image(
            verse, aspect_ratio=ratio, output_size=size, font_path=font_path,
            caption_style=template.get("caption_style", "quranic"),
            caption_color=template.get("caption_color", "ivory"), wrap_width=85,
            show_surah_title=template.get("show_surah_title", True),
            surah_title=_surah_caption_title(surah_number), ayah_number=ayah_number,
            surah_color=template.get("surah_color"),
            show_ayah_number=template.get("show_ayah_number", True),
            surah_template=template.get("surah_template", "ornamental_gold"),
            ayah_number_template=template.get("ayah_number_template", "gold_medallion"),
            ayah_color=template.get("ayah_color"),
            max_height_ratio=.44,
            **_caption_options(template, {}),
        )
        anchor = {"upper": .34, "center": .54, "lower": .72}.get(
            template.get("caption_position", "center"), .54
        )
        y = max(int(height * .12), min(int(height * anchor - caption.height / 2),
                                        height - caption.height - int(height * .12)))
        background.alpha_composite(caption, ((width - caption.width) // 2, y))

    viewer_options = _viewer_layer_options({}, template)
    viewer_options.update({
        "header_surah_arabic": SURAHS_BY_NUMBER[surah_number]["name_arabic"],
        "ayah_range_start": ayah_number,
        "ayah_range_end": ayah_number,
    })
    static_layer = render_static_layer(
        size, surah_name=SURAHS_BY_NUMBER[surah_number]["english_name"],
        surah_number=surah_number, ayah_number=ayah_number,
        reciter_name=RECITERS_BY_ID["mishary_alafasy"]["name"],
        options=viewer_options,
    )
    background.alpha_composite(static_layer)
    playback_layer = Image.fromarray(render_playback_layer(2.2, 4.0, size, viewer_options))
    background.alpha_composite(playback_layer)
    buffer = BytesIO()
    background.convert("RGB").save(buffer, format="JPEG", quality=88, optimize=True)
    buffer.seek(0)
    return buffer


@bp.get("/")
def studio():
    initial_ayah = get_ayahs(55, 13, 13)[0]
    return render_template("index.html", reciters=RECITERS, surahs=SURAHS, initial_ayah=initial_ayah,
                           themes=THEMES, caption_colors=CAPTION_COLORS,
                           theme_categories=THEME_CATEGORIES,
                           video_templates=_template_catalog(),
                           viewer_templates=REEL_VIEWER_TEMPLATES,
                           text_templates=QURAN_TEXT_TEMPLATES,
                           surah_templates=SURAH_NAME_TEMPLATES,
                           ayah_templates=AYAH_NUMBER_TEMPLATES,
                           font_catalog={key: {"name": value["name"]} for key, value in FONT_CATALOG.items()},
                           default_font_id=DEFAULT_FONT_ID, copyright_year=datetime.now().year,
                           quality_presets=QUALITY_PRESETS,
                           image_animation_presets=IMAGE_ANIMATION_PRESETS,
                           background_sequence_templates=BACKGROUND_SEQUENCE_TEMPLATES,
                           background_video_templates=available_background_video_templates(
                               static_folder=current_app.static_folder),
                           app_version=APP_VERSION, display_version=DISPLAY_VERSION)


@bp.get("/api/version")
def application_version():
    return jsonify({"name": "Quran Reels Generator", "version": APP_VERSION,
                    "display_version": DISPLAY_VERSION})


@bp.get("/api/youtube-metadata")
def youtube_metadata():
    try:
        surah = int(request.args.get("surah", "55"))
        ayah_start = int(request.args.get("start", "13"))
        ayah_end = int(request.args.get("end", str(ayah_start)))
        get_ayahs(surah, ayah_start, ayah_end)
    except (TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    reciter = RECITERS_BY_ID.get(request.args.get("reciter_id", "mishary_alafasy"))
    if reciter is None:
        return jsonify(error="Choose a reciter from the list."), 400
    chapter = SURAHS_BY_NUMBER[surah]
    return jsonify(generate_youtube_metadata(
        surah_number=surah, surah_english=chapter["english_name"],
        surah_arabic=chapter["name_arabic"], ayah_start=ayah_start,
        ayah_end=ayah_end, reciter_name=reciter["name"],
    ))


@bp.get("/api/surahs")
def list_surahs():
    return jsonify({"surahs": SURAHS})


@bp.get("/api/verses")
def list_verses():
    try:
        surah = int(request.args.get("surah", "55"))
        start = int(request.args.get("start", "1"))
        end = int(request.args.get("end", str(start)))
        verses = get_ayahs(surah, start, end)
    except (TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify({"surah": surah, "start": start, "end": end, "ayahs": verses})


@bp.get("/api/backgrounds")
def list_backgrounds():
    return jsonify({"backgrounds": [
        {"id": key, "name": value["name"], "category": THEME_CATEGORIES.get(key, "Other")}
        for key, value in THEMES.items()
    ]})


@bp.get("/api/background-video-templates")
def list_background_video_templates():
    templates = {}
    for template_id, template in available_background_video_templates(
            static_folder=current_app.static_folder).items():
        templates[template_id] = {
            "id": template_id,
            "name": template["name"],
            "description": template["description"],
            "duration": template["duration"],
            "video_url": url_for("static", filename=f"assets/background-videos/{template['filename']}"),
            "poster_url": url_for("main.background_preview", theme=template["theme"], ratio="9:16"),
            "audio": False,
        }
    return jsonify({"templates": templates})


@bp.get("/api/video-templates")
def list_video_templates():
    return jsonify({"templates": _template_catalog(), "viewer_templates": REEL_VIEWER_TEMPLATES,
                    "default": "cinematic_nature"})


@bp.get("/api/background-sequence-templates")
def list_background_sequence_templates():
    return jsonify({"templates": BACKGROUND_SEQUENCE_TEMPLATES,
                    "default": "nature_in_motion"})


@bp.get("/api/design-templates")
def list_design_templates():
    return jsonify({"quran_text": QURAN_TEXT_TEMPLATES,
                    "surah_name": SURAH_NAME_TEMPLATES,
                    "ayah_number": AYAH_NUMBER_TEMPLATES,
                    "reel_viewer": REEL_VIEWER_TEMPLATES,
                    "transitions": TRANSITION_TEMPLATES,
                    "image_animations": IMAGE_ANIMATION_PRESETS,
                    "background_sequences": BACKGROUND_SEQUENCE_TEMPLATES})


@bp.get("/api/fonts")
def list_fonts():
    return jsonify({"fonts": [{"id": key, "name": item["name"]} for key, item in FONT_CATALOG.items()],
                    "default": DEFAULT_FONT_ID})


@bp.get("/api/render-capabilities")
def render_capabilities():
    hardware = hardware_encoder_status(refresh=request.args.get("refresh") == "1")
    return jsonify({"default_encoder": "auto", "encoders": {
        "auto": {"available": True, "name": "NVIDIA Quadro T2000 first, CPU fallback", "reason": None},
        "cpu": {"available": True, "name": "CPU · x264", "reason": None},
        "nvidia": hardware["nvidia"],
        "intel": hardware["intel"],
    }})


@bp.post("/api/scenes/plan")
def scene_plan():
    payload = request.get_json(silent=True) or {}
    try:
        template_id = payload.get("template_id", DEFAULT_VIDEO_TEMPLATE)
        template = _template_catalog().get(template_id)
        if template is None:
            return jsonify(error="Choose a supported video template."), 400
        ayahs = payload.get("ayahs")
        if not isinstance(ayahs, list) or not ayahs or any(not str(text).strip() for text in ayahs):
            return jsonify(error="Provide one or more non-empty ayah text lines."), 400
        ayah_start = int(payload.get("ayah_start", 1))
        wrap_width = int(payload.get("wrap_width", 85))
        max_lines = int(payload.get("max_lines", template.get("max_lines", 5)))
        words_per_scene = int(payload.get("words_per_scene", 8))
        ratio = payload.get("aspect_ratio", "9:16")
        dimensions = output_dimensions(ratio, payload.get("resolution", "1080p"),
                                       payload.get("custom_width"), payload.get("custom_height"))
        show_header = payload.get("show_surah_title", template.get("show_surah_title", False))
        if isinstance(show_header, str):
            show_header = show_header.lower() in ("true", "1", "yes", "on")
        show_number = payload.get("show_ayah_number", show_header)
        if isinstance(show_number, str):
            show_number = show_number.lower() in ("true", "1", "yes", "on")
        font_id = payload.get("font_id", template.get("font_id", DEFAULT_FONT_ID))
        default_scenes = build_scene_plan(
            ayahs, ayah_start=ayah_start, aspect_ratio=ratio, wrap_width=wrap_width,
            max_lines=max_lines, font_path=resolve_font(font_id, current_app.config.get("ARABIC_FONT")),
            show_surah_title=show_header or show_number, output_size=dimensions,
            words_per_scene=words_per_scene, preview_untimed_splits=True,
        )
        composition = compose_scene_plan_overrides(
            ayahs, default_scenes, ayah_start=ayah_start,
            saved_defaults=payload.get("scene_defaults"),
            saved_edits=payload.get("scene_edits"),
        )
        resolved_defaults = default_scenes
        scenes = default_scenes
        if composition["cached_default_ayah_count"] or composition["edited_ayah_count"]:
            overrides = [
                {"scene_id":scene["scene_id"], "ayah_number":scene["ayah_number"],
                 "text":scene["text"], "locked":scene["locked"],
                 "manual_duration":scene.get("manual_duration")}
                for scene in composition["default_scenes"]
            ]
            resolved_defaults = build_scene_plan(
                ayahs, ayah_start=ayah_start, aspect_ratio=ratio, wrap_width=wrap_width,
                max_lines=max_lines, font_path=resolve_font(font_id, current_app.config.get("ARABIC_FONT")),
                show_surah_title=show_header or show_number, output_size=dimensions,
                words_per_scene=words_per_scene, scene_overrides=overrides,
            )
            edited_overrides = [
                {"scene_id":scene["scene_id"], "ayah_number":scene["ayah_number"],
                 "text":scene["text"], "locked":scene["locked"],
                 "manual_duration":scene.get("manual_duration")}
                for scene in composition["scenes"]
            ]
            scenes = build_scene_plan(
                ayahs, ayah_start=ayah_start, aspect_ratio=ratio, wrap_width=wrap_width,
                max_lines=max_lines, font_path=resolve_font(font_id, current_app.config.get("ARABIC_FONT")),
                show_surah_title=show_header or show_number, output_size=dimensions,
                words_per_scene=words_per_scene, scene_overrides=edited_overrides,
            )
    except (TypeError, ValueError, FileNotFoundError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify({"scenes": scenes, "default_scenes": resolved_defaults, "count": len(scenes),
                    "saved_edit_ayah_count": composition["edited_ayah_count"],
                    "approximate_timing": True,
                    "words_per_scene": words_per_scene,
                    "timing_note": "Caption groups use the selected word count. Export uses validated word timestamps when available; otherwise split boundaries use a clearly marked word-length estimate, while an unsplit ayah keeps its measured ayah timing."})


@bp.post("/api/scenes/redistribute")
def scene_redistribute():
    payload = request.get_json(silent=True) or {}
    try:
        ayahs = payload.get("ayahs")
        if not isinstance(ayahs, list) or not ayahs or any(not str(text).strip() for text in ayahs):
            raise ValueError("Provide the source ayah text for every selected ayah.")
        action = payload.get("action", "word_count")
        if action == "merge_previous":
            result = merge_scene_with_previous(
                ayahs, payload.get("scenes"), ayah_start=payload.get("ayah_start", 1),
                scene_index=payload.get("scene_index"),
            )
        elif action == "edit_text":
            result = edit_scene_text(
                ayahs, payload.get("scenes"), ayah_start=payload.get("ayah_start", 1),
                scene_index=payload.get("scene_index"), text=payload.get("text", ""),
            )
        elif action == "set_lock":
            result = set_scene_lock(
                ayahs, payload.get("scenes"), ayah_start=payload.get("ayah_start", 1),
                scene_index=payload.get("scene_index"), locked=payload.get("locked"),
            )
        elif action == "word_count":
            result = redistribute_scene_words(
                ayahs, payload.get("scenes"), ayah_start=payload.get("ayah_start", 1),
                scene_index=payload.get("scene_index"),
                requested_word_count=payload.get("word_count"),
            )
        elif action == "split_by_word_count":
            result = split_scene_by_word_count(
                ayahs, payload.get("scenes"), ayah_start=payload.get("ayah_start", 1),
                scene_index=payload.get("scene_index"),
                words_per_scene=payload.get("words_per_scene"),
            )
        else:
            raise ValueError("Choose a supported scene operation.")
        # Structural edits recalculate timing for changed word allocations.
        # Keep a manual duration only when that exact scene and text survived.
        old_rows = payload.get("scenes") or []
        old_timing = {
            (str(row.get("scene_id") or ""), str(row.get("text", "")).strip()): row.get("manual_duration")
            for row in old_rows if isinstance(row, dict) and row.get("manual_duration") not in (None, "")
        }
        for row in result.get("scenes", []):
            key = (str(row.get("scene_id") or ""), str(row.get("text", "")).strip())
            if key in old_timing:
                row["manual_duration"] = old_timing[key]
    except (TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(result)


@bp.get("/api/backgrounds/<theme>/preview")
def background_preview(theme):
    if theme not in THEMES:
        return jsonify(error="Choose one of the available wallpapers."), 404
    ratio = request.args.get("ratio", "9:16")
    if ratio not in SIZES:
        return jsonify(error="Aspect ratio must be 9:16, 16:9, or 1:1."), 400
    width, height = SIZES[ratio]
    scale = min(960 / max(width, height), 1)
    fit_mode = request.args.get("fit", "cover")
    if fit_mode not in BACKGROUND_FIT_MODES:
        return jsonify(error="Fit must be cover, contain, stretch, or blurred."), 400
    try:
        crop_x = float(request.args.get("x", .5)); crop_y = float(request.args.get("y", .5))
    except ValueError:
        return jsonify(error="Crop position must be between 0 and 1."), 400
    if not 0 <= crop_x <= 1 or not 0 <= crop_y <= 1:
        return jsonify(error="Crop position must be between 0 and 1."), 400
    wallpaper = _background(None, (int(width * scale), int(height * scale)), theme, fit_mode, crop_x, crop_y)
    wallpaper = Image.blend(wallpaper, Image.new("RGB", wallpaper.size, (0, 0, 0)), 0.16)
    buffer = BytesIO()
    wallpaper.save(buffer, format="JPEG", quality=88, optimize=True)
    buffer.seek(0)
    return send_file(buffer, mimetype="image/jpeg", max_age=86400)


@bp.get("/api/video-templates/<template_id>/preview")
def video_template_preview(template_id):
    """Return a real composed frame rather than a background-only template card."""
    if template_id not in _template_catalog():
        return jsonify(error="Choose one of the available video templates."), 404
    ratio = request.args.get("ratio", "9:16")
    if ratio not in SIZES:
        return jsonify(error="Aspect ratio must be 9:16, 16:9, or 1:1."), 400
    try:
        preview = _render_template_preview(template_id, ratio)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        return jsonify(error=str(exc)), 400
    return send_file(preview, mimetype="image/jpeg", max_age=86400)


@bp.post("/api/caption-preview")
def caption_preview():
    """Rasterize the live caption with the exact renderer used by exported MP4s."""
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify(error="Caption text is required."), 400
    ratio = payload.get("aspect_ratio", "9:16")
    if ratio not in SIZES:
        return jsonify(error="Aspect ratio must be 9:16, 16:9, or 1:1."), 400
    template_id = payload.get("template_id", DEFAULT_VIDEO_TEMPLATE)
    template = _template_catalog().get(template_id)
    if template is None:
        return jsonify(error="Choose a supported video template."), 400
    raw_style = payload.get("caption_style", template["caption_style"])
    style = CAPTION_STYLES.get(raw_style, raw_style)
    color = payload.get("caption_color", template["caption_color"])
    font_id = payload.get("font_id", template.get("font_id", DEFAULT_FONT_ID))
    wrap_width = payload.get("wrap_width", 85)
    try:
        output_size = output_dimensions(ratio, payload.get("resolution", "1080p"),
                                        payload.get("custom_width"), payload.get("custom_height"))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    try:
        wrap_width = int(wrap_width)
    except (TypeError, ValueError):
        return jsonify(error="Text wrap width must be 65, 75, 85, or 95 percent."), 400
    if wrap_width not in {65, 75, 85, 95}:
        return jsonify(error="Text wrap width must be 65, 75, 85, or 95 percent."), 400
    custom_opts = _caption_options(template, payload)
    try:
        label_options = _label_style_options(payload, font_id)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    show_surah = payload.get("show_surah_title", template["show_surah_title"])
    if isinstance(show_surah, str):
        show_surah = show_surah.lower() in ("true", "1", "yes", "on")

    surah_num = int(payload.get("surah", payload.get("surah_number", 55)))
    ayah_num = int(payload.get("ayah", payload.get("ayah_number", 13)))
    surah_title = _surah_caption_title(surah_num)
    surah_color = payload.get("surah_color", template["surah_color"])
    show_ayah_number = payload.get("show_ayah_number", show_surah)
    if isinstance(show_ayah_number, str):
        show_ayah_number = show_ayah_number.lower() in ("true", "1", "yes", "on")
    surah_template = payload.get("surah_template", template.get("surah_template", "ornamental_gold"))
    ayah_number_template = payload.get("ayah_number_template", template.get("ayah_number_template", "gold_medallion"))
    if surah_template not in SURAH_NAME_TEMPLATES or ayah_number_template not in AYAH_NUMBER_TEMPLATES:
        return jsonify(error="Choose supported Surah name and ayah number templates."), 400
    try:
        surah_scale = float(payload.get("surah_scale", .46))
        ayah_number_scale = float(payload.get("ayah_number_scale", .38))
    except (TypeError, ValueError):
        return jsonify(error="Surah and ayah label sizes must be valid numbers."), 400
    surah_align = payload.get("surah_align", "center")
    ayah_number_align = payload.get("ayah_number_align", "center")
    if not .25 <= surah_scale <= .7 or not .2 <= ayah_number_scale <= .6:
        return jsonify(error="Surah size must be 25–70% and ayah number size 20–60% of verse size."), 400
    if surah_align not in {"left", "center", "right"} or ayah_number_align not in {"left", "center", "right"}:
        return jsonify(error="Label alignment must be left, center, or right."), 400

    try:
        image = render_caption_image(
            text, aspect_ratio=ratio,
            font_path=resolve_font(font_id, current_app.config.get("ARABIC_FONT")),
            caption_style=style, caption_color=color, wrap_width=wrap_width,
            show_surah_title=show_surah, surah_title=surah_title,
            ayah_number=ayah_num, surah_color=surah_color,
            show_ayah_number=show_ayah_number, surah_template=surah_template,
            ayah_number_template=ayah_number_template,
            ayah_color=payload.get("ayah_color"), surah_scale=surah_scale,
            ayah_number_scale=ayah_number_scale, surah_align=surah_align,
            ayah_number_align=ayah_number_align,
            max_height_ratio=.36 if str(payload.get("translation", "")).strip() else .44,
            output_size=output_size,
            **custom_opts, **label_options,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        return jsonify(error=str(exc)), 400
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png", max_age=0)


@bp.get("/api/reciters")
def list_reciters():
    return jsonify({"reciters": [
        {"id": item["id"], "name": item["name"], "style": item["style"]}
        for item in RECITERS
    ]})


@bp.get("/api/reciters/<reciter_id>/preview")
def preview_reciter(reciter_id):
    reciter = RECITERS_BY_ID.get(reciter_id)
    if reciter is None:
        return jsonify(error="Choose a reciter from the list."), 404
    try:
        surah = int(request.args.get("surah", "55"))
    except ValueError:
        return jsonify(error="Surah number must be between 1 and 114."), 400
    if surah not in SURAHS_BY_NUMBER:
        return jsonify(error="Surah number must be between 1 and 114."), 400
    return jsonify({"audio_url": get_audio_url(reciter, surah), "name": reciter["name"]})


@bp.get("/api/reciters/<reciter_id>/timings")
def preview_reciter_timings(reciter_id):
    reciter = RECITERS_BY_ID.get(reciter_id)
    if reciter is None:
        return jsonify(error="Choose a reciter from the list."), 404
    try:
        surah = int(request.args.get("surah", "55"))
        start = int(request.args.get("start", "1"))
        end = int(request.args.get("end", str(start)))
        verses = get_ayahs(surah, start, end)
        word_data = get_chapter_word_timing(reciter_id, surah, start, end, verses)
        rows = word_data["ayahs"] if word_data else get_recitation_timings(reciter, surah, start, end)
    except (TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    except AudioSourceError as exc:
        return jsonify(error=str(exc)), 502
    except RuntimeError:
        word_data = None
        try:
            rows = get_recitation_timings(reciter, surah, start, end)
        except AudioSourceError as exc:
            return jsonify(error=str(exc)), 502
    durations = []
    for index, row in enumerate(rows):
        next_start = rows[index + 1]["start_time"] if index + 1 < len(rows) else row["end_time"]
        durations.append(max(0.001, (int(next_start) - int(row["start_time"])) / 1000))
    return jsonify({
        "audio_url": url_for("main.preview_reciter_audio", reciter_id=reciter_id,
                              surah=surah, start=start, end=end),
        "audio_start": int(rows[0]["start_time"]) / 1000,
        "audio_end": int(rows[-1]["end_time"]) / 1000,
        "audio_duration": (int(rows[-1]["end_time"]) - int(rows[0]["start_time"])) / 1000,
        "timings": [{"ayah": int(row["ayah"]), "start": int(row["start_time"]) / 1000,
                     "end": int(row["end_time"]) / 1000,
                     **({"words": [
                         {"index": int(word["index"]),
                          "start": (int(word["start_ms"]) - int(row["start_time"])) / 1000,
                          "end": (int(word["end_ms"]) - int(row["start_time"])) / 1000}
                         for word in row["segments"]
                     ]} if word_data else {})} for index, row in enumerate(rows)],
        "timing_source": "quran_foundation_word" if word_data else "mp3quran_ayah",
        "timing_note": ("Validated word timing from Quran Foundation chapter audio."
                        if word_data else "Ayah boundaries only; full ayahs remain visible during recitation."),
    })


@bp.get("/api/reciters/<reciter_id>/audio-preview")
def preview_reciter_audio(reciter_id):
    """Serve a PCM excerpt containing only the selected ayah range."""
    reciter = RECITERS_BY_ID.get(reciter_id)
    if reciter is None:
        return jsonify(error="Choose a reciter from the list."), 404
    try:
        surah = int(request.args.get("surah", "55"))
        start = int(request.args.get("start", "1"))
        end = int(request.args.get("end", str(start)))
        verses = get_ayahs(surah, start, end)
    except (TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400

    cache_dir = Path(current_app.config.get(
        "AUDIO_PREVIEW_FOLDER", Path(tempfile.gettempdir()) / "quran-reels-audio-previews",
    ))
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(f"{reciter_id}:{surah}:{start}:{end}".encode()).hexdigest()
    preview_path = cache_dir / f"{cache_key}.wav"
    with _AUDIO_PREVIEW_CACHE_LOCK:
        try:
            now = time.time()
            cached_segments = []
            for cached in cache_dir.glob("*.wav"):
                try:
                    modified = cached.stat().st_mtime
                    if now - modified > 24 * 60 * 60:
                        cached.unlink(missing_ok=True)
                    else:
                        cached_segments.append((modified, cached))
                except OSError:
                    continue
            if not preview_path.is_file() or preview_path.stat().st_size < 1024:
                track = download_recitation(
                    reciter, surah, start, end,
                    Path(tempfile.gettempdir()) / "quran-reels-uploads",
                    expected_ayahs=verses,
                )
                partial_path = preview_path.with_name(f".{preview_path.stem}-{uuid4().hex}.partial.wav")
                source_audio = selected_audio = None
                try:
                    from moviepy import AudioFileClip
                    source_audio = AudioFileClip(str(track.path))
                    source_duration = float(source_audio.duration or 0)
                    if (track.start < 0 or track.end <= track.start
                            or track.start >= source_duration
                            or track.end > source_duration + .05):
                        raise ValueError("Selected recitation boundaries fall outside the downloaded audio.")
                    selected_audio = source_audio.subclipped(
                        float(track.start), min(float(track.end), source_duration),
                    )
                    selected_audio.write_audiofile(
                        str(partial_path), fps=48000, nbytes=2,
                        codec="pcm_s16le", logger=None,
                    )
                    if not partial_path.is_file() or partial_path.stat().st_size < 1024:
                        raise AudioSourceError("Could not create the selected recitation preview segment.")
                    partial_path.replace(preview_path)
                    cached_segments.append((now, preview_path))
                    for _modified, old_preview in sorted(cached_segments, key=lambda item: item[0])[:-24]:
                        old_preview.unlink(missing_ok=True)
                finally:
                    if selected_audio is not None:
                        selected_audio.close()
                    if source_audio is not None:
                        source_audio.close()
                    partial_path.unlink(missing_ok=True)
                    track.path.unlink(missing_ok=True)
        except (AudioSourceError, OSError, RuntimeError, ValueError, ImportError) as exc:
            current_app.logger.exception("Could not prepare the selected recitation preview")
            preview_path.unlink(missing_ok=True)
            return jsonify(error=str(exc)), 502

    return send_file(preview_path, mimetype="audio/wav", conditional=True,
                     max_age=3600, download_name=f"surah-{surah:03d}-{start}-{end}.wav")


@bp.post("/api/generate")
def generate():
    data = request.form if request.form else (request.get_json(silent=True) or {})
    try:
        ratio = data.get("aspect_ratio", "9:16")
        if ratio not in SIZES:
            return jsonify(error="Aspect ratio must be 9:16, 16:9, or 1:1."), 400
        resolution = str(data.get("resolution", "1080p")).lower()
        try:
            output_size = output_dimensions(ratio, resolution, data.get("custom_width"), data.get("custom_height"))
            fps = int(data.get("fps", 30))
        except (TypeError, ValueError) as exc:
            return jsonify(error=str(exc)), 400
        if fps not in {24, 25, 30, 60}:
            return jsonify(error="Frame rate must be 24, 25, 30, or 60 FPS."), 400
        quality = str(data.get("quality", "balanced")).lower()
        if quality not in QUALITY_PRESETS:
            return jsonify(error="Quality must be fast, balanced, high, or maximum."), 400
        encoder = str(data.get("encoder", "auto")).lower()
        if encoder not in {"auto", "cpu", "nvidia", "intel"}:
            return jsonify(error="Encoder must be auto, cpu, nvidia, or intel."), 400
        if encoder in {"nvidia", "intel"}:
            capability = hardware_encoder_status(refresh=True)[encoder]
            if not capability["available"]:
                return jsonify(error=f"{capability['name']} is unavailable: {capability['reason']}"), 400
        try:
            crf = int(data.get("crf", QUALITY_PRESETS[quality]["crf"]))
            audio_fps = int(data.get("audio_sample_rate", 48000))
        except (TypeError, ValueError):
            return jsonify(error="CRF and audio sample rate must be valid numbers."), 400
        audio_bitrate = str(data.get("audio_bitrate", "192k"))
        if not 16 <= crf <= 34 or audio_bitrate not in {"128k", "192k", "256k", "320k"}:
            return jsonify(error="CRF must be 16–34 and audio bitrate must be 128, 192, 256, or 320 kbps."), 400
        if audio_fps not in {44100, 48000}:
            return jsonify(error="Audio sample rate must be 44100 or 48000 Hz."), 400

        reciter = RECITERS_BY_ID.get(data.get("reciter_id", "mishary_alafasy"))
        if reciter is None:
            return jsonify(error="Choose a reciter from the list."), 400
        try:
            surah = int(data.get("surah", 55))
            ayah_start = int(data.get("ayah_start", 13))
            ayah_end = int(data.get("ayah_end", ayah_start))
        except (TypeError, ValueError):
            return jsonify(error="Surah and ayah numbers must be whole numbers."), 400
        try:
            official_ayahs = get_ayahs(surah, ayah_start, ayah_end)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        chapter = SURAHS_BY_NUMBER[surah]
        metadata_defaults = generate_youtube_metadata(
            surah_number=surah, surah_english=chapter["english_name"],
            surah_arabic=chapter["name_arabic"], ayah_start=ayah_start,
            ayah_end=ayah_end, reciter_name=reciter["name"],
        )
        download_title = str(data.get("video_title", "")).strip()[:100] or metadata_defaults["title"]

        entered_text = str(data.get("ayah_text", "")).strip()
        ayahs = [line.strip() for line in entered_text.splitlines() if line.strip()] if entered_text else official_ayahs
        if len(ayahs) != len(official_ayahs):
            return jsonify(error="Enter one ayah text line for each ayah in the selected range."), 400
        translation_text = str(data.get("translation_text", ""))
        if len(translation_text) > 10000:
            return jsonify(error="Translation text is too long (maximum 10,000 characters)."), 400
        translation_lines = translation_text.splitlines()
        if any(line.strip() for line in translation_lines) and len(translation_lines) != len(official_ayahs):
            return jsonify(error="Enter one translation line per selected ayah, including blank lines where needed."), 400

        template_id = data.get("template_id", DEFAULT_VIDEO_TEMPLATE)
        template = _template_catalog().get(template_id)
        if template is None:
            return jsonify(error="Choose a supported video template."), 400
        try:
            viewer_options = _viewer_layer_options(data, template)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        viewer_options.update({
            "header_surah_arabic": SURAHS_BY_NUMBER[surah]["name_arabic"],
            "ayah_range_start": ayah_start,
            "ayah_range_end": ayah_end,
        })
        show_quran_text = data.get("show_quran_text", True)
        if isinstance(show_quran_text, str):
            show_quran_text = show_quran_text.lower() in ("true", "1", "yes", "on")

        transition = data.get("transition", "crossfade")
        if transition not in {"crossfade", "cut"}:
            transition = "crossfade"
        raw_caption_style = data.get("caption_style", template["caption_style"])
        caption_style = CAPTION_STYLES.get(raw_caption_style, raw_caption_style)
        caption_color = data.get("caption_color", template["caption_color"])
        font_id = data.get("font_id", template.get("font_id", DEFAULT_FONT_ID))
        font_path = resolve_font(font_id, current_app.config.get("ARABIC_FONT"))
        try:
            wrap_width = int(data.get("wrap_width", 85))
        except (TypeError, ValueError):
            return jsonify(error="Text wrap width must be 65, 75, 85, or 95 percent."), 400
        if wrap_width not in {65, 75, 85, 95}:
            return jsonify(error="Text wrap width must be 65, 75, 85, or 95 percent."), 400
        try:
            max_lines = int(data.get("max_lines", template.get("max_lines", 5)))
        except (TypeError, ValueError):
            return jsonify(error="Maximum lines must be between 1 and 8."), 400
        if max_lines not in range(1, 9):
            return jsonify(error="Maximum lines must be between 1 and 8."), 400
        try:
            words_per_scene = int(data.get("words_per_scene", 8))
        except (TypeError, ValueError):
            return jsonify(error="Words per scene must be a whole number from 1 to 30."), 400
        if words_per_scene not in range(1, 31):
            return jsonify(error="Words per scene must be a whole number from 1 to 30."), 400
        theme = data.get("theme", template["theme"])
        if theme not in THEMES:
            return jsonify(error="Choose one of the available background presets."), 400
        try:
            speed = float(data.get("speed", 1.0))
        except (TypeError, ValueError):
            return jsonify(error="Speed must be 0.9, 1.0, or 1.15."), 400
        if speed not in {0.9, 1.0, 1.15}:
            return jsonify(error="Speed must be 0.9, 1.0, or 1.15."), 400

        custom_opts = _caption_options(template, data)
        try:
            label_options = _label_style_options(data, font_id)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

        show_surah = data.get("show_surah_title", template["show_surah_title"])
        if isinstance(show_surah, str):
            show_surah = show_surah.lower() in ("true", "1", "yes", "on")
        show_ayah_number = data.get("show_ayah_number", show_surah)
        if isinstance(show_ayah_number, str):
            show_ayah_number = show_ayah_number.lower() in ("true", "1", "yes", "on")

        surah_title = _surah_caption_title(surah)
        surah_color = data.get("surah_color", template["surah_color"])
        ayah_color = data.get("ayah_color")
        surah_template = data.get("surah_template", template.get("surah_template", "ornamental_gold"))
        ayah_number_template = data.get("ayah_number_template", template.get("ayah_number_template", "gold_medallion"))
        if surah_template not in SURAH_NAME_TEMPLATES or ayah_number_template not in AYAH_NUMBER_TEMPLATES:
            return jsonify(error="Choose supported Surah name and ayah number templates."), 400
        try:
            surah_scale = float(data.get("surah_scale", .46))
            ayah_number_scale = float(data.get("ayah_number_scale", .38))
        except (TypeError, ValueError):
            return jsonify(error="Surah and ayah label sizes must be valid numbers."), 400
        surah_align = data.get("surah_align", "center")
        ayah_number_align = data.get("ayah_number_align", "center")
        if not .25 <= surah_scale <= .7 or not .2 <= ayah_number_scale <= .6:
            return jsonify(error="Surah size must be 25–70% and ayah number size 20–60% of verse size."), 400
        if surah_align not in {"left", "center", "right"} or ayah_number_align not in {"left", "center", "right"}:
            return jsonify(error="Label alignment must be left, center, or right."), 400
        caption_position = data.get("caption_position", template["caption_position"])
        background_fit = data.get("background_fit", template.get("background_fit", "cover"))
        if background_fit not in BACKGROUND_FIT_MODES:
            return jsonify(error="Background fit must be cover, contain, stretch, or blurred."), 400
        try:
            crop_x = float(data.get("crop_x", .5)); crop_y = float(data.get("crop_y", .5))
            background_speed = float(data.get("background_speed", 1.0))
        except (TypeError, ValueError):
            return jsonify(error="Crop position and background speed must be valid numbers."), 400
        if not 0 <= crop_x <= 1 or not 0 <= crop_y <= 1 or not .5 <= background_speed <= 2:
            return jsonify(error="Crop positions must be 0–1 and background speed must be 0.5–2.0."), 400
        background_loop = data.get("background_loop", template.get("background_loop", True))
        if isinstance(background_loop, str):
            background_loop = background_loop.lower() in ("true", "1", "yes", "on")
        background_audio_enabled = data.get("background_audio_enabled", False)
        if isinstance(background_audio_enabled, str):
            background_audio_enabled = background_audio_enabled.lower() in ("true", "1", "yes", "on")
        sequence_enabled = data.get("sequence_enabled", False)
        if isinstance(sequence_enabled, str):
            sequence_enabled = sequence_enabled.lower() in ("true", "1", "yes", "on")
        background_sequence_template = str(data.get("background_sequence_template", "") or "")
        if background_sequence_template and background_sequence_template not in BACKGROUND_SEQUENCE_TEMPLATES:
            return jsonify(error="Choose a supported cinematic background sequence."), 400
        transitions_enabled = data.get("transitions_enabled", False)
        if isinstance(transitions_enabled, str):
            transitions_enabled = transitions_enabled.lower() in ("true", "1", "yes", "on")
        animation_enabled = data.get("background_animation_enabled", False)
        if isinstance(animation_enabled, str):
            animation_enabled = animation_enabled.lower() in ("true", "1", "yes", "on")
        atmosphere_enabled = data.get("background_atmosphere_enabled", False)
        if isinstance(atmosphere_enabled, str):
            atmosphere_enabled = atmosphere_enabled.lower() in ("true", "1", "yes", "on")
        animation_preset = data.get("background_animation_preset", "static")
        if animation_preset not in IMAGE_ANIMATION_PRESETS:
            return jsonify(error="Choose a supported still-image animation preset."), 400
        motion_direction = str(data.get("background_motion_direction", "preset"))
        if motion_direction != "preset" and motion_direction not in MOTION_DIRECTIONS:
            return jsonify(error="Choose left-to-right, right-to-left, top-to-bottom, bottom-to-top, static, or use the saved preset."), 400
        animation_preset = resolve_motion_preset(motion_direction, animation_preset)
        if motion_direction != "preset":
            animation_enabled = motion_direction != "static"
        try:
            animation_intensity = float(data.get("background_animation_intensity", .6))
            animation_duration = float(data.get("background_animation_duration", 12))
            animation_speed = float(data.get("background_animation_speed", 1))
            animation_start = float(data.get("background_animation_start", 0))
        except (TypeError, ValueError):
            return jsonify(error="Background animation start, intensity, duration, and speed must be valid numbers."), 400
        if (not 0 <= animation_intensity <= 1 or not 1 <= animation_duration <= 120
                or not .25 <= animation_speed <= 3 or not 0 <= animation_start <= 600):
            return jsonify(error="Animation start must be 0–600 seconds, intensity 0–1, duration 1–120 seconds, and speed 0.25–3x."), 400
        try:
            atmosphere_intensity = float(data.get("background_atmosphere_intensity", .35))
            atmosphere_duration = float(data.get("background_atmosphere_duration", 36))
            atmosphere_speed = float(data.get("background_atmosphere_speed", .7))
            atmosphere_start = float(data.get("background_atmosphere_start", 0))
        except (TypeError, ValueError):
            return jsonify(error="Atmospheric light intensity, duration, speed, and start time must be valid numbers."), 400
        if (not 0 <= atmosphere_intensity <= 1 or not 8 <= atmosphere_duration <= 120
                or not .25 <= atmosphere_speed <= 3 or not 0 <= atmosphere_start <= 600):
            return jsonify(error="Atmospheric light intensity must be 0–1, duration 8–120 seconds, speed 0.25–3x, and start time 0–600 seconds."), 400
        default_background_transition = data.get("default_background_transition", "crossfade")
        transition_color = data.get("background_transition_color", "#000000")
        try:
            if not isinstance(transition_color, str) or len(transition_color) != 7 or not transition_color.startswith("#"):
                raise ValueError
            int(transition_color[1:], 16)
        except ValueError:
            return jsonify(error="Transition color must be a six-digit hex color."), 400
        supported_background_transitions = {"cut", "crossfade", "dissolve", "fade_black", "fade_color",
                                            "slide_left", "slide_right", "zoom"}
        if default_background_transition not in supported_background_transitions:
            return jsonify(error="Choose a supported background transition."), 400
        try:
            background_audio_volume = float(data.get("background_audio_volume", .08))
        except (TypeError, ValueError):
            return jsonify(error="Background audio volume must be a number from 0 to 0.5."), 400
        if not 0 <= background_audio_volume <= .5:
            return jsonify(error="Background audio volume must be between 0 and 0.5."), 400
        try:
            background_brightness = float(data.get("background_brightness", 1))
            background_contrast = float(data.get("background_contrast", 1))
            background_saturation = float(data.get("background_saturation", 1))
            background_overlay_opacity = float(data.get("background_overlay_opacity", 0))
        except (TypeError, ValueError):
            return jsonify(error="Background color adjustments must be valid numbers."), 400
        if (not .5 <= background_brightness <= 1.5 or not .5 <= background_contrast <= 1.5
                or not 0 <= background_saturation <= 2 or not 0 <= background_overlay_opacity <= .5):
            return jsonify(error="Brightness and contrast must be 0.5–1.5, saturation 0–2, and overlay opacity 0–0.5."), 400
        background_overlay_color = data.get("background_overlay_color", "#0b1626")
        if not isinstance(background_overlay_color, str) or len(background_overlay_color) != 7 or not background_overlay_color.startswith("#"):
            return jsonify(error="Background overlay color must be a six-digit hex color."), 400
        try:
            int(background_overlay_color[1:], 16)
        except ValueError:
            return jsonify(error="Background overlay color must be a six-digit hex color."), 400

        raw_scenes = data.get("scene_overrides")
        if isinstance(raw_scenes, str):
            try:
                raw_scenes = json.loads(raw_scenes)
            except json.JSONDecodeError:
                return jsonify(error="Manual scene data must be valid JSON."), 400

        background_files = [item for item in request.files.getlist("background_clips")
                            if item and item.filename]
        background_video_template = str(data.get("background_video_template", "") or "").strip()
        if background_video_template and background_video_template not in BACKGROUND_VIDEO_TEMPLATES:
            return jsonify(error="Choose one of the available video backgrounds."), 400
        if background_video_template and sequence_enabled and background_sequence_template:
            return jsonify(error="Choose either a bundled video background or a photo sequence template."), 400
        legacy_background_upload = False
        if not background_files:
            legacy_file = request.files.get("background")
            if legacy_file and legacy_file.filename:
                background_files = [legacy_file]
                legacy_background_upload = True
        if background_video_template and background_files:
            return jsonify(error="Choose either a bundled video background or uploaded media, not both."), 400
        if len(background_files) > 12:
            return jsonify(error="A background sequence can contain up to 12 clips."), 400
        raw_clip_settings = data.get("background_clip_settings", "[]")
        if isinstance(raw_clip_settings, str):
            try:
                raw_clip_settings = json.loads(raw_clip_settings)
            except json.JSONDecodeError:
                return jsonify(error="Background clip settings must be valid JSON."), 400
        if not isinstance(raw_clip_settings, list) or (raw_clip_settings and len(raw_clip_settings) != len(background_files)):
            return jsonify(error="Background clip settings must match the uploaded file order."), 400
        if not sequence_enabled and len(background_files) > 1:
            background_files = background_files[:1]
            raw_clip_settings = raw_clip_settings[:1] if raw_clip_settings else []

        job_id = uuid4().hex
        upload_dir = Path(tempfile.gettempdir()) / "quran-reels-uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        background_path = None
        background_paths = []
        background_clip_specs = []
        try:
            if background_video_template:
                background_path = background_video_template_path(
                    background_video_template, static_folder=current_app.static_folder,
                )
                if not background_path.is_file():
                    raise ValueError("The selected bundled video file is missing.")
                validate_background_upload(background_path, background_path.suffix.lower())
            for index, background_file in enumerate(background_files):
                background_name = secure_filename(background_file.filename)
                background_extension = Path(background_name).suffix.lower()
                if background_extension not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
                    raise ValueError("Use PNG, JPG, WEBP, MP4, MOV, WEBM, or M4V background media.")
                is_video = background_extension in VIDEO_EXTENSIONS
                expected_mime = "video/" if is_video else "image/"
                if not (background_file.mimetype or "").startswith(expected_mime):
                    raise ValueError("The selected background media type does not match its file extension.")
                path = upload_dir / f"{job_id}-{index}{background_extension}"
                background_file.save(path)
                background_paths.append(path)
                media_info = validate_background_upload(path, background_extension)
                if not sequence_enabled:
                    background_path = path
                    continue
                settings = raw_clip_settings[index] if raw_clip_settings else {}
                if not isinstance(settings, dict):
                    raise ValueError("Each background clip setting must be an object.")
                try:
                    transition_duration = float(settings.get("transition_duration", .45))
                    clip_transition = settings.get("transition", default_background_transition)
                    if is_video:
                        trim_start = float(settings.get("start", 0))
                        trim_end_raw = settings.get("end")
                        trim_end = media_info["duration"] if trim_end_raw in (None, "") else float(trim_end_raw)
                        clip_speed = float(settings.get("speed", background_speed))
                        if (trim_start < 0 or trim_end <= trim_start or trim_end > media_info["duration"] + .05
                                or not .5 <= clip_speed <= 2):
                            raise ValueError("A background video has an invalid trim range or playback speed.")
                    else:
                        clip_duration = float(settings.get("duration", 4.0))
                        if not 1 <= clip_duration <= 300:
                            raise ValueError("Each still image in a sequence must last 1–300 seconds.")
                        trim_start, trim_end, clip_speed = 0.0, clip_duration, 1.0
                except (TypeError, ValueError) as exc:
                    raise ValueError("Background clip timing, speed, or transition is invalid.") from exc
                if (clip_transition not in supported_background_transitions
                        or not 0 <= transition_duration <= 2):
                    raise ValueError("A background clip uses an unsupported transition or transition duration.")
                if not transitions_enabled:
                    clip_transition = "cut"
                    transition_duration = 0
                background_clip_specs.append({
                    "path": path, "start": trim_start, "end": trim_end, "duration": clip_duration if not is_video else None,
                    "speed": clip_speed, "transition": clip_transition,
                    "transition_duration": transition_duration,
                })
            if (sequence_enabled and not background_files and not background_video_template
                    and background_sequence_template):
                preset = BACKGROUND_SEQUENCE_TEMPLATES[background_sequence_template]
                background_asset_dir = Path(current_app.static_folder) / "assets" / "backgrounds"
                for scene in preset["scenes"]:
                    scene_theme = scene["theme"]
                    if scene_theme not in THEMES:
                        raise ValueError("The selected background sequence refers to an unavailable scene.")
                    scene_path = background_asset_dir / f"{scene_theme}.jpg"
                    if not scene_path.is_file():
                        raise ValueError(f"The bundled image for {THEMES[scene_theme]['name']} is missing.")
                    background_clip_specs.append({
                        "path": scene_path, "start": 0, "end": None,
                        "duration": scene["duration"], "speed": 1,
                        "transition": scene.get("transition", preset["transition"]),
                        "transition_duration": scene.get("transition_duration", preset["transition_duration"]),
                    })
        except (OSError, ValueError, RuntimeError) as exc:
            for path in background_paths:
                path.unlink(missing_ok=True)
            return jsonify(error=f"Could not use the selected background: {exc}"), 400

        app = current_app._get_current_object()
        output_dir = Path(app.config["OUTPUT_FOLDER"])
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{job_id}.mp4"
        partial_path = output_dir / f".{job_id}.partial.mp4"
        # Build this while the request context is available. The render worker
        # runs on a separate thread with only an application context, where
        # Flask cannot infer the host needed by url_for().
        download_url = url_for("main.download", filename=output_path.name)
        manager = app.extensions["render_job_manager"]

        def render_worker(update, cancel_event):
            with app.app_context():
                return execute_render_job(update, cancel_event)

        def execute_render_job(update, cancel_event):
            track = None
            try:
                update(progress=1, phase="audio", message="Fetching recitation timing for the selected ayahs.")

                def audio_progress(received, expected):
                    if expected and expected > 0:
                        fraction = min(1.0, received / expected)
                        progress = 3 + 11 * fraction
                        amount = f"{received / 1024 / 1024:.1f} / {expected / 1024 / 1024:.1f} MB"
                    else:
                        progress = 5
                        amount = f"{received / 1024 / 1024:.1f} MB received"
                    update(progress=progress, phase="audio", message=f"Downloading recitation · {amount}")

                track = download_recitation(
                    reciter, surah, ayah_start, ayah_end, upload_dir,
                    expected_ayahs=official_ayahs if ayahs == official_ayahs else None,
                    cancel_event=cancel_event, on_progress=audio_progress,
                )
                update(progress=15, phase="preparing", message="Preparing Arabic scenes and video layers.")

                def render_progress(fraction, render_speed_fps=None, estimated_remaining_seconds=None):
                    update(
                        progress=15 + min(1, max(0, fraction)) * 84,
                        phase="rendering",
                        message=f"Encoding video · {round(fraction * 100)}%",
                        render_speed_fps=render_speed_fps,
                        estimated_remaining_seconds=estimated_remaining_seconds,
                    )

                result = render_reel(
                    ayahs=ayahs, output_path=partial_path, aspect_ratio=ratio,
                    output_size=output_size, fps=fps, quality=quality, encoder=encoder, crf=crf,
                    audio_bitrate=audio_bitrate, audio_fps=audio_fps,
                    audio_path=track.path, audio_start=track.start, audio_end=track.end,
                    ayah_durations=track.ayah_durations,
                    word_timings=getattr(track, "word_timings", None) if ayahs == official_ayahs else None,
                    background_path=background_path,
                    background_clips=background_clip_specs,
                    theme=theme, transition=transition, caption_style=caption_style, speed=speed,
                    caption_color=caption_color, wrap_width=wrap_width,
                    font_path=font_path, max_lines=max_lines, words_per_scene=words_per_scene,
                    scene_overrides=raw_scenes,
                    background_fit=background_fit, crop_x=crop_x, crop_y=crop_y,
                    background_speed=background_speed, background_loop=background_loop,
                    background_audio_enabled=background_audio_enabled,
                    background_audio_volume=background_audio_volume,
                    background_brightness=background_brightness,
                    background_contrast=background_contrast,
                    background_saturation=background_saturation,
                    background_overlay_color=background_overlay_color,
                    background_overlay_opacity=background_overlay_opacity,
                    background_animation_enabled=animation_enabled,
                    background_animation_preset=animation_preset,
                    background_animation_intensity=animation_intensity,
                    background_animation_duration=animation_duration,
                    background_animation_speed=animation_speed,
                    background_animation_start=animation_start,
                    background_atmosphere_enabled=atmosphere_enabled,
                    background_atmosphere_intensity=atmosphere_intensity,
                    background_atmosphere_duration=atmosphere_duration,
                    background_atmosphere_speed=atmosphere_speed,
                    background_atmosphere_start=atmosphere_start,
                    transitions_enabled=transitions_enabled,
                    background_transition_color=transition_color,
                    ayah_start=ayah_start, show_surah_title=show_surah,
                    show_quran_text=show_quran_text,
                    show_ayah_number=show_ayah_number, surah_template=surah_template,
                    ayah_number_template=ayah_number_template, ayah_color=ayah_color,
                    surah_scale=surah_scale, ayah_number_scale=ayah_number_scale,
                    surah_align=surah_align, ayah_number_align=ayah_number_align,
                    surah_title=surah_title, surah_color=surah_color,
                    viewer_surah_name=SURAHS_BY_NUMBER[surah]["english_name"],
                    viewer_surah_number=surah,
                    reciter_name=reciter["name"], translation_lines=translation_lines,
                    viewer_options=viewer_options,
                    caption_position=caption_position,
                    progress_callback=render_progress,
                    cancel_event=cancel_event,
                    **custom_opts, **label_options
                )
                if cancel_event.is_set():
                    from .job_errors import JobCancelled
                    raise JobCancelled()
                if not partial_path.is_file() or partial_path.stat().st_size < 1024:
                    raise RuntimeError("The encoder did not produce a complete MP4 file.")
                update(progress=99, phase="verification", message="Checking the exported MP4 video and audio streams.")
                playback = validate_rendered_output(partial_path, expected_size=output_size, require_audio=True)
                result.pop("path", None)
                phrase_timing_mode = result.get("phrase_timing_mode", "ayah_boundary_fallback")
                if ayahs == official_ayahs:
                    timing_note = getattr(track, "timing_note", "Ayah-level timing; word-level alignment is not configured.")
                else:
                    timing_note = "Custom caption text differs from the Quran source; exact voice-word alignment was disabled."
                if phrase_timing_mode == "weighted_estimate":
                    timing_note += " Split-scene spans are approximate, weighted by Arabic word length and Quran pause marks within measured ayah durations."
                elif phrase_timing_mode == "mixed":
                    timing_note += " Some split-scene boundaries use exact voice word timestamps; the remaining spans are approximate estimates weighted by Arabic word length and pause marks."
                elif phrase_timing_mode == "word_timestamp":
                    timing_note += " Split-scene boundaries use validated voice word timestamps."
                else:
                    timing_note += " Whole ayahs remain visible for their measured ayah intervals because phrase-level voice timing is unavailable."
                caption_tail = float(result.get("caption_audio_overrun_seconds") or 0)
                if caption_tail > .005:
                    timing_note += (
                        f" The video continues {caption_tail:.2f}s after the selected recitation "
                        "so the final caption remains visible; no Quran audio is added after the selected boundary."
                    )
                result.update({
                    "filename": output_path.name,
                    "download_url": download_url,
                    "download_title": download_title,
                    "reciter": reciter["name"],
                    "surah": SURAHS_BY_NUMBER[surah]["english_name"],
                    "ayah_start": ayah_start,
                    "ayah_end": ayah_end,
                    "recitation_audio_start": float(track.start),
                    "recitation_audio_end": float(track.end),
                    "selected_recitation_duration": round(float(track.end) - float(track.start), 3),
                    "timing_source": (getattr(track, "timing_source", "mp3quran_ayah")
                                      if ayahs == official_ayahs else "ayah_only_custom_text"),
                    "timing_note": timing_note,
                    "phrase_timing_mode": phrase_timing_mode,
                    "phrase_timing_approximate": bool(result.get("phrase_timing_approximate", False)),
                    "theme": theme,
                    "template_id": template_id,
                    "font_id": font_id,
                    "max_lines": max_lines,
                    "words_per_scene": words_per_scene,
                    "caption_color": caption_color,
                    "caption_style": caption_style,
                    "caption_position": caption_position,
                    "wrap_width": wrap_width,
                    "show_surah_title": show_surah, "show_ayah_number": show_ayah_number,
                    "show_quran_text": show_quran_text,
                    "viewer_layers": {**viewer_options,
                                      "translation_count": sum(bool(line.strip()) for line in translation_lines)},
                    "surah_template": surah_template, "ayah_number_template": ayah_number_template,
                    "surah_scale": surah_scale, "ayah_number_scale": ayah_number_scale,
                    "surah_align": surah_align, "ayah_number_align": ayah_number_align,
                    "background_clip_count": len(background_clip_specs),
                    "background_video_template": background_video_template or None,
                    "background_sequence_template": background_sequence_template or None,
                    "background_audio_enabled": background_audio_enabled,
                    "background_brightness": background_brightness,
                    "background_contrast": background_contrast,
                    "background_saturation": background_saturation,
                    "background_overlay_color": background_overlay_color,
                    "background_overlay_opacity": background_overlay_opacity,
                    "background_animation_start": animation_start,
                    "background_motion_direction": motion_direction,
                    "background_atmosphere_enabled": atmosphere_enabled,
                    "background_atmosphere_intensity": atmosphere_intensity if atmosphere_enabled else 0,
                    "background_fit": background_fit,
                    "resolution": resolution, "quality": quality, "fps": fps,
                    "crf": crf, "audio_bitrate": audio_bitrate,
                    "audio_sample_rate": audio_fps,
                    **playback,
                })
                partial_path.replace(output_path)
                return result
            except Exception:
                app.logger.exception("Video render job %s failed", job_id)
                raise
            finally:
                if track is not None:
                    track.path.unlink(missing_ok=True)
                for uploaded_path in background_paths:
                    uploaded_path.unlink(missing_ok=True)
                partial_path.unlink(missing_ok=True)
                partial_audio = partial_path.with_name(f"{partial_path.stem}_temp-audio.m4a")
                partial_audio.unlink(missing_ok=True)

        snapshot = manager.submit(job_id, render_worker)
        return jsonify({
            "job_id": job_id,
            "status": snapshot["status"],
            "status_url": url_for("main.render_job_status", job_id=job_id),
            "cancel_url": url_for("main.cancel_render_job", job_id=job_id),
        }), 202
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        current_app.logger.exception("Video render failed")
        return jsonify(error=f"Video render failed: {exc}"), 500


@bp.get("/api/jobs/<job_id>")
def render_job_status(job_id):
    job = current_app.extensions["render_job_manager"].get(job_id)
    if job is None:
        return jsonify(error="Render job was not found or has expired."), 404
    return jsonify(job)


@bp.post("/api/jobs/<job_id>/cancel")
def cancel_render_job(job_id):
    job = current_app.extensions["render_job_manager"].cancel(job_id)
    if job is None:
        return jsonify(error="Render job was not found or has expired."), 404
    if job["status"] in {"complete", "failed", "cancelled"}:
        return jsonify(job), 409
    return jsonify(job), 202


@bp.get("/outputs/<path:filename>")
def download(filename):
    fallback = "Quran Reel"
    try:
        source_name = Path(filename).name
        result = current_app.extensions["render_job_manager"]
        # Render outputs use UUID storage names; metadata and title are supplied
        # in the current download request so edits do not rename stored files.
        title = request.args.get("title", "").strip()
        if title:
            download_name = unique_download_filename(
                title, fallback, current_app.config["OUTPUT_FOLDER"], source_name,
            )
        else:
            job_id = Path(source_name).stem
            snapshot = result.get(job_id)
            saved_title = ((snapshot or {}).get("result") or {}).get("download_title", "")
            download_name = unique_download_filename(
                saved_title or fallback, fallback,
                current_app.config["OUTPUT_FOLDER"], source_name,
            )
    except (TypeError, ValueError):
        download_name = "Quran Reel.mp4"
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename,
                               as_attachment=True, download_name=download_name)
