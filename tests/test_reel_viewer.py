import numpy as np

from app.reel_viewer import (
    format_ayah_range,
    render_playback_layer,
    render_static_layer,
    translation_for_ayah,
)


def test_static_viewer_layers_can_be_hidden_without_reserving_pixels():
    empty = render_static_layer(
        (540, 960), surah_name="Ar-Rahmaan", surah_number=55,
        ayah_number=13, reciter_name="Mishary Alafasy",
        translation="A supplied translation",
        options={"show_viewer_title": False, "show_translation": False,
                 "show_reciter_badge": False},
    )
    assert empty.mode == "RGBA"
    assert empty.getbbox() is None


def test_static_viewer_renders_optional_title_translation_and_reciter_layers():
    image = render_static_layer(
        (540, 960), surah_name="Ar-Rahmaan", surah_number=55,
        ayah_number=13, reciter_name="Mishary Alafasy",
        translation="So which of the favors of your Lord would you deny?",
        options={"show_viewer_title": True, "show_title_icon": False,
                 "show_translation": True, "translation_bg_enabled": True,
                 "show_reciter_badge": True},
    )
    assert image.getbbox() is not None
    assert np.asarray(image).shape == (960, 540, 4)


def test_playback_layer_uses_video_time_for_progress_and_animates_bars():
    settings = {"show_waveform": True, "waveform_style": "gold", "show_progress": True}
    early = render_playback_layer(.2, 2, (240, 426), settings)
    late = render_playback_layer(1.8, 2, (240, 426), settings)
    y = int(426 * .976) + 2
    # The same timeline pixel is still unplayed early and filled near the end.
    assert tuple(early[y, 190, :3]) != tuple(late[y, 190, :3])
    # Bar frames vary with the frame timestamp; they are a playback animation.
    assert not np.array_equal(early, late)


def test_custom_translation_lines_follow_the_actual_ayah_number():
    lines = ["first supplied translation", "", "third supplied translation"]
    assert translation_for_ayah(lines, 20, 20) == "first supplied translation"
    assert translation_for_ayah(lines, 21, 20) == ""
    assert translation_for_ayah(lines, 22, 20) == "third supplied translation"
    assert translation_for_ayah(lines, 19, 20) == ""


def test_header_ayah_range_formats_single_and_multiple_ayahs_in_both_languages():
    assert format_ayah_range(13, 13) == "Ayah 13"
    assert format_ayah_range(13, 15) == "Ayahs 13–15"
    assert format_ayah_range(15, 13, language="arabic") == "الآيات ١٣–١٥"
    assert format_ayah_range(13, 13, language="arabic", style="compact") == "١٣"
