import pytest

from app import create_app
from app.quran_data import get_ayahs
from app.scenes import plan_auto_split_scenes, split_tall_ayah_into_lines
from app.text_renderer import DEFAULT_FONT, load_arabic_font, measure_arabic_line_width


class TestConfig:
    TESTING = True
    RENDER_JOBS_INLINE = True
    SECRET_KEY = "test"
    OUTPUT_FOLDER = "/tmp/quran-reels-auto-split-test-output"
    ARABIC_FONT = "/tmp/missing-font.ttf"


def test_auto_split_uses_shaped_font_width_and_preserves_exact_arabic_word_order():
    ayah = get_ayahs(2, 255, 255)[0]
    font = load_arabic_font(DEFAULT_FONT, 62)
    result = split_tall_ayah_into_lines(ayah, font=font, max_width=760, stroke_width=2)

    assert result["is_tall"] is True
    assert result["needs_split"] is True
    assert result["minimum_met"] is True
    assert " ".join(" ".join(result["chunks"]).split()) == " ".join(ayah.split())
    assert all(len(chunk.split()) >= 3 for chunk in result["chunks"])
    assert all(measure_arabic_line_width(chunk, font, 2) <= 760 for chunk in result["chunks"])


def test_auto_split_leaves_short_fitting_ayah_unchanged():
    ayah = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    font = load_arabic_font(DEFAULT_FONT, 48)
    result = split_tall_ayah_into_lines(ayah, font=font, max_width=1000)

    assert result["chunks"] == [ayah]
    assert result["needs_split"] is False


def test_auto_split_prefers_readable_whole_words_when_three_word_lines_are_impossible():
    word = "مُسْتَطِيلَاتٌ"
    ayah = " ".join([word] * 6)
    font = load_arabic_font(DEFAULT_FONT, 64)
    width_two_words = measure_arabic_line_width(f"{word} {word}", font)
    width_three_words = measure_arabic_line_width(f"{word} {word} {word}", font)
    result = split_tall_ayah_into_lines(ayah, font=font,
                                       max_width=(width_two_words + width_three_words) // 2)

    assert result["needs_split"] is True
    assert result["minimum_met"] is False
    assert [len(chunk.split()) for chunk in result["chunks"]] == [2, 2, 2]
    assert " ".join(" ".join(result["chunks"]).split()) == ayah


def test_auto_split_scene_rows_keep_source_ayah_numbers_and_one_line_chunks():
    ayahs = ["بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", get_ayahs(2, 255, 255)[0]]
    font = load_arabic_font(DEFAULT_FONT, 62)
    result = plan_auto_split_scenes(ayahs, ayah_start=13, font=font, max_width=760)

    assert result["split_ayahs"] == [14]
    assert [row["ayah_number"] for row in result["scenes"] if row["ayah_number"] == 13] == [13]
    assert all(row["ayah_number"] == 14 for row in result["scenes"] if row["ayah_number"] != 13)
    assert all("\n" not in row["text"] for row in result["scenes"])


def test_auto_split_route_returns_measured_editable_scene_rows():
    client = create_app(TestConfig).test_client()
    ayah = get_ayahs(2, 255, 255)[0]
    translation = "Allah there is no deity except Him the Ever-Living the Sustainer."
    response = client.post("/api/scenes/auto-split", json={
        "ayahs":[ayah], "ayah_start":255, "aspect_ratio":"9:16",
        "resolution":"1080p", "wrap_width":85, "font_id":"naskh",
        "template_id":"cinematic_nature", "caption_style":"quranic",
        "caption_color":"white", "show_surah_title":False,
        "show_ayah_number":False, "translation_lines":[translation],
    })

    assert response.status_code == 200
    result = response.get_json()
    assert result["split_ayahs"] == [255]
    assert result["minimum_arabic_words"] == 3
    assert result["layout"]["dimensions"] == [1080, 1920]
    assert len(result["scenes"]) > 1
    assert all(scene["ayah_number"] == 255 and scene["locked"] is False for scene in result["scenes"])
    assert "translation_text" in result["scenes"][0]
    translated_chunks = [scene["translation_text"] for scene in result["scenes"]]
    assert len(set(translated_chunks)) > 1
    assert " ".join(" ".join(translated_chunks).split()) == translation

    saved_rows = [{key:scene[key] for key in ("scene_id", "ayah_number", "text", "locked")}
                  for scene in result["scenes"]]
    restored = client.post("/api/scenes/plan", json={
        "ayahs":[ayah], "ayah_start":255, "aspect_ratio":"9:16",
        "resolution":"1080p", "wrap_width":85, "font_id":"naskh",
        "template_id":"cinematic_nature", "words_per_scene":8,
        "scene_edits":[{"ayah_number":255, "source_text":ayah, "scenes":saved_rows}],
        "translation_lines":[translation],
    })
    assert restored.status_code == 200
    restored_result = restored.get_json()
    assert restored_result["saved_edit_ayah_count"] == 1
    assert [scene["text"] for scene in restored_result["scenes"]] == [scene["text"] for scene in result["scenes"]]


@pytest.mark.parametrize("payload", [
    {"ayahs":[]},
    {"ayahs":["النَّصُّ"], "template_id":"missing"},
    {"ayahs":["النَّصُّ"], "wrap_width":42},
])
def test_auto_split_route_rejects_invalid_layout_requests(payload):
    client = create_app(TestConfig).test_client()
    response = client.post("/api/scenes/auto-split", json=payload)
    assert response.status_code == 400
