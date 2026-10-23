"""Resolve timed chapter recitations and download the selected audio range."""
from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path
import shutil
import subprocess
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
    except HTTPError as exc:
        audio_path.unlink(missing_ok=True)
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
        audio_path.unlink(missing_ok=True)
        raise AudioSourceError(
            "Could not download the selected recitation. Check your connection and try again."
        ) from exc
    if total == 0:
        audio_path.unlink(missing_ok=True)
        raise AudioSourceError("The recitation service returned an empty audio file.")

    if timing_source == "qud_ayah":
        source_audio_path = audio_path
        try:
            audio_path = _stitch_qud_ayah_windows(
                source_audio_path, selected, destination_dir, reciter["id"], surah_number,
                cancel_event=cancel_event,
            )
        finally:
            source_audio_path.unlink(missing_ok=True)
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
                      word_timings, timing_source, timing_note)
