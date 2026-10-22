"""Reusable component presets used by both the editor and Arabic renderer."""

QURAN_TEXT_TEMPLATES = {
    "traditional_naskh": {"name": "Traditional Naskh", "description": "Readable classic Quran typography", "caption_style": "quranic", "caption_color": "ivory", "font_id": "naskh", "glow_type": "none", "text_bg_enabled": True, "text_bg_color": "#0a0c10", "text_bg_opacity": .65},
    "luminous_gold": {"name": "Luminous Gold", "description": "Warm gold letters with a soft glow", "caption_style": "golden_illuminated", "caption_color": "gold", "font_id": "naskh", "glow_type": "gold", "text_bg_enabled": True, "text_bg_color": "#090806", "text_bg_opacity": .68},
    "cinematic_white": {"name": "Cinematic White", "description": "White Naskh with a restrained glow", "caption_style": "soft_white", "caption_color": "white", "font_id": "naskh", "glow_type": "white", "text_bg_enabled": True, "text_bg_color": "#08111d", "text_bg_opacity": .58},
    "emerald_luxury": {"name": "Emerald Luxury", "description": "Cream lettering with emerald light", "caption_style": "quranic", "caption_color": "ivory", "font_id": "naskh_bold", "glow_type": "emerald", "text_bg_enabled": True, "text_bg_color": "#061e16", "text_bg_opacity": .62},
    "minimal_dark": {"name": "Minimal Dark", "description": "Clean white verse with no panel", "caption_style": "minimal", "caption_color": "white", "font_id": "naskh", "glow_type": "none", "text_bg_enabled": False, "text_bg_color": "#000000", "text_bg_opacity": 0},
    "gold_on_black": {"name": "Gold on Black", "description": "Premium gold verse on a dark plate", "caption_style": "golden_illuminated", "caption_color": "gold", "font_id": "naskh_bold", "glow_type": "gold", "text_bg_enabled": True, "text_bg_color": "#050505", "text_bg_opacity": .82},
    "cream_nature": {"name": "Cream on Nature", "description": "Soft cream text with a natural palette", "caption_style": "subtle_shadow", "caption_color": "ivory", "font_id": "naskh", "glow_type": "none", "text_bg_enabled": False, "text_bg_color": "#000000", "text_bg_opacity": 0},
    "modern_gradient": {"name": "Modern Blue", "description": "Bright blue lettering with crisp outline", "caption_style": "bold_modern", "caption_color": "sky", "font_id": "kufi", "glow_type": "blue", "text_bg_enabled": True, "text_bg_color": "#07162a", "text_bg_opacity": .72},
    "ornate_frame": {"name": "Ornate Frame", "description": "Framed Arabic with a warm gold accent", "caption_style": "quranic", "caption_color": "ivory", "font_id": "naskh", "glow_type": "gold", "text_bg_enabled": True, "text_bg_color": "#0a0b0b", "text_bg_opacity": .70},
    "clear_outline": {"name": "Clear Outline", "description": "Readable text directly over the background", "caption_style": "subtle_outline", "caption_color": "white", "font_id": "naskh", "glow_type": "none", "text_bg_enabled": False, "text_bg_color": "#000000", "text_bg_opacity": 0},
}

SURAH_NAME_TEMPLATES = {
    "ornamental_gold": {"name": "Ornamental Gold", "shape": "ornamental", "color": "#f3d58d", "background": "#17130d", "border_color": "#c8a557", "font_scale": .46, "padding_x": 20, "padding_y": 9, "align": "center", "opacity": .9, "accent_line": True},
    "classic_label": {"name": "Classic Label", "shape": "pill", "color": "#fff2ca", "background": "#282015", "border_color": "#a98a4b", "font_scale": .44, "padding_x": 18, "padding_y": 8, "align": "center", "opacity": .88},
    "minimal_header": {"name": "Minimal Header", "shape": "none", "color": "#fff4db", "background": None, "border_color": None, "font_scale": .42, "padding_x": 12, "padding_y": 5, "align": "center", "opacity": 1, "accent_line": True},
    "emerald_ribbon": {"name": "Emerald Ribbon", "shape": "ribbon", "color": "#f4e7bf", "background": "#12372c", "border_color": "#bfa05b", "font_scale": .43, "padding_x": 22, "padding_y": 8, "align": "center", "opacity": .94},
    "soft_glow": {"name": "Soft Glow", "shape": "none", "color": "#ffe8a8", "background": None, "border_color": None, "font_scale": .46, "padding_x": 12, "padding_y": 6, "align": "center", "opacity": 1, "glow": True},
    "transparent_title": {"name": "Transparent Text", "shape": "none", "color": "#ffffff", "background": None, "border_color": None, "font_scale": .40, "padding_x": 8, "padding_y": 4, "align": "center", "opacity": 1},
    "geometric_frame": {"name": "Geometric Frame", "shape": "ornamental", "color": "#f8e7b0", "background": "#102c25", "border_color": "#c7a45a", "font_scale": .44, "padding_x": 24, "padding_y": 11, "align": "center", "opacity": .94, "accent_line": True},
    "corner_label": {"name": "Quiet Corner Label", "shape": "pill", "color": "#fff5dc", "background": "#101820", "border_color": "#c4a968", "font_scale": .36, "padding_x": 15, "padding_y": 7, "align": "right", "opacity": .86},
    "bottom_ribbon": {"name": "Bottom Emerald Ribbon", "shape": "ribbon", "color": "#f4e7bf", "background": "#12372c", "border_color": "#bfa05b", "font_scale": .42, "padding_x": 22, "padding_y": 8, "align": "center", "opacity": .94, "placement": "below"},
}

AYAH_NUMBER_TEMPLATES = {
    "gold_medallion": {"name": "Gold Medallion", "shape": "medallion", "color": "#ffdf8e", "background": "#21190b", "border_color": "#d0aa55", "font_scale": .38, "padding_x": 14, "padding_y": 10, "align": "center", "opacity": .96},
    "ornate_badge": {"name": "Ornate Badge", "shape": "ornamental", "color": "#f5d990", "background": "#19150e", "border_color": "#b89852", "font_scale": .36, "padding_x": 17, "padding_y": 7, "align": "center", "opacity": .9},
    "simple_gold": {"name": "Simple Gold", "shape": "none", "color": "#ffdf8e", "background": None, "border_color": None, "font_scale": .34, "padding_x": 10, "padding_y": 5, "align": "center", "opacity": 1},
    "emerald_circle": {"name": "Emerald Circle", "shape": "medallion", "color": "#f6e8bd", "background": "#124132", "border_color": "#d0b36c", "font_scale": .35, "padding_x": 14, "padding_y": 10, "align": "center", "opacity": .96},
    "glow_number": {"name": "Glowing Number", "shape": "none", "color": "#fff1ba", "background": None, "border_color": None, "font_scale": .38, "padding_x": 10, "padding_y": 5, "align": "center", "opacity": 1, "glow": True},
    "transparent_number": {"name": "Transparent Number", "shape": "none", "color": "#ffffff", "background": None, "border_color": None, "font_scale": .32, "padding_x": 6, "padding_y": 3, "align": "center", "opacity": 1},
    "geometric_square": {"name": "Geometric Square Badge", "shape": "ornamental", "color": "#f6e8bd", "background": "#102c25", "border_color": "#c7a45a", "font_scale": .34, "padding_x": 15, "padding_y": 11, "align": "center", "opacity": .94},
    "quiet_corner": {"name": "Quiet Corner Number", "shape": "pill", "color": "#fff3d0", "background": "#101820", "border_color": "#d0b36c", "font_scale": .30, "padding_x": 12, "padding_y": 6, "align": "right", "opacity": .86},
    "bottom_medallion": {"name": "Bottom Medallion", "shape": "medallion", "color": "#ffdf8e", "background": "#21190b", "border_color": "#d0aa55", "font_scale": .36, "padding_x": 14, "padding_y": 10, "align": "center", "opacity": .96, "placement": "below"},
}

TRANSITION_TEMPLATES = {
    "cut": {"name": "Hard Cut", "style": "cut", "duration": 0, "direction": "none"},
    "crossfade": {"name": "Crossfade", "style": "crossfade", "duration": .45, "direction": "none"},
    "dissolve": {"name": "Smooth Dissolve", "style": "dissolve", "duration": .6, "direction": "none"},
    "fade_black": {"name": "Fade through Black", "style": "fade_black", "duration": .7, "direction": "none"},
    "fade_color": {"name": "Fade through Color", "style": "fade_color", "duration": .7, "direction": "none"},
    "slide_left": {"name": "Slide Left", "style": "slide_left", "duration": .5, "direction": "left"},
    "slide_right": {"name": "Slide Right", "style": "slide_right", "duration": .5, "direction": "right"},
    "zoom": {"name": "Gentle Zoom", "style": "zoom", "duration": .6, "direction": "in"},
}
