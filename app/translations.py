"""Source-backed Quran translations with a validated local chapter cache."""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .quran_data import SURAHS_BY_NUMBER

TRANSLATION_EDITION = "en.sahih"
TRANSLATION_NAME = "Saheeh International"
TRANSLATION_SOURCE = "AlQuranCloud"
TRANSLATION_API = "https://api.alquran.cloud/v1/surah/{surah}/{edition}"
MAX_TRANSLATION_RESPONSE_BYTES = 2 * 1024 * 1024


class TranslationSourceError(RuntimeError):
    """The selected translation could not be loaded or validated."""


class TranslationRequestError(ValueError):
    """The selected edition or ayah range is not supported."""


class TranslationSourceUnavailable(TranslationSourceError):
    """The translation API could not provide a chapter for this request."""


def _chapter_cache_path(cache_dir: Path, surah: int, edition: str) -> Path:
    return Path(cache_dir) / "translations" / f"{surah:03d}-{edition}.json"


def _validated_chapter(payload, surah: int, edition: str) -> dict:
    """Accept only a complete, indexed chapter for the requested edition."""
    expected_count = int(SURAHS_BY_NUMBER[surah]["ayah_count"])
    if not isinstance(payload, dict):
        raise TranslationSourceError("The translation source returned an invalid chapter.")
    if payload.get("surah") != surah or payload.get("edition") != edition:
        raise TranslationSourceError("The cached translation does not match the selected Surah and edition.")
    rows = payload.get("ayahs")
    if not isinstance(rows, list) or len(rows) != expected_count:
        raise TranslationSourceError("The translation source did not return every ayah in this Surah.")
    indexed = {}
    for row in rows:
        if not isinstance(row, dict):
            raise TranslationSourceError("The translation source returned a malformed ayah.")
        try:
            number = int(row.get("ayah"))
        except (TypeError, ValueError) as exc:
            raise TranslationSourceError("The translation source returned an invalid ayah number.") from exc
        text = row.get("text")
        if not isinstance(text, str) or not text.strip() or len(text) > 5000 or number in indexed:
            raise TranslationSourceError("The translation source returned missing or duplicate ayah text.")
        indexed[number] = text.strip()
    if list(sorted(indexed)) != list(range(1, expected_count + 1)):
        raise TranslationSourceError("The translation source returned an incomplete or unordered Surah.")
    return {
        "surah": surah,
        "edition": edition,
        "translator": TRANSLATION_NAME,
        "source": TRANSLATION_SOURCE,
        "ayahs": [{"ayah": number, "text": indexed[number]}
                  for number in range(1, expected_count + 1)],
    }


def _read_cache(path: Path, surah: int, edition: str) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return _validated_chapter(payload, surah, edition)
    except (OSError, ValueError, json.JSONDecodeError, TranslationSourceError):
        return None


def _fetch_chapter(surah: int, edition: str) -> dict:
    url = TRANSLATION_API.format(surah=surah, edition=edition)
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "QuranReelsStudio/1.3",
    })
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read(MAX_TRANSLATION_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise TranslationSourceUnavailable(
            "English translation is unavailable and no cached copy exists. Check your connection and try again."
        ) from exc
    if not raw or len(raw) > MAX_TRANSLATION_RESPONSE_BYTES:
        raise TranslationSourceError("The translation source returned an empty or oversized chapter.")
    try:
        envelope = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TranslationSourceError("The translation source returned invalid JSON.") from exc
    data = envelope.get("data") if isinstance(envelope, dict) and envelope.get("code") == 200 else None
    metadata = data.get("edition") if isinstance(data, dict) else None
    rows = data.get("ayahs") if isinstance(data, dict) else None
    if (not isinstance(data, dict) or data.get("number") != surah
            or not isinstance(metadata, dict) or metadata.get("identifier") != edition
            or not isinstance(rows, list)):
        raise TranslationSourceError("The translation source returned a different Surah or edition.")
    converted = []
    for row in rows:
        if not isinstance(row, dict):
            raise TranslationSourceError("The translation source returned a malformed ayah.")
        converted.append({"ayah": row.get("numberInSurah"), "text": row.get("text")})
    return _validated_chapter({"surah": surah, "edition": edition, "ayahs": converted}, surah, edition)


def get_translation_range(surah: int, ayah_start: int, ayah_end: int, cache_dir: Path,
                          edition: str = TRANSLATION_EDITION) -> dict:
    """Return an exact inclusive range from a whitelisted edition.

    The complete chapter is cached atomically so repeated requests and offline
    exports use the same validated source text.
    """
    try:
        surah, ayah_start, ayah_end = int(surah), int(ayah_start), int(ayah_end)
    except (TypeError, ValueError) as exc:
        raise TranslationRequestError("Surah and ayah numbers must be whole numbers.") from exc
    chapter_info = SURAHS_BY_NUMBER.get(surah)
    if chapter_info is None:
        raise TranslationRequestError("Surah number must be between 1 and 114.")
    if edition != TRANSLATION_EDITION:
        raise TranslationRequestError("Choose the supported Saheeh International English edition.")
    if not 1 <= ayah_start <= ayah_end <= int(chapter_info["ayah_count"]):
        raise TranslationRequestError("The requested ayah range is outside this Surah.")

    cache_path = _chapter_cache_path(Path(cache_dir), surah, edition)
    chapter = _read_cache(cache_path, surah, edition)
    cached = chapter is not None
    if chapter is None:
        chapter = _fetch_chapter(surah, edition)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = cache_path.with_name(f".{cache_path.name}.{uuid4().hex}.tmp")
        try:
            temp_path.write_text(json.dumps(chapter, ensure_ascii=False), encoding="utf-8")
            os.replace(temp_path, cache_path)
        except OSError:
            temp_path.unlink(missing_ok=True)
            # A writable cache is best-effort; a verified response can still
            # be returned for this render when the output volume is read-only.
    return {
        **chapter,
        "cached": cached,
        "ayahs": [row for row in chapter["ayahs"] if ayah_start <= row["ayah"] <= ayah_end],
    }
