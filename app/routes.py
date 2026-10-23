"""Web routes for Quran text, reciters, and video generation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import http.client
import ipaddress
import json
import os
import re
import secrets
import socket
import ssl
import tempfile
import time
from io import BytesIO
from threading import Lock
from uuid import uuid4
from urllib.parse import quote, urljoin, urlsplit

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
                     split_scene_by_word_count, synchronize_scene_translations)
from .media_validation import validate_rendered_output
from .ffmpeg_encoder import hardware_encoder_status
from .word_alignment import get_chapter_word_timing
from .translations import (TRANSLATION_EDITION, TranslationSourceError,
                           TranslationRequestError,
                           TranslationSourceUnavailable,
                           get_translation_range)
from .design_templates import (AYAH_NUMBER_TEMPLATES, QURAN_TEXT_TEMPLATES,
                               SURAH_NAME_TEMPLATES, TRANSITION_TEMPLATES)
from .reel_viewer import (DEFAULT_WAVEFORM_X_OFFSET, DEFAULT_WAVEFORM_Y_OFFSET,
                          REEL_VIEWER_TEMPLATES, WAVEFORM_X_OFFSET_RANGE,
                          WAVEFORM_Y_OFFSET_RANGE, render_playback_layer,
                          render_static_layer)
from .youtube_metadata import generate_youtube_metadata
from .file_names import unique_download_filename
from .preview_storage import (PREVIEW_RETENTION_SECONDS, cleanup_expired_previews,
                              load_preview, new_preview_id, preview_paths,
                              utc_timestamp, write_preview_metadata)
from .version import APP_VERSION, DISPLAY_VERSION

bp = Blueprint("main", __name__)
_AUDIO_PREVIEW_CACHE_LOCK = Lock()
_IMAGE_GENERATION_LOCK = Lock()
_POLLINATIONS_MODEL_CACHE_LOCK = Lock()
_POLLINATIONS_MODEL_CACHE = {"expires": 0.0, "models": []}


def _preview_dimensions(size, max_edge=960):
    """Scale an export down for preview while preserving its aspect ratio."""
    width, height = (int(size[0]), int(size[1]))
    scale = min(1.0, float(max_edge) / max(width, height))
    scaled_width = max(2, int(round(width * scale)))
    scaled_height = max(2, int(round(height * scale)))
    return scaled_width - scaled_width % 2, scaled_height - scaled_height % 2


def _preview_noindex(response):
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
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
MAX_IMPORTED_IMAGE_BYTES = 25 * 1024 * 1024
MAX_IMPORTED_IMAGE_PIXELS = 40_000_000
_IMPORT_IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}


def _public_image_url(url):
    """Parse an external image URL and reject local or non-public destinations."""
    url = str(url or "").strip()
    if any(ord(char) < 33 for char in url) or "\\" in url:
        raise ValueError("The image URL contains invalid characters.")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Enter a valid public image URL.") from exc
    if (parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None or parsed.fragment):
        raise ValueError("Use a public HTTP or HTTPS image URL without credentials or a fragment.")
    host = parsed.hostname.rstrip(".").lower()
    if not host or host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Local and internal image URLs are not allowed.")
    expected_port = 443 if parsed.scheme.lower() == "https" else 80
    if port not in (None, expected_port):
        raise ValueError("Image URLs may use only the standard HTTP or HTTPS port.")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        try:
            host = host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise ValueError("The image URL hostname is invalid.") from exc
        if any(ord(char) < 33 for char in host):
            raise ValueError("The image URL hostname is invalid.")
    else:
        if not literal.is_global:
            raise ValueError("Local and private network image URLs are not allowed.")
    return parsed, host, port or expected_port


def _resolved_public_addresses(host, port):
    """Resolve a host once and return only globally routable addresses to pin."""
    try:
        rows = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("The image host could not be reached.") from exc
    addresses = []
    for row in rows:
        address = row[4][0]
        try:
            parsed = ipaddress.ip_address(address.split("%", 1)[0])
        except ValueError as exc:
            raise ValueError("The image host returned an invalid network address.") from exc
        if not parsed.is_global:
            raise ValueError("The image URL resolves to a local or private network.")
        if address not in addresses:
            addresses.append(address)
    if not addresses:
        raise ValueError("The image host did not resolve to a public address.")
    return addresses


class _PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTP connection pinned to an IP address validated before the request."""
    def __init__(self, host, address, port, timeout):
        super().__init__(host, port=port, timeout=timeout)
        self._address = address

    def connect(self):
        self.sock = socket.create_connection((self._address, self.port), self.timeout)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection pinned to a validated IP while retaining hostname TLS checks."""
    def __init__(self, host, address, port, timeout):
        super().__init__(host, port=port, timeout=timeout, context=ssl.create_default_context())
        self._address = address

    def connect(self):
        raw = socket.create_connection((self._address, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def _download_public_image(url):
    """Download a small supported image, revalidating and pinning every redirect."""
    current_url = url
    for redirect_count in range(6):
        parsed, host, port = _public_image_url(current_url)
        addresses = _resolved_public_addresses(host, port)
        connection_type = _PinnedHTTPSConnection if parsed.scheme.lower() == "https" else _PinnedHTTPConnection
        connection = connection_type(host, addresses[0], port, timeout=12)
        path = quote(parsed.path or "/", safe="/%:@-._~!$&'()*+,;=")
        if parsed.query:
            path += "?" + quote(parsed.query, safe="/?%:@-._~!$&'()*+,;=")
        host_header = f"[{host}]" if ":" in host else host
        try:
            connection.request("GET", path, headers={
                "Host": host_header,
                "User-Agent": "QuranReels-BackgroundImporter/1.0",
                "Accept": "image/png,image/jpeg,image/webp",
                "Accept-Encoding": "identity",
                "Connection": "close",
            })
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                if not location or redirect_count >= 5:
                    raise ValueError("The image URL has too many or invalid redirects.")
                current_url = urljoin(current_url, location)
                continue
            if response.status != 200:
                raise ValueError(f"The image host returned HTTP {response.status}.")
            content_type = (response.getheader("Content-Type") or "").split(";", 1)[0].strip().lower()
            if content_type not in {item[0] for item in _IMPORT_IMAGE_FORMATS.values()}:
                raise ValueError("The URL must return a JPEG, PNG, or WEBP image.")
            length = response.getheader("Content-Length")
            if length:
                try:
                    declared_length = int(length)
                except ValueError as exc:
                    raise ValueError("The image host returned an invalid file size.") from exc
                if declared_length > MAX_IMPORTED_IMAGE_BYTES:
                    raise ValueError("The image is larger than the 25 MB import limit.")
            body = response.read(MAX_IMPORTED_IMAGE_BYTES + 1)
            if len(body) > MAX_IMPORTED_IMAGE_BYTES:
                raise ValueError("The image is larger than the 25 MB import limit.")
            return body, content_type, host
        except (OSError, http.client.HTTPException, ssl.SSLError) as exc:
            raise ValueError("The image could not be downloaded from that URL.") from exc
        finally:
            connection.close()
    raise ValueError("The image URL has too many redirects.")


def _imported_background_folder():
    folder = Path(current_app.config["OUTPUT_FOLDER"]) / "imported-backgrounds"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _imported_background_path(image_id):
    if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", str(image_id or "")):
        return None
    folder = _imported_background_folder()
    metadata_path = folder / f"{image_id}.json"
    if not metadata_path.is_file():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        filename = metadata.get("filename", "")
    except (OSError, json.JSONDecodeError):
        return None
    if filename != f"{image_id}{Path(filename).suffix}" or Path(filename).suffix not in {".jpg", ".png", ".webp"}:
        return None
    image_path = folder / filename
    return (metadata, image_path) if image_path.is_file() and image_path.parent == folder else None


def _caption_options(template, overrides):
    """Merge the editor's caption controls once for preview and final rendering."""
    options = {key: template[key] for key in CAPTION_OPTION_KEYS if key in template}
    options.update({key: overrides[key] for key in CAPTION_OPTION_KEYS if key in overrides})
    return options


def _caption_position_coordinates(data, template, *, has_translation=False):
    """Validate output-frame center coordinates shared by preview and export."""
    preset = data.get("caption_position", template.get("caption_position", "center"))
    if preset not in {"upper", "center", "lower"}:
        raise ValueError("Choose upper, center, or lower-third caption placement.")
    default_y = {"upper": 34, "center": 43 if has_translation else 54, "lower": 72}[preset]
    try:
        x = float(data.get("caption_x", 50))
        y = float(data.get("caption_y", default_y))
    except (TypeError, ValueError) as exc:
        raise ValueError("Caption X and Y positions must be numbers from 0 to 100.") from exc
    if not all(0 <= value <= 100 for value in (x, y)):
        raise ValueError("Caption X and Y positions must be between 0 and 100 percent.")
    return int(round(x)), int(round(y)), preset


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
        "translation_font": data.get("translation_font", template.get("translation_font", "sans")),
        "translation_opacity": number("translation_opacity", template.get("translation_opacity", .96), 0, 1),
        "translation_line_spacing": number("translation_line_spacing", template.get("translation_line_spacing", 1.35), 1, 2.2),
        "translation_gap": number("translation_gap", template.get("translation_gap", .012), .003, .05),
        "translation_align": data.get("translation_align", template.get("translation_align", "center")),
        "translation_wrap_width": number("translation_wrap_width", template.get("translation_wrap_width", .84), .45, .95),
        "translation_bg_enabled": flag("translation_bg_enabled", template.get("translation_bg_enabled", False)),
        "translation_bg_color": data.get("translation_bg_color", template.get("translation_bg_color", "#10161d")),
        "translation_bg_opacity": number("translation_bg_opacity", template.get("translation_bg_opacity", .4), .1, .9),
        "show_waveform": flag("show_waveform", template.get("show_waveform", True)),
        "waveform_style": data.get("waveform_style", template.get("waveform_style", "gold")),
        "waveform_color": data.get("waveform_color", template.get("waveform_color", "#f0c64b")),
        "waveform_count": number("waveform_count", template.get("waveform_count", 13), 5, 31, int),
        "waveform_speed": number("waveform_speed", template.get("waveform_speed", 1), .25, 2.5),
        "waveform_x_offset": number("waveform_x_offset", DEFAULT_WAVEFORM_X_OFFSET,
                                    *WAVEFORM_X_OFFSET_RANGE),
        "waveform_y_offset": number("waveform_y_offset", DEFAULT_WAVEFORM_Y_OFFSET,
                                    *WAVEFORM_Y_OFFSET_RANGE),
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
    if options["translation_font"] not in {"sans", "serif", "noto"}:
        raise ValueError("Choose a supported English translation font.")
    if options["translation_align"] not in {"left", "center", "right"}:
        raise ValueError("English translation alignment must be left, center, or right.")
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
    for key, label in (("surah_color", "Surah name color"), ("ayah_color", "Ayah number color")):
        value = data.get(key)
        if value not in (None, ""):
            _validate_editor_color(value, label)
    try:
        surah_opacity = float(data["surah_opacity"]) if data.get("surah_opacity") not in (None, "") else None
        ayah_opacity = float(data["ayah_number_opacity"]) if data.get("ayah_number_opacity") not in (None, "") else None
    except (TypeError, ValueError) as exc:
        raise ValueError("Surah name and ayah number opacity must be valid numbers.") from exc
    if any(value is not None and not 0 <= value <= 1 for value in (surah_opacity, ayah_opacity)):
        raise ValueError("Surah name and ayah number opacity must be between 0 and 1.")
    try:
        surah_position_x = float(data.get("surah_x_offset", 0))
        surah_position_y = float(data.get("surah_y_offset", 0))
        ayah_position_x = float(data.get("ayah_number_x_offset", 0))
        ayah_position_y = float(data.get("ayah_number_y_offset", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Surah and ayah position offsets must be numbers from -8 to 8 percent.") from exc
    if any(not -8 <= value <= 8 for value in
           (surah_position_x, surah_position_y, ayah_position_x, ayah_position_y)):
        raise ValueError("Surah and ayah position offsets must be between -8 and 8 percent of the frame.")
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
        "surah_position_x": surah_position_x,
        "surah_position_y": surah_position_y,
        "ayah_number_position_x": ayah_position_x,
        "ayah_number_position_y": ayah_position_y,
    }


def _validate_editor_color(value, label, allow_palette=False):
    """Reject malformed editor colors before preview/export silently falls back."""
    if allow_palette and isinstance(value, str) and value in CAPTION_COLORS:
        return value
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value.strip()):
        raise ValueError(f"{label} must be a 6-digit hexadecimal color.")
    return value.strip().lower()


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
                           font_catalog={key: {"name": value["name"],
                                               "css_family": value.get("css_family", "serif"),
                                               "font_weight": value.get("font_weight", 400)}
                                         for key, value in FONT_CATALOG.items()},
                           default_font_id=DEFAULT_FONT_ID, copyright_year=datetime.now().year,
                           quality_presets=QUALITY_PRESETS,
                           image_animation_presets=IMAGE_ANIMATION_PRESETS,
                           background_sequence_templates=BACKGROUND_SEQUENCE_TEMPLATES,
                           background_video_templates=available_background_video_templates(
                               static_folder=current_app.static_folder),
                           app_version=APP_VERSION, display_version=DISPLAY_VERSION)


@bp.get("/images")
def image_studio():
    return render_template("image_generator.html")


@bp.get("/preview/<preview_id>")
def preview_result(preview_id):
    metadata = load_preview(current_app.config["OUTPUT_FOLDER"], preview_id)
    if metadata is None:
        response = current_app.make_response((render_template(
            "result_preview.html", preview=None,
            error="This preview is invalid, unavailable, or expired.",
        ), 404))
        return _preview_noindex(response)
    response = current_app.make_response(render_template(
        "result_preview.html", preview=metadata,
        video_url=url_for("main.preview_video", preview_id=preview_id),
        editor_url=url_for("main.studio"), error=None,
        expires_at_label=datetime.fromtimestamp(float(metadata["expires_at"]), timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    ))
    return _preview_noindex(response)


@bp.get("/preview/<preview_id>/video")
def preview_video(preview_id):
    if load_preview(current_app.config["OUTPUT_FOLDER"], preview_id) is None:
        response = jsonify(error="This preview is invalid, unavailable, or expired.")
        response.status_code = 404
        return _preview_noindex(response)
    paths = preview_paths(current_app.config["OUTPUT_FOLDER"], preview_id)
    response = send_from_directory(paths[0], paths[1].name, mimetype="video/mp4", conditional=True)
    return _preview_noindex(response)


@bp.get("/api/images/models")
def pollinations_image_models():
    """Return the live Pollinations image catalog for the model picker."""
    import os
    import urllib.error
    import urllib.request

    now = time.monotonic()
    with _POLLINATIONS_MODEL_CACHE_LOCK:
        if _POLLINATIONS_MODEL_CACHE["expires"] > now:
            return jsonify(models=_POLLINATIONS_MODEL_CACHE["models"], default_model=os.environ.get(
                "POLLINATIONS_IMAGE_MODEL", "black-forest-labs/flux.1-schnell"
            ).strip())
        headers = {"Accept": "application/json"}
        api_key = os.environ.get("POLLINATIONS_API_KEY", "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        req = urllib.request.Request("https://gen.pollinations.ai/image/models", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                catalog = json.loads(response.read(2 * 1024 * 1024 + 1))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
            if _POLLINATIONS_MODEL_CACHE["models"]:
                return jsonify(models=_POLLINATIONS_MODEL_CACHE["models"], stale=True, default_model=os.environ.get(
                    "POLLINATIONS_IMAGE_MODEL", "black-forest-labs/flux.1-schnell"
                ).strip())
            return jsonify(error="Pollinations model list is unavailable right now."), 503
        if not isinstance(catalog, list):
            return jsonify(error="Pollinations returned an invalid model list."), 502
        models = []
        for item in catalog:
            if not isinstance(item, dict):
                continue
            endpoints = item.get("supported_endpoints") or []
            modalities = item.get("output_modalities") or []
            if item.get("category") != "image" and "image" not in modalities:
                continue
            if endpoints and not any("/image/" in endpoint for endpoint in endpoints):
                continue
            name = item.get("name")
            if not isinstance(name, str) or not name:
                continue
            pricing = item.get("pricing") if isinstance(item.get("pricing"), dict) else {}
            models.append({
                "name": name,
                "aliases": [alias for alias in item.get("aliases", []) if isinstance(alias, str)],
                "title": str(item.get("title") or name),
                "publisher": str(item.get("publisher") or ""),
                "pricing": pricing,
                "paid_only": bool(item.get("paid_only", False)),
                "community": bool(item.get("community", False)),
            })
        models.sort(key=lambda item: (item["publisher"].lower(), item["title"].lower(), item["name"]))
        _POLLINATIONS_MODEL_CACHE.update(models=models, expires=now + 600)
        return jsonify(models=models, default_model=os.environ.get(
            "POLLINATIONS_IMAGE_MODEL", "black-forest-labs/flux.1-schnell"
        ).strip())


class ComfyUIError(RuntimeError):
    """A safe-to-display failure from the configured ComfyUI server."""


class PollinationsError(RuntimeError):
    """A safe-to-display failure from Pollinations."""


class PollinationsNotConfigured(PollinationsError):
    """Pollinations was selected without a server API key."""


def _comfyui_dimensions(ratio):
    # Realistic Vision V6 is an SD 1.5 checkpoint; these multiples of 64
    # preserve the selected ratios at a sensible native resolution.
    return {"9:16": (576, 1024), "16:9": (1024, 576), "1:1": (768, 768)}[ratio]


def _comfyui_workflow(prompt, ratio, checkpoint):
    width, height = _comfyui_dimensions(ratio)
    seed = secrets.randbits(64)
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {
            "text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {
            "text": "", "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {
            "width": width, "height": height, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 24, "cfg": 6.5, "sampler_name": "dpmpp_2m",
            "scheduler": "karras", "denoise": 1.0, "model": ["1", 0],
            "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0]}},
        "6": {"class_type": "VAEDecode", "inputs": {
            "samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {
            "filename_prefix": "quran-reels", "images": ["6", 0]}},
    }


def _comfyui_json(base_url, path, payload=None, timeout=30):
    import urllib.request

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(f"{base_url}{path}", data=data, headers=headers,
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read())


def _generate_comfyui_image(prompt, ratio):
    import os
    import time
    import urllib.parse
    import urllib.request

    base_url = os.environ.get("COMFYUI_BASE_URL", "http://127.0.0.1:8188").strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise ComfyUIError("COMFYUI_BASE_URL must be an http or https URL.")
    checkpoint = os.environ.get(
        "COMFYUI_CHECKPOINT", "Realistic_Vision_V6.0_NV_B1_fp16.safetensors"
    ).strip()
    if not checkpoint or ".." in checkpoint or checkpoint.startswith(("/", "\\")):
        raise ComfyUIError("Set COMFYUI_CHECKPOINT to a model file installed in ComfyUI.")
    try:
        timeout = max(1.0, min(float(os.environ.get("COMFYUI_TIMEOUT_SECONDS", "300")), 1800.0))
        poll_interval = max(0.1, min(float(os.environ.get("COMFYUI_POLL_INTERVAL_SECONDS", "1")), 10.0))
    except ValueError as exc:
        raise ComfyUIError("ComfyUI timeout settings must be numeric.") from exc

    workflow = _comfyui_workflow(prompt, ratio, checkpoint)
    submitted = _comfyui_json(base_url, "/prompt", {"prompt": workflow}, timeout=30)
    prompt_id = submitted.get("prompt_id")
    if not isinstance(prompt_id, str) or not prompt_id:
        raise ComfyUIError("ComfyUI rejected the workflow. Check that the configured checkpoint is installed.")

    deadline = time.monotonic() + timeout
    image_info = None
    while time.monotonic() < deadline:
        history = _comfyui_json(base_url, f"/history/{urllib.parse.quote(prompt_id, safe='')}", timeout=30)
        result = history.get(prompt_id, {})
        for node_output in result.get("outputs", {}).values():
            images = node_output.get("images", []) if isinstance(node_output, dict) else []
            if images:
                image_info = images[0]
                break
        if image_info:
            break
        status = result.get("status", {})
        if status.get("status_str") == "error":
            raise ComfyUIError("ComfyUI failed to render the image. Check the ComfyUI console and model setup.")
        time.sleep(min(poll_interval, max(0, deadline - time.monotonic())))
    if not image_info:
        raise ComfyUIError("ComfyUI did not finish before the configured timeout. Try again or increase COMFYUI_TIMEOUT_SECONDS.")

    filename = image_info.get("filename")
    if not isinstance(filename, str) or not filename:
        raise ComfyUIError("ComfyUI completed without returning an image file.")
    query = urllib.parse.urlencode({
        "filename": filename,
        "subfolder": str(image_info.get("subfolder", "")),
        "type": str(image_info.get("type", "output")),
    })
    req = urllib.request.Request(f"{base_url}/view?{query}")
    with urllib.request.urlopen(req, timeout=30) as response:
        image_bytes = response.read(20 * 1024 * 1024 + 1)
    if not image_bytes or len(image_bytes) > 20 * 1024 * 1024:
        raise ComfyUIError("ComfyUI returned an empty or oversized image.")
    return image_bytes, checkpoint


def _generate_pollinations_image(prompt, ratio, model=None):
    import os
    import urllib.parse
    import urllib.request

    api_key = os.environ.get("POLLINATIONS_API_KEY", "").strip()
    if not api_key:
        raise PollinationsNotConfigured("Pollinations needs a server API key. Set POLLINATIONS_API_KEY in the app's .env file.")
    model = str(model or os.environ.get(
        "POLLINATIONS_IMAGE_MODEL", "black-forest-labs/flux.1-schnell"
    )).strip()
    if not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,120}", model):
        raise PollinationsError("POLLINATIONS_IMAGE_MODEL must be a valid model identifier.")
    width, height = _comfyui_dimensions(ratio)
    query = urllib.parse.urlencode({"model": model, "width": width, "height": height})
    url = "https://gen.pollinations.ai/image/{}?{}".format(
        urllib.parse.quote(prompt, safe=""), query
    )
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/png, image/jpeg, image/webp",
    })
    with urllib.request.urlopen(req, timeout=300) as response:
        image_bytes = response.read(20 * 1024 * 1024 + 1)
    if not image_bytes or len(image_bytes) > 20 * 1024 * 1024:
        raise PollinationsError("Pollinations returned an empty or oversized image.")
    return image_bytes, model


def _generate_pollinations_legacy_image(prompt, ratio, model=None):
    """Use Pollinations' classic image endpoint without an API key."""
    import urllib.parse
    import urllib.request

    supported_models = {"flux", "zimage", "klein"}
    model = str(model or "flux").strip()
    if model not in supported_models:
        raise PollinationsError("Choose flux, zimage, or klein for keyless Pollinations generation.")
    width, height = _comfyui_dimensions(ratio)
    query = urllib.parse.urlencode({"model": model, "width": width, "height": height})
    url = "https://image.pollinations.ai/prompt/{}?{}".format(
        urllib.parse.quote(prompt, safe=""), query
    )
    req = urllib.request.Request(url, headers={
        "Accept": "image/png, image/jpeg, image/webp",
        "User-Agent": "QuranReelsStudio/1.0",
    })
    with urllib.request.urlopen(req, timeout=300) as response:
        image_bytes = response.read(20 * 1024 * 1024 + 1)
    if not image_bytes or len(image_bytes) > 20 * 1024 * 1024:
        raise PollinationsError("Pollinations returned an empty or oversized image.")
    return image_bytes, model


@bp.post("/api/images/generate")
def generate_image():
    """Generate and persist an image with ComfyUI or Pollinations."""
    import urllib.error
    if request.content_length and request.content_length > 16 * 1024:
        return jsonify(error="Image-generation request is too large."), 413
    payload = request.get_json(silent=True) or {}
    user_prompt = str(payload.get("prompt", "")).strip()
    if not user_prompt or len(user_prompt) > 4000:
        return jsonify(error="Enter a prompt of 1–4000 characters."), 400
    ratio = payload.get("ratio", "9:16")
    if ratio not in {"9:16", "16:9", "1:1"}:
        return jsonify(error="Choose a supported aspect ratio."), 400
    prompt = user_prompt
    provider = payload.get("provider", "pollinations_legacy")
    if provider not in {"comfyui", "pollinations", "pollinations_legacy"}:
        return jsonify(error="Choose one of the Pollinations image-generation options."), 400
    if not _IMAGE_GENERATION_LOCK.acquire(blocking=False):
        return jsonify(error="An image is already being generated. Wait for it to finish before starting another."), 429
    try:
        if provider == "pollinations":
            image_bytes, model_name = _generate_pollinations_image(prompt, ratio, payload.get("model"))
            provider_name = "Pollinations"
            error_type = PollinationsError
        elif provider == "pollinations_legacy":
            image_bytes, model_name = _generate_pollinations_legacy_image(prompt, ratio, payload.get("model"))
            provider_name = "Pollinations (no API key)"
            error_type = PollinationsError
        else:
            image_bytes, model_name = _generate_comfyui_image(prompt, ratio)
            provider_name = "ComfyUI"
            error_type = ComfyUIError
        image = Image.open(BytesIO(image_bytes))
        if image.size != _comfyui_dimensions(ratio):
            raise error_type(f"{provider_name} returned dimensions that do not match the selected format.")
        width, height = image.size
        image.verify()
        image = Image.open(BytesIO(image_bytes))
        image_format = image.format
        formats = {"PNG": ("png", "image/png"), "JPEG": ("jpg", "image/jpeg"),
                   "WEBP": ("webp", "image/webp")}
        if image_format not in formats:
            raise error_type(f"{provider_name} returned an unsupported image format.")
        ext, mime = formats[image_format]
        if width < 16 or height < 16:
            raise error_type(f"{provider_name} returned an image that is too small to use as a background.")
        image_id = uuid4().hex
        folder = Path(current_app.config["OUTPUT_FOLDER"]) / "generated-images"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{image_id}.{ext}").write_bytes(image_bytes)
        metadata = {
            "id": image_id, "prompt": user_prompt, "user_prompt": user_prompt,
            "generation_prompt": prompt, "ratio": ratio,
            "width": width, "height": height, "mime_type": mime,
            "provider": provider, "model": f"{provider_name} · {model_name}", "created_at": datetime.now().astimezone().isoformat(),
            "filename": f"{image_id}.{ext}",
        }
        (folder / f"{image_id}.json").write_text(json.dumps(metadata), encoding="utf-8")
        return jsonify(metadata)
    except urllib.error.HTTPError as exc:
        current_app.logger.warning("Image provider %s returned HTTP %s", provider, exc.code)
        if provider in {"pollinations", "pollinations_legacy"}:
            message = ("Pollinations rejected the request. Check the configured model and prompt." if exc.code in (400, 404) else
                       ("Pollinations' classic no-key service could not complete the request. Try its API-key option." if provider == "pollinations_legacy" else
                        "Pollinations could not complete the request. Check the API key, account limits, and try again."))
        else:
            message = ("ComfyUI rejected the workflow. Check its checkpoint and workflow configuration." if exc.code in (400, 404) else
                       "ComfyUI could not complete the request. Check the server and try again.")
        return jsonify(error=message), 502
    except urllib.error.URLError:
        if provider == "pollinations_legacy":
            return jsonify(error="The Pollinations classic no-key service could not be reached. Try its API-key option."), 503
        if provider in {"pollinations", "pollinations_legacy"}:
            return jsonify(error="Cannot reach Pollinations. Check the server's internet connection and try again."), 503
        return jsonify(error="Cannot reach ComfyUI. Start ComfyUI and check COMFYUI_BASE_URL on the server."), 503
    except PollinationsNotConfigured as exc:
        return jsonify(error=str(exc)), 503
    except (ComfyUIError, PollinationsError) as exc:
        return jsonify(error=str(exc)), 502
    except Exception:
        current_app.logger.exception("Image generation failed for provider %s", provider)
        message = ("Image generation failed. Try the Pollinations API-key option." if provider == "pollinations_legacy" else
                   "Image generation failed. Check the Pollinations configuration and try again." if provider == "pollinations" else
                   "Image generation failed. Check the ComfyUI server and model configuration.")
        return jsonify(error=message), 502
    finally:
        _IMAGE_GENERATION_LOCK.release()


def _generated_image_folder():
    return Path(current_app.config["OUTPUT_FOLDER"]) / "generated-images"


def _read_generated_image_metadata(folder, image_id):
    try:
        metadata=json.loads((folder/f"{image_id}.json").read_text(encoding="utf-8"))
    except (OSError,ValueError):
        return None
    extensions={"image/png":".png","image/jpeg":".jpg","image/webp":".webp"}
    expected=extensions.get(metadata.get("mime_type"))
    if not expected or metadata.get("filename") != f"{image_id}{expected}":
        return None
    return metadata


@bp.get("/api/images")
def generated_images():
    folder=_generated_image_folder()
    items=[]
    if folder.exists():
        for path in folder.glob("*.json"):
            try: items.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError,ValueError): continue
    return jsonify(images=sorted(items,key=lambda item:item.get("created_at",""),reverse=True))


@bp.get("/api/images/<image_id>/file")
def generated_image_file(image_id):
    if not re.fullmatch(r"[a-f0-9]{32}",image_id): return jsonify(error="Invalid image ID."),400
    folder=_generated_image_folder()
    metadata=_read_generated_image_metadata(folder,image_id)
    if not metadata:return jsonify(error="Image not found."),404
    suffix=Path(metadata["filename"]).suffix.lower()
    label=secure_filename(str(metadata.get("prompt", ""))[:72]).strip("-_") or "quran-background"
    return send_file(folder/metadata["filename"],mimetype=metadata["mime_type"],as_attachment=request.args.get("download")=="1",download_name=f"{label}-{image_id[:8]}{suffix}")


@bp.delete("/api/images/<image_id>")
def delete_generated_image(image_id):
    if not re.fullmatch(r"[a-f0-9]{32}",image_id): return jsonify(error="Invalid image ID."),400
    folder=_generated_image_folder()
    metadata=_read_generated_image_metadata(folder,image_id)
    if not metadata:return jsonify(error="Image not found."),404
    (folder/metadata["filename"]).unlink(missing_ok=True); (folder/f"{image_id}.json").unlink(missing_ok=True)
    return jsonify(ok=True)


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


@bp.post("/api/backgrounds/import-url")
def import_background_url():
    """Fetch a public image through a pinned, redirect-safe server connection."""
    payload = request.get_json(silent=True) or {}
    url = str(payload.get("url", "")).strip()
    if len(url) > 4096:
        return jsonify(error="Image URL must be 4,096 characters or shorter."), 400
    try:
        body, content_type, source_host = _download_public_image(url)
        with Image.open(BytesIO(body)) as image:
            image_format = str(image.format or "").upper()
            if image_format not in _IMPORT_IMAGE_FORMATS:
                raise ValueError("The downloaded file is not a supported JPEG, PNG, or WEBP image.")
            expected_type, extension = _IMPORT_IMAGE_FORMATS[image_format]
            if content_type != expected_type:
                raise ValueError("The image content does not match the host's image type.")
            width, height = image.size
            if width < 16 or height < 16:
                raise ValueError("The background image is too small to use in a video.")
            if width * height > MAX_IMPORTED_IMAGE_PIXELS:
                raise ValueError("The image exceeds the 40-megapixel safety limit.")
            image.verify()
        with Image.open(BytesIO(body)) as image:
            image.load()
            if image.size != (width, height):
                raise ValueError("The downloaded image could not be decoded consistently.")
    except (ValueError, OSError, Image.DecompressionBombError) as exc:
        return jsonify(error=str(exc)), 400

    image_id = str(uuid4())
    folder = _imported_background_folder()
    filename = f"{image_id}{extension}"
    image_path = folder / filename
    metadata_path = folder / f"{image_id}.json"
    image_tmp = folder / f".{image_id}.image.tmp"
    metadata_tmp = folder / f".{image_id}.json.tmp"
    metadata = {
        "id": image_id, "filename": filename, "width": int(width), "height": int(height),
        "format": image_format, "mime_type": content_type, "size_bytes": len(body),
        "source_host": source_host,
        "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    try:
        with image_tmp.open("xb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        with metadata_tmp.open("x", encoding="utf-8") as stream:
            json.dump(metadata, stream, ensure_ascii=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(image_tmp, image_path)
        os.replace(metadata_tmp, metadata_path)
    except OSError:
        image_tmp.unlink(missing_ok=True)
        metadata_tmp.unlink(missing_ok=True)
        image_path.unlink(missing_ok=True)
        return jsonify(error="The image could not be saved to the persistent background gallery."), 500
    return jsonify({**metadata, "file_url": url_for("main.imported_background_file", image_id=image_id)}), 201


@bp.get("/api/backgrounds/imported")
def list_imported_backgrounds():
    folder = _imported_background_folder()
    items = []
    for metadata_path in folder.glob("*.json"):
        image_id = metadata_path.stem
        found = _imported_background_path(image_id)
        if not found:
            continue
        metadata, _image_path = found
        items.append({**metadata, "file_url": url_for("main.imported_background_file", image_id=image_id)})
    items.sort(key=lambda item: (item.get("imported_at", ""), item["id"]), reverse=True)
    return jsonify(backgrounds=items)


@bp.get("/api/backgrounds/imported/<image_id>/file")
def imported_background_file(image_id):
    found = _imported_background_path(image_id)
    if not found:
        return jsonify(error="Imported background image was not found."), 404
    metadata, image_path = found
    return send_from_directory(image_path.parent, image_path.name, mimetype=metadata["mime_type"],
                               as_attachment=False, conditional=True, max_age=3600)


@bp.delete("/api/backgrounds/imported/<image_id>")
def delete_imported_background(image_id):
    found = _imported_background_path(image_id)
    if not found:
        return jsonify(error="Imported background image was not found."), 404
    _metadata, image_path = found
    (image_path.parent / f"{image_id}.json").unlink(missing_ok=True)
    image_path.unlink(missing_ok=True)
    return jsonify(deleted=True, id=image_id)


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
        translation_lines = payload.get("translation_lines")
        if translation_lines not in (None, []) and (
                not isinstance(translation_lines, list) or len(translation_lines) != len(ayahs)):
            raise ValueError("English translations must contain one line per selected ayah.")
        scenes = synchronize_scene_translations(
            scenes, translation_lines, ayah_start=ayah_start,
        )
        resolved_defaults = synchronize_scene_translations(
            resolved_defaults, translation_lines, ayah_start=ayah_start,
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
        translation_lines = payload.get("translation_lines")
        if translation_lines not in (None, []) and (
                not isinstance(translation_lines, list) or len(translation_lines) != len(ayahs)):
            raise ValueError("English translations must contain one line per selected ayah.")
        result["scenes"] = synchronize_scene_translations(
            result.get("scenes", []), translation_lines,
            ayah_start=payload.get("ayah_start", 1),
        )
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


@bp.get("/api/translations")
def translations_for_range():
    """Return exact, edition-indexed English ayahs from the chapter cache."""
    try:
        surah = int(request.args.get("surah", ""))
        start = int(request.args.get("start", ""))
        end = int(request.args.get("end", str(start)))
        edition = request.args.get("edition", TRANSLATION_EDITION)
        payload = get_translation_range(
            surah, start, end, Path(current_app.config["OUTPUT_FOLDER"]), edition,
        )
    except (TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    except TranslationSourceUnavailable as exc:
        return jsonify(error=str(exc)), 503
    except TranslationSourceError as exc:
        return jsonify(error=str(exc)), 502
    return jsonify(payload)


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
    try:
        color = _validate_editor_color(color, "Quran text color", allow_palette=True)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
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
        viewer_options = _viewer_layer_options(payload, template)
        translation_text = str(payload.get("translation", "")).strip()
        if len(translation_text) > 5000:
            return jsonify(error="One ayah translation is too long to preview."), 400
        if translation_text and not viewer_options["show_translation"]:
            translation_text = ""
        caption_x, caption_y, _caption_position = _caption_position_coordinates(
            payload, template, has_translation=bool(translation_text)
        )
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    default_show_surah = template.get("show_surah_title", False) if "template_id" in payload else False
    default_show_ayah = template.get("show_ayah_number", False) if "template_id" in payload else False
    show_surah = payload.get("show_surah_title", default_show_surah)
    if isinstance(show_surah, str):
        show_surah = show_surah.lower() in ("true", "1", "yes", "on")

    surah_num = int(payload.get("surah", payload.get("surah_number", 55)))
    ayah_num = int(payload.get("ayah", payload.get("ayah_number", 13)))
    surah_title = _surah_caption_title(surah_num)
    surah_color = payload.get("surah_color", template["surah_color"])
    show_ayah_number = payload.get("show_ayah_number", default_show_ayah)
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
            translation_text=translation_text, translation_options=viewer_options,
            max_height_ratio=.5 if translation_text else .44,
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
        {key: item[key] for key in (
            "id", "group_id", "name", "recording_name", "style", "riwayah",
            "available_surahs", "available_surah_numbers", "source", "source_url",
            "audio_base_url", "timing_provider", "timing_source", "timing_source_url",
        )}
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
    if surah not in reciter.get("available_surah_numbers", range(1, 115)):
        return jsonify(error="This recording has no verified audio for the selected Surah."), 404
    try:
        audio_url = get_audio_url(reciter, surah)
    except AudioSourceError as exc:
        return jsonify(error=str(exc)), 503
    return jsonify({"audio_url": audio_url, "name": reciter["name"]})


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
        if surah not in reciter.get("available_surah_numbers", range(1, 115)):
            return jsonify(error="This recording has no verified audio for the selected Surah."), 404
        word_data = (None if reciter.get("timing_provider") == "qud"
                     else get_chapter_word_timing(reciter_id, surah, start, end, verses))
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
    qud_stitched = not word_data and reciter.get("timing_provider") == "qud"
    if qud_stitched:
        # The preview endpoint stitches only selected canonical windows, so
        # expose timing on that compact timeline rather than chapter offsets.
        timing_rows = []
        cursor = 0
        for row in rows:
            duration = int(row["end_time"]) - int(row["start_time"])
            timing_rows.append({"ayah": row["ayah"], "start_time": cursor,
                                "end_time": cursor + duration})
            cursor += duration
        rows = timing_rows
        audio_start_ms, audio_end_ms = 0, cursor
        timing_source = "qud_ayah"
        timing_note = (
            "Pinned QUD v3.2.0 ayah boundaries matched to this recording. "
            "The preview contains only the selected canonical ayah clips; "
            "phrase splits use the labeled ayah-duration fallback."
        )
    else:
        audio_start_ms, audio_end_ms = int(rows[0]["start_time"]), int(rows[-1]["end_time"])
        timing_source = "quran_foundation_word" if word_data else "mp3quran_ayah"
        timing_note = ("Validated word timing from Quran Foundation chapter audio."
                       if word_data else "Ayah boundaries only; full ayahs remain visible during recitation.")
    return jsonify({
        "audio_url": url_for("main.preview_reciter_audio", reciter_id=reciter_id,
                              surah=surah, start=start, end=end),
        "audio_start": audio_start_ms / 1000,
        "audio_end": audio_end_ms / 1000,
        "audio_duration": (audio_end_ms - audio_start_ms) / 1000,
        "timings": [{"ayah": int(row["ayah"]), "start": int(row["start_time"]) / 1000,
                     "end": int(row["end_time"]) / 1000,
                     **({"words": [
                         {"index": int(word["index"]),
                          "start": (int(word["start_ms"]) - int(row["start_time"])) / 1000,
                          "end": (int(word["end_ms"]) - int(row["start_time"])) / 1000}
                         for word in row["segments"]
                     ]} if word_data else {})} for index, row in enumerate(rows)],
        "timing_source": timing_source,
        "timing_note": timing_note,
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
        if surah not in reciter.get("available_surah_numbers", range(1, 115)):
            return jsonify(error="This recording has no verified audio for the selected Surah."), 404
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
        preview_only = str(data.get("preview_only", "false")).strip().lower() in {"true", "1", "yes", "on"}
        ratio = data.get("aspect_ratio", "9:16")
        if ratio not in SIZES:
            return jsonify(error="Aspect ratio must be 9:16, 16:9, or 1:1."), 400
        resolution = str(data.get("resolution", "1080p")).lower()
        try:
            final_output_size = output_dimensions(ratio, resolution, data.get("custom_width"), data.get("custom_height"))
            fps = int(data.get("fps", 30))
        except (TypeError, ValueError) as exc:
            return jsonify(error=str(exc)), 400
        if fps not in {24, 25, 30, 60}:
            return jsonify(error="Frame rate must be 24, 25, 30, or 60 FPS."), 400
        output_size = _preview_dimensions(final_output_size) if preview_only else final_output_size
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
        translation_edition = str(data.get("translation_edition", "")).strip()
        translation_requested = data.get("show_translation", False)
        if not isinstance(translation_requested, bool):
            translation_requested = str(translation_requested).lower() in {"true", "1", "yes", "on"}
        if translation_requested and translation_edition:
            try:
                translation_payload = get_translation_range(
                    surah, ayah_start, ayah_end,
                    Path(current_app.config["OUTPUT_FOLDER"]), translation_edition,
                )
            except TranslationRequestError as exc:
                return jsonify(error=str(exc)), 400
            except TranslationSourceUnavailable as exc:
                return jsonify(error=str(exc)), 503
            except TranslationSourceError as exc:
                return jsonify(error=str(exc)), 502
            translation_lines = [row["text"] for row in translation_payload["ayahs"]]
        else:
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
        if viewer_options["show_translation"] and not show_quran_text:
            return jsonify(error="English translation is shown below Quran text. Enable Show Quran text first."), 400
        transition = data.get("transition", "crossfade")
        if transition not in {"crossfade", "cut"}:
            transition = "crossfade"
        raw_caption_style = data.get("caption_style", template["caption_style"])
        caption_style = CAPTION_STYLES.get(raw_caption_style, raw_caption_style)
        caption_color = data.get("caption_color", template["caption_color"])
        try:
            caption_color = _validate_editor_color(caption_color, "Quran text color", allow_palette=True)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
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
            caption_x, caption_y, caption_position = _caption_position_coordinates(
                data, template,
                has_translation=bool(viewer_options["show_translation"] and any(line.strip() for line in translation_lines)),
            )
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

        default_show_surah = template.get("show_surah_title", False) if "template_id" in data else False
        default_show_ayah = template.get("show_ayah_number", False) if "template_id" in data else False
        show_surah = data.get("show_surah_title", default_show_surah)
        if isinstance(show_surah, str):
            show_surah = show_surah.lower() in ("true", "1", "yes", "on")
        show_ayah_number = data.get("show_ayah_number", default_show_ayah)
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
        background_overlay_color = data.get("background_overlay_color", "#000000")
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
        output_root = Path(app.config["OUTPUT_FOLDER"])
        output_root.mkdir(parents=True, exist_ok=True)
        preview_id = None
        preview_metadata_path = None
        preview_expires_epoch = None
        if preview_only:
            preview_dir = output_root / "previews"
            cleanup_expired_previews(preview_dir)
            preview_id = new_preview_id()
            preview_paths_for_job = preview_paths(output_root, preview_id)
            output_dir, output_path, preview_metadata_path = preview_paths_for_job
            retention_seconds = max(60, int(app.config.get(
                "PREVIEW_RETENTION_SECONDS", PREVIEW_RETENTION_SECONDS
            )))
            preview_expires_epoch = int(time.time()) + retention_seconds
            download_url = url_for("main.preview_video", preview_id=preview_id)
            preview_page_url = url_for("main.preview_result", preview_id=preview_id)
        else:
            output_dir = output_root
            output_path = output_dir / f"{job_id}.mp4"
            download_url = url_for("main.download", filename=output_path.name)
            preview_page_url = None
        partial_path = output_dir / f".{output_path.stem}.partial.mp4"
        # Build this while the request context is available. The render worker
        # runs on a separate thread with only an application context, where
        # Flask cannot infer the host needed by url_for().
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
                    caption_x=caption_x, caption_y=caption_y,
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
                if preview_only:
                    created_epoch = int(time.time())
                    result.update({
                        "preview_only": True,
                        "preview_id": preview_id,
                        "preview_url": preview_page_url,
                        "preview_expires_at": utc_timestamp(preview_expires_epoch),
                        "preview_dimensions": {"width": output_size[0], "height": output_size[1]},
                        "final_dimensions": {"width": final_output_size[0], "height": final_output_size[1]},
                    })
                    preview_settings = {
                        "aspect_ratio": ratio,
                        "requested_resolution": resolution,
                        "final_dimensions": list(final_output_size),
                        "preview_dimensions": list(output_size),
                        "fps": fps,
                        "quality": quality,
                        "encoder": encoder,
                        "crf": crf,
                        "audio_bitrate": audio_bitrate,
                        "audio_sample_rate": audio_fps,
                        "selected_audio": {
                            "reciter_id": str(data.get("reciter_id", "mishary_alafasy")),
                            "reciter_name": reciter["name"],
                            "surah_number": surah,
                            "surah_name": SURAHS_BY_NUMBER[surah]["english_name"],
                            "ayah_start": ayah_start,
                            "ayah_end": ayah_end,
                            "audio_start_seconds": float(track.start),
                            "audio_end_seconds": float(track.end),
                            "timing_source": result.get("timing_source"),
                        },
                        "ayah_text": ayahs,
                        "translation_lines": translation_lines,
                        "translation_edition": translation_edition,
                        "scene_overrides": raw_scenes or [],
                        "render_settings": result,
                        "background_assets": {
                            "theme": theme,
                            "fit": background_fit,
                            "video_template": background_video_template or None,
                            "sequence_template": background_sequence_template or None,
                            "uploaded_files": [path.name for path in background_paths],
                            "clips": [{
                                "asset": Path(spec["path"]).name,
                                "start": spec["start"], "end": spec["end"],
                                "duration": spec["duration"], "speed": spec["speed"],
                                "transition": spec["transition"],
                                "transition_duration": spec["transition_duration"],
                            } for spec in background_clip_specs],
                        },
                        "caption_settings": {
                            "font_id": font_id, "font_path": str(font_path),
                            "caption_style": caption_style, "caption_color": caption_color,
                            "caption_position": caption_position,
                            "caption_x": caption_x, "caption_y": caption_y,
                            "wrap_width": wrap_width, "max_lines": max_lines,
                            "custom_options": custom_opts,
                            "label_options": label_options,
                            "viewer_layers": viewer_options,
                        },
                        "background_motion": {
                            "speed": background_speed, "loop": background_loop,
                            "animation_enabled": animation_enabled,
                            "animation_preset": animation_preset,
                            "animation_intensity": animation_intensity,
                            "animation_duration": animation_duration,
                            "animation_speed": animation_speed,
                            "animation_start": animation_start,
                            "atmosphere_enabled": atmosphere_enabled,
                            "atmosphere_intensity": atmosphere_intensity,
                            "atmosphere_duration": atmosphere_duration,
                            "atmosphere_speed": atmosphere_speed,
                            "atmosphere_start": atmosphere_start,
                            "brightness": background_brightness,
                            "contrast": background_contrast,
                            "saturation": background_saturation,
                            "overlay_color": background_overlay_color,
                            "overlay_opacity": background_overlay_opacity,
                        },
                        "created_at": utc_timestamp(created_epoch),
                    }
                    preview_record = {
                        "version": 1,
                        "id": preview_id,
                        "created_at": utc_timestamp(created_epoch),
                        "expires_at": preview_expires_epoch,
                        "settings": preview_settings,
                    }
                partial_path.replace(output_path)
                if preview_only:
                    write_preview_metadata(preview_metadata_path, preview_record)
                return result
            except Exception:
                app.logger.exception("Video render job %s failed", job_id)
                if preview_only:
                    output_path.unlink(missing_ok=True)
                    preview_metadata_path.unlink(missing_ok=True)
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
