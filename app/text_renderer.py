"""Arabic text shaping and rasterization, independent of MoviePy."""
from pathlib import Path
from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageFilter, features

DEFAULT_FONT = Path(__file__).resolve().parents[1] / "static" / "assets" / "NotoNaskhArabic-Regular.ttf"
PIL_HAS_RAQM = features.check("raqm")


def shape_arabic(text: str) -> str:
    """Preserve Quranic marks and prepare Arabic according to Pillow's shaper.

    Pillow builds with libraqm already perform Arabic joining and bidirectional
    layout. Pre-shaping those strings with arabic_reshaper deletes Quranic
    harakat by default and can disturb their placement, so RAQM must receive
    the original logical Unicode text. Older Pillow builds use the explicit
    reshaper/bidi fallback with harakat preservation enabled.
    """
    if not text or not text.strip():
        raise ValueError("Arabic caption text cannot be empty")
    if PIL_HAS_RAQM:
        return text
    try:
        from arabic_reshaper import ArabicReshaper
        from bidi.algorithm import get_display
    except ImportError as exc:
        raise RuntimeError("Install arabic-reshaper and python-bidi when Pillow lacks RAQM support") from exc
    # Keep diacritics and shift them with their base glyph during visual-order
    # conversion. The package defaults to deleting them, which is unsuitable
    # for Uthmani Quran text.
    reshaped = ArabicReshaper(configuration={
        "delete_harakat": False,
        "shift_harakat_position": True,
    }).reshape(text)
    return get_display(reshaped, base_dir="R")


def _text_options():
    """RAQM should shape logical Arabic in RTL; fallback text is already visual."""
    return {"direction": "rtl", "language": "ar"} if PIL_HAS_RAQM else {}


def _load_font(font_path, size):
    """Load Arabic fonts with RAQM explicitly so Arabic joining and bidi are stable."""
    layout = getattr(ImageFont, "Layout", None)
    raqm = getattr(layout, "RAQM", None) if layout is not None else None
    if PIL_HAS_RAQM and raqm is not None:
        return ImageFont.truetype(str(font_path), int(size), layout_engine=raqm)
    return ImageFont.truetype(str(font_path), int(size))


def wrap_arabic_lines(text: str, font, max_width: int, stroke_width: int = 0) -> list[str]:
    """Wrap logical Arabic words using the same bidi-aware metrics as raster output."""
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    text_options = _text_options()
    lines, current = [], []
    for word in text.split():
        candidate = " ".join((*current, word))
        visual = shape_arabic(candidate)
        bounds = probe.textbbox((0, 0), visual, font=font, stroke_width=stroke_width,
                                **text_options)
        if current and bounds[2] - bounds[0] > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def render_arabic_text(text: str, *, font_path=None, font_size=72, color=(255,255,255,255),
                       max_width=1400, max_height=None, padding=28, padding_x=None, padding_y=None,
                       stroke_width=2, stroke_fill=(0,0,0,220), backdrop_fill=(0,0,0,145), corner_radius=24,
                       glow_fill=None, glow_radius=0, show_surah_title=False, surah_title=None,
                       ayah_number=None, surah_color=(235, 205, 110, 255),
                       show_ayah_number=None, surah_template=None, ayah_number_template=None,
                       surah_font_path=None, ayah_number_font_path=None,
                       surah_position_x=0, surah_position_y=0,
                       ayah_number_position_x=0, ayah_number_position_y=0,
                       output_size=None) -> Image.Image:
    """Return a readable RGBA Arabic caption with custom styling, contrast plate, and optional Surah header."""
    shape_arabic(text)  # Fail early with a clear message if shaping dependencies are unavailable.
    chosen_font = Path(font_path) if font_path else DEFAULT_FONT
    if not chosen_font.exists():
        raise FileNotFoundError(f"Arabic font not found: {chosen_font}. Add an Arabic Naskh .ttf font under static/assets.")
    surah_font = Path(surah_font_path) if surah_font_path else chosen_font
    number_font = Path(ayah_number_font_path) if ayah_number_font_path else chosen_font
    for label_font in (surah_font, number_font):
        if not label_font.exists():
            raise FileNotFoundError(f"Arabic label font not found: {label_font}")
    probe = Image.new("RGBA", (1, 1)); draw = ImageDraw.Draw(probe)
    text_options = _text_options()

    pad_x = padding if padding_x is None else int(padding_x)
    pad_y = padding if padding_y is None else int(padding_y)

    from .design_templates import AYAH_NUMBER_TEMPLATES, SURAH_NAME_TEMPLATES

    def style_for(value, presets, fallback):
        if isinstance(value, dict):
            return {**fallback, **value}
        return {**fallback, **presets.get(value, {})}

    surah_style = style_for(surah_template, SURAH_NAME_TEMPLATES, SURAH_NAME_TEMPLATES["ornamental_gold"])
    number_style = style_for(ayah_number_template, AYAH_NUMBER_TEMPLATES, AYAH_NUMBER_TEMPLATES["gold_medallion"])
    if show_ayah_number is None:
        show_ayah_number = False

    def rgba(value, opacity=1.0, fallback=(235, 205, 110)):
        try:
            rgb = ImageColor.getrgb(value) if isinstance(value, str) else tuple(value[:3])
            return (*rgb[:3], int(255 * max(0, min(1, float(opacity)))))
        except (ValueError, TypeError):
            return (*fallback, int(255 * max(0, min(1, float(opacity)))))

    def layout(size):
        font = _load_font(chosen_font, size)
        lines = wrap_arabic_lines(text, font, max_width, stroke_width)
        shaped = [shape_arabic(item) for item in lines]
        boxes = [draw.textbbox((0, 0), item, font=font, stroke_width=stroke_width,
                               **text_options) for item in shaped]
        line_height = max(size + 14, max((box[3] - box[1] for box in boxes), default=size))
        content_width = max((box[2] - box[0] for box in boxes), default=1)
        verse_height = line_height * len(lines)

        header_items = []
        header_max_w = 0
        if show_surah_title and surah_title:
            h_font = _load_font(Path(surah_style.get("font_path") or surah_font),
                                max(24, int(size * float(surah_style["font_scale"]))))
            s_shaped = shape_arabic(str(surah_title))
            s_box = draw.textbbox((0, 0), s_shaped, font=h_font, **text_options)
            item_w = s_box[2] - s_box[0] + int(surah_style["padding_x"]) * 2
            item_h = s_box[3] - s_box[1] + int(surah_style["padding_y"]) * 2
            header_items.append({"kind": "title", "text": s_shaped, "font": h_font, "box": s_box,
                                 "height": item_h, "width": item_w, "style": surah_style,
                                 "position_x": surah_position_x, "position_y": surah_position_y})
            header_max_w = max(header_max_w, item_w)

        if show_ayah_number and ayah_number is not None:
            arabic_digits = str(ayah_number).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))
            badge_txt = shape_arabic(arabic_digits)
            b_font = _load_font(Path(number_style.get("font_path") or number_font),
                                max(20, int(size * float(number_style["font_scale"]))))
            b_box = draw.textbbox((0, 0), badge_txt, font=b_font, **text_options)
            item_w = b_box[2] - b_box[0] + int(number_style["padding_x"]) * 2
            item_h = b_box[3] - b_box[1] + int(number_style["padding_y"]) * 2
            if number_style.get("shape") == "medallion":
                item_w = item_h = max(item_w, item_h)
            header_items.append({"kind": "badge", "text": badge_txt, "font": b_font, "box": b_box,
                                 "height": item_h, "width": item_w, "style": number_style,
                                 "position_x": ayah_number_position_x, "position_y": ayah_number_position_y})
            header_max_w = max(header_max_w, item_w)

        before_items = [item for item in header_items if item["style"].get("placement", "above") != "below"]
        after_items = [item for item in header_items if item["style"].get("placement", "above") == "below"]
        def labels_height(items):
            return sum(item["height"] + 8 + (6 if item["style"].get("accent_line") else 0) for item in items)
        before_height, after_height = labels_height(before_items), labels_height(after_items)
        total_content_w = max(content_width, header_max_w)
        total_h = verse_height + before_height + after_height + pad_y * 2
        return (font, shaped, boxes, line_height, content_width, total_content_w, verse_height,
                before_items, after_items, before_height, after_height, total_h)

    # Keep even very long ayat inside the video safe area by reducing type size
    # gradually while retaining word boundaries and the user's selected wrap width.
    current_size = int(font_size)
    layout_result = layout(current_size)
    while max_height and layout_result[-1] > max_height and current_size > 26:
        current_size -= 2
        layout_result = layout(current_size)

    (font, shaped_lines, boxes, line_height, content_width,
     total_w, verse_h, before_items, after_items, before_h, after_h, height) = layout_result
    width = total_w + pad_x * 2
    frame_width, frame_height = output_size or (width, height)
    for item in (*before_items, *after_items):
        try:
            x_percent = max(-8.0, min(8.0, float(item.get("position_x") or 0)))
            y_percent = max(-8.0, min(8.0, float(item.get("position_y") or 0)))
        except (TypeError, ValueError) as exc:
            raise ValueError("Surah and ayah position offsets must be numbers from -8 to 8 percent.") from exc
        item["_position_x"] = int(round(frame_width * x_percent / 100))
        item["_position_y"] = int(round(frame_height * y_percent / 100))
        # Keep labels in their own header lane: they may move freely away from
        # the verse, but a move toward the verse cannot cross the reserved gap.
        if item["style"].get("placement", "above") != "below":
            item["_position_y"] = min(item["_position_y"], 8)
        else:
            item["_position_y"] = max(item["_position_y"], -8)
    x_offsets = [item["_position_x"] for item in (*before_items, *after_items)]
    y_offsets = [item["_position_y"] for item in (*before_items, *after_items)]
    pad_left, pad_right = max(0, -min(x_offsets, default=0)), max(0, max(x_offsets, default=0))
    pad_top, pad_bottom = max(0, -min(y_offsets, default=0)), max(0, max(y_offsets, default=0))
    width += pad_left + pad_right
    height += pad_top + pad_bottom

    image = Image.new("RGBA", (width, height), (0,0,0,0)); draw = ImageDraw.Draw(image)
    if backdrop_fill is not None and backdrop_fill != "none":
        draw.rounded_rectangle((pad_left, pad_top, width - pad_right - 1, height - pad_bottom - 1),
                               radius=corner_radius, fill=backdrop_fill)

    positions = []
    for idx, (text_line, box) in enumerate(zip(shaped_lines, boxes)):
        x = (total_w - (box[2]-box[0])) // 2 - box[0] + pad_x + pad_left
        y = pad_y + before_h + idx*line_height - box[1] + pad_top
        positions.append((text_line, x, y))
    obstacles = [
        (x + box[0] - stroke_width, y + box[1] - stroke_width,
         x + box[2] + stroke_width, y + box[3] + stroke_width)
        for (_text_line, x, y), box in zip(positions, boxes)
    ]

    def intersects(candidate, rect):
        return candidate[0] < rect[2] and candidate[2] > rect[0] and candidate[1] < rect[3] and candidate[3] > rect[1]

    def draw_label(item, curr_y):
        nonlocal draw
        if item:
            style = item["style"]
            item_w, item_h = item["width"], item["height"]
            align = style.get("align", "center")
            base_width = width - pad_left - pad_right
            if align == "left":
                item_x = pad_left + pad_x
            elif align == "right":
                item_x = pad_left + base_width - pad_x - item_w
            else:
                item_x = pad_left + (base_width - item_w) // 2
            item_x = max(0, min(width - item_w, item_x + item["_position_x"]))
            item_y = max(0, min(height - item_h, curr_y + pad_top + item["_position_y"]))
            label_rect = (item_x - 2, item_y - 2, item_x + item_w + 2, item_y + item_h + 2)
            if any(intersects(label_rect, rect) for rect in obstacles):
                candidates = sorted(range(max(0, pad_top - item_h), min(height - item_h, pad_top + height) + 1),
                                    key=lambda candidate: abs(candidate - item_y))
                for candidate_y in candidates:
                    candidate_rect = (item_x - 2, candidate_y - 2, item_x + item_w + 2, candidate_y + item_h + 2)
                    if not any(intersects(candidate_rect, rect) for rect in obstacles):
                        item_y = candidate_y
                        label_rect = candidate_rect
                        break
            background = style.get("background")
            shape = style.get("shape", "none")
            if background and shape != "none":
                fill = rgba(background, style.get("opacity", 1))
                border = rgba(style.get("border_color"), style.get("opacity", 1)) if style.get("border_color") else None
                if shape == "medallion":
                    draw.ellipse((item_x, item_y, item_x + item_w - 1, item_y + item_h - 1), fill=fill,
                                 outline=border, width=max(1, int(item["font"].size * .003)))
                elif shape == "ribbon":
                    notch = min(14, item_h // 2)
                    points = [(item_x, item_y), (item_x + item_w, item_y),
                              (item_x + item_w - notch, item_y + item_h // 2),
                              (item_x + item_w, item_y + item_h), (item_x, item_y + item_h),
                              (item_x + notch, item_y + item_h // 2)]
                    draw.polygon(points, fill=fill)
                    if border:
                        draw.line(points + [points[0]], fill=border, width=1, joint="curve")
                else:
                    radius = max(4, item_h // 3) if shape == "ornamental" else item_h // 2
                    draw.rounded_rectangle((item_x, item_y, item_x + item_w - 1, item_y + item_h - 1),
                                           radius=radius, fill=fill, outline=border, width=1 if border else 0)
                    if shape == "ornamental" and item_w > 16:
                        draw.arc((item_x + 3, item_y + 3, item_x + item_w - 4, item_y + item_h - 4),
                                 15, 165, fill=border or fill, width=1)

            h_b = item["box"]
            text_w = h_b[2] - h_b[0]
            text_h = h_b[3] - h_b[1]
            hx = item_x + (item_w - text_w) // 2 - h_b[0]
            hy = item_y + (item_h - text_h) // 2 - h_b[1]
            h_color = rgba(style.get("color", surah_color), style.get("opacity", 1))
            shadow_fill = (0, 0, 0, min(180, h_color[3]))
            draw.text((hx + 1, hy + 2), item["text"], font=item["font"], fill=shadow_fill,
                      **text_options)
            if style.get("glow"):
                glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
                ImageDraw.Draw(glow).text((hx, hy), item["text"], font=item["font"], fill=h_color,
                                          **text_options)
                image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(max(2, int(item["font"].size) // 100))))
                draw = ImageDraw.Draw(image)
            draw.text((hx, hy), item["text"], font=item["font"], fill=h_color, **text_options)
            obstacles.append(label_rect)
            curr_y += item_h + 8

            if style.get("accent_line"):
                div_w = min(int(width * 0.45), 260)
                div_x = (width - div_w) // 2
                draw.line([(div_x, curr_y - 2), (div_x + div_w, curr_y - 2)],
                          fill=(*h_color[:3], int(h_color[3] * .42)),
                          width=max(1, int(item["font"].size) // 90))
                curr_y += 6
        return curr_y

    curr_y = pad_y
    for item in before_items:
        curr_y = draw_label(item, curr_y)

    if glow_fill and glow_radius:
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        for text_line, x, y in positions:
            glow_draw.text((x, y), text_line, font=font, fill=glow_fill,
                           stroke_width=max(2, stroke_width + 1), **text_options)
        image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(glow_radius)))
        draw = ImageDraw.Draw(image)

    for text_line, x, y in positions:
        draw.text((x,y), text_line, font=font, fill=color, stroke_width=stroke_width,
                  stroke_fill=stroke_fill, **text_options)
    curr_y += verse_h
    for item in after_items:
        curr_y = draw_label(item, curr_y)
    return image
