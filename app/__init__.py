from flask import Flask
from config import Config
from .render_jobs import RenderJobManager
from pathlib import Path
import tempfile


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
    app.config["OUTPUT_FOLDER"] = _prepare_output_folder(app.config["OUTPUT_FOLDER"])
    app.extensions["render_job_manager"] = RenderJobManager(
        max_workers=app.config.get("RENDER_WORKERS", 1),
        inline=app.config.get("RENDER_JOBS_INLINE", False),
        retention_seconds=app.config.get("JOB_RETENTION_SECONDS", 24 * 60 * 60),
    )
    from .routes import bp
    app.register_blueprint(bp)
    return app
