"""Local Uthmani Arabic Quran text and complete chapter metadata."""
import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[1] / "static" / "data"
with (_DATA_DIR / "surahs.json").open(encoding="utf-8") as stream:
    SURAHS = json.load(stream)
with (_DATA_DIR / "quran_uthmani.json").open(encoding="utf-8") as stream:
    _QURAN = json.load(stream)

SURAHS_BY_NUMBER = {chapter["number"]: chapter for chapter in SURAHS}
AYAH_TEXT_BY_SURAH = {chapter["number"]: chapter["ayahs"] for chapter in _QURAN}


def get_ayahs(surah_number: int, ayah_start: int, ayah_end: int) -> list[str]:
    """Return a validated inclusive range of local Uthmani Arabic ayah text."""
    chapter = SURAHS_BY_NUMBER.get(surah_number)
    if chapter is None:
        raise ValueError("Surah number must be between 1 and 114.")
    if ayah_start < 1 or ayah_end < ayah_start or ayah_end > chapter["ayah_count"]:
        raise ValueError(f"Ayah range must be between 1 and {chapter['ayah_count']} for {chapter['english_name']}.")
    return AYAH_TEXT_BY_SURAH[surah_number][ayah_start - 1:ayah_end]
