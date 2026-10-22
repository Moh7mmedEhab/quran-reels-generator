import pytest
import numpy as np
from app.video_engine import (QUALITY_PRESETS, SIZES, THEMES, _adjust_background_frame, _background, _fit_image,
                              _fit_video_clip, output_dimensions, render_reel)
from app.quran_data import SURAHS, get_ayahs
from app.quraa_data import RECITERS


def test_full_quran_catalog_and_local_text():
    assert len(SURAHS) == 114
    assert sum(item["ayah_count"] for item in SURAHS) == 6236
    assert len(get_ayahs(55, 13, 13)) == 1
    assert len(RECITERS) == 20


def test_all_aspect_ratio_dimensions():
    assert SIZES == {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}


@pytest.mark.parametrize("ratio,expected", [
    ("9:16", (1080, 1920)), ("16:9", (1920, 1080)), ("1:1", (1080, 1080)),
])
def test_export_resolution_presets_resolve_for_each_aspect(ratio, expected):
    assert output_dimensions(ratio, "1080p") == expected


def test_custom_resolution_must_match_ratio_and_be_even_and_bounded():
    assert output_dimensions("16:9", "custom", 1280, 720) == (1280, 720)
    with pytest.raises(ValueError, match="must match"):
        output_dimensions("9:16", "custom", 1280, 720)
    with pytest.raises(ValueError, match="even"):
        output_dimensions("1:1", "custom", 721, 721)
    with pytest.raises(ValueError, match="between 240 and 3840"):
        output_dimensions("1:1", "custom", 4096, 4096)


def test_encoder_quality_presets_have_real_different_settings():
    assert len({(item["preset"], item["crf"]) for item in QUALITY_PRESETS.values()}) == 4


def test_background_color_grade_controls_change_pixel_values():
    original = np.array([[[100, 120, 140]]], dtype=np.uint8)
    grayscale = _adjust_background_frame(original, background_saturation=0)
    assert grayscale[0, 0, 0] == grayscale[0, 0, 1] == grayscale[0, 0, 2]
    tinted = _adjust_background_frame(original, background_saturation=0,
                                       background_overlay_color="#0000ff",
                                       background_overlay_opacity=.5)
    assert tinted[0, 0, 2] > tinted[0, 0, 0]


def test_multiple_background_videos_render_as_a_playable_trimmed_sequence(tmp_path):
    from moviepy import AudioClip, ColorClip, VideoFileClip
    from app.media_validation import validate_rendered_output

    first, second, output_path = tmp_path / "first.mp4", tmp_path / "second.mp4", tmp_path / "sequence.mp4"
    for path, color in ((first, (25, 90, 125)), (second, (115, 65, 30))):
        source = ColorClip((96, 54), color=color, duration=1)
        background_tone = AudioClip(lambda t: .03 * np.sin(2 * np.pi * 120 * np.asarray(t)),
                                    duration=1, fps=44100)
        muxed = source.with_audio(background_tone)
        muxed.write_videofile(str(path), fps=12, codec="libx264", audio_codec="aac",
                              audio_fps=44100, preset="ultrafast", logger=None)
        muxed.close(); background_tone.close()
        source.close()

    audio_path = tmp_path / "tone.wav"
    audio = AudioClip(lambda t: .08 * np.sin(2 * np.pi * 440 * np.asarray(t)),
                      duration=1.5, fps=44100)
    audio.write_audiofile(str(audio_path), fps=44100, codec="pcm_s16le", logger=None)
    audio.close()
    metadata = render_reel(
        ayahs=["بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"], output_path=output_path,
        aspect_ratio="9:16", output_size=(240, 426), fps=24, quality="fast",
        audio_path=audio_path, audio_start=0, audio_end=1.5, ayah_durations=[1.5],
        background_audio_enabled=True, background_audio_volume=.08,
        background_brightness=1.08, background_contrast=.94,
        background_saturation=1.12, background_overlay_color="#102030",
        background_overlay_opacity=.06,
        background_clips=[
            {"path": first, "start": 0, "end": 1, "speed": 1,
             "transition": "cut", "transition_duration": 0},
            {"path": second, "start": 0, "end": 1, "speed": 1,
             "transition": "crossfade", "transition_duration": .2},
        ], background_loop=False, duration_per_ayah=1.5, transition="cut",
    )
    exported = VideoFileClip(str(output_path))
    try:
        assert metadata["width"] == 240 and metadata["height"] == 426
        assert exported.size == [240, 426]
        assert exported.duration == pytest.approx(1.5, abs=.08)
        assert exported.audio is not None
        before = exported.get_frame(.1).astype("int16")
        after = exported.get_frame(1.2).astype("int16")
        assert abs(int(before.mean()) - int(after.mean())) > 5
    finally:
        exported.close()
    assert validate_rendered_output(output_path, expected_size=(240, 426), require_audio=True)["playable"] is True


def test_independent_label_templates_render_separately_from_the_verse_panel():
    from app.video_engine import render_caption_image
    from app.font_catalog import resolve_font
    caption = render_caption_image(
        "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ", aspect_ratio="9:16",
        show_surah_title=True, show_ayah_number=True, surah_title="سُورَةُ الرَّحْمَٰنِ",
        ayah_number=13, surah_template="emerald_ribbon", ayah_number_template="emerald_circle",
        surah_color="#fff2ca", ayah_color="#f6e8bd",
        surah_font_path=resolve_font("kufi"), ayah_number_font_path=resolve_font("sans_bold"),
        surah_opacity=.72, ayah_number_opacity=.84,
        surah_placement="below", ayah_number_placement="above",
    )
    assert caption.mode == "RGBA"
    assert caption.width < 1080 and caption.height < 1920


def test_export_includes_optional_viewer_layers_and_timeline_progress(tmp_path):
    from moviepy import VideoFileClip

    output_path = tmp_path / "viewer-layers.mp4"
    metadata = render_reel(
        ayahs=["فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ"], output_path=output_path,
        aspect_ratio="9:16", output_size=(240, 426), fps=24, quality="fast",
        duration_per_ayah=1, ayah_start=13, show_surah_title=False,
        show_ayah_number=True, viewer_surah_name="Ar-Rahmaan", viewer_surah_number=55,
        reciter_name="Mishary Rashid Alafasy",
        translation_lines=["So which of the favors of your Lord would you deny?"],
        viewer_options={"show_viewer_title": True, "show_title_icon": True,
                        "show_translation": True, "show_waveform": True,
                        "waveform_style": "gold", "show_reciter_badge": True,
                        "show_progress": True, "progress_color": "#edbd36"},
    )
    exported = VideoFileClip(str(output_path))
    try:
        assert metadata["width"] == 240 and metadata["height"] == 426
        assert exported.duration == pytest.approx(1, abs=.08)
        early, late = exported.get_frame(.08), exported.get_frame(.92)
        progress_y = int(426 * .976) + 2
        assert late[progress_y, 200, 0] > late[progress_y, 200, 1]
        assert early[progress_y, 200, 1] >= early[progress_y, 200, 0]
    finally:
        exported.close()


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_each_preset_generates_the_requested_background(theme):
    image = _background(None, (96, 160), theme)
    assert image.size == (96, 160)


@pytest.mark.parametrize("fit_mode", ["cover", "contain", "stretch", "blurred"])
def test_uploaded_image_fit_modes_return_exact_output_dimensions(fit_mode):
    from PIL import Image
    source = Image.new("RGB", (320, 120), (30, 90, 140))
    assert _fit_image(source, (180, 320), fit_mode, .25, .75).size == (180, 320)


def test_cover_crop_respects_horizontal_focal_position():
    from PIL import Image
    source = Image.new("RGB", (200, 100))
    for x in range(source.width):
        for y in range(source.height):
            source.putpixel((x, y), (x, y, 0))
    left = _fit_image(source, (100, 100), "cover", 0, .5)
    right = _fit_image(source, (100, 100), "cover", 1, .5)
    assert left.getpixel((50, 50))[0] < right.getpixel((50, 50))[0]


def test_uploaded_image_motion_is_static_by_default_and_edge_safe_when_enabled():
    from PIL import Image, ImageDraw
    from app.video_engine import _motion_frames
    image = Image.new("RGB", (180, 320), (18, 30, 42))
    ImageDraw.Draw(image).rectangle((20, 35, 65, 90), fill=(220, 180, 90))
    static = _motion_frames(image)
    moving = _motion_frames(image, "cinematic_zoom", .65, steps=32)
    assert len(static) == 1
    assert np.array_equal(static[0], np.asarray(image))
    assert len(moving) == 32
    assert all(frame.shape == (320, 180, 3) for frame in moving)
    assert not np.array_equal(moving[0], moving[16])


def test_background_motion_has_a_delayed_smooth_ping_pong_cycle():
    from app.background_motion import image_animation_phase
    assert image_animation_phase(1, 8, 1, start_time=2) == 0
    assert image_animation_phase(2, 8, 1, start_time=2) == 0
    assert image_animation_phase(6, 8, 1, start_time=2) == pytest.approx(1)
    assert image_animation_phase(10, 8, 1, start_time=2) == pytest.approx(0)


def test_ambient_light_motion_is_optional_and_uses_a_soft_transparent_sprite():
    from app.background_motion import ambient_light_position
    from app.video_engine import _ambient_light_sprite

    assert ambient_light_position(0) == pytest.approx((.08, .12))
    assert ambient_light_position(1) == pytest.approx((.92, .67))
    sprite = _ambient_light_sprite((240, 426), .5)
    alpha = np.asarray(sprite.getchannel("A"))
    assert sprite.mode == "RGBA"
    assert 20 <= alpha.max() <= 22
    assert alpha.min() == 0


def test_ambient_light_is_composited_into_exported_video_when_enabled(tmp_path):
    from moviepy import VideoFileClip
    from PIL import Image

    image_path = tmp_path / "still.png"
    output_path = tmp_path / "atmosphere.mp4"
    Image.new("RGB", (120, 210), (25, 45, 70)).save(image_path)
    result = render_reel(
        ayahs=["آية كريمة"], output_path=output_path, aspect_ratio="9:16",
        output_size=(240, 426), fps=24, quality="fast", background_path=image_path,
        background_atmosphere_enabled=True, background_atmosphere_intensity=.7,
        background_atmosphere_duration=8, background_atmosphere_speed=2,
        duration_per_ayah=1.4,
    )
    video = VideoFileClip(str(output_path))
    try:
        first = video.get_frame(.1).astype("int16")
        later = video.get_frame(1.1).astype("int16")
        assert result["background_atmosphere_enabled"] is True
        assert result["background_atmosphere_intensity"] == pytest.approx(.7)
        assert np.abs(first - later).mean() > .1
    finally:
        video.close()


def test_ambient_light_controls_are_validated_even_when_disabled(tmp_path):
    with pytest.raises(ValueError, match="Atmospheric light intensity"):
        render_reel(ayahs=["آية"], output_path=tmp_path / "invalid.mp4",
                    background_atmosphere_intensity=1.5)


def test_mixed_image_and_video_background_sequence_renders_playably(tmp_path):
    from PIL import Image, ImageDraw
    from moviepy import ColorClip, VideoFileClip
    from app.media_validation import validate_rendered_output
    first_image, source_video, output_path = tmp_path / "first.png", tmp_path / "middle.mp4", tmp_path / "mixed.mp4"
    still = Image.new("RGB", (96, 160), (170, 115, 35))
    ImageDraw.Draw(still).rectangle((10, 10, 70, 100), fill=(230, 210, 110))
    still.save(first_image)
    clip = ColorClip((96, 54), color=(20, 110, 165), duration=.8)
    clip.write_videofile(str(source_video), fps=12, codec="libx264", audio=False,
                          preset="ultrafast", logger=None)
    clip.close()
    metadata = render_reel(
        ayahs=["بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"], output_path=output_path,
        aspect_ratio="9:16", output_size=(240, 426), fps=24, quality="fast",
        background_clips=[
            {"path":first_image, "duration":.7, "transition":"fade_black", "transition_duration":.2},
            {"path":source_video, "start":0, "end":.8, "speed":1,
             "transition":"crossfade", "transition_duration":.2},
        ], transitions_enabled=True, background_loop=False,
        duration_per_ayah=1.5, transition="cut",
    )
    exported = VideoFileClip(str(output_path))
    try:
        assert metadata["width"] == 240 and metadata["height"] == 426
        assert exported.duration == pytest.approx(1.5, abs=.08)
        image_frame = exported.get_frame(.15).astype("int16")
        video_frame = exported.get_frame(1.0).astype("int16")
        assert abs(int(image_frame.mean()) - int(video_frame.mean())) > 10
    finally:
        exported.close()
    assert validate_rendered_output(output_path, expected_size=(240, 426), require_audio=False)["playable"] is True


@pytest.mark.parametrize("style", ["cut", "crossfade", "dissolve", "fade_black", "fade_color",
                                     "slide_left", "slide_right", "zoom"])
def test_supported_background_transitions_render_without_gaps(tmp_path, style):
    from PIL import Image
    from moviepy import VideoFileClip
    from app.video_engine import render_reel
    first, second, output_path = tmp_path / "a.png", tmp_path / "b.png", tmp_path / f"{style}.mp4"
    Image.new("RGB", (80, 120), (20, 85, 130)).save(first)
    Image.new("RGB", (120, 80), (150, 65, 20)).save(second)
    result = render_reel(
        ayahs=["آية كريمة"], output_path=output_path, output_size=(240, 426),
        aspect_ratio="9:16", fps=24, quality="fast", transition="cut",
        background_clips=[
            {"path":first, "duration":.7, "transition":"cut", "transition_duration":0},
            {"path":second, "duration":.7, "transition":style, "transition_duration":.25},
        ], transitions_enabled=True, background_loop=False, duration_per_ayah=1.2,
        background_transition_color="#183040",
    )
    video = VideoFileClip(str(output_path))
    try:
        assert result["duration"] == pytest.approx(1.2)
        assert video.get_frame(.1).shape == (426, 240, 3)
        assert video.get_frame(1.1).shape == (426, 240, 3)
    finally:
        video.close()


def test_video_fit_modes_keep_frame_inside_target_without_stretching():
    from moviepy import ColorClip, vfx
    clip = ColorClip(size=(64, 32), color=(20, 40, 60), duration=1)
    try:
        cover, align = _fit_video_clip(clip, (40, 80), "cover", .5, .5, vfx)
        assert (int(cover.w), int(cover.h), align) == (40, 80, None)
        contain, align = _fit_video_clip(clip, (40, 80), "contain", .5, .5, vfx)
        assert contain.w == 40 and contain.h < 80 and align == "contain"
        blurred, align = _fit_video_clip(clip, (40, 80), "blurred", .5, .5, vfx)
        assert blurred.w == 40 and blurred.h < 80 and align == "contain"
        stretched, align = _fit_video_clip(clip, (40, 80), "stretch", .5, .5, vfx)
        assert (int(stretched.w), int(stretched.h), align) == (40, 80, None)
    finally:
        clip.close()


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


def test_rejects_unsupported_fps_and_quality(tmp_path):
    with pytest.raises(ValueError, match="Frame rate"):
        render_reel(ayahs=["نص"], output_path=tmp_path / "out.mp4", fps=50)
    with pytest.raises(ValueError, match="Quality"):
        render_reel(ayahs=["نص"], output_path=tmp_path / "out.mp4", quality="fake")


def test_arabic_shaping_preserves_input_marks():
    import unicodedata
    from app.text_renderer import shape_arabic
    text = "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ"
    shaped = shape_arabic(text)
    assert shaped
    input_marks = sum(unicodedata.category(char) == "Mn" for char in text)
    output_marks = sum(unicodedata.category(char) == "Mn" for char in shaped)
    assert output_marks == input_marks


def test_raqm_receives_logical_arabic_text_without_pre_shaping():
    from app.text_renderer import PIL_HAS_RAQM, shape_arabic
    text = "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ"
    if PIL_HAS_RAQM:
        assert shape_arabic(text) == text


def test_arabic_caption_font_uses_raqm_layout_when_available():
    from PIL import ImageFont
    from app.text_renderer import DEFAULT_FONT, PIL_HAS_RAQM, _load_font
    font = _load_font(DEFAULT_FONT, 56)
    if PIL_HAS_RAQM:
        assert font.layout_engine == ImageFont.Layout.RAQM


def test_long_ayah_scene_plan_preserves_every_uthmani_character():
    from app.scenes import build_scene_plan
    long_ayah = get_ayahs(2, 282, 282)[0]
    scenes = build_scene_plan([long_ayah], ayah_start=282, max_lines=4,
                              show_surah_title=True, default_duration=90)
    assert len(scenes) > 1
    assert all(scene["ayah_number"] == 282 for scene in scenes)
    assert [scene["segment_index"] for scene in scenes] == list(range(1, len(scenes) + 1))
    assert all(scene["timing_mode"] == "character_weighted_estimate" for scene in scenes)
    assert "".join(long_ayah.split()) == "".join("".join(scene["text"].split()) for scene in scenes)
    assert sum(scene["duration"] for scene in scenes) == pytest.approx(90)
    assert scenes[0]["start_time"] == 0
    assert scenes[-1]["end_time"] == pytest.approx(90)


def test_manual_scene_plan_only_accepts_order_preserving_splits():
    from app.scenes import build_scene_plan
    ayah = get_ayahs(55, 13, 13)[0]
    words = ayah.split()
    split = len(words) // 2
    scenes = build_scene_plan([ayah], ayah_start=13, scene_overrides=[
        {"ayah_number": 13, "text": " ".join(words[:split])},
        {"ayah_number": 13, "text": " ".join(words[split:])},
    ])
    assert len(scenes) == 2
    assert "".join(ayah.split()) == "".join("".join(scene["text"].split()) for scene in scenes)
    with pytest.raises(ValueError, match="preserve every character and its order"):
        build_scene_plan([ayah], ayah_start=13, scene_overrides=[
            {"ayah_number": 13, "text": " ".join(words[split:])},
            {"ayah_number": 13, "text": " ".join(words[:split])},
        ])


def test_manual_phrase_share_moves_scene_boundary_without_changing_ayah_duration():
    from app.scenes import build_scene_plan
    ayah = get_ayahs(55, 13, 13)[0]
    words = ayah.split()
    middle = len(words) // 2
    scenes = build_scene_plan([ayah], ayah_start=13, durations=[8.0], scene_overrides=[
        {"ayah_number":13,"text":" ".join(words[:middle]),"duration_fraction":.35},
        {"ayah_number":13,"text":" ".join(words[middle:]),"duration_fraction":.65},
    ])
    assert scenes[0]["duration"] == pytest.approx(2.8)
    assert scenes[0]["start_time"] == 0
    assert scenes[0]["end_time"] == pytest.approx(2.8)
    assert scenes[1]["start_time"] == pytest.approx(2.8)
    assert scenes[1]["end_time"] == pytest.approx(8.0)
    assert all(scene["timing_mode"] == "manual_fraction_estimate" for scene in scenes)
    with pytest.raises(ValueError, match="sum to 100%"):
        build_scene_plan([ayah], ayah_start=13, durations=[8.0], scene_overrides=[
            {"ayah_number":13,"text":" ".join(words[:middle]),"duration_fraction":.35},
            {"ayah_number":13,"text":" ".join(words[middle:]),"duration_fraction":.55},
        ])


def test_bundled_arabic_font_catalog_contains_multiple_readable_fonts():
    from app.font_catalog import FONT_CATALOG
    from PIL import ImageFont
    assert len(FONT_CATALOG) >= 4
    assert all(ImageFont.truetype(str(item["file"]), 64) for item in FONT_CATALOG.values())
