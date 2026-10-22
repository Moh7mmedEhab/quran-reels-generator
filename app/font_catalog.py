"""Bundled Arabic fonts with redistribution terms recorded in static/assets/FONT-LICENSE.txt."""
from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parents[1] / "static" / "assets"
FONT_CATALOG = {
    "naskh": {"name": "Noto Naskh Arabic", "file": ASSET_ROOT / "fonts" / "NotoNaskhArabic-Regular.ttf"},
    "naskh_bold": {"name": "Noto Naskh Arabic Bold", "file": ASSET_ROOT / "fonts" / "NotoNaskhArabic-Bold.ttf"},
    "sans": {"name": "Noto Sans Arabic", "file": ASSET_ROOT / "fonts" / "NotoSansArabic-Regular.ttf"},
    "sans_bold": {"name": "Noto Sans Arabic Bold", "file": ASSET_ROOT / "fonts" / "NotoSansArabic-Bold.ttf"},
    "kufi": {"name": "Noto Kufi Arabic", "file": ASSET_ROOT / "fonts" / "NotoKufiArabic-Regular.ttf"},
    "kufi_bold": {"name": "Noto Kufi Arabic Bold", "file": ASSET_ROOT / "fonts" / "NotoKufiArabic-Bold.ttf"},
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
