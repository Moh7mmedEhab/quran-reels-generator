"""Deterministic bilingual YouTube metadata based on selected Quran content."""
from __future__ import annotations

from .file_names import sanitize_video_filename
from .word_alignment import normalize_arabic_word


def _limited_tags(values, maximum=500):
    result, seen, used = [], set(), 0
    for item in values:
        item = " ".join(str(item).split()).strip()
        key = item.casefold()
        if not item or key in seen:
            continue
        cost = len(item) + (1 if result else 0)
        if used + cost > maximum:
            continue
        result.append(item)
        seen.add(key)
        used += cost
    return result


def _arabic_surah_names(value: str) -> tuple[str, str]:
    """Return a natural chapter label and bare name without duplicating "Surah"."""
    name = " ".join(str(value or "").split())
    words = name.split()
    has_prefix = bool(words and normalize_arabic_word(words[0]) == normalize_arabic_word("سُورَةُ"))
    return (name if has_prefix else f"سُورَةُ {name}"), (" ".join(words[1:]) if has_prefix else name)


def generate_youtube_metadata(*, surah_number: int, surah_english: str,
                              surah_arabic: str, ayah_start: int, ayah_end: int,
                              reciter_name: str) -> dict:
    """Build editable upload fields without inventing a translation or source."""
    range_ar = str(ayah_start) if ayah_start == ayah_end else f"{ayah_start}–{ayah_end}"
    range_en = str(ayah_start) if ayah_start == ayah_end else f"{ayah_start}-{ayah_end}"
    arabic_surah_label, arabic_surah_name = _arabic_surah_names(surah_arabic)
    arabic_title = f"{arabic_surah_label} | تلاوة قرآنية | الآيات {range_ar}"
    english_title = f"Surah {surah_english} | Quran Recitation | Ayahs {range_en}"
    title = f"{arabic_surah_label} | Surah {surah_english} · {range_en}"
    if len(title) > 100:
        title = arabic_title[:100].rstrip(" |·-")

    arabic_description = (
        f"تلاوة قرآنية من {arabic_surah_label}، الآيات {range_ar}.\n"
        f"القارئ: {reciter_name}.\n"
        "استمع بتدبر، وشارك المقطع مع من تحب.\n"
        "النص المعروض هو الآيات المحددة من القرآن الكريم.\n\n"
        f"#القرآن_الكريم #تلاوة_قرآنية #سورة_{arabic_surah_name.replace(' ', '_')}"
    )
    english_description = (
        f"Quran recitation from Surah {surah_english}, ayahs {range_en}.\n"
        f"Reciter: {reciter_name}.\n"
        "Listen, reflect, and share this selected passage. The video displays the selected Quran verses.\n\n"
        f"#Quran #QuranRecitation #Surah{surah_english.replace(' ', '')}"
    )
    arabic_tags = _limited_tags([
        "القرآن الكريم", "تلاوة قرآنية", arabic_surah_label,
        f"{arabic_surah_label} الآيات {range_ar}", "آيات قرآنية", "تدبر القرآن", reciter_name,
    ])
    english_tags = _limited_tags([
        "Quran", "Quran recitation", f"Surah {surah_english}",
        f"Surah {surah_english} ayahs {range_en}", reciter_name,
    ])
    return {
        "title": title[:100],
        "arabic": {
            "title": arabic_title[:100],
            "description": arabic_description[:5000],
            "tags": arabic_tags,
            "hashtags": ["#القرآن_الكريم", "#تلاوة_قرآنية", f"#سورة_{arabic_surah_name.replace(' ', '_')}"],
        },
        "english": {
            "title": english_title[:100],
            "description": english_description[:5000],
            "tags": english_tags,
            "hashtags": ["#Quran", "#QuranRecitation", f"#Surah{surah_english.replace(' ', '')}"],
        },
        "limits": {"title_characters": 100, "description_characters": 5000, "tags_characters": 500},
        "download_filename": sanitize_video_filename(title, f"Surah {surah_english} {range_en}"),
        "surah_number": int(surah_number),
        "ayah_start": int(ayah_start),
        "ayah_end": int(ayah_end),
        "reciter": reciter_name,
    }
