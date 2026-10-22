from pathlib import Path
from types import SimpleNamespace
import pytest

from app import create_app
from app.quraa_data import RECITERS
from app.quran_data import SURAHS


class TestConfig:
    TESTING = True
    RENDER_JOBS_INLINE = True
    SECRET_KEY = "test"
    OUTPUT_FOLDER = "/tmp/quran-reels-test-output"
    ARABIC_FONT = "/tmp/missing-font.ttf"


def test_studio_renders_light_template_with_all_surahs():
    response = create_app(TestConfig).test_client().get("/")
    assert response.status_code == 200
    assert b"Render High-Res Reel" in response.data
    assert "114 · An-Naas".encode() in response.data
    assert b"id=\"rendered-video\"" in response.data
    assert b"id=\"audio-file\"" not in response.data
    assert b"data-theme=\"marble_arch\"" in response.data
    assert len(SURAHS) == 114
    assert b"id=\"export-resolution\"" in response.data
    assert b"id=\"background-clip-list\"" in response.data
    assert b"id=\"sequence-enabled\"" in response.data
    assert b"Enable Sequential Background Media" in response.data
    assert b"id=\"transitions-enabled\"" in response.data
    assert b"id=\"background-animation-enabled\"" in response.data
    assert b"id=\"background-animation-start\"" in response.data
    assert b"id=\"background-atmosphere-enabled\"" in response.data
    assert b"id=\"background-atmosphere-start\"" in response.data
    assert b"Ayah scene transition" in response.data
    assert b"Camera Motion" not in response.data
    assert b"Cinematic Background Sequences" in response.data
    assert b"id=\"background-brightness\"" in response.data
    assert b"id=\"background-contrast\"" in response.data
    assert b"id=\"background-saturation\"" in response.data
    assert b"id=\"project-manager\"" in response.data
    assert b"id=\"save-project-btn\"" in response.data
    assert b"id=\"undo-project-btn\"" in response.data
    assert b"id=\"custom-template-manager\"" in response.data
    assert b"id=\"save-custom-template-btn\"" in response.data
    assert b"id=\"import-custom-template-btn\"" in response.data
    assert b"id=\"export-custom-template-btn\"" in response.data
    assert b"id=\"surah-name-template\"" in response.data
    assert b"id=\"viewer-title-badge\"" in response.data
    assert b"id=\"show-quran-text\"" in response.data
    assert b"id=\"translation-text\"" in response.data
    assert b"id=\"viewer-progress-track\"" in response.data
    assert b"id=\"export-encoder\"" in response.data


def test_ayah_range_fields_are_styled_text_inputs_with_numeric_mobile_keypad():
    client = create_app(TestConfig).test_client()
    page = client.get("/")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert 'id="start-ayah" data-max="78" data-min="1"' in html
    assert 'id="end-ayah" data-max="78" data-min="1"' in html
    assert 'inputmode="numeric"' in html
    assert 'id="start-ayah"' in html and 'dir="ltr" type="text"' in html
    assert 'id="end-ayah"' in html and 'dir="ltr" type="text"' in html
    assert 'id="ayah-range-grid"' in html
    assert html.count('id="start-ayah"') == 1
    assert html.count('id="end-ayah"') == 1
    assert 'id="words-per-scene" type="text"' in html
    assert 'id="reset-scenes"' in html
    assert "scene-timing-1" in html
    css = client.get("/static/css/app.css?v=studio-2026-10-22-scene-timing-1")
    assert css.status_code == 200
    assert b".ayah-range-control:focus-within" in css.data
    assert b".ayah-range-value:focus-visible" in css.data
    assert b"#ayah-range-grid { grid-template-columns:minmax(0,1fr); }" in css.data
    assert b".scene-setting-input" in css.data
    assert b".scene-setting-input:hover:not(:disabled)" in css.data
    assert b".scene-word-apply:focus-visible" in css.data
    assert b".scene-duration-input" in css.data
    assert b".scene-duration-adjustments" in css.data
    assert b".scene-text-input[aria-invalid=\"true\"]" in css.data
    assert "$('scene-text-input')?.setAttribute('aria-invalid', 'true')" in html
    assert b".scene-row.active-scene" in css.data
    assert b".scene-text-input" in css.data and b"overflow-wrap:anywhere" in css.data
    assert b"@media (max-width:520px)" in css.data


def test_app_uses_writable_temp_output_when_project_output_is_read_only():
    class ReadOnlyOutputConfig(TestConfig):
        OUTPUT_FOLDER = "/proc/quran-reels-unwritable"

    app = create_app(ReadOnlyOutputConfig)
    output_folder = Path(app.config["OUTPUT_FOLDER"])
    assert output_folder.is_dir()
    assert output_folder != Path(ReadOnlyOutputConfig.OUTPUT_FOLDER)


def test_render_capabilities_reports_both_gpus_and_cpu(monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes, "hardware_encoder_status", lambda **kwargs: {
        "nvidia": {"available": False, "name": "NVIDIA NVENC", "reason": "No CUDA device"},
        "intel": {"available": True, "name": "Intel UHD", "reason": None},
    })
    response = create_app(TestConfig).test_client().get("/api/render-capabilities")
    assert response.status_code == 200
    assert response.json["default_encoder"] == "auto"
    assert response.json["encoders"]["cpu"]["available"] is True
    assert response.json["encoders"]["nvidia"]["available"] is False
    assert response.json["encoders"]["nvidia"]["reason"] == "No CUDA device"
    assert response.json["encoders"]["intel"]["available"] is True


def test_generate_rejects_unavailable_nvidia_before_downloading_audio(monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes, "hardware_encoder_status", lambda **kwargs: {
        "nvidia": {"available": False, "name": "NVIDIA NVENC", "reason": "No CUDA device"},
        "intel": {"available": False, "name": "Intel UHD", "reason": "No media device"},
    })
    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: pytest.fail(
        "Audio should not download if the selected encoder is unavailable"))
    response = create_app(TestConfig).test_client().post("/api/generate", json={
        "surah": 55, "ayah_start": 13, "ayah_end": 13,
        "reciter_id": "mishary_alafasy", "encoder": "nvidia",
    })
    assert response.status_code == 400
    assert "NVIDIA NVENC is unavailable" in response.json["error"]


def test_generate_rejects_unavailable_intel_gpu(monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes, "hardware_encoder_status", lambda **kwargs: {
        "nvidia": {"available": False, "name": "NVIDIA NVENC", "reason": "No CUDA device"},
        "intel": {"available": False, "name": "Intel UHD", "reason": "No media device"},
    })
    response = create_app(TestConfig).test_client().post("/api/generate", json={
        "surah": 55, "ayah_start": 13, "ayah_end": 13,
        "reciter_id": "mishary_alafasy", "encoder": "intel",
    })
    assert response.status_code == 400
    assert "Intel UHD is unavailable" in response.json["error"]


def test_cinematic_background_sequence_template_has_five_credited_local_scenes():
    client = create_app(TestConfig).test_client()
    response = client.get("/api/background-sequence-templates")
    assert response.status_code == 200
    templates = response.json["templates"]
    assert len(templates) >= 4
    assert all(len(item["scenes"]) == 5 for item in templates.values())
    available = {item["id"] for item in client.get("/api/backgrounds").json["backgrounds"]}
    assert all(scene["theme"] in available for item in templates.values() for scene in item["scenes"])


def test_footer_uses_runtime_year_and_requested_author():
    from datetime import datetime
    response = create_app(TestConfig).test_client().get("/")
    assert f"© {datetime.now().year} Mohammed Ehab. All rights reserved.".encode() in response.data
    assert b"Sacred Arts Studio" not in response.data


def test_surah_endpoint_includes_all_114_chapters():
    response = create_app(TestConfig).test_client().get("/api/surahs")
    assert response.status_code == 200
    assert len(response.json["surahs"]) == 114
    assert sum(chapter["ayah_count"] for chapter in response.json["surahs"]) == 6236


def test_design_template_api_exposes_independent_complete_presets():
    response = create_app().test_client().get("/api/design-templates")
    assert response.status_code == 200
    assert len(response.json["quran_text"]) >= 10
    assert len(response.json["surah_name"]) >= 6
    assert len(response.json["ayah_number"]) >= 6
    assert response.json["surah_name"]["emerald_ribbon"]["shape"] == "ribbon"
    assert response.json["ayah_number"]["gold_medallion"]["shape"] == "medallion"
    assert {"fade_black", "fade_color", "slide_left", "slide_right", "zoom"} <= set(response.json["transitions"])
    assert {"static", "cinematic_zoom", "slow_pan_left", "parallax_depth"} <= set(response.json["image_animations"])


def test_complete_video_presets_keep_surah_and_ayah_visibility_independent():
    response = create_app(TestConfig).test_client().get("/api/video-templates")
    assert response.status_code == 200
    templates = response.json["templates"]
    assert templates["minimal_cream"]["show_surah_title"] is False
    assert templates["minimal_cream"]["show_ayah_number"] is True


def test_reel_viewer_presets_define_ten_complete_compositions():
    response = create_app(TestConfig).test_client().get("/api/video-templates")
    assert response.status_code == 200
    presets = response.json["viewer_templates"]
    assert len(presets) == 10
    required = {"show_viewer_title", "show_quran_text", "show_translation", "show_waveform",
                "show_reciter_badge", "show_progress", "title_template", "waveform_style",
                "progress_color", "caption_style", "theme"}
    assert all(required <= preset.keys() for preset in presets.values())
    assert presets["modern_translation"]["show_translation"] is True
    assert presets["clean_arabic"]["show_reciter_badge"] is False


def test_verse_endpoint_returns_arabic_range():
    response = create_app(TestConfig).test_client().get("/api/verses?surah=55&start=13&end=14")
    assert response.status_code == 200
    assert len(response.json["ayahs"]) == 2
    assert "تُكَذِّبَانِ" in response.json["ayahs"][0]


def test_verse_endpoint_rejects_out_of_range_ayah():
    response = create_app(TestConfig).test_client().get("/api/verses?surah=93&start=1&end=12")
    assert response.status_code == 400


def test_reciter_endpoint_returns_streamable_recordings_with_source_metadata():
    response = create_app(TestConfig).test_client().get("/api/reciters")
    assert response.status_code == 200
    assert len(response.json["reciters"]) == len(RECITERS) == 25
    assert all(item["audio_base_url"].startswith("https://") for item in response.json["reciters"])
    assert all(item["source"] == "MP3Quran.net" for item in response.json["reciters"])
    groups = {}
    for item in response.json["reciters"]:
        groups.setdefault(item["group_id"], []).append(item)
    assert len(groups["minshawi"]) == 1
    assert len(groups["abdul_basit"]) == 2
    assert len(groups["husary"]) == 5
    assert {item["read_id"] for item in RECITERS if item["group_id"] == "husary"} == {118, 119, 120, 269, 270}


def test_reciter_preview_builds_selected_chapter_url():
    response = create_app(TestConfig).test_client().get("/api/reciters/mishary_alafasy/preview?surah=55")
    assert response.status_code == 200
    assert response.json["audio_url"].endswith("/055.mp3")


def test_mujawwad_recording_preview_uses_its_own_audio_archive():
    response = create_app(TestConfig).test_client().get("/api/reciters/abdul_basit_mujawwad/preview?surah=55")
    assert response.status_code == 200
    assert response.json["audio_url"] == "https://cdn.mp3quran.net/audio/abdulbasit-abdulsamad/r1/055.mp3"


def test_background_endpoint_lists_twenty_three_presets_including_bundled_photos():
    response = create_app(TestConfig).test_client().get("/api/backgrounds")
    assert response.status_code == 200
    assert len(response.json["backgrounds"]) == 23
    assert {item["category"] for item in response.json["backgrounds"]} >= {
        "Nature & Landscapes", "Islamic Architecture", "Night & Celestial"
    }
    from PIL import Image
    asset_root = Path(__file__).resolve().parents[1] / "static" / "assets" / "backgrounds"
    for theme in ("lake_dawn", "haram_night", "misty_valley"):
        with Image.open(asset_root / f"{theme}.jpg") as original:
            assert original.width == 3000
        assert (asset_root / f"{theme}_cinematic.jpg").is_file()
        preview = create_app(TestConfig).test_client().get(f"/api/backgrounds/{theme}/preview?ratio=9:16")
        assert preview.status_code == 200
        assert preview.mimetype == "image/jpeg"


def test_background_preview_returns_image_and_rejects_bad_ratio():
    client = create_app(TestConfig).test_client()
    response = client.get("/api/backgrounds/midnight_blue/preview?ratio=1:1")
    assert response.status_code == 200
    assert response.mimetype == "image/jpeg"
    assert client.get("/api/backgrounds/midnight_blue/preview?ratio=4:3").status_code == 400
    assert client.get("/api/backgrounds/midnight_blue/preview?fit=invalid").status_code == 400
    assert client.get("/api/backgrounds/midnight_blue/preview?fit=contain&ratio=16:9").status_code == 200


def test_video_template_preview_composes_the_arabic_and_viewer_layers():
    from io import BytesIO
    from PIL import Image

    client = create_app(TestConfig).test_client()
    golden = client.get("/api/video-templates/golden_quran/preview?ratio=9:16")
    minimal = client.get("/api/video-templates/minimalist_white/preview?ratio=9:16")
    assert golden.status_code == minimal.status_code == 200
    assert golden.mimetype == "image/jpeg"
    assert golden.data != minimal.data
    with Image.open(BytesIO(golden.data)) as image:
        assert image.size == (360, 640)
        assert image.mode == "RGB"
    assert client.get("/api/video-templates/not-a-template/preview").status_code == 404
    assert client.get("/api/video-templates/golden_quran/preview?ratio=4:3").status_code == 400


def test_font_catalog_lists_bundled_arabic_font_families():
    response = create_app().test_client().get("/api/fonts")
    assert response.status_code == 200
    assert {"amiri", "amiri_bold", "naskh", "naskh_bold", "sans", "sans_bold", "kufi", "kufi_bold"} <= {
        item["id"] for item in response.json["fonts"]
    }
    assert len(response.json["fonts"]) >= 8
    assert response.json["default"] == "naskh"


def test_caption_preview_uses_position_controls_and_validates_safe_ranges():
    client = create_app(TestConfig).test_client()
    payload = {
        "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "aspect_ratio": "9:16",
        "show_surah_title": True, "show_ayah_number": True,
    }
    centered = client.post("/api/caption-preview", json=payload)
    shifted = client.post("/api/caption-preview", json={
        **payload, "caption_x": 58, "caption_y": 46,
        "surah_x_offset": -5, "surah_y_offset": -5,
        "ayah_number_x_offset": 5, "ayah_number_y_offset": 5,
    })
    assert centered.status_code == shifted.status_code == 200
    assert centered.data != shifted.data
    assert client.post("/api/caption-preview", json={**payload, "caption_x": 101}).status_code == 400
    assert client.post("/api/caption-preview", json={**payload, "ayah_number_y_offset": 9}).status_code == 400


def test_caption_preview_rejects_invalid_caption_and_label_colors():
    client = create_app(TestConfig).test_client()
    payload = {"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"}
    invalid_values = [
        {"caption_color": "not-a-color"},
        {"surah_color": "#12GG00"},
        {"ayah_color": "#abc"},
    ]
    for values in invalid_values:
        response = client.post("/api/caption-preview", json={**payload, **values})
        assert response.status_code == 400
        assert "color" in response.json["error"].lower()

    valid = client.post("/api/caption-preview", json={
        **payload, "caption_color": "#12aBcD", "surah_color": "#456789", "ayah_color": "#fedcba",
    })
    assert valid.status_code == 200


def test_generate_rejects_invalid_label_color_before_audio_download(monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: pytest.fail(
        "Invalid colors should be rejected before fetching audio"))
    response = create_app(TestConfig).test_client().post("/api/generate", json={
        "surah": 55, "ayah_start": 13, "ayah_end": 13,
        "reciter_id": "mishary_alafasy", "surah_color": "invalid",
    })
    assert response.status_code == 400
    assert "Surah name color" in response.json["error"]


def test_url_background_import_is_persistent_and_preserves_original_bytes(monkeypatch, tmp_path):
    from io import BytesIO
    from PIL import Image
    import app.routes as routes

    original = BytesIO()
    Image.new("RGB", (123, 77), (18, 91, 143)).save(original, format="PNG")
    data = original.getvalue()

    class ImportConfig(TestConfig):
        OUTPUT_FOLDER = tmp_path / "outputs"

    monkeypatch.setattr(routes, "_download_public_image", lambda _url: (data, "image/png", "images.example"))
    client = create_app(ImportConfig).test_client()
    imported = client.post("/api/backgrounds/import-url", json={"url": "https://images.example/photo.png"})
    assert imported.status_code == 201
    item = imported.json
    assert (item["width"], item["height"], item["format"]) == (123, 77, "PNG")
    assert item["size_bytes"] == len(data)
    assert client.get(item["file_url"]).data == data
    assert client.get("/api/backgrounds/imported").json["backgrounds"][0]["id"] == item["id"]
    assert client.delete(f"/api/backgrounds/imported/{item['id']}").json["deleted"] is True
    assert client.get(item["file_url"]).status_code == 404


def test_url_background_import_blocks_local_hosts_private_dns_and_redirects(monkeypatch):
    import socket
    import app.routes as routes

    client = create_app(TestConfig).test_client()
    for url in ("file:///etc/passwd", "http://localhost/image.png", "http://127.0.0.1/image.png",
                "http://192.168.1.4/image.png", "https://example.local/image.png"):
        response = client.post("/api/backgrounds/import-url", json={"url": url})
        assert response.status_code == 400

    monkeypatch.setattr(routes.socket, "getaddrinfo", lambda *args, **kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.8", 443))
    ])
    with pytest.raises(ValueError, match="private network"):
        routes._resolved_public_addresses("images.example", 443)

    class RedirectResponse:
        status = 302
        def getheader(self, name):
            return "http://127.0.0.1/private.png" if name == "Location" else None

    connections = []
    class FakeConnection:
        def __init__(self, *args, **kwargs): connections.append(self)
        def request(self, *args, **kwargs): pass
        def getresponse(self): return RedirectResponse()
        def close(self): pass

    monkeypatch.setattr(routes, "_resolved_public_addresses", lambda *_: ["93.184.216.34"])
    monkeypatch.setattr(routes, "_PinnedHTTPConnection", FakeConnection)
    with pytest.raises(ValueError, match="private network"):
        routes._download_public_image("http://images.example/start")
    assert len(connections) == 1


def test_scene_plan_endpoint_groups_by_word_count_without_inventing_times():
    from app.quran_data import get_ayahs
    ayah = get_ayahs(2, 282, 282)[0]
    response = create_app().test_client().post("/api/scenes/plan", json={
        "ayahs": [ayah], "ayah_start": 282, "words_per_scene": 7,
        "aspect_ratio": "9:16", "wrap_width": 85, "max_lines": 4,
        "font_id": "naskh", "show_surah_title": True,
    })
    assert response.status_code == 200, response.json
    assert response.json["count"] > 1
    assert response.json["approximate_timing"] is True
    scenes = response.json["scenes"]
    assert all(scene["word_count"] <= 7 for scene in scenes)
    assert all(scene["timing_mode"] == "word_timing_pending" for scene in scenes)
    assert all(scene["duration"] is None and scene["start_time"] is None for scene in scenes)
    assert "word-length estimate" in response.json["timing_note"]
    assert "".join(ayah.split()) == "".join("".join(scene["text"].split()) for scene in scenes)


def test_scene_plan_restores_saved_ayah_edits_across_narrowed_range():
    client = create_app(TestConfig).test_client()
    ayahs = [
        "أَوَّلٌ",
        "ثَانٍ ثَالِثٌ رَابِعٌ خَامِسٌ",
        "سَادِسٌ",
        "سَابِعٌ ثَامِنٌ تَاسِعٌ عَاشِرٌ",
        "حَادِيَ عَشَرَ",
    ]
    edits = [
        {"ayah_number":2, "source_text":ayahs[1], "scenes":[
            {"ayah_number":2, "scene_id":"ayah-2-first", "text":"ثَانٍ ثَالِثٌ", "locked":False, "manual_duration":2.75},
            {"ayah_number":2, "scene_id":"ayah-2-rest", "text":"رَابِعٌ خَامِسٌ", "locked":False, "manual_duration":1.25},
        ]},
        {"ayah_number":4, "source_text":ayahs[3], "scenes":[
            {"ayah_number":4, "scene_id":"ayah-4-first", "text":"سَابِعٌ ثَامِنٌ", "locked":True},
            {"ayah_number":4, "scene_id":"ayah-4-rest", "text":"تَاسِعٌ عَاشِرٌ", "locked":False},
        ]},
    ]
    full_payload = {"ayahs":ayahs, "ayah_start":1, "words_per_scene":30, "scene_edits":edits}
    full = client.post("/api/scenes/plan", json=full_payload)
    assert full.status_code == 200, full.json
    assert [row["text"] for row in full.json["scenes"] if row["ayah_number"] == 2] == [
        "ثَانٍ ثَالِثٌ", "رَابِعٌ خَامِسٌ",
    ]
    assert [row["manual_duration"] for row in full.json["scenes"] if row["ayah_number"] == 2] == [2.75, 1.25]
    assert [row["text"] for row in full.json["scenes"] if row["ayah_number"] == 4] == [
        "سَابِعٌ ثَامِنٌ", "تَاسِعٌ عَاشِرٌ",
    ]

    narrowed = client.post("/api/scenes/plan", json={
        **full_payload, "ayahs":ayahs[:3],
    })
    assert narrowed.status_code == 200, narrowed.json
    assert all(row["ayah_number"] <= 3 for row in narrowed.json["scenes"])
    assert [row["text"] for row in narrowed.json["scenes"] if row["ayah_number"] == 2] == [
        "ثَانٍ ثَالِثٌ", "رَابِعٌ خَامِسٌ",
    ]
    assert [row["manual_duration"] for row in narrowed.json["scenes"] if row["ayah_number"] == 2] == [2.75, 1.25]

    expanded = client.post("/api/scenes/plan", json=full_payload)
    assert expanded.status_code == 200, expanded.json
    assert [row["text"] for row in expanded.json["scenes"] if row["ayah_number"] == 4] == [
        "سَابِعٌ ثَامِنٌ", "تَاسِعٌ عَاشِرٌ",
    ]
    assert [row["manual_duration"] for row in expanded.json["scenes"] if row["ayah_number"] == 2] == [2.75, 1.25]
    assert [row["locked"] for row in expanded.json["scenes"] if row["ayah_number"] == 4] == [True, False]

    shifted_start = client.post("/api/scenes/plan", json={
        **full_payload, "ayah_start":3, "ayahs":ayahs[2:],
    })
    assert shifted_start.status_code == 200, shifted_start.json
    assert all(row["ayah_number"] >= 3 for row in shifted_start.json["scenes"])
    assert [row["text"] for row in shifted_start.json["scenes"] if row["ayah_number"] == 4] == [
        "سَابِعٌ ثَامِنٌ", "تَاسِعٌ عَاشِرٌ",
    ]

    default_groups = {}
    for row in expanded.json["default_scenes"]:
        default_groups.setdefault(row["ayah_number"], []).append(row)
    defaults_for_reset_range = [
        {"ayah_number":number, "source_text":ayahs[number - 1], "scenes":rows}
        for number, rows in default_groups.items() if number <= 3
    ]
    reset_range = client.post("/api/scenes/plan", json={
        **full_payload, "ayahs":ayahs[:3], "scene_defaults":defaults_for_reset_range,
        "scene_edits":[],
    })
    assert reset_range.status_code == 200, reset_range.json
    assert [row["text"] for row in reset_range.json["scenes"] if row["ayah_number"] == 2] == [ayahs[1]]
    assert all(row["ayah_number"] <= 3 for row in reset_range.json["scenes"])

    after_reset_expansion = client.post("/api/scenes/plan", json={
        **full_payload, "scene_edits":[edits[1]],
    })
    assert after_reset_expansion.status_code == 200, after_reset_expansion.json
    assert [row["text"] for row in after_reset_expansion.json["scenes"] if row["ayah_number"] == 2] == [ayahs[1]]
    assert [row["text"] for row in after_reset_expansion.json["scenes"] if row["ayah_number"] == 4] == [
        "سَابِعٌ ثَامِنٌ", "تَاسِعٌ عَاشِرٌ",
    ]


def test_scene_plan_endpoint_validates_words_per_scene():
    response = create_app().test_client().post("/api/scenes/plan", json={
        "ayahs": ["بِسْمِ اللَّهِ"], "words_per_scene": 31,
    })
    assert response.status_code == 400
    assert "between 1 and 30" in response.json["error"]


def test_scene_redistribution_endpoint_updates_adjacent_word_groups():
    from app import create_app
    ayahs = ["أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ", "خَامِسٌ سَادِسٌ"]
    response = create_app().test_client().post("/api/scenes/redistribute", json={
        "ayah_start":1, "ayahs":ayahs, "scene_index":0, "word_count":3,
        "scenes":[
            {"ayah_number":1,"text":"أَوَّلٌ ثَانٍ"},
            {"ayah_number":1,"text":"ثَالِثٌ رَابِعٌ"},
            {"ayah_number":2,"text":ayahs[1]},
        ],
    })
    assert response.status_code == 200, response.json
    assert [row["text"] for row in response.json["scenes"]] == [
        "أَوَّلٌ ثَانٍ ثَالِثٌ", "رَابِعٌ", ayahs[1],
    ]
    assert response.json["max_words"] == 4


def test_scene_redistribution_keeps_timing_only_for_unchanged_scenes():
    ayahs = ["أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ", "خَامِسٌ سَادِسٌ"]
    response = create_app().test_client().post("/api/scenes/redistribute", json={
        "ayah_start":1, "ayahs":ayahs, "scene_index":0, "word_count":3,
        "scenes":[
            {"scene_id":"first", "ayah_number":1, "text":"أَوَّلٌ ثَانٍ", "manual_duration":1.2},
            {"scene_id":"second", "ayah_number":1, "text":"ثَالِثٌ رَابِعٌ", "manual_duration":1.4},
            {"scene_id":"other-ayah", "ayah_number":2, "text":ayahs[1], "manual_duration":.9},
        ],
    })
    assert response.status_code == 200, response.json
    rows = response.json["scenes"]
    assert [row.get("manual_duration") for row in rows] == [None, None, .9]


def test_scene_redistribution_rejects_zero_word_count():
    response = create_app().test_client().post("/api/scenes/redistribute", json={
        "ayah_start":1, "ayahs":["أَوَّلٌ ثَانٍ"], "scene_index":0,
        "word_count":0, "scenes":[{"ayah_number":1,"text":"أَوَّلٌ ثَانٍ"}],
    })
    assert response.status_code == 400
    assert "at least one" in response.json["error"]


def test_scene_redistribution_endpoint_preserves_existing_merge_action():
    ayahs = ["أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ", "خَامِسٌ سَادِسٌ"]
    response = create_app().test_client().post("/api/scenes/redistribute", json={
        "action":"merge_previous", "ayah_start":1, "ayahs":ayahs,
        "scene_index":1,
        "scenes":[
            {"ayah_number":1,"text":"أَوَّلٌ ثَانٍ"},
            {"ayah_number":1,"text":"ثَالِثٌ رَابِعٌ"},
            {"ayah_number":2,"text":ayahs[1]},
        ],
    })
    assert response.status_code == 200, response.json
    assert [scene["text"] for scene in response.json["scenes"]] == ayahs
    assert response.json["selected_scene_index"] == 0


def test_scene_redistribution_endpoint_splits_selected_scene_by_requested_word_count():
    ayah = "كَلِمَة١ كَلِمَة٢ كَلِمَة٣ كَلِمَة٤ كَلِمَة٥ كَلِمَة٦ كَلِمَة٧ كَلِمَة٨ كَلِمَة٩ كَلِمَة١٠ كَلِمَة١١ كَلِمَة١٢"
    response = create_app().test_client().post("/api/scenes/redistribute", json={
        "action":"split_by_word_count", "ayah_start":7, "ayahs":[ayah],
        "scene_index":0, "words_per_scene":4,
        "scenes":[{"ayah_number":7,"text":ayah}],
    })
    assert response.status_code == 200, response.json
    assert response.json["word_counts"] == [4,4,4]
    assert [len(row["text"].split()) for row in response.json["scenes"]] == [4,4,4]
    assert "".join(ayah.split()) == "".join("".join(row["text"].split()) for row in response.json["scenes"])


def test_scene_redistribution_endpoint_supports_locks_and_exact_text_edits():
    ayah = "أَوَّلٌ ثَانٍ ثَالِثٌ رَابِعٌ"
    scenes = [
        {"scene_id":"opening","ayah_number":1,"text":"أَوَّلٌ ثَانٍ"},
        {"scene_id":"closing","ayah_number":1,"text":"ثَالِثٌ رَابِعٌ"},
    ]
    client = create_app(TestConfig).test_client()
    locked = client.post("/api/scenes/redistribute", json={
        "action":"set_lock", "ayah_start":1, "ayahs":[ayah], "scenes":scenes,
        "scene_index":1, "locked":True,
    })
    assert locked.status_code == 200, locked.json
    assert locked.json["locked"] is True
    assert locked.json["scenes"][1]["scene_id"] == "closing"
    edited = client.post("/api/scenes/redistribute", json={
        "action":"edit_text", "ayah_start":1, "ayahs":[ayah], "scenes":scenes,
        "scene_index":0, "text":"أَوَّلٌ ثَانٍ ثَالِثٌ",
    })
    assert edited.status_code == 200, edited.json
    assert [scene["text"] for scene in edited.json["scenes"]] == ["أَوَّلٌ ثَانٍ ثَالِثٌ", "رَابِعٌ"]
    invalid = client.post("/api/scenes/redistribute", json={
        "action":"edit_text", "ayah_start":1, "ayahs":[ayah], "scenes":scenes,
        "scene_index":0, "text":"ثَانٍ أَوَّلٌ",
    })
    assert invalid.status_code == 400
    assert "exact next words" in invalid.json["error"]


def test_caption_preview_returns_pillow_caption_for_selected_video_template():
    response = create_app().test_client().post("/api/caption-preview", json={
        "text": "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ",
        "aspect_ratio": "9:16",
        "caption_style": "Dynamic Karaoke (Glow)",
        "caption_color": "gold",
        "wrap_width": 75,
    })
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    from io import BytesIO
    from PIL import Image
    image = Image.open(BytesIO(response.data))
    assert image.mode == "RGBA"
    assert image.width <= 810
    assert image.height > 0


def test_caption_preview_uses_arabic_only_surah_header_and_number(monkeypatch):
    import app.routes as routes
    from PIL import Image
    captured = {}

    def fake_renderer(text, **kwargs):
        captured.update(kwargs)
        return Image.new("RGBA", (320, 160), (0, 0, 0, 0))

    monkeypatch.setattr(routes, "render_caption_image", fake_renderer)
    response = create_app(TestConfig).test_client().post("/api/caption-preview", json={
        "text": "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ",
        "show_surah_title": True, "surah": 55, "ayah": 13,
        "surah_font_id": "kufi", "ayah_number_font_id": "sans_bold",
        "surah_opacity": .72, "ayah_number_opacity": .84,
        "surah_placement": "below", "ayah_number_placement": "above",
    })
    assert response.status_code == 200
    assert captured["surah_title"] == routes._surah_caption_title(55)
    assert "SURAH" not in captured["surah_title"]
    assert captured["ayah_number"] == 13
    assert captured["aspect_ratio"] == "9:16"
    assert captured["caption_style"] == "golden_illuminated"
    assert captured["caption_color"] == "gold"
    assert captured["output_size"] == (1080, 1920)
    assert captured["surah_font_path"].name == "NotoKufiArabic-Regular.ttf"
    assert captured["ayah_number_font_path"].name == "NotoSansArabic-Bold.ttf"
    assert captured["surah_opacity"] == .72
    assert captured["ayah_number_opacity"] == .84
    assert captured["surah_placement"] == "below"
    assert captured["ayah_number_placement"] == "above"


def test_timing_endpoint_returns_selected_ayah_sequence(monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes, "get_recitation_timings", lambda *args: [
        {"ayah": 13, "start_time": 1200, "end_time": 3200},
        {"ayah": 14, "start_time": 3400, "end_time": 5800},
    ])
    response = create_app(TestConfig).test_client().get(
        "/api/reciters/mishary_alafasy/timings?surah=55&start=13&end=14"
    )
    assert response.status_code == 200
    assert response.json["timings"] == [
        {"ayah": 13, "start": 1.2, "end": 3.2},
        {"ayah": 14, "start": 3.4, "end": 5.8},
    ]
    assert response.json["audio_start"] == pytest.approx(1.2)
    assert response.json["audio_end"] == pytest.approx(5.8)
    assert response.json["audio_duration"] == pytest.approx(4.6)
    assert response.json["audio_url"].startswith("/api/reciters/mishary_alafasy/audio-preview?")


def test_timing_endpoint_includes_word_timestamps_from_matching_recitation(monkeypatch):
    import app.routes as routes
    monkeypatch.setattr(routes, "get_chapter_word_timing", lambda *args: {
        "audio_url": "https://audio.example/chapter.mp3",
        "ayahs": [{"ayah":13, "start_time":1200, "end_time":3200, "segments":[
            {"index":0,"start_ms":1400,"end_ms":1750},
            {"index":1,"start_ms":1900,"end_ms":2250},
        ]}],
    })
    response = create_app(TestConfig).test_client().get(
        "/api/reciters/mishary_alafasy/timings?surah=55&start=13&end=13"
    )
    assert response.status_code == 200, response.json
    assert response.json["audio_url"].startswith("/api/reciters/mishary_alafasy/audio-preview?")
    assert response.json["audio_start"] == pytest.approx(1.2)
    assert response.json["audio_end"] == pytest.approx(3.2)
    assert response.json["timing_source"] == "quran_foundation_word"
    assert response.json["timings"][0]["words"] == [
        {"index":0,"start":.2,"end":.55},
        {"index":1,"start":.7,"end":1.05},
    ]


def test_recitation_preview_endpoint_serves_only_selected_ayah_audio(tmp_path, monkeypatch):
    import wave
    import numpy as np
    import app.routes as routes

    sample_rate = 44100
    time_axis = np.arange(int(sample_rate * 3.5), dtype=np.float64) / sample_rate
    samples = np.zeros_like(time_axis)
    for start, end, frequency in ((.5, 1.5, 220), (1.5, 2.5, 440), (2.5, 3.5, 880)):
        active = (time_axis >= start) & (time_axis < end)
        samples[active] = .35 * np.sin(2 * np.pi * frequency * time_axis[active])
    source_path = tmp_path / "chapter-with-next-ayah.wav"
    with wave.open(str(source_path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes((samples * 32767).astype("int16").tobytes())
    monkeypatch.setattr(routes, "download_recitation", lambda *_args, **_kwargs: SimpleNamespace(
        path=source_path, start=.5, end=2.5,
    ))
    app = create_app(TestConfig)
    app.config["AUDIO_PREVIEW_FOLDER"] = tmp_path / "preview-cache"

    response = app.test_client().get(
        "/api/reciters/mishary_alafasy/audio-preview?surah=18&start=29&end=30"
    )

    assert response.status_code == 200
    assert response.mimetype == "audio/wav"
    from io import BytesIO
    with wave.open(BytesIO(response.data), "rb") as audio_file:
        assert audio_file.getframerate() == 48000
        assert audio_file.getnframes() == 2 * 48000
        interleaved = np.frombuffer(audio_file.readframes(audio_file.getnframes()), dtype="<i2").astype(float)
        selected = interleaved.reshape(-1, audio_file.getnchannels()).mean(axis=1) / 32768
    first = selected[int(.2 * 48000):int(.4 * 48000)]
    second = selected[int(1.6 * 48000):int(1.8 * 48000)]
    assert np.sqrt(np.mean(first ** 2)) > .15
    assert np.sqrt(np.mean(second ** 2)) > .15
    first_reference = np.sin(2 * np.pi * 220 * (np.arange(len(first)) / 48000 + .7))
    second_reference = np.sin(2 * np.pi * 440 * (np.arange(len(second)) / 48000 + 2.1))
    assert np.corrcoef(first_reference, first)[0, 1] > .98
    assert np.corrcoef(second_reference, second)[0, 1] > .98


def test_generate_rejects_invalid_range_before_audio_fetch():
    response = create_app(TestConfig).test_client().post("/api/generate", json={
        "surah": 93, "ayah_start": 1, "ayah_end": 12, "aspect_ratio": "9:16"
    })
    assert response.status_code == 400


def test_generate_validates_export_fps_and_custom_dimensions_before_audio_fetch():
    client = create_app(TestConfig).test_client()
    base = {"surah": 55, "ayah_start": 13, "ayah_end": 13, "aspect_ratio": "9:16"}
    bad_fps = client.post("/api/generate", json={**base, "fps": 50})
    assert bad_fps.status_code == 400
    assert "24, 25, 30, or 60" in bad_fps.json["error"]
    bad_size = client.post("/api/generate", json={
        **base, "resolution": "custom", "custom_width": 1280, "custom_height": 720,
    })
    assert bad_size.status_code == 400
    assert "must match" in bad_size.json["error"]


def test_generate_requires_translation_lines_to_match_selected_ayah_count():
    response = create_app(TestConfig).test_client().post("/api/generate", json={
        "surah": 55, "ayah_start": 13, "ayah_end": 14,
        "translation_text": "Only one verse translation", "show_translation": True,
    })
    assert response.status_code == 400
    assert "one translation line per selected ayah" in response.json["error"]


def test_viewer_header_options_validate_language_and_range_format():
    import pytest
    import app.routes as routes

    options = routes._viewer_layer_options({
        "viewer_header_surah_enabled": "false",
        "viewer_header_surah_language": "both",
        "viewer_header_range_enabled": "true",
        "viewer_header_range_language": "arabic",
        "viewer_header_range_format": "compact",
        "viewer_header_qari_enabled": "false",
    })
    assert options["show_header_surah"] is False
    assert options["header_surah_language"] == "both"
    assert options["show_ayah_range"] is True
    assert options["ayah_range_language"] == "arabic"
    assert options["ayah_range_format"] == "compact"
    assert options["show_qari_in_header"] is False
    with pytest.raises(ValueError, match="Choose English or Arabic"):
        routes._viewer_layer_options({"viewer_header_range_language": "french"})


def test_viewer_header_can_render_without_surah_range_or_qari():
    from app.reel_viewer import render_static_layer

    image = render_static_layer(
        (540, 960), surah_name="Ar-Rahmaan", surah_number=55,
        ayah_number=13, reciter_name="Mishary Alafasy",
        options={"show_viewer_title": True, "show_header_surah": False,
                 "show_ayah_range": False, "show_qari_in_header": False,
                 "show_reciter_badge": False, "show_translation": False},
    )
    assert image.mode == "RGBA"
    # The title icon remains visible with every dynamic header label hidden.
    assert image.getbbox() is not None
    no_icon = render_static_layer(
        (540, 960), surah_name="Ar-Rahmaan", surah_number=55,
        ayah_number=13, reciter_name="Mishary Alafasy",
        options={"show_viewer_title": True, "show_header_surah": False,
                 "show_ayah_range": False, "show_qari_in_header": False,
                 "show_title_icon": False, "show_reciter_badge": False,
                 "show_translation": False},
    )
    assert no_icon.getbbox() is None


def test_generate_success_uses_local_ayah_text_and_selected_qari(monkeypatch, tmp_path):
    import app.routes as routes
    track_path = tmp_path / "recitation.mp3"
    track_path.write_bytes(b"audio")
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        Path(kwargs["output_path"]).write_bytes(b"complete-mp4" * 200)
        return {"path": str(kwargs["output_path"]), "duration": 4.16, "width": 1080,
                "height": 1920, "has_audio": True, "scene_count": 2,
                "phrase_timing_mode":"weighted_estimate", "phrase_timing_approximate":True}

    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: SimpleNamespace(
        path=track_path, start=1.0, end=5.16, ayah_durations=[4.16]))
    monkeypatch.setattr(routes, "render_reel", fake_render)
    monkeypatch.setattr(routes, "validate_rendered_output", lambda *args, **kwargs: {"playable":True})

    class Config(TestConfig):
        OUTPUT_FOLDER = tmp_path / "outputs"

    client = create_app(Config).test_client()
    from app.quran_data import get_ayahs
    ayah = get_ayahs(55, 13, 13)[0]
    words = ayah.split()
    midpoint = len(words) // 2
    scene_overrides = [
        {"scene_id":"first-half","ayah_number":13,"text":" ".join(words[:midpoint]),"locked":True},
        {"scene_id":"second-half","ayah_number":13,"text":" ".join(words[midpoint:]),"locked":False},
    ]
    response = client.post("/api/generate", json={
        "surah": 55, "ayah_start": 13, "ayah_end": 13,
        "reciter_id": "mishary_alafasy", "aspect_ratio": "9:16", "theme": "desert_dawn"
        , "scene_overrides": scene_overrides
        , "caption_color": "gold", "wrap_width": 75,
        "show_quran_text": False, "viewer_title_enabled": False,
        "viewer_title_icon_enabled": False, "show_translation": True,
        "viewer_header_surah_enabled": True,
        "viewer_header_surah_language": "both",
        "viewer_header_range_enabled": True,
        "viewer_header_range_language": "arabic",
        "viewer_header_range_format": "compact",
        "viewer_header_qari_enabled": True,
        "reciter_label": "Sheikh Mishary",
        "translation_text": "So which of the favors of your Lord would you deny?",
        "show_waveform": False, "show_reciter_badge": False,
        "show_progress": True, "progress_color": "#006aff",
    })
    assert response.status_code == 202, response.json
    job = client.get(response.json["status_url"])
    assert job.json["status"] == "complete", job.json
    result = job.json["result"]
    assert result["has_audio"] is True
    assert result["reciter"] == "Mishary Rashid Alafasy"
    assert result["theme"] == "desert_dawn"
    assert result["phrase_timing_mode"] == "weighted_estimate"
    assert result["phrase_timing_approximate"] is True
    assert "approximate" in result["timing_note"]
    assert captured["scene_overrides"] == scene_overrides
    assert "تُكَذِّبَانِ" in captured["ayahs"][0]
    assert captured["audio_start"] == 1.0
    assert captured["theme"] == "desert_dawn"
    assert captured["caption_color"] == "gold"
    assert captured["wrap_width"] == 75
    assert captured["show_surah_title"] is False
    assert captured["surah_title"] == routes._surah_caption_title(55)
    assert captured["caption_position"] == "center"
    assert captured["caption_style"] == "golden_illuminated"
    assert captured["text_bg_enabled"] is True
    assert captured["text_bg_color"] == "#090806"
    assert captured["corner_radius"] == 28
    assert captured["output_size"] == (1080, 1920)
    assert captured["fps"] == 30
    assert captured["quality"] == "balanced"
    assert captured["show_quran_text"] is False
    assert captured["viewer_options"]["show_viewer_title"] is False
    assert captured["viewer_options"]["show_title_icon"] is False
    assert captured["viewer_options"]["show_header_surah"] is True
    assert captured["viewer_options"]["header_surah_language"] == "both"
    assert captured["viewer_options"]["header_surah_arabic"] == routes.SURAHS_BY_NUMBER[55]["name_arabic"]
    assert captured["viewer_options"]["show_ayah_range"] is True
    assert captured["viewer_options"]["ayah_range_start"] == 13
    assert captured["viewer_options"]["ayah_range_end"] == 13
    assert captured["viewer_options"]["ayah_range_language"] == "arabic"
    assert captured["viewer_options"]["ayah_range_format"] == "compact"
    assert captured["viewer_options"]["show_qari_in_header"] is True
    assert captured["viewer_options"]["reciter_label"] == "Sheikh Mishary"
    assert captured["viewer_options"]["show_translation"] is True
    assert captured["viewer_options"]["show_waveform"] is False
    assert captured["viewer_options"]["show_reciter_badge"] is False
    assert captured["viewer_options"]["progress_color"] == "#006aff"
    assert captured["translation_lines"] == ["So which of the favors of your Lord would you deny?"]
    assert captured["crf"] == 23
    assert not track_path.exists()


def test_background_render_worker_builds_download_url_without_request_context(monkeypatch, tmp_path):
    import time
    import app.routes as routes

    track_path = tmp_path / "recitation.mp3"
    track_path.write_bytes(b"audio")

    def fake_render(**kwargs):
        Path(kwargs["output_path"]).write_bytes(b"complete-mp4" * 200)
        return {"path": str(kwargs["output_path"]), "duration": 4.0,
                "width": 1080, "height": 1920, "has_audio": True}

    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: SimpleNamespace(
        path=track_path, start=0.0, end=4.0, ayah_durations=[4.0]))
    monkeypatch.setattr(routes, "render_reel", fake_render)
    monkeypatch.setattr(routes, "validate_rendered_output", lambda *args, **kwargs: {"playable": True})

    class AsyncConfig(TestConfig):
        RENDER_JOBS_INLINE = False
        OUTPUT_FOLDER = tmp_path / "outputs"

    client = create_app(AsyncConfig).test_client()
    response = client.post("/api/generate", json={
        "surah": 55, "ayah_start": 13, "ayah_end": 13,
        "reciter_id": "mishary_alafasy", "aspect_ratio": "9:16",
    })
    assert response.status_code == 202, response.json

    deadline = time.monotonic() + 3
    job = None
    while time.monotonic() < deadline:
        job = client.get(response.json["status_url"]).json
        if job["status"] in {"complete", "failed", "cancelled"}:
            break
        time.sleep(.01)

    assert job["status"] == "complete", job
    result = job["result"]
    assert result["download_url"] == f"/outputs/{result['filename']}"
    downloaded = client.get(result["download_url"])
    assert downloaded.status_code == 200
    assert downloaded.data.startswith(b"complete-mp4")


def test_generate_applies_selected_complete_video_template(monkeypatch, tmp_path):
    import app.routes as routes
    track_path = tmp_path / "recitation.mp3"
    track_path.write_bytes(b"audio")
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        Path(kwargs["output_path"]).write_bytes(b"complete-mp4" * 200)
        return {"path": str(kwargs["output_path"]), "duration": 4.0, "width": 1080,
                "height": 1920, "has_audio": True}

    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: SimpleNamespace(
        path=track_path, start=0.0, end=4.0, ayah_durations=[4.0]))
    monkeypatch.setattr(routes, "render_reel", fake_render)
    monkeypatch.setattr(routes, "validate_rendered_output", lambda *args, **kwargs: {"playable":True})

    class Config(TestConfig):
        OUTPUT_FOLDER = tmp_path / "outputs"

    client = create_app(Config).test_client()
    response = client.post("/api/generate", json={
        "surah": 55, "ayah_start": 13, "ayah_end": 13,
        "reciter_id": "mishary_alafasy", "aspect_ratio": "9:16",
        "template_id": "emerald_serenity",
        "surah_font_id": "kufi_bold", "ayah_number_font_id": "sans",
        "surah_opacity": ".7", "ayah_number_opacity": ".8",
        "surah_placement": "below", "ayah_number_placement": "above",
    })
    assert response.status_code == 202, response.json
    result = client.get(response.json["status_url"]).json["result"]
    assert result["theme"] == "olive_garden"
    assert result["template_id"] == "emerald_serenity"
    assert captured["caption_style"] == "quranic"
    assert captured["caption_color"] == "ivory"
    assert captured["show_surah_title"] is True
    assert captured["caption_position"] == "center"
    assert captured["text_bg_color"] == "#061e16"
    assert captured["glow_type"] == "emerald"
    assert captured["surah_font_path"].name == "NotoKufiArabic-Bold.ttf"
    assert captured["ayah_number_font_path"].name == "NotoSansArabic-Regular.ttf"
    assert captured["surah_opacity"] == .7
    assert captured["ayah_number_opacity"] == .8
    assert captured["surah_placement"] == "below"
    assert captured["ayah_number_placement"] == "above"


def test_generate_accepts_ordered_background_video_clips_with_edit_settings(monkeypatch, tmp_path):
    import io
    import json
    import app.routes as routes
    track_path = tmp_path / "recitation.mp3"
    track_path.write_bytes(b"audio")
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        assert [Path(item["path"]).read_bytes() for item in kwargs["background_clips"]] == [b"clip-a", b"clip-b"]
        Path(kwargs["output_path"]).write_bytes(b"complete-mp4" * 200)
        return {"path": str(kwargs["output_path"]), "duration": 4, "width": 1080, "height": 1920}

    monkeypatch.setattr(routes, "validate_background_upload", lambda *args: {
        "width": 96, "height": 54, "duration": 5.0,
    })
    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: SimpleNamespace(
        path=track_path, start=0, end=4, ayah_durations=[4]))
    monkeypatch.setattr(routes, "render_reel", fake_render)
    monkeypatch.setattr(routes, "validate_rendered_output", lambda *args, **kwargs: {"playable":True})

    class Config(TestConfig):
        OUTPUT_FOLDER = tmp_path / "outputs"

    client = create_app(Config).test_client()
    response = client.post("/api/generate", data={
        "surah": "55", "ayah_start": "13", "ayah_end": "13", "aspect_ratio": "9:16",
        "reciter_id": "mishary_alafasy",
        "background_audio_enabled": "true", "background_audio_volume": ".12",
        "sequence_enabled": "true", "transitions_enabled": "true",
        "background_clip_settings": json.dumps([
            {"start": .25, "end": 2.5, "speed": 1.25, "transition": "cut", "transition_duration": 0},
            {"start": 1, "end": 4.5, "speed": .75, "transition": "crossfade", "transition_duration": .6},
        ]),
        "background_clips": [
            (io.BytesIO(b"clip-a"), "clip-a.mp4", "video/mp4"),
            (io.BytesIO(b"clip-b"), "clip-b.mp4", "video/mp4"),
        ],
    }, content_type="multipart/form-data")
    assert response.status_code == 202, response.json
    assert captured["background_path"] is None
    assert len(captured["background_clips"]) == 2
    assert captured["background_clips"][0]["start"] == .25
    assert captured["background_clips"][0]["speed"] == 1.25
    assert captured["background_clips"][1]["transition"] == "crossfade"
    assert captured["transitions_enabled"] is True
    assert captured["background_audio_enabled"] is True
    assert captured["background_audio_volume"] == .12
    snapshot = client.get(response.json["status_url"])
    assert snapshot.json["status"] == "complete"
    assert snapshot.json["result"]["background_clip_count"] == 2


def test_generate_uses_only_one_custom_background_when_sequence_mode_is_off(monkeypatch, tmp_path):
    import io
    import app.routes as routes
    track_path = tmp_path / "recitation.mp3"
    track_path.write_bytes(b"audio")
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        assert Path(kwargs["background_path"]).read_bytes() == b"first-image"
        assert not kwargs["background_clips"]
        Path(kwargs["output_path"]).write_bytes(b"complete-mp4" * 200)
        return {"path": str(kwargs["output_path"]), "duration": 4, "width": 1080, "height": 1920}

    monkeypatch.setattr(routes, "validate_background_upload", lambda *args: {"width": 96, "height": 54})
    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: SimpleNamespace(
        path=track_path, start=0, end=4, ayah_durations=[4]))
    monkeypatch.setattr(routes, "render_reel", fake_render)
    monkeypatch.setattr(routes, "validate_rendered_output", lambda *args, **kwargs: {"playable":True})

    class Config(TestConfig):
        OUTPUT_FOLDER = tmp_path / "outputs"

    response = create_app(Config).test_client().post("/api/generate", data={
        "surah":"55", "ayah_start":"13", "ayah_end":"13", "reciter_id":"mishary_alafasy",
        "background_clips":[
            (io.BytesIO(b"first-image"),"first.png","image/png"),
            (io.BytesIO(b"ignored-image"),"second.png","image/png"),
        ],
    }, content_type="multipart/form-data")
    assert response.status_code == 202, response.json
    assert captured["background_animation_enabled"] is False
    assert captured["background_animation_preset"] == "static"


def test_generate_renders_selected_five_scene_background_template(monkeypatch, tmp_path):
    import app.routes as routes
    from app.background_sequence_templates import BACKGROUND_SEQUENCE_TEMPLATES
    track_path = tmp_path / "recitation.mp3"
    track_path.write_bytes(b"audio")
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        Path(kwargs["output_path"]).write_bytes(b"complete-mp4" * 200)
        return {"path": str(kwargs["output_path"]), "duration": 4, "width": 480, "height": 852}

    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: SimpleNamespace(
        path=track_path, start=0, end=4, ayah_durations=[4]))
    monkeypatch.setattr(routes, "render_reel", fake_render)
    monkeypatch.setattr(routes, "validate_rendered_output", lambda *args, **kwargs: {"playable":True})

    class Config(TestConfig):
        OUTPUT_FOLDER = tmp_path / "outputs"

    template_id = "nature_in_motion"
    client = create_app(Config).test_client()
    response = client.post("/api/generate", data={
        "surah":"55", "ayah_start":"13", "ayah_end":"13", "reciter_id":"mishary_alafasy",
        "resolution":"480p", "quality":"fast", "sequence_enabled":"true",
        "background_sequence_template":template_id, "transitions_enabled":"true",
        "background_animation_enabled":"true", "background_animation_preset":"gentle_movement",
        "background_animation_start":"1.5",
        "background_atmosphere_enabled":"true", "background_atmosphere_intensity":".6",
        "background_atmosphere_duration":"48", "background_atmosphere_speed":".9",
        "background_atmosphere_start":"2.5",
    })
    assert response.status_code == 202, response.json
    expected = BACKGROUND_SEQUENCE_TEMPLATES[template_id]["scenes"]
    assert len(captured["background_clips"]) == 5
    assert [Path(spec["path"]).stem for spec in captured["background_clips"]] == [scene["theme"] for scene in expected]
    assert all(Path(spec["path"]).is_file() for spec in captured["background_clips"])
    assert captured["transitions_enabled"] is True
    assert captured["background_animation_enabled"] is True
    assert captured["background_animation_start"] == 1.5
    assert captured["background_atmosphere_enabled"] is True
    assert captured["background_atmosphere_intensity"] == .6
    assert captured["background_atmosphere_duration"] == 48
    assert captured["background_atmosphere_speed"] == .9
    assert captured["background_atmosphere_start"] == 2.5
    status = client.get(response.json["status_url"])
    assert status.json["status"] == "complete"
    assert status.json["result"]["background_sequence_template"] == template_id


def test_generate_accepts_mixed_sequential_images_and_videos_with_animation_settings(monkeypatch, tmp_path):
    import io
    import json
    import app.routes as routes
    track_path = tmp_path / "recitation.mp3"
    track_path.write_bytes(b"audio")
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        assert [Path(item["path"]).read_bytes() for item in kwargs["background_clips"]] == [b"still", b"motion"]
        Path(kwargs["output_path"]).write_bytes(b"complete-mp4" * 200)
        return {"path": str(kwargs["output_path"]), "duration": 4, "width": 1080, "height": 1920}

    monkeypatch.setattr(routes, "validate_background_upload", lambda path, extension: {
        "width": 96, "height": 54, **({"duration":2.0} if extension == ".mp4" else {})})
    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: SimpleNamespace(
        path=track_path, start=0, end=4, ayah_durations=[4]))
    monkeypatch.setattr(routes, "render_reel", fake_render)
    monkeypatch.setattr(routes, "validate_rendered_output", lambda *args, **kwargs: {"playable":True})

    class Config(TestConfig):
        OUTPUT_FOLDER = tmp_path / "outputs"

    response = create_app(Config).test_client().post("/api/generate", data={
        "surah":"55", "ayah_start":"13", "ayah_end":"13", "reciter_id":"mishary_alafasy",
        "sequence_enabled":"true", "transitions_enabled":"true", "default_background_transition":"fade_black",
        "background_animation_enabled":"true", "background_animation_preset":"cinematic_zoom",
        "background_animation_intensity":".4", "background_animation_duration":"8", "background_animation_speed":"1.2",
        "background_clip_settings":json.dumps([
            {"duration":2,"transition":"fade_black","transition_duration":.6},
            {"start":0,"end":2,"speed":1,"transition":"slide_left","transition_duration":.4},
        ]),
        "background_clips":[
            (io.BytesIO(b"still"),"still.png","image/png"),
            (io.BytesIO(b"motion"),"motion.mp4","video/mp4"),
        ],
    }, content_type="multipart/form-data")
    assert response.status_code == 202, response.json
    assert captured["background_clips"][0]["duration"] == 2
    assert captured["background_clips"][1]["transition"] == "slide_left"
    assert captured["background_animation_enabled"] is True
    assert captured["background_animation_preset"] == "cinematic_zoom"
    assert captured["transitions_enabled"] is True


def test_caption_option_overrides_are_normalized_in_one_shared_merge():
    from app.routes import _caption_options
    from app.video_templates import VIDEO_TEMPLATES
    template = VIDEO_TEMPLATES["golden_calligraphy"]
    options = _caption_options(template, {
        "text_bg_enabled": "false", "text_bg_opacity": "0.35",
        "glow_type": "blue", "glow_radius": "9", "caption_style": "soft_white",
    })
    assert options["text_bg_enabled"] == "false"
    assert options["text_bg_opacity"] == "0.35"
    assert options["glow_type"] == "blue"
    assert options["glow_radius"] == "9"
    assert options["corner_radius"] == template["corner_radius"]
    assert "caption_style" not in options


def test_generate_accepts_valid_background_video_and_fit_controls(monkeypatch, tmp_path):
    import io
    import app.routes as routes
    track_path = tmp_path / "recitation.mp3"
    track_path.write_bytes(b"audio")
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        assert Path(kwargs["background_path"]).read_bytes() == b"video-data"
        Path(kwargs["output_path"]).write_bytes(b"complete-mp4" * 200)
        return {"path": str(kwargs["output_path"]), "duration": 4.0, "width": 1080,
                "height": 1920, "has_audio": True}

    monkeypatch.setattr(routes, "validate_background_upload", lambda *args: {"width": 64, "height": 32, "duration": 1})
    monkeypatch.setattr(routes, "download_recitation", lambda *args, **kwargs: SimpleNamespace(
        path=track_path, start=0.0, end=4.0, ayah_durations=[4.0]))
    monkeypatch.setattr(routes, "render_reel", fake_render)
    monkeypatch.setattr(routes, "validate_rendered_output", lambda *args, **kwargs: {"playable":True})

    class Config(TestConfig):
        OUTPUT_FOLDER = tmp_path / "outputs"

    client = create_app(Config).test_client()
    response = client.post("/api/generate", data={
        "surah": "55", "ayah_start": "13", "ayah_end": "13", "aspect_ratio": "9:16",
        "reciter_id": "mishary_alafasy", "background_fit": "blurred", "crop_x": "0.2",
        "crop_y": "0.8", "background_speed": "1.25", "background_loop": "true",
        "background_brightness": "1.2", "background_contrast": ".85",
        "background_saturation": "1.4", "background_overlay_color": "#123456",
        "background_overlay_opacity": ".2",
        "background": (io.BytesIO(b"video-data"), "background.mp4", "video/mp4"),
    }, content_type="multipart/form-data")
    assert response.status_code == 202, response.json
    assert client.get(response.json["status_url"]).json["status"] == "complete"
    assert captured["background_fit"] == "blurred"
    assert captured["crop_x"] == 0.2
    assert captured["crop_y"] == 0.8
    assert captured["background_speed"] == 1.25
    assert captured["background_loop"] is True
    assert captured["background_brightness"] == 1.2
    assert captured["background_contrast"] == .85
    assert captured["background_saturation"] == 1.4
    assert captured["background_overlay_color"] == "#123456"
    assert captured["background_overlay_opacity"] == .2


def test_background_upload_is_decoded_before_job_acceptance(tmp_path):
    from PIL import Image
    import pytest
    from app.routes import validate_background_upload
    valid = tmp_path / "wallpaper.png"
    Image.new("RGB", (64, 96), (12, 30, 42)).save(valid)
    assert validate_background_upload(valid, ".png") == {"width": 64, "height": 96}
    invalid = tmp_path / "broken.png"
    invalid.write_bytes(b"not an image")
    with pytest.raises(Exception):
        validate_background_upload(invalid, ".png")


def test_render_job_status_reports_real_progress_and_cancellation():
    from threading import Event
    import time
    from app.job_errors import JobCancelled
    from app.render_jobs import RenderJobManager

    manager = RenderJobManager(max_workers=1)
    started = Event()

    def worker(update, cancel_event):
        update(progress=31, phase="rendering", message="Encoding frames")
        started.set()
        while not cancel_event.wait(.01):
            pass
        raise JobCancelled()

    try:
        manager.submit("cancel-test", worker)
        assert started.wait(1)
        snapshot = manager.get("cancel-test")
        assert snapshot["progress"] == 31
        assert snapshot["phase"] == "rendering"
        manager.cancel("cancel-test")
        deadline = time.monotonic() + 1
        while manager.get("cancel-test")["status"] not in {"cancelled", "failed"} and time.monotonic() < deadline:
            time.sleep(.01)
        assert manager.get("cancel-test")["status"] == "cancelled"
    finally:
        manager.shutdown(wait=True)
