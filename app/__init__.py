from flask import Flask
from config import Config
from .render_jobs import RenderJobManager
from .publisher_store import PublisherStore
from .publishing import UploadManager
from .version import APP_VERSION
from pathlib import Path
import tempfile

__version__ = APP_VERSION


def _prepare_output_folder(configured_path):
    """Choose an output directory that this process can actually write to."""
    candidates = [Path(configured_path), Path(tempfile.gettempdir()) / "quran-reels-outputs"]
    last_error = None
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write-check"
            probe.write_bytes(b"ok")
            probe.unlink()
            return candidate
        except OSError as exc:
            last_error = exc
    raise OSError(f"No writable video output directory is available: {last_error}")

def create_app(config_object=Config):
    app=Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_object)
    app.config.setdefault("PUBLISHER_DATABASE_PATH", Path(app.instance_path) / "publisher.sqlite3")
    app.config.setdefault("PUBLISHER_TOKEN_ENCRYPTION_KEY", "")
    app.config.setdefault("PUBLISHING_WORKERS", 2)
    app.config["OUTPUT_FOLDER"] = _prepare_output_folder(app.config["OUTPUT_FOLDER"])
    app.extensions["render_job_manager"] = RenderJobManager(
        max_workers=app.config.get("RENDER_WORKERS", 1),
        inline=app.config.get("RENDER_JOBS_INLINE", False),
        retention_seconds=app.config.get("JOB_RETENTION_SECONDS", 24 * 60 * 60),
    )
    app.extensions["publisher_store"] = PublisherStore(
        app.config["PUBLISHER_DATABASE_PATH"],
        app.config.get("PUBLISHER_TOKEN_ENCRYPTION_KEY", ""),
        app.config["SECRET_KEY"],
    )
    app.extensions["publisher_store"].mark_interrupted_uploads()
    app.extensions["upload_manager"] = UploadManager(
        app, app.extensions["publisher_store"],
        workers=app.config.get("PUBLISHING_WORKERS", 2),
    )
    from .routes import bp
    app.register_blueprint(bp)
    return app
