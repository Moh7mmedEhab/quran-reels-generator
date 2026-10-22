"""Optional local Arabic forced alignment for recitations without word marks.

This adapter only runs when explicitly enabled. It aligns a normalized copy of
the known Quran text with a matching audio excerpt, then maps times by token
index back to the untouched Uthmani display text. Low-confidence or incomplete
output is rejected so callers can keep the full ayah visible instead.
"""
from __future__ import annotations

import math
import os
import threading

from .word_alignment import normalize_arabic_word

_MODEL_CACHE = {}
_MODEL_LOCK = threading.Lock()


def _enabled() -> bool:
    return os.environ.get("QURAN_REELS_FORCE_ALIGN", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _load_model(whisperx, model_name: str, device: str):
    key = (model_name, device)
    with _MODEL_LOCK:
        cached = _MODEL_CACHE.get(key)
        if cached:
            return cached
        model, metadata = whisperx.load_align_model(
            language_code="ar", device=device, model_name=model_name or None,
        )
        _MODEL_CACHE[key] = (model, metadata)
        return model, metadata


def forced_align_arabic_audio(audio_path, expected_ayahs, ayah_rows):
    """Try Arabic CTC forced alignment; return timing rows plus a status note.

    ``ayah_rows`` are source-audio millisecond boundaries for the same file.
    Returned word starts and ends are seconds relative to each ayah's start.
    ``(None, reason)`` means callers must use their explicit ayah-level fallback.
    """
    if not _enabled():
        return None, "Local forced alignment is disabled."
    if len(expected_ayahs) != len(ayah_rows) or not expected_ayahs:
        return None, "Local forced alignment received an incomplete ayah range."
    try:
        import whisperx
        import torch
    except ImportError:
        return None, "WhisperX and PyTorch are not installed."

    model_name = os.environ.get("QURAN_REELS_WHISPERX_MODEL", "").strip()
    requested_device = os.environ.get("QURAN_REELS_WHISPERX_DEVICE", "auto").strip().lower()
    if requested_device not in {"auto", "cpu", "cuda"}:
        return None, "QURAN_REELS_WHISPERX_DEVICE must be auto, cpu, or cuda."
    device = ("cuda" if torch.cuda.is_available() else "cpu") if requested_device == "auto" else requested_device
    if device == "cuda" and not torch.cuda.is_available():
        return None, "WhisperX CUDA alignment was requested but CUDA is unavailable."

    tokens_by_ayah = [str(ayah).split() for ayah in expected_ayahs]
    clean_texts = [" ".join(normalize_arabic_word(token) for token in tokens)
                   for tokens in tokens_by_ayah]
    if any(not text or any(not normalize_arabic_word(token) for token in tokens)
           for text, tokens in zip(clean_texts, tokens_by_ayah)):
        return None, "A Quran token cannot be represented by the Arabic alignment model."

    try:
        audio = whisperx.load_audio(str(audio_path))
        model, metadata = _load_model(whisperx, model_name, device)
        transcript = []
        for text, row in zip(clean_texts, ayah_rows):
            start = float(row["start_time"]) / 1000
            end = float(row["end_time"]) / 1000
            if not math.isfinite(start) or not math.isfinite(end) or end <= start:
                return None, "A source ayah boundary is invalid for forced alignment."
            transcript.append({"start": start, "end": end, "text": text})
        aligned = whisperx.align(
            transcript, model, metadata, audio, device,
            return_char_alignments=False,
        )
    except Exception as exc:
        # Optional model loading/inference must not turn a renderable ayah into
        # a failed export. The caller reports that the ayah-level fallback ran.
        return None, f"Arabic forced alignment failed ({type(exc).__name__})."

    segments = aligned.get("segments") if isinstance(aligned, dict) else None
    if not isinstance(segments, list) or len(segments) != len(expected_ayahs):
        return None, "Arabic forced alignment did not return one segment per ayah."
    result = []
    for index, (segment, tokens, row) in enumerate(zip(segments, tokens_by_ayah, ayah_rows)):
        words = segment.get("words") if isinstance(segment, dict) else None
        if not isinstance(words, list) or len(words) != len(tokens):
            return None, f"Arabic forced alignment did not align every word in ayah {index + 1}."
        verse_start = float(row["start_time"]) / 1000
        verse_end = float(row["end_time"]) / 1000
        aligned_words = []
        scores = []
        previous_end = verse_start - .01
        for word in words:
            try:
                start, end = float(word["start"]), float(word["end"])
                score = float(word["score"])
            except (KeyError, TypeError, ValueError):
                return None, f"Arabic forced alignment omitted a word boundary in ayah {index + 1}."
            if (not all(map(math.isfinite, (start, end, score))) or end <= start
                    or start < previous_end or start < verse_start - .25
                    or end > verse_end + .25 or score < .01):
                return None, f"Arabic forced alignment produced an uncertain boundary in ayah {index + 1}."
            previous_end = end
            scores.append(score)
            aligned_words.append({"start": start - verse_start, "end": end - verse_start})
        if sum(scores) / len(scores) < .25:
            return None, f"Arabic forced alignment confidence was low in ayah {index + 1}."
        result.append(aligned_words)
    return result, "Local Arabic forced alignment used a normalized copy of the selected Quran text."
