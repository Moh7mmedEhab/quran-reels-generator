"""Resolve timed chapter recitations and download the selected audio range."""
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import shutil
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .job_errors import JobCancelled

TIMING_API = "https://mp3quran.net/api/v3/ayat_timing"
MAX_AUDIO_BYTES = 200 * 1024 * 1024


class AudioSourceError(RuntimeError):
    """The selected online recitation could not be fetched or timed."""


@dataclass(frozen=True)
class AudioTrack:
    path: Path
    url: str
    start: float
    end: float
    ayah_durations: list[float]


@lru_cache(maxsize=512)
def _get_surah_timings(surah_number: int, read_id: int) -> tuple[dict, ...]:
    url = f"{TIMING_API}?surah={surah_number}&read={read_id}"
    request = Request(url, headers={"User-Agent": "QuranReelsGenerator/1.0"})
    try:
        with urlopen(request, timeout=25) as response:
            rows = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AudioSourceError("Could not retrieve verse timing for this reciter. Try again or upload an audio file.") from exc
    if not isinstance(rows, list) or not rows:
        raise AudioSourceError("Timing data is unavailable for this reciter and surah.")
    return tuple(row for row in rows if row.get("ayah") is not None and row.get("start_time") is not None and row.get("end_time") is not None)


def get_audio_url(reciter: dict, surah_number: int) -> str:
    return f"{reciter['audio_base_url']}{surah_number:03d}.mp3"


def get_recitation_timings(reciter: dict, surah_number: int, ayah_start: int, ayah_end: int) -> list[dict]:
    """Return millisecond timings for an inclusive ayah range."""
    rows = _get_surah_timings(surah_number, reciter["read_id"])
    rows_by_ayah = {int(row["ayah"]): row for row in rows}
    selected = [rows_by_ayah.get(number) for number in range(ayah_start, ayah_end + 1)]
    if any(row is None for row in selected):
        raise AudioSourceError("Timing data does not cover the complete ayah range for this reciter.")
    if any(int(row["end_time"]) <= int(row["start_time"]) for row in selected):
        raise AudioSourceError("The recitation service returned invalid verse timings.")
    return selected


def download_recitation(reciter: dict, surah_number: int, ayah_start: int, ayah_end: int,
                        destination_dir: Path, *, cancel_event=None, on_progress=None) -> AudioTrack:
    """Download the chapter file and return its exact selected ayah time span."""
    if cancel_event is not None and cancel_event.is_set():
        raise JobCancelled()
    selected = get_recitation_timings(reciter, surah_number, ayah_start, ayah_end)
    if cancel_event is not None and cancel_event.is_set():
        raise JobCancelled()
    start_ms = int(selected[0]["start_time"])
    end_ms = int(selected[-1]["end_time"])
    if end_ms <= start_ms:
        raise AudioSourceError("The recitation service returned an invalid ayah time range.")

    # Assign inter-ayah pauses to the ayah before them so display durations sum to the audio span.
    starts = [int(row["start_time"]) for row in selected]
    durations = [
        ((starts[index + 1] if index + 1 < len(starts) else end_ms) - starts[index]) / 1000
        for index in range(len(starts))
    ]
    if any(duration <= 0 for duration in durations):
        raise AudioSourceError("The recitation service returned invalid verse timings.")

    audio_url = get_audio_url(reciter, surah_number)
    destination_dir.mkdir(parents=True, exist_ok=True)
    audio_path = destination_dir / f"qari-{reciter['id']}-{surah_number:03d}-{uuid4().hex}.mp3"
    request = Request(audio_url, headers={"User-Agent": "QuranReelsGenerator/1.0"})
    total = 0
    try:
        with urlopen(request, timeout=45) as response, audio_path.open("wb") as output:
            content_length = response.headers.get("Content-Length")
            try:
                expected = int(content_length) if content_length else None
            except (TypeError, ValueError):
                expected = None
            if on_progress:
                on_progress(0, expected)
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    raise JobCancelled()
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_AUDIO_BYTES:
                    raise AudioSourceError("This chapter audio is too large to process in one render.")
                output.write(chunk)
                if on_progress:
                    on_progress(total, expected)
    except JobCancelled:
        audio_path.unlink(missing_ok=True)
        raise
    except AudioSourceError:
        audio_path.unlink(missing_ok=True)
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        audio_path.unlink(missing_ok=True)
        raise AudioSourceError("Could not download the selected recitation. Check your connection or upload an audio file.") from exc
    if total == 0:
        audio_path.unlink(missing_ok=True)
        raise AudioSourceError("The recitation service returned an empty audio file.")

    return AudioTrack(audio_path, audio_url, start_ms / 1000, end_ms / 1000, durations)
