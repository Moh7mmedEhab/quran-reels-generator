import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from app.background_motion import IMAGE_ANIMATION_PRESETS, image_motion_values, resolve_motion_preset
from app.file_names import sanitize_video_filename
from app.youtube_metadata import generate_youtube_metadata


def test_directional_background_motion_covers_four_directions_and_static():
    expected = {
        "left_to_right": "slow_pan_left",
        "right_to_left": "slow_pan_right",
        "top_to_bottom": "slow_pan_top_to_bottom",
        "bottom_to_top": "slow_pan_bottom_to_top",
        "static": "static",
    }
    for direction, preset in expected.items():
        assert resolve_motion_preset(direction, "cinematic_zoom") == preset
        assert preset in IMAGE_ANIMATION_PRESETS
    assert image_motion_values("static", .5, 1) == (1.0, .5, .5)
    assert image_motion_values("slow_pan_top_to_bottom", 0, 1)[2] != image_motion_values(
        "slow_pan_top_to_bottom", 1, 1
    )[2]
    assert image_motion_values("slow_pan_bottom_to_top", 0, 1)[2] != image_motion_values(
        "slow_pan_bottom_to_top", 1, 1
    )[2]


def test_video_background_motion_moves_crop_without_reversing_video_playback():
    import numpy as np
    from moviepy import VideoClip
    from app.video_engine import _animated_video_clip

    y, x = np.mgrid[:128, :128]
    source_frame = np.stack((x, y, np.zeros_like(x)), axis=-1).astype(np.uint8)
    cases = {
        "left_to_right": ("slow_pan_left", 0, "decreasing"),
        "right_to_left": ("slow_pan_right", 0, "increasing"),
        "top_to_bottom": ("slow_pan_top_to_bottom", 1, "decreasing"),
        "bottom_to_top": ("slow_pan_bottom_to_top", 1, "increasing"),
        "static": ("static", 0, "same"),
    }
    for _direction, (preset, channel, expected) in cases.items():
        class Source:
            duration = 4.0

            def __init__(self):
                self.times = []

            def get_frame(self, time):
                self.times.append(float(time))
                return source_frame

        source = Source()
        clip = _animated_video_clip(
            source, size=(64, 64), preset_id=preset, intensity=1,
            cycle_duration=4, speed=1, start_time=0, VideoClip=VideoClip,
        )
        source.times.clear()
        first = clip.get_frame(0)
        last = clip.get_frame(2)
        assert source.times == [0.0, 2.0]
        assert first.shape == last.shape == (64, 64, 3)
        before, after = first[:, :, channel].mean(), last[:, :, channel].mean()
        if expected == "decreasing":
            assert before > after
        elif expected == "increasing":
            assert before < after
        else:
            assert np.array_equal(first, last)


def test_bilingual_metadata_uses_selected_content_and_platform_limits():
    metadata = generate_youtube_metadata(
        surah_number=55, surah_english="Ar-Rahmaan", surah_arabic="سُورَةُ الرَّحۡمَٰن",
        ayah_start=13, ayah_end=16, reciter_name="Mishary Rashid Alafasy",
    )
    from app.word_alignment import normalize_arabic_word
    assert normalize_arabic_word("الرحمن") in normalize_arabic_word(metadata["arabic"]["title"])
    assert "سُورَةُ سُورَةُ" not in metadata["arabic"]["title"]
    assert "13–16" in metadata["arabic"]["title"]
    assert "القارئ: Mishary Rashid Alafasy" in metadata["arabic"]["description"]
    assert "Ar-Rahmaan" in metadata["english"]["title"]
    assert "Mishary Rashid Alafasy" in metadata["english"]["description"]
    assert metadata["limits"]["title_characters"] == 100
    assert len(metadata["arabic"]["title"]) <= 100
    assert len(metadata["english"]["title"]) <= 100
    assert len(", ".join(metadata["arabic"]["tags"])) <= 500
    assert len(", ".join(metadata["english"]["tags"])) <= 500
    assert metadata["arabic"]["hashtags"] and metadata["english"]["hashtags"]


def test_filename_sanitizer_preserves_arabic_and_removes_filesystem_controls():
    filename = sanitize_video_filename('سورة الرحمن / "آية": 13?\x00')
    assert filename.startswith("سورة الرحمن")
    assert filename.endswith(".mp4")
    assert "/" not in filename and '"' not in filename and "?" not in filename
    assert "\x00" not in filename
    assert sanitize_video_filename("...  ") == "Quran Reel.mp4"
    assert len(Path(sanitize_video_filename("ع" * 300)).stem) <= 120
    assert len(sanitize_video_filename("😀" * 300).encode("utf-8")) <= 184


def test_all_bundled_arabic_fonts_render_quran_text_and_marks():
    from app.font_catalog import FONT_CATALOG
    from app.text_renderer import render_arabic_text

    sample = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ ۞"
    assert {"amiri", "amiri_bold", "naskh", "naskh_bold", "sans", "sans_bold", "kufi", "kufi_bold"} <= set(FONT_CATALOG)
    rendered = {}
    for font_id, font in FONT_CATALOG.items():
        assert font["file"].is_file(), f"Missing bundled font {font_id}"
        image = render_arabic_text(sample, font_path=font["file"], font_size=56,
                                   color=(255, 255, 255, 255), max_width=600,
                                   backdrop_fill=None, stroke_width=1)
        assert image.getbbox()
        rendered[font_id] = image.tobytes()
    assert len(set(rendered.values())) > 1


def test_new_caption_labels_are_off_by_default_and_independent_label_offsets_render():
    from app.text_renderer import render_arabic_text

    sample = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    base_args = dict(text=sample, ayah_number=7, surah_title="سُورَةُ الفَاتِحَةِ",
                     font_size=54, max_width=700, backdrop_fill=None, output_size=(1080, 1920))
    default = render_arabic_text(**base_args)
    explicit_off = render_arabic_text(**base_args, show_surah_title=False, show_ayah_number=False)
    assert default.size == explicit_off.size
    assert default.tobytes() == explicit_off.tobytes()

    shifted = render_arabic_text(**base_args, show_surah_title=True, show_ayah_number=True,
                                 surah_position_x=-5, surah_position_y=-5,
                                 ayah_number_position_x=5, ayah_number_position_y=5)
    centered = render_arabic_text(**base_args, show_surah_title=True, show_ayah_number=True)
    assert shifted.size != centered.size
    assert shifted.tobytes() != centered.tobytes()


def test_quran_foundation_word_timing_is_opt_in_and_word_count_checked(monkeypatch):
    import app.word_alignment as alignment

    monkeypatch.setenv("QURAN_FOUNDATION_CLIENT_ID", "client")
    monkeypatch.setenv("QURAN_FOUNDATION_CLIENT_SECRET", "secret")
    monkeypatch.setenv("QURAN_REELS_QF_RECITER_MAP", json.dumps({"mishary_alafasy": 501}))
    monkeypatch.setattr(alignment, "_chapter_payload", lambda *args: {
        "audio_url": "https://audio.example/chapter.mp3",
        "timestamps": [{
            "verse_key": "55:13", "timestamp_from": 1000, "timestamp_to": 3000,
            "segments": [[1, 1100, 1800], [2, 1900, 2800]],
        }],
    })
    monkeypatch.setattr(alignment, "_chapter_verse_words", lambda *args: {
        13: ["بسم", "الله"],
    })
    result = alignment.get_chapter_word_timing(
        "mishary_alafasy", 55, 13, 13, ["بِسْمِ اللَّهِ"],
    )
    assert result["audio_url"].endswith("chapter.mp3")
    assert result["ayahs"][0]["segments"][0] == {"index": 0, "start_ms": 1100, "end_ms": 1800}


def test_relative_word_timing_rejects_overlaps_and_words_outside_effective_ayah_span():
    from app.audio_sources import _validated_relative_word_timings

    ayahs = [{"start_time": 1000, "end_time": 3200, "segments": [
        {"start_ms": 1100, "end_ms": 1800}, {"start_ms": 1900, "end_ms": 2800},
    ]}]
    assert _validated_relative_word_timings(ayahs, ["بسم الله"], [2.0]) == [[
        {"start": .1, "end": .8}, {"start": .9, "end": 1.8},
    ]]

    overlapping = [{**ayahs[0], "segments": [
        {"start_ms": 1100, "end_ms": 2100}, {"start_ms": 2000, "end_ms": 2800},
    ]}]
    with pytest.raises(ValueError, match="overlap"):
        _validated_relative_word_timings(overlapping, ["بسم الله"], [2.0])

    beyond_effective_end = [{**ayahs[0], "segments": [
        {"start_ms": 1100, "end_ms": 1800}, {"start_ms": 1900, "end_ms": 3200},
    ]}]
    with pytest.raises(ValueError, match="effective ayah interval"):
        _validated_relative_word_timings(beyond_effective_end, ["بسم الله"], [2.0])


def test_quran_foundation_rejects_word_index_count_mismatch(monkeypatch):
    import app.word_alignment as alignment

    monkeypatch.setenv("QURAN_FOUNDATION_CLIENT_ID", "client")
    monkeypatch.setenv("QURAN_FOUNDATION_CLIENT_SECRET", "secret")
    monkeypatch.setenv("QURAN_REELS_QF_RECITER_MAP", '{"mishary_alafasy":501}')
    monkeypatch.setattr(alignment, "_chapter_payload", lambda *args: {
        "audio_url": "https://audio.example/chapter.mp3",
        "timestamps": [{
            "verse_key": "55:13", "timestamp_from": 1000, "timestamp_to": 3000,
            "segments": [[1, 1100, 1800]],
        }],
    })
    monkeypatch.setattr(alignment, "_chapter_verse_words", lambda *args: {
        13: ["بسم", "الله"],
    })
    with pytest.raises(RuntimeError, match="Word count does not match"):
        alignment.get_chapter_word_timing(
            "mishary_alafasy", 55, 13, 13, ["بِسْمِ اللَّهِ"],
        )


def test_arabic_alignment_normalization_handles_marks_hamza_variants_and_quranic_controls():
    from app.word_alignment import normalize_arabic_word

    assert normalize_arabic_word("ٱلرَّحْمَٰنِ") == normalize_arabic_word("الرحمن")
    assert normalize_arabic_word("إِيمَان") == normalize_arabic_word("ايمان")
    assert normalize_arabic_word("مُؤْمِن") == normalize_arabic_word("مومن")


def test_optional_local_forced_alignment_maps_normalized_tokens_to_original_ayah(monkeypatch):
    import app.forced_alignment as alignment

    monkeypatch.setenv("QURAN_REELS_FORCE_ALIGN", "1")
    monkeypatch.delenv("QURAN_REELS_WHISPERX_MODEL", raising=False)
    monkeypatch.setenv("QURAN_REELS_WHISPERX_DEVICE", "cpu")
    alignment._MODEL_CACHE.clear()
    fake_whisperx = SimpleNamespace(
        load_audio=lambda path: "audio-array",
        load_align_model=lambda **kwargs: ("model", {"language": "ar"}),
        align=lambda transcript, model, metadata, audio, device, **kwargs: {
            "segments": [{"words": [
                {"start": 1.2, "end": 1.55, "score": .91},
                {"start": 1.6, "end": 2.1, "score": .88},
            ]}],
        },
    )
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    monkeypatch.setitem(sys.modules, "whisperx", fake_whisperx)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    result, note = alignment.forced_align_arabic_audio(
        "/tmp/chapter.mp3", ["بِسْمِ اللَّهِ"],
        [{"start_time": 1000, "end_time": 3000}],
    )
    assert result == [[{"start": pytest.approx(.2), "end": pytest.approx(.55)},
                      {"start": pytest.approx(.6), "end": pytest.approx(1.1)}]]
    assert "normalized copy" in note


def test_optional_local_forced_alignment_rejects_low_confidence(monkeypatch):
    import app.forced_alignment as alignment

    monkeypatch.setenv("QURAN_REELS_FORCE_ALIGN", "1")
    monkeypatch.setenv("QURAN_REELS_WHISPERX_DEVICE", "cpu")
    alignment._MODEL_CACHE.clear()
    fake_whisperx = SimpleNamespace(
        load_audio=lambda path: "audio-array",
        load_align_model=lambda **kwargs: ("model", {"language": "ar"}),
        align=lambda *args, **kwargs: {"segments": [{"words": [
            {"start": 1.1, "end": 1.6, "score": .1},
            {"start": 1.7, "end": 2.0, "score": .1},
        ]}]},
    )
    monkeypatch.setitem(sys.modules, "whisperx", fake_whisperx)
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False)))
    result, note = alignment.forced_align_arabic_audio(
        "/tmp/chapter.mp3", ["بِسْمِ اللَّهِ"],
        [{"start_time": 1000, "end_time": 3000}],
    )
    assert result is None
    assert "confidence was low" in note


def test_version_and_metadata_endpoints_use_selected_surah_range_and_reciter():
    from app import create_app

    client = create_app().test_client()
    version = client.get("/api/version")
    assert version.status_code == 200
    assert version.json["version"] == "1.2.0"
    metadata = client.get(
        "/api/youtube-metadata?surah=55&start=13&end=14&reciter_id=mishary_alafasy"
    )
    assert metadata.status_code == 200
    assert "13–14" in metadata.json["arabic"]["title"]
    assert "Mishary Rashid Alafasy" in metadata.json["english"]["description"]
    assert client.get("/api/youtube-metadata?surah=55&start=78&end=79").status_code == 400


def test_download_response_uses_edited_arabic_title_and_unique_name(tmp_path):
    from app import create_app

    class DownloadConfig:
        TESTING = True
        SECRET_KEY = "test"
        OUTPUT_FOLDER = tmp_path
        ARABIC_FONT = "/tmp/missing-font.ttf"

    stored = tmp_path / "render-id.mp4"
    stored.write_bytes(b"mock mp4")
    (tmp_path / "سورة الرحمن.mp4").write_bytes(b"prior file")
    client = create_app(DownloadConfig).test_client()
    response = client.get("/outputs/render-id.mp4?title=سورة%20الرحمن")
    assert response.status_code == 200
    from werkzeug.http import parse_options_header
    _kind, params = parse_options_header(response.headers["Content-Disposition"])
    assert params["filename"] == "سورة الرحمن (2).mp4"
    assert response.data == b"mock mp4"


def test_template_exposes_image_video_tabs_and_release_version():
    from app import create_app

    page = create_app().test_client().get("/")
    assert page.status_code == 200
    assert b'id="background-image-tab"' in page.data
    assert b'id="background-video-tab"' in page.data
    assert b'id="background-motion-direction"' in page.data
    assert b'id="video-title"' in page.data
    assert b'id="api-curl-command"' in page.data
    assert b"function currentRenderCurl()" in page.data
    assert b"window.location.origin + '/api/generate'" in page.data
    assert b"Studio v1.2" in page.data
    assert b"Misty Forest Drift" in page.data


def test_scene_editor_preview_is_submitted_as_render_source_of_truth():
    from app import create_app

    page = create_app().test_client().get("/")
    assert page.status_code == 200
    script = page.get_data(as_text=True)
    assert "form.set('scene_overrides', JSON.stringify(sceneRowsForRequest()))" in script
    assert "duration:scene.duration == null ? null : Number(scene.duration)" in script
    assert "start_time:scene.start_time == null ? null : Number(scene.start_time)" in script
    assert "end_time:scene.end_time == null ? null : Number(scene.end_time)" in script
    assert "if (scenePlanManual) {\n        form.set('scene_overrides'" not in script
    assert 'id="words-per-scene"' in script
    assert 'type="text" inputmode="numeric"' in script
    assert "form.set('words_per_scene', String(appliedWordsPerScene))" in script
    assert "Apply or clear the pending scene word-count edit before exporting." in script
    assert "Share %" not in script
    assert "scene-word-count" in script
    assert "sceneWordCountBounds" in script
    assert "fetch('/api/scenes/redistribute'" in script
    assert "locked:Boolean(scene.locked)" in script
    assert "scene_id:scene.scene_id" in script
    assert "row.manual_duration = Number(scene.manual_duration)" in script
    assert "sceneDurationDrafts.delete(scene.scene_id)" in script
    assert "Reset Timing" in script
    assert "−1.0s" in script and "+0.1s" in script
    assert "Duration (seconds)" in script


def test_recitation_preview_uses_audio_boundary_separate_from_caption_end():
    from app import create_app

    page = create_app().test_client().get("/")
    assert page.status_code == 200
    script = page.get_data(as_text=True)
    assert "previewAudioStart = Number(result.audio_start ?? previewAyahTimingRows[0]?.start)" in script
    assert "previewAudioEnd = Number(result.audio_end ?? previewAyahTimingRows.at(-1)?.end)" in script
    assert "previewAudioDuration = Number(result.audio_duration ?? (previewAudioEnd - previewAudioStart))" in script
    assert "previewAudioUrl.hash = ''" in script
    assert "player.currentTime = 0" in script
    assert "const elapsed = audioStart + player.currentTime" in script
    assert "elapsed >= (timing.caption_start ?? timing.start)" in script
    assert "elapsed < (timing.caption_end ?? timing.end)" in script
    assert "player.onended = finishPreview" in script
    assert "function stopRecitationPreview()" in script
    assert "timing.start = timingOrigin + Number(applied.start_time)" not in script


def test_video_background_catalog_serves_three_local_silent_mp4_templates():
    from app import create_app

    client = create_app().test_client()
    response = client.get("/api/background-video-templates")
    assert response.status_code == 200
    templates = response.json["templates"]
    assert set(templates) == {"misty_forest_drift", "marble_arch_glow", "moonlit_horizon"}
    for template in templates.values():
        assert template["audio"] is False
        video = client.get(template["video_url"])
        assert video.status_code == 200
        assert video.mimetype == "video/mp4"
        assert len(video.data) > 10_000


def test_builtin_video_background_is_passed_to_the_export_renderer(monkeypatch, tmp_path):
    import app.routes as routes
    from app import create_app
    from app.background_video_templates import background_video_template_path

    audio_path = tmp_path / "recitation.mp3"
    audio_path.write_bytes(b"mock audio")
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        Path(kwargs["output_path"]).write_bytes(b"complete-mp4" * 200)
        return {"path": str(kwargs["output_path"]), "duration": 4,
                "width": 480, "height": 854, "has_audio": True, "scene_count": 1}

    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: SimpleNamespace(
        path=audio_path, start=0, end=4, ayah_durations=[4], word_timings=None,
        timing_source="mp3quran_ayah", timing_note="Ayah timing.",
    ))
    monkeypatch.setattr(routes, "render_reel", fake_render)
    monkeypatch.setattr(routes, "validate_rendered_output", lambda *args, **kwargs: {"playable": True})

    class Config:
        TESTING = True
        RENDER_JOBS_INLINE = True
        SECRET_KEY = "test"
        OUTPUT_FOLDER = tmp_path / "outputs"
        ARABIC_FONT = Path(__file__).resolve().parents[1] / "static/assets/NotoNaskhArabic-Regular.ttf"

    app = create_app(Config)
    client = app.test_client()
    response = client.post("/api/generate", json={
        "surah": 55, "ayah_start": 13, "ayah_end": 13,
        "reciter_id": "mishary_alafasy", "encoder": "cpu", "resolution": "480p",
        "quality": "fast", "background_video_template": "marble_arch_glow",
    })
    assert response.status_code == 202, response.json
    job = client.get(response.json["status_url"]).json
    assert job["status"] == "complete", job
    assert job["result"]["background_video_template"] == "marble_arch_glow"
    assert captured["background_path"] == background_video_template_path(
        "marble_arch_glow", static_folder=app.static_folder,
    )
    assert captured["background_audio_enabled"] is False
