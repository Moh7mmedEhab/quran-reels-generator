import json
from urllib.error import URLError

import pytest

from app import create_app
from app import translations


class TranslationConfig:
    TESTING = True
    SECRET_KEY = "test"
    OUTPUT_FOLDER = None
    RENDER_JOBS_INLINE = True


def _api_response(surah=55):
    ayah_count = 78
    return {
        "code": 200,
        "data": {
            "number": surah,
            "edition": {"identifier": "en.sahih", "englishName": "Saheeh International"},
            "ayahs": [
                {"numberInSurah": number, "text": f"Verified translation for ayah {number}."}
                for number in range(1, ayah_count + 1)
            ],
        },
    }


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def read(self, _size=-1):
        return json.dumps(self.payload).encode("utf-8")


def test_translation_endpoint_returns_exact_ayah_range_and_caches_full_chapter(monkeypatch, tmp_path):
    TranslationConfig.OUTPUT_FOLDER = tmp_path
    requested = []

    def fetch(request, timeout):
        requested.append((request.full_url, timeout))
        return Response(_api_response())

    monkeypatch.setattr(translations, "urlopen", fetch)
    client = create_app(TranslationConfig).test_client()
    first = client.get("/api/translations?surah=55&start=13&end=14&edition=en.sahih")
    assert first.status_code == 200
    assert first.json["translator"] == "Saheeh International"
    assert first.json["source"] == "AlQuranCloud"
    assert first.json["cached"] is False
    assert first.json["ayahs"] == [
        {"ayah": 13, "text": "Verified translation for ayah 13."},
        {"ayah": 14, "text": "Verified translation for ayah 14."},
    ]
    assert requested[0][0] == "https://api.alquran.cloud/v1/surah/55/en.sahih"

    second = client.get("/api/translations?surah=55&start=13&end=14&edition=en.sahih")
    assert second.status_code == 200
    assert second.json["cached"] is True
    assert second.json["ayahs"] == first.json["ayahs"]
    assert len(requested) == 1
    assert (tmp_path / "translations" / "055-en.sahih.json").is_file()


def test_translation_endpoint_reports_network_failure_as_service_unavailable(monkeypatch, tmp_path):
    TranslationConfig.OUTPUT_FOLDER = tmp_path
    monkeypatch.setattr(translations, "urlopen", lambda *_args, **_kwargs: (_ for _ in ()).throw(URLError("offline")))
    response = create_app(TranslationConfig).test_client().get(
        "/api/translations?surah=55&start=13&end=13"
    )
    assert response.status_code == 503
    assert "no cached copy" in response.json["error"]


def test_translation_endpoint_rejects_unsupported_editions_and_ranges(tmp_path):
    TranslationConfig.OUTPUT_FOLDER = tmp_path
    client = create_app(TranslationConfig).test_client()
    assert client.get("/api/translations?surah=55&start=13&end=13&edition=en.pickthall").status_code == 400
    assert client.get("/api/translations?surah=55&start=79&end=79").status_code == 400


def test_incomplete_translation_cache_is_not_returned_as_if_complete(monkeypatch, tmp_path):
    TranslationConfig.OUTPUT_FOLDER = tmp_path
    cache = tmp_path / "translations" / "055-en.sahih.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(json.dumps({
        "surah": 55, "edition": "en.sahih", "translator": "Saheeh International",
        "source": "AlQuranCloud", "ayahs": [{"ayah": 1, "text": "wrong partial cache"}],
    }), encoding="utf-8")
    monkeypatch.setattr(translations, "urlopen", lambda *_args, **_kwargs: Response(_api_response()))
    result = translations.get_translation_range(55, 78, 78, tmp_path)
    assert result["cached"] is False
    assert result["ayahs"] == [{"ayah": 78, "text": "Verified translation for ayah 78."}]
    payload = json.loads(cache.read_text(encoding="utf-8"))
    assert len(payload["ayahs"]) == 78


def test_translation_api_rejects_incomplete_upstream_chapter(monkeypatch, tmp_path):
    TranslationConfig.OUTPUT_FOLDER = tmp_path
    payload = _api_response()
    payload["data"]["ayahs"].pop()
    monkeypatch.setattr(translations, "urlopen", lambda *_args, **_kwargs: Response(payload))
    with pytest.raises(translations.TranslationSourceError, match="every ayah"):
        translations.get_translation_range(55, 1, 1, tmp_path)
