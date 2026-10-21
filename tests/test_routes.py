from types import SimpleNamespace

from app import create_app
from app.quraa_data import RECITERS
from app.quran_data import SURAHS


class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    OUTPUT_FOLDER = "/tmp/quran-reels-test-output"
    ARABIC_FONT = "/tmp/missing-font.ttf"


def test_studio_renders_light_template_with_all_surahs():
    response = create_app(TestConfig).test_client().get("/")
    assert response.status_code == 200
    assert b"Render High-Res Reel" in response.data
    assert b"114 - An-Naas" in response.data
    assert b"id=\"rendered-video\"" in response.data
    assert b"id=\"audio-file\"" not in response.data
    assert b"data-theme=\"marble_arch\"" in response.data
    assert len(SURAHS) == 114


def test_surah_endpoint_includes_all_114_chapters():
    response = create_app(TestConfig).test_client().get("/api/surahs")
    assert response.status_code == 200
    assert len(response.json["surahs"]) == 114
    assert sum(chapter["ayah_count"] for chapter in response.json["surahs"]) == 6236


def test_verse_endpoint_returns_arabic_range():
    response = create_app(TestConfig).test_client().get("/api/verses?surah=55&start=13&end=14")
    assert response.status_code == 200
    assert len(response.json["ayahs"]) == 2
    assert "تُكَذِّبَانِ" in response.json["ayahs"][0]


def test_verse_endpoint_rejects_out_of_range_ayah():
    response = create_app(TestConfig).test_client().get("/api/verses?surah=93&start=1&end=12")
    assert response.status_code == 400


def test_reciter_endpoint_returns_twenty_streamable_reciters():
    response = create_app(TestConfig).test_client().get("/api/reciters")
    assert response.status_code == 200
    assert len(response.json["reciters"]) == len(RECITERS) == 20
    assert all(item["audio_base_url"].startswith("https://") for item in RECITERS)


def test_reciter_preview_builds_selected_chapter_url():
    response = create_app(TestConfig).test_client().get("/api/reciters/mishary_alafasy/preview?surah=55")
    assert response.status_code == 200
    assert response.json["audio_url"].endswith("/055.mp3")


def test_background_endpoint_lists_twenty_presets():
    response = create_app(TestConfig).test_client().get("/api/backgrounds")
    assert response.status_code == 200
    assert len(response.json["backgrounds"]) == 20


def test_background_preview_returns_image_and_rejects_bad_ratio():
    client = create_app(TestConfig).test_client()
    response = client.get("/api/backgrounds/midnight_blue/preview?ratio=1:1")
    assert response.status_code == 200
    assert response.mimetype == "image/jpeg"
    assert client.get("/api/backgrounds/midnight_blue/preview?ratio=4:3").status_code == 400


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


def test_generate_rejects_invalid_range_before_audio_fetch():
    response = create_app(TestConfig).test_client().post("/api/generate", json={
        "surah": 93, "ayah_start": 1, "ayah_end": 12, "aspect_ratio": "9:16"
    })
    assert response.status_code == 400


def test_generate_success_uses_local_ayah_text_and_selected_qari(monkeypatch, tmp_path):
    import app.routes as routes
    track_path = tmp_path / "recitation.mp3"
    track_path.write_bytes(b"audio")
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        return {"path": str(kwargs["output_path"]), "duration": 4.16, "width": 1080,
                "height": 1920, "has_audio": True}

    monkeypatch.setattr(routes, "download_recitation", lambda *args: SimpleNamespace(
        path=track_path, start=1.0, end=5.16, ayah_durations=[4.16]))
    monkeypatch.setattr(routes, "render_reel", fake_render)

    class Config(TestConfig):
        OUTPUT_FOLDER = tmp_path / "outputs"

    response = create_app(Config).test_client().post("/api/generate", json={
        "surah": 55, "ayah_start": 13, "ayah_end": 13,
        "reciter_id": "mishary_alafasy", "aspect_ratio": "9:16", "theme": "desert_dawn"
        , "caption_color": "gold", "wrap_width": 75
    })
    assert response.status_code == 201, response.json
    assert response.json["has_audio"] is True
    assert response.json["reciter"] == "Mishary Rashid Alafasy"
    assert response.json["theme"] == "desert_dawn"
    assert "تُكَذِّبَانِ" in captured["ayahs"][0]
    assert captured["audio_start"] == 1.0
    assert captured["theme"] == "desert_dawn"
    assert captured["caption_color"] == "gold"
    assert captured["wrap_width"] == 75
    assert not track_path.exists()
