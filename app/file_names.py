"""Safe, title-based download filenames."""
from pathlib import Path
import re
import unicodedata

INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]+')
WHITESPACE = re.compile(r"\s+")
MAX_STEM_LENGTH = 120
MAX_STEM_UTF8_BYTES = 180


def _truncate_utf8(value: str, maximum: int) -> str:
    parts = []
    used = 0
    for char in value:
        size = len(char.encode("utf-8"))
        if used + size > maximum:
            break
        parts.append(char)
        used += size
    return "".join(parts)


def sanitize_video_filename(title: str, fallback: str = "Quran Reel") -> str:
    """Return a cross-platform MP4 name while preserving Arabic and English."""
    value = unicodedata.normalize("NFC", str(title or "")).strip()
    value = INVALID_FILENAME_CHARS.sub(" ", value)
    value = WHITESPACE.sub(" ", value).strip(" .-_")
    value = _truncate_utf8(value[:MAX_STEM_LENGTH], MAX_STEM_UTF8_BYTES).rstrip(" .")
    if not value:
        value = unicodedata.normalize("NFC", str(fallback or "Quran Reel"))
        value = INVALID_FILENAME_CHARS.sub(" ", value)
        value = WHITESPACE.sub(" ", value).strip(" .-_")
        value = _truncate_utf8(value[:MAX_STEM_LENGTH], MAX_STEM_UTF8_BYTES).rstrip(" .-_")
    if value.upper() in {"CON", "PRN", "AUX", "NUL"} or re.fullmatch(r"COM[1-9]|LPT[1-9]", value.upper()):
        value = f"_{value}"
    return f"{value or 'Quran Reel'}.mp4"


def unique_download_filename(title: str, fallback: str, output_folder, source_filename: str) -> str:
    """Keep duplicate title downloads distinct when a prior file exists."""
    filename = sanitize_video_filename(title, fallback)
    folder = Path(output_folder)
    stem, suffix = Path(filename).stem, ".mp4"
    source = Path(source_filename).name
    candidate = filename
    index = 2
    while candidate != source and (folder / candidate).exists():
        marker = f" ({index})"
        candidate = sanitize_video_filename(f"{stem[:MAX_STEM_LENGTH - len(marker)].rstrip(' .')}{marker}", fallback)
        index += 1
    return candidate
