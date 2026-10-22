"""Pinned, source-paired ayah timings from Qur'anic Universal Audio v3.2.0.

Only verse boundaries are used here. Its word tokens use a different mushaf
tokenization from this app's displayed text, so word timings are not mapped
unless a separately configured Quran Foundation source validates them.
"""
from __future__ import annotations

import gzip
import json
from functools import lru_cache
from pathlib import Path

from .quran_data import SURAHS_BY_NUMBER

QUD_VERSION = "v3.2.0"
QUD_SOURCE_URL = "https://github.com/QUD-Technologies/quranic-universal-audio/releases/tag/v3.2.0"
_DATA_FOLDER = Path(__file__).resolve().parents[1] / "static" / "data" / "recitations" / "qud-v3.2.0"
_SLUGS = {
    "islam_sobhi": "islam_sobhi_mp3quran",
    "minshawi": "mohammed_siddiq_al_minshawi_mp3quran",
    "minshawi_mujawwad": "mohammed_siddiq_al_minshawi_mujawwad_mp3quran",
}


class QudTimingError(RuntimeError):
    """The bundled QUD timing set is absent, malformed, or incomplete."""


@lru_cache(maxsize=3)
def _catalog(slug: str) -> dict:
    if slug not in _SLUGS.values():
        raise QudTimingError("No verified QUD timing set is configured for this recording.")
    path = _DATA_FOLDER / f"{slug}-catalog.json"
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QudTimingError("The bundled QUD recording catalog is unavailable.") from exc
    if (not isinstance(catalog, dict) or catalog.get("slug") != slug
            or catalog.get("audio_category") != "by_surah"
            or catalog.get("channel") != "mp3quran"):
        raise QudTimingError("The QUD catalog does not match the selected recording.")
    return catalog


@lru_cache(maxsize=3)
def _canonical_verse_rows(slug: str) -> dict[tuple[int, int], dict]:
    if slug not in _SLUGS.values():
        raise QudTimingError("No verified QUD timing set is configured for this recording.")
    path = _DATA_FOLDER / f"{slug}-verse_timestamps.json.gz"
    try:
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, json.JSONDecodeError, EOFError) as exc:
        raise QudTimingError("The bundled QUD ayah timings are unavailable.") from exc
    metadata = payload.get("_meta") if isinstance(payload, dict) else None
    raw_rows = payload.get("rows") if isinstance(payload, dict) else None
    if (not isinstance(metadata, dict) or metadata.get("slug") != slug
            or metadata.get("tier") != "verse" or metadata.get("units") != "ms"
            or not isinstance(raw_rows, list)):
        raise QudTimingError("The bundled QUD ayah timings do not match this recitation.")
    indexed = {}
    for raw in raw_rows:
        if not isinstance(raw, list) or len(raw) < 5:
            raise QudTimingError("The bundled QUD ayah timing data is malformed.")
        try:
            chapter, verse = (int(part) for part in str(raw[0]).split(":"))
            start, end = int(raw[1]), int(raw[2])
        except (TypeError, ValueError) as exc:
            raise QudTimingError("The bundled QUD ayah timing data has an invalid row.") from exc
        if chapter not in SURAHS_BY_NUMBER or not 1 <= verse <= int(SURAHS_BY_NUMBER[chapter]["ayah_count"]):
            raise QudTimingError("The bundled QUD ayah timing data has an invalid ayah reference.")
        if not bool(raw[3]):
            continue
        if start < 0 or end <= start or (chapter, verse) in indexed:
            raise QudTimingError("The bundled QUD canonical ayah timing is invalid or duplicated.")
        indexed[(chapter, verse)] = {"ayah": verse, "start_time": start, "end_time": end}
    return indexed


def get_chapter_audio_url(slug: str, surah: int) -> str:
    catalog = _catalog(slug)
    urls = catalog.get("audio", {}).get("chapter_urls", {})
    url = urls.get(str(int(surah))) if isinstance(urls, dict) else None
    if not isinstance(url, str) or not url.startswith("https://"):
        raise QudTimingError("This recording has no verified audio for the selected Surah.")
    from urllib.parse import urlsplit
    parsed = urlsplit(url)
    if parsed.hostname not in {"server10.mp3quran.net", "server14.mp3quran.net"} or not parsed.path.endswith(".mp3"):
        raise QudTimingError("The QUD catalog contains an unexpected audio source URL.")
    return url


def available_surahs(slug: str) -> tuple[int, ...]:
    catalog = _catalog(slug)
    urls = catalog.get("audio", {}).get("chapter_urls", {})
    try:
        return tuple(sorted(int(key) for key in urls))
    except (TypeError, ValueError) as exc:
        raise QudTimingError("The QUD catalog contains invalid Surah coverage.") from exc


def get_recitation_timings(slug: str, surah: int, ayah_start: int, ayah_end: int) -> list[dict]:
    """Return canonical source-file ayah boundaries for a complete range."""
    if surah not in available_surahs(slug):
        raise QudTimingError("This reciter has no verified audio for the selected Surah.")
    indexed = _canonical_verse_rows(slug)
    selected = [indexed.get((surah, ayah)) for ayah in range(ayah_start, ayah_end + 1)]
    if any(row is None for row in selected):
        raise QudTimingError("QUD timing data does not cover the complete selected ayah range.")
    if any(selected[index]["end_time"] > selected[index + 1]["start_time"]
           for index in range(len(selected) - 1)):
        raise QudTimingError("QUD canonical ayah windows overlap and cannot be stitched safely.")
    return [dict(row) for row in selected]


def get_slug(reciter: dict) -> str | None:
    slug = reciter.get("timing_slug")
    return slug if slug in _SLUGS.values() else None
