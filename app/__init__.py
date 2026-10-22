from flask import Flask
from config import Config
from .render_jobs import RenderJobManager

def create_app(config_object=Config):
    app=Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_object)
    app.extensions["render_job_manager"] = RenderJobManager(
        max_workers=app.config.get("RENDER_WORKERS", 1),
        inline=app.config.get("RENDER_JOBS_INLINE", False),
        retention_seconds=app.config.get("JOB_RETENTION_SECONDS", 24 * 60 * 60),
    )
    from .routes import bp
    app.register_blueprint(bp)
    return app
