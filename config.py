"""Application configuration with production-safe defaults."""
from __future__ import annotations

import os
import secrets
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass


BASE_DIR = Path(__file__).resolve().parent


def _enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


class Config:
    # Deployments should set QURAN_REELS_SECRET_KEY so multiple workers share
    # a stable secret. The fallback is unique per process and avoids a known
    # development secret when running the local studio.
    SECRET_KEY = os.environ.get("QURAN_REELS_SECRET_KEY") or secrets.token_urlsafe(32)
    DEBUG = _enabled(os.environ.get("FLASK_DEBUG"))
    TESTING = False
    MAX_CONTENT_LENGTH = 512 * 1024 * 1024
    # Let deployments place rendered files on a writable volume. create_app()
    # falls back to the system temp directory when the project tree is read-only.
    OUTPUT_FOLDER = Path(os.environ.get(
        "QURAN_REELS_OUTPUT_FOLDER", str(BASE_DIR / "static" / "outputs")
    )).expanduser()
    ARABIC_FONT = BASE_DIR / "static" / "assets" / "NotoNaskhArabic-Regular.ttf"
    RENDER_WORKERS = 1
    RENDER_JOBS_INLINE = False
    JOB_RETENTION_SECONDS = 24 * 60 * 60
    PREVIEW_RETENTION_SECONDS = 7 * 24 * 60 * 60

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PREFERRED_URL_SCHEME = "http"
