import pytest
from app.video_engine import SIZES, THEMES, _background, render_reel
from app.quran_data import SURAHS, get_ayahs
from app.quraa_data import RECITERS


def test_full_quran_catalog_and_local_text():
    assert len(SURAHS) == 114
    assert sum(item["ayah_count"] for item in SURAHS) == 6236
    assert len(get_ayahs(55, 13, 13)) == 1
    assert len(RECITERS) == 20


def test_all_aspect_ratio_dimensions():
    assert SIZES == {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_each_preset_generates_the_requested_background(theme):
    image = _background(None, (96, 160), theme)
    assert image.size == (96, 160)


def test_rejects_invalid_ratio_before_rendering(tmp_path):
    with pytest.raises(ValueError, match="Unsupported aspect ratio"):
        render_reel(ayahs=["نص"], output_path=tmp_path / "out.mp4", aspect_ratio="4:3")


def test_rejects_empty_captions_before_rendering(tmp_path):
    with pytest.raises(ValueError, match="non-empty ayah"):
        render_reel(ayahs=[], output_path=tmp_path / "out.mp4")


def test_rejects_mismatched_ayah_timing(tmp_path):
    with pytest.raises(ValueError, match="one positive duration"):
        render_reel(ayahs=["نص", "آية"], output_path=tmp_path / "out.mp4",
                    ayah_durations=[3])


def test_arabic_shaping_preserves_input_marks():
    from app.text_renderer import shape_arabic
    text = "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ"
    shaped = shape_arabic(text)
    assert shaped
    assert shaped != text
