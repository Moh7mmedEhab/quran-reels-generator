"""Bundled Arabic fonts with redistribution terms recorded in static/assets/FONT-LICENSE.txt."""
from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parents[1] / "static" / "assets"
FONT_CATALOG = {
    "amiri": {"name": "Amiri", "file": ASSET_ROOT / "fonts" / "Amiri-Regular.ttf", "css_family": "App Amiri"},
    "amiri_bold": {"name": "Amiri Bold", "file": ASSET_ROOT / "fonts" / "Amiri-Bold.ttf", "css_family": "App Amiri", "font_weight": 700},
    "naskh": {"name": "Noto Naskh Arabic", "file": ASSET_ROOT / "fonts" / "NotoNaskhArabic-Regular.ttf", "css_family": "App Noto Naskh"},
    "naskh_bold": {"name": "Noto Naskh Arabic Bold", "file": ASSET_ROOT / "fonts" / "NotoNaskhArabic-Bold.ttf", "css_family": "App Noto Naskh", "font_weight": 700},
    "sans": {"name": "Noto Sans Arabic", "file": ASSET_ROOT / "fonts" / "NotoSansArabic-Regular.ttf", "css_family": "App Noto Sans Arabic"},
    "sans_bold": {"name": "Noto Sans Arabic Bold", "file": ASSET_ROOT / "fonts" / "NotoSansArabic-Bold.ttf", "css_family": "App Noto Sans Arabic", "font_weight": 700},
    "kufi": {"name": "Noto Kufi Arabic", "file": ASSET_ROOT / "fonts" / "NotoKufiArabic-Regular.ttf", "css_family": "App Noto Kufi Arabic"},
    "kufi_bold": {"name": "Noto Kufi Arabic Bold", "file": ASSET_ROOT / "fonts" / "NotoKufiArabic-Bold.ttf", "css_family": "App Noto Kufi Arabic", "font_weight": 700},
}
DEFAULT_FONT_ID = "naskh"


def resolve_font(font_id, fallback=None):
    """Resolve a catalog key to a bundled file; arbitrary filesystem paths are never accepted."""
    entry = FONT_CATALOG.get(str(font_id or DEFAULT_FONT_ID))
    if entry is None:
        raise ValueError("Choose one of the bundled Arabic fonts.")
    if not entry["file"].is_file():
        return Path(fallback) if fallback else entry["file"]
    return entry["file"]
