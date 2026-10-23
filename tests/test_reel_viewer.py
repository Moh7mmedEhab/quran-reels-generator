import numpy as np
import pytest
from PIL import Image

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


@pytest.mark.parametrize("style", ["gold", "white", "glow", "minimal"])
@pytest.mark.parametrize("size", [(360, 640), (1920, 1080), (1000, 1000)])
def test_waveform_position_offsets_apply_to_every_style_and_canvas_size(style, size):
    width, height = size
    base = render_playback_layer(.4, 2, size, {
        "show_waveform": True, "show_progress": False,
        "waveform_style": style, "waveform_count": 13,
    })
    moved = render_playback_layer(.4, 2, size, {
        "show_waveform": True, "show_progress": False,
        "waveform_style": style, "waveform_count": 13,
        "waveform_x_offset": 12, "waveform_y_offset": -8,
    })
    later = render_playback_layer(1.3, 2, size, {
        "show_waveform": True, "show_progress": False,
        "waveform_style": style, "waveform_count": 13,
        "waveform_x_offset": 12, "waveform_y_offset": -8,
    })
    base_box = Image.fromarray(base).getchannel("A").getbbox()
    moved_box = Image.fromarray(moved).getchannel("A").getbbox()
    assert base_box and moved_box
    base_center_x = (base_box[0] + base_box[2]) / 2
    moved_center_x = (moved_box[0] + moved_box[2]) / 2
    base_center_y = (base_box[1] + base_box[3]) / 2
    moved_center_y = (moved_box[1] + moved_box[3]) / 2
    assert moved_center_x - base_center_x == pytest.approx(width * .12, abs=1.5)
    assert moved_center_y - base_center_y == pytest.approx(-height * .08, abs=1.5)
    assert not np.array_equal(moved, later)
    shift_x = round(moved_center_x - base_center_x)
    shift_y = round(moved_center_y - base_center_y)
    assert np.array_equal(np.roll(moved, shift=(-shift_y, -shift_x), axis=(0, 1)), base)


def test_waveform_position_defaults_match_original_canvas_position():
    default = render_playback_layer(.5, 2, (400, 800), {
        "show_waveform": True, "show_progress": False, "waveform_style": "minimal",
    })
    explicit_default = render_playback_layer(.5, 2, (400, 800), {
        "show_waveform": True, "show_progress": False, "waveform_style": "minimal",
        "waveform_x_offset": 0, "waveform_y_offset": 0,
    })
    assert np.array_equal(default, explicit_default)


@pytest.mark.parametrize("size", [(240, 426), (1920, 1080), (1000, 1000)])
@pytest.mark.parametrize("x_offset,y_offset", [(-28, -65), (28, 27)])
def test_waveform_extreme_positions_remain_on_the_video_canvas(size, x_offset, y_offset):
    width, height = size
    frame = render_playback_layer(.5, 2, size, {
        "show_waveform": True, "show_progress": False,
        "waveform_style": "minimal", "waveform_count": 17,
        "waveform_x_offset": x_offset, "waveform_y_offset": y_offset,
    })
    bounds = Image.fromarray(frame).getchannel("A").getbbox()
    assert bounds is not None
    assert 0 < bounds[0] and bounds[2] < width
    assert 0 < bounds[1] and bounds[3] < height


def test_waveform_offsets_do_not_move_or_change_the_progress_track():
    base = render_playback_layer(.7, 2, (360, 640), {
        "show_waveform": False, "show_progress": True,
    })
    offset = render_playback_layer(.7, 2, (360, 640), {
        "show_waveform": False, "show_progress": True,
        "waveform_x_offset": 35, "waveform_y_offset": 27,
    })
    assert np.array_equal(base, offset)


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
