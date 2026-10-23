"""Optional Quran Foundation chapter-audio word timestamps.

This integration is deliberately opt-in: chapter-reciter IDs are supplied by
the deployment and OAuth credentials stay on the server. If setup or word
segments are incomplete, callers use ayah-boundary timing and keep each full
ayah visible instead of guessing phrase durations.
"""
from __future__ import annotations

import json
import os
import threading
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .quran_words import split_quran_words

TOKEN_URL = "https://oauth2.quran.foundation/oauth2/token"
API_BASE = "https://apis.quran.foundation/content/api/v4"
_TOKEN_CACHE = {}
_TOKEN_LOCK = threading.Lock()
_ARABIC_MATCH_MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ؤ": "و", "ئ": "ي", "ى": "ي",
})


def normalize_arabic_word(text: str) -> str:
    """Normalize only for alignment matching; never modify displayed Quran text."""
    normalized = unicodedata.normalize("NFKC", str(text or "")).translate(_ARABIC_MATCH_MAP)
    return "".join(char for char in normalized
                   if char != "ـ" and not unicodedata.category(char).startswith(("M", "P", "C"))
                   and char not in {"ء", "۞", "۩"})


def _credentials():
    return (os.environ.get("QURAN_FOUNDATION_CLIENT_ID", "").strip(),
            os.environ.get("QURAN_FOUNDATION_CLIENT_SECRET", "").strip())


def _reciter_map():
    raw = os.environ.get("QURAN_REELS_QF_RECITER_MAP", "")
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(value, dict):
        return {}
    result = {}
    for key, chapter_reciter_id in value.items():
        try:
            parsed = int(chapter_reciter_id)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            result[str(key)] = parsed
    return result


def _access_token(client_id: str, client_secret: str) -> str:
    key = (client_id, client_secret)
    with _TOKEN_LOCK:
        cached = _TOKEN_CACHE.get(key)
        if cached and cached[1] > time.monotonic():
            return cached[0]
    body = urlencode({"grant_type": "client_credentials", "scope": "content"}).encode()
    request = Request(TOKEN_URL, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    })
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("Quran Foundation authentication failed.") from exc
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if not token:
        raise RuntimeError("Quran Foundation did not return an access token.")
    expires_in = payload.get("expires_in", 300)
    try:
        lifetime = max(30, int(expires_in) - 30)
    except (TypeError, ValueError):
        lifetime = 300
    with _TOKEN_LOCK:
        _TOKEN_CACHE[key] = (str(token), time.monotonic() + lifetime)
    return str(token)


def _chapter_payload(chapter_reciter_id: int, surah: int, client_id: str, client_secret: str):
    token = _access_token(client_id, client_secret)
    url = f"{API_BASE}/chapter_recitations/{chapter_reciter_id}/{surah}?segments=true"
    request = Request(url, headers={
        "Accept": "application/json",
        "x-auth-token": token,
        "x-client-id": client_id,
    })
    try:
        with urlopen(request, timeout=25) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("Quran Foundation chapter word timings are unavailable.") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Quran Foundation returned an invalid chapter timing response.")
    return payload


def _chapter_verse_words(chapter: int, start: int, end: int, client_id: str, client_secret: str):
    token = _access_token(client_id, client_secret)
    query = urlencode({
        "from": f"{chapter}:{start}", "to": f"{chapter}:{end}", "words": "true",
        "fields": "verse_key,text_uthmani", "word_fields": "text_uthmani,char_type_name",
    })
    request = Request(f"{API_BASE}/verses/by_range?{query}", headers={
        "Accept": "application/json", "x-auth-token": token, "x-client-id": client_id,
    })
    try:
        with urlopen(request, timeout=25) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("Quran Foundation canonical word text is unavailable.") from exc
    rows = payload.get("verses") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError("Quran Foundation did not return canonical verse words.")
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = str(row.get("verse_key", ""))
        try:
            verse_number = int(key.split(":")[-1])
        except ValueError:
            continue
        words = row.get("words")
        if not isinstance(words, list):
            raise RuntimeError("Quran Foundation returned a verse without word text.")
        parsed = []
        for word in words:
            if not isinstance(word, dict):
                continue
            if word.get("char_type_name") not in (None, "word"):
                continue
            text = str(word.get("text_uthmani") or "")
            if normalize_arabic_word(text):
                parsed.append(text)
        result[verse_number] = parsed
    if any(number not in result for number in range(start, end + 1)):
        raise RuntimeError("Quran Foundation canonical word text does not cover the selected range.")
    return result


def _extract_audio_url(payload):
    direct = payload.get("audio_url") or payload.get("url")
    if direct:
        return str(direct)
    audio_file = payload.get("audio_file")
    if isinstance(audio_file, dict):
        direct = audio_file.get("audio_url") or audio_file.get("url")
        if direct:
            return str(direct)
    files = payload.get("audio_files")
    if isinstance(files, list) and files and isinstance(files[0], dict):
        return str(files[0].get("audio_url") or files[0].get("url") or "")
    return ""


def _parse_segments(raw):
    if not isinstance(raw, list) or not raw:
        raise RuntimeError("Quran Foundation did not return complete word segments.")
    segments = []
    for item in raw:
        if isinstance(item, dict):
            index = item.get("word_index", item.get("index"))
            start = item.get("start_ms", item.get("timestamp_from"))
            end = item.get("end_ms", item.get("timestamp_to"))
        elif isinstance(item, (list, tuple)) and len(item) >= 3:
            index, start, end = item[:3]
        else:
            raise RuntimeError("Quran Foundation returned a malformed word segment.")
        try:
            index, start, end = int(index), int(start), int(end)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Quran Foundation returned non-numeric word timestamps.") from exc
        if index < 0 or start < 0 or end <= start:
            raise RuntimeError("Quran Foundation returned invalid word timestamps.")
        segments.append({"index": index, "start_ms": start, "end_ms": end})
    segments.sort(key=lambda row: (row["start_ms"], row["index"]))
    indices = [row["index"] for row in segments]
    expected_zero = list(range(len(indices)))
    expected_one = list(range(1, len(indices) + 1))
    if indices not in (expected_zero, expected_one):
        raise RuntimeError("Quran Foundation word indices are incomplete or duplicated.")
    previous_end = -1
    for row in segments:
        if row["start_ms"] < previous_end:
            raise RuntimeError("Quran Foundation word timestamps overlap in the recitation.")
        row["index"] = row["index"] - (1 if indices == expected_one else 0)
        previous_end = row["end_ms"]
    return segments


def get_chapter_word_timing(reciter_id: str, surah: int, ayah_start: int, ayah_end: int,
                            expected_ayahs: list[str]):
    """Return validated selected-range timing data, or None when not configured.

    A returned object always points to the same chapter audio from which its
    timestamps were obtained. Network/API failures raise RuntimeError so the
    audio source can explicitly record an ayah-only fallback reason.
    """
    client_id, client_secret = _credentials()
    chapter_reciter_id = _reciter_map().get(str(reciter_id))
    if not client_id or not client_secret or not chapter_reciter_id:
        return None
    payload = _chapter_payload(chapter_reciter_id, int(surah), client_id, client_secret)
    canonical_words = _chapter_verse_words(
        int(surah), int(ayah_start), int(ayah_end), client_id, client_secret,
    )
    audio_url = _extract_audio_url(payload)
    audio_file = payload.get("audio_file") if isinstance(payload.get("audio_file"), dict) else {}
    rows = payload.get("timestamps") or payload.get("verses") or audio_file.get("timestamps")
    if not audio_url or not isinstance(rows, list):
        raise RuntimeError("Quran Foundation response is missing its audio URL or ayah timestamps.")
    by_ayah = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = str(row.get("verse_key") or row.get("verse") or row.get("ayah") or "")
        try:
            number = int(key.split(":")[-1])
            start = int(row.get("timestamp_from", row.get("start_time")))
            end = int(row.get("timestamp_to", row.get("end_time")))
        except (TypeError, ValueError):
            continue
        if end <= start:
            continue
        segments = _parse_segments(row.get("segments"))
        if ayah_start <= number <= ayah_end:
            expected_count = len(split_quran_words(expected_ayahs[number - ayah_start]))
            if len(segments) != expected_count:
                raise RuntimeError(f"Word count does not match local Quran text for ayah {number}.")
            local_tokens = split_quran_words(expected_ayahs[number - ayah_start])
            if [normalize_arabic_word(word) for word in local_tokens] != [
                    normalize_arabic_word(word) for word in canonical_words[number]]:
                raise RuntimeError(
                    f"Canonical Quran word text differs from local orthography for ayah {number}."
                )
        by_ayah[number] = {"ayah": number, "start_time": start, "end_time": end,
                           "segments": segments}
    selected = [by_ayah.get(number) for number in range(ayah_start, ayah_end + 1)]
    if any(row is None for row in selected):
        raise RuntimeError("Word timing data does not cover the selected ayah range.")
    return {"audio_url": audio_url, "ayahs": selected}
