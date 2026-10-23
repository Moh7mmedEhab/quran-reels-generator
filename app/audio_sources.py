"""Resolve timed chapter recitations and download the selected audio range."""
from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path
import shutil
import subprocess
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .job_errors import JobCancelled
from .quran_data import SURAHS_BY_NUMBER
from .qud_timings import (QudTimingError, get_chapter_audio_url,
                          get_recitation_timings as get_qud_recitation_timings)

TIMING_API = "https://mp3quran.net/api/v3/ayat_timing"
MAX_AUDIO_BYTES = 200 * 1024 * 1024
SOURCE_CACHE_TTL_SECONDS = 24 * 60 * 60
SOURCE_CACHE_MAX_BYTES = 2 * 1024 * 1024 * 1024
_SOURCE_AUDIO_CACHE_LOCK = threading.RLock()


class AudioSourceError(RuntimeError):
    """The selected online recitation could not be fetched or timed."""


@dataclass(frozen=True)
class AudioTrack:
    path: Path
    url: str
    start: float
    end: float
    ayah_durations: list[float]
    word_timings: list[list[dict]] | None = None
    timing_source: str = "mp3quran_ayah"
    timing_note: str = "Ayah-level timing; phrase-level word timestamps are unavailable."
    persistent: bool = False


def select_audio_word_range(track: AudioTrack, ayahs: list[str], *, ayah_start: int,
                            start_word: int, end_word: int, mode: str = "automatic",
                            manual_start: float | None = None,
                            manual_end: float | None = None) -> tuple[AudioTrack, list[str], list[tuple[int, int]]]:
    """Trim a recording and Quran text to validated inclusive word boundaries.

    Word positions are one-based within the first and last selected ayah.
    Automatic partial-word trimming is enabled only for timestamps tied to
    this recording. Manual second offsets are relative to the selected
    ayah-range audio interval and are explicitly identified in track metadata.
    """
    from dataclasses import replace

    if not ayahs:
        raise AudioSourceError("Select at least one ayah before choosing word boundaries.")
    try:
        start_word = int(start_word)
        end_word = int(end_word)
        ayah_start = int(ayah_start)
    except (TypeError, ValueError) as exc:
        raise AudioSourceError("Start and end words must be whole-number positions.") from exc

    counts = [len(str(ayah).split()) for ayah in ayahs]
    if any(count < 1 for count in counts):
        raise AudioSourceError("Word-level boundaries require non-empty Quran text in every selected ayah.")
    if not 1 <= start_word <= counts[0]:
        raise AudioSourceError(f"Start word must be from 1 to {counts[0]} in ayah {ayah_start}.")
    final_ayah_number = ayah_start + len(ayahs) - 1
    if not 1 <= end_word <= counts[-1]:
        raise AudioSourceError(f"End word must be from 1 to {counts[-1]} in ayah {final_ayah_number}.")
    if len(ayahs) == 1 and end_word < start_word:
        raise AudioSourceError("The end word cannot come before the start word in the same ayah.")
    if mode not in {"automatic", "manual"}:
        raise AudioSourceError("Choose automatic verified word timing or manual audio trim.")

    word_ranges = [(1, count) for count in counts]
    word_ranges[0] = (start_word, counts[0])
    word_ranges[-1] = (word_ranges[-1][0], end_word)
    partial_start = start_word > 1
    partial_end = end_word < counts[-1]
    if not partial_start and not partial_end:
        return track, list(ayahs), word_ranges

    durations = [float(value) for value in track.ayah_durations]
    if len(durations) != len(ayahs) or any(not math.isfinite(value) or value <= 0 for value in durations):
        raise AudioSourceError("The recording has no complete ayah timeline for this word selection.")
    if (not math.isfinite(float(track.start)) or not math.isfinite(float(track.end))
            or track.start < 0 or track.end <= track.start
            or abs(sum(durations) - (float(track.end) - float(track.start))) > .1):
        raise AudioSourceError("The recording returned an inconsistent ayah audio timeline.")

    first_row = None
    final_row = None
    if track.word_timings is not None and len(track.word_timings) == len(ayahs):
        first_row = track.word_timings[0]
        final_row = track.word_timings[-1]
    automatic_source = track.timing_source == "quran_foundation_word"
    if mode == "automatic":
        if not automatic_source or track.word_timings is None or len(track.word_timings) != len(ayahs):
            raise AudioSourceError(
                "Verified word timestamps are unavailable for this recording. Choose manual audio trim and enter both boundary times."
            )
        if any(len(row) != count for row, count in zip(track.word_timings, counts)):
            raise AudioSourceError("Word timestamp counts do not match the selected Quran text.")
        for row, duration in zip(track.word_timings, durations):
            previous_end = 0.0
            for word in row:
                try:
                    word_start, word_end = float(word["start"]), float(word["end"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise AudioSourceError("The recording returned a malformed word timestamp.") from exc
                if (not math.isfinite(word_start) or not math.isfinite(word_end)
                        or word_start < previous_end or word_end <= word_start
                        or word_end > duration + .05):
                    raise AudioSourceError("The recording returned invalid or overlapping word timestamps.")
                previous_end = word_end
        if partial_start and len(first_row or []) < start_word:
            raise AudioSourceError("The recording has no verified timestamp for the selected start word.")
        if partial_end and len(final_row or []) < end_word:
            raise AudioSourceError("The recording has no verified timestamp for the selected end word.")
        start_offset = float(first_row[start_word - 1]["start"]) if partial_start else 0.0
        end_offset = float(final_row[end_word - 1]["end"]) if partial_end else durations[-1]
        if (not math.isfinite(start_offset) or not math.isfinite(end_offset)
                or start_offset < 0 or end_offset <= 0):
            raise AudioSourceError("The recording returned invalid timestamps for the selected words.")
        elapsed_before_final = sum(durations[:-1])
        new_start = float(track.start) + start_offset
        new_end = float(track.start) + elapsed_before_final + end_offset
        if new_end <= new_start or new_start < track.start or new_end > track.end + .05:
            raise AudioSourceError("The selected word timestamps fall outside the ayah audio range.")

        trimmed_durations = list(durations)
        if partial_start:
            trimmed_durations[0] -= start_offset
        if partial_end:
            if len(ayahs) == 1:
                trimmed_durations[0] = end_offset - (start_offset if partial_start else 0.0)
            else:
                trimmed_durations[-1] = end_offset
        trimmed_word_timings = []
        for index, row in enumerate(track.word_timings):
            lower = start_word - 1 if index == 0 else 0
            upper = end_word if index == len(ayahs) - 1 else len(row)
            offset = start_offset if index == 0 and partial_start else 0.0
            selected = []
            for word in row[lower:upper]:
                word_start, word_end = float(word["start"]), float(word["end"])
                selected.append({"start": max(0.0, word_start - offset),
                                 "end": word_end - offset})
            trimmed_word_timings.append(selected)
        selected_ayahs = [" ".join(str(ayah).split()[lo - 1:hi])
                          for ayah, (lo, hi) in zip(ayahs, word_ranges)]
        new_track = replace(
            track, start=new_start, end=new_end,
            ayah_durations=trimmed_durations,
            word_timings=trimmed_word_timings,
            timing_note=(track.timing_note + " Selected boundaries use validated word timestamps from this recording."),
        )
        return new_track, selected_ayahs, word_ranges

    try:
        manual_start = float(manual_start)
        manual_end = float(manual_end)
    except (TypeError, ValueError) as exc:
        raise AudioSourceError(
            "Manual audio trim needs both a start and end time in seconds from the selected range's beginning."
        ) from exc
    selected_duration = float(track.end) - float(track.start)
    if (not math.isfinite(manual_start) or not math.isfinite(manual_end)
            or manual_start < 0 or manual_end <= manual_start
            or manual_end > selected_duration + .001):
        raise AudioSourceError(
            f"Manual audio times must be within 0 and {selected_duration:.3f} seconds, with end after start."
        )
    selected_ayahs = [" ".join(str(ayah).split()[lo - 1:hi])
                      for ayah, (lo, hi) in zip(ayahs, word_ranges)]
    note = (track.timing_note + " Partial audio uses manually entered recording offsets; "
            "scene boundaries are approximate without verified word timestamps.")
    new_track = replace(
        track,
        start=float(track.start) + manual_start,
        end=float(track.start) + manual_end,
        word_timings=None,
        timing_source="manual_audio_trim",
        timing_note=note,
    )
    clipped_durations = []
    cursor = 0.0
    for duration in durations:
        segment_start, segment_end = cursor, cursor + duration
        clipped_start = max(segment_start, manual_start)
        clipped_end = min(segment_end, manual_end)
        if clipped_end > clipped_start:
            clipped_durations.append(clipped_end - clipped_start)
        cursor = segment_end
    if len(clipped_durations) != len(ayahs):
        raise AudioSourceError(
            "Manual trim times must include audio from every selected ayah. Adjust the range or select fewer ayahs."
        )
    new_track = replace(new_track, ayah_durations=clipped_durations)
    return new_track, selected_ayahs, word_ranges


def _cached_source_path(destination_dir: Path, reciter_id: str, surah_number: int,
                        audio_url: str) -> Path:
    import hashlib

    key = hashlib.sha256(f"{reciter_id}:{int(surah_number)}:{audio_url}".encode()).hexdigest()
    cache_dir = destination_dir / ".chapter-audio-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{key}.mp3"


def _prune_source_audio_cache(cache_dir: Path, *, keep: Path | None = None) -> None:
    now = time.time()
    cached = []
    total_bytes = 0
    for path in cache_dir.glob("*.mp3"):
        try:
            stat = path.stat()
            if now - stat.st_mtime > SOURCE_CACHE_TTL_SECONDS:
                if path != keep:
                    path.unlink(missing_ok=True)
                continue
            cached.append((stat.st_mtime, path, stat.st_size))
            total_bytes += stat.st_size
        except OSError:
            continue
    for _modified, path, size in sorted(cached):
        if total_bytes <= SOURCE_CACHE_MAX_BYTES:
            break
        if path == keep:
            continue
        path.unlink(missing_ok=True)
        total_bytes -= size


def _download_cached_source(reciter_id: str, surah_number: int, audio_url: str,
                            destination_dir: Path, *, cancel_event=None,
                            on_progress=None) -> Path:
    """Fetch a source chapter once and reuse it for nearby selections.

    Audio providers in this project expose chapter files rather than stable
    time-addressable byte ranges. Cache identity includes both the selected
    recording and its configured source URL so reciter changes cannot reuse
    the wrong recording.
    """
    cache_path = _cached_source_path(destination_dir, reciter_id, surah_number, audio_url)
    cache_dir = cache_path.parent
    with _SOURCE_AUDIO_CACHE_LOCK:
        _prune_source_audio_cache(cache_dir, keep=cache_path)
        try:
            if cache_path.is_file() and 0 < cache_path.stat().st_size <= MAX_AUDIO_BYTES:
                if on_progress:
                    size = cache_path.stat().st_size
                    on_progress(size, size)
                cache_path.touch()
                return cache_path
            cache_path.unlink(missing_ok=True)
        except OSError:
            cache_path.unlink(missing_ok=True)

        partial_path = cache_path.with_name(f".{cache_path.stem}-{uuid4().hex}.partial")
        request = Request(audio_url, headers={"User-Agent": "QuranReelsGenerator/1.0"})
        total = 0
        try:
            with urlopen(request, timeout=45) as response, partial_path.open("wb") as output:
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
            if total == 0:
                raise AudioSourceError("The recitation service returned an empty audio file.")
            partial_path.replace(cache_path)
            _prune_source_audio_cache(cache_dir, keep=cache_path)
            return cache_path
        except JobCancelled:
            raise
        except AudioSourceError:
            raise
        except HTTPError as exc:
            if exc.code == 404:
                raise AudioSourceError(
                    "The selected provider has no audio file for this Surah. Choose another available Surah."
                ) from exc
            if exc.code == 429:
                raise AudioSourceError(
                    "The audio provider is rate limiting requests. Wait a moment and try again."
                ) from exc
            if exc.code >= 500:
                raise AudioSourceError(
                    "The audio provider is temporarily unavailable. Try again shortly."
                ) from exc
            raise AudioSourceError(
                f"The audio provider rejected the request (HTTP {exc.code})."
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise AudioSourceError(
                "Could not download the selected recitation. Check your connection and try again."
            ) from exc
        finally:
            partial_path.unlink(missing_ok=True)


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
    if reciter.get("timing_provider") == "qud":
        try:
            return get_chapter_audio_url(reciter["timing_slug"], surah_number)
        except (KeyError, QudTimingError) as exc:
            raise AudioSourceError(str(exc)) from exc
    overrides = reciter.get("audio_url_overrides_by_surah")
    if isinstance(overrides, dict) and str(int(surah_number)) in overrides:
        audio_url = overrides[str(int(surah_number))]
        if not isinstance(audio_url, str) or not audio_url.startswith("https://"):
            raise AudioSourceError("This recording has no verified audio for the selected Surah.")
        return audio_url
    audio_urls_by_surah = reciter.get("audio_urls_by_surah")
    if isinstance(audio_urls_by_surah, dict):
        audio_url = audio_urls_by_surah.get(str(int(surah_number)))
        if not isinstance(audio_url, str) or not audio_url.startswith("https://"):
            raise AudioSourceError("This recording has no verified audio for the selected Surah.")
        return audio_url
    template = reciter.get("audio_url_template")
    if template:
        return template.format(surah=int(surah_number))
    return f"{reciter['audio_base_url']}{surah_number:03d}.mp3"


def get_recitation_timings(reciter: dict, surah_number: int, ayah_start: int, ayah_end: int) -> list[dict]:
    """Return millisecond timings for an inclusive ayah range."""
    if reciter.get("timing_provider") == "chapter_only":
        raise AudioSourceError(
            "This recording is available by Surah only and has no verified ayah boundaries."
        )
    if reciter.get("timing_provider") == "qud":
        try:
            return get_qud_recitation_timings(
                reciter["timing_slug"], surah_number, ayah_start, ayah_end,
            )
        except (KeyError, QudTimingError) as exc:
            raise AudioSourceError(str(exc)) from exc
    rows = _get_surah_timings(surah_number, reciter["read_id"])
    rows_by_ayah = {int(row["ayah"]): row for row in rows}
    selected = [rows_by_ayah.get(number) for number in range(ayah_start, ayah_end + 1)]
    if any(row is None for row in selected):
        raise AudioSourceError("Timing data does not cover the complete ayah range for this reciter.")
    if any(int(row["end_time"]) <= int(row["start_time"]) for row in selected):
        raise AudioSourceError("The recitation service returned invalid verse timings.")
    return selected


def probe_audio_duration(audio_path: Path) -> float:
    """Read the downloaded chapter's measured duration with FFprobe."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise AudioSourceError("FFprobe is required to read this chapter recording's duration.")
    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            check=False, capture_output=True, text=True, timeout=25,
        )
        duration = float(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired, TypeError, ValueError) as exc:
        raise AudioSourceError("Could not read the downloaded chapter audio duration.") from exc
    if result.returncode != 0 or not math.isfinite(duration) or duration <= 0:
        raise AudioSourceError("The chapter audio has an invalid or unreadable duration.")
    return duration


def estimate_ayah_durations(expected_ayahs, total_duration: float) -> list[float]:
    """Distribute chapter time by Quran text length when no verse times exist.

    These estimates are explicitly approximate and must not be used to cut a
    chapter-level recording into a partial ayah range.
    """
    from .word_alignment import normalize_arabic_word

    if not expected_ayahs or not math.isfinite(float(total_duration)) or total_duration <= 0:
        raise AudioSourceError("Cannot estimate ayah display timing for this chapter.")
    weights = [
        max(1, sum(len(normalize_arabic_word(word)) for word in str(ayah).split()))
        for ayah in expected_ayahs
    ]
    total_weight = sum(weights)
    if total_weight <= 0:
        raise AudioSourceError("Cannot estimate ayah display timing for this chapter.")
    durations = [float(total_duration) * weight / total_weight for weight in weights]
    durations[-1] += float(total_duration) - sum(durations)
    if any(not math.isfinite(value) or value <= 0 for value in durations):
        raise AudioSourceError("The chapter duration could not be divided into ayah timings.")
    return durations


def _stitch_qud_ayah_windows(source_path: Path, selected: list[dict], destination_dir: Path,
                              reciter_id: str, surah_number: int, cancel_event=None) -> Path:
    """Concatenate only the selected canonical ayah windows from a chapter file."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise AudioSourceError("FFmpeg is required to isolate the selected ayahs in this recording.")
    if not selected:
        raise AudioSourceError("QUD did not return ayah windows for the selected range.")
    filters = []
    concat_inputs = []
    for index, row in enumerate(selected):
        try:
            start = int(row["start_time"]) / 1000
            end = int(row["end_time"]) / 1000
        except (KeyError, TypeError, ValueError) as exc:
            raise AudioSourceError("QUD returned an invalid ayah window.") from exc
        if start < 0 or end <= start:
            raise AudioSourceError("QUD returned an invalid ayah window.")
        filters.append(
            f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a{index}]"
        )
        concat_inputs.append(f"[a{index}]")
    filters.append(f"{''.join(concat_inputs)}concat=n={len(selected)}:v=0:a=1[out]")
    output_path = destination_dir / f"qari-{reciter_id}-{surah_number:03d}-{uuid4().hex}.wav"
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source_path),
               "-filter_complex", ";".join(filters), "-map", "[out]", "-ac", "2",
               "-ar", "44100", "-c:a", "pcm_s16le", str(output_path)]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        while process.poll() is None:
            if cancel_event is not None and cancel_event.is_set():
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise JobCancelled()
            time.sleep(.05)
        if process.returncode != 0 or not output_path.is_file() or output_path.stat().st_size < 1024:
            output_path.unlink(missing_ok=True)
            raise AudioSourceError("FFmpeg could not isolate the selected ayahs from this recording.")
        import wave
        with wave.open(str(output_path), "rb") as stream:
            actual_duration = stream.getnframes() / float(stream.getframerate())
        requested_duration = sum(
            (int(row["end_time"]) - int(row["start_time"])) / 1000
            for row in selected
        )
        if abs(actual_duration - requested_duration) > .08:
            output_path.unlink(missing_ok=True)
            raise AudioSourceError("The selected audio windows do not match the verified QUD ayah timings.")
    except JobCancelled:
        output_path.unlink(missing_ok=True)
        raise
    except OSError as exc:
        output_path.unlink(missing_ok=True)
        raise AudioSourceError("Could not isolate the selected ayahs from this recording.") from exc
    return output_path


def _validated_relative_word_timings(selected, expected_ayahs, durations):
    """Convert chapter timestamps to offsets inside each effective ayah interval.

    The interval ends at the next ayah's start (or the final selected ayah's
    end), matching ``ayah_durations``. This prevents a word from being shown
    during a pause assigned to the previous ayah or outside the selected audio.
    """
    if len(selected) != len(expected_ayahs) or len(selected) != len(durations):
        raise ValueError("Word timestamp data does not cover the complete ayah range.")
    result = []
    for index, row in enumerate(selected):
        ayah_start_ms = int(row["start_time"])
        effective_end_ms = ayah_start_ms + round(float(durations[index]) * 1000)
        current = []
        previous_end_ms = 0
        for segment in row["segments"]:
            start_ms = int(segment["start_ms"]) - ayah_start_ms
            end_ms = int(segment["end_ms"]) - ayah_start_ms
            if (start_ms < previous_end_ms or end_ms <= start_ms
                    or end_ms > effective_end_ms - ayah_start_ms):
                raise ValueError("Word timestamps overlap or fall outside their effective ayah interval.")
            current.append({"start": start_ms / 1000, "end": end_ms / 1000})
            previous_end_ms = end_ms
        if len(current) != len(str(expected_ayahs[index]).split()):
            raise ValueError("Word timestamp count differs from the selected ayah text.")
        result.append(current)
    return result


def download_recitation(reciter: dict, surah_number: int, ayah_start: int, ayah_end: int,
                        destination_dir: Path, *, expected_ayahs=None,
                        cancel_event=None, on_progress=None) -> AudioTrack:
    """Download a chapter recording with timestamps from its matching audio.

    Quran Foundation word timestamps are used only when credentials, a
    chapter-reciter mapping, complete segment data, and local word counts all
    validate. Otherwise source-matched MP3Quran or pinned QUD ayah timings stay
    authoritative; the QUD path stitches only canonical selected ayah windows.
    """
    if cancel_event is not None and cancel_event.is_set():
        raise JobCancelled()
    from .word_alignment import get_chapter_word_timing

    chapter_only = reciter.get("timing_provider") == "chapter_only"
    if chapter_only:
        expected_count = int(SURAHS_BY_NUMBER[surah_number]["ayah_count"])
        if (ayah_start != 1 or ayah_end != expected_count or expected_ayahs is None
                or len(expected_ayahs) != expected_count):
            raise AudioSourceError(
                "This recording has chapter-level audio only. Select the complete Surah; "
                "partial ayah exports need verified ayah timings."
            )
        if surah_number not in reciter.get("available_surah_numbers", ()):
            raise AudioSourceError("This recording has no verified audio for the selected Surah.")
        word_timing_data = None
        fallback_note = ""
        selected = []
        audio_url = get_audio_url(reciter, surah_number)
        timing_source = "chapter_estimate"
        provider = reciter.get("source") or "This provider"
        timing_note = (
            f"{provider} provides this recording as per-Surah audio; no matching ayah timings are "
            "integrated for it. "
            "The complete Surah audio is kept intact; caption/scene boundaries are approximate, "
            "estimated from the Arabic text length. Partial ayah ranges are disabled."
        )
    else:
        word_timing_data = None
        fallback_note = "Word timing is not configured for this reciter; full ayahs use ayah-level timing."
        if expected_ayahs is not None and reciter.get("timing_provider") != "qud":
            try:
                word_timing_data = get_chapter_word_timing(
                    reciter["id"], surah_number, ayah_start, ayah_end, expected_ayahs,
                )
            except RuntimeError as exc:
                fallback_note = f"Word-level timing unavailable ({exc}); full ayahs use ayah-level timing."

    if chapter_only:
        pass
    elif word_timing_data:
        selected = word_timing_data["ayahs"]
        audio_url = word_timing_data["audio_url"]
        timing_source = "quran_foundation_word"
        timing_note = "Word timestamps from Quran Foundation chapter audio; checked against local ayah word counts."
    else:
        selected = get_recitation_timings(reciter, surah_number, ayah_start, ayah_end)
        audio_url = get_audio_url(reciter, surah_number)
        if reciter.get("timing_provider") == "qud":
            timing_source = "qud_ayah"
            timing_note = ("Pinned QUD v3.2.0 ayah timings matched to the listed MP3Quran audio. "
                           "Only selected canonical ayah audio windows are included; phrase splits "
                           "use the labeled ayah-duration fallback unless local forced alignment is enabled.")
        else:
            timing_source = "mp3quran_ayah"
            timing_note = fallback_note
    if cancel_event is not None and cancel_event.is_set():
        raise JobCancelled()
    if chapter_only:
        start_ms = end_ms = 0
        durations = []
    else:
        start_ms = int(selected[0]["start_time"])
        end_ms = int(selected[-1]["end_time"])
        if end_ms <= start_ms:
            raise AudioSourceError("The recitation service returned an invalid ayah time range.")

        # Assign inter-ayah pauses to the ayah before them so display durations sum to the audio span.
        starts = [int(row["start_time"]) for row in selected]
        if timing_source == "qud_ayah":
            durations = [(int(row["end_time"]) - int(row["start_time"])) / 1000
                         for row in selected]
        else:
            durations = [
                ((starts[index + 1] if index + 1 < len(starts) else end_ms) - starts[index]) / 1000
                for index in range(len(starts))
            ]
        if any(duration <= 0 for duration in durations):
            raise AudioSourceError("The recitation service returned invalid verse timings.")

    word_timings = None
    if word_timing_data:
        try:
            word_timings = _validated_relative_word_timings(selected, expected_ayahs, durations)
        except (KeyError, TypeError, ValueError) as exc:
            # Never pair uncertain word timing with the user's captions/audio.
            word_timing_data = None
            word_timings = None
            selected = get_recitation_timings(reciter, surah_number, ayah_start, ayah_end)
            audio_url = get_audio_url(reciter, surah_number)
            timing_source = "qud_ayah" if reciter.get("timing_provider") == "qud" else "mp3quran_ayah"
            timing_note = f"Word-level alignment did not validate ({exc}); full ayahs use ayah-level timing."
            start_ms = int(selected[0]["start_time"])
            end_ms = int(selected[-1]["end_time"])
            starts = [int(row["start_time"]) for row in selected]
            if timing_source == "qud_ayah":
                durations = [(int(row["end_time"]) - int(row["start_time"])) / 1000
                             for row in selected]
            else:
                durations = [((starts[i + 1] if i + 1 < len(starts) else end_ms) - starts[i]) / 1000
                             for i in range(len(starts))]
            if any(duration <= 0 for duration in durations):
                raise AudioSourceError("The recitation service returned invalid verse timings.")

    destination_dir.mkdir(parents=True, exist_ok=True)
    audio_path = _download_cached_source(
        reciter["id"], surah_number, audio_url, destination_dir,
        cancel_event=cancel_event, on_progress=on_progress,
    )

    if timing_source == "qud_ayah":
        source_audio_path = audio_path
        audio_path = _stitch_qud_ayah_windows(
            source_audio_path, selected, destination_dir, reciter["id"], surah_number,
            cancel_event=cancel_event,
        )
        selected = []
        offset_ms = 0
        for index, row in enumerate(durations):
            duration_ms = round(float(row) * 1000)
            selected.append({
                "ayah": ayah_start + index,
                "start_time": offset_ms,
                "end_time": offset_ms + duration_ms,
            })
            offset_ms += duration_ms
        start_ms, end_ms = 0, offset_ms

    if chapter_only:
        try:
            total_duration = probe_audio_duration(audio_path)
        except AudioSourceError:
            audio_path.unlink(missing_ok=True)
            raise
        durations = estimate_ayah_durations(expected_ayahs, total_duration)
        start_ms, end_ms = 0, round(total_duration * 1000)

    if word_timings is None and expected_ayahs is not None and not chapter_only:
        from .forced_alignment import forced_align_arabic_audio

        aligned_timings, alignment_note = forced_align_arabic_audio(
            audio_path, expected_ayahs, selected,
        )
        if aligned_timings is not None:
            word_timings = aligned_timings
            timing_source = "whisperx_forced_alignment"
            timing_note = alignment_note
        elif alignment_note != "Local forced alignment is disabled.":
            timing_note = f"{timing_note} {alignment_note} Full ayahs remain synchronized at ayah boundaries."

    return AudioTrack(audio_path, audio_url, start_ms / 1000, end_ms / 1000, durations,
                      word_timings, timing_source, timing_note,
                      persistent=(timing_source != "qud_ayah"))
