"""Scene planning and word-boundary-safe Quran phrase grouping.

Validated word timestamps provide exact phrase timing. When only ayah
durations are available, split scenes use an explicitly approximate estimate
weighted by Arabic word length and pause marks.
"""
import re
import unicodedata
from pathlib import Path
from math import isfinite

from PIL import Image, ImageDraw

from .text_renderer import (DEFAULT_FONT, load_arabic_font,
                            measure_arabic_line_width, wrap_arabic_lines)
from .video_engine import SIZES

PREFERRED_BREAKS = frozenset("،؛.?!ۚۖۗۘۙۛۜ۞۩۝")


def _translation_boundary_rank(token):
    token = re.sub(r"[\"'’”’»\)\]\}]+$", "", str(token))
    if re.search(r"[.!?…]$", token):
        return 0
    if re.search(r"[;:—–]$", token):
        return 1
    if token.endswith(","):
        return 2
    return 3


def split_translation_across_scenes(translation, scene_word_counts):
    """Partition one ayah translation across Arabic scenes without rewriting it.

    Scene Arabic word counts set proportional targets. Sentence and phrase
    punctuation are preferred boundaries; plain word boundaries are used only
    when the source translation has no suitable phrase break near a target.
    """
    counts = [max(0, int(count)) for count in scene_word_counts]
    if not counts:
        return []
    text = str(translation or "").strip()
    if not text:
        return [""] * len(counts)
    if len(counts) == 1:
        return [text]

    words = list(re.finditer(r"\S+", text))
    word_total = len(words)
    if not word_total:
        return [""] * len(counts)
    weights = counts if sum(counts) else [1] * len(counts)
    weight_total = sum(weights)
    min_words = 1 if word_total >= len(counts) else 0
    states = {0: (0.0, [])}
    cumulative_weight = 0
    for boundary_index in range(1, len(counts)):
        cumulative_weight += weights[boundary_index - 1]
        target = word_total * cumulative_weight / weight_total
        remaining_scenes = len(counts) - boundary_index
        next_states = {}
        for previous_cut, (previous_cost, previous_cuts) in states.items():
            first_cut = previous_cut + min_words
            last_cut = word_total - remaining_scenes * min_words
            for cut in range(first_cut, last_cut + 1):
                if 0 < cut < word_total:
                    rank = _translation_boundary_rank(words[cut - 1].group())
                else:
                    rank = 3
                punctuation_penalty = (0.0, .4, .9, 2.0)[rank]
                empty_penalty = .25 if cut == previous_cut else 0.0
                cost = (previous_cost + abs(cut - target) + punctuation_penalty
                        + empty_penalty)
                candidate = (cost, [*previous_cuts, cut])
                existing = next_states.get(cut)
                if existing is None or (candidate[0], candidate[1]) < (existing[0], existing[1]):
                    next_states[cut] = candidate
        states = next_states

    cuts = min(states.values(), key=lambda item: (item[0], item[1]))[1]
    boundaries = [0, *cuts, word_total]
    segments = []
    for start, end in zip(boundaries, boundaries[1:]):
        if end <= start:
            segments.append("")
        else:
            segments.append(text[words[start].start():words[end - 1].end()].strip())
    return segments


def synchronize_scene_translations(scene_rows, translation_lines, *, ayah_start=1):
    """Attach each ayah's phrase-aligned translation to its Arabic scene span."""
    if not isinstance(scene_rows, list):
        raise ValueError("Scene translation alignment requires a scene list.")
    scenes = [dict(scene) for scene in scene_rows]
    for scene in scenes:
        scene["translation_text"] = ""
    if translation_lines is None or translation_lines == []:
        return scenes
    if not isinstance(translation_lines, list):
        raise ValueError("English translations must contain one line per selected ayah.")
    translations = []
    for line in translation_lines:
        if not isinstance(line, str) or len(line) > 5000:
            raise ValueError("Each English ayah translation must be text no longer than 5,000 characters.")
        translations.append(line.strip())

    grouped = {}
    for index, scene in enumerate(scenes):
        try:
            ayah_number = int(scene["ayah_number"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Every scene needs a valid ayah number for translation alignment.") from exc
        grouped.setdefault(ayah_number, []).append((index, scene))

    for ayah_number, indexed_scenes in grouped.items():
        translation_index = ayah_number - int(ayah_start)
        translation = translations[translation_index] if 0 <= translation_index < len(translations) else ""
        has_word_spans = all(
            isinstance(scene.get("word_start_index"), int)
            and not isinstance(scene.get("word_start_index"), bool)
            for _, scene in indexed_scenes
        )
        if has_word_spans:
            ordered = sorted(indexed_scenes, key=lambda item: (item[1]["word_start_index"], item[0]))
        else:
            ordered = indexed_scenes
        segments = split_translation_across_scenes(
            translation, [len(str(scene.get("text", "")).split()) for _, scene in ordered],
        )
        for (scene_index, _scene), segment in zip(ordered, segments):
            scenes[scene_index]["translation_text"] = segment
    return scenes


def split_ayah_at_word_boundaries(text: str, *, max_words=18, max_characters=180,
                                  preferred_breaks=PREFERRED_BREAKS) -> list[str]:
    """Group whole whitespace-delimited Quran tokens without altering their order.

    Display whitespace is normalized to one ASCII space between words. Quranic
    marks and punctuation remain attached to their source word. Concatenating
    the returned strings after removing whitespace reconstructs the input.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Ayah text cannot be empty.")
    try:
        max_words, max_characters = int(max_words), int(max_characters)
    except (TypeError, ValueError) as exc:
        raise ValueError("Word and character limits must be whole numbers.") from exc
    if max_words < 1 or max_characters < 1:
        raise ValueError("Word and character limits must be positive.")

    words = text.split()
    groups: list[list[str]] = []
    pending: list[str] = []
    for word in words:
        would_exceed = pending and (
            len(pending) >= max_words
            or len(" ".join((*pending, word))) > max_characters
        )
        if would_exceed:
            # Prefer a nearby pause mark without producing an empty group.
            preferred = next((i for i in range(len(pending) - 1, -1, -1)
                              if pending[i][-1:] in preferred_breaks), None)
            if preferred is not None and preferred >= max(0, len(pending) - 3):
                groups.append(pending[:preferred + 1])
                pending = pending[preferred + 1:]
            else:
                groups.append(pending)
                pending = []
        pending.append(word)
    if pending:
        groups.append(pending)
    return [" ".join(group) for group in groups if group]


def _split_wrapped_lines(lines: list[str], max_lines: int) -> list[str]:
    """Group complete wrapped lines, preferring nearby Arabic pause marks."""
    chunks = []
    start = 0
    while start < len(lines):
        end = min(start + max_lines, len(lines))
        if end < len(lines):
            lower_bound = max(start + 1, end - 2)
            for candidate in range(end, lower_bound - 1, -1):
                ending = lines[candidate - 1].rstrip()[-1:]
                if ending in PREFERRED_BREAKS:
                    end = candidate
                    break
        chunks.append(" ".join(lines[start:end]))
        start = end
    return chunks


def _split_scene_text(text, *, font, max_width, max_lines, words_per_scene):
    """Split at a word-count limit, then enforce the visual line limit."""
    word_groups = split_ayah_at_word_boundaries(
        text, max_words=words_per_scene, max_characters=100_000,
    )
    chunks = []
    for word_group in word_groups:
        lines = wrap_arabic_lines(word_group, font, max_width)
        chunks.extend(_split_wrapped_lines(lines, max_lines))
    return chunks


def _arabic_letter_word_count(text):
    """Count whitespace-delimited tokens that contain an Arabic-script letter."""
    count = 0
    for token in str(text).split():
        if any(unicodedata.category(character).startswith("L")
               and "ARABIC" in unicodedata.name(character, "") for character in token):
            count += 1
    return count


def split_tall_ayah_into_lines(text, *, font, max_width, stroke_width=0,
                               minimum_arabic_words=3):
    """Split an ayah into measured one-line chunks while balancing its final group.

    Width checks use the same shaped Arabic, font, and stroke-aware Pillow
    metrics as the caption renderer. If no partition can keep every chunk at
    the requested Arabic-word minimum, the greedy one-line layout is retained.
    """
    source = str(text or "").strip()
    if not source:
        raise ValueError("Ayah text cannot be empty.")
    try:
        max_width = int(max_width)
        stroke_width = max(0, int(stroke_width))
        minimum_arabic_words = int(minimum_arabic_words)
    except (TypeError, ValueError) as exc:
        raise ValueError("Arabic layout measurements must be whole numbers.") from exc
    if max_width < 1 or minimum_arabic_words < 1:
        raise ValueError("Arabic line width and minimum word count must be positive.")

    matches = list(re.finditer(r"\S+", source))
    if not matches:
        raise ValueError("Ayah text cannot be empty.")
    tokens = [match.group() for match in matches]
    full_width = measure_arabic_line_width(source, font, stroke_width)
    if full_width <= max_width:
        return {"text": source, "chunks": [source], "is_tall": False,
                "needs_split": False, "minimum_met": True}

    token_weights = [int(bool(_arabic_letter_word_count(token))) for token in tokens]
    prefix = [0]
    for weight in token_weights:
        prefix.append(prefix[-1] + weight)
    arabic_words = prefix[-1]
    if arabic_words < minimum_arabic_words:
        return {"text": source, "chunks": [source], "is_tall": True,
                "needs_split": False, "minimum_met": True,
                "reason": "Ayah has fewer than the minimum Arabic words."}

    # Find a minimum-scene partition that keeps every line readable and has
    # at least three Arabic words. Among equally short layouts, prefer balanced
    # word counts and then Quranic pause-mark boundaries.
    best = [None] * (len(tokens) + 1)
    best[0] = (0, 0, 0, ())
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for start in range(len(tokens)):
        previous = best[start]
        if previous is None:
            continue
        for end in range(start + 1, len(tokens) + 1):
            candidate = source[matches[start].start():matches[end - 1].end()]
            if measure_arabic_line_width(candidate, font, stroke_width, draw=draw) > max_width:
                break
            arabic_count = prefix[end] - prefix[start]
            if arabic_count < minimum_arabic_words:
                continue
            pause_penalty = 0 if tokens[end - 1].rstrip()[-1:] in PREFERRED_BREAKS else 1
            score = (previous[0] + 1, previous[1] + arabic_count ** 2,
                     previous[2] + pause_penalty, (*previous[3], end))
            if best[end] is None or score < best[end]:
                best[end] = score

    minimum_met = best[-1] is not None
    if minimum_met:
        boundaries = (0, *best[-1][3], len(tokens))
    else:
        # Readability wins when unusually long words make the 3-word minimum
        # impossible. The shared renderer's wrapper still keeps whole words.
        wrapped = wrap_arabic_lines(source, font, max_width, stroke_width)
        counts = [len(line.split()) for line in wrapped]
        cursor = 0
        boundaries_list = [0]
        for count in counts:
            cursor += count
            boundaries_list.append(cursor)
        if cursor != len(tokens):
            raise ValueError("Arabic wrapping did not preserve the ayah's complete word sequence.")
        boundaries = tuple(boundaries_list)

    chunks = [source[matches[start].start():matches[end - 1].end()]
              for start, end in zip(boundaries, boundaries[1:]) if end > start]
    short_chunks = any(_arabic_letter_word_count(chunk) < minimum_arabic_words for chunk in chunks)
    return {"text": source, "chunks": chunks, "is_tall": True,
            "needs_split": len(chunks) > 1, "minimum_met": minimum_met and not short_chunks}


def plan_auto_split_scenes(ayahs, *, ayah_start=1, font, max_width, stroke_width=0,
                           minimum_arabic_words=3):
    """Create standard scene override rows for only ayahs that visually wrap."""
    if not isinstance(ayahs, list) or not ayahs:
        raise ValueError("At least one ayah is required to auto-split scenes.")
    try:
        ayah_start = int(ayah_start)
    except (TypeError, ValueError) as exc:
        raise ValueError("The starting ayah must be a whole number.") from exc

    rows = []
    split_ayahs = []
    tall_ayahs = []
    short_fallback_ayahs = []
    for index, ayah in enumerate(ayahs):
        ayah_number = ayah_start + index
        result = split_tall_ayah_into_lines(
            ayah, font=font, max_width=max_width, stroke_width=stroke_width,
            minimum_arabic_words=minimum_arabic_words,
        )
        if result["is_tall"]:
            tall_ayahs.append(ayah_number)
        if result["needs_split"]:
            split_ayahs.append(ayah_number)
        if result["needs_split"] and not result["minimum_met"]:
            short_fallback_ayahs.append(ayah_number)
        word_offset = 0
        for chunk in result["chunks"]:
            count = len(chunk.split())
            rows.append({
                "scene_id": f"ayah-{ayah_number}-word-{word_offset}",
                "ayah_number": ayah_number,
                "text": chunk,
                "locked": False,
            })
            word_offset += count
    return {"scenes": rows, "tall_ayahs": tall_ayahs,
            "split_ayahs": split_ayahs,
            "short_fallback_ayahs": short_fallback_ayahs}


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
    scene_ids = set()
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
        word_count = len(text.split())
        locked = row.get("locked", False)
        if not isinstance(locked, bool):
            raise ValueError("Scene lock state must be true or false.")
        word_offset = sum(len(part.split()) for part in grouped[ayah_index])
        scene_id = str(row.get("scene_id") or f"ayah-{ayah_number}-word-{word_offset}").strip()
        if not scene_id or len(scene_id) > 128 or scene_id in scene_ids:
            raise ValueError("Every scene needs a unique identifier no longer than 128 characters.")
        scene_ids.add(scene_id)
        grouped[ayah_index].append(text)
        scene = {"ayah_number": ayah_number, "text": text,
                 "scene_id": scene_id, "locked": locked,
                 "segment_index": len(grouped[ayah_index]), "word_count": word_count, "weight": 1,
                 "word_start_index": word_offset,
                 "word_end_index": word_offset + word_count - 1}
        if row.get("manual_duration") not in (None, ""):
            if isinstance(row["manual_duration"], bool):
                raise ValueError("Scene duration must be a positive decimal number of seconds.")
            try:
                manual_duration = float(row["manual_duration"])
            except (TypeError, ValueError) as exc:
                raise ValueError("Scene duration must be a positive decimal number of seconds.") from exc
            if not isfinite(manual_duration) or not 0 < manual_duration <= 3600:
                raise ValueError("Scene duration must be greater than 0 and no more than 3600 seconds.")
            submitted_duration = row.get("duration")
            if submitted_duration not in (None, ""):
                try:
                    submitted_duration = float(submitted_duration)
                except (TypeError, ValueError) as exc:
                    raise ValueError("Scene duration must be a positive decimal number of seconds.") from exc
                if not isfinite(submitted_duration) or abs(submitted_duration - manual_duration) > .001:
                    raise ValueError("The applied scene duration does not match its manual duration value.")
            scene["manual_duration"] = manual_duration
        if row.get("duration_fraction") not in (None, ""):
            raise ValueError("Manual percentage timing is no longer supported. Use word-count splits with voice timing.")
        scenes.append(scene)

    for index, ayah in enumerate(ayahs):
        if not grouped[index]:
            raise ValueError(f"Manual scenes must include every selected ayah; ayah {ayah_start + index} is missing.")
        actual = "".join("".join(part.split()) for part in grouped[index])
        expected = "".join(str(ayah).split())
        if actual != expected:
            raise ValueError(
                f"Manual scenes for ayah {ayah_start + index} must preserve every character and its order."
            )
        if grouped[index]:
            source_words = str(ayah).split()
            scene_words = [word for scene in scenes if scene["ayah_number"] == ayah_start + index
                           for word in scene["text"].split()]
            if source_words != scene_words:
                raise ValueError(
                    f"Manual scenes for ayah {ayah_start + index} must split only at word boundaries."
                )

    counts = {}
    for scene in scenes:
        number = scene["ayah_number"]
        counts[number] = counts.get(number, 0) + 1
    for scene in scenes:
        number = scene["ayah_number"]
        scene["segment_count"] = counts[number]
    for scene in scenes:
        scene["timing_mode"] = "word_timing_pending" if scene["segment_count"] > 1 else "ayah_timestamp"
    return scenes


def clip_scene_overrides_to_word_ranges(ayahs, ayah_start, overrides, word_ranges):
    """Project existing scene edits onto selected word spans without mutating them.

    A partially intersected scene keeps its ID, lock state, and manual duration;
    source scenes outside the chosen audio range are omitted from this render.
    The editor's saved full-ayah scene plan remains untouched.
    """
    if overrides is None or not isinstance(overrides, list):
        return overrides
    if len(word_ranges) != len(ayahs):
        raise ValueError("Word selection does not cover the complete ayah range.")
    previous_ayah = int(ayah_start)
    for row in overrides:
        if not isinstance(row, dict):
            return overrides
        try:
            number = int(row.get("ayah_number"))
        except (TypeError, ValueError):
            return overrides
        if number < int(ayah_start) or number >= int(ayah_start) + len(ayahs) or number < previous_ayah:
            return overrides
        previous_ayah = number
    projected = []
    for index, (ayah, selected_range) in enumerate(zip(ayahs, word_ranges)):
        try:
            lower, upper = int(selected_range[0]), int(selected_range[1])
            ayah_number = int(ayah_start) + index
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError("Word selection contains an invalid ayah boundary.") from exc
        source_words = str(ayah).split()
        if lower < 1 or upper < lower or upper > len(source_words):
            raise ValueError(f"Word selection is invalid for ayah {ayah_number}.")
        matching_rows = []
        for row in overrides:
            if not isinstance(row, dict):
                continue
            try:
                row_number = int(row.get("ayah_number"))
            except (TypeError, ValueError):
                continue
            if row_number == ayah_number:
                matching_rows.append(row)
        if not matching_rows:
            continue
        scene_cursor = 0
        for row in matching_rows:
            scene_words = str(row.get("text", "")).strip().split()
            scene_end = scene_cursor + len(scene_words)
            overlap_start = max(scene_cursor, lower - 1)
            overlap_end = min(scene_end, upper)
            if overlap_end > overlap_start:
                clipped = dict(row)
                clipped["text"] = " ".join(scene_words[overlap_start - scene_cursor:
                                                          overlap_end - scene_cursor])
                projected.append(clipped)
            scene_cursor = scene_end
        if scene_cursor != len(source_words):
            # Keep invalid or custom scene data intact so the existing strict
            # scene validator can return its specific error to the caller.
            return overrides
    return projected


def compose_scene_plan_overrides(ayahs, default_scenes, *, ayah_start=1,
                                 saved_defaults=None, saved_edits=None):
    """Restore stable per-ayah scene arrangements over a newly planned range.

    Saved records are scoped by source text and ayah number. Records outside
    the active range are ignored, so clients can keep one cache while changing
    the visible range. The returned default and edited plans are both checked
    against the selected Quran text and word order.
    """
    try:
        ayah_start = int(ayah_start)
    except (TypeError, ValueError) as exc:
        raise ValueError("The selected ayah range must start at a whole number.") from exc
    if not isinstance(ayahs, list) or not ayahs:
        raise ValueError("At least one ayah is required to restore scene edits.")
    if not isinstance(default_scenes, list) or not default_scenes:
        raise ValueError("The default scene plan is empty.")

    default_groups = {ayah_start + index: [] for index in range(len(ayahs))}
    for scene in default_scenes:
        if not isinstance(scene, dict):
            raise ValueError("The default scene plan contains an invalid row.")
        try:
            number = int(scene.get("ayah_number"))
        except (TypeError, ValueError) as exc:
            raise ValueError("The default scene plan contains an invalid ayah number.") from exc
        if number not in default_groups:
            raise ValueError("The default scene plan contains an ayah outside the selected range.")
        default_groups[number].append({
            "ayah_number": number,
            "text": scene.get("text", ""),
            "scene_id": scene.get("scene_id"),
            "locked": bool(scene.get("locked", False)),
            "manual_duration": scene.get("manual_duration"),
        })
    if any(not rows for rows in default_groups.values()):
        raise ValueError("The default scene plan must include every selected ayah.")

    def cached_groups(records, label):
        if records is None:
            return {}
        if not isinstance(records, list) or len(records) > 300:
            raise ValueError(f"Saved {label} must contain at most 300 ayah records.")
        result = {}
        for record in records:
            if not isinstance(record, dict):
                raise ValueError(f"Each saved {label} record must be an object.")
            try:
                number = int(record.get("ayah_number"))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Each saved {label} record needs an ayah number.") from exc
            if number < ayah_start or number >= ayah_start + len(ayahs):
                continue
            source = str(record.get("source_text", "")).strip()
            if source != str(ayahs[number - ayah_start]).strip():
                continue
            if number in result:
                raise ValueError(f"Saved {label} contain duplicate records for ayah {number}.")
            rows = record.get("scenes")
            if not isinstance(rows, list) or not rows:
                raise ValueError(f"Saved {label} for ayah {number} need at least one scene.")
            result[number] = []
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError(f"Saved {label} for ayah {number} contain an invalid scene.")
                row_number = row.get("ayah_number", number)
                try:
                    row_number = int(row_number)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Saved {label} for ayah {number} contain an invalid scene ayah.") from exc
                if row_number != number:
                    raise ValueError(f"Saved {label} scenes must stay within ayah {number}.")
                result[number].append({
                    "ayah_number": number,
                    "text": row.get("text", ""),
                    "scene_id": row.get("scene_id"),
                    "locked": row.get("locked", False),
                    "manual_duration": row.get("manual_duration"),
                })
        return result

    default_cache = cached_groups(saved_defaults, "scene defaults")
    edit_cache = cached_groups(saved_edits, "scene edits")
    default_rows = []
    edited_rows = []
    for index, ayah in enumerate(ayahs):
        number = ayah_start + index
        defaults = default_cache.get(number, default_groups[number])
        default_rows.extend(defaults)
        edited_rows.extend(edit_cache.get(number, defaults))

    validated_defaults = _manual_scenes(ayahs, ayah_start, default_rows)
    validated_edits = _manual_scenes(ayahs, ayah_start, edited_rows)
    return {
        "default_scenes": validated_defaults,
        "scenes": validated_edits,
        "cached_default_ayah_count": len(default_cache),
        "edited_ayah_count": len(edit_cache),
    }


def redistribute_scene_words(ayahs, scene_rows, *, ayah_start=1,
                            scene_index, requested_word_count):
    """Move whole words between adjacent scenes in the selected ayah only.

    The input rows are validated against the source ayahs before mutation. A
    lone ayah scene can be split by reducing its count; later scenes can only
    take or give words to following scenes from the same ayah.
    """
    if isinstance(requested_word_count, str) and not requested_word_count.isdecimal():
        raise ValueError("Words in a scene must be a positive whole number.")
    try:
        selected_index = int(scene_index)
        requested = int(requested_word_count)
    except (TypeError, ValueError) as exc:
        raise ValueError("Scene index and word count must be whole numbers.") from exc
    if isinstance(requested_word_count, bool) or requested < 1:
        raise ValueError("Words in a scene must be at least one.")
    if isinstance(requested_word_count, float) and requested_word_count != requested:
        raise ValueError("Words in a scene must be a whole number.")

    scenes = _manual_scenes(ayahs, int(ayah_start), scene_rows)
    if selected_index < 0 or selected_index >= len(scenes):
        raise ValueError("The selected scene no longer exists.")
    selected = scenes[selected_index]
    selected_ayah = selected["ayah_number"]
    ayah_first = selected_index
    while ayah_first > 0 and scenes[ayah_first - 1]["ayah_number"] == selected_ayah:
        ayah_first -= 1
    ayah_after = selected_index + 1
    while ayah_after < len(scenes) and scenes[ayah_after]["ayah_number"] == selected_ayah:
        ayah_after += 1

    current_words = selected["text"].split()
    if selected["locked"]:
        raise ValueError("Unlock this scene before changing its word allocation.")
    safe_following = []
    for following in scenes[selected_index + 1:ayah_after]:
        if following["locked"]:
            break
        safe_following.append(following)
    following_words = sum(len(row["text"].split()) for row in safe_following)
    max_words = len(current_words) + following_words
    has_following = selected_index + 1 < ayah_after and not scenes[selected_index + 1]["locked"]
    if requested > max_words:
        raise ValueError(f"This scene can contain at most {max_words} words without crossing an ayah boundary.")
    target = requested

    if target < len(current_words):
        moved = current_words[target:]
        current_words = current_words[:target]
        if has_following:
            next_words = scenes[selected_index + 1]["text"].split()
            scenes[selected_index + 1]["text"] = " ".join([*moved, *next_words])
        else:
            next_word_offset = (sum(len(row["text"].split()) for row in scenes[ayah_first:selected_index])
                                + len(current_words))
            scenes.insert(selected_index + 1, {
                "ayah_number": selected_ayah, "text": " ".join(moved),
                "scene_id": f"ayah-{selected_ayah}-word-{next_word_offset}",
                "locked": False, "segment_index": 0, "segment_count": 0,
                "word_count": len(moved),
            })
    elif target > len(current_words):
        remaining = target - len(current_words)
        while (remaining > 0 and selected_index + 1 < ayah_after
               and not scenes[selected_index + 1]["locked"]):
            next_words = scenes[selected_index + 1]["text"].split()
            take = min(remaining, len(next_words))
            current_words.extend(next_words[:take])
            remaining -= take
            leftover = next_words[take:]
            if leftover:
                scenes[selected_index + 1]["text"] = " ".join(leftover)
            else:
                scenes.pop(selected_index + 1)
                ayah_after -= 1
        target = len(current_words)

    scenes[selected_index]["text"] = " ".join(current_words)
    validated = _manual_scenes(ayahs, int(ayah_start), [
        {"ayah_number": scene["ayah_number"], "text": scene["text"],
         "scene_id": scene["scene_id"], "locked": scene["locked"]}
        for scene in scenes
    ])
    for index, scene in enumerate(validated):
        scene["scene_index"] = index
        scene["word_count"] = len(scene["text"].split())
    return {
        "scenes": validated,
        "selected_scene_index": selected_index,
        "word_count": len(validated[selected_index]["text"].split()),
        "min_words": 1,
        "max_words": max_words,
        "locked": validated[selected_index]["locked"],
    }


def merge_scene_with_previous(ayahs, scene_rows, *, ayah_start=1, scene_index):
    """Merge a scene with its immediately preceding scene in the same ayah."""
    try:
        selected_index = int(scene_index)
    except (TypeError, ValueError) as exc:
        raise ValueError("Scene index must be a whole number.") from exc
    scenes = _manual_scenes(ayahs, int(ayah_start), scene_rows)
    if selected_index <= 0 or selected_index >= len(scenes):
        raise ValueError("Choose a scene that has a previous scene to merge with.")
    current, previous = scenes[selected_index], scenes[selected_index - 1]
    if current["ayah_number"] != previous["ayah_number"]:
        raise ValueError("Scenes cannot be merged across ayah boundaries.")
    if current["locked"] or previous["locked"]:
        raise ValueError("Unlock both scenes before merging them.")
    previous["text"] = f"{previous['text']} {current['text']}"
    scenes.pop(selected_index)
    validated = _manual_scenes(ayahs, int(ayah_start), [
        {"ayah_number": scene["ayah_number"], "text": scene["text"],
         "scene_id": scene["scene_id"], "locked": scene["locked"]}
        for scene in scenes
    ])
    for index, scene in enumerate(validated):
        scene["scene_index"] = index
        scene["word_count"] = len(scene["text"].split())
    return {
        "scenes": validated,
        "selected_scene_index": selected_index - 1,
        "word_count": len(validated[selected_index - 1]["text"].split()),
    }


def split_scene_by_word_count(ayahs, scene_rows, *, ayah_start=1, scene_index,
                              words_per_scene):
    """Split one edited scene into exact-size word groups, preserving tokens."""
    if isinstance(words_per_scene, str) and not words_per_scene.isdecimal():
        raise ValueError("Words per scene must be a positive whole number.")
    try:
        selected_index = int(scene_index)
        limit = int(words_per_scene)
    except (TypeError, ValueError) as exc:
        raise ValueError("Scene index and words per scene must be whole numbers.") from exc
    if isinstance(words_per_scene, bool) or (isinstance(words_per_scene, float) and words_per_scene != limit):
        raise ValueError("Words per scene must be a whole number.")
    if not 1 <= limit <= 30:
        raise ValueError("Words per scene must be between 1 and 30.")
    scenes = _manual_scenes(ayahs, int(ayah_start), scene_rows)
    if selected_index < 0 or selected_index >= len(scenes):
        raise ValueError("The selected scene no longer exists.")
    selected = scenes[selected_index]
    if selected["locked"]:
        raise ValueError("Unlock this scene before splitting it.")
    words = selected["text"].split()
    if len(words) <= limit:
        raise ValueError("This scene already fits within the selected words-per-scene limit.")
    word_offset = sum(len(row["text"].split()) for row in scenes[:selected_index]
                      if row["ayah_number"] == selected["ayah_number"])
    replacements = [
        {"ayah_number": selected["ayah_number"],
         "text": " ".join(words[offset:offset + limit]),
         "scene_id": (selected["scene_id"] if offset == 0
                      else f"ayah-{selected['ayah_number']}-word-{word_offset + offset}"),
         "locked": False}
        for offset in range(0, len(words), limit)
    ]
    rows = [
        {"ayah_number": scene["ayah_number"], "text": scene["text"],
         "scene_id": scene["scene_id"], "locked": scene["locked"]}
        for scene in scenes[:selected_index]
    ] + replacements + [
        {"ayah_number": scene["ayah_number"], "text": scene["text"],
         "scene_id": scene["scene_id"], "locked": scene["locked"]}
        for scene in scenes[selected_index + 1:]
    ]
    validated = _manual_scenes(ayahs, int(ayah_start), rows)
    for index, scene in enumerate(validated):
        scene["scene_index"] = index
        scene["word_count"] = len(scene["text"].split())
    return {
        "scenes": validated,
        "selected_scene_index": selected_index,
        "word_counts": [len(row["text"].split()) for row in replacements],
    }


def set_scene_lock(ayahs, scene_rows, *, ayah_start=1, scene_index, locked):
    """Set the word-boundary lock on exactly one validated scene."""
    if not isinstance(locked, bool):
        raise ValueError("Scene lock state must be true or false.")
    try:
        selected_index = int(scene_index)
    except (TypeError, ValueError) as exc:
        raise ValueError("Scene index must be a whole number.") from exc
    scenes = _manual_scenes(ayahs, int(ayah_start), scene_rows)
    if selected_index < 0 or selected_index >= len(scenes):
        raise ValueError("The selected scene no longer exists.")
    scenes[selected_index]["locked"] = locked
    for index, scene in enumerate(scenes):
        scene["scene_index"] = index
    return {"scenes": scenes, "selected_scene_index": selected_index,
            "locked": locked, "scene_id": scenes[selected_index]["scene_id"]}


def edit_scene_text(ayahs, scene_rows, *, ayah_start=1, scene_index, text):
    """Set a scene to an exact contiguous sequence of its ayah's source words."""
    scenes = _manual_scenes(ayahs, int(ayah_start), scene_rows)
    try:
        selected_index = int(scene_index)
    except (TypeError, ValueError) as exc:
        raise ValueError("Scene index must be a whole number.") from exc
    if selected_index < 0 or selected_index >= len(scenes):
        raise ValueError("The selected scene no longer exists.")
    selected = scenes[selected_index]
    source_index = selected["ayah_number"] - int(ayah_start)
    group_start = selected_index
    while group_start > 0 and scenes[group_start - 1]["ayah_number"] == selected["ayah_number"]:
        group_start -= 1
    word_offset = sum(len(row["text"].split()) for row in scenes[group_start:selected_index])
    source_words = str(ayahs[source_index]).split()
    requested_words = str(text or "").split()
    if not requested_words:
        raise ValueError("A scene must contain at least one whole Quran word.")
    if source_words[word_offset:word_offset + len(requested_words)] != requested_words:
        raise ValueError("Enter the exact next words from this ayah, in their original order and spelling.")
    return redistribute_scene_words(
        ayahs, scenes, ayah_start=ayah_start, scene_index=selected_index,
        requested_word_count=len(requested_words),
    )


def _validated_word_times(text, timings, ayah_duration):
    words = text.split()
    if not isinstance(timings, (list, tuple)) or len(timings) != len(words):
        raise ValueError("Word timings must match the ayah's exact whitespace-delimited word count.")
    parsed = []
    previous_end = 0.0
    for index, row in enumerate(timings):
        try:
            start, end = float(row["start"]), float(row["end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Every word timing needs numeric start and end seconds.") from exc
        if (not isfinite(start) or not isfinite(end) or start < 0 or end <= start
                or start < previous_end or end > ayah_duration + .001):
            raise ValueError("Word timings are invalid, out of order, or outside the ayah audio span.")
        parsed.append({"word_index": index, "start": start, "end": end})
        previous_end = end
    return parsed


def _estimated_scene_durations(source_text, scene_texts, ayah_duration):
    """Estimate phrase spans by Arabic token length when word times are absent.

    This is deliberately labelled approximate. Token length and Quranic pause
    marks are a better fallback than equal scene durations, but they cannot
    replace timestamps measured from the selected recitation.
    """
    source_words = str(source_text).split()
    scene_counts = [len(str(text).split()) for text in scene_texts]
    if sum(scene_counts) != len(source_words):
        raise ValueError("Approximate scene timing requires every source word exactly once.")
    weights = []
    for word in source_words:
        letters = sum(char.isalpha() and not unicodedata.category(char).startswith("M")
                      for char in word)
        marks = sum(unicodedata.category(char).startswith("M") for char in word)
        pause_marks = sum(char in PREFERRED_BREAKS for char in word)
        weights.append(max(1.0, letters + marks * .3 + pause_marks * 2.0))
    total_weight = sum(weights)
    if total_weight <= 0:
        raise ValueError("The ayah contains no words for approximate scene timing.")
    durations = []
    cursor = 0
    elapsed_weight = 0.0
    for count in scene_counts:
        elapsed_weight += sum(weights[cursor:cursor + count])
        cursor += count
        boundary = float(ayah_duration) * elapsed_weight / total_weight
        previous = durations and sum(durations) or 0.0
        durations.append(max(0.001, boundary - previous))
    if durations:
        durations[-1] = float(ayah_duration) - sum(durations[:-1])
    if any(not isfinite(item) or item <= 0 for item in durations):
        raise ValueError("Approximate word-weight timing produced a non-positive scene interval.")
    return durations


def build_scene_plan(ayahs, *, ayah_start=1, durations=None, word_timings=None,
                     aspect_ratio="9:16", wrap_width=85, max_lines=5, font_path=None,
                     show_surah_title=False, padding_y=24, scene_overrides=None,
                     default_duration=3.0, output_size=None, words_per_scene=8,
                     preview_untimed_splits=False):
    """Plan word-count display scenes and their available audio timings.

    Exact phrase boundaries use validated word timestamps. If the editor
    supplies scene overrides and only ayah durations are available, scene
    spans use a clearly approximate Arabic-text-weighted estimate.
    """
    if aspect_ratio not in SIZES:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
    if not ayahs:
        raise ValueError("At least one ayah is required to plan scenes.")
    try:
        ayah_start = int(ayah_start)
        max_lines = max(1, min(8, int(max_lines)))
        wrap_width = int(wrap_width)
        words_per_scene = int(words_per_scene)
        width, height = output_size or SIZES[aspect_ratio]
        font_size = max(26, int(width * .07))
    except (TypeError, ValueError) as exc:
        raise ValueError("Scene layout settings must be valid numbers.") from exc
    if wrap_width not in {65, 75, 85, 95}:
        raise ValueError("Text wrap width must be 65, 75, 85, or 95 percent.")
    if words_per_scene not in range(1, 31):
        raise ValueError("Words per scene must be between 1 and 30.")
    if durations is not None and (len(durations) != len(ayahs)
                                  or any(not isfinite(float(item)) or float(item) <= 0 for item in durations)):
        raise ValueError("Audio timing must provide one positive duration for each ayah.")
    if word_timings is not None and len(word_timings) != len(ayahs):
        raise ValueError("Word timing data must provide one word list for each ayah.")

    max_width = int(width * wrap_width / 100)
    max_height = int(height * .44)
    chosen_font = Path(font_path) if font_path else DEFAULT_FONT
    if not chosen_font.exists():
        raise FileNotFoundError(f"Arabic font not found: {chosen_font}")
    font = load_arabic_font(chosen_font, font_size)
    line_limit = _effective_line_limit(
        requested=max_lines, font_size=font_size, max_height=max_height,
        show_surah_title=show_surah_title, padding_y=int(padding_y),
    )

    planned = []
    for index, ayah in enumerate(ayahs):
        source_text = str(ayah).strip()
        if not source_text:
            raise ValueError(f"Ayah {ayah_start + index} has no renderable words.")
        verse_duration = float(durations[index]) if durations is not None else float(default_duration)
        if not isfinite(verse_duration) or verse_duration <= 0:
            raise ValueError("Ayah duration must be positive and finite.")

        chunks = [source_text]
        parsed_times = None
        if word_timings is not None:
            parsed_times = _validated_word_times(source_text, word_timings[index], verse_duration)
            chunks = _split_scene_text(
                source_text, font=font, max_width=max_width,
                max_lines=line_limit, words_per_scene=words_per_scene,
            )
        elif preview_untimed_splits:
            chunks = _split_scene_text(
                source_text, font=font, max_width=max_width,
                max_lines=line_limit, words_per_scene=words_per_scene,
            )

        offsets = []
        if parsed_times is not None:
            word_cursor = 0
            for chunk in chunks:
                word_count = len(chunk.split())
                offsets.append((word_cursor, word_cursor + word_count))
                word_cursor += word_count
            if word_cursor != len(parsed_times):
                raise ValueError("The visual word split does not match the validated timing word count.")

        estimated_durations = None
        if parsed_times is None and durations is not None and len(chunks) > 1:
            estimated_durations = _estimated_scene_durations(source_text, chunks, verse_duration)
        word_offset = 0
        for part, chunk in enumerate(chunks, start=1):
            scene_word_count = len(chunk.split())
            scene = {
                "scene_index": len(planned),
                "scene_id": f"ayah-{ayah_start + index}-word-{word_offset}",
                "ayah_number": ayah_start + index,
                "segment_index": part,
                "segment_count": len(chunks),
                "text": chunk,
                "ayah_total_duration": verse_duration,
                "locked": False,
                "duration": (None if parsed_times is None and durations is None
                             and preview_untimed_splits and len(chunks) > 1
                             else estimated_durations[part - 1] if estimated_durations is not None
                             else verse_duration),
                "timing_mode": ("word_timing_pending" if parsed_times is None and durations is None
                                and preview_untimed_splits and len(chunks) > 1
                                else "weighted_estimate" if estimated_durations is not None
                                else "ayah_timestamp" if durations is not None
                                else "default_duration_estimate"),
                "timing_approximate": estimated_durations is not None,
                "word_count": scene_word_count,
                "word_start_index": word_offset,
                "word_end_index": word_offset + scene_word_count - 1,
            }
            if parsed_times is not None:
                first_word, after_last_word = offsets[part - 1]
                phrase_start = 0.0 if part == 1 else parsed_times[first_word]["start"]
                phrase_end = (parsed_times[offsets[part][0]]["start"]
                              if part < len(chunks) else verse_duration)
                if phrase_end <= phrase_start:
                    raise ValueError("Word timestamps do not provide positive chronological phrase durations.")
                scene.update({
                    "word_start_index": first_word,
                    "word_end_index": after_last_word - 1,
                    "duration": phrase_end - phrase_start,
                    "timing_mode": "word_timestamp",
                    "timing_approximate": False,
                })
            word_offset += len(chunk.split())
            planned.append(scene)

    scenes = planned
    if scene_overrides is not None:
        manual_scenes = _manual_scenes(ayahs, ayah_start, scene_overrides)
        for scene_number, scene in enumerate(manual_scenes, start=1):
            if len(wrap_arabic_lines(scene["text"], font, max_width)) > line_limit:
                raise ValueError(
                    f"Manual scene {scene_number} exceeds the selected line limit; split at a word boundary."
                )
        scenes = manual_scenes
        grouped = {}
        for scene in scenes:
            grouped.setdefault(scene["ayah_number"], []).append(scene)
        for ayah_number, group in grouped.items():
            source_index = ayah_number - ayah_start
            verse_duration = float(durations[source_index]) if durations is not None else float(default_duration)
            parsed_times = (_validated_word_times(ayahs[source_index], word_timings[source_index], verse_duration)
                            if word_timings is not None else None)
            estimated_durations = (_estimated_scene_durations(
                ayahs[source_index], [scene["text"] for scene in group], verse_duration,
            ) if parsed_times is None and durations is not None and len(group) > 1 else None)
            word_cursor = 0
            for scene_index, scene in enumerate(group):
                scene["ayah_total_duration"] = verse_duration
                count = len(scene["text"].split())
                if parsed_times is not None and len(group) > 1:
                    start = 0.0 if word_cursor == 0 else parsed_times[word_cursor]["start"]
                    word_cursor += count
                    end = (parsed_times[word_cursor]["start"] if word_cursor < len(parsed_times)
                           else verse_duration)
                    if end <= start:
                        raise ValueError("Word timestamps do not align with the manual word-boundary split.")
                    scene["word_start_index"] = word_cursor - count
                    scene["word_end_index"] = word_cursor - 1
                    scene["duration"] = end - start
                    scene["timing_mode"] = "word_timestamp"
                    scene["timing_approximate"] = False
                elif estimated_durations is not None:
                    scene["word_start_index"] = word_cursor
                    scene["word_end_index"] = word_cursor + count - 1
                    word_cursor += count
                    scene["duration"] = estimated_durations[scene_index]
                    scene["timing_mode"] = "weighted_estimate"
                    scene["timing_approximate"] = True
                elif parsed_times is None and durations is None and len(group) > 1:
                    scene["duration"] = None
                    scene["timing_mode"] = "word_timing_pending"
                    scene["timing_approximate"] = False
                else:
                    scene["duration"] = verse_duration
                    scene["timing_mode"] = "ayah_timestamp" if durations is not None else "default_duration_estimate"
                    scene["timing_approximate"] = False

    scenes_by_ayah = {}
    for index, scene in enumerate(scenes):
        scene["scene_index"] = index
        scenes_by_ayah.setdefault(int(scene["ayah_number"]), []).append(scene)

    cursor = 0.0
    for ayah_index, ayah in enumerate(ayahs):
        ayah_number = ayah_start + ayah_index
        group = scenes_by_ayah.get(ayah_number, [])
        verse_duration = float(durations[ayah_index]) if durations is not None else float(default_duration)
        parsed_times = (_validated_word_times(ayah, word_timings[ayah_index], verse_duration)
                        if word_timings is not None else None)
        if parsed_times is not None:
            word_cursor = 0
            for scene in group:
                count = len(scene["text"].split())
                first_word = word_cursor
                last_word = first_word + count - 1
                if count < 1 or last_word >= len(parsed_times):
                    raise ValueError("Scene word allocations do not match the exact audio word timestamps.")
                start = cursor + parsed_times[first_word]["start"]
                end = cursor + parsed_times[last_word]["end"]
                if end <= start:
                    raise ValueError("Word timestamps do not provide positive scene intervals.")
                scene.update({
                    "word_start_index": first_word,
                    "word_end_index": last_word,
                    "start_time": round(start, 3),
                    "end_time": round(end, 3),
                    "duration": round(end - start, 3),
                    "timing_mode": "word_timestamp",
                    "timing_approximate": False,
                })
                word_cursor += count
            if word_cursor != len(parsed_times):
                raise ValueError("Scene word allocations omit words from the exact audio timestamps.")
        elif durations is None and len(group) > 1:
            for scene in group:
                scene.update({"start_time": None, "end_time": None, "duration": None,
                              "timing_mode": "word_timing_pending", "timing_approximate": False})
        elif len(group) > 1 and durations is not None:
            estimated = _estimated_scene_durations(ayah, [scene["text"] for scene in group], verse_duration)
            scene_cursor = cursor
            for scene, duration in zip(group, estimated):
                scene.update({"start_time": round(scene_cursor, 3),
                              "end_time": round(scene_cursor + duration, 3),
                              "duration": duration, "timing_mode": "weighted_estimate",
                              "timing_approximate": True})
                scene_cursor += duration
        else:
            for scene in group:
                scene.update({"start_time": round(cursor, 3),
                              "end_time": round(cursor + verse_duration, 3),
                              "duration": verse_duration,
                              "timing_mode": "ayah_timestamp" if durations is not None else "default_duration_estimate",
                              "timing_approximate": False})
        cursor += verse_duration

    # Keep the automatic voice-derived timing intact as the reset baseline.
    # ``duration`` remains an individual caption length; absolute timeline
    # coordinates live only in start_time/end_time.
    for scene in scenes:
        automatic_duration = scene.get("duration")
        scene["automatic_duration"] = automatic_duration
        scene["automatic_start_time"] = scene.get("start_time")
        scene["automatic_end_time"] = scene.get("end_time")

    by_ayah = {}
    for scene in scenes:
        by_ayah.setdefault(int(scene["ayah_number"]), []).append(scene)
    manual_timeline = any(scene.get("manual_duration") is not None for scene in scenes)
    if manual_timeline:
        cursor = 0.0
        for scene in scenes:
            automatic = scene.get("automatic_duration")
            manual = scene.get("manual_duration")
            duration = float(manual) if manual is not None else automatic
            scene["duration"] = duration
            if duration is None:
                scene["start_time"] = scene["end_time"] = None
                continue
            start = cursor
            end = start + float(duration)
            scene["start_time"] = round(start, 3)
            scene["end_time"] = round(end, 3)
            cursor = end
            automatic_start = scene.get("automatic_start_time")
            automatic_end = scene.get("automatic_end_time")
            if automatic_start is not None and automatic_end is not None:
                start_shift = start - float(automatic_start)
                end_shift = end - float(automatic_end)
                if abs(start_shift) >= .01 or abs(end_shift) >= .01:
                    if abs(start_shift) >= .01:
                        relation = "after" if start_shift > 0 else "before"
                        scene["timing_warning"] = (
                            f"Manual scene timing shifts {abs(start_shift):.3f}s {relation} its voice timing."
                        )
                    else:
                        scene["timing_warning"] = (
                            f"Manual scene duration differs from its voice timing by {abs(end_shift):.3f}s."
                        )
    else:
        for group in by_ayah.values():
            exact_word_times = all(scene.get("timing_mode") == "word_timestamp" for scene in group)
            cursor = group[0].get("automatic_start_time")
            for scene in group:
                automatic = scene.get("automatic_duration")
                duration = automatic
                scene["duration"] = duration
                if duration is None or scene.get("automatic_start_time") is None:
                    scene["start_time"] = scene["end_time"] = None
                    continue
                if exact_word_times:
                    start = float(scene["automatic_start_time"])
                elif len(group) > 1:
                    start = float(cursor if cursor is not None else 0.0)
                else:
                    start = float(scene["automatic_start_time"] or 0.0)
                end = start + float(duration)
                scene["start_time"] = round(start, 3)
                scene["end_time"] = round(end, 3)
                if not exact_word_times:
                    cursor = end

    total_duration = sum(float(item) for item in durations) if durations is not None else None
    previous = None
    for scene in scenes:
        start, end, duration = scene.get("start_time"), scene.get("end_time"), scene.get("duration")
        if duration is None:
            continue
        if start is None or end is None:
            if scene.get("automatic_start_time") is None:
                # The editor can retain a manual individual duration before
                # recitation timings are loaded; absolute positions wait for
                # the audio timing endpoint or export planner.
                continue
            raise ValueError("Scene timing must have a positive duration and a valid absolute interval.")
        if (not isfinite(float(duration)) or float(duration) <= 0
                or not isfinite(float(start)) or not isfinite(float(end))
                or float(start) < 0
                or abs(float(end) - (float(start) + float(duration))) > .002):
            raise ValueError("Scene timing must have a positive duration and a valid absolute interval.")
        if total_duration is not None and float(end) > total_duration + .002:
            overrun = round(float(end) - total_duration, 3)
            scene["audio_overrun_seconds"] = overrun
            overrun_warning = (
                f"Caption remains visible {overrun:.3f}s after the selected recitation ends; "
                "Quran audio remains cropped to the selected range."
            )
            if scene.get("timing_warning"):
                scene["timing_warning"] += f" {overrun_warning}"
            else:
                scene["timing_warning"] = overrun_warning
        if previous is not None and float(start) < float(previous["end_time"]) - .002:
            raise ValueError(
                f"Timing for ayah {scene['ayah_number']} overlaps the previous caption. Shorten or reset one of the scene durations."
            )
        previous = scene
    return scenes
