"""Scene planning for readable Quran captions and approximate phrase timing."""
from pathlib import Path
from unicodedata import category

from PIL import ImageFont

from .text_renderer import DEFAULT_FONT, wrap_arabic_lines
from .video_engine import SIZES

PREFERRED_BREAKS = frozenset("،؛.?!ۚۖۗۘۙۛۜ۞۩۝")


def _content_weight(text: str) -> int:
    """Use visible base characters as a proportional timing estimate, never exact timing."""
    return max(1, sum(not char.isspace() and category(char) not in {"Mn", "Me", "Cf"}
                      for char in text))


def _split_wrapped_lines(lines: list[str], max_lines: int) -> list[str]:
    """Group wrapped lines, preferring a nearby Arabic pause mark at each scene edge."""
    chunks = []
    start = 0
    while start < len(lines):
        end = min(start + max_lines, len(lines))
        if end < len(lines):
            lower_bound = max(start + 1, end - 2)
            for candidate in range(end, lower_bound - 1, -1):
                if lines[candidate - 1].rstrip()[-1:] and lines[candidate - 1].rstrip()[-1] in PREFERRED_BREAKS:
                    end = candidate
                    break
        chunks.append(" ".join(lines[start:end]))
        start = end
    return chunks


def _effective_line_limit(*, requested, font_size, max_height, show_surah_title, padding_y):
    line_height = font_size + 20
    header_space = int(font_size * .82) + 34 if show_surah_title else 0
    available = max(1, max_height - header_space - padding_y * 2)
    return max(1, min(requested, available // line_height))


def _manual_scenes(ayahs, ayah_start, overrides):
    if not isinstance(overrides, list) or not overrides or len(overrides) > 300:
        raise ValueError("Manual scene data must contain between 1 and 300 scenes.")
    grouped = [[] for _ in ayahs]
    scenes = []
    last_ayah_index = 0
    for row in overrides:
        if not isinstance(row, dict):
            raise ValueError("Each manual scene must be an object with an ayah number and text.")
        try:
            ayah_number = int(row.get("ayah_number"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Each manual scene needs a valid ayah number.") from exc
        ayah_index = ayah_number - ayah_start
        if ayah_index < 0 or ayah_index >= len(ayahs):
            raise ValueError("A manual scene references an ayah outside the selected range.")
        if ayah_index < last_ayah_index:
            raise ValueError("Scene order must preserve the Quran's original ayah order.")
        last_ayah_index = ayah_index
        text = str(row.get("text", "")).strip()
        if not text:
            raise ValueError("A manual scene cannot have empty text.")
        grouped[ayah_index].append(text)
        scene = {"ayah_number": ayah_number, "text": text,
                 "segment_index": len(grouped[ayah_index]), "weight": _content_weight(text)}
        if row.get("duration_fraction") not in (None, ""):
            try:
                fraction = float(row["duration_fraction"])
            except (TypeError, ValueError) as exc:
                raise ValueError("Manual scene timing fractions must be valid numbers.") from exc
            if not 0.05 <= fraction <= .95:
                raise ValueError("A manual scene timing fraction must be between 5% and 95%.")
            scene["duration_fraction"] = fraction
            scene["manual_duration_fraction"] = True
        scenes.append(scene)

    for index, ayah in enumerate(ayahs):
        actual = "".join("".join(part.split()) for part in grouped[index])
        expected = "".join(str(ayah).split())
        if actual != expected:
            raise ValueError(
                f"Manual scenes for ayah {ayah_start + index} must preserve every character and its order."
            )
    counts = {}
    for scene in scenes:
        number = scene["ayah_number"]
        counts[number] = counts.get(number, 0) + 1
    for scene in scenes:
        scene["segment_count"] = counts[scene["ayah_number"]]
    for ayah_number in counts:
        group = [scene for scene in scenes if scene["ayah_number"] == ayah_number]
        explicit = [scene for scene in group if scene.get("manual_duration_fraction")]
        if explicit and len(explicit) != len(group):
            raise ValueError("Set a manual timing fraction on every segment of the same ayah.")
        if explicit and abs(sum(scene["duration_fraction"] for scene in group) - 1) > .005:
            raise ValueError("Manual scene timing fractions for each ayah must sum to 100%.")
    return scenes


def build_scene_plan(ayahs, *, ayah_start=1, durations=None, aspect_ratio="9:16",
                     wrap_width=85, max_lines=5, font_path=None, show_surah_title=False,
                     padding_y=24, scene_overrides=None, default_duration=3.0, output_size=None):
    """Create readable display scenes, allocating exact verse time proportionally for splits.

    Ayah timing from the source remains authoritative. Phrase timing inside a long
    ayah is explicitly an estimate based on visible character count because the
    source provides no word-level timestamps.
    """
    if aspect_ratio not in SIZES:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
    if not ayahs:
        raise ValueError("At least one ayah is required to plan scenes.")
    try:
        max_lines = max(1, min(8, int(max_lines)))
        wrap_width = int(wrap_width)
        width, height = output_size or SIZES[aspect_ratio]
        font_size = max(26, int(width * .07))
    except (TypeError, ValueError) as exc:
        raise ValueError("Scene layout settings must be valid numbers.") from exc
    if wrap_width not in {65, 75, 85, 95}:
        raise ValueError("Text wrap width must be 65, 75, 85, or 95 percent.")

    width, height = output_size or SIZES[aspect_ratio]
    max_width = int(width * wrap_width / 100)
    max_height = int(height * .44)
    chosen_font = Path(font_path) if font_path else DEFAULT_FONT
    if not chosen_font.exists():
        raise FileNotFoundError(f"Arabic font not found: {chosen_font}")
    font = ImageFont.truetype(str(chosen_font), font_size)
    line_limit = _effective_line_limit(
        requested=max_lines, font_size=font_size, max_height=max_height,
        show_surah_title=show_surah_title, padding_y=int(padding_y),
    )

    if durations is not None and (len(durations) != len(ayahs) or any(float(item) <= 0 for item in durations)):
        raise ValueError("Audio timing must provide one positive duration for each ayah.")

    scenes = []
    for index, ayah in enumerate(ayahs):
        source_text = str(ayah).strip()
        lines = wrap_arabic_lines(source_text, font, max_width)
        chunks = _split_wrapped_lines(lines, line_limit)
        if not chunks:
            raise ValueError(f"Ayah {ayah_start + index} has no renderable words.")
        weights = [_content_weight(chunk) for chunk in chunks]
        verse_duration = float(durations[index]) if durations is not None else float(default_duration)
        total_weight = sum(weights)
        for part, (chunk, weight) in enumerate(zip(chunks, weights), start=1):
            scenes.append({
                "scene_index": len(scenes),
                "ayah_number": int(ayah_start) + index,
                "segment_index": part,
                "segment_count": len(chunks),
                "text": chunk,
                "weight": weight,
                "duration_fraction": weight / total_weight,
                "ayah_total_duration": verse_duration,
                "duration": verse_duration * weight / total_weight,
                "timing_mode": ("character_weighted_estimate" if len(chunks) > 1 else
                                "ayah_timestamp" if durations is not None else "default_duration_estimate"),
            })

    if scene_overrides is not None:
        scenes = _manual_scenes(ayahs, int(ayah_start), scene_overrides)
        for scene_number, scene in enumerate(scenes, start=1):
            if len(wrap_arabic_lines(scene["text"], font, max_width)) > line_limit:
                raise ValueError(
                    f"Manual scene {scene_number} exceeds the selected line limit; split that scene."
                )
        for index, scene in enumerate(scenes):
            scene["scene_index"] = index
            source_index = scene["ayah_number"] - int(ayah_start)
            source_scenes = [item for item in scenes if item["ayah_number"] == scene["ayah_number"]]
            weights = [item["weight"] for item in source_scenes]
            verse_duration = float(durations[source_index]) if durations is not None else float(default_duration)
            scene["ayah_total_duration"] = verse_duration
            if source_scenes[0].get("manual_duration_fraction"):
                scene["duration"] = verse_duration * scene["duration_fraction"]
                scene["timing_mode"] = "manual_fraction_estimate"
            else:
                scene["duration_fraction"] = scene["weight"] / sum(weights)
                scene["duration"] = verse_duration * scene["duration_fraction"]
                scene["timing_mode"] = (
                    "manual_character_weighted_estimate" if len(source_scenes) > 1 else
                    "ayah_timestamp" if durations is not None else "default_duration_estimate"
                )

    cursor = 0.0
    for scene in scenes:
        scene["start_time"] = round(cursor, 3)
        cursor += float(scene["duration"])
        scene["end_time"] = round(cursor, 3)

    return scenes
