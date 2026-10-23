"""Bundled, locally generated motion backgrounds used by the Video gallery."""
from pathlib import Path


BACKGROUND_VIDEO_TEMPLATES = {
    "misty_forest_drift": {
        "name": "Misty Forest Drift",
        "description": "Sunlit mist with a slow, seamless camera drift.",
        "theme": "misty_forest",
        "filename": "misty_forest_drift.mp4",
        "duration": 6,
    },
    "marble_arch_glow": {
        "name": "Marble Arch Glow",
        "description": "A quiet architectural scene with a warm, gentle push.",
        "theme": "marble_arch",
        "filename": "marble_arch_glow.mp4",
        "duration": 6,
    },
    "moonlit_horizon": {
        "name": "Moonlit Horizon",
        "description": "A cool night landscape with subtle floating movement.",
        "theme": "sahara_moon",
        "filename": "moonlit_horizon.mp4",
        "duration": 6,
    },
    "midnight_coast_drift": {
        "name": "Midnight Coast Drift",
        "description": "A dark ocean horizon with a quiet, slow floating camera movement.",
        "theme": "midnight_coast",
        "filename": "midnight_coast_drift.mp4",
        "duration": 6,
        "width": 1440,
        "height": 2560,
        "fps": 24,
    },
}


def background_video_template_path(template_id: str, *, static_folder=None) -> Path:
    """Resolve a catalogued file beneath the app's bundled video directory."""
    template = BACKGROUND_VIDEO_TEMPLATES.get(str(template_id))
    if template is None:
        raise ValueError("Choose one of the available video backgrounds.")
    root = Path(static_folder) if static_folder else Path(__file__).resolve().parents[1] / "static"
    return root / "assets" / "background-videos" / template["filename"]


def available_background_video_templates(*, static_folder=None) -> dict:
    """Return only bundled presets whose local media files are present."""
    return {
        template_id: template
        for template_id, template in BACKGROUND_VIDEO_TEMPLATES.items()
        if background_video_template_path(template_id, static_folder=static_folder).is_file()
    }
