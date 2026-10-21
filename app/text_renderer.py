"""Arabic text shaping and rasterization, independent of MoviePy."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, features

DEFAULT_FONT = Path(__file__).resolve().parents[1] / "static" / "assets" / "NotoNaskhArabic-Regular.ttf"
PIL_HAS_RAQM = features.check("raqm")


def shape_arabic(text: str) -> str:
    """Prepare Arabic text for Pillow without applying the bidi pass twice."""
    if not text or not text.strip():
        raise ValueError("Arabic caption text cannot be empty")
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError as exc:
        raise RuntimeError("Install arabic-reshaper and python-bidi to render Arabic captions") from exc
    reshaped = arabic_reshaper.reshape(text)
    if PIL_HAS_RAQM:
        # RAQM handles paragraph direction and glyph positioning itself. Keep
        # logical order here; a bidi pass before RAQM reverses the words twice.
        return reshaped
    # Older Pillow builds need python-bidi to provide visual order manually.
    return get_display(reshaped, base_dir="R")


def render_arabic_text(text: str, *, font_path=None, font_size=72, color=(255,255,255,255),
                       max_width=1400, max_height=None, padding=28, stroke_width=2,
                       stroke_fill=(0,0,0,220), backdrop_fill=(0,0,0,145), corner_radius=24,
                       glow_fill=None, glow_radius=0) -> Image.Image:
    """Return a readable RGBA Arabic caption with a translucent contrast plate."""
    shape_arabic(text)  # Fail early with a clear message if shaping dependencies are unavailable.
    chosen_font = Path(font_path) if font_path else DEFAULT_FONT
    if not chosen_font.exists():
        raise FileNotFoundError(f"Arabic font not found: {chosen_font}. Add an Arabic Naskh .ttf font under static/assets.")
    probe = Image.new("RGBA", (1, 1)); draw = ImageDraw.Draw(probe)
    draw_direction = "rtl" if PIL_HAS_RAQM else "ltr"

    def layout(size):
        font = ImageFont.truetype(str(chosen_font), size)
        words = text.split()
        lines, line = [], ""
        for word in words:
            candidate = f"{line} {word}".strip()
            visual = shape_arabic(candidate)
            bounds = draw.textbbox((0, 0), visual, font=font, direction=draw_direction, stroke_width=stroke_width)
            if line and bounds[2] - bounds[0] > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        shaped = [shape_arabic(item) for item in lines]
        boxes = [draw.textbbox((0, 0), item, font=font, direction=draw_direction, stroke_width=stroke_width) for item in shaped]
        line_height = max(size + 14, max((box[3] - box[1] for box in boxes), default=size))
        content_width = max((box[2] - box[0] for box in boxes), default=1)
        image_height = line_height * len(lines) + padding * 2
        return font, shaped, boxes, line_height, content_width, image_height

    # Keep even very long ayat inside the video safe area by reducing type size
    # gradually while retaining word boundaries and the user's selected wrap width.
    current_size = int(font_size)
    layout_result = layout(current_size)
    while max_height and layout_result[-1] > max_height and current_size > 30:
        current_size -= 2
        layout_result = layout(current_size)
    font, shaped_lines, boxes, line_height, content_width, height = layout_result
    width = content_width + padding * 2
    image = Image.new("RGBA", (width, height), (0,0,0,0)); draw = ImageDraw.Draw(image)
    if backdrop_fill is not None:
        draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=corner_radius, fill=backdrop_fill)
    positions = []
    for idx, (text_line, box) in enumerate(zip(shaped_lines, boxes)):
        x = (width - (box[2]-box[0])) // 2 - box[0]
        y = padding + idx*line_height - box[1]
        positions.append((text_line, x, y))
    if glow_fill and glow_radius:
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        for text_line, x, y in positions:
            glow_draw.text((x, y), text_line, font=font, fill=glow_fill,
                           direction=draw_direction, stroke_width=max(1, stroke_width))
        image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(glow_radius)))
        draw = ImageDraw.Draw(image)
    for text_line, x, y in positions:
        draw.text((x,y), text_line, font=font, fill=color, direction=draw_direction, stroke_width=stroke_width, stroke_fill=stroke_fill)
    return image
