from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
pytest.importorskip("cryptography.fernet")
from cryptography.fernet import Fernet

from app import create_app
from app.routes import _generated_publish_metadata
from app.quran_data import SURAHS_BY_NUMBER


class PublishingTestConfig:
    TESTING = True
    SECRET_KEY = "test-publisher-secret"
    OUTPUT_FOLDER = Path("/tmp/quran-publisher-test-outputs")
    PUBLISHER_DATABASE_PATH = Path("/tmp/quran-publisher-tests.sqlite3")
    PUBLISHER_TOKEN_ENCRYPTION_KEY = Fernet.generate_key().decode("ascii")
    YOUTUBE_CLIENT_ID = "youtube-test-client"
    YOUTUBE_CLIENT_SECRET = "youtube-test-secret"
    YOUTUBE_REDIRECT_URI = "https://studio.example.test/oauth/youtube/callback"
    YOUTUBE_DEFAULT_CATEGORY_ID = "10"
    TIKTOK_CLIENT_KEY = "tiktok-test-client"
    TIKTOK_CLIENT_SECRET = "tiktok-test-secret"
    TIKTOK_REDIRECT_URI = "https://studio.example.test/oauth/tiktok/callback"
    TIKTOK_DIRECT_POST_ENABLED = False
    PUBLISHING_WORKERS = 1


@pytest.fixture
def publisher_app(tmp_path):
    class Config(PublishingTestConfig):
        OUTPUT_FOLDER = tmp_path / "outputs"
        PUBLISHER_DATABASE_PATH = tmp_path / "instance" / "publisher.sqlite3"
        PUBLISHER_TOKEN_ENCRYPTION_KEY = Fernet.generate_key().decode("ascii")

    return create_app(Config)


def test_publisher_store_encrypts_tokens_and_scopes_accounts_to_browser(tmp_path):
    from app.publisher_store import PublisherStore

    key = Fernet.generate_key().decode("ascii")
    db_path = tmp_path / "private" / "publisher.sqlite3"
    store = PublisherStore(db_path, key, "session-secret")
    owner_a = store.owner_key("browser-a")
    owner_b = store.owner_key("browser-b")
    store.save_account(owner_a, "youtube", {
        "access_token": "access-token-never-plain", "refresh_token": "refresh-token-never-plain",
        "expires_at": 0,
    }, external_id="channel-1", display_name="Test Channel", scopes="youtube.upload")

    assert store.get_account(owner_a, "youtube")["secrets"]["refresh_token"] == "refresh-token-never-plain"
    assert store.get_account(owner_b, "youtube") is None
    assert b"refresh-token-never-plain" not in db_path.read_bytes()
    assert db_path.stat().st_mode & 0o077 == 0


def test_publishing_status_does_not_expose_provider_tokens(publisher_app):
    client = publisher_app.test_client()
    client.get("/api/publishing")
    with client.session_transaction() as browser:
        owner = publisher_app.extensions["publisher_store"].owner_key(browser["publisher_session_id"])
    publisher_app.extensions["publisher_store"].save_account(owner, "youtube", {
        "access_token": "secret-access", "refresh_token": "secret-refresh", "expires_at": 0,
    }, external_id="channel-7", display_name="Channel Seven", scopes="https://www.googleapis.com/auth/youtube.upload")

    response = client.get("/api/publishing")
    data = response.get_json()
    assert response.status_code == 200
    assert data["providers"]["youtube"]["account"]["display_name"] == "Channel Seven"
    assert data["providers"]["youtube"]["ready"] is True
    assert data["providers"]["youtube"]["credential_ready"] is True
    assert "secret-access" not in response.get_data(as_text=True)
    assert "secret-refresh" not in response.get_data(as_text=True)


def test_publisher_readiness_requires_usable_credentials_and_upload_scope(publisher_app):
    client = publisher_app.test_client()
    client.get("/api/publishing")
    with client.session_transaction() as browser:
        owner = publisher_app.extensions["publisher_store"].owner_key(browser["publisher_session_id"])
    store = publisher_app.extensions["publisher_store"]

    store.save_account(owner, "youtube", {
        "access_token":"expired-without-refresh", "expires_at":0,
    }, scopes="https://www.googleapis.com/auth/youtube.upload")
    state = client.get("/api/publishing").get_json()["providers"]["youtube"]
    assert state["connected"] is True
    assert state["ready"] is False
    assert state["credential_ready"] is False

    store.save_account(owner, "youtube", {
        "access_token":"refreshable", "refresh_token":"refreshable-too",
        "expires_at":0,
    }, scopes="https://www.googleapis.com/auth/youtube.upload")
    state = client.get("/api/publishing").get_json()["providers"]["youtube"]
    assert state["ready"] is True

    store.save_account(owner, "youtube", {
        "access_token":"token-without-upload-scope", "expires_at":9999999999,
    }, scopes="https://www.googleapis.com/auth/youtube.readonly")
    state = client.get("/api/publishing").get_json()["providers"]["youtube"]
    assert state["credential_ready"] is True
    assert state["ready"] is False
    assert state["missing_scopes"] == ["https://www.googleapis.com/auth/youtube.upload"]


def test_publish_page_lists_and_previews_persisted_owned_renders(publisher_app, tmp_path):
    client = publisher_app.test_client()
    client.get("/api/publishing")
    with client.session_transaction() as browser:
        owner = publisher_app.extensions["publisher_store"].owner_key(browser["publisher_session_id"])
    store = publisher_app.extensions["publisher_store"]
    render_id = "7" * 32
    store.register_render(render_id, owner, "project-previous")
    metadata = {
        "title": "سورة الرحمن . Surah Ar-Rahman",
        "description": "Generated Quran description\n\n#Quran #QuranRecitation",
        "tags": ["Quran", "Quran recitation"],
        "caption": "سورة الرحمن . Surah Ar-Rahman\n\n#Quran #QuranRecitation",
    }
    store.complete_render(render_id, owner, {
        "filename": f"{render_id}.mp4", "download_title": metadata["title"],
        "publish_metadata": metadata, "surah": "Ar-Rahman", "ayah_start": 1,
        "ayah_end": 20, "reciter": "Test Reciter", "duration": 31.5,
    })
    output_path = Path(publisher_app.config["OUTPUT_FOLDER"]) / f"{render_id}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"completed-mp4" * 200)

    # No in-memory job is needed: the persistent owner record and MP4 are sufficient.
    assert publisher_app.extensions["render_job_manager"].get(render_id) is None
    listing = client.get("/api/publishing/renders").get_json()["renders"]
    assert len(listing) == 1
    assert listing[0]["project_id"] == "project-previous"
    assert listing[0]["publish_metadata"] == metadata

    page = client.get(f"/publish?render_job_id={render_id}")
    assert page.status_code == 200
    assert f'data-initial-render-id="{render_id}"' in page.get_data(as_text=True)
    selected = client.get(f"/api/publishing/renders/{render_id}").get_json()
    assert selected["preview_url"] == f"/publishing/video/{render_id}"
    assert selected["download_url"].startswith(f"/outputs/{render_id}.mp4")
    video = client.get(selected["preview_url"])
    assert video.status_code == 200
    assert video.mimetype == "video/mp4"
    assert video.data.startswith(b"completed-mp4")
    assert publisher_app.extensions["render_job_manager"].get(render_id) is None

    studio = client.get("/").get_data(as_text=True)
    assert 'id="youtube-upload-btn"' not in studio
    assert 'id="post-render-publish-link"' in studio
    assert 'id="completed-render-select"' in page.get_data(as_text=True)

    unavailable = client.get("/api/publishing/renders/" + "8" * 32)
    assert unavailable.status_code == 404
    unavailable_page = client.get(f"/publish?render_job_id={'8' * 32}").get_data(as_text=True)
    assert f'data-initial-render-id="{"8" * 32}"' in unavailable_page


def test_youtube_oauth_uses_real_authorization_endpoint_and_rejects_bad_state(publisher_app):
    client = publisher_app.test_client()
    response = client.get("/api/publishing/youtube/connect")
    parsed = urlparse(response.location)
    query = parse_qs(parsed.query)
    assert parsed.netloc == "accounts.google.com"
    assert query["response_type"] == ["code"]
    assert "https://www.googleapis.com/auth/youtube.upload" in query["scope"][0]
    assert "https://www.googleapis.com/auth/youtube.readonly" in query["scope"][0]
    rejected = client.get("/oauth/youtube/callback?code=fake-code&state=wrong-state")
    assert "youtube_state_error" in rejected.location
    assert publisher_app.extensions["publisher_store"].list_accounts("nobody") == []


def test_tiktok_oauth_requests_upload_scope_without_direct_post_scope(publisher_app):
    client = publisher_app.test_client()
    response = client.get("/api/publishing/tiktok/connect")
    parsed = urlparse(response.location)
    query = parse_qs(parsed.query)
    assert parsed.netloc == "www.tiktok.com"
    assert query["response_type"] == ["code"]
    assert "video.upload" in query["scope"][0]
    assert "user.info.basic" in query["scope"][0]
    assert "video.publish" not in query["scope"][0]


def test_provider_upload_url_requires_a_trusted_https_host():
    from app.publishing import PublishError, _safe_upload_url

    assert _safe_upload_url("https://open-upload.tiktokapis.com/video/?token=abc", "tiktok")
    with pytest.raises(PublishError):
        _safe_upload_url("https://malicioustiktokapis.com/video/", "tiktok")
    with pytest.raises(PublishError):
        _safe_upload_url("https://user@upload.googleapis.com/session", "youtube")


@pytest.mark.parametrize("size_mib", [4, 32, 34, 65, 127, 129])
def test_tiktok_chunk_plan_respects_provider_chunk_limits(size_mib):
    from app.publishing import TIKTOK_MAX_CHUNK_SIZE, TIKTOK_MIN_CHUNK_SIZE, _tiktok_chunk_plan

    size = size_mib * 1024 * 1024
    chunk_size, chunk_count = _tiktok_chunk_plan(size)
    final_chunk = size - chunk_size * (chunk_count - 1)
    assert 1 <= chunk_size <= TIKTOK_MAX_CHUNK_SIZE
    assert chunk_count >= 1
    assert chunk_size * (chunk_count - 1) < size <= chunk_size * chunk_count
    assert chunk_count == 1 or final_chunk >= TIKTOK_MIN_CHUNK_SIZE


def test_tiktok_chunk_plan_rejects_files_over_four_gigabytes():
    from app.publishing import PublishError, TIKTOK_MAX_VIDEO_SIZE, _tiktok_chunk_plan

    with pytest.raises(PublishError, match="up to 4 GB"):
        _tiktok_chunk_plan(TIKTOK_MAX_VIDEO_SIZE + 1)


def test_youtube_oauth_callback_saves_account_server_side(publisher_app, monkeypatch):
    import app.routes as routes

    monkeypatch.setattr(routes, "exchange_youtube_code", lambda app, code: {
        "access_token": "mock-access", "refresh_token": "mock-refresh", "expires_in": 3600,
        "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
    })
    monkeypatch.setattr(routes, "youtube_channel_info", lambda token: ("channel-12", "Surah Channel"))
    client = publisher_app.test_client()
    render_id = "9" * 32
    client.get(f"/api/publishing/youtube/connect?render_job_id={render_id}")
    with client.session_transaction() as browser:
        state = browser["publisher_oauth_youtube"]["state"]

    response = client.get(f"/oauth/youtube/callback?code=mock-code&state={state}")
    with client.session_transaction() as browser:
        owner = publisher_app.extensions["publisher_store"].owner_key(browser["publisher_session_id"])
    account = publisher_app.extensions["publisher_store"].get_account(owner, "youtube")
    assert "youtube_connected" in response.location
    assert f"render_job_id={render_id}" in response.location
    assert account["external_id"] == "channel-12"
    assert account["display_name"] == "Surah Channel"
    assert account["secrets"]["refresh_token"] == "mock-refresh"


def test_upload_post_requires_csrf_and_session_owned_completed_render(publisher_app, monkeypatch, tmp_path):
    client = publisher_app.test_client()
    state = client.get("/api/publishing").get_json()
    with client.session_transaction() as browser:
        owner = publisher_app.extensions["publisher_store"].owner_key(browser["publisher_session_id"])
    store = publisher_app.extensions["publisher_store"]
    store.save_account(owner, "youtube", {
        "access_token": "mock", "refresh_token": "mock", "expires_at": 0,
    }, scopes="https://www.googleapis.com/auth/youtube.upload")
    job_id = "a" * 32
    store.register_render(job_id, owner, "saved-project-42")
    output_path = Path(publisher_app.config["OUTPUT_FOLDER"]) / f"{job_id}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"x" * 2048)
    monkeypatch.setattr(publisher_app.extensions["render_job_manager"], "get", lambda _job: {
        "status": "complete", "result": {"filename": output_path.name},
    })
    captured = {}

    def start(**kwargs):
        captured.update(kwargs)
        return ({"id": "b" * 32, "platform": "youtube", "status": "queued"}, True)

    monkeypatch.setattr(publisher_app.extensions["upload_manager"], "start", start)
    payload = {"platform": "youtube", "render_job_id": job_id,
               "metadata": {"title": "سورة الرحمن . Surah Ar-Rahman", "description": "generated", "tags": ["Quran"]},
               "privacy": "private", "category_id": "10"}
    denied = client.post("/api/publishing/uploads", json=payload)
    assert denied.status_code == 403
    accepted = client.post("/api/publishing/uploads", json=payload,
                           headers={"X-Publisher-CSRF": state["csrf_token"]})
    assert accepted.status_code == 202
    assert captured["render_job_id"] == job_id
    assert captured["project_id"] == "saved-project-42"
    assert captured["settings"]["privacy"] == "private"


def test_failed_upload_retry_uses_saved_metadata_and_settings_snapshot(publisher_app, monkeypatch):
    client = publisher_app.test_client()
    state = client.get("/api/publishing").get_json()
    with client.session_transaction() as browser:
        owner = publisher_app.extensions["publisher_store"].owner_key(browser["publisher_session_id"])
    store = publisher_app.extensions["publisher_store"]
    store.save_account(owner, "youtube", {"access_token": "mock", "expires_at": 0},
                       scopes="https://www.googleapis.com/auth/youtube.upload")
    render_id = "c" * 32
    store.register_render(render_id, owner, "retry-project")
    store.complete_render(render_id, owner, {"filename": f"{render_id}.mp4"})
    output_path = Path(publisher_app.config["OUTPUT_FOLDER"]) / f"{render_id}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"completed mp4" * 200)

    old_metadata = {"title": "Original title", "description": "Original description with #Quran",
                    "tags": ["Original tag"]}
    old_settings = {"privacy": "private", "category_id": "10"}
    monkeypatch.setattr(store, "latest_upload", lambda *_args: {"id": "d" * 32, "status": "failed"})
    monkeypatch.setattr(store, "get_upload", lambda *_args, **_kwargs: {
        "metadata": old_metadata, "settings": old_settings,
    })
    captured = {}
    monkeypatch.setattr(publisher_app.extensions["upload_manager"], "start", lambda **kwargs: (
        captured.update(kwargs) or ({"id": "e" * 32, "status": "queued"}, True)
    ))
    response = client.post("/api/publishing/uploads", json={
        "platform": "youtube", "render_job_id": render_id,
        "metadata": {"title": "Changed after failure", "description": "Changed", "tags": []},
        "privacy": "public", "category_id": "22",
    }, headers={"X-Publisher-CSRF": state["csrf_token"]})

    assert response.status_code == 202
    assert captured["metadata"] == old_metadata
    assert captured["settings"] == old_settings


def test_render_metadata_mapping_reuses_generator_text_and_required_title():
    from app.youtube_metadata import generate_youtube_metadata

    chapter = SURAHS_BY_NUMBER[55]
    generated = generate_youtube_metadata(
        surah_number=55, surah_english=chapter["english_name"], surah_arabic=chapter["name_arabic"],
        ayah_start=13, ayah_end=14, reciter_name="Test Reciter",
    )
    mapped = _generated_publish_metadata(generated, chapter)
    assert mapped["title"] == f"{generated['arabic']['title'].split(' | ', 1)[0]} . Surah {chapter['english_name']}"
    assert generated["english"]["description"] in mapped["description"]
    assert generated["arabic"]["description"] in mapped["description"]
    assert set(generated["english"]["tags"] + generated["arabic"]["tags"]).issubset(set(mapped["tags"]))
    assert set(generated["english"]["hashtags"] + generated["arabic"]["hashtags"]).issubset(
        set(mapped["hashtags"])
    )
    assert len(mapped["hashtags"]) == len({tag.casefold() for tag in mapped["hashtags"]})


class MockResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self):
        return self._payload


def test_youtube_upload_uses_resumable_protocol_and_reports_available_video(publisher_app, monkeypatch, tmp_path):
    import app.publishing as publishing

    owner = publisher_app.extensions["publisher_store"].owner_key("yt-upload")
    store = publisher_app.extensions["publisher_store"]
    source = tmp_path / "rendered.mp4"
    source.write_bytes(b"v" * 1024)
    store.create_upload(upload_id="c" * 32, owner=owner, platform="youtube", render_job_id="d" * 32,
                        source_path=str(source), metadata={"title": "سورة الرحمن . Surah Ar-Rahman",
                                                           "description": "generated description", "tags": ["Quran"]},
                        settings={"privacy": "private", "category_id": "10"})
    upload = store.get_upload("c" * 32, owner, internal=True)
    calls = []

    def fake_request(method, url, *, platform, **kwargs):
        calls.append((method, url, kwargs))
        if method == "POST":
            return MockResponse(200, headers={"Location": "https://www.googleapis.com/upload/youtube/v3/videos?upload_id=secret"})
        return MockResponse(201, {"id": "video-abc", "processingDetails": {"processingStatus": "succeeded"}})

    monkeypatch.setattr(publishing, "_request", fake_request)
    publishing._youtube_upload(publisher_app, store, upload, "mock-access")
    result = store.get_upload("c" * 32, owner)
    assert calls[0][2]["params"] == {"uploadType": "resumable", "part": "snippet,status"}
    assert calls[0][2]["json"]["snippet"]["title"] == "سورة الرحمن . Surah Ar-Rahman"
    assert result["status"] == "available"
    assert result["result_url"] == "https://www.youtube.com/watch?v=video-abc"
    assert result["external_id"] == "video-abc"


def test_tiktok_inbox_upload_sends_video_without_claiming_it_is_published(publisher_app, monkeypatch, tmp_path):
    import app.publishing as publishing

    owner = publisher_app.extensions["publisher_store"].owner_key("tt-upload")
    store = publisher_app.extensions["publisher_store"]
    source = tmp_path / "rendered.mp4"
    source.write_bytes(b"v" * 2048)
    store.create_upload(upload_id="e" * 32, owner=owner, platform="tiktok", render_job_id="f" * 32,
                        source_path=str(source), metadata={"caption": "Surah title\n\nGenerated description"},
                        settings={"mode": "draft", "privacy": ""})
    upload = store.get_upload("e" * 32, owner, internal=True)
    init_body = {}

    def fake_request(method, url, *, platform, **kwargs):
        if url.endswith("inbox/video/init/"):
            init_body.update(kwargs["json"])
            return MockResponse(200, {"data": {"publish_id": "draft-id",
                                                "upload_url": "https://open-upload.tiktokapis.com/video/?token=secret"},
                                     "error": {"code": "ok"}})
        return MockResponse(200, {"data": {"status": "SEND_TO_USER_INBOX"}, "error": {"code": "ok"}})

    monkeypatch.setattr(publishing, "_request", fake_request)
    monkeypatch.setattr(publishing.requests, "put", lambda *args, **kwargs: MockResponse(200))
    publishing._tiktok_upload(publisher_app, store, upload, "mock-access")
    result = store.get_upload("e" * 32, owner)
    assert "post_info" not in init_body
    assert init_body["source_info"]["chunk_size"] == source.stat().st_size
    assert init_body["source_info"]["total_chunk_count"] == 1
    assert result["status"] == "waiting_user"
    assert "notified" in result["message"] or "Draft uploaded" in result["message"]
    assert result["result_url"] is None


def test_upload_manager_returns_existing_operation_for_duplicate_clicks(publisher_app, monkeypatch, tmp_path):
    owner = publisher_app.extensions["publisher_store"].owner_key("duplicate-browser")
    manager = publisher_app.extensions["upload_manager"]
    monkeypatch.setattr(manager, "_dispatch", lambda upload_id, session_owner: None)
    source = tmp_path / "finished.mp4"
    source.write_bytes(b"video" * 400)
    arguments = {"owner": owner, "platform": "youtube", "render_job_id": "1" * 32,
                 "source_path": str(source), "metadata": {"title": "Surah . Name"},
                 "settings": {"privacy": "private"}}

    first, started = manager.start(**arguments)
    second, started_again = manager.start(**arguments)
    assert started is True
    assert started_again is False
    assert first["id"] == second["id"]
    assert len(publisher_app.extensions["publisher_store"].list_uploads(owner)) == 1


def test_upload_state_is_marked_interrupted_after_process_restart(tmp_path):
    from app.publisher_store import PublisherStore

    path = tmp_path / "instance" / "uploads.sqlite3"
    key = Fernet.generate_key().decode("ascii")
    first_process = PublisherStore(path, key, "stable-secret")
    owner = first_process.owner_key("browser-restart")
    source = tmp_path / "video.mp4"
    source.write_bytes(b"x" * 2048)
    first_process.create_upload(upload_id="7" * 32, owner=owner, platform="youtube",
                                render_job_id="8" * 32, source_path=str(source),
                                metadata={"title": "Surah . Name"}, settings={"privacy": "private"})
    first_process.update_upload("7" * 32, status="uploading", phase="uploading",
                                message="Sending chunks.", operation_id="https://www.googleapis.com/upload/session")

    restarted_process = PublisherStore(path, key, "stable-secret")
    restarted_process.mark_interrupted_uploads()
    snapshot = restarted_process.get_upload("7" * 32, owner)
    assert snapshot["status"] == "failed"
    assert "process stopped" in snapshot["message"]

