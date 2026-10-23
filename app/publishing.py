"""OAuth helpers and background uploads to YouTube and TikTok."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import math
import re
import threading
import time
from urllib.parse import urlparse
from uuid import uuid4

try:
    import requests
except ImportError:  # Optional until a provider is configured; rendering does not depend on it.
    requests = None

_REQUEST_EXCEPTION = requests.RequestException if requests else OSError


YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_READ_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
TIKTOK_USER_SCOPE = "user.info.basic"
TIKTOK_UPLOAD_SCOPE = "video.upload"
TIKTOK_PUBLISH_SCOPE = "video.publish"
YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
YOUTUBE_API = "https://www.googleapis.com/youtube/v3"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_REVOKE_URL = "https://open.tiktokapis.com/v2/oauth/revoke/"
TIKTOK_API = "https://open.tiktokapis.com/v2"
TIKTOK_CHUNK_SIZE = 32 * 1024 * 1024
TIKTOK_MIN_CHUNK_SIZE = 5 * 1024 * 1024
TIKTOK_MAX_CHUNK_SIZE = 64 * 1024 * 1024
TIKTOK_MAX_VIDEO_SIZE = 4 * 1024 * 1024 * 1024
YOUTUBE_CHUNK_SIZE = 8 * 1024 * 1024


class PublishError(RuntimeError):
    """Safe, user-facing failure without provider credentials or raw payloads."""


def is_configured(app, platform):
    store = app.extensions.get("publisher_store")
    if store is None or not store.encryption_ready or requests is None:
        return False
    if platform == "youtube":
        configured = all(app.config.get(key) for key in (
            "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REDIRECT_URI"))
        uri = urlparse(str(app.config.get("YOUTUBE_REDIRECT_URI") or ""))
        secure = uri.scheme == "https" or (uri.scheme == "http" and uri.hostname in {"localhost", "127.0.0.1", "::1"})
        return configured and secure and uri.path == "/oauth/youtube/callback" and not uri.query and not uri.fragment
    if platform == "tiktok":
        configured = all(app.config.get(key) for key in (
            "TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REDIRECT_URI"))
        uri = urlparse(str(app.config.get("TIKTOK_REDIRECT_URI") or ""))
        return configured and uri.scheme == "https" and bool(uri.hostname) and uri.path == "/oauth/tiktok/callback" and not uri.query and not uri.fragment
    return False


def setup_message(app, platform):
    store = app.extensions["publisher_store"]
    if not store.encryption_available:
        return "Publishing needs the cryptography dependency from requirements.txt; install it, then restart the app."
    if requests is None:
        return "Publishing needs the requests dependency from requirements.txt; install it, then restart the app."
    if not store.encryption_ready:
        return "Publishing is disabled until a valid QURAN_REELS_TOKEN_ENCRYPTION_KEY is configured."
    if platform == "youtube":
        missing = [key for key in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REDIRECT_URI")
                   if not app.config.get(key)]
    else:
        missing = [key for key in ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REDIRECT_URI")
                   if not app.config.get(key)]
    if missing:
        return "Configure " + ", ".join(missing) + " in the server environment."
    uri = urlparse(str(app.config.get("YOUTUBE_REDIRECT_URI" if platform == "youtube" else "TIKTOK_REDIRECT_URI") or ""))
    expected_path = "/oauth/youtube/callback" if platform == "youtube" else "/oauth/tiktok/callback"
    if uri.path != expected_path or uri.query or uri.fragment:
        return f"Set the registered redirect URI path to {expected_path} with no query string or fragment."
    if platform == "tiktok" and uri.scheme != "https":
        return "TikTok's web OAuth callback must use HTTPS."
    if platform == "youtube" and uri.scheme != "https" and not (uri.scheme == "http" and uri.hostname in {"localhost", "127.0.0.1", "::1"}):
        return "Google OAuth redirect URIs must use HTTPS, except for local loopback development."
    return ""


def provider_error_message(response, platform):
    """Translate common provider responses without surfacing tokens or raw data."""
    try:
        payload = response.json()
    except (ValueError, _REQUEST_EXCEPTION):
        payload = {}
    if response.status_code == 401:
        return "Authorization expired. Reconnect this account and try again."
    if response.status_code == 403:
        return "The connected account or developer app lacks permission for this action. Check the requested scopes and platform approval."
    if response.status_code == 429:
        return "The platform rate limit was reached. Wait a little, then retry."
    if response.status_code >= 500:
        return f"{platform.title()} is temporarily unavailable. Retry the upload later."
    if platform == "TikTok":
        error = payload.get("error") or {}
        code = error.get("code") if isinstance(error, dict) else payload.get("error")
        if code == "scope_not_authorized":
            return "The TikTok account did not grant the required upload permission. Reconnect and approve the requested scope."
        if code == "spam_risk_too_many_pending_share":
            return "TikTok currently has too many pending inbox uploads for this account. Complete or remove a pending draft, then retry."
        if code == "url_ownership_unverified":
            return "TikTok rejected the upload source because its domain is not verified. Use the file upload workflow or verify the configured domain."
        if code == "unaudited_client_can_only_post_to_private_accounts":
            return "TikTok has not approved direct posting for this developer app. Use the draft upload mode or complete TikTok's app audit."
    if platform == "YouTube" and response.status_code == 400:
        return "YouTube rejected the video metadata or upload request. Review the title, description, tags, and video format."
    return f"{platform} rejected the request (HTTP {response.status_code}). Check developer-app permissions and metadata."


def _json_response(response, platform):
    if response.status_code >= 400:
        raise PublishError(provider_error_message(response, platform))
    try:
        payload = response.json()
    except ValueError as exc:
        raise PublishError(f"{platform} returned an unreadable response.") from exc
    if platform == "TikTok":
        error = payload.get("error") or {}
        if isinstance(error, dict) and error.get("code") not in (None, "ok"):
            code = error.get("code")
            message = provider_error_message(response, platform)
            if code == "scope_not_authorized":
                message = "The TikTok account did not grant the required upload permission. Reconnect and approve the requested scope."
            raise PublishError(message)
    return payload


def _request(method, url, *, platform, **kwargs):
    if requests is None:
        raise PublishError("Install the requests dependency and restart the app before using social publishing.")
    try:
        response = requests.request(method, url, timeout=(20, 120), **kwargs)
    except requests.RequestException as exc:
        raise PublishError(f"A network error interrupted the {platform} request. Check the connection and retry.") from exc
    return response


def exchange_youtube_code(app, code):
    response = _request("POST", YOUTUBE_TOKEN_URL, platform="YouTube", data={
        "code": code,
        "client_id": app.config["YOUTUBE_CLIENT_ID"],
        "client_secret": app.config["YOUTUBE_CLIENT_SECRET"],
        "redirect_uri": app.config["YOUTUBE_REDIRECT_URI"],
        "grant_type": "authorization_code",
    })
    payload = _json_response(response, "YouTube")
    if not payload.get("access_token"):
        raise PublishError("Google did not return an access token. Try connecting YouTube again.")
    return payload


def exchange_tiktok_code(app, code):
    response = _request("POST", TIKTOK_TOKEN_URL, platform="TikTok", data={
        "client_key": app.config["TIKTOK_CLIENT_KEY"],
        "client_secret": app.config["TIKTOK_CLIENT_SECRET"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": app.config["TIKTOK_REDIRECT_URI"],
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    payload = _json_response(response, "TikTok")
    if not payload.get("access_token") or not payload.get("open_id"):
        raise PublishError("TikTok did not return an account token. Try connecting TikTok again.")
    return payload


def _refresh_account(app, store, owner, platform):
    account = store.get_account(owner, platform)
    if account is None:
        raise PublishError("This platform is disconnected. Connect the account and try again.")
    tokens = account["secrets"]
    expires_at = float(tokens.get("expires_at") or 0)
    if expires_at > time.time() + 90:
        return account, tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise PublishError("Authorization expired. Reconnect this account and try again.")
    if platform == "youtube":
        response = _request("POST", YOUTUBE_TOKEN_URL, platform="YouTube", data={
            "client_id": app.config["YOUTUBE_CLIENT_ID"],
            "client_secret": app.config["YOUTUBE_CLIENT_SECRET"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        })
    else:
        response = _request("POST", TIKTOK_TOKEN_URL, platform="TikTok", data={
            "client_key": app.config["TIKTOK_CLIENT_KEY"],
            "client_secret": app.config["TIKTOK_CLIENT_SECRET"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    payload = _json_response(response, platform.title())
    tokens.update(payload)
    tokens["expires_at"] = time.time() + max(0, int(payload.get("expires_in") or 0))
    if payload.get("refresh_expires_in") is not None:
        tokens["refresh_expires_at"] = time.time() + int(payload["refresh_expires_in"])
    store.save_account(owner, platform, tokens, external_id=account["external_id"],
                       display_name=account["display_name"], scopes=account["scopes"])
    return store.get_account(owner, platform), tokens.get("access_token", "")


def youtube_channel_info(access_token):
    response = _request("GET", f"{YOUTUBE_API}/channels", platform="YouTube", params={
        "part": "snippet", "mine": "true",
    }, headers={"Authorization": f"Bearer {access_token}"})
    payload = _json_response(response, "YouTube")
    items = payload.get("items") or []
    if not items:
        return "", ""
    return str(items[0].get("id") or ""), str((items[0].get("snippet") or {}).get("title") or "")


def tiktok_user_info(access_token):
    response = _request("GET", f"{TIKTOK_API}/user/info/", platform="TikTok",
                        params={"fields": "open_id,display_name"},
                        headers={"Authorization": f"Bearer {access_token}"})
    payload = _json_response(response, "TikTok")
    data = payload.get("data") or {}
    return str(data.get("open_id") or ""), str(data.get("display_name") or "")


def tiktok_creator_info(access_token):
    response = _request("POST", f"{TIKTOK_API}/post/publish/creator_info/query/",
                        platform="TikTok", json={},
                        headers={"Authorization": f"Bearer {access_token}",
                                 "Content-Type": "application/json; charset=UTF-8"})
    payload = _json_response(response, "TikTok")
    return payload.get("data") or {}


def _safe_upload_url(value, platform):
    parsed = urlparse(str(value or ""))
    host = (parsed.hostname or "").lower()
    allowed = (platform == "youtube" and (host == "googleapis.com" or host.endswith(".googleapis.com")))
    allowed = allowed or (platform == "tiktok" and
                          (host == "tiktokapis.com" or host.endswith(".tiktokapis.com")))
    try:
        port = parsed.port
    except ValueError:
        port = -1
    if (parsed.scheme != "https" or not allowed or parsed.username or parsed.password
            or port not in (None, 443) or parsed.fragment):
        raise PublishError("The platform returned an invalid secure upload URL. No file was sent.")
    return parsed.geturl()


def _tiktok_chunk_plan(file_size):
    """Choose legal TikTok chunks, avoiding a short final chunk on large files."""
    size = int(file_size)
    if size <= 0:
        raise PublishError("The rendered video is empty and cannot be uploaded to TikTok.")
    if size > TIKTOK_MAX_VIDEO_SIZE:
        raise PublishError("TikTok accepts videos up to 4 GB. Choose a smaller export before uploading.")
    chunk_size = min(TIKTOK_CHUNK_SIZE, size)
    total_chunks = math.ceil(size / chunk_size)
    final_chunk_size = size - chunk_size * (total_chunks - 1)
    if total_chunks > 1 and final_chunk_size < TIKTOK_MIN_CHUNK_SIZE:
        total_chunks -= 1
        chunk_size = math.ceil(size / total_chunks)
        total_chunks = math.ceil(size / chunk_size)
    if chunk_size > TIKTOK_MAX_CHUNK_SIZE:
        raise PublishError("TikTok's upload chunk limit was exceeded. Choose a smaller export.")
    return chunk_size, total_chunks


def _progress(store, upload_id, value, message, phase="uploading"):
    store.update_upload(upload_id, status=phase, phase=phase, progress=max(0, min(99, value)), message=message)


def _read_range(response, file_size):
    match = re.search(r"bytes=0-(\d+)", response.headers.get("Range", ""), flags=re.I)
    if match:
        return min(file_size, int(match.group(1)) + 1)
    return 0


def _youtube_resource(response):
    try:
        payload = response.json()
    except ValueError as exc:
        raise PublishError("YouTube accepted an upload response that could not be read.") from exc
    if not payload.get("id"):
        raise PublishError("YouTube did not return a video ID, so the upload cannot be confirmed.")
    return payload


def _youtube_query_resume(upload_url, access_token, file_size):
    response = _request("PUT", upload_url, platform="YouTube", data=b"", headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Length": "0",
        "Content-Range": f"bytes */{file_size}",
    })
    if response.status_code in (200, 201):
        return file_size, _youtube_resource(response)
    if response.status_code == 308:
        return _read_range(response, file_size), None
    if response.status_code == 404 or response.status_code == 410:
        raise PublishError("The resumable YouTube upload session expired. Reconnect YouTube and start a new upload.")
    if response.status_code >= 400:
        raise PublishError(provider_error_message(response, "YouTube"))
    return 0, None


def _youtube_upload(app, store, upload, access_token, *, cancel_event=None):
    path = Path(upload["source_path"])
    size = path.stat().st_size
    metadata = upload["metadata"]
    settings = upload["settings"]
    operation = upload.get("operation_id")
    resume_existing = bool(operation)

    def finish_cancelled():
        if operation:
            try:
                _request("DELETE", operation, platform="YouTube", headers={
                    "Authorization": f"Bearer {access_token}",
                })
            except PublishError:
                pass
        store.update_upload(upload["id"], status="cancelled", phase="cancelled", progress=0,
                            message="YouTube upload cancelled. The video was not confirmed as uploaded.")

    if cancel_event is not None and cancel_event.is_set():
        finish_cancelled()
        return
    if not operation:
        store.update_upload(upload["id"], status="initializing", phase="initializing",
                            progress=0, message="Preparing YouTube's resumable upload session.")
        category = str(settings.get("category_id") or app.config.get("YOUTUBE_DEFAULT_CATEGORY_ID", "10"))
        body = {"snippet": {"title": metadata["title"], "description": metadata["description"],
                            "tags": metadata["tags"], "categoryId": category},
                "status": {"privacyStatus": settings["privacy"]}}
        response = _request("POST", f"{YOUTUBE_API.rsplit('/youtube/v3', 1)[0]}/upload/youtube/v3/videos",
                            platform="YouTube", params={"uploadType": "resumable",
                                                          "part": "snippet,status"},
                            json=body, headers={
                                "Authorization": f"Bearer {access_token}",
                                "Content-Type": "application/json; charset=UTF-8",
                                "X-Upload-Content-Length": str(size),
                                "X-Upload-Content-Type": "video/mp4",
                            })
        if response.status_code not in (200, 201):
            raise PublishError(provider_error_message(response, "YouTube"))
        operation = _safe_upload_url(response.headers.get("Location"), "youtube")
        store.update_upload(upload["id"], status="uploading", phase="uploading",
                            progress=0, message="YouTube upload session started.", operation_id=operation)

    offset = 0
    resource = None
    if resume_existing:
        offset, resource = _youtube_query_resume(operation, access_token, size)
        if offset:
            _progress(store, upload["id"], 90 * offset / max(1, size),
                      f"Resuming YouTube transfer · {offset / size:.0%}")
    network_retries = 0
    with path.open("rb") as source:
        while offset < size and resource is None:
            if cancel_event is not None and cancel_event.is_set():
                finish_cancelled()
                return
            source.seek(offset)
            chunk = source.read(min(YOUTUBE_CHUNK_SIZE, size - offset))
            end = offset + len(chunk) - 1
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "video/mp4",
                       "Content-Length": str(len(chunk)), "Content-Range": f"bytes {offset}-{end}/{size}"}
            try:
                response = _request("PUT", operation, platform="YouTube", data=chunk, headers=headers)
            except PublishError:
                network_retries += 1
                if network_retries > 3:
                    raise PublishError("The YouTube upload could not reconnect after three attempts. Refresh status before retrying.")
                time.sleep(min(2 ** (network_retries - 1), 8))
                offset, resource = _youtube_query_resume(operation, access_token, size)
                _progress(store, upload["id"], 90 * offset / max(1, size),
                          f"Resuming YouTube transfer · {offset / size:.0%}")
                continue
            if response.status_code in (200, 201):
                resource = _youtube_resource(response)
                network_retries = 0
            elif response.status_code == 308:
                if cancel_event is not None and cancel_event.is_set():
                    finish_cancelled()
                    return
                acknowledged = _read_range(response, size)
                offset = acknowledged if acknowledged > offset else end + 1
                network_retries = 0
                _progress(store, upload["id"], 90 * offset / max(1, size),
                          f"Uploading to YouTube · {offset / size:.0%}")
            elif response.status_code >= 500:
                network_retries += 1
                if network_retries > 3:
                    raise PublishError("YouTube could not resume the upload after three attempts. Refresh status before retrying.")
                time.sleep(min(2 ** (network_retries - 1), 8))
                offset, resource = _youtube_query_resume(operation, access_token, size)
            else:
                raise PublishError(provider_error_message(response, "YouTube"))
    if resource is None:
        offset, resource = _youtube_query_resume(operation, access_token, size)
    if resource is None:
        raise PublishError("YouTube has not confirmed receipt of the complete video. Refresh the status before retrying.")
    video_id = str(resource["id"])
    result_url = f"https://www.youtube.com/watch?v={video_id}"
    store.update_upload(upload["id"], status="processing", phase="processing", progress=96,
                        message="YouTube received the MP4 and is processing it.", external_id=video_id,
                        result_url=result_url)
    _poll_youtube_processing(app, store, upload["id"], video_id, access_token, settings.get("privacy", "private"),
                             resource.get("processingDetails", {}))


def _youtube_status(access_token, video_id):
    response = _request("GET", f"{YOUTUBE_API}/videos", platform="YouTube", params={
        "part": "status,processingDetails", "id": video_id,
    }, headers={"Authorization": f"Bearer {access_token}"})
    payload = _json_response(response, "YouTube")
    items = payload.get("items") or []
    if not items:
        return {"uploadStatus": "unknown", "processingStatus": "unknown"}
    row = items[0]
    return {**(row.get("status") or {}), **(row.get("processingDetails") or {})}


def _poll_youtube_processing(app, store, upload_id, video_id, access_token, privacy, initial):
    details = initial or {}
    for attempt in range(12):
        state = str(details.get("processingStatus") or "").lower()
        if state == "succeeded":
            store.update_upload(upload_id, status="available", phase="complete", progress=100,
                                message=f"YouTube finished processing the {privacy} video.")
            return
        if state in {"failed", "terminated"}:
            store.update_upload(upload_id, status="failed", phase="failed",
                                message="YouTube received the video but could not process it.",
                                error="YouTube video processing failed.")
            return
        if attempt == 11:
            break
        time.sleep(5)
        try:
            details = _youtube_status(access_token, video_id)
        except PublishError:
            break
    store.update_upload(upload_id, status="processing", phase="processing", progress=98,
                        message="Upload finished. YouTube is still processing the video; use Refresh status to check again.")


def _tiktok_status(access_token, publish_id):
    response = _request("POST", f"{TIKTOK_API}/post/publish/status/fetch/", platform="TikTok",
                        json={"publish_id": publish_id},
                        headers={"Authorization": f"Bearer {access_token}",
                                 "Content-Type": "application/json; charset=UTF-8"})
    payload = _json_response(response, "TikTok")
    return payload.get("data") or {}


def _tiktok_status_result(store, upload_id, result, *, username=""):
    state = str(result.get("status") or "").upper()
    if state == "SEND_TO_USER_INBOX":
        store.update_upload(upload_id, status="waiting_user", phase="waiting_user", progress=100,
                            message="Draft uploaded to TikTok. Open the TikTok inbox notification to review and publish it.")
        return
    if state in {"PROCESSING_UPLOAD", "PROCESSING_DOWNLOAD"}:
        uploaded = float(result.get("uploaded_bytes") or result.get("downloaded_bytes") or 0)
        store.update_upload(upload_id, status="processing", phase="processing", progress=95,
                            message=f"TikTok is processing the video ({int(uploaded)} bytes transferred).")
        return
    if state == "PUBLISH_COMPLETE":
        post_ids = result.get("publicaly_available_post_id") or []
        post_id = str(post_ids[0]) if post_ids else ""
        result_url = (f"https://www.tiktok.com/@{username}/video/{post_id}"
                      if post_id.isdigit() and username else "")
        store.update_upload(upload_id, status="published", phase="complete", progress=100,
                            message="TikTok confirmed that the post was published.",
                            external_id=post_id or "completed", result_url=result_url)
        return
    if state == "FAILED":
        reason = str(result.get("fail_reason") or "TikTok could not process this video.")
        safe_reason = {
            "file_format_check_failed": "TikTok does not accept this MP4 video format.",
            "duration_check_failed": "The video duration is outside TikTok's current limits.",
            "frame_rate_check_failed": "The video's frame rate is not accepted by TikTok.",
            "picture_size_check_failed": "The video's dimensions are not accepted by TikTok.",
            "publish_cancelled": "The TikTok publishing operation was cancelled.",
            "internal": "TikTok encountered a temporary processing error. Retry after checking the operation status.",
        }.get(reason, "TikTok could not process this video. Review the video and try again.")
        store.update_upload(upload_id, status="failed", phase="failed", message=safe_reason,
                            error="provider_confirmed_failure")
        return
    store.update_upload(upload_id, status="processing", phase="processing", progress=95,
                        message="TikTok accepted the video and is still processing it.")


def _poll_tiktok_status(store, upload_id, access_token, publish_id, *, username=""):
    """Poll within the API rate limit, then leave an accurate refreshable state."""
    for attempt in range(12):
        result = _tiktok_status(access_token, publish_id)
        state = str(result.get("status") or "").upper()
        _tiktok_status_result(store, upload_id, result, username=username)
        if state in {"SEND_TO_USER_INBOX", "PUBLISH_COMPLETE", "FAILED"}:
            return
        if attempt < 11:
            time.sleep(5)


def _tiktok_upload(app, store, upload, access_token):
    path = Path(upload["source_path"])
    size = path.stat().st_size
    chunk_size, total_chunks = _tiktok_chunk_plan(size)
    settings = upload["settings"]
    metadata = upload["metadata"]
    mode = settings.get("mode", "draft")
    if mode == "direct":
        if not app.config.get("TIKTOK_DIRECT_POST_ENABLED"):
            raise PublishError("TikTok direct publishing is disabled. Use the supported inbox draft flow or configure approved video.publish access.")
        creator = tiktok_creator_info(access_token)
        allowed_privacy = creator.get("privacy_level_options") or []
        privacy = settings.get("privacy")
        if not privacy or privacy not in allowed_privacy:
            raise PublishError("Choose one of the privacy settings currently allowed by the connected TikTok account.")
        title_length = len(metadata["caption"].encode("utf-16-le")) // 2
        if title_length > 2200:
            raise PublishError("The TikTok caption exceeds 2,200 UTF-16 characters. Review and shorten it before uploading.")
        username = str(creator.get("creator_username") or "")
        init_url = f"{TIKTOK_API}/post/publish/video/init/"
        body = {"post_info": {"title": metadata["caption"], "privacy_level": privacy,
                               "disable_comment": bool(settings.get("disable_comment")) or bool(creator.get("comment_disabled")),
                               "disable_duet": bool(settings.get("disable_duet")) or bool(creator.get("duet_disabled")),
                               "disable_stitch": bool(settings.get("disable_stitch")) or bool(creator.get("stitch_disabled"))},
                "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                "chunk_size": chunk_size, "total_chunk_count": total_chunks}}
    else:
        username = ""
        init_url = f"{TIKTOK_API}/post/publish/inbox/video/init/"
        body = {"source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                "chunk_size": chunk_size, "total_chunk_count": total_chunks}}

    publish_id = upload.get("operation_id")
    upload_url = upload.get("upload_url")
    resume_existing = bool(publish_id)
    if not publish_id:
        store.update_upload(upload["id"], status="initializing", phase="initializing",
                            progress=0, message="Preparing TikTok's video upload.")
        response = _request("POST", init_url, platform="TikTok", json=body,
                            headers={"Authorization": f"Bearer {access_token}",
                                     "Content-Type": "application/json; charset=UTF-8"})
        payload = _json_response(response, "TikTok")
        data = payload.get("data") or {}
        publish_id = data.get("publish_id")
        upload_url = _safe_upload_url(data.get("upload_url"), "tiktok")
        if not publish_id:
            raise PublishError("TikTok did not return an upload identifier, so the operation cannot be tracked.")
        store.update_upload(upload["id"], status="uploading", phase="uploading", progress=0,
                            message="TikTok upload initialized.", operation_id=publish_id)
        # The returned upload URL is short-lived and functions as a secret; keep
        # it encrypted beside the operation id for this running worker only.
        store.update_upload(upload["id"], operation_id=json.dumps({"publish_id": publish_id,
                                                                   "upload_url": upload_url,
                                                                   "username": username}))

    # The operation id is encrypted in storage. On a retry, reconstruct the
    # upload URL only if the same-process worker kept it in the encrypted blob.
    if not upload_url:
        try:
            operation_data = json.loads(publish_id)
            publish_id = operation_data["publish_id"]
            upload_url = operation_data["upload_url"]
            username = operation_data.get("username", username)
        except (TypeError, ValueError, KeyError):
            existing = _tiktok_status(access_token, str(publish_id))
            _tiktok_status_result(store, upload["id"], existing, username=username)
            return

    upload_url = _safe_upload_url(upload_url, "tiktok")
    offset = 0
    if resume_existing:
        prior_state = _tiktok_status(access_token, str(publish_id))
        prior_status = str(prior_state.get("status") or "").upper()
        if prior_status in {"SEND_TO_USER_INBOX", "PUBLISH_COMPLETE", "FAILED"}:
            _tiktok_status_result(store, upload["id"], prior_state, username=username)
            return
        offset = min(size, int(prior_state.get("uploaded_bytes") or 0))
        if offset:
            _progress(store, upload["id"], 90 * offset / max(1, size),
                      f"Resuming TikTok transfer · {offset / size:.0%}")
    with path.open("rb") as source:
        network_retries = 0
        while offset < size:
            source.seek(offset)
            chunk = source.read(min(chunk_size, size - offset))
            end = offset + len(chunk) - 1
            headers = {"Content-Type": "video/mp4", "Content-Length": str(len(chunk)),
                       "Content-Range": f"bytes {offset}-{end}/{size}"}
            try:
                response = requests.put(upload_url, data=chunk, headers=headers, timeout=(20, 180))
            except _REQUEST_EXCEPTION as exc:
                # Reconcile before retrying: TikTok may have received this range.
                network_retries += 1
                if network_retries > 3:
                    raise PublishError("The TikTok transfer could not reconnect after three attempts. Refresh status before retrying.") from exc
                _progress(store, upload["id"], 90 * offset / max(1, size),
                          "Network interrupted; checking TikTok receipt before retrying.")
                state = _tiktok_status(access_token, str(publish_id))
                if str(state.get("status", "")).upper() in {"SEND_TO_USER_INBOX", "PUBLISH_COMPLETE", "FAILED"}:
                    _tiktok_status_result(store, upload["id"], state, username=username)
                    return
                received = int(state.get("uploaded_bytes") or 0)
                if received > offset:
                    offset = min(size, received)
                    network_retries = 0
                    continue
                time.sleep(min(2 ** (network_retries - 1), 8))
                continue
            if response.status_code >= 500:
                network_retries += 1
                if network_retries > 3:
                    raise PublishError("TikTok could not resume the transfer after three attempts. Refresh status before retrying.")
                state = _tiktok_status(access_token, str(publish_id))
                if str(state.get("status", "")).upper() in {"SEND_TO_USER_INBOX", "PUBLISH_COMPLETE", "FAILED"}:
                    _tiktok_status_result(store, upload["id"], state, username=username)
                    return
                received = int(state.get("uploaded_bytes") or 0)
                if received > offset:
                    offset = min(size, received)
                    network_retries = 0
                    continue
                time.sleep(min(2 ** (network_retries - 1), 8))
                continue
            if response.status_code not in (200, 201, 206, 308):
                raise PublishError(provider_error_message(response, "TikTok"))
            offset = end + 1
            network_retries = 0
            _progress(store, upload["id"], 90 * offset / max(1, size),
                      f"Uploading to TikTok · {offset / size:.0%}")

    store.update_upload(upload["id"], status="processing", phase="processing", progress=94,
                        message="TikTok received the MP4 and is processing it.")
    result = _tiktok_status(access_token, str(publish_id))
    _tiktok_status_result(store, upload["id"], result, username=username)
    if str(result.get("status") or "").upper() not in {"SEND_TO_USER_INBOX", "PUBLISH_COMPLETE", "FAILED"}:
        _poll_tiktok_status(store, upload["id"], access_token, str(publish_id), username=username)


class UploadManager:
    """Run provider uploads independently of browser requests and persist state."""

    def __init__(self, app, store, workers=2):
        self.app = app
        self.store = store
        self.executor = ThreadPoolExecutor(max_workers=max(1, int(workers)),
                                           thread_name_prefix="quran-publish")
        self._lock = threading.RLock()
        self._active = set()
        self._cancel_events = {}

    def start(self, *, owner, platform, render_job_id, source_path, metadata, settings, project_id="draft"):
        with self._lock:
            previous = self.store.latest_upload(owner, render_job_id, platform)
            if previous:
                if previous["status"] in {"queued", "initializing", "uploading", "processing", "cancelling"}:
                    return previous, False
                if previous["status"] in {"waiting_user", "published", "available"}:
                    return previous, False
                internal = self.store.get_upload(previous["id"], owner, internal=True)
                if internal.get("operation_id") and platform == "tiktok":
                    if previous.get("error") != "provider_confirmed_failure":
                        raise PublishError("The earlier TikTok operation may already be with TikTok. Refresh its status before starting another upload.")
                elif internal.get("operation_id") and platform == "youtube":
                    if internal.get("external_id"):
                        raise PublishError("YouTube already received this video. Refresh its processing status before starting another upload.")
                    upload_id = previous["id"]
                    self.store.update_upload(upload_id, status="queued", phase="queued", progress=0,
                                             message="Retry queued; resuming the existing YouTube upload session.", error="")
                    self._dispatch(upload_id, owner)
                    return self.store.get_upload(upload_id, owner), True
            upload_id = uuid4().hex
            self.store.create_upload(upload_id=upload_id, owner=owner, platform=platform,
                                     render_job_id=render_job_id, source_path=source_path, project_id=project_id,
                                     metadata=metadata, settings=settings)
            self._dispatch(upload_id, owner)
            return self.store.get_upload(upload_id, owner), True

    def _dispatch(self, upload_id, owner):
        if upload_id in self._active:
            return
        self._active.add(upload_id)
        cancel_event = threading.Event()
        self._cancel_events[upload_id] = cancel_event
        self.executor.submit(self._run, upload_id, owner, cancel_event)

    def cancel(self, upload_id, owner):
        with self._lock:
            upload = self.store.get_upload(upload_id, owner, internal=True)
            if upload is None:
                return None
            if upload["platform"] != "youtube":
                raise PublishError("TikTok file uploads cannot be cancelled through the Content Posting API after initialization.")
            if upload["status"] not in {"queued", "initializing", "uploading"} or upload.get("external_id"):
                raise PublishError("This YouTube upload can no longer be cancelled because processing has started.")
            cancel_event = self._cancel_events.get(upload_id)
            if cancel_event is None:
                raise PublishError("This upload is not active in the current app process. Refresh provider status before retrying.")
            cancel_event.set()
            self.store.update_upload(upload_id, status="cancelling", phase="cancelling",
                                     message="Cancellation requested; the current transfer chunk will finish first.")
            return self.store.get_upload(upload_id, owner)

    def _run(self, upload_id, owner, cancel_event):
        try:
            with self.app.app_context():
                upload = self.store.get_upload(upload_id, owner, internal=True)
                if upload is None:
                    return
                if cancel_event.is_set():
                    self.store.update_upload(upload_id, status="cancelled", phase="cancelled", progress=0,
                                             message="YouTube upload cancelled before transfer started.")
                    return
                account, token = _refresh_account(self.app, self.store, owner, upload["platform"])
                if upload["platform"] == "youtube":
                    _youtube_upload(self.app, self.store, upload, token, cancel_event=cancel_event)
                else:
                    _tiktok_upload(self.app, self.store, upload, token)
        except PublishError as exc:
            self.app.logger.info("Social upload %s ended: %s", upload_id, str(exc))
            current = self.store.get_upload(upload_id, owner, internal=True)
            if current:
                self.store.update_upload(upload_id, status="failed", phase="failed",
                                         message=str(exc), error=str(exc))
        except Exception as exc:
            self.app.logger.error("Social upload %s failed internally (%s)", upload_id, type(exc).__name__)
            self.store.update_upload(upload_id, status="failed", phase="failed",
                                     message="Upload failed because of an internal server error. Retry after checking the connection.",
                                     error="Internal upload error.")
        finally:
            with self._lock:
                self._active.discard(upload_id)
                self._cancel_events.pop(upload_id, None)


def refresh_upload_status(app, store, owner, upload_id):
    """Ask the provider for a persisted operation's latest status."""
    upload = store.get_upload(upload_id, owner, internal=True)
    if upload is None:
        return None
    if upload["platform"] == "tiktok" and upload.get("operation_id"):
        operation = upload["operation_id"]
        username = ""
        try:
            operation_data = json.loads(operation)
            publish_id = operation_data.get("publish_id")
            username = operation_data.get("username", "")
        except (TypeError, ValueError):
            publish_id = operation
        account, token = _refresh_account(app, store, owner, "tiktok")
        result = _tiktok_status(token, str(publish_id))
        _tiktok_status_result(store, upload_id, result, username=username)
    elif upload["platform"] == "youtube" and upload.get("external_id"):
        account, token = _refresh_account(app, store, owner, "youtube")
        result = _youtube_status(token, upload["external_id"])
        state = str(result.get("processingStatus") or "").lower()
        if state == "succeeded":
            privacy = (upload.get("settings") or {}).get("privacy", "private")
            store.update_upload(upload_id, status="available", phase="complete", progress=100,
                                message=f"YouTube finished processing the {privacy} video.")
        elif state in {"failed", "terminated"}:
            store.update_upload(upload_id, status="failed", phase="failed",
                                message="YouTube received the video but could not process it.",
                                error="YouTube video processing failed.")
        else:
            store.update_upload(upload_id, status="processing", phase="processing", progress=98,
                                message="YouTube is still processing the video.")
    return store.get_upload(upload_id, owner)
