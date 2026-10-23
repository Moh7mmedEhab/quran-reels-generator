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
    assert len(RECITERS) == 27


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


def test_nvenc_command_uses_hardware_encoder_and_maps_mixed_audio(tmp_path):
    from app.ffmpeg_encoder import build_nvenc_command
    command = build_nvenc_command(
        "/usr/bin/ffmpeg", width=720, height=1280, fps=30,
        output_path=tmp_path / "out.mp4", audio_path=tmp_path / "audio.wav",
        crf=23, audio_bitrate="192k", audio_fps=48000,
    )
    assert "h264_nvenc" in command
    assert "p4" in command
    assert str(tmp_path / "audio.wav") in command
    assert command[-1] == str(tmp_path / "out.mp4")


def test_nvenc_broken_pipe_cleanup_preserves_ffmpeg_error(monkeypatch, tmp_path):
    import io
    import app.ffmpeg_encoder as encoder_module

    class BrokenPipe:
        closed = False

        def write(self, _frame):
            raise BrokenPipeError("FFmpeg exited")

        def close(self):
            raise BrokenPipeError("pipe close also failed")

    class FailedProcess:
        stdin = BrokenPipe()
        stderr = io.BytesIO(b"encoder exited with an NVENC error\n")

        def poll(self):
            return 1

        def wait(self, timeout=None):
            return 1

        def terminate(self):
            raise AssertionError("an exited process must not be terminated")

        def kill(self):
            raise AssertionError("an exited process must not be killed")

    process = FailedProcess()
    monkeypatch.setattr(encoder_module.subprocess, "Popen", lambda *args, **kwargs: process)

    class Clip:
        size = (240, 426)
        duration = 1
        audio = None

        def iter_frames(self, **kwargs):
            yield np.zeros((426, 240, 3), dtype=np.uint8)

    with pytest.raises(RuntimeError, match="encoder exited with an NVENC error"):
        encoder_module.write_hardware_video(
            Clip(), tmp_path / "broken.mp4", fps=24, ffmpeg="ffmpeg",
            encoder="nvidia", crf=23, audio_bitrate="192k", audio_fps=48000,
        )


def test_nvenc_cancellation_stops_process_and_removes_temporary_audio(monkeypatch, tmp_path):
    import io
    import threading
    from pathlib import Path
    import app.ffmpeg_encoder as encoder_module
    from app.job_errors import JobCancelled

    class Pipe:
        closed = False

        def close(self):
            self.closed = True

    class RunningProcess:
        stdin = Pipe()
        stderr = io.BytesIO()
        returncode = None
        terminated = False

        def poll(self):
            return self.returncode

        def terminate(self):
            self.terminated = True
            self.returncode = -15

        def wait(self, timeout=None):
            return self.returncode

    process = RunningProcess()
    monkeypatch.setattr(encoder_module.subprocess, "Popen", lambda *args, **kwargs: process)
    cancel_event = threading.Event()
    cancel_event.set()

    class Audio:
        def write_audiofile(self, path, **kwargs):
            Path(path).write_bytes(b"temporary pcm")

    class Clip:
        size = (240, 426)
        duration = 1
        audio = Audio()

        def iter_frames(self, **kwargs):
            yield np.zeros((426, 240, 3), dtype=np.uint8)

    output = tmp_path / "cancelled.mp4"
    audio_path = output.with_name("cancelled_nvidia_audio.wav")
    with pytest.raises(JobCancelled):
        encoder_module.write_hardware_video(
            Clip(), output, fps=24, ffmpeg="ffmpeg", encoder="nvidia",
            crf=23, audio_bitrate="192k", audio_fps=48000,
            cancel_event=cancel_event,
        )
    assert process.terminated
    assert process.stdin.closed
    assert not audio_path.exists()


def test_intel_qsv_command_uses_hardware_encoder_and_nv12(tmp_path):
    from app.ffmpeg_encoder import build_qsv_command
    command = build_qsv_command(
        "/usr/bin/ffmpeg", width=720, height=1280, fps=30,
        output_path=tmp_path / "out.mp4", audio_path=None,
        crf=23, audio_bitrate="192k", audio_fps=48000,
    )
    assert "h264_qsv" in command
    assert "format=nv12" in command
    assert command[-1] == str(tmp_path / "out.mp4")


def test_nvidia_render_fails_early_with_actionable_capability_error(monkeypatch, tmp_path):
    import app.ffmpeg_encoder as encoder_module
    monkeypatch.setattr(encoder_module, "hardware_encoder_status", lambda: {
        "ffmpeg": "/usr/bin/ffmpeg",
        "nvidia": {"available": False, "name": "NVIDIA NVENC", "reason": "Driver not active"},
        "intel": {"available": False, "name": "Intel UHD", "reason": "QSV unavailable"},
    })
    with pytest.raises(ValueError, match="NVIDIA NVENC is unavailable.*Driver not active"):
        render_reel(ayahs=["آية"], output_path=tmp_path / "never.mp4", encoder="nvidia")


def test_auto_encoder_falls_back_to_x264_when_nvenc_fails_during_render(monkeypatch, tmp_path):
    import app.ffmpeg_encoder as encoder_module

    monkeypatch.setattr(encoder_module, "hardware_encoder_status", lambda: {
        "ffmpeg": "/usr/bin/ffmpeg",
        "nvidia": {"available": True, "name": "Quadro T2000", "gpu_index": 0},
        "intel": {"available": False, "name": "Intel UHD", "reason": "No media device"},
    })

    def fail_nvenc(*args, **kwargs):
        raise RuntimeError("mock NVENC encode failure")

    monkeypatch.setattr(encoder_module, "write_hardware_video", fail_nvenc)
    output = tmp_path / "fallback.mp4"
    result = render_reel(
        ayahs=["بِسْمِ اللَّهِ"], output_path=output, aspect_ratio="9:16",
        output_size=(240, 426), fps=24, quality="fast", duration_per_ayah=.5,
        encoder="auto", show_surah_title=False,
    )
    assert output.is_file() and output.stat().st_size > 1024
    assert result["requested_encoder"] == "auto"
    assert result["encoder"] == "cpu"
    assert "mock NVENC encode failure" in result["fallback_reason"]


def test_intel_render_fails_early_when_quick_sync_is_unavailable(monkeypatch, tmp_path):
    import app.ffmpeg_encoder as encoder_module
    monkeypatch.setattr(encoder_module, "hardware_encoder_status", lambda: {
        "ffmpeg": "/usr/bin/ffmpeg",
        "nvidia": {"available": False, "name": "NVIDIA NVENC", "reason": "No CUDA"},
        "intel": {"available": False, "name": "Intel UHD · Quick Sync", "reason": "No media device"},
    })
    with pytest.raises(ValueError, match="Intel UHD.*No media device"):
        render_reel(ayahs=["آية"], output_path=tmp_path / "never.mp4", encoder="intel")


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


def test_long_translation_wraps_beneath_arabic_and_stays_inside_caption_safe_height():
    from app.video_engine import render_caption_image

    ayah = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    canvas = (240, 426)
    arabic_only = render_caption_image(ayah, aspect_ratio="9:16", output_size=canvas)
    combined = render_caption_image(
        ayah, aspect_ratio="9:16", output_size=canvas,
        translation_text="A source translation with a long sentence that wraps cleanly across lines. " * 4,
        translation_options={"translation_font": "serif", "translation_size": .026,
                             "translation_align": "left", "translation_wrap_width": .55},
        max_height_ratio=.5,
    )
    assert combined.width <= canvas[0]
    assert combined.height <= canvas[1] * .5
    assert combined.height > arabic_only.height


def test_obsolete_translation_credit_setting_does_not_add_caption_text():
    from app.video_engine import render_caption_image

    ayah = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    settings = {"translation_font": "serif", "translation_size": .026,
                "translation_align": "center", "translation_wrap_width": .85}
    plain = render_caption_image(
        ayah, aspect_ratio="9:16", output_size=(240, 426),
        translation_text="In the name of Allah, the Entirely Merciful, the Especially Merciful.",
        translation_options=settings,
    )
    with_legacy_credit = render_caption_image(
        ayah, aspect_ratio="9:16", output_size=(240, 426),
        translation_text="In the name of Allah, the Entirely Merciful, the Especially Merciful.",
        translation_options={**settings, "translation_credit": "Saheeh AI"},
    )
    assert plain.tobytes() == with_legacy_credit.tobytes()


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


def test_translation_splits_across_export_scenes_and_export_audio_is_cropped(tmp_path, monkeypatch):
    import math
    import struct
    import wave
    from app import video_engine
    from moviepy import VideoFileClip

    source_rate = 44100
    source_samples = []
    for index in range(source_rate * 3):
        seconds = index / source_rate
        frequency = 440 if .5 <= seconds < 1.5 else 880 if 1.5 <= seconds < 2.5 else 220
        source_samples.append(int(9000 * math.sin(2 * math.pi * frequency * seconds)))
    audio_path = tmp_path / "timing-source.wav"
    with wave.open(str(audio_path), "wb") as source:
        source.setnchannels(1)
        source.setsampwidth(2)
        source.setframerate(source_rate)
        source.writeframes(struct.pack(f"<{len(source_samples)}h", *source_samples))

    arabic = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    word_times = [[
        {"start": .1, "end": .35}, {"start": .5, "end": .75},
        {"start": 1.0, "end": 1.25}, {"start": 1.5, "end": 1.75},
    ]]
    rendered_translations = []
    original_caption_renderer = video_engine.render_caption_image

    def record_translation(*args, **kwargs):
        rendered_translations.append(kwargs.get("translation_text", ""))
        return original_caption_renderer(*args, **kwargs)

    monkeypatch.setattr(video_engine, "render_caption_image", record_translation)
    output_path = tmp_path / "translation-split.mp4"
    metadata = video_engine.render_reel(
        ayahs=[arabic], output_path=output_path, aspect_ratio="9:16",
        output_size=(240, 426), fps=24, quality="fast", encoder="cpu",
        audio_path=audio_path, audio_start=.5, audio_end=2.5,
        ayah_durations=[2], word_timings=word_times, ayah_start=13,
        words_per_scene=2,
        translation_lines=["The verified phrase, followed by its closing words."],
        viewer_options={"show_viewer_title": False, "show_translation": True,
                       "show_waveform": False, "show_reciter_badge": False,
                       "show_progress": False},
    )
    assert rendered_translations == ["The verified phrase,", "followed by its closing words."]
    assert " ".join(rendered_translations) == "The verified phrase, followed by its closing words."
    assert metadata["duration"] == pytest.approx(2)
    assert metadata["scene_count"] == 2

    exported = VideoFileClip(str(output_path))
    try:
        assert exported.duration == pytest.approx(2, abs=.08)
        assert exported.audio is not None
        samples = exported.audio.to_soundarray(fps=source_rate).mean(axis=1)
        assert len(samples) / source_rate == pytest.approx(2, abs=.08)
        first = samples[int(.15 * source_rate):int(.4 * source_rate)]
        last = samples[int(1.6 * source_rate):int(1.85 * source_rate)]
        first_frequency = np.fft.rfftfreq(len(first), 1 / source_rate)[np.argmax(np.abs(np.fft.rfft(first)))]
        last_frequency = np.fft.rfftfreq(len(last), 1 / source_rate)[np.argmax(np.abs(np.fft.rfft(last)))]
        assert first_frequency == pytest.approx(440, abs=15)
        assert last_frequency == pytest.approx(880, abs=15)
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


def test_long_ayah_without_word_timing_stays_whole_for_its_ayah_duration():
    from app.scenes import build_scene_plan
    long_ayah = get_ayahs(2, 282, 282)[0]
    scenes = build_scene_plan([long_ayah], ayah_start=282, max_lines=4,
                              show_surah_title=True, default_duration=90)
    assert len(scenes) == 1
    assert scenes[0]["ayah_number"] == 282
    assert scenes[0]["segment_index"] == scenes[0]["segment_count"] == 1
    assert scenes[0]["timing_mode"] == "default_duration_estimate"
    assert scenes[0]["text"] == long_ayah
    assert sum(scene["duration"] for scene in scenes) == pytest.approx(90)
    assert scenes[0]["start_time"] == 0
    assert scenes[-1]["end_time"] == pytest.approx(90)


def test_word_boundary_split_preserves_arabic_marks_punctuation_and_repeated_words():
    from app.scenes import split_ayah_at_word_boundaries
    ayah = "قُلْ هُوَ اللَّهُ أَحَدٌ ۚ قُلْ هُوَ اللَّهُ"
    parts = split_ayah_at_word_boundaries(ayah, max_words=3, max_characters=100)
    assert all(1 <= len(part.split()) <= 3 for part in parts)
    assert "".join(ayah.split()) == "".join("".join(part.split()) for part in parts)
    assert sum(part.split().count("قُلْ") for part in parts) == 2
    assert any(part.endswith("ۚ") for part in parts)


def test_word_timestamps_are_required_for_automatic_phrase_scene_timing():
    from app.scenes import build_scene_plan
    ayah = " ".join(["بِسْمِ", "اللَّهِ", "الرَّحْمَٰنِ", "الرَّحِيمِ"] * 8)
    word_times = [[{"start": index * .5, "end": index * .5 + .4}
                   for index, _ in enumerate(ayah.split())]]
    scenes = build_scene_plan([ayah], durations=[30], word_timings=word_times,
                              output_size=(240, 426), max_lines=1, wrap_width=65)
    assert len(scenes) > 1
    assert all(scene["timing_mode"] == "word_timestamp" for scene in scenes)
    assert "".join(ayah.split()) == "".join("".join(scene["text"].split()) for scene in scenes)
    assert scenes[0]["start_time"] == pytest.approx(0)
    assert scenes[-1]["end_time"] == pytest.approx(word_times[0][-1]["end"])
    assert [scene["word_start_index"] for scene in scenes] == sorted(
        scene["word_start_index"] for scene in scenes
    )


def test_configured_word_count_sets_scene_boundaries_and_voice_timestamps_set_durations():
    from app.scenes import build_scene_plan
    ayah = "قُلْ هُوَ اللَّهُ أَحَدٌ " * 3
    words = ayah.split()
    word_times = [[{"start": index * .75, "end": index * .75 + .5}
                   for index in range(len(words))]]
    scenes = build_scene_plan(
        [ayah], durations=[20], word_timings=word_times, words_per_scene=4,
        output_size=(1080, 1920), wrap_width=95, max_lines=8,
    )
    assert [scene["word_count"] for scene in scenes] == [4, 4, 4]
    assert [scene["start_time"] for scene in scenes] == pytest.approx([0, 3, 6])
    assert [scene["end_time"] for scene in scenes] == pytest.approx([2.75, 5.75, 8.75])
    assert all(scene["timing_mode"] == "word_timestamp" for scene in scenes)
    assert "".join(ayah.split()) == "".join("".join(scene["text"].split()) for scene in scenes)


def test_manual_scene_durations_are_individual_and_shift_only_sequential_caption_positions():
    from app.scenes import build_scene_plan
    ayah = "أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ خَامِسٌ سَادِسٌ"
    words = ayah.split()
    rows = [
        {"scene_id":"part-1", "ayah_number":1, "text":" ".join(words[:2]), "manual_duration":11},
        {"scene_id":"part-2", "ayah_number":1, "text":" ".join(words[2:4]), "manual_duration":9},
        {"scene_id":"part-3", "ayah_number":1, "text":" ".join(words[4:]), "manual_duration":7.5},
    ]
    plan = build_scene_plan([ayah], durations=[40], scene_overrides=rows)
    assert [scene["duration"] for scene in plan] == pytest.approx([11, 9, 7.5])
    assert [scene["start_time"] for scene in plan] == pytest.approx([0, 11, 20])
    assert [scene["end_time"] for scene in plan] == pytest.approx([11, 20, 27.5])
    assert [scene["automatic_duration"] for scene in plan] != pytest.approx([11, 9, 7.5])

    rows[0]["manual_duration"] = 12
    changed = build_scene_plan([ayah], durations=[40], scene_overrides=rows)
    assert [scene["duration"] for scene in changed] == pytest.approx([12, 9, 7.5])
    assert [scene["start_time"] for scene in changed] == pytest.approx([0, 12, 21])
    assert [scene["end_time"] for scene in changed] == pytest.approx([12, 21, 28.5])

    # Reset just the second scene by omitting its manual override. Other edits
    # stay applied and the second scene returns to its original weighted span.
    rows[1].pop("manual_duration")
    reset_one = build_scene_plan([ayah], durations=[40], scene_overrides=rows)
    assert reset_one[0]["duration"] == pytest.approx(12)
    assert reset_one[1]["duration"] == pytest.approx(reset_one[1]["automatic_duration"])
    assert reset_one[2]["duration"] == pytest.approx(7.5)
    assert reset_one[2]["start_time"] == pytest.approx(reset_one[1]["end_time"])


@pytest.mark.parametrize("duration", [0, -1, "NaN", "inf", True, 3600.01])
def test_scene_manual_duration_rejects_invalid_values(duration):
    from app.scenes import build_scene_plan
    with pytest.raises(ValueError, match="Scene duration"):
        build_scene_plan(["أَوَّلٌ ثَانٍ"], durations=[4], scene_overrides=[
            {"ayah_number":1, "text":"أَوَّلٌ ثَانٍ", "manual_duration":duration},
        ])


@pytest.mark.parametrize("extension", [0, .1, 1.0])
def test_final_caption_can_outlast_selected_audio_without_changing_audio_timing(extension):
    from app.scenes import build_scene_plan

    audio_duration = 41.18
    requested_duration = audio_duration + extension
    plan = build_scene_plan(["أَوَّلٌ ثَانٍ"], ayah_start=29, durations=[audio_duration], scene_overrides=[
        {"scene_id":"final", "ayah_number":29, "text":"أَوَّلٌ ثَانٍ",
         "manual_duration":requested_duration},
    ])
    scene = plan[0]
    assert scene["automatic_duration"] == pytest.approx(audio_duration)
    assert scene["duration"] == pytest.approx(requested_duration)
    assert scene["start_time"] == pytest.approx(0)
    assert scene["end_time"] == pytest.approx(requested_duration)
    if extension:
        assert scene["audio_overrun_seconds"] == pytest.approx(extension)
        assert "Quran audio remains cropped" in scene["timing_warning"]
    else:
        assert "timing_warning" not in scene


def test_exact_word_timestamps_keep_caption_start_anchored_and_reject_overlap():
    from app.scenes import build_scene_plan
    ayah = "أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ"
    rows = [
        {"scene_id":"first", "ayah_number":1, "text":"أَوَّلٌ ثَانٍ", "manual_duration":.8},
        {"scene_id":"second", "ayah_number":1, "text":"ثَالِثٌ رَابِعٌ", "manual_duration":.7},
    ]
    words = [[{"start":.1,"end":.35},{"start":.55,"end":.9},
              {"start":1.2,"end":1.5},{"start":1.75,"end":2.05}]]
    plan = build_scene_plan([ayah], durations=[3], word_timings=words, scene_overrides=rows)
    assert [scene["duration"] for scene in plan] == pytest.approx([.8, .7])
    assert [scene["start_time"] for scene in plan] == pytest.approx([.1, 1.2])
    assert [scene["end_time"] for scene in plan] == pytest.approx([.9, 1.9])
    rows[0]["manual_duration"] = 1.3
    with pytest.raises(ValueError, match="overlaps the previous caption"):
        build_scene_plan([ayah], durations=[3], word_timings=words, scene_overrides=rows)


def test_untimed_word_count_preview_has_no_guessed_times_and_export_keeps_whole_ayah():
    from app.scenes import build_scene_plan
    ayah = "قُلْ هُوَ اللَّهُ أَحَدٌ " * 3
    preview = build_scene_plan(
        [ayah], words_per_scene=4, preview_untimed_splits=True,
        output_size=(1080, 1920), wrap_width=95, max_lines=8,
    )
    assert [scene["word_count"] for scene in preview] == [4, 4, 4]
    assert all(scene["duration"] is None and scene["start_time"] is None for scene in preview)
    exported = build_scene_plan([ayah], durations=[9], words_per_scene=4)
    assert len(exported) == 1
    assert exported[0]["text"] == ayah.strip()
    assert exported[0]["duration"] == 9
    assert exported[0]["timing_mode"] == "ayah_timestamp"


def test_invalid_word_timing_count_fails_closed():
    from app.scenes import build_scene_plan
    with pytest.raises(ValueError, match="exact whitespace-delimited word count"):
        build_scene_plan(["بِسْمِ اللَّهِ"], durations=[3], word_timings=[[
            {"start": 0, "end": 1},
        ]])


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
    with pytest.raises(ValueError, match="word boundaries"):
        build_scene_plan([ayah], ayah_start=13, scene_overrides=[
            {"ayah_number": 13, "text": words[0][:-1]},
            {"ayah_number": 13, "text": words[0][-1:] + " " + " ".join(words[1:])},
        ])


def test_manual_percentage_timing_is_rejected_and_ayah_timing_uses_labeled_weighted_split_estimates():
    from app.scenes import build_scene_plan
    ayah = get_ayahs(55, 13, 13)[0]
    words = ayah.split()
    middle = len(words) // 2
    overrides = [
        {"ayah_number":13,"text":" ".join(words[:middle])},
        {"ayah_number":13,"text":" ".join(words[middle:])},
    ]
    scenes = build_scene_plan([ayah], ayah_start=13, durations=[8.0], scene_overrides=overrides)
    assert len(scenes) == 2
    assert all(scene["timing_mode"] == "weighted_estimate" for scene in scenes)
    assert all(scene["timing_approximate"] is True for scene in scenes)
    assert sum(scene["duration"] for scene in scenes) == pytest.approx(8.0)
    assert scenes[0]["duration"] != pytest.approx(scenes[1]["duration"])
    overrides[0]["duration_fraction"] = .35
    with pytest.raises(ValueError, match="percentage timing is no longer supported"):
        build_scene_plan([ayah], ayah_start=13, durations=[8.0], scene_overrides=overrides)


def test_scene_word_redistribution_moves_exact_words_forward_and_backward_without_crossing_ayahs():
    from app.scenes import redistribute_scene_words
    ayahs = ["أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ خَامِسٌ سَادِسٌ", "سَابِعٌ ثَامِنٌ"]
    scenes = [
        {"ayah_number": 1, "text": "أَوَّلٌ ثَانٍ"},
        {"ayah_number": 1, "text": "ثَالِثٌ رَابِعٌ"},
        {"ayah_number": 1, "text": "خَامِسٌ سَادِسٌ"},
        {"ayah_number": 2, "text": ayahs[1]},
    ]

    grown_by_one = redistribute_scene_words(ayahs, scenes, scene_index=0, requested_word_count=3)
    assert [row["word_count"] for row in grown_by_one["scenes"][:3]] == [3, 1, 2]
    assert "".join(ayahs[0].split()) == "".join(
        "".join(row["text"].split()) for row in grown_by_one["scenes"][:3]
    )

    grown = redistribute_scene_words(ayahs, grown_by_one["scenes"], scene_index=0, requested_word_count=5)
    assert [row["text"] for row in grown["scenes"]] == [
        "أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ خَامِسٌ", "سَادِسٌ", ayahs[1],
    ]
    assert grown["word_count"] == 5 and grown["max_words"] == 6

    reduced_by_one = redistribute_scene_words(ayahs, grown["scenes"], scene_index=0, requested_word_count=4)
    assert [row["word_count"] for row in reduced_by_one["scenes"][:2]] == [4, 2]
    reduced = redistribute_scene_words(ayahs, reduced_by_one["scenes"], scene_index=0, requested_word_count=2)
    assert [row["text"] for row in reduced["scenes"]] == [
        "أَوَّلٌ ثَانٍ", "ثَالِثٌ رَابِعٌ خَامِسٌ سَادِسٌ", ayahs[1],
    ]
    assert "".join(ayahs[0].split()) == "".join(
        "".join(row["text"].split()) for row in reduced["scenes"][:2]
    )
    assert reduced["scenes"][2]["text"] == ayahs[1]


def test_scene_word_redistribution_maximum_never_crosses_ayah_boundary():
    from app.scenes import redistribute_scene_words
    ayahs = ["أَوَّلٌ ثَانٍ", "ثَالِثٌ رَابِعٌ"]
    scenes = [
        {"ayah_number":1,"text":"أَوَّلٌ"},
        {"ayah_number":1,"text":"ثَانٍ"},
        {"ayah_number":2,"text":ayahs[1]},
    ]
    with pytest.raises(ValueError, match="at most 2 words"):
        redistribute_scene_words(ayahs, scenes, scene_index=0, requested_word_count=99)
    result = redistribute_scene_words(ayahs, scenes, scene_index=0, requested_word_count=2)
    assert result["word_count"] == result["max_words"] == 2
    assert [scene["text"] for scene in result["scenes"]] == [ayahs[0], ayahs[1]]


def test_scene_word_redistribution_recomputes_limits_for_the_selected_scene():
    from app.scenes import redistribute_scene_words
    ayah = "أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ خَامِسٌ سَادِسٌ"
    scenes = [
        {"ayah_number":1,"text":"أَوَّلٌ ثَانٍ"},
        {"ayah_number":1,"text":"ثَالِثٌ رَابِعٌ"},
        {"ayah_number":1,"text":"خَامِسٌ سَادِسٌ"},
    ]
    middle = redistribute_scene_words([ayah], scenes, scene_index=1, requested_word_count=4)
    assert middle["selected_scene_index"] == 1
    assert middle["word_count"] == 4 and middle["max_words"] == 4
    with pytest.raises(ValueError, match="at most 4 words"):
        redistribute_scene_words([ayah], scenes, scene_index=1, requested_word_count=99)
    first = redistribute_scene_words([ayah], middle["scenes"], scene_index=0, requested_word_count=1)
    assert first["selected_scene_index"] == 0
    assert first["word_count"] == 1
    assert first["max_words"] == 6


def test_scene_word_redistribution_can_shrink_final_segment_and_obeys_explicit_locks():
    from app.scenes import redistribute_scene_words, set_scene_lock
    ayahs = ["أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ"]
    initial = [{"ayah_number": 1, "text": ayahs[0]}]
    split = redistribute_scene_words(ayahs, initial, scene_index=0, requested_word_count=2)
    assert [scene["word_count"] for scene in split["scenes"]] == [2, 2]
    assert "".join(ayahs[0].split()) == "".join(
        "".join(scene["text"].split()) for scene in split["scenes"]
    )

    reduced = redistribute_scene_words(ayahs, split["scenes"], scene_index=1, requested_word_count=1)
    assert [scene["word_count"] for scene in reduced["scenes"]] == [2, 1, 1]
    assert "".join(ayahs[0].split()) == "".join(
        "".join(scene["text"].split()) for scene in reduced["scenes"]
    )
    locked = set_scene_lock(ayahs, reduced["scenes"], scene_index=1, locked=True)
    with pytest.raises(ValueError, match="Unlock this scene"):
        redistribute_scene_words(ayahs, locked["scenes"], scene_index=1, requested_word_count=2)
    with pytest.raises(ValueError, match="at least one"):
        redistribute_scene_words(ayahs, split["scenes"], scene_index=0, requested_word_count=0)


def test_locked_scene_is_unchanged_when_previous_scene_grows_or_shrinks():
    from app.scenes import redistribute_scene_words, set_scene_lock
    ayah = "أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ خَامِسٌ سَادِسٌ"
    rows = [
        {"ayah_number":1,"scene_id":"first","text":"أَوَّلٌ ثَانٍ"},
        {"ayah_number":1,"scene_id":"protected","text":"ثَالِثٌ رَابِعٌ"},
        {"ayah_number":1,"scene_id":"last","text":"خَامِسٌ سَادِسٌ"},
    ]
    locked = set_scene_lock([ayah], rows, scene_index=1, locked=True)["scenes"]
    shrunk = redistribute_scene_words([ayah], locked, scene_index=0, requested_word_count=1)
    assert [scene["text"] for scene in shrunk["scenes"]] == [
        "أَوَّلٌ", "ثَانٍ", "ثَالِثٌ رَابِعٌ", "خَامِسٌ سَادِسٌ",
    ]
    assert shrunk["scenes"][2]["scene_id"] == "protected"
    assert shrunk["scenes"][2]["locked"] is True
    with pytest.raises(ValueError, match="at most 2 words"):
        redistribute_scene_words([ayah], locked, scene_index=0, requested_word_count=3)


def test_scene_text_edit_accepts_only_exact_next_source_words():
    from app.scenes import edit_scene_text
    ayah = "أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ خَامِسٌ"
    rows = [
        {"ayah_number":1,"scene_id":"first","text":"أَوَّلٌ ثَانٍ"},
        {"ayah_number":1,"scene_id":"second","text":"ثَالِثٌ رَابِعٌ خَامِسٌ"},
    ]
    edited = edit_scene_text([ayah], rows, scene_index=0, text="أَوَّلٌ ثَانٍ ثَالِثٌ")
    assert [scene["text"] for scene in edited["scenes"]] == ["أَوَّلٌ ثَانٍ ثَالِثٌ", "رَابِعٌ خَامِسٌ"]
    assert [scene["scene_id"] for scene in edited["scenes"]][0] == "first"
    with pytest.raises(ValueError, match="exact next words"):
        edit_scene_text([ayah], rows, scene_index=0, text="ثَانٍ أَوَّلٌ")


def test_word_redistribution_recalculates_scene_audio_boundaries_from_word_timestamps():
    from app.scenes import build_scene_plan, redistribute_scene_words
    ayah = "أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ خَامِسٌ سَادِسٌ"
    source_rows = [
        {"ayah_number":1,"text":"أَوَّلٌ ثَانٍ"},
        {"ayah_number":1,"text":"ثَالِثٌ رَابِعٌ"},
        {"ayah_number":1,"text":"خَامِسٌ سَادِسٌ"},
    ]
    timings = [[{"start": .2 + index * .5, "end": .45 + index * .5} for index in range(6)]]
    allocation = redistribute_scene_words([ayah], source_rows, scene_index=0, requested_word_count=4)
    plan = build_scene_plan([ayah], durations=[4], word_timings=timings,
                            scene_overrides=allocation["scenes"])
    assert [scene["word_start_index"] for scene in plan] == [0, 4]
    assert [scene["start_time"] for scene in plan] == pytest.approx([.2, 2.2])
    assert [scene["end_time"] for scene in plan] == pytest.approx([1.95, 2.95])
    assert [scene["duration"] for scene in plan] == pytest.approx([1.75, .75])
    assert [scene["word_count"] for scene in plan] == [4, 2]
    assert plan[1]["start_time"] > plan[0]["end_time"]  # Preserve measured silence.

    reduced = redistribute_scene_words([ayah], allocation["scenes"], scene_index=0, requested_word_count=2)
    reduced_plan = build_scene_plan([ayah], durations=[4], word_timings=timings,
                                    scene_overrides=reduced["scenes"])
    assert [scene["start_time"] for scene in reduced_plan] == pytest.approx([.2, 1.2])
    assert [scene["end_time"] for scene in reduced_plan] == pytest.approx([.95, 2.95])
    assert [scene["text"] for scene in reduced_plan] == ["أَوَّلٌ ثَانٍ", "ثَالِثٌ رَابِعٌ خَامِسٌ سَادِسٌ"]
    assert " ".join(word for scene in reduced_plan for word in scene["text"].split()) == ayah


def test_scene_split_and_merge_retime_each_assigned_word_and_reject_overlap():
    from app.scenes import build_scene_plan, merge_scene_with_previous, split_scene_by_word_count
    ayah = "أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ خَامِسٌ"
    timings = [[
        {"start":.1,"end":.35}, {"start":.55,"end":.9},
        {"start":1.2,"end":1.5}, {"start":1.75,"end":2.05},
        {"start":2.4,"end":2.75},
    ]]
    initial = [{"ayah_number":1,"scene_id":"whole","text":ayah,"locked":False}]
    split = split_scene_by_word_count([ayah], initial, scene_index=0, words_per_scene=2)
    plan = build_scene_plan([ayah], durations=[3], word_timings=timings,
                            scene_overrides=split["scenes"])
    assert [row["start_time"] for row in plan] == pytest.approx([.1,1.2,2.4])
    assert [row["end_time"] for row in plan] == pytest.approx([.9,2.05,2.75])
    merged = merge_scene_with_previous([ayah], split["scenes"], scene_index=1)
    merged_plan = build_scene_plan([ayah], durations=[3], word_timings=timings,
                                   scene_overrides=merged["scenes"])
    assert [row["text"] for row in merged_plan] == ["أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ", "خَامِسٌ"]
    assert [row["start_time"] for row in merged_plan] == pytest.approx([.1,2.4])
    assert [row["end_time"] for row in merged_plan] == pytest.approx([2.05,2.75])
    with pytest.raises(ValueError, match="out of order"):
        build_scene_plan([ayah], durations=[3], word_timings=[[
            {"start":.1,"end":.7}, {"start":.6,"end":.9}, *timings[0][2:],
        ]], scene_overrides=split["scenes"])


def test_merge_previous_preserves_order_and_refuses_to_cross_ayah_boundary():
    from app.scenes import merge_scene_with_previous
    ayahs = ["أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ", "خَامِسٌ سَادِسٌ"]
    rows = [
        {"ayah_number":1,"text":"أَوَّلٌ ثَانٍ"},
        {"ayah_number":1,"text":"ثَالِثٌ رَابِعٌ"},
        {"ayah_number":2,"text":ayahs[1]},
    ]
    merged = merge_scene_with_previous(ayahs, rows, scene_index=1)
    assert merged["scenes"][0]["text"] == ayahs[0]
    assert merged["scenes"][0]["word_count"] == 4
    assert merged["selected_scene_index"] == 0
    assert merged["scenes"][1]["text"] == ayahs[1]
    with pytest.raises(ValueError, match="across ayah boundaries"):
        merge_scene_with_previous(ayahs, rows, scene_index=2)


def test_split_scene_by_word_count_creates_exact_groups_and_final_remainder():
    from app.scenes import split_scene_by_word_count
    ayah = "كَلِمَة١ كَلِمَة٢ كَلِمَة٣ كَلِمَة٤ كَلِمَة٥ كَلِمَة٦ كَلِمَة٧ كَلِمَة٨ كَلِمَة٩ كَلِمَة١٠ كَلِمَة١١ كَلِمَة١٢"
    result = split_scene_by_word_count([ayah], [{"ayah_number":7,"text":ayah}],
                                       ayah_start=7, scene_index=0, words_per_scene=4)
    assert result["word_counts"] == [4,4,4]
    assert [row["text"].split() for row in result["scenes"]] == [ayah.split()[0:4], ayah.split()[4:8], ayah.split()[8:12]]
    assert "".join(ayah.split()) == "".join("".join(row["text"].split()) for row in result["scenes"])


def test_exported_video_uses_each_edited_scene_caption_at_word_timed_boundaries(tmp_path, monkeypatch):
    from moviepy import AudioClip, VideoFileClip
    from PIL import Image
    import app.video_engine as engine

    ayah = "كَلِمَة١ كَلِمَة٢ كَلِمَة٣ كَلِمَة٤ كَلِمَة٥ كَلِمَة٦ كَلِمَة٧ كَلِمَة٨ كَلِمَة٩ كَلِمَة١٠ كَلِمَة١١ كَلِمَة١٢"
    chunks = [" ".join(ayah.split()[offset:offset + 4]) for offset in (0, 4, 8)]
    rendered_texts = []
    colors = [(230, 35, 45), (30, 210, 65), (35, 75, 235)]

    def caption_for_scene(text, *, output_size, **_options):
        rendered_texts.append(text)
        return Image.new("RGBA", (80, 40), (*colors[len(rendered_texts) - 1], 255))

    monkeypatch.setattr(engine, "render_caption_image", caption_for_scene)
    audio_path = tmp_path / "recitation.wav"
    tone = AudioClip(lambda time: .05 * np.sin(2 * np.pi * 220 * np.asarray(time)),
                     duration=3, fps=44100)
    tone.write_audiofile(str(audio_path), fps=44100, codec="pcm_s16le", logger=None)
    tone.close()
    output_path = tmp_path / "split-scenes.mp4"
    word_times = [[{"start": index * .2, "end": index * .2 + .16} for index in range(12)]]

    metadata = render_reel(
        ayahs=[ayah], output_path=output_path, aspect_ratio="9:16",
        output_size=(240, 426), fps=24, quality="fast", encoder="cpu",
        audio_path=audio_path, audio_start=0, audio_end=3, ayah_durations=[3],
        word_timings=word_times, words_per_scene=4, ayah_start=7,
        scene_overrides=[{"ayah_number":7,"text":chunk} for chunk in chunks],
        show_surah_title=False, show_ayah_number=False, transition="cut",
    )
    assert rendered_texts == chunks
    assert ayah not in rendered_texts
    assert metadata["scene_count"] == 3
    assert metadata["phrase_timing_mode"] == "word_timestamp"
    assert metadata["phrase_timing_approximate"] is False
    video = VideoFileClip(str(output_path))
    try:
        observed = [video.get_frame(time)[213, 120].astype("int16") for time in (.25, 1.05, 2.05)]
        assert observed[0][0] > observed[0][1] * 2
        assert observed[1][1] > observed[1][0] * 2
        assert observed[2][2] > observed[2][0] * 2
    finally:
        video.close()


def test_export_applies_manual_caption_durations_without_shifting_recitation(tmp_path, monkeypatch):
    from moviepy import VideoFileClip
    from PIL import Image
    import subprocess
    import wave
    import app.video_engine as engine

    ayah = "أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ"
    chunks = ["أَوَّلٌ ثَانٍ", "ثَالِثٌ رَابِعٌ"]
    colors = [(230, 35, 45), (30, 210, 65)]
    def caption_for_scene(text, *, output_size, **_options):
        return Image.new("RGBA", (80, 40), (*colors[chunks.index(text)], 255))

    monkeypatch.setattr(engine, "render_caption_image", caption_for_scene)
    audio_path = tmp_path / "manual-timed-recitation.wav"
    sample_rate = 44100
    source_times = np.arange(sample_rate * 3, dtype=np.float64) / sample_rate
    source_tone = (0.4 * np.sin(2 * np.pi * 220 * source_times) * 32767).astype("int16")
    with wave.open(str(audio_path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(source_tone.tobytes())
    output_path = tmp_path / "manual-caption-duration.mp4"
    metadata = render_reel(
        ayahs=[ayah], output_path=output_path, aspect_ratio="9:16",
        output_size=(240, 426), fps=24, quality="fast", encoder="cpu",
        audio_path=audio_path, audio_start=0, audio_end=3, ayah_durations=[3],
        word_timings=[[{"start":.1,"end":.35},{"start":.55,"end":.9},
                       {"start":1.2,"end":1.5},{"start":1.75,"end":2.05}]],
        ayah_start=1,
        scene_overrides=[
            {"scene_id":"first", "ayah_number":1, "text":chunks[0], "manual_duration":.8},
            {"scene_id":"second", "ayah_number":1, "text":chunks[1], "manual_duration":.6},
        ],
        show_surah_title=False, show_ayah_number=False, transition="cut",
    )
    assert metadata["duration"] == pytest.approx(3, abs=.08)
    video = VideoFileClip(str(output_path))
    try:
        red = video.get_frame(.3)[213, 120].astype("int16")
        gap = video.get_frame(1.0)[213, 120].astype("int16")
        green = video.get_frame(1.5)[213, 120].astype("int16")
        after_manual_window = video.get_frame(1.85)[213, 120].astype("int16")
        assert red[0] > red[1] * 2
        assert gap[0] < 180 and gap[1] < 180
        assert green[1] > green[0] * 2
        assert after_manual_window[1] < 180
        assert video.audio.duration == pytest.approx(3, abs=.08)
        extracted_audio = tmp_path / "exported-audio.wav"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", str(output_path),
            "-vn", "-ac", "1", "-ar", str(sample_rate), "-c:a", "pcm_s16le", str(extracted_audio),
        ], check=True, capture_output=True)
        with wave.open(str(extracted_audio), "rb") as audio_file:
            audio_samples = np.frombuffer(audio_file.readframes(audio_file.getnframes()), dtype="<i2").astype("float64") / 32768
        sample_times = np.arange(int(.05 * sample_rate), int(.1 * sample_rate)) / sample_rate
        expected = np.sin(2 * np.pi * 220 * sample_times)
        actual = audio_samples[int(.05 * sample_rate):int(.1 * sample_rate)]
        correlation = np.corrcoef(expected, actual)[0, 1]
        assert correlation > .98
    finally:
        video.close()


@pytest.mark.parametrize("caption_extension", [.1, 1.0])
def test_caption_tail_extends_video_as_silence_without_extending_selected_recitation(
        tmp_path, monkeypatch, caption_extension):
    from moviepy import VideoFileClip
    from PIL import Image
    import subprocess
    import wave
    import app.video_engine as engine

    ayah = "أَوَّلٌ ثَانٍ"
    monkeypatch.setattr(engine, "render_caption_image", lambda text, **_: Image.new(
        "RGBA", (80, 40), (230, 35, 45, 255),
    ))
    audio_path = tmp_path / "selected-two-second-ayah.wav"
    sample_rate = 44100
    source_times = np.arange(sample_rate * 2, dtype=np.float64) / sample_rate
    source_tone = (0.4 * np.sin(2 * np.pi * 220 * source_times) * 32767).astype("int16")
    with wave.open(str(audio_path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(source_tone.tobytes())

    output_path = tmp_path / "caption-tail-with-silent-audio.mp4"
    metadata = render_reel(
        ayahs=[ayah], output_path=output_path, aspect_ratio="9:16",
        output_size=(240, 426), fps=24, quality="fast", encoder="cpu",
        audio_path=audio_path, audio_start=0, audio_end=2, ayah_durations=[2],
        scene_overrides=[{"scene_id":"final", "ayah_number":1, "text":ayah,
                          "manual_duration":2 + caption_extension}],
        show_surah_title=False, show_ayah_number=False, transition="cut",
        audio_fps=sample_rate,
    )

    assert metadata["duration"] == pytest.approx(2 + caption_extension, abs=.08)
    assert metadata["video_duration"] == pytest.approx(2 + caption_extension, abs=.08)
    assert metadata["recitation_audio_duration"] == pytest.approx(2, abs=.08)
    assert metadata["caption_audio_overrun_seconds"] == pytest.approx(caption_extension, abs=.08)
    assert metadata["caption_timing_warnings"]

    video = VideoFileClip(str(output_path))
    try:
        assert video.duration == pytest.approx(2 + caption_extension, abs=.08)
        assert video.audio.duration == pytest.approx(2 + caption_extension, abs=.08)
        final_caption = video.get_frame(2 + caption_extension / 2)[213, 120].astype("int16")
        assert final_caption[0] > final_caption[1] * 2
        extracted_audio = tmp_path / "caption-tail-audio.wav"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", str(output_path),
            "-vn", "-ac", "1", "-ar", str(sample_rate), "-c:a", "pcm_s16le", str(extracted_audio),
        ], check=True, capture_output=True)
        with wave.open(str(extracted_audio), "rb") as audio_file:
            exported = np.frombuffer(
                audio_file.readframes(audio_file.getnframes()), dtype="<i2",
            ).astype("float64") / 32768
        assert len(exported) >= sample_rate * (2 + caption_extension) - 100
        source_probe = source_tone[int(.2 * sample_rate):int(1.8 * sample_rate)].astype("float64") / 32768
        output_probe = exported[int(.2 * sample_rate):int(1.8 * sample_rate)]
        assert np.corrcoef(source_probe, output_probe)[0, 1] > .98
        silent_tail = exported[int((2 + caption_extension / 2) * sample_rate):]
        assert np.sqrt(np.mean(silent_tail ** 2)) < .003
    finally:
        video.close()


def test_multi_ayah_export_contains_only_the_selected_audio_interval(tmp_path):
    from moviepy import VideoFileClip
    import subprocess
    import wave

    sample_rate = 44100
    duration = 3.5
    sample_times = np.arange(int(sample_rate * duration), dtype=np.float64) / sample_rate
    source_signal = np.empty_like(sample_times)
    intervals = ((0.0, .5, 880), (.5, 1.5, 220), (1.5, 2.5, 440), (2.5, 3.5, 880))
    for start, end, frequency in intervals:
        selected = (sample_times >= start) & (sample_times < end)
        source_signal[selected] = .35 * np.sin(2 * np.pi * frequency * sample_times[selected])
    audio_path = tmp_path / "three-distinct-ayah-tones.wav"
    with wave.open(str(audio_path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes((source_signal * 32767).astype("int16").tobytes())

    output_path = tmp_path / "selected-two-ayahs-only.mp4"
    metadata = render_reel(
        ayahs=["أَوَّلٌ ثَانٍ", "ثَالِثٌ رَابِعٌ"], output_path=output_path,
        aspect_ratio="9:16", output_size=(240, 426), fps=24, quality="fast",
        encoder="cpu", audio_path=audio_path, audio_start=.5, audio_end=2.5,
        ayah_durations=[1, 1], ayah_start=29, show_quran_text=False,
        show_surah_title=False, show_ayah_number=False, transition="cut",
        audio_fps=sample_rate,
    )

    assert metadata["duration"] == pytest.approx(2, abs=.08)
    assert metadata["recitation_source_start"] == pytest.approx(.5)
    assert metadata["recitation_source_end"] == pytest.approx(2.5)
    assert metadata["recitation_audio_duration"] == pytest.approx(2, abs=.08)
    video = VideoFileClip(str(output_path))
    try:
        extracted_audio = tmp_path / "selected-two-ayahs-only.wav"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", str(output_path),
            "-vn", "-ac", "1", "-ar", str(sample_rate), "-c:a", "pcm_s16le", str(extracted_audio),
        ], check=True, capture_output=True)
        with wave.open(str(extracted_audio), "rb") as audio_file:
            exported = np.frombuffer(
                audio_file.readframes(audio_file.getnframes()), dtype="<i2",
            ).astype("float64") / 32768
        assert video.audio.duration == pytest.approx(2, abs=.08)
        early = exported[int(.2 * sample_rate):int(.45 * sample_rate)]
        late = exported[int(1.55 * sample_rate):int(1.8 * sample_rate)]
        assert np.sqrt(np.mean(early ** 2)) > .15
        assert np.sqrt(np.mean(late ** 2)) > .15
        early_220 = np.sin(2 * np.pi * 220 * (np.arange(len(early)) / sample_rate + .2))
        late_440 = np.sin(2 * np.pi * 440 * (np.arange(len(late)) / sample_rate + 1.55))
        assert np.corrcoef(early_220, early)[0, 1] > .97
        assert np.corrcoef(late_440, late)[0, 1] > .97
    finally:
        video.close()


def test_split_export_uses_labeled_weighted_timing_when_only_ayah_duration_exists(tmp_path, monkeypatch):
    from moviepy import AudioClip, VideoFileClip
    from PIL import Image
    import app.video_engine as engine
    from app.scenes import build_scene_plan

    ayah = "قُلْ هُوَ اللَّهُ أَحَدٌ رَبُّ السَّمَاوَاتِ وَالْأَرْضِ"
    chunks = ["قُلْ هُوَ اللَّهُ", "أَحَدٌ رَبُّ السَّمَاوَاتِ وَالْأَرْضِ"]
    palette = [(230, 35, 45), (30, 210, 65)]
    rendered_texts = []

    def caption_for_scene(text, *, output_size, **_options):
        rendered_texts.append(text)
        return Image.new("RGBA", (80, 40), (*palette[len(rendered_texts) - 1], 255))

    monkeypatch.setattr(engine, "render_caption_image", caption_for_scene)
    audio_path = tmp_path / "recitation-weighted.wav"
    tone = AudioClip(lambda time: .05 * np.sin(2 * np.pi * 220 * np.asarray(time)), duration=3, fps=44100)
    tone.write_audiofile(str(audio_path), fps=44100, codec="pcm_s16le", logger=None)
    tone.close()
    output_path = tmp_path / "weighted-scenes.mp4"
    metadata = render_reel(
        ayahs=[ayah], output_path=output_path, aspect_ratio="9:16", output_size=(240,426),
        fps=24, quality="fast", encoder="cpu", audio_path=audio_path, audio_start=0,
        audio_end=3, ayah_durations=[3], words_per_scene=4, ayah_start=7,
        scene_overrides=[{"ayah_number":7,"text":chunk} for chunk in chunks],
        show_surah_title=False, show_ayah_number=False, transition="cut",
    )
    assert rendered_texts == chunks
    assert metadata["scene_count"] == 2
    assert metadata["phrase_timing_mode"] == "weighted_estimate"
    assert metadata["phrase_timing_approximate"] is True
    plan = build_scene_plan([ayah], ayah_start=7, durations=[3], scene_overrides=[
        {"ayah_number":7,"text":chunk} for chunk in chunks
    ])
    assert sum(scene["duration"] for scene in plan) == pytest.approx(3)
    assert plan[0]["duration"] != pytest.approx(plan[1]["duration"])
    video = VideoFileClip(str(output_path))
    try:
        first_sample = video.get_frame(plan[0]["duration"] / 2)[213, 120].astype("int16")
        second_sample = video.get_frame(plan[0]["duration"] + plan[1]["duration"] / 2)[213, 120].astype("int16")
        assert first_sample[0] > first_sample[1] * 2
        assert second_sample[1] > second_sample[0] * 2
    finally:
        video.close()


def test_bundled_arabic_font_catalog_contains_multiple_readable_fonts():
    from app.font_catalog import FONT_CATALOG
    from PIL import ImageFont
    assert len(FONT_CATALOG) >= 4
    assert all(ImageFont.truetype(str(item["file"]), 64) for item in FONT_CATALOG.values())
