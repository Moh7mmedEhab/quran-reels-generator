"""Web routes for Quran text, reciters, and video generation."""
from pathlib import Path
import tempfile
from io import BytesIO
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, render_template, request, send_file, send_from_directory, url_for
from PIL import Image
from werkzeug.utils import secure_filename

from .audio_sources import AudioSourceError, download_recitation, get_audio_url, get_recitation_timings
from .quraa_data import RECITERS, RECITERS_BY_ID
from .quran_data import SURAHS, SURAHS_BY_NUMBER, get_ayahs
from .video_engine import (CAPTION_COLORS, SIZES, THEMES, _background,
                           caption_render_options, render_reel)
from .text_renderer import render_arabic_text

bp = Blueprint("main", __name__)
CAPTION_STYLES = {
    "Dynamic Karaoke (Glow)": "karaoke",
    "Minimalist Subtitle Fade": "minimal",
    "Classic Calligraphic": "classic",
    "Arabic Only (No Translation)": "arabic_only",
    "karaoke": "karaoke", "minimal": "minimal", "classic": "classic", "arabic_only": "arabic_only",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


@bp.get("/")
def studio():
    initial_ayah = get_ayahs(55, 13, 13)[0]
    return render_template("index.html", reciters=RECITERS, surahs=SURAHS, initial_ayah=initial_ayah,
                           themes=THEMES, caption_colors=CAPTION_COLORS)


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
    return jsonify({"backgrounds": [{"id": key, "name": value["name"]} for key, value in THEMES.items()]})


@bp.get("/api/backgrounds/<theme>/preview")
def background_preview(theme):
    if theme not in THEMES:
        return jsonify(error="Choose one of the available wallpapers."), 404
    ratio = request.args.get("ratio", "9:16")
    if ratio not in SIZES:
        return jsonify(error="Aspect ratio must be 9:16, 16:9, or 1:1."), 400
    width, height = SIZES[ratio]
    scale = min(960 / max(width, height), 1)
    wallpaper = _background(None, (int(width * scale), int(height * scale)), theme)
    wallpaper = Image.blend(wallpaper, Image.new("RGB", wallpaper.size, (0, 0, 0)), 0.16)
    buffer = BytesIO()
    wallpaper.save(buffer, format="JPEG", quality=88, optimize=True)
    buffer.seek(0)
    return send_file(buffer, mimetype="image/jpeg", max_age=86400)


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
    style = CAPTION_STYLES.get(payload.get("caption_style", "classic"))
    if style is None:
        return jsonify(error="Choose a supported caption style."), 400
    color = payload.get("caption_color", "white")
    wrap_width = payload.get("wrap_width", 85)
    try:
        wrap_width = int(wrap_width)
    except (TypeError, ValueError):
        return jsonify(error="Text wrap width must be 65, 75, 85, or 95 percent."), 400
    if wrap_width not in {65, 75, 85, 95}:
        return jsonify(error="Text wrap width must be 65, 75, 85, or 95 percent."), 400
    width, height = SIZES[ratio]
    try:
        color_rgba, options = caption_render_options(style, color)
        image = render_arabic_text(
            text, font_path=current_app.config.get("ARABIC_FONT"),
            font_size=max(50, int(width * .07)),
            max_width=int(width * wrap_width / 100),
            max_height=int(height * .44), color=color_rgba, **options,
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
        get_ayahs(surah, start, end)
        rows = get_recitation_timings(reciter, surah, start, end)
    except (TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    except AudioSourceError as exc:
        return jsonify(error=str(exc)), 502
    return jsonify({
        "audio_url": get_audio_url(reciter, surah),
        "timings": [{"ayah": int(row["ayah"]), "start": int(row["start_time"]) / 1000,
                     "end": int(row["end_time"]) / 1000} for row in rows],
    })


@bp.post("/api/generate")
def generate():
    data = request.form if request.form else (request.get_json(silent=True) or {})
    temporary_files = []
    try:
        ratio = data.get("aspect_ratio", "9:16")
        if ratio not in SIZES:
            return jsonify(error="Aspect ratio must be 9:16, 16:9, or 1:1."), 400

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

        entered_text = str(data.get("ayah_text", "")).strip()
        ayahs = [line.strip() for line in entered_text.splitlines() if line.strip()] if entered_text else official_ayahs
        if len(ayahs) != len(official_ayahs):
            return jsonify(error="Enter one ayah text line for each ayah in the selected range."), 400

        transition = data.get("transition", "crossfade")
        if transition not in {"crossfade", "cut"}:
            transition = "crossfade"
        caption_style = CAPTION_STYLES.get(data.get("caption_style", "classic"))
        if caption_style is None:
            return jsonify(error="Choose a supported caption style."), 400
        caption_color = data.get("caption_color", "white")
        if caption_color not in CAPTION_COLORS:
            return jsonify(error="Choose a supported caption color."), 400
        try:
            wrap_width = int(data.get("wrap_width", 85))
        except (TypeError, ValueError):
            return jsonify(error="Text wrap width must be 65, 75, 85, or 95 percent."), 400
        if wrap_width not in {65, 75, 85, 95}:
            return jsonify(error="Text wrap width must be 65, 75, 85, or 95 percent."), 400
        theme = data.get("theme", "misty_forest")
        if theme not in THEMES:
            return jsonify(error="Choose one of the available background presets."), 400
        try:
            speed = float(data.get("speed", 1.0))
        except (TypeError, ValueError):
            return jsonify(error="Speed must be 0.9, 1.0, or 1.15."), 400
        if speed not in {0.9, 1.0, 1.15}:
            return jsonify(error="Speed must be 0.9, 1.0, or 1.15."), 400

        background_file = request.files.get("background")
        background_name = secure_filename(background_file.filename) if background_file and background_file.filename else ""
        if background_name and Path(background_name).suffix.lower() not in IMAGE_EXTENSIONS:
            return jsonify(error="Use a PNG, JPG, or WEBP still image background."), 400

        job_id = uuid4().hex
        output_dir = Path(current_app.config["OUTPUT_FOLDER"])
        output_dir.mkdir(parents=True, exist_ok=True)
        upload_dir = Path(tempfile.gettempdir()) / "quran-reels-uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        background_path = None
        track = download_recitation(reciter, surah, ayah_start, ayah_end, upload_dir)
        audio_path = track.path
        audio_start, audio_end = track.start, track.end
        ayah_durations = track.ayah_durations
        temporary_files.append(track.path)
        if background_name:
            background_path = upload_dir / f"{job_id}_{background_name}"
            background_file.save(background_path)
            temporary_files.append(background_path)

        output_path = output_dir / f"{job_id}.mp4"
        result = render_reel(
            ayahs=ayahs, output_path=output_path, aspect_ratio=ratio,
            audio_path=audio_path, audio_start=audio_start, audio_end=audio_end,
            ayah_durations=ayah_durations, background_path=background_path,
            theme=theme, transition=transition, caption_style=caption_style, speed=speed,
            caption_color=caption_color, wrap_width=wrap_width,
            font_path=current_app.config.get("ARABIC_FONT"),
        )
        result.pop("path", None)
        result.update({
            "filename": output_path.name,
            "download_url": url_for("main.download", filename=output_path.name),
            "reciter": reciter["name"],
            "surah": SURAHS_BY_NUMBER[surah]["english_name"],
            "ayah_start": ayah_start,
            "ayah_end": ayah_end,
            "theme": theme,
            "caption_color": caption_color,
            "wrap_width": wrap_width,
        })
        return jsonify(result), 201
    except AudioSourceError as exc:
        return jsonify(error=str(exc)), 502
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        current_app.logger.exception("Video render failed")
        return jsonify(error=f"Video render failed: {exc}"), 500
    finally:
        for temporary in temporary_files:
            temporary.unlink(missing_ok=True)


@bp.get("/outputs/<path:filename>")
def download(filename):
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename, as_attachment=True)
