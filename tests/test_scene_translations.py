from app.scenes import (
    merge_scene_with_previous,
    split_scene_by_word_count,
    split_translation_across_scenes,
    synchronize_scene_translations,
)


def test_two_scene_translation_splits_at_a_phrase_boundary():
    translation = "The first phrase, followed by another."
    segments = split_translation_across_scenes(translation, [2, 2])

    assert segments == ["The first phrase,", "followed by another."]
    assert " ".join(filter(None, segments)) == translation
    assert all(segment != translation for segment in segments)


def test_three_scene_translation_prefers_ordered_clause_boundaries():
    translation = "The first phrase, the second phrase; and the final words."
    segments = split_translation_across_scenes(translation, [2, 2, 2])

    assert segments == ["The first phrase,", "the second phrase;", "and the final words."]
    assert " ".join(filter(None, segments)) == translation


def test_translation_stays_attached_to_word_spans_when_scene_rows_are_reordered():
    translation = "The first phrase, the second phrase; and the final words."
    scenes = [
        {"scene_id": "second", "ayah_number": 55, "text": "ج د", "word_start_index": 2},
        {"scene_id": "first", "ayah_number": 55, "text": "أ ب", "word_start_index": 0},
        {"scene_id": "last", "ayah_number": 55, "text": "هـ و", "word_start_index": 4},
    ]

    synchronized = synchronize_scene_translations([*scenes], [translation], ayah_start=55)

    assert [scene["scene_id"] for scene in synchronized] == ["second", "first", "last"]
    by_id = {scene["scene_id"]: scene["translation_text"] for scene in synchronized}
    assert by_id == {
        "first": "The first phrase,",
        "second": "the second phrase;",
        "last": "and the final words.",
    }


def test_merge_split_and_selected_ayah_range_rebuild_translation_segments():
    ayahs = ["أ ب ج د هـ و", "ز ح ط ي ك ل"]
    scenes = [
        {"scene_id": "ayah-55-word-0", "ayah_number": 55, "text": "أ ب"},
        {"scene_id": "ayah-55-word-2", "ayah_number": 55, "text": "ج د"},
        {"scene_id": "ayah-55-word-4", "ayah_number": 55, "text": "هـ و"},
        {"scene_id": "ayah-56-word-0", "ayah_number": 56, "text": "ز ح ط ي ك ل"},
    ]
    translations = [
        "The first phrase, the second phrase; and the final words.",
        "A separate ayah keeps its own complete translation.",
    ]
    initial = synchronize_scene_translations(scenes, translations, ayah_start=55)

    merged = merge_scene_with_previous(ayahs, initial, ayah_start=55, scene_index=1)
    after_merge = synchronize_scene_translations(merged["scenes"], translations, ayah_start=55)
    assert len([scene for scene in after_merge if scene["ayah_number"] == 55]) == 2
    assert " ".join(scene["translation_text"] for scene in after_merge[:2]) == translations[0]
    assert after_merge[-1]["translation_text"] == translations[1]

    split = split_scene_by_word_count(
        ayahs, after_merge, ayah_start=55, scene_index=0, words_per_scene=2,
    )
    after_split = synchronize_scene_translations(split["scenes"], translations, ayah_start=55)
    assert len([scene for scene in after_split if scene["ayah_number"] == 55]) == 3
    assert " ".join(scene["translation_text"] for scene in after_split[:3]) == translations[0]
    assert after_split[-1]["translation_text"] == translations[1]


def test_disabling_translation_clears_all_scene_translation_text():
    scenes = [
        {"scene_id": "first", "ayah_number": 1, "text": "أ ب", "word_start_index": 0},
        {"scene_id": "second", "ayah_number": 1, "text": "ج د", "word_start_index": 2},
    ]
    translated = synchronize_scene_translations(scenes, ["The ayah translation."], ayah_start=1)

    disabled = synchronize_scene_translations(translated, [], ayah_start=1)

    assert [scene["translation_text"] for scene in disabled] == ["", ""]
