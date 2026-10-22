
(() => {
  const $ = (id) => document.getElementById(id);
  const videoTemplates = {"cinematic_nature": {"ayah_number_template": "gold_medallion", "ayah_range_format": "label", "ayah_range_language": "english", "caption_color": "white", "caption_position": "center", "caption_style": "soft_white", "corner_radius": 24, "description": "Soft white Naskh, a quiet surah pill, and gold playback details.", "font_id": "naskh", "glow_type": "none", "header_surah_language": "english", "name": "Cinematic Nature", "progress_color": "#edbd36", "progress_height": 6, "progress_track_color": "#d1d5db", "reciter_background": "#10161d", "reciter_color": "#ffffff", "reciter_opacity": 0.88, "show_ayah_number": true, "show_ayah_range": true, "show_header_surah": true, "show_progress": true, "show_qari_in_header": true, "show_quran_text": true, "show_reciter_badge": false, "show_surah_arabic": true, "show_surah_title": true, "show_title_icon": true, "show_translation": false, "show_viewer_title": true, "show_waveform": true, "surah_color": "#edc85f", "surah_template": "ornamental_gold", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "misty_forest", "title_accent": "#edc85f", "title_color": "#ffffff", "title_opacity": 0.88, "title_position": "top", "title_size": 0.027, "title_template": "dark_pill", "translation_bg_color": "#10161d", "translation_bg_enabled": false, "translation_bg_opacity": 0.4, "translation_color": "#ffffff", "translation_size": 0.026, "waveform_color": "#f0c64b", "waveform_count": 13, "waveform_speed": 1, "waveform_style": "gold"}, "clean_arabic": {"ayah_number_template": "gold_medallion", "ayah_range_format": "label", "ayah_range_language": "english", "caption_color": "white", "caption_position": "center", "caption_style": "minimal", "corner_radius": 24, "description": "A pared-back Arabic composition with progress only.", "font_id": "naskh", "glow_type": "none", "header_surah_language": "english", "name": "Clean Arabic", "progress_color": "#ffffff", "progress_height": 4, "progress_track_color": "#505050", "reciter_background": "#10161d", "reciter_color": "#ffffff", "reciter_opacity": 0.8, "show_ayah_number": false, "show_ayah_range": false, "show_header_surah": false, "show_progress": true, "show_qari_in_header": false, "show_quran_text": true, "show_reciter_badge": false, "show_surah_arabic": false, "show_surah_title": false, "show_title_icon": true, "show_translation": false, "show_viewer_title": false, "show_waveform": false, "surah_color": "#e5c16e", "surah_template": "ornamental_gold", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "marble_arch", "title_accent": "#e5c16e", "title_color": "#ffffff", "title_opacity": 0.8, "title_position": "top", "title_size": 0.027, "title_template": "dark_pill", "translation_bg_color": "#10161d", "translation_bg_enabled": false, "translation_bg_opacity": 0.4, "translation_color": "#ffffff", "translation_size": 0.024, "waveform_color": "#ffffff", "waveform_count": 9, "waveform_speed": 1, "waveform_style": "minimal"}, "elegant_dark": {"ayah_number_template": "gold_medallion", "ayah_range_format": "label", "ayah_range_language": "english", "caption_color": "white", "caption_position": "center", "caption_style": "soft_white", "corner_radius": 24, "description": "Dark cinematic background, glowing verse, and a warm gold timeline.", "font_id": "naskh", "glow_type": "none", "header_surah_language": "english", "name": "Elegant Dark", "progress_color": "#e5c16e", "progress_height": 6, "progress_track_color": "#64646b", "reciter_background": "#10161d", "reciter_color": "#ffffff", "reciter_opacity": 0.9, "show_ayah_number": true, "show_ayah_range": true, "show_header_surah": true, "show_progress": true, "show_qari_in_header": true, "show_quran_text": true, "show_reciter_badge": false, "show_surah_arabic": true, "show_surah_title": true, "show_title_icon": true, "show_translation": false, "show_viewer_title": true, "show_waveform": true, "surah_color": "#e5c16e", "surah_template": "ornamental_gold", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "midnight_blue", "title_accent": "#e5c16e", "title_color": "#ffffff", "title_opacity": 0.9, "title_position": "top", "title_size": 0.027, "title_template": "dark_pill", "translation_bg_color": "#10161d", "translation_bg_enabled": false, "translation_bg_opacity": 0.4, "translation_color": "#ffffff", "translation_size": 0.024, "waveform_color": "#e5c16e", "waveform_count": 13, "waveform_speed": 0.9, "waveform_style": "glow"}, "emerald_luxury": {"ayah_number_template": "gold_medallion", "ayah_range_format": "label", "ayah_range_language": "english", "caption_color": "ivory", "caption_position": "center", "caption_style": "quranic", "corner_radius": 24, "description": "Ivory calligraphy with coordinated emerald and antique-gold badges.", "font_id": "naskh_bold", "glow_type": "none", "header_surah_language": "english", "name": "Emerald Islamic Luxury", "progress_color": "#d8c06e", "progress_height": 6, "progress_track_color": "#637568", "reciter_background": "#12372c", "reciter_color": "#f7efdd", "reciter_opacity": 0.94, "show_ayah_number": true, "show_ayah_range": true, "show_header_surah": true, "show_progress": true, "show_qari_in_header": true, "show_quran_text": true, "show_reciter_badge": false, "show_surah_arabic": true, "show_surah_title": true, "show_title_icon": true, "show_translation": false, "show_viewer_title": true, "show_waveform": true, "surah_color": "#d2b15d", "surah_template": "ornamental_gold", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "jade_courtyard", "title_accent": "#d2b15d", "title_color": "#f7efdd", "title_opacity": 0.94, "title_position": "top", "title_size": 0.027, "title_template": "gold_ornament", "translation_bg_color": "#10161d", "translation_bg_enabled": false, "translation_bg_opacity": 0.4, "translation_color": "#f7efdd", "translation_size": 0.024, "waveform_color": "#d8c06e", "waveform_count": 13, "waveform_speed": 0.9, "waveform_style": "gold"}, "emerald_serenity": {"ayah_color": "#f6e8bd", "ayah_number_template": "emerald_circle", "caption_color": "ivory", "caption_position": "center", "caption_style": "quranic", "corner_radius": 26, "description": "Soft ivory calligraphy with an emerald glow", "font_id": "naskh_bold", "glow_type": "emerald", "max_lines": 5, "name": "Emerald Serenity", "show_ayah_number": true, "show_surah_title": true, "surah_color": "#e4c574", "surah_template": "emerald_ribbon", "text_bg_color": "#061e16", "text_bg_enabled": true, "text_bg_opacity": 0.62, "theme": "olive_garden"}, "golden_calligraphy": {"ayah_color": "#ffdf8e", "ayah_number_template": "gold_medallion", "caption_color": "gold", "caption_position": "center", "caption_style": "golden_illuminated", "corner_radius": 28, "description": "Warm gold lettering on a quiet dark scene", "font_id": "naskh", "glow_type": "gold", "max_lines": 5, "name": "Golden Calligraphy", "show_ayah_number": true, "show_surah_title": true, "surah_color": "#ffd166", "surah_template": "ornamental_gold", "text_bg_color": "#090806", "text_bg_enabled": true, "text_bg_opacity": 0.68, "theme": "copper_dusk"}, "golden_quran": {"ayah_number_template": "gold_medallion", "ayah_range_format": "label", "ayah_range_language": "english", "caption_color": "gold", "caption_position": "center", "caption_style": "golden_illuminated", "corner_radius": 24, "description": "Gold calligraphy and warm ornamental accents over copper dusk.", "font_id": "naskh", "glow_type": "none", "header_surah_language": "english", "name": "Golden Quran", "progress_color": "#ffc84a", "progress_height": 7, "progress_track_color": "#6b6250", "reciter_background": "#21190b", "reciter_color": "#ffe5a7", "reciter_opacity": 0.92, "show_ayah_number": true, "show_ayah_range": true, "show_header_surah": true, "show_progress": true, "show_qari_in_header": true, "show_quran_text": true, "show_reciter_badge": false, "show_surah_arabic": true, "show_surah_title": true, "show_title_icon": true, "show_translation": false, "show_viewer_title": true, "show_waveform": true, "surah_color": "#f2c14e", "surah_template": "ornamental_gold", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "copper_dusk", "title_accent": "#f2c14e", "title_color": "#fff7e7", "title_opacity": 0.94, "title_position": "top", "title_size": 0.027, "title_template": "gold_ornament", "translation_bg_color": "#10161d", "translation_bg_enabled": false, "translation_bg_opacity": 0.4, "translation_color": "#fff2cf", "translation_size": 0.024, "waveform_color": "#ffc84a", "waveform_count": 13, "waveform_speed": 0.85, "waveform_style": "glow"}, "minimal_cream": {"ayah_color": "#755c2e", "ayah_number_template": "transparent_number", "caption_color": "ink", "caption_position": "center", "caption_style": "subtle_outline", "corner_radius": 0, "description": "Uncluttered typography with a restrained outline", "font_id": "sans", "glow_type": "none", "max_lines": 5, "name": "Minimal Cream", "show_ayah_number": true, "show_surah_title": false, "surah_color": "#755c2e", "surah_template": "minimal_header", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "pearl_dawn"}, "minimalist_white": {"ayah_number_template": "gold_medallion", "ayah_range_format": "label", "ayah_range_language": "english", "caption_color": "ink", "caption_position": "center", "caption_style": "subtle_outline", "corner_radius": 24, "description": "Clean outlined verse, blue timeline, and a light title treatment.", "font_id": "naskh", "glow_type": "none", "header_surah_language": "english", "name": "Minimalist White", "progress_color": "#006aff", "progress_height": 4, "progress_track_color": "#ffffff", "reciter_background": "#10161d", "reciter_color": "#ffffff", "reciter_opacity": 0.6, "show_ayah_number": true, "show_ayah_range": true, "show_header_surah": true, "show_progress": true, "show_qari_in_header": true, "show_quran_text": true, "show_reciter_badge": false, "show_surah_arabic": false, "show_surah_title": false, "show_title_icon": true, "show_translation": false, "show_viewer_title": true, "show_waveform": true, "surah_color": "#006aff", "surah_template": "ornamental_gold", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "pearl_dawn", "title_accent": "#006aff", "title_color": "#18212b", "title_opacity": 0.94, "title_position": "top", "title_size": 0.027, "title_template": "minimal_white", "translation_bg_color": "#10161d", "translation_bg_enabled": false, "translation_bg_opacity": 0.4, "translation_color": "#ffffff", "translation_size": 0.023, "waveform_color": "#ffffff", "waveform_count": 9, "waveform_speed": 0.8, "waveform_style": "minimal"}, "modern_translation": {"ayah_number_template": "gold_medallion", "ayah_range_format": "label", "ayah_range_language": "english", "caption_color": "white", "caption_position": "upper", "caption_style": "clean_subtitle", "corner_radius": 24, "description": "Upper Arabic caption with space for a supplied English translation.", "font_id": "naskh", "glow_type": "none", "header_surah_language": "english", "name": "Modern Translation", "progress_color": "#55bdff", "progress_height": 5, "progress_track_color": "#637488", "reciter_background": "#08213a", "reciter_color": "#ffffff", "reciter_opacity": 0.86, "show_ayah_number": true, "show_ayah_range": true, "show_header_surah": true, "show_progress": true, "show_qari_in_header": true, "show_quran_text": true, "show_reciter_badge": false, "show_surah_arabic": false, "show_surah_title": false, "show_title_icon": true, "show_translation": true, "show_viewer_title": true, "show_waveform": true, "surah_color": "#73cbff", "surah_template": "ornamental_gold", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "sapphire_horizon", "title_accent": "#73cbff", "title_color": "#ffffff", "title_opacity": 0.82, "title_position": "top", "title_size": 0.027, "title_template": "dark_pill", "translation_bg_color": "#10161d", "translation_bg_enabled": false, "translation_bg_opacity": 0.4, "translation_color": "#ffffff", "translation_size": 0.026, "waveform_color": "#73cbff", "waveform_count": 13, "waveform_speed": 1.2, "waveform_style": "white"}, "moonlit_masjid": {"ayah_color": "#fff1ba", "ayah_number_template": "glow_number", "caption_color": "white", "caption_position": "center", "caption_style": "soft_white", "corner_radius": 30, "description": "A calm night palette with a luminous verse", "font_id": "naskh", "glow_type": "white", "max_lines": 5, "name": "Moonlit Masjid", "show_ayah_number": true, "show_surah_title": true, "surah_color": "#f2d18e", "surah_template": "soft_glow", "text_bg_color": "#080d1b", "text_bg_enabled": true, "text_bg_opacity": 0.64, "theme": "masjid_night"}, "night_sky": {"ayah_number_template": "gold_medallion", "ayah_range_format": "label", "ayah_range_language": "english", "caption_color": "white", "caption_position": "center", "caption_style": "soft_white", "corner_radius": 24, "description": "Luminous white verse and cool blue indicators on a moonlit scene.", "font_id": "naskh", "glow_type": "none", "header_surah_language": "english", "name": "Night Sky", "progress_color": "#9bcfff", "progress_height": 6, "progress_track_color": "#5f6c82", "reciter_background": "#0b1930", "reciter_color": "#ffffff", "reciter_opacity": 0.82, "show_ayah_number": true, "show_ayah_range": true, "show_header_surah": true, "show_progress": true, "show_qari_in_header": true, "show_quran_text": true, "show_reciter_badge": false, "show_surah_arabic": true, "show_surah_title": true, "show_title_icon": true, "show_translation": false, "show_viewer_title": true, "show_waveform": true, "surah_color": "#9bcfff", "surah_template": "ornamental_gold", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "sahara_moon", "title_accent": "#9bcfff", "title_color": "#ffffff", "title_opacity": 0.8, "title_position": "top", "title_size": 0.027, "title_template": "dark_pill", "translation_bg_color": "#10161d", "translation_bg_enabled": false, "translation_bg_opacity": 0.4, "translation_color": "#ffffff", "translation_size": 0.024, "waveform_color": "#d9edff", "waveform_count": 17, "waveform_speed": 1.1, "waveform_style": "white"}, "sapphire_horizon": {"ayah_color": "#d8e9ff", "ayah_number_template": "ornate_badge", "caption_color": "white", "caption_position": "center", "caption_style": "frosted", "corner_radius": 32, "description": "Cool blue waves with a soft white glow", "font_id": "kufi", "glow_type": "blue", "max_lines": 5, "name": "Sapphire Horizon", "show_ayah_number": true, "show_surah_title": true, "surah_color": "#d8e9ff", "surah_template": "classic_label", "text_bg_color": "#061427", "text_bg_enabled": true, "text_bg_opacity": 0.48, "theme": "sapphire_horizon"}, "soft_light": {"ayah_number_template": "gold_medallion", "ayah_range_format": "label", "ayah_range_language": "english", "caption_color": "ivory", "caption_position": "center", "caption_style": "subtle_shadow", "corner_radius": 24, "description": "Gentle cream typography and restrained gold playback markers.", "font_id": "naskh", "glow_type": "none", "header_surah_language": "english", "name": "Soft Light", "progress_color": "#d4a943", "progress_height": 5, "progress_track_color": "#f4e8c8", "reciter_background": "#302516", "reciter_color": "#ffffff", "reciter_opacity": 0.72, "show_ayah_number": false, "show_ayah_range": true, "show_header_surah": true, "show_progress": true, "show_qari_in_header": true, "show_quran_text": true, "show_reciter_badge": false, "show_surah_arabic": true, "show_surah_title": true, "show_title_icon": true, "show_translation": false, "show_viewer_title": true, "show_waveform": true, "surah_color": "#c99a3b", "surah_template": "ornamental_gold", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "golden_dunes", "title_accent": "#c99a3b", "title_color": "#18212b", "title_opacity": 0.9, "title_position": "top", "title_size": 0.027, "title_template": "minimal_white", "translation_bg_color": "#10161d", "translation_bg_enabled": false, "translation_bg_opacity": 0.4, "translation_color": "#ffffff", "translation_size": 0.024, "waveform_color": "#d4a943", "waveform_count": 9, "waveform_speed": 0.75, "waveform_style": "gold"}, "starlit_recitation": {"ayah_color": "#e8d29a", "ayah_number_template": "gold_medallion", "caption_color": "ivory", "caption_position": "lower", "caption_style": "quranic", "corner_radius": 24, "description": "A quiet celestial backdrop with gold verse details", "font_id": "naskh_bold", "glow_type": "gold", "max_lines": 5, "name": "Starlit Recitation", "show_ayah_number": true, "show_surah_title": true, "surah_color": "#e8d29a", "surah_template": "ornamental_gold", "text_bg_color": "#090f1d", "text_bg_enabled": true, "text_bg_opacity": 0.58, "theme": "sahara_moon"}, "traditional_calligraphy": {"ayah_number_template": "gold_medallion", "ayah_range_format": "label", "ayah_range_language": "english", "caption_color": "ivory", "caption_position": "center", "caption_style": "quranic", "corner_radius": 24, "description": "Traditional Naskh with measured gold labels and waveform.", "font_id": "naskh_bold", "glow_type": "none", "header_surah_language": "english", "name": "Traditional Calligraphy", "progress_color": "#e7c56c", "progress_height": 6, "progress_track_color": "#68604a", "reciter_background": "#222015", "reciter_color": "#fff2ca", "reciter_opacity": 0.9, "show_ayah_number": true, "show_ayah_range": true, "show_header_surah": true, "show_progress": true, "show_qari_in_header": true, "show_quran_text": true, "show_reciter_badge": false, "show_surah_arabic": true, "show_surah_title": true, "show_title_icon": true, "show_translation": false, "show_viewer_title": true, "show_waveform": true, "surah_color": "#c8a557", "surah_template": "ornamental_gold", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0, "theme": "olive_garden", "title_accent": "#c8a557", "title_color": "#fff2ca", "title_opacity": 0.92, "title_position": "top", "title_size": 0.027, "title_template": "gold_ornament", "translation_bg_color": "#10161d", "translation_bg_enabled": false, "translation_bg_opacity": 0.4, "translation_color": "#fff2ca", "translation_size": 0.023, "waveform_color": "#e7c56c", "waveform_count": 13, "waveform_speed": 0.82, "waveform_style": "gold"}};
  const textTemplates = {"cinematic_white": {"caption_color": "white", "caption_style": "soft_white", "description": "White Naskh with a restrained glow", "font_id": "naskh", "glow_type": "white", "name": "Cinematic White", "text_bg_color": "#08111d", "text_bg_enabled": true, "text_bg_opacity": 0.58}, "clear_outline": {"caption_color": "white", "caption_style": "subtle_outline", "description": "Readable text directly over the background", "font_id": "naskh", "glow_type": "none", "name": "Clear Outline", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0}, "cream_nature": {"caption_color": "ivory", "caption_style": "subtle_shadow", "description": "Soft cream text with a natural palette", "font_id": "naskh", "glow_type": "none", "name": "Cream on Nature", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0}, "emerald_luxury": {"caption_color": "ivory", "caption_style": "quranic", "description": "Cream lettering with emerald light", "font_id": "naskh_bold", "glow_type": "emerald", "name": "Emerald Luxury", "text_bg_color": "#061e16", "text_bg_enabled": true, "text_bg_opacity": 0.62}, "gold_on_black": {"caption_color": "gold", "caption_style": "golden_illuminated", "description": "Premium gold verse on a dark plate", "font_id": "naskh_bold", "glow_type": "gold", "name": "Gold on Black", "text_bg_color": "#050505", "text_bg_enabled": true, "text_bg_opacity": 0.82}, "luminous_gold": {"caption_color": "gold", "caption_style": "golden_illuminated", "description": "Warm gold letters with a soft glow", "font_id": "naskh", "glow_type": "gold", "name": "Luminous Gold", "text_bg_color": "#090806", "text_bg_enabled": true, "text_bg_opacity": 0.68}, "minimal_dark": {"caption_color": "white", "caption_style": "minimal", "description": "Clean white verse with no panel", "font_id": "naskh", "glow_type": "none", "name": "Minimal Dark", "text_bg_color": "#000000", "text_bg_enabled": false, "text_bg_opacity": 0}, "modern_gradient": {"caption_color": "sky", "caption_style": "bold_modern", "description": "Bright blue lettering with crisp outline", "font_id": "kufi", "glow_type": "blue", "name": "Modern Blue", "text_bg_color": "#07162a", "text_bg_enabled": true, "text_bg_opacity": 0.72}, "ornate_frame": {"caption_color": "ivory", "caption_style": "quranic", "description": "Framed Arabic with a warm gold accent", "font_id": "naskh", "glow_type": "gold", "name": "Ornate Frame", "text_bg_color": "#0a0b0b", "text_bg_enabled": true, "text_bg_opacity": 0.7}, "traditional_naskh": {"caption_color": "ivory", "caption_style": "quranic", "description": "Readable classic Quran typography", "font_id": "naskh", "glow_type": "none", "name": "Traditional Naskh", "text_bg_color": "#0a0c10", "text_bg_enabled": true, "text_bg_opacity": 0.65}};
  const fontCatalog = {"kufi": {"name": "Noto Kufi Arabic"}, "kufi_bold": {"name": "Noto Kufi Arabic Bold"}, "naskh": {"name": "Noto Naskh Arabic"}, "naskh_bold": {"name": "Noto Naskh Arabic Bold"}, "sans": {"name": "Noto Sans Arabic"}, "sans_bold": {"name": "Noto Sans Arabic Bold"}};
  const imageAnimationPresets = {"cinematic_zoom": {"description": "A very slow, smooth push toward the scene.", "name": "Cinematic zoom", "pan_x": [0.5, 0.5], "pan_y": [0.5, 0.5], "zoom": [1.0, 1.09]}, "floating_camera": {"description": "A slow, subtle floating movement.", "name": "Floating camera", "pan_x": [0.3, 0.7], "pan_y": [0.38, 0.62], "zoom": [1.055, 1.075]}, "gentle_movement": {"description": "A restrained zoom with a small diagonal drift.", "name": "Gentle movement", "pan_x": [0.42, 0.58], "pan_y": [0.58, 0.42], "zoom": [1.025, 1.06]}, "parallax_depth": {"description": "A slow forward move with a mild vertical shift.", "name": "Parallax depth", "pan_x": [0.44, 0.56], "pan_y": [0.62, 0.38], "zoom": [1.04, 1.105]}, "slow_pan_bottom_to_top": {"description": "A gentle vertical drift.", "name": "Move bottom to top", "pan_x": [0.5, 0.5], "pan_y": [0.0, 1.0], "zoom": [1.08, 1.08]}, "slow_pan_left": {"description": "A gentle horizontal camera move.", "name": "Slow pan left", "pan_x": [1.0, 0.0], "pan_y": [0.5, 0.5], "zoom": [1.08, 1.08]}, "slow_pan_right": {"description": "A gentle horizontal camera move.", "name": "Slow pan right", "pan_x": [0.0, 1.0], "pan_y": [0.5, 0.5], "zoom": [1.08, 1.08]}, "slow_pan_top_to_bottom": {"description": "A gentle vertical drift.", "name": "Move top to bottom", "pan_x": [0.5, 0.5], "pan_y": [1.0, 0.0], "zoom": [1.08, 1.08]}, "static": {"description": "Keep the background still.", "name": "Static image", "pan_x": [0.5, 0.5], "pan_y": [0.5, 0.5], "zoom": [1.0, 1.0]}};
  const backgroundSequenceTemplates = {"moonlit_horizons": {"animation_duration": 22, "animation_intensity": 0.35, "animation_preset": "floating_camera", "animation_speed": 0.7, "description": "Five celestial scenes with restrained floating camera motion.", "loop": true, "name": "Moonlit Horizons", "scenes": [{"duration": 7, "theme": "sahara_moon"}, {"duration": 7, "theme": "midnight_blue"}, {"duration": 7, "theme": "lavender_twilight"}, {"duration": 7, "theme": "crescent_garden"}, {"duration": 7, "theme": "aurora_drift"}], "transition": "dissolve", "transition_duration": 0.8}, "mosque_at_dusk": {"animation_duration": 20, "animation_intensity": 0.4, "animation_preset": "cinematic_zoom", "animation_speed": 0.75, "description": "Five illuminated mosque and courtyard scenes in a quiet palette.", "loop": true, "name": "Mosque at Dusk", "scenes": [{"duration": 7, "theme": "masjid_night"}, {"duration": 7, "theme": "olive_garden"}, {"duration": 7, "theme": "jade_courtyard"}, {"duration": 7, "theme": "marble_arch"}, {"duration": 7, "theme": "turquoise_mosaic"}], "transition": "crossfade", "transition_duration": 0.75}, "nature_in_motion": {"animation_duration": 18, "animation_intensity": 0.45, "animation_preset": "gentle_movement", "animation_speed": 0.8, "description": "Five calm landscape scenes with gentle camera movement.", "loop": true, "name": "Nature in Motion", "scenes": [{"duration": 7, "theme": "misty_forest"}, {"duration": 7, "theme": "cloud_morning"}, {"duration": 7, "theme": "golden_dunes"}, {"duration": 7, "theme": "desert_dawn"}, {"duration": 7, "theme": "sapphire_horizon"}], "transition": "crossfade", "transition_duration": 0.7}, "waterside_reflections": {"animation_duration": 24, "animation_intensity": 0.3, "animation_preset": "slow_pan_right", "animation_speed": 0.65, "description": "Five water and atmosphere scenes, softly graded for readable captions.", "loop": true, "name": "Waterside Reflections", "scenes": [{"duration": 7, "theme": "ocean_calm"}, {"duration": 7, "theme": "sapphire_horizon"}, {"duration": 7, "theme": "pearl_dawn"}, {"duration": 7, "theme": "rose_sand"}, {"duration": 7, "theme": "plum_evening"}], "transition": "fade_black", "transition_duration": 0.65}};
  const backgroundVideoTemplates = {"marble_arch_glow": {"description": "A quiet architectural scene with a warm, gentle push.", "duration": 6, "filename": "marble_arch_glow.mp4", "name": "Marble Arch Glow", "theme": "marble_arch"}, "misty_forest_drift": {"description": "Sunlit mist with a slow, seamless camera drift.", "duration": 6, "filename": "misty_forest_drift.mp4", "name": "Misty Forest Drift", "theme": "misty_forest"}, "moonlit_horizon": {"description": "A cool night landscape with subtle floating movement.", "duration": 6, "filename": "moonlit_horizon.mp4", "name": "Moonlit Horizon", "theme": "sahara_moon"}};
  let selectedTemplateId = videoTemplates.cinematic_nature ? 'cinematic_nature' : Object.keys(videoTemplates)[0];
  const initialTemplate = videoTemplates[selectedTemplateId];
  let selectedReciter = 'mishary_alafasy';
  let ratio = '9:16';
  const qualityProfiles = {"balanced": {"crf": 23, "label": "Balanced", "preset": "veryfast"}, "fast": {"crf": 29, "label": "Fast", "preset": "ultrafast"}, "high": {"crf": 19, "label": "High Quality", "preset": "medium"}, "maximum": {"crf": 17, "label": "Maximum Quality", "preset": "slow"}};
  let theme = initialTemplate.theme;
  let captionColor = initialTemplate.caption_color;
  let wrapWidth = 85;
  let speed = 1.0;
  let verseLoadTimer;
  let verseLoadRequest = 0;
  let activeRenderJobId = null;
  let lastDownloadUrl = null;
  let previewAyahs = [];
  let previewScenes = [];
  let previewTimings = [];
  let previewIndex = 0;
  let previewObjectUrls = [];
  let selectedBackgroundFiles = [];
  let backgroundClipRows = [];
  let previewClipIndex = 0;
  let previewClipAdvancing = false;
  let currentBackgroundKind = null;
  let backgroundMediaCategory = 'image';
  let selectedBackgroundVideoTemplate = '';
  let backgroundPreviewTimer;
  let sequencePreviewTimer = null;
  let sequencePreviewFadeTimer = null;
  let sequencePreviewCleanupTimer = null;
  let builtinSequencePreviewTimer = null;
  let builtinSequenceIndex = 0;
  let animationPreviewFrame = null;
  let animationPreviewStartedAt = performance.now();
  let loadedVerseSelection = '';
  let scenePlanRequest = 0;
  let scenePlanManual = false;
  let scenePlanTimer;
  const surahSelect = $('surah-select');
  const startInput = $('start-ayah');
  const endInput = $('end-ayah');
  const ayahText = $('ayah-text');
  const reciterList = $('reciters-list');
  const PROJECT_DRAFT_KEY = 'quran-reels-studio-draft-v1';
  const SAVED_PROJECTS_KEY = 'quran-reels-studio-projects-v1';
  const CUSTOM_DESIGNS_KEY = 'quran-reels-studio-custom-designs-v1';
  const PROJECT_TEMPLATE_FIELDS = [
    'caption-style','arabic-font','max-lines','show-surah-title','show-ayah-number',
    'show-quran-text','viewer-title-enabled','viewer-title-icon-enabled','viewer-header-surah-enabled','viewer-header-surah-language','viewer-header-range-enabled','viewer-header-range-language','viewer-header-range-format','viewer-header-qari-enabled','viewer-title-text','viewer-title-template','viewer-title-color','viewer-title-opacity','viewer-title-size','viewer-title-position',
    'show-translation','translation-text','translation-color','translation-size','translation-bg-enabled','translation-bg-color','translation-bg-opacity','show-waveform','waveform-style','waveform-color','waveform-count','waveform-speed',
    'show-reciter-badge','reciter-label','reciter-color','reciter-background','reciter-opacity','show-progress','progress-color','progress-track-color','progress-height',
    'surah-name-template','ayah-number-template','surah-color','ayah-color','surah-scale',
    'ayah-number-scale','surah-align','ayah-number-align','surah-font-id','ayah-number-font-id',
    'surah-opacity','ayah-number-opacity','surah-placement','ayah-number-placement','caption-position','text-bg-enabled',
    'text-bg-color','text-bg-opacity','glow-type','glow-radius','quran-text-template','wrap-width',
    'transition-style','background-fit','background-crop-x','background-crop-y','background-speed',
    'background-animation-enabled','background-motion-direction','background-animation-preset','background-animation-intensity',
    'background-animation-duration','background-animation-speed','background-animation-start',
    'background-atmosphere-enabled','background-atmosphere-intensity','background-atmosphere-duration',
    'background-atmosphere-speed','background-atmosphere-start','transitions-enabled',
    'background-sequence-template','sequence-enabled','transitions-enabled',
    'background-video-template',
    'default-background-transition','background-transition-color','background-transition-duration',
    'background-loop','background-brightness','background-contrast','background-saturation',
    'background-overlay-color','background-overlay-opacity','background-audio-enabled',
    'background-audio-volume','export-resolution','custom-width','custom-height','export-fps',
    'export-quality','export-encoder','export-crf','audio-bitrate','audio-sample-rate',
    'sequence-enabled','transitions-enabled','default-background-transition','background-transition-color',
    'background-transition-duration','sequence-loop','background-animation-enabled',
    'background-motion-direction','background-animation-preset','background-animation-intensity','background-animation-duration',
    'background-animation-speed',
  ];
  const EXCLUDED_PROJECT_FIELDS = new Set([
    'reciter-filter-input','background-search','background-category','preview-scrubber',
    'preview-volume','saved-projects','custom-template-list','custom-template-name',
  ]);
  let activeProjectId = 'draft';
  let projectDatabasePromise = null;
  let mediaSignatures = new Map();
  let undoHistory = [];
  let redoHistory = [];
  let historyApplying = false;
  let autosaveTimer = null;
  let autosaveQueue = Promise.resolve();
  let lastPersistedSignature = '';

  function makeEditorSnapshot() {
    const fields = {};
    document.querySelectorAll('input[id],select[id],textarea[id]').forEach(element => {
      if (element.type === 'file' || EXCLUDED_PROJECT_FIELDS.has(element.id)) return;
      fields[element.id] = element.type === 'checkbox' ? element.checked : element.value;
    });
    return {
      version: 2, fields, projectName: $('project-name').value.trim() || 'Untitled Reel',
      videoTemplate: selectedTemplateId, reciter: selectedReciter, ratio, theme,
      captionColor, wrapWidth, speed, scenePlanManual,
      scenes: scenePlanManual ? previewScenes.map(scene => ({
        ayah_number:scene.ayah_number, text:scene.text,
        ...(scene.manual_duration_fraction ? {duration_fraction:scene.duration_fraction} : {}),
      })) : [],
      mediaClips: backgroundClipRows.map(row => ({
        file:row.file, name:row.file?.name || '', size:row.file?.size || 0,
        type:row.file?.type || '', lastModified:row.file?.lastModified || 0,
        start:row.start, end:row.end, speed:row.speed, transition:row.transition,
        transition_duration:row.transition_duration, duration:row.duration,
      })),
    };
  }

  function serializableProjectSnapshot(snapshot) {
    return {...snapshot, mediaClips:(snapshot.mediaClips || []).map(({file, ...clip}) => clip)};
  }

  function snapshotSignature(snapshot) {
    return JSON.stringify(serializableProjectSnapshot(snapshot));
  }

  function safeReadStorage(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; }
    catch (_) { return fallback; }
  }

  function savedProjectRecords() {
    const records = safeReadStorage(SAVED_PROJECTS_KEY, []);
    return Array.isArray(records) ? records.filter(item => item && item.id && item.state) : [];
  }

  function customDesignRecords() {
    const records = safeReadStorage(CUSTOM_DESIGNS_KEY, []);
    return Array.isArray(records) ? records.filter(item => item && item.id && item.name && item.design) : [];
  }

  function newLocalId(prefix) {
    return `${prefix}-${window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2,10)}`}`;
  }

  function openProjectDatabase() {
    if (!window.indexedDB) return Promise.reject(new Error('This browser does not provide local media storage.'));
    if (!projectDatabasePromise) {
      projectDatabasePromise = new Promise((resolve, reject) => {
        const request = indexedDB.open('QuranReelsStudio', 1);
        request.onupgradeneeded = () => {
          if (!request.result.objectStoreNames.contains('background_media')) {
            request.result.createObjectStore('background_media', {keyPath:'key'});
          }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error || new Error('Could not open browser media storage.'));
        request.onblocked = () => reject(new Error('Close another Quran Reels tab to enable local media storage.'));
      });
    }
    return projectDatabasePromise;
  }

  function mediaSignature(projectId, clips) {
    return `${projectId}|${(clips || []).map(item => `${item.name}:${item.size}:${item.lastModified}:${item.type}`).join('|')}`;
  }

  async function persistProjectMedia(projectId, clips) {
    const signature = mediaSignature(projectId, clips);
    if (mediaSignatures.get(projectId) === signature) return;
    const db = await openProjectDatabase();
    await new Promise((resolve, reject) => {
      const transaction = db.transaction('background_media', 'readwrite');
      const store = transaction.objectStore('background_media');
      const prefix = `${projectId}:`;
      const keys = store.getAllKeys();
      keys.onsuccess = () => {
        keys.result.filter(key => String(key).startsWith(prefix)).forEach(key => store.delete(key));
        (clips || []).forEach((clip, index) => {
          if (clip.file instanceof Blob) store.put({key:`${prefix}${index}`, file:clip.file, size:clip.size,
                                                    name:clip.name, type:clip.type, lastModified:clip.lastModified});
        });
      };
      keys.onerror = () => reject(keys.error || new Error('Could not update saved background media.'));
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error || new Error('Could not save background media in this browser.'));
      transaction.onabort = () => reject(transaction.error || new Error('Browser storage rejected the uploaded media.'));
    });
    mediaSignatures.set(projectId, signature);
  }

  async function readProjectMedia(projectId, clipSettings = []) {
    const db = await openProjectDatabase();
    const rows = await new Promise((resolve, reject) => {
      const transaction = db.transaction('background_media', 'readonly');
      const request = transaction.objectStore('background_media').getAll();
      request.onsuccess = () => resolve(request.result.filter(item => String(item.key).startsWith(`${projectId}:`))
        .sort((a,b) => Number(a.key.split(':').at(-1)) - Number(b.key.split(':').at(-1))));
      request.onerror = () => reject(request.error || new Error('Could not read saved background media.'));
    });
    mediaSignatures.set(projectId, mediaSignature(projectId, rows.map(row => row)));
    return rows.map((row,index) => {
      const saved = clipSettings[index] || {};
      const file = new File([row.file], row.name || saved.name || 'background', {
        type:row.type || saved.type || 'application/octet-stream',
        lastModified:row.lastModified || saved.lastModified || Date.now(),
      });
      return {...saved, file};
    });
  }

  async function removeProjectMedia(projectId) {
    mediaSignatures.delete(projectId);
    const db = await openProjectDatabase();
    await new Promise((resolve,reject) => {
      const transaction = db.transaction('background_media','readwrite');
      const store = transaction.objectStore('background_media');
      const keys = store.getAllKeys();
      keys.onsuccess = () => keys.result.filter(key => String(key).startsWith(`${projectId}:`)).forEach(key => store.delete(key));
      keys.onerror = () => reject(keys.error || new Error('Could not remove saved project media.'));
      transaction.oncomplete = resolve;
      transaction.onerror = () => reject(transaction.error || new Error('Could not remove saved project media.'));
    });
  }

  function refreshSavedProjects(selectedId = activeProjectId) {
    const select = $('saved-projects');
    if (!select) return;
    select.replaceChildren(new Option('Choose a saved project…',''));
    savedProjectRecords().sort((a,b) => b.updatedAt - a.updatedAt).forEach(project => {
      select.add(new Option(`${project.name} · ${new Date(project.updatedAt).toLocaleDateString()}`, project.id));
    });
    select.value = selectedId === 'draft' ? '' : selectedId;
    $('open-project-btn').disabled = !select.value;
    $('delete-project-btn').disabled = !select.value;
  }

  function refreshCustomDesigns(selectedId = '') {
    const select = $('custom-template-list');
    if (!select) return;
    select.replaceChildren(new Option('Choose a saved design…',''));
    customDesignRecords().sort((a,b) => a.name.localeCompare(b.name)).forEach(item => select.add(new Option(item.name,item.id)));
    select.value = selectedId;
    $('apply-custom-template-btn').disabled = !select.value;
    $('delete-custom-template-btn').disabled = !select.value;
    $('export-custom-template-btn').disabled = !select.value;
  }

  function setProjectStatus(message, warning = false) {
    const status = $('project-save-status');
    if (!status) return;
    status.textContent = message;
    status.classList.toggle('text-amber-700', warning);
    status.classList.toggle('text-gray-500', !warning);
  }

  function updateHistoryButtons() {
    $('undo-project-btn').disabled = undoHistory.length < 2;
    $('redo-project-btn').disabled = redoHistory.length === 0;
  }

  function updatePreviewReciterName(name) {
    const previewLabel = $('preview-reciter-name');
    if (previewLabel) previewLabel.textContent = $('reciter-label')?.value.trim() || `Sheikh ${name}`;
    updateViewerLayerPreview();
  }

  function currentPreviewAyahNumber() {
    return Number(previewScenes[previewIndex]?.ayah_number || startInput.value || 1);
  }

  function activeTranslationText() {
    if (!$('show-translation').checked) return '';
    const lines = $('translation-text').value.split(/\r?\n/);
    const index = currentPreviewAyahNumber() - Number(startInput.value || 1);
    return index >= 0 && index < lines.length ? lines[index].trim() : '';
  }

  function localizeHeaderDigits(value) {
    return String(value).replace(/\d/g, digit => '٠١٢٣٤٥٦٧٨٩'[Number(digit)]);
  }

  function currentHeaderAyahRange() {
    const included = [...new Set(previewScenes.map(scene => Number(scene.ayah_number)).filter(Number.isFinite))];
    return [included[0] || Number(startInput.value || 1), included.at(-1) || Number(endInput.value || startInput.value || 1)];
  }

  function updateViewerLayerPreview() {
    const selectedSurah = surahSelect?.selectedOptions?.[0]?.textContent || '';
    const surahParts = selectedSurah.split('·').map(part => part.trim());
    const englishName = surahParts[1] || 'Selected Surah';
    const arabicName = surahParts[2] || '';
    const range = currentHeaderAyahRange();
    const rangeStart = Math.min(...range), rangeEnd = Math.max(...range);
    const frameWidth = $('preview-frame')?.getBoundingClientRect().width || document.querySelector('.preview-frame').getBoundingClientRect().width;
    const title = $('viewer-title-badge');
    title.hidden = !$('viewer-title-enabled').checked;
    const customTitle = $('viewer-title-text').value.trim();
    const language = $('viewer-header-surah-language').value;
    const name = $('viewer-title-name');
    name.textContent = customTitle || (language === 'arabic' ? arabicName : `Surah ${englishName}`);
    name.hidden = !$('viewer-header-surah-enabled').checked;
    const arabicHeading = $('viewer-title-surah-arabic');
    arabicHeading.textContent = language === 'both' && !customTitle ? arabicName : '';
    arabicHeading.hidden = !arabicHeading.textContent || !$('viewer-header-surah-enabled').checked;
    name.dir = !customTitle && language === 'arabic' ? 'rtl' : 'auto';
    const rangeLabel = $('viewer-title-reference');
    const rangeLanguage = $('viewer-header-range-language').value;
    const compactRange = $('viewer-header-range-format').value === 'compact';
    if (rangeStart === rangeEnd) {
      rangeLabel.textContent = rangeLanguage === 'arabic'
        ? (compactRange ? localizeHeaderDigits(rangeStart) : `الآية ${localizeHeaderDigits(rangeStart)}`)
        : (compactRange ? String(rangeStart) : `Ayah ${rangeStart}`);
    } else if (rangeLanguage === 'arabic') {
      const bounds = `${localizeHeaderDigits(rangeStart)}–${localizeHeaderDigits(rangeEnd)}`;
      rangeLabel.textContent = compactRange ? bounds : `الآيات ${bounds}`;
    } else {
      const bounds = `${rangeStart}–${rangeEnd}`;
      rangeLabel.textContent = compactRange ? bounds : `Ayahs ${bounds}`;
    }
    rangeLabel.hidden = !$('viewer-header-range-enabled').checked;
    rangeLabel.dir = rangeLanguage === 'arabic' ? 'rtl' : 'ltr';
    const selectedReciterName = $('selected-reciter-name')?.textContent.trim() || '';
    const displayReciter = $('reciter-label').value.trim() || `Sheikh ${selectedReciterName}`;
    const qariInHeader = $('viewer-header-qari-enabled').checked;
    $('viewer-title-qari').textContent = displayReciter;
    $('viewer-title-qari').hidden = !qariInHeader;
    title.dataset.style = $('viewer-title-template').value;
    title.style.setProperty('--viewer-title-accent', $('viewer-title-color').value);
    title.style.setProperty('--viewer-title-opacity', $('viewer-title-opacity').value);
    $('viewer-title-icon').hidden = !$('viewer-title-icon-enabled').checked;
    title.style.top = $('viewer-title-position').value === 'upper' ? '10%' : '5.5%';
    title.style.fontSize = `${Math.max(8, frameWidth * Number($('viewer-title-size').value))}px`;

    const translation = $('viewer-translation');
    const translationText = activeTranslationText();
    translation.textContent = translationText;
    translation.classList.toggle('hidden', !translationText);
    translation.style.color = $('translation-color').value;
    translation.style.fontSize = `${Math.max(8, frameWidth * Number($('translation-size').value))}px`;
    translation.style.background = $('translation-bg-enabled').checked
      ? `color-mix(in srgb, ${$('translation-bg-color').value} ${Math.round(Number($('translation-bg-opacity').value)*100)}%, transparent)` : 'transparent';
    translation.style.padding = $('translation-bg-enabled').checked ? '.22em .6em' : '0';
    translation.style.borderRadius = $('translation-bg-enabled').checked ? '.5em' : '0';

    const reciterBadge = $('viewer-reciter-badge');
    reciterBadge.hidden = !$('show-reciter-badge').checked;
    $('preview-reciter-name').textContent = displayReciter;
    reciterBadge.style.setProperty('--viewer-reciter-color', $('reciter-color').value);
    reciterBadge.style.setProperty('--viewer-reciter-bg', $('reciter-background').value);
    reciterBadge.style.setProperty('--viewer-reciter-opacity', $('reciter-opacity').value);
    const wave = $('viewer-waveform');
    wave.hidden = !$('show-waveform').checked;
    wave.dataset.style = $('waveform-style').value;
    wave.style.setProperty('--viewer-wave-color', $('waveform-color').value);
    const barCount = Number($('waveform-count').value);
    if (wave.children.length !== barCount) {
      wave.replaceChildren(...Array.from({length:barCount}, () => document.createElement('span')));
    }
    wave.style.setProperty('--viewer-wave-speed', `${1 / Number($('waveform-speed').value)}s`);
    const progress = $('viewer-progress-track');
    progress.hidden = !$('show-progress').checked;
    progress.style.setProperty('--viewer-progress-color', $('progress-color').value);
    progress.style.setProperty('--viewer-progress-track', $('progress-track-color').value);
    progress.style.height = `${Math.max(2, Number($('progress-height').value) * frameWidth / 1080)}px`;
  }

  function activeBackgroundSequencePreset() {
    return backgroundSequenceTemplates[$('background-sequence-template').value] || null;
  }

  function updateBackgroundSequenceSelection() {
    const selectedId = $('background-sequence-template').value;
    document.querySelectorAll('.background-sequence-choice').forEach(button => {
      const selected = button.dataset.sequenceId === selectedId;
      button.classList.toggle('selected-sequence', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
  }

  async function persistProjectSnapshot(snapshot, projectId = activeProjectId, createRecord = false) {
    const serial = serializableProjectSnapshot(snapshot);
    let mediaSaved = true;
    try { await persistProjectMedia(projectId, snapshot.mediaClips); }
    catch (error) { mediaSaved = false; console.warn('Background media autosave failed:', error); }
    localStorage.setItem(PROJECT_DRAFT_KEY, JSON.stringify({projectId,state:serial}));
    const records = savedProjectRecords();
    const index = records.findIndex(item => item.id === projectId);
    if (index >= 0 || createRecord) {
      const record = {id:projectId, name:snapshot.projectName, updatedAt:Date.now(), state:serial};
      if (index >= 0) records[index] = record; else records.push(record);
      localStorage.setItem(SAVED_PROJECTS_KEY, JSON.stringify(records.slice(-40)));
      refreshSavedProjects(projectId);
    }
    setProjectStatus(mediaSaved ? 'Saved on this browser' : 'Settings saved; browser could not store the background file', !mediaSaved);
    return mediaSaved;
  }

  async function applyProjectSnapshot(snapshot, projectId = 'draft') {
    if (!snapshot || ![1, 2].includes(snapshot.version)) throw new Error('This saved project uses an unsupported format.');
    historyApplying = true;
    try {
      const fields = {...(snapshot.fields || {})};
      if (snapshot.version === 1 && fields['export-encoder'] === 'cpu') fields['export-encoder'] = 'auto';
      for (const [id,value] of Object.entries(fields)) {
        const element = $(id);
        if (!element || element.type === 'file') continue;
        if (element.tagName === 'SELECT' && ![...element.options].some(option => option.value === String(value))) continue;
        if (element.type === 'checkbox' || element.type === 'radio') element.checked = Boolean(value);
        else element.value = value;
      }
      selectedTemplateId = videoTemplates[snapshot.videoTemplate] ? snapshot.videoTemplate : selectedTemplateId;
      selectedReciter = snapshot.reciter || selectedReciter;
      ratio = ['9:16','16:9','1:1'].includes(snapshot.ratio) ? snapshot.ratio : ratio;
      theme = document.querySelector(`.background-choice[data-theme="${snapshot.theme}"]`) ? snapshot.theme : theme;
      captionColor = snapshot.captionColor || captionColor;
      wrapWidth = Number(snapshot.wrapWidth || 85);
      speed = Number(snapshot.speed || 1);
      scenePlanManual = Boolean(snapshot.scenePlanManual);
      previewScenes = scenePlanManual ? (snapshot.scenes || []).map((scene,index) => ({...scene,scene_index:index})) : [];
      $('project-name').value = snapshot.projectName || fields['project-name'] || 'Untitled Reel';
      document.querySelectorAll('.aspect-ratio-btn').forEach(button => button.classList.toggle('selected-ratio', button.dataset.ratio === ratio));
      syncPreviewAspectRatio();
      document.querySelectorAll('.video-template-choice').forEach(button => button.classList.toggle('selected-video-template', button.dataset.templateId === selectedTemplateId));
      document.querySelectorAll('.background-choice').forEach(button => button.classList.toggle('selected-background', button.dataset.theme === theme));
      document.querySelectorAll('.caption-color-choice').forEach(button => button.classList.toggle('selected-caption-color', button.dataset.color === captionColor));
      $('speed-cycle-btn').textContent = `${speed.toFixed(2).replace(/0+$/,'').replace(/\.$/,'')}x`;
      $('speed-indicator').textContent = `${speed}x (${speed === 1 ? 'Natural' : 'Adjusted'})`;
      $('custom-resolution-fields').classList.toggle('hidden', $('export-resolution').value !== 'custom');
      const customCrf = $('export-crf').value;
      updateQualityDescription();
      $('export-crf').value = customCrf;
      $('export-crf-value').textContent = customCrf;
      updateSurahInfo(); updateRangeSummary(); updateCanvasSummary();
      setWallpaperPreview(); updateBackgroundAdjustments();

      const savedClips = snapshot.mediaClips || [];
      if (savedClips.length) {
        let clips = savedClips.filter(item => item.file instanceof Blob);
        if (clips.length !== savedClips.length) {
          try { clips = await readProjectMedia(projectId, savedClips); }
          catch (error) { clips = []; console.warn('Saved background files are unavailable:', error); }
        }
        if (clips.length === savedClips.length) {
          $('background-file-name').textContent = clips.length === 1 ? clips[0].file.name : `${clips.length} saved video clips`;
          renderUploadedBackgroundPreview(clips);
        } else {
          clearCustomBackgroundPreview();
          $('background-file-name').textContent = 'Re-select the custom background used by this project';
          setProjectStatus('Settings restored; saved background media is unavailable', true);
        }
      } else if (snapshot.fields?.['background-video-template'] &&
                 selectBackgroundVideoTemplate(snapshot.fields['background-video-template'], {save:false})) {
        updateBackgroundSequenceSelection();
      } else {
        clearCustomBackgroundPreview();
        $('background-file-name').textContent = 'PNG, JPG, WEBP, MP4, MOV or WEBM';
        updateBackgroundSequenceSelection();
        playBackgroundSequenceTemplate(0);
      }
      await loadVerses(false);
      if (fields['ayah-text'] != null) ayahText.value = fields['ayah-text'];
      scenePlanManual = Boolean(snapshot.scenePlanManual);
      previewScenes = scenePlanManual ? (snapshot.scenes || []).map((scene,index) => ({...scene,scene_index:index})) : [];
      await updateScenePlan();
      await updateCaptionPreview();
      hideRenderedVideo();
    } finally { historyApplying = false; }
  }

  async function saveNamedProject() {
    const name = $('project-name').value.trim();
    if (!name) { $('project-name').focus(); setProjectStatus('Enter a project name before saving', true); return; }
    if (activeProjectId === 'draft') activeProjectId = newLocalId('project');
    const snapshot = makeEditorSnapshot(); snapshot.projectName = name;
    try {
      await persistProjectSnapshot(snapshot, activeProjectId, true);
      lastPersistedSignature = snapshotSignature(snapshot);
      if (!undoHistory.length) undoHistory.push(snapshot);
      refreshSavedProjects(activeProjectId);
    } catch (error) { setProjectStatus(`Could not save project: ${error.message}`, true); }
  }

  async function openNamedProject() {
    const project = savedProjectRecords().find(item => item.id === $('saved-projects').value);
    if (!project) return;
    activeProjectId = project.id;
    await applyProjectSnapshot(project.state, project.id);
    undoHistory = [makeEditorSnapshot()]; redoHistory = [];
    lastPersistedSignature = snapshotSignature(undoHistory[0]);
    refreshSavedProjects(activeProjectId); updateHistoryButtons();
    await persistProjectSnapshot(undoHistory[0], activeProjectId);
  }

  async function deleteNamedProject() {
    const projectId = $('saved-projects').value;
    if (!projectId) return;
    localStorage.setItem(SAVED_PROJECTS_KEY, JSON.stringify(savedProjectRecords().filter(item => item.id !== projectId)));
    try { await removeProjectMedia(projectId); } catch (error) { console.warn('Could not remove saved media:', error); }
    if (activeProjectId === projectId) {
      activeProjectId = 'draft'; $('project-name').value = 'Untitled Reel';
      await persistProjectSnapshot(makeEditorSnapshot(), 'draft');
    }
    refreshSavedProjects();
  }

  function makeSavedDesign() {
    const fields = {};
    PROJECT_TEMPLATE_FIELDS.forEach(id => {
      const element = $(id);
      if (element) fields[id] = element.type === 'checkbox' ? element.checked : element.value;
    });
    return {version:1, fields, videoTemplate:selectedTemplateId, ratio, theme, captionColor, wrapWidth, speed};
  }

  function saveCustomDesign() {
    const name = $('custom-template-name').value.trim();
    if (!name) { $('custom-template-name').focus(); setProjectStatus('Name the design before saving it', true); return; }
    const records = customDesignRecords();
    const existing = records.find(item => item.name.toLowerCase() === name.toLowerCase());
    const item = {id:existing?.id || newLocalId('design'), name, updatedAt:Date.now(), design:makeSavedDesign()};
    const next = existing ? records.map(record => record.id === existing.id ? item : record) : [...records,item];
    try {
      localStorage.setItem(CUSTOM_DESIGNS_KEY, JSON.stringify(next.slice(-40)));
      $('custom-template-name').value = name;
      refreshCustomDesigns(item.id);
      setProjectStatus(existing ? 'Saved design updated' : 'Reusable design saved');
    } catch (_) { setProjectStatus('Browser storage is full; this design could not be saved', true); }
  }

  async function applyCustomDesign() {
    const item = customDesignRecords().find(record => record.id === $('custom-template-list').value);
    if (!item) return;
    const design = item.design;
    theme = document.querySelector(`.background-choice[data-theme="${design.theme}"]`) ? design.theme : theme;
    ratio = ['9:16','16:9','1:1'].includes(design.ratio) ? design.ratio : ratio;
    selectedTemplateId = videoTemplates[design.videoTemplate] ? design.videoTemplate : selectedTemplateId;
    captionColor = design.captionColor || captionColor;
    wrapWidth = Number(design.wrapWidth || 85); speed = Number(design.speed || 1);
    for (const [id,value] of Object.entries(design.fields || {})) {
      const element = $(id);
      if (!element) continue;
      if (element.type === 'checkbox' || element.type === 'radio') element.checked = Boolean(value);
      else element.value = value;
    }
    document.querySelectorAll('.aspect-ratio-btn').forEach(button => button.classList.toggle('selected-ratio', button.dataset.ratio === ratio));
    syncPreviewAspectRatio();
    document.querySelectorAll('.background-choice').forEach(button => button.classList.toggle('selected-background', button.dataset.theme === theme));
    document.querySelectorAll('.video-template-choice').forEach(button => button.classList.toggle('selected-video-template', button.dataset.templateId === selectedTemplateId));
    document.querySelectorAll('.caption-color-choice').forEach(button => button.classList.toggle('selected-caption-color', button.dataset.color === captionColor));
    $('custom-resolution-fields').classList.toggle('hidden', $('export-resolution').value !== 'custom');
    const crf = $('export-crf').value; updateQualityDescription(); $('export-crf').value = crf; $('export-crf-value').textContent = crf;
    $('speed-cycle-btn').textContent = `${speed.toFixed(2).replace(/0+$/,'').replace(/\.$/,'')}x`;
    $('speed-indicator').textContent = `${speed}x (${speed === 1 ? 'Natural' : 'Adjusted'})`;
    updateCanvasSummary(); setWallpaperPreview(); updateBackgroundAdjustments();
    updateBackgroundSequenceSelection(); playBackgroundSequenceTemplate(0);
    scenePlanManual = false;
    await updateScenePlan(); await updateCaptionPreview(); hideRenderedVideo();
    setProjectStatus(`Applied “${item.name}”`);
    scheduleProjectAutosave();
  }

  function deleteCustomDesign() {
    const id = $('custom-template-list').value;
    if (!id) return;
    localStorage.setItem(CUSTOM_DESIGNS_KEY, JSON.stringify(customDesignRecords().filter(item => item.id !== id)));
    refreshCustomDesigns(); setProjectStatus('Reusable design deleted');
  }

  function validateImportedDesign(design) {
    if (!design || design.version !== 1 || !design.fields || typeof design.fields !== 'object' || Array.isArray(design.fields)) {
      throw new Error('This file is not a supported Quran Reels visual template.');
    }
    if (!['9:16','16:9','1:1'].includes(design.ratio) ||
        !document.querySelector(`.background-choice[data-theme="${design.theme}"]`) ||
        !videoTemplates[design.videoTemplate]) throw new Error('The template uses an unsupported background, video design, or aspect ratio.');
    if (![65,75,85,95].includes(Number(design.wrapWidth)) || ![.9,1,1.15].includes(Number(design.speed))) {
      throw new Error('The template has an invalid text wrap width or recitation speed.');
    }
    const colors = [...document.querySelectorAll('.caption-color-choice')].map(button => button.dataset.color);
    if (!(colors.includes(design.captionColor) || /^#[\da-f]{6}$/i.test(design.captionColor || ''))) {
      throw new Error('The template has an unsupported Quran text color.');
    }
    for (const [id,value] of Object.entries(design.fields)) {
      if (!PROJECT_TEMPLATE_FIELDS.includes(id)) throw new Error(`The template contains an unsupported setting: ${id}.`);
      const element = $(id);
      if (!element) throw new Error(`The template refers to a missing editor control: ${id}.`);
      if (element.type === 'checkbox') {
        if (typeof value !== 'boolean') throw new Error(`The ${id} setting must be true or false.`);
      } else if (id === 'background-video-template') {
        if (value !== '' && !backgroundVideoTemplates[value]) throw new Error('The template uses an unavailable bundled video background.');
      } else if (element.type === 'color') {
        if (typeof value !== 'string' || !/^#[\da-f]{6}$/i.test(value)) throw new Error(`The ${id} setting must be a hex color.`);
      } else if (element.type === 'range' || element.type === 'number') {
        if (value === '' && !element.required) continue;
        const number = Number(value);
        if (!Number.isFinite(number) || (element.min !== '' && number < Number(element.min)) ||
            (element.max !== '' && number > Number(element.max))) throw new Error(`The ${id} setting is outside its allowed range.`);
      } else if (element.tagName === 'SELECT' && ![...element.options].some(option => option.value === String(value))) {
        throw new Error(`The template uses an unsupported ${id} option.`);
      }
    }
    return design;
  }

  function exportCustomDesign() {
    const item = customDesignRecords().find(record => record.id === $('custom-template-list').value);
    if (!item) return;
    const payload = {format:'quran-reels-custom-template',version:1,name:item.name,design:item.design};
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));
    const link = document.createElement('a');
    link.href = url; link.download = `${item.name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'') || 'quran-reels-template'}.json`;
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url),1000);
  }

  async function importCustomDesign(file) {
    if (!file) return;
    if (file.size > 256 * 1024) throw new Error('Template JSON files must be smaller than 256 KB.');
    let payload;
    try { payload = JSON.parse(await file.text()); }
    catch (_) { throw new Error('The selected template file is not valid JSON.'); }
    if (payload.format !== 'quran-reels-custom-template' || payload.version !== 1 ||
        typeof payload.name !== 'string' || !payload.name.trim() || payload.name.trim().length > 48) {
      throw new Error('The file must contain a named Quran Reels template in version 1 format.');
    }
    const design = validateImportedDesign(payload.design);
    const name = payload.name.trim();
    const records = customDesignRecords();
    const existing = records.find(item => item.name.toLowerCase() === name.toLowerCase());
    const item = {id:existing?.id || newLocalId('design'),name,updatedAt:Date.now(),design};
    const next = existing ? records.map(record => record.id === existing.id ? item : record) : [...records,item];
    localStorage.setItem(CUSTOM_DESIGNS_KEY,JSON.stringify(next.slice(-40)));
    $('custom-template-name').value = name;
    refreshCustomDesigns(item.id);
    setProjectStatus(`Imported “${name}”`);
  }

  function scheduleProjectAutosave() {
    if (historyApplying) return;
    setProjectStatus('Saving changes…');
    clearTimeout(autosaveTimer);
    autosaveTimer = setTimeout(() => {
      const snapshot = makeEditorSnapshot();
      const signature = snapshotSignature(snapshot);
      if (!undoHistory.length) undoHistory.push(snapshot);
      else if (signature !== snapshotSignature(undoHistory[undoHistory.length - 1])) {
        undoHistory.push(snapshot);
        if (undoHistory.length > 40) undoHistory.shift();
        redoHistory = [];
      }
      updateHistoryButtons();
      if (signature === lastPersistedSignature) return;
      autosaveQueue = autosaveQueue.then(async () => {
        const mediaSaved = await persistProjectSnapshot(snapshot, activeProjectId);
        lastPersistedSignature = signature;
        if (!mediaSaved) setProjectStatus('Settings saved; browser storage could not keep uploaded media', true);
      }).catch(error => setProjectStatus(`Autosave failed: ${error.message}`, true));
    }, 450);
  }

  async function undoProjectChange() {
    if (historyApplying || undoHistory.length < 2) return;
    redoHistory.push(undoHistory.pop());
    await applyProjectSnapshot(undoHistory[undoHistory.length - 1], activeProjectId);
    updateHistoryButtons();
    const snapshot = makeEditorSnapshot();
    await persistProjectSnapshot(snapshot, activeProjectId);
    lastPersistedSignature = snapshotSignature(snapshot);
  }

  async function redoProjectChange() {
    if (historyApplying || !redoHistory.length) return;
    undoHistory.push(redoHistory.pop());
    await applyProjectSnapshot(undoHistory[undoHistory.length - 1], activeProjectId);
    updateHistoryButtons();
    const snapshot = makeEditorSnapshot();
    await persistProjectSnapshot(snapshot, activeProjectId);
    lastPersistedSignature = snapshotSignature(snapshot);
  }

  async function initializeProjectWorkspace() {
    applyVideoTemplate(selectedTemplateId);
    refreshSavedProjects(); refreshCustomDesigns();
    const draft = safeReadStorage(PROJECT_DRAFT_KEY, null);
    if ([1, 2].includes(draft?.state?.version)) {
      activeProjectId = draft.projectId || 'draft';
      await applyProjectSnapshot(draft.state, activeProjectId);
    } else {
      setWallpaperPreview(); updateCaptionPreview().catch(showError); updateSurahInfo(); await loadVerses();
    }
    undoHistory = [makeEditorSnapshot()]; redoHistory = [];
    lastPersistedSignature = snapshotSignature(undoHistory[0]);
    refreshSavedProjects(activeProjectId); updateHistoryButtons();
    if (selectedReciter && reciterById.has(selectedReciter)) {
      const name = reciterById.get(selectedReciter).name;
      $('selected-reciter-name').textContent = name; updatePreviewReciterName(name);
    }
    const missingMedia = Boolean(draft?.state?.mediaClips?.length && backgroundClipRows.length === 0);
    setProjectStatus(missingMedia ? 'Project restored; re-select its custom background media' :
                     draft?.state ? 'Draft restored from this browser' : 'Autosaves in this browser', missingMedia);
  }
  function currentOutputSize() {
    if ($('export-resolution').value === 'custom') {
      return [Number($('custom-width').value), Number($('custom-height').value)];
    }
    const edge = {'480p':480,'720p':720,'1080p':1080,'1440p':1440,'4k':2160}[$('export-resolution').value] || 1080;
    if (ratio === '9:16') return [edge, Math.floor(edge * 16 / 9 / 2) * 2];
    if (ratio === '16:9') return [Math.floor(edge * 16 / 9 / 2) * 2, edge];
    return [edge, edge];
  }
  function updateCanvasSummary() {
    const [width, height] = currentOutputSize();
    const fps = Number($('export-fps').value || 30);
    const resolution = $('export-resolution').value;
    const label = resolution === 'custom' ? 'Custom' : resolution.toUpperCase();
    const summary = `${width} × ${height} (${ratio}) • ${fps} FPS`;
    $('canvas-resolution').textContent = `${summary} · ${label}`;
    $('generate-video-btn').querySelector('span:last-child').textContent = `Render ${label} Reel (${width}×${height})`;
    const pill = $('resolution-pill'); if (pill) pill.textContent = label;
    return [width, height];
  }
  function syncPreviewAspectRatio() {
    const mockup = $('reel-mockup');
    mockup.style.maxWidth = ratio === '16:9' ? '580px' : ratio === '1:1' ? '400px' : '340px';
    mockup.querySelector('.aspect-screen').style.aspectRatio = ratio.replace(':', ' / ');
  }
  window.addEventListener('resize', updateViewerLayerPreview, {passive:true});
  function updateQualityDescription() {
    const quality = $('export-quality').value;
    const profile = qualityProfiles[quality];
    $('export-crf').value = profile.crf;
    $('export-crf-value').textContent = profile.crf;
    $('export-quality-help').textContent = `${profile.label}: x264 ${profile.preset}, CRF ${profile.crf}. Lower CRF improves quality and increases file size; higher CRF reduces both quality and file size. The mode controls encoding speed.`;
  }
  async function updateEncoderCapabilities(refresh = false) {
    const select = $('export-encoder');
    const requestedEncoder = select.value;
    const options = {
      nvidia: select.querySelector('option[value="nvidia"]'),
      intel: select.querySelector('option[value="intel"]'),
    };
    const help = $('export-encoder-help');
    try {
      const response = await fetch(`/api/render-capabilities${refresh ? '?refresh=1' : ''}`);
      if (!response.ok) throw new Error('Could not check render capabilities.');
      const data = await response.json();
      const nvidia = data.encoders?.nvidia || {};
      const intel = data.encoders?.intel || {};
      const automatic = select.querySelector('option[value="auto"]');
      automatic.textContent = nvidia.available
        ? `Auto · ${nvidia.name || 'NVIDIA GPU'} first, CPU fallback`
        : 'Auto · Quadro T2000 first if available, CPU fallback';
      options.nvidia.disabled = !nvidia.available;
      options.nvidia.textContent = nvidia.available ? `NVIDIA · ${nvidia.name || 'NVENC'}` : 'NVIDIA · unavailable';
      options.intel.disabled = !intel.available;
      options.intel.textContent = intel.available ? `Internal GPU · ${intel.name || 'Quick Sync'}` : 'Internal GPU · unavailable';
      const unavailable = [
        !nvidia.available && `NVIDIA: ${nvidia.reason || 'driver or NVENC unavailable'}`,
        !intel.available && `Intel: ${intel.reason || 'driver or Quick Sync unavailable'}`,
      ].filter(Boolean);
      help.textContent = `${unavailable.join(' · ')}${nvidia.available ? ' Auto will try NVIDIA first, then use CPU x264 if encoding fails.' : ' Auto will use CPU x264 because NVIDIA is unavailable.'} Scene composition still runs on the CPU.`;
      if (['nvidia', 'intel'].includes(requestedEncoder) && data.encoders?.[requestedEncoder]?.available !== true) {
        const capability = data.encoders?.[requestedEncoder] || {};
        if (!refresh) select.value = 'auto';
        else throw new Error(`${capability.name || requestedEncoder} is unavailable: ${capability.reason || 'GPU encoder not detected.'}`);
      }
    } catch (error) {
      Object.values(options).forEach(option => { option.disabled = true; });
      options.nvidia.textContent = 'NVIDIA · unavailable';
      options.intel.textContent = 'Internal GPU · unavailable';
      help.textContent = refresh && error.message.includes('unavailable:')
        ? error.message : 'Could not check hardware encoder support. CPU x264 remains available.';
      if (refresh && requestedEncoder !== 'auto') throw error;
    }
  }
  function setPlaybackIcon(isPlaying) {
    $('playback-play-icon').classList.toggle('hidden', isPlaying);
    $('playback-pause-icon').classList.toggle('hidden', !isPlaying);
    $('playback-toggle').setAttribute('aria-label', isPlaying ? 'Pause preview' : 'Play preview');
    $('viewer-waveform').classList.toggle('is-playing', isPlaying);
  }
  const reciterById = new Map();

  function hideRenderedVideo() {
    const video = $('rendered-video');
    video.pause(); video.removeAttribute('src'); video.load(); video.classList.add('hidden');
  }

  function verseSelectionKey() {
    return `${surahSelect.value}:${startInput.value || '1'}:${endInput.value || startInput.value || '1'}`;
  }

  function activePlayer() {
    const video = $('rendered-video');
    return !video.classList.contains('hidden') && video.src ? video : $('voice-preview-audio');
  }

  function syncTimeline(player) {
    if (!player || !Number.isFinite(player.duration)) return;
    const scrubber = $('preview-scrubber');
    const isRecitation = player === $('voice-preview-audio') && previewTimings.length;
    const start = isRecitation ? previewTimings[0].start : 0;
    const end = isRecitation ? previewTimings[previewTimings.length - 1].end : player.duration;
    scrubber.min = start; scrubber.max = end;
    scrubber.value = Math.min(end, Math.max(start, player.currentTime));
    $('preview-time').textContent = `${formatTime(Math.max(0, player.currentTime - start))} / ${formatTime(end - start)}`;
    $('viewer-progress-fill').style.width = `${Math.max(0, Math.min(1, (player.currentTime - start) / Math.max(.001, end - start))) * 100}%`;
  }

  function setWallpaperPreview() {
    const preview = $('preview-background');
    const file = selectedBackgroundFiles[0];
    const sequencePreset = activeBackgroundSequencePreset();
    const sequenceScene = sequencePreset && $('sequence-enabled').checked && !backgroundClipRows.length
      ? sequencePreset.scenes[builtinSequenceIndex % sequencePreset.scenes.length] : null;
    const previewTheme = sequenceScene?.theme || theme;
    const option = document.querySelector(`.background-choice[data-theme="${previewTheme}"]`);
    const top = option?.dataset.top || '19,31,40';
    const bottom = option?.dataset.bottom || '55,85,75';
    preview.style.setProperty('--wallpaper-top', `rgb(${top})`);
    preview.style.setProperty('--wallpaper-bottom', `rgb(${bottom})`);
    const query = new URLSearchParams({ratio, fit:$('background-fit').value, v:'cinematic-1',
      x:$('background-crop-x').value, y:$('background-crop-y').value});
    $('preview-wallpaper').src = `/api/backgrounds/${encodeURIComponent(previewTheme)}/preview?${query}`;
    configureBackgroundFit();
    updateBackgroundAdjustments();
    updateBackgroundAnimationPreview();
    if (file && previewObjectUrls.length) return;
  }

  function playBackgroundSequenceTemplate(index = 0) {
    clearTimeout(builtinSequencePreviewTimer);
    const preset = activeBackgroundSequencePreset();
    if (!preset || !$('sequence-enabled').checked || backgroundClipRows.length) {
      setWallpaperPreview();
      return;
    }
    const scenes = preset.scenes;
    const sceneIndex = ((index % scenes.length) + scenes.length) % scenes.length;
    const scene = scenes[sceneIndex];
    const previousImage = $('preview-background-image-previous');
    const transitionOverlay = $('preview-transition-overlay');
    const previousUrl = $('preview-wallpaper').src;
    const hasPrevious = builtinSequenceIndex !== sceneIndex || index > 0;
    previousImage.classList.add('hidden'); previousImage.style.opacity = '0'; previousImage.removeAttribute('src');
    if (hasPrevious && $('transitions-enabled').checked && previousUrl) {
      previousImage.src = previousUrl; previousImage.classList.remove('hidden'); previousImage.style.opacity = '1';
    }
    builtinSequenceIndex = sceneIndex;
    setWallpaperPreview();
    const nextIndex = (sceneIndex + 1) % scenes.length;
    const nextScene = scenes[nextIndex];
    const transitionStyle = $('transitions-enabled').checked
      ? (nextScene.transition || preset.transition || 'cut') : 'cut';
    const transitionDuration = $('transitions-enabled').checked
      ? Number(nextScene.transition_duration ?? preset.transition_duration ?? .45) : 0;
    const overlapping = ['crossfade','dissolve','slide_left','slide_right','zoom'].includes(transitionStyle);
    if (hasPrevious && $('transitions-enabled').checked && transitionDuration > 0) {
      transitionOverlay.style.transitionDuration = `${transitionDuration}s`;
      if (transitionStyle === 'fade_black' || transitionStyle === 'fade_color') {
        transitionOverlay.style.backgroundColor = transitionStyle === 'fade_black' ? '#000000' : $('background-transition-color').value;
        transitionOverlay.style.opacity = '1';
        requestAnimationFrame(() => { transitionOverlay.style.opacity = '0'; });
      } else if (overlapping) {
        requestAnimationFrame(() => { previousImage.style.opacity = '0'; });
      }
      setTimeout(() => { previousImage.classList.add('hidden'); previousImage.removeAttribute('src'); }, transitionDuration * 1000 + 50);
    }
    const duration = Math.max(1, Number(scene.duration) || 7);
    const nextDuration = Math.max(1, Number(nextScene.duration) || 7);
    const lead = overlapping && $('transitions-enabled').checked
      ? Math.min(transitionDuration, duration * .4, nextDuration * .4) : 0;
    if (sceneIndex === scenes.length - 1 && !$('sequence-loop').checked) return;
    builtinSequencePreviewTimer = setTimeout(() => playBackgroundSequenceTemplate(nextIndex),
      Math.max(.05, duration - lead) * 1000);
  }

  function updateBackgroundAdjustments() {
    const brightness = Number($('background-brightness').value);
    const contrast = Number($('background-contrast').value);
    const saturation = Number($('background-saturation').value);
    const opacity = Number($('background-overlay-opacity').value);
    const color = $('background-overlay-color').value;
    const mediaFilter = `brightness(${brightness}) contrast(${contrast}) saturate(${saturation})`;
    ['preview-wallpaper','preview-background-image','preview-background-image-previous','preview-background-video','preview-background-video-previous'].forEach(id => { $(id).style.filter = mediaFilter; });
    $('preview-background-video-blur').style.filter = `${mediaFilter} blur(24px) brightness(.62)`;
    const overlay = $('preview-background-overlay');
    const channels = color.match(/[a-f\d]{2}/gi)?.map(channel => parseInt(channel, 16)) || [11,22,38];
    overlay.style.backgroundColor = `rgba(${channels.join(',')},${opacity})`;
    overlay.style.display = opacity > 0 ? 'block' : 'none';
    $('background-brightness-value').textContent = `${Math.round(brightness * 100)}%`;
    $('background-contrast-value').textContent = `${Math.round(contrast * 100)}%`;
    $('background-saturation-value').textContent = `${Math.round(saturation * 100)}%`;
    $('background-overlay-opacity-value').textContent = `${Math.round(opacity * 100)}%`;
  }

  function updateBackgroundAnimationPreview() {
    const direction = $('background-motion-direction').value;
    const directionPresets = {left_to_right:'slow_pan_left',right_to_left:'slow_pan_right',
      top_to_bottom:'slow_pan_top_to_bottom',bottom_to_top:'slow_pan_bottom_to_top'};
    const enabled = direction === 'static' ? false
      : direction !== 'preset' ? true : $('background-animation-enabled').checked;
    const atmosphereEnabled = $('background-atmosphere-enabled').checked;
    const presetId = directionPresets[direction] || (direction === 'static' ? 'static' : $('background-animation-preset').value);
    const preset = imageAnimationPresets[presetId] || imageAnimationPresets.static;
    const intensity = Number($('background-animation-intensity').value);
    const duration = Math.max(1, Number($('background-animation-duration').value) || 12);
    const speedValue = Number($('background-animation-speed').value) || 1;
    const startDelay = Math.max(0, Number($('background-animation-start').value) || 0);
    const atmosphereIntensity = Number($('background-atmosphere-intensity').value);
    const atmosphereDuration = Math.max(8, Number($('background-atmosphere-duration').value) || 36);
    const atmosphereSpeed = Number($('background-atmosphere-speed').value) || .7;
    const atmosphereStart = Math.max(0, Number($('background-atmosphere-start').value) || 0);
    const atmosphereOverlay = $('preview-atmosphere-overlay');
    $('background-animation-intensity-label').textContent = `${Math.round(intensity * 100)}%`;
    $('background-animation-speed-label').textContent = `${speedValue.toFixed(2)}×`;
    $('background-atmosphere-intensity-label').textContent = `${Math.round(atmosphereIntensity * 100)}%`;
    $('background-atmosphere-speed-label').textContent = `${atmosphereSpeed.toFixed(2)}×`;
    atmosphereOverlay.style.opacity = atmosphereEnabled ? String(Math.min(.9, atmosphereIntensity)) : '0';
    for (const id of ['preview-wallpaper','preview-background-image','preview-background-video']) $(id).style.transform = 'none';
    if (animationPreviewFrame) cancelAnimationFrame(animationPreviewFrame);
    if ((!enabled || presetId === 'static' || intensity <= 0) && !atmosphereEnabled) return;
    animationPreviewStartedAt = performance.now();
    const draw = now => {
      const elapsed = (now - animationPreviewStartedAt) / 1000;
      if (enabled && presetId !== 'static' && intensity > 0) {
        const cycle = elapsed < startDelay ? 0 : ((elapsed - startDelay) * speedValue / duration) % 1;
        const phase = (1 - Math.cos(2 * Math.PI * cycle)) / 2;
        const zoom = 1 + (preset.zoom[0] - 1 + (preset.zoom[1] - preset.zoom[0]) * phase) * intensity;
        const cropX = preset.pan_x[0] + (preset.pan_x[1] - preset.pan_x[0]) * phase;
        const cropY = preset.pan_y[0] + (preset.pan_y[1] - preset.pan_y[0]) * phase;
        const transform = `translate3d(${((.5 - cropX) * (zoom - 1) * 100).toFixed(3)}%,${((.5 - cropY) * (zoom - 1) * 100).toFixed(3)}%,0) scale(${zoom.toFixed(4)})`;
        for (const id of ['preview-wallpaper','preview-background-image','preview-background-video']) $(id).style.transform = transform;
      }
      if (atmosphereEnabled && atmosphereIntensity > 0) {
        const cycle = elapsed < atmosphereStart ? 0 : ((elapsed - atmosphereStart) * atmosphereSpeed / atmosphereDuration) % 1;
        const phase = (1 - Math.cos(2 * Math.PI * cycle)) / 2;
        atmosphereOverlay.style.backgroundPosition = `${20 + phase * 58}% ${12 + phase * 48}%`;
      }
      animationPreviewFrame = requestAnimationFrame(draw);
    };
    animationPreviewFrame = requestAnimationFrame(draw);
  }

  function scheduleWallpaperPreview() {
    configureBackgroundFit();
    clearTimeout(backgroundPreviewTimer);
    backgroundPreviewTimer = setTimeout(setWallpaperPreview, 100);
  }

  function configureBackgroundFit() {
    const preview = $('preview-background'), fit = $('background-fit').value;
    ['cover','contain','stretch','blurred'].forEach(mode => preview.classList.toggle(`background-${mode}`, fit === mode));
    const position = `${Number($('background-crop-x').value)*100}% ${Number($('background-crop-y').value)*100}%`;
    $('preview-wallpaper').style.objectPosition = position;
    $('preview-background-image').style.objectPosition = position;
    $('preview-background-image-previous').style.objectPosition = position;
    $('preview-background-video').style.objectPosition = position;
    $('preview-background-video-previous').style.objectPosition = position;
    $('preview-background-blur').style.backgroundImage = currentBackgroundKind === 'image' && previewObjectUrls[0]
      ? `url("${previewObjectUrls[0]}")` : 'none';
    const video = $('preview-background-video'), blurVideo = $('preview-background-video-blur');
    const showVideo = currentBackgroundKind === 'video' &&
      (Boolean(previewObjectUrls.length) || Boolean(selectedBackgroundVideoTemplate));
    video.classList.toggle('hidden', !showVideo);
    blurVideo.classList.toggle('hidden', !showVideo || fit !== 'blurred');
    if (showVideo) {
      video.loop = Boolean(selectedBackgroundVideoTemplate) || (!$('sequence-enabled').checked && $('background-loop').checked);
      video.playbackRate = Number(backgroundClipRows[previewClipIndex]?.speed || $('background-speed').value);
      blurVideo.loop = true; blurVideo.playbackRate = video.playbackRate;
      video.play().catch(() => {}); if (fit === 'blurred') blurVideo.play().catch(() => {});
    }
  }

  function clearCustomBackgroundPreview(clearSelection = true) {
    previewObjectUrls.forEach(url => URL.revokeObjectURL(url));
    previewObjectUrls = []; currentBackgroundKind = null;
    if (clearSelection) {
      selectedBackgroundFiles = [];
      backgroundClipRows = [];
      selectedBackgroundVideoTemplate = '';
      $('background-video-template').value = '';
      document.querySelectorAll('.background-video-choice').forEach(button => {
        button.classList.remove('selected-background-video');
        button.setAttribute('aria-pressed', 'false');
      });
      renderBackgroundClipList();
    }
    const image = $('preview-background-image'); image.removeAttribute('src'); image.classList.add('hidden');
    $('preview-background-image-previous').removeAttribute('src'); $('preview-background-image-previous').classList.add('hidden');
    ['preview-background-video','preview-background-video-blur','preview-background-video-previous'].forEach(id => {
      const video = $(id); video.pause(); video.onended = null; video.ontimeupdate = null;
      video.removeAttribute('src'); video.load(); video.classList.add('hidden');
    });
    $('preview-background').classList.remove('has-custom-background');
    $('preview-background-blur').style.backgroundImage = 'none';
    clearTimeout(sequencePreviewTimer);
    clearTimeout(sequencePreviewFadeTimer);
    clearTimeout(sequencePreviewCleanupTimer);
    clearTimeout(builtinSequencePreviewTimer);
    const transitionOverlay = $('preview-transition-overlay'); transitionOverlay.style.opacity = '0'; transitionOverlay.style.backgroundColor = '#000';
    updateBackgroundAnimationPreview();
  }

  function renderUploadedBackgroundPreview(files) {
    selectedBackgroundVideoTemplate = '';
    $('background-video-template').value = '';
    document.querySelectorAll('.background-video-choice').forEach(button => {
      button.classList.remove('selected-background-video');
      button.setAttribute('aria-pressed', 'false');
    });
    $('background-sequence-template').value = '';
    updateBackgroundSequenceSelection();
    clearTimeout(builtinSequencePreviewTimer);
    const rows = [...files].map(item => item.file ? item : ({
      file:item, start:0, end:null, speed:Number($('background-speed').value),
      transition:$('default-background-transition').value || 'crossfade',
      transition_duration:Number($('background-transition-duration').value) || .45,
      duration:item.type.startsWith('image/') ? 4 : null,
    }));
    clearCustomBackgroundPreview(false);
    backgroundClipRows = rows;
    selectedBackgroundFiles = rows.map(row => row.file);
    previewObjectUrls = selectedBackgroundFiles.map(file => URL.createObjectURL(file));
    previewClipIndex = 0;
    renderBackgroundClipList();
    const preview = $('preview-background');
    preview.classList.add('has-custom-background');
    playPreviewSequenceItem(0);
    setWallpaperPreview();
    selectedBackgroundFiles.forEach((file, index) => {
      if (!file.type.startsWith('video/')) return;
      const probe = document.createElement('video');
      probe.preload = 'metadata'; probe.src = previewObjectUrls[index];
      probe.onloadedmetadata = () => {
        const row = backgroundClipRows.find(item => item.file === file);
        if (row) { row.duration = probe.duration; if (row.end === null) row.end = probe.duration; renderBackgroundClipList(); }
        probe.removeAttribute('src'); probe.load();
      };
    });
  }

  function selectBackgroundVideoTemplate(templateId, {save = true} = {}) {
    const button = document.querySelector(`.background-video-choice[data-video-template="${templateId}"]`);
    const preset = backgroundVideoTemplates[templateId];
    if (!button || !preset) return false;
    clearCustomBackgroundPreview();
    selectedBackgroundVideoTemplate = templateId;
    $('background-video-template').value = templateId;
    $('background-sequence-template').value = '';
    $('sequence-enabled').checked = false;
    updateBackgroundSequenceSelection();
    $('background-file').value = '';
    $('background-file-name').textContent = `${preset.name} · silent looping video`;
    $('background-video-selection').textContent = `${preset.name} selected · source audio muted`;
    document.querySelectorAll('.background-video-choice').forEach(item => {
      const selected = item.dataset.videoTemplate === templateId;
      item.classList.toggle('selected-background-video', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    currentBackgroundKind = 'video';
    $('preview-background').classList.add('has-custom-background');
    const src = button.dataset.videoSrc;
    for (const id of ['preview-background-video','preview-background-video-blur']) {
      const video = $(id);
      video.muted = true; video.loop = true; video.playsInline = true;
      video.src = src; video.classList.remove('hidden'); video.style.opacity = '1';
      video.load(); video.play().catch(() => {});
    }
    $('preview-background-image').classList.add('hidden');
    configureBackgroundFit();
    updateBackgroundAdjustments();
    updateBackgroundAnimationPreview();
    hideRenderedVideo();
    if (save) scheduleProjectAutosave();
    return true;
  }

  function playPreviewClip(index) {
    if (!backgroundClipRows.length || !previewObjectUrls.length) return;
    const video = $('preview-background-video'), blurVideo = $('preview-background-video-blur');
    const row = backgroundClipRows[index];
    if (!row) return;
    previewClipIndex = index; previewClipAdvancing = false;
    currentBackgroundKind = 'video';
    const begin = element => {
      element.src = previewObjectUrls[index]; element.loop = false;
      element.classList.remove('hidden'); element.style.opacity = '0';
      element.playbackRate = Number(row.speed || 1); element.load();
      element.onloadedmetadata = () => {
        element.currentTime = Math.min(Number(row.start || 0), Math.max(0, element.duration - .05));
        requestAnimationFrame(() => { element.style.opacity = '1'; });
        element.play().catch(() => {});
      };
    };
    begin(video); begin(blurVideo);
    const next = () => {
      if (previewClipAdvancing) return;
      previewClipAdvancing = true;
      const nextIndex = index + 1;
      if ($('sequence-enabled').checked && nextIndex < backgroundClipRows.length) playPreviewSequenceItem(nextIndex);
      else if ($('sequence-enabled').checked && $('sequence-loop').checked) playPreviewSequenceItem(0);
      else if (!$('sequence-enabled').checked && $('background-loop').checked) playPreviewClip(index);
      else { video.pause(); blurVideo.pause(); }
    };
    video.ontimeupdate = () => {
      const end = Number(row.end ?? row.duration);
      const speed = Math.max(.5, Number(row.speed || 1));
      const lead = sequenceTransitionLead(index) * speed;
      if (Number.isFinite(end) && end > 0 && video.currentTime >= end - lead - .04) next();
    };
    video.onended = next;
    blurVideo.onended = null; blurVideo.ontimeupdate = null;
  }

  function playPreviewSequenceItem(index) {
    if (!backgroundClipRows.length || !previewObjectUrls.length) return;
    clearTimeout(sequencePreviewTimer);
    if (!$('sequence-enabled').checked) index = 0;
    const row = backgroundClipRows[index];
    if (!row) return;
    clearTimeout(sequencePreviewFadeTimer);
    const image = $('preview-background-image');
    const video = $('preview-background-video');
    const blurVideo = $('preview-background-video-blur');
    const previousImage = $('preview-background-image-previous');
    const previousVideo = $('preview-background-video-previous');
    const transitionOverlay = $('preview-transition-overlay');
    const previousKind = currentBackgroundKind;
    const isChangingScene = previousKind && previewClipIndex !== index;
    const transitionEnabled = $('sequence-enabled').checked && $('transitions-enabled').checked && isChangingScene;
    const transitionStyle = transitionEnabled ? (row.transition || $('default-background-transition').value) : 'cut';
    const transitionDuration = transitionEnabled ? Math.max(0, Math.min(2, Number(row.transition_duration ?? .45) || 0)) : 0;
    const overlapStyles = new Set(['crossfade','dissolve','slide_left','slide_right','zoom']);
    const useTransition = transitionStyle !== 'cut' && transitionDuration > 0;

    clearTimeout(sequencePreviewCleanupTimer);
    previousImage.classList.add('hidden'); previousImage.style.opacity = '0'; previousImage.removeAttribute('src');
    previousVideo.pause(); previousVideo.classList.add('hidden'); previousVideo.style.opacity = '0';
    previousVideo.removeAttribute('src'); previousVideo.load();
    transitionOverlay.style.transitionDuration = `${transitionDuration}s`;
    transitionOverlay.style.opacity = '0';

    let previousLayer = null;
    if (useTransition && previousKind === 'image' && image.getAttribute('src')) {
      previousImage.src = image.src; previousImage.classList.remove('hidden'); previousImage.style.opacity = '1';
      previousLayer = previousImage;
    } else if (useTransition && previousKind === 'video' && video.currentSrc) {
      const previousTime = video.currentTime;
      previousVideo.src = video.currentSrc; previousVideo.playbackRate = video.playbackRate;
      previousVideo.classList.remove('hidden'); previousVideo.style.opacity = '1';
      previousVideo.onloadedmetadata = () => {
        previousVideo.currentTime = Math.min(previousTime, Math.max(0, previousVideo.duration - .05));
        previousVideo.play().catch(() => {});
      };
      previousVideo.load(); previousLayer = previousVideo;
    }
    if (!previousLayer) {
      transitionOverlay.style.transitionDuration = '0s';
    } else if (transitionStyle === 'fade_black' || transitionStyle === 'fade_color') {
      transitionOverlay.style.backgroundColor = transitionStyle === 'fade_black' ? '#000000' : $('background-transition-color').value;
      transitionOverlay.style.opacity = '1';
    }
    previewClipIndex = index;

    const beginIncoming = element => {
      element.style.transitionDuration = `${transitionDuration}s`;
      element.style.transitionProperty = 'opacity, transform';
      element.style.opacity = useTransition && overlapStyles.has(transitionStyle) ? '0' : '1';
      element.style.transform = transitionStyle === 'slide_left' ? 'translate3d(-100%,0,0)'
        : transitionStyle === 'slide_right' ? 'translate3d(100%,0,0)'
        : transitionStyle === 'zoom' ? 'scale(1.1)' : 'none';
      requestAnimationFrame(() => {
        element.style.opacity = '1'; element.style.transform = 'none';
        if (previousLayer) previousLayer.style.opacity = '0';
        if (transitionStyle === 'fade_black' || transitionStyle === 'fade_color') transitionOverlay.style.opacity = '0';
      });
      if (useTransition && previousLayer) {
        sequencePreviewCleanupTimer = setTimeout(() => {
          previousLayer.classList.add('hidden'); previousLayer.style.opacity = '0';
          if (previousLayer === previousImage) previousImage.removeAttribute('src');
          if (previousLayer === previousVideo) { previousVideo.pause(); previousVideo.removeAttribute('src'); previousVideo.load(); }
          transitionOverlay.style.transitionDuration = '0s'; transitionOverlay.style.opacity = '0';
        }, transitionDuration * 1000 + 50);
      }
    };
    const advance = () => {
      if (!$('sequence-enabled').checked) return;
      const next = index + 1;
      if (next < backgroundClipRows.length) playPreviewSequenceItem(next);
      else if ($('sequence-loop').checked) playPreviewSequenceItem(0);
    };
    if (row.file.type.startsWith('video/')) {
      currentBackgroundKind = 'video';
      image.style.opacity = '0';
      video.style.opacity = '0';
      video.style.transform = transitionStyle === 'slide_left' ? 'translate3d(-100%,0,0)'
        : transitionStyle === 'slide_right' ? 'translate3d(100%,0,0)'
        : transitionStyle === 'zoom' ? 'scale(1.1)' : 'none';
      video.style.transitionDuration = `${transitionDuration}s`;
      playPreviewClip(index);
      const loaded = video.onloadedmetadata;
      video.onloadedmetadata = () => { if (loaded) loaded(); beginIncoming(video); };
      if ($('sequence-enabled').checked) {
        video.onended = advance;
      }
      return;
    }
    currentBackgroundKind = 'image';
    video.pause(); blurVideo.pause();
    video.style.opacity = '0';
    video.style.transform = 'none';
    image.src = previewObjectUrls[index];
    image.classList.remove('hidden');
    beginIncoming(image);
    updateBackgroundAnimationPreview();
    if ($('sequence-enabled').checked) {
      const duration = Math.max(1, Number(row.duration) || 4);
      const lead = sequenceTransitionLead(index);
      const nextRow = backgroundClipRows[(index + 1) % backgroundClipRows.length];
      const nextTransition = $('transitions-enabled').checked && nextRow
        ? nextRow.transition || $('default-background-transition').value : 'cut';
      if ($('transitions-enabled').checked && ['fade_black','fade_color'].includes(nextTransition) && $('sequence-loop').checked ||
          $('transitions-enabled').checked && ['fade_black','fade_color'].includes(nextTransition) && index + 1 < backgroundClipRows.length) {
        const fadeDuration = Math.min(Number(nextRow.transition_duration ?? .45) || 0, duration * .35);
        sequencePreviewFadeTimer = setTimeout(() => {
          const overlay = $('preview-transition-overlay');
          overlay.style.backgroundColor = nextTransition === 'fade_black' ? '#000000' : $('background-transition-color').value;
          overlay.style.transitionDuration = `${fadeDuration}s`; overlay.style.opacity = '0';
          requestAnimationFrame(() => { overlay.style.opacity = '1'; });
        }, Math.max(0, duration - fadeDuration) * 1000);
      }
      sequencePreviewTimer = setTimeout(advance, Math.max(.05, duration - lead) * 1000);
    }
  }

  function selectedBackgroundDuration(row) {
    if (!row) return 0;
    if (row.file?.type?.startsWith('video/')) {
      const end = Number(row.end ?? row.duration);
      return Math.max(0, end - Number(row.start || 0)) / Math.max(.5, Number(row.speed || 1));
    }
    return Math.max(0, Number(row.duration) || 4);
  }

  function sequenceTransitionLead(index) {
    if (!$('sequence-enabled').checked || !$('transitions-enabled').checked || backgroundClipRows.length < 2) return 0;
    const nextIndex = index + 1 < backgroundClipRows.length ? index + 1 : $('sequence-loop').checked ? 0 : -1;
    if (nextIndex < 0) return 0;
    const incoming = backgroundClipRows[nextIndex];
    if (!['crossfade','dissolve','slide_left','slide_right','zoom'].includes(incoming.transition || 'cut')) return 0;
    return Math.min(Number(incoming.transition_duration ?? .45) || 0,
      selectedBackgroundDuration(backgroundClipRows[index]) * .4,
      selectedBackgroundDuration(incoming) * .4);
  }

  function refreshSequencePreview(index) {
    if ($('sequence-enabled').checked && previewClipIndex === index) playPreviewSequenceItem(index);
  }

  function renderBackgroundClipList() {
    const container = $('background-clip-list');
    if (!container) return;
    container.replaceChildren();
    if (!backgroundClipRows.length) return;
    backgroundClipRows.forEach((row, index) => {
      const card = document.createElement('div'); card.className = 'background-clip-card';
      const head = document.createElement('div'); head.className = 'background-clip-head';
      const title = document.createElement('strong'); title.textContent = `${index + 1}. ${row.file.name}`;
      const tools = document.createElement('div'); tools.className = 'background-clip-actions';
      const action = (label, icon, callback, disabled = false) => {
        const button = document.createElement('button'); button.type = 'button'; button.title = label;
        button.setAttribute('aria-label', label); button.disabled = disabled;
        button.innerHTML = `<span class="material-symbols-outlined" aria-hidden="true">${icon}</span>`;
        button.addEventListener('click', callback); tools.append(button);
      };
      action('Replace media','sync',() => {
        const input=document.createElement('input'); input.type='file';
        input.accept='image/png,image/jpeg,image/webp,video/mp4,video/quicktime,video/webm,video/x-m4v';
        input.addEventListener('change',()=>{
          const file=input.files?.[0]; if(!file) return;
          row.file=file; row.start=0; row.end=null; row.speed=Number($('background-speed').value);
          row.duration=file.type.startsWith('image/')?4:null;
          renderUploadedBackgroundPreview(backgroundClipRows); hideRenderedVideo();
        }); input.click();
      });
      action('Move media up','arrow_upward',() => { if (!index) return; [backgroundClipRows[index-1],backgroundClipRows[index]]=[backgroundClipRows[index],backgroundClipRows[index-1]]; renderUploadedBackgroundPreview(backgroundClipRows); }, index===0);
      action('Move media down','arrow_downward',() => { if (index>=backgroundClipRows.length-1) return; [backgroundClipRows[index+1],backgroundClipRows[index]]=[backgroundClipRows[index],backgroundClipRows[index+1]]; renderUploadedBackgroundPreview(backgroundClipRows); }, index===backgroundClipRows.length-1);
      action('Duplicate clip','content_copy',() => { backgroundClipRows.splice(index+1,0,{...row}); renderUploadedBackgroundPreview(backgroundClipRows); });
      action('Remove media','delete',() => { backgroundClipRows.splice(index,1); renderUploadedBackgroundPreview(backgroundClipRows); if (!backgroundClipRows.length) { $('background-file').value=''; clearCustomBackgroundPreview(); } });
      head.append(title,tools); card.append(head);
      if (row.file.type.startsWith('video/')) {
        const info = document.createElement('p'); info.className='background-clip-duration';
        info.textContent = row.duration ? `Media ${row.duration.toFixed(1)} s · selected ${(Number(row.end||row.duration)-Number(row.start||0)).toFixed(1)} s` : 'Reading video duration…';
        card.append(info);
        const controls=document.createElement('div'); controls.className='background-clip-controls';
        const field=(label,type,value,min,max,step,change)=>{ const wrap=document.createElement('label'); wrap.textContent=label; const input=document.createElement('input'); input.type=type; input.value=value ?? ''; if(min!==null) input.min=min; if(max!==null) input.max=max; if(step) input.step=step; input.addEventListener('change',()=>{change(input.value); const text=card.querySelector('.background-clip-duration'); if(row.duration) text.textContent=`Media ${row.duration.toFixed(1)} s · selected ${(Number(row.end||row.duration)-Number(row.start||0)).toFixed(1)} s`; hideRenderedVideo(); refreshSequencePreview(index);}); wrap.append(input); controls.append(wrap); return input; };
        field('Trim in (s)','number',row.start,0,row.duration||null,.1,value=>row.start=Number(value));
        field('Trim out (s)','number',row.end,0,row.duration||null,.1,value=>row.end=Number(value));
        const select=(label,value,options,change)=>{const wrap=document.createElement('label');wrap.textContent=label;const input=document.createElement('select');options.forEach(([key,text])=>{const option=document.createElement('option');option.value=key;option.textContent=text;input.append(option);});input.value=value;input.addEventListener('change',()=>{change(input.value);hideRenderedVideo();refreshSequencePreview(index);});wrap.append(input);controls.append(wrap);};
        select('Speed',String(row.speed),[['0.5','0.5×'],['0.75','0.75×'],['1','1×'],['1.25','1.25×'],['1.5','1.5×'],['2','2×']],value=>row.speed=Number(value));
      } else {
        const info=document.createElement('p'); info.className='background-clip-duration'; info.textContent='Still image · configured duration'; card.append(info);
        const controls=document.createElement('div'); controls.className='background-clip-controls';
        const field=(label,type,value,min,max,step,change)=>{ const wrap=document.createElement('label'); wrap.textContent=label; const input=document.createElement('input'); input.type=type; input.value=value ?? ''; if(min!==null) input.min=min; if(max!==null) input.max=max; if(step) input.step=step; input.addEventListener('change',()=>{change(input.value);hideRenderedVideo();}); wrap.append(input); controls.append(wrap); return input; };
        field('Duration (s)','number',row.duration||4,1,300,.5,value=>row.duration=Number(value));
        const durationInput = controls.querySelector('input[type="number"]');
        durationInput?.addEventListener('change', () => refreshSequencePreview(index));
        card.append(controls);
      }
      const transitionControls=document.createElement('div'); transitionControls.className='background-clip-controls';
      const transitionLabel=document.createElement('label'); transitionLabel.textContent='Transition in';
      const transitionSelect=document.createElement('select');
      [['cut','Hard cut'],['crossfade','Crossfade'],['dissolve','Dissolve'],['fade_black','Fade through black'],['fade_color','Fade through color'],['slide_left','Slide left'],['slide_right','Slide right'],['zoom','Gentle zoom']]
        .forEach(([value,label])=>{const option=document.createElement('option');option.value=value;option.textContent=label;transitionSelect.append(option);});
      transitionSelect.value=row.transition||$('default-background-transition').value;
      transitionSelect.disabled=!$('transitions-enabled').checked;
      transitionSelect.addEventListener('change',()=>{row.transition=transitionSelect.value;hideRenderedVideo();});
      transitionLabel.append(transitionSelect); transitionControls.append(transitionLabel);
      const durationWrap=document.createElement('label');durationWrap.textContent='Blend (s)';
      const durationInput=document.createElement('input');durationInput.type='number';durationInput.min='0';durationInput.max='2';durationInput.step='.05';durationInput.value=row.transition_duration??.45;
      durationInput.disabled=!$('transitions-enabled').checked;
      durationInput.addEventListener('change',()=>{row.transition_duration=Number(durationInput.value);hideRenderedVideo();});
      durationWrap.append(durationInput);transitionControls.append(durationWrap);card.append(transitionControls);
      container.append(card);
    });
  }

  let captionPreviewRequest = 0, captionPreviewObjectUrl = null;
  async function updateCaptionPreview() {
    const caption = $('preview-ayah-text');
    if (!$('show-quran-text').checked) {
      caption.style.display = 'none';
      updateViewerLayerPreview();
      return;
    }
    const lines = ayahText.value.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
    const activeScene = previewScenes[previewIndex];
    const text = activeScene?.text || lines[0] || previewAyahs[0] || '';
    if (!text) return;
    const requestId = ++captionPreviewRequest;
    const response = await fetch('/api/caption-preview', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({text, aspect_ratio:ratio, caption_style:$('caption-style').value,
                            caption_color:captionColor, wrap_width:wrapWidth,
                            template_id:selectedTemplateId, surah:Number(surahSelect.value),
                            ayah:activeScene?.ayah_number || Number(startInput.value || 1),
                            font_id:$('arabic-font').value,
                            show_surah_title:$('show-surah-title').checked,
                            show_ayah_number:$('show-ayah-number').checked,
                            surah_template:$('surah-name-template').value,
                            ayah_number_template:$('ayah-number-template').value,
                            surah_color:$('surah-color').value, ayah_color:$('ayah-color').value,
                            surah_scale:Number($('surah-scale').value),
                            ayah_number_scale:Number($('ayah-number-scale').value),
                            surah_align:$('surah-align').value,
                            ayah_number_align:$('ayah-number-align').value,
                            surah_font_id:$('surah-font-id').value,
                            ayah_number_font_id:$('ayah-number-font-id').value,
                            surah_opacity:Number($('surah-opacity').value),
                            ayah_number_opacity:Number($('ayah-number-opacity').value),
                            surah_placement:$('surah-placement').value,
                            ayah_number_placement:$('ayah-number-placement').value,
                            caption_position:$('caption-position').value,
                            translation:activeTranslationText(),
                            text_bg_enabled:$('text-bg-enabled').checked,
                            text_bg_color:$('text-bg-color').value,
                            text_bg_opacity:Number($('text-bg-opacity').value),
                            glow_type:$('glow-type').value,
                            glow_radius:Number($('glow-radius').value),
                            resolution:$('export-resolution').value,
                            custom_width:$('custom-width').value, custom_height:$('custom-height').value})
    });
    if (!response.ok) return;
    const imageUrl = URL.createObjectURL(await response.blob());
    if (requestId !== captionPreviewRequest) { URL.revokeObjectURL(imageUrl); return; }
    const previousUrl = captionPreviewObjectUrl;
    captionPreviewObjectUrl = imageUrl;
    caption.onload = () => {
      if (requestId !== captionPreviewRequest) return;
      const frame = $('preview-background').parentElement;
      const frameBox = frame.getBoundingClientRect();
      const sourceSize = currentOutputSize();
      const scale = frameBox.width / sourceSize[0];
      const outputHeight = sourceSize[1], captionHeight = caption.naturalHeight;
      const hasTranslation = Boolean(activeTranslationText());
      const anchor = {'upper':.34,'center':hasTranslation ? .43 : .54,'lower':.72}[$('caption-position').value] || .54;
      const y = Math.max(Math.trunc(outputHeight*.12),
        Math.min(Math.trunc(outputHeight*anchor-captionHeight/2), outputHeight-captionHeight-Math.trunc(outputHeight*.12)));
      caption.style.width = `${caption.naturalWidth*scale}px`;
      caption.style.top = `${y*scale}px`;
      caption.style.display = 'block';
      if (hasTranslation) {
        const translation = $('viewer-translation');
        const captionBottom = y*scale + captionHeight*scale;
        translation.style.top = `${Math.min(.665, Math.max(.60, captionBottom/frameBox.height + .018))*100}%`;
      }
      updateViewerLayerPreview();
      if (previousUrl) URL.revokeObjectURL(previousUrl);
    };
    caption.src = imageUrl;
  }

  function scenePayload() {
    return {
      ayahs: ayahText.value.split(/\r?\n/).map(line => line.trim()).filter(Boolean),
      ayah_start: Number(startInput.value || 1), aspect_ratio: ratio, wrap_width: wrapWidth,
      resolution: $('export-resolution').value,
      custom_width: $('custom-width').value, custom_height: $('custom-height').value,
      max_lines: Number($('max-lines').value), font_id: $('arabic-font').value,
      template_id: selectedTemplateId,
      show_surah_title: $('show-surah-title').checked,
      show_ayah_number: $('show-ayah-number').checked,
    };
  }

  function refreshSceneLabels() {
    const totals = new Map();
    const groups = new Map();
    previewScenes.forEach(scene => totals.set(scene.ayah_number, (totals.get(scene.ayah_number) || 0) + 1));
    const seen = new Map();
    previewScenes.forEach((scene, index) => {
      scene.scene_index = index;
      scene.segment_index = (seen.get(scene.ayah_number) || 0) + 1;
      seen.set(scene.ayah_number, scene.segment_index);
      scene.segment_count = totals.get(scene.ayah_number);
      scene.weight = Math.max(1, [...scene.text].filter(char => !/\s/.test(char) && !/[\u0300-\u036f\u064b-\u065f\u0670\u06d6-\u06ed]/u.test(char)).length);
      if (!groups.has(scene.ayah_number)) groups.set(scene.ayah_number, []);
      groups.get(scene.ayah_number).push(scene);
    });
    for (const group of groups.values()) {
      const verseDuration = Number(group[0].ayah_total_duration) || group.reduce((sum, scene) => sum + Number(scene.duration || 0), 0) || 3;
      const fractionsTotal = group.reduce((sum, scene) => sum + Number(scene.duration_fraction || 0), 0);
      const hasValidFractions = group.every(scene => scene.manual_duration_fraction && Number(scene.duration_fraction) > 0)
        && Math.abs(fractionsTotal - 1) < .005;
      if (group.length === 1) {
        group[0].duration_fraction = 1;
        group[0].duration = verseDuration;
        group[0].timing_mode ||= 'ayah_timestamp';
      } else if (hasValidFractions) {
        group.forEach(scene => {
          scene.ayah_total_duration = verseDuration;
          scene.duration = verseDuration * scene.duration_fraction;
          scene.timing_mode = 'manual_fraction_estimate';
        });
      } else {
        group.forEach(scene => {
          scene.ayah_total_duration = verseDuration;
          scene.duration_fraction = null;
          scene.duration = 0;
          scene.timing_mode = 'untimed_manual_phrase';
          scene.manual_duration_fraction = false;
        });
      }
    }
    let cursor = 0;
    previewScenes.forEach(scene => {
      scene.start_time = cursor;
      cursor += Number(scene.duration || 0);
      scene.end_time = cursor;
    });
  }

  function renderSceneTimeline(approximate = previewScenes.some(scene => scene.segment_count > 1)) {
    const list = $('scene-timeline');
    list.replaceChildren();
    if (!previewScenes.length) {
      $('scene-summary').textContent = 'No scenes planned';
      return;
    }
    previewScenes.forEach((scene, index) => {
      const row = document.createElement('div');
      row.className = `scene-row${index === previewIndex ? ' active-scene' : ''}`;
      const select = document.createElement('button');
      select.type = 'button';
      select.className = 'scene-select';
      select.setAttribute('aria-label', `Preview Ayah ${scene.ayah_number}, scene ${scene.segment_index} of ${scene.segment_count}`);
      const heading = document.createElement('strong');
      heading.textContent = `Ayah ${scene.ayah_number}${scene.segment_count > 1 ? ` · Part ${scene.segment_index}/${scene.segment_count}` : ''}`;
      const excerpt = document.createElement('span');
      excerpt.textContent = scene.text;
      const sceneTime = document.createElement('span');
      sceneTime.className = 'scene-time';
      const timingLabel = scene.timing_mode === 'word_timestamp' ? 'word-timed'
        : scene.timing_mode === 'manual_fraction_estimate' ? 'manual share estimate'
        : scene.timing_mode === 'untimed_manual_phrase' ? 'set timing shares or merge'
        : scene.timing_mode === 'ayah_timestamp' ? 'ayah timing' : 'duration estimate';
      sceneTime.textContent = scene.segment_count > 1 && scene.timing_mode === 'untimed_manual_phrase'
        ? timingLabel : `${Number(scene.start_time || 0).toFixed(1)}–${Number(scene.end_time || 0).toFixed(1)} s · ${timingLabel}`;
      select.append(heading, excerpt, sceneTime);
      select.addEventListener('click', () => paintPreviewAyah(index));
      row.append(select);

      const actions = document.createElement('div');
      actions.className = 'scene-actions';
      if (scene.segment_count > 1) {
        const share = document.createElement('label'); share.className = 'scene-share'; share.textContent = 'Share %';
        const input = document.createElement('input'); input.type = 'number'; input.min = '5'; input.max = '95'; input.step = '1';
        input.value = scene.manual_duration_fraction ? String(Math.round(Number(scene.duration_fraction) * 100)) : '';
        input.placeholder = 'Set %';
        input.setAttribute('aria-label', `Ayah ${scene.ayah_number}, part ${scene.segment_index} audio time percentage`);
        input.addEventListener('change', () => {
          const group = previewScenes.filter(item => item.ayah_number === scene.ayah_number);
          const shareValue = Math.max(5, Math.min(95, Number(input.value || 5))) / 100;
          const siblings = group.filter(item => item !== scene);
          scene.duration_fraction = shareValue; scene.manual_duration_fraction = true;
          if (siblings.length === 1 && !siblings[0].manual_duration_fraction) {
            siblings[0].duration_fraction = 1 - shareValue;
            siblings[0].manual_duration_fraction = true;
          }
          input.value = String(Math.round(shareValue * 100));
          const total = group.reduce((sum, item) => sum + Number(item.duration_fraction || 0), 0);
          if (!group.every(item => item.manual_duration_fraction) || Math.abs(total - 1) >= .005) {
            scene.timing_mode = 'untimed_manual_phrase';
            $('scene-timing-note').textContent = 'Set timing shares for every phrase so they total 100%, or merge the phrases to keep the whole ayah synchronized.';
          }
          scenePlanRequest++; scenePlanManual = true; refreshSceneLabels(); renderSceneTimeline(true);
          updateCaptionPreview().catch(showError); hideRenderedVideo();
        });
        share.append(input); actions.append(share);
      }
      const words = scene.text.trim().split(/\s+/);
      if (words.length >= 6 && scene.segment_count === 1) {
        const split = document.createElement('button');
        split.type = 'button'; split.textContent = 'Split'; split.title = 'Split this caption scene';
        split.addEventListener('click', event => {
          event.stopPropagation();
          let middle = Math.floor(words.length / 2);
          for (let distance = 0; distance < 3; distance++) {
            const candidate = middle + distance;
            if (candidate > 0 && candidate < words.length && /[،؛.!؟ۚۖۗۘۙۛۜ۞۩۝]$/u.test(words[candidate - 1])) { middle = candidate; break; }
          }
          previewScenes.splice(index, 1,
            {...scene, text: words.slice(0, middle).join(' ')},
            {...scene, text: words.slice(middle).join(' ')});
          scenePlanRequest++; scenePlanManual = true; refreshSceneLabels(); previewIndex = index;
          renderSceneTimeline(true); updateCaptionPreview().catch(showError); hideRenderedVideo();
        });
        actions.append(split);
      }
      if (index > 0 && previewScenes[index - 1].ayah_number === scene.ayah_number) {
        const merge = document.createElement('button');
        merge.type = 'button'; merge.textContent = 'Merge'; merge.title = 'Merge with the previous part of this ayah';
        merge.addEventListener('click', event => {
          event.stopPropagation();
          previewScenes.splice(index - 1, 2, {...scene, text: `${previewScenes[index - 1].text} ${scene.text}`});
          scenePlanRequest++; scenePlanManual = true; refreshSceneLabels(); previewIndex = index - 1;
          renderSceneTimeline(true); updateCaptionPreview().catch(showError); hideRenderedVideo();
        });
        actions.append(merge);
      }
      row.append(actions); list.append(row);
    });
    $('scene-summary').textContent = `${previewScenes.length} scene${previewScenes.length === 1 ? '' : 's'} · ${new Set(previewScenes.map(scene => scene.ayah_number)).size} ayah${new Set(previewScenes.map(scene => scene.ayah_number)).size === 1 ? '' : 's'}`;
    $('scene-timing-note').textContent = previewScenes.some(scene => scene.timing_mode === 'untimed_manual_phrase')
      ? 'Phrase splits need validated word timestamps or timing shares you set that total 100%. Merge them to keep the full ayah visible at its ayah boundary.'
      : 'Scene boundaries follow ayah timing. Phrase-level word timing is used only when the configured recitation service returns validated word segments.';
  }

  async function updateScenePlan() {
    if (scenePlanManual) { renderSceneTimeline(true); return previewScenes; }
    const requestId = ++scenePlanRequest;
    const response = await fetch('/api/scenes/plan', {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(scenePayload()),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'Could not plan caption scenes.');
    if (requestId !== scenePlanRequest) return previewScenes;
    previewScenes = payload.scenes;
    previewIndex = Math.min(previewIndex, Math.max(0, previewScenes.length - 1));
    renderSceneTimeline(payload.approximate_timing);
    return previewScenes;
  }

  function applyVideoTemplate(templateId) {
    const preset = videoTemplates[templateId];
    if (!preset) return;
    selectedTemplateId = templateId;
    theme = preset.theme;
    $('caption-style').value = preset.caption_style;
    captionColor = preset.caption_color;
    $('arabic-font').value = preset.font_id || 'naskh';
    $('max-lines').value = String(preset.max_lines || 5);
    $('show-surah-title').checked = Boolean(preset.show_surah_arabic ?? preset.show_surah_title);
    $('show-ayah-number').checked = preset.show_ayah_number !== false;
    $('show-quran-text').checked = preset.show_quran_text !== false;
    $('surah-name-template').value = preset.surah_template || 'ornamental_gold';
    $('ayah-number-template').value = preset.ayah_number_template || 'gold_medallion';
    $('surah-color').value = preset.surah_color || '#ffd166';
    $('ayah-color').value = preset.ayah_color || '#ffdf8e';
    $('surah-scale').value = preset.surah_scale || '0.46';
    $('ayah-number-scale').value = preset.ayah_number_scale || '0.38';
    $('surah-align').value = preset.surah_align || 'center';
    $('ayah-number-align').value = preset.ayah_number_align || 'center';
    $('surah-font-id').value = preset.surah_font_id || preset.font_id || $('arabic-font').value;
    $('ayah-number-font-id').value = preset.ayah_number_font_id || preset.font_id || $('arabic-font').value;
    $('surah-opacity').value = preset.surah_opacity ?? 0.9;
    $('ayah-number-opacity').value = preset.ayah_number_opacity ?? 0.96;
    $('surah-placement').value = preset.surah_placement || 'above';
    $('ayah-number-placement').value = preset.ayah_number_placement || 'above';
    $('caption-position').value = preset.caption_position || 'center';
    $('text-bg-enabled').checked = Boolean(preset.text_bg_enabled);
    $('text-bg-color').value = preset.text_bg_color || '#000000';
    $('text-bg-opacity').value = preset.text_bg_opacity ?? 0.65;
    $('glow-type').value = preset.glow_type || 'none';
    $('glow-radius').value = preset.glow_radius ?? 14;
    $('viewer-title-enabled').checked = preset.show_viewer_title !== false;
    $('viewer-title-icon-enabled').checked = preset.show_title_icon !== false;
    $('viewer-header-surah-enabled').checked = preset.show_header_surah !== false;
    $('viewer-header-surah-language').value = preset.header_surah_language || 'english';
    $('viewer-header-range-enabled').checked = preset.show_ayah_range !== false;
    $('viewer-header-range-language').value = preset.ayah_range_language || 'english';
    $('viewer-header-range-format').value = preset.ayah_range_format || 'label';
    $('viewer-header-qari-enabled').checked = preset.show_qari_in_header !== false;
    $('viewer-title-template').value = preset.title_template || 'dark_pill';
    $('viewer-title-color').value = preset.title_accent || '#edc85f';
    $('viewer-title-opacity').value = preset.title_opacity ?? .88;
    $('viewer-title-size').value = preset.title_size || .027;
    $('viewer-title-position').value = preset.title_position || 'top';
    $('show-translation').checked = Boolean(preset.show_translation);
    $('translation-color').value = preset.translation_color || '#ffffff';
    $('translation-size').value = preset.translation_size || .026;
    $('translation-bg-enabled').checked = Boolean(preset.translation_bg_enabled);
    $('translation-bg-color').value = preset.translation_bg_color || '#10161d';
    $('translation-bg-opacity').value = preset.translation_bg_opacity || .4;
    $('show-waveform').checked = preset.show_waveform !== false;
    $('waveform-style').value = preset.waveform_style || 'gold';
    $('waveform-color').value = preset.waveform_color || '#f0c64b';
    $('waveform-count').value = String(preset.waveform_count || 13);
    $('waveform-speed').value = preset.waveform_speed || 1;
    $('show-reciter-badge').checked = preset.show_reciter_badge !== false;
    $('reciter-color').value = preset.reciter_color || '#ffffff';
    $('reciter-background').value = preset.reciter_background || '#10161d';
    $('reciter-opacity').value = preset.reciter_opacity ?? .88;
    $('show-progress').checked = preset.show_progress !== false;
    $('progress-color').value = preset.progress_color || '#edbd36';
    $('progress-track-color').value = preset.progress_track_color || '#d1d5db';
    $('progress-height').value = preset.progress_height || 6;
    document.querySelectorAll('.video-template-choice').forEach(button => {
      const selected = button.dataset.templateId === templateId;
      button.classList.toggle('selected-video-template', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
    document.querySelectorAll('.background-choice').forEach(button => {
      button.classList.toggle('selected-background', button.dataset.theme === theme);
    });
    document.querySelectorAll('.caption-color-choice').forEach(button => {
      button.classList.toggle('selected-caption-color', button.dataset.color === captionColor);
    });
    setWallpaperPreview();
    updateViewerLayerPreview();
    scenePlanManual = false;
    updateScenePlan().then(updateCaptionPreview).catch(showError);
    hideRenderedVideo();
  }

  function applyBackgroundSequenceTemplate(templateId) {
    const preset = backgroundSequenceTemplates[templateId];
    if (!preset || !preset.scenes?.length) return;
    clearCustomBackgroundPreview();
    $('background-file').value = '';
    $('background-file-name').textContent = 'Five bundled photo scenes · no uploaded media';
    $('background-sequence-template').value = templateId;
    $('sequence-enabled').checked = true;
    $('transitions-enabled').checked = true;
    $('sequence-loop').checked = Boolean(preset.loop);
    $('default-background-transition').value = preset.transition || 'crossfade';
    $('background-transition-duration').value = preset.transition_duration ?? .45;
    $('background-animation-enabled').checked = true;
    $('background-animation-preset').value = preset.animation_preset || 'gentle_movement';
    $('background-animation-intensity').value = preset.animation_intensity ?? .4;
    $('background-animation-duration').value = preset.animation_duration ?? 18;
    $('background-animation-speed').value = preset.animation_speed ?? 1;
    $('background-animation-start').value = preset.animation_start ?? 0;
    theme = preset.scenes[0].theme;
    builtinSequenceIndex = 0;
    updateBackgroundSequenceSelection();
    document.querySelectorAll('.background-choice').forEach(button => {
      button.classList.toggle('selected-background', button.dataset.theme === theme);
    });
    renderBackgroundClipList();
    playBackgroundSequenceTemplate(0);
    hideRenderedVideo(); scheduleProjectAutosave();
    setProjectStatus(`Applied “${preset.name}” · five scenes with ${preset.transition.replace('_',' ')}`);
  }

  function applyQuranTextTemplate(templateId) {
    const preset = textTemplates[templateId];
    if (!preset) return;
    $('caption-style').value = preset.caption_style;
    captionColor = preset.caption_color;
    $('arabic-font').value = preset.font_id;
    $('text-bg-enabled').checked = Boolean(preset.text_bg_enabled);
    $('text-bg-color').value = preset.text_bg_color;
    $('text-bg-opacity').value = preset.text_bg_opacity;
    $('glow-type').value = preset.glow_type;
    document.querySelectorAll('.caption-color-choice').forEach(button => {
      button.classList.toggle('selected-caption-color', button.dataset.color === captionColor);
    });
    hideRenderedVideo(); updateScenePlan().then(updateCaptionPreview).catch(showError);
  }

  function formatTime(seconds) {
    if (!Number.isFinite(seconds)) return '--:--';
    return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
  }

  function paintPreviewAyah(index = 0) {
    previewIndex = index;
    renderSceneTimeline();
    updateViewerLayerPreview();
    updateCaptionPreview().catch(() => {});
  }

  function updateSurahInfo() {
    const selected = surahSelect.selectedOptions[0];
    const count = Number(selected.dataset.ayahCount);
    const surah = Number(surahSelect.value);
    $('surah-total').textContent = `Total ${count} Ayahs`;
    startInput.max = count; endInput.max = count;
    updateRangeSummary();
    updateViewerLayerPreview();
  }

  function updateRangeSummary() {
    const first = Number(startInput.value || 1), last = Number(endInput.value || first);
    if (!Number.isInteger(first) || !Number.isInteger(last) || first < 1 || last < first) return;
    const count = Math.max(0, last - first + 1);
    document.querySelector('.scope-count').textContent = `${count} ${count === 1 ? 'Ayah' : 'Ayahs'}`;
    document.querySelector('.scope-duration').textContent = `Audio timed to ${count} ${count === 1 ? 'ayah' : 'ayahs'}`;
  }

  async function loadVerses(updateEditor = true) {
    const selectionKey = verseSelectionKey();
    const requestId = ++verseLoadRequest;
    if (updateEditor) {
      ayahText.setAttribute('aria-busy', 'true');
      $('ayah-text-status').textContent = 'Loading the selected ayahs…';
    }
    const [surah, start, end] = selectionKey.split(':');
    const params = new URLSearchParams({surah, start, end});
    const response = await fetch(`/api/verses?${params}`);
    let payload;
    try {
      payload = await response.json();
    } catch (_) {
      const contentType = response.headers.get('content-type') || 'unknown content type';
      throw new Error(`The Quran text endpoint returned ${contentType} instead of JSON (HTTP ${response.status}). Restart Flask from this project, then reload the page.`);
    }
    if (!response.ok) {
      if (updateEditor && requestId === verseLoadRequest) {
        ayahText.setAttribute('aria-busy', 'false');
        $('ayah-text-status').textContent = 'Could not load the selected ayahs. Check the range and try again.';
      }
      throw new Error(payload.error || 'Could not load Quran text.');
    }
    // Range controls can change while a fetch is in flight. Never let an older
    // response replace the current selection's Quran text or preview scenes.
    if (requestId !== verseLoadRequest || selectionKey !== verseSelectionKey()) return previewAyahs;
    previewAyahs = payload.ayahs;
    if (updateEditor) {
      ayahText.value = payload.ayahs.join('\n');
      ayahText.setAttribute('aria-busy', 'false');
      $('ayah-text-status').textContent = `${payload.ayahs.length} ${payload.ayahs.length === 1 ? 'ayah' : 'ayahs'} loaded for this range. You can edit the captions.`;
      scenePlanManual = false;
    }
    loadedVerseSelection = selectionKey;
    const status = $('render-status');
    if (!status.classList.contains('bg-brand-50')) {
      status.className = 'hidden rounded-lg px-3 py-2 text-sm';
      $('render-status-message').replaceChildren();
      $('render-progress-row').classList.add('hidden');
      $('render-cancel-btn').classList.add('hidden');
    }
    document.querySelector('.scope-duration').textContent = 'Audio timed to selected ayahs';
    hideRenderedVideo();
    if (updateEditor || !scenePlanManual) await updateScenePlan();
    if (requestId !== verseLoadRequest || selectionKey !== verseSelectionKey()) return previewAyahs;
    paintPreviewAyah(0);
    return payload.ayahs;
  }

  function scheduleVerseLoad(changedInput = null) {
    updateSurahInfo();
    const count = Number(surahSelect.selectedOptions[0]?.dataset.ayahCount || 1);
    const start = Number(startInput.value), end = Number(endInput.value);
    let message = '';
    if (!Number.isInteger(start) || start < 1 || start > count) message = `Starting ayah must be a whole number from 1 to ${count}.`;
    else if (!Number.isInteger(end) || end < 1 || end > count) message = `Ending ayah must be a whole number from 1 to ${count}.`;
    else if (end < start) message = 'Ending ayah must be the same as or later than the starting ayah.';
    $('ayah-range-validation').textContent = message;
    $('ayah-range-validation').classList.toggle('hidden', !message);
    startInput.setAttribute('aria-invalid', String(Boolean(message && changedInput === startInput)));
    endInput.setAttribute('aria-invalid', String(Boolean(message && changedInput === endInput)));
    if (message) return;
    loadedVerseSelection = '';
    ayahText.setAttribute('aria-busy', 'true');
    $('ayah-text-status').textContent = `Updating Arabic text for ayahs ${start}–${end}…`;
    updateRangeSummary();
    scenePlanRequest++;
    scenePlanManual = false;
    clearTimeout(verseLoadTimer);
    verseLoadTimer = setTimeout(() => loadVerses(true).catch(error => {
      ayahText.setAttribute('aria-busy', 'false');
      $('ayah-text-status').textContent = 'Could not load the selected ayahs. Check your connection and try again.';
      showError(error);
    }), 100);
  }

  function showError(message) {
    const status = $('render-status');
    status.className = 'rounded-lg px-3 py-2 text-sm bg-red-50 text-red-700';
    $('render-status-message').textContent = typeof message === 'string' ? message : message.message;
    $('render-progress-row').classList.add('hidden');
    $('render-cancel-btn').classList.add('hidden');
  }

  function refreshDownloadLink() {
    const link = $('result-download-link');
    if (!link || !lastDownloadUrl) return;
    const target = new URL(lastDownloadUrl, window.location.origin);
    const title = $('video-title').value.trim();
    if (title) target.searchParams.set('title', title);
    else target.searchParams.delete('title');
    link.href = target.pathname + target.search;
  }

  async function loadYoutubeMetadata() {
    const params = new URLSearchParams({
      surah: surahSelect.value, start: startInput.value || '1',
      end: endInput.value || startInput.value || '1', reciter_id: selectedReciter,
    });
    const response = await fetch('/api/youtube-metadata?' + params);
    const metadata = await response.json();
    if (!response.ok) throw new Error(metadata.error || 'Could not generate YouTube metadata.');
    $('metadata-ar-title').value = metadata.arabic.title;
    $('metadata-ar-description').value = metadata.arabic.description + '\n\n' + metadata.arabic.hashtags.join(' ');
    $('metadata-ar-tags').value = metadata.arabic.tags.join(', ');
    $('metadata-en-title').value = metadata.english.title;
    $('metadata-en-description').value = metadata.english.description + '\n\n' + metadata.english.hashtags.join(' ');
    $('metadata-en-tags').value = metadata.english.tags.join(', ');
    if (!$('video-title').value.trim()) $('video-title').value = metadata.title;
    refreshDownloadLink();
    return metadata;
  }

  $('refresh-youtube-metadata').addEventListener('click', () => {
    loadYoutubeMetadata().catch(error => { $('metadata-copy-status').textContent = error.message; });
  });
  document.querySelectorAll('.metadata-copy').forEach(button => button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText($(button.dataset.copyTarget).value);
      $('metadata-copy-status').textContent = button.textContent.replace(/^Copy /, '') + ' copied.';
    } catch {
      $('metadata-copy-status').textContent = 'Clipboard access is unavailable in this browser.';
    }
  }));
  $('video-title').addEventListener('input', () => { refreshDownloadLink(); scheduleProjectAutosave(); });

  function expandSceneTimings(ayahTimings) {
    const scenesByAyah = new Map();
    previewScenes.forEach(scene => {
      if (!scenesByAyah.has(scene.ayah_number)) scenesByAyah.set(scene.ayah_number, []);
      scenesByAyah.get(scene.ayah_number).push(scene);
    });
    const expanded = [];
    ayahTimings.forEach((timing, index) => {
      const scenes = scenesByAyah.get(Number(timing.ayah)) || [];
      const nextStart = ayahTimings[index + 1]?.start;
      const end = Number.isFinite(nextStart) ? nextStart : timing.end;
      const duration = Math.max(.01, end - timing.start);
      let parts = scenes.length ? scenes : [{scene_index:index, ayah_number:Number(timing.ayah), text:previewAyahs[index] || ''}];
      const useManualFractions = parts.length > 1 && parts.every(scene => scene.manual_duration_fraction)
        && Math.abs(parts.reduce((sum, scene) => sum + Number(scene.duration_fraction || 0), 0) - 1) < .005;
      if (parts.length > 1 && !useManualFractions) {
        parts = [{scene_index:index, ayah_number:Number(timing.ayah),
          text:previewAyahs[index] || parts.map(scene => scene.text).join(' '), timing_mode:'ayah_timestamp'}];
      }
      let cursor = timing.start;
      parts.forEach((scene, part) => {
        const partEnd = part === parts.length - 1 ? end : cursor + duration * scene.duration_fraction;
        scene.start_time = cursor; scene.end_time = partEnd; scene.duration = partEnd - cursor;
        scene.ayah_total_duration = duration;
        if (parts.length === 1) scene.duration_fraction = 1;
        expanded.push({...scene, start:cursor, end:partEnd});
        cursor = partEnd;
      });
    });
    return expanded;
  }

  async function startRecitationPreview() {
    const params = new URLSearchParams({surah: surahSelect.value, start: startInput.value || '1', end: endInput.value || startInput.value || '1'});
    const response = await fetch(`/api/reciters/${selectedReciter}/timings?${params}`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not load verse timing.');
    const player = $('voice-preview-audio');
    previewAyahs = await loadVerses(false);
    previewTimings = expandSceneTimings(result.timings);
    if (!previewTimings.length) throw new Error('No ayah scene timing was returned for this selection.');
    if (player.src !== result.audio_url) {
      player.src = result.audio_url;
      await new Promise((resolve, reject) => {
        player.addEventListener('loadedmetadata', resolve, {once:true});
        player.addEventListener('error', () => reject(new Error('Recitation audio could not be loaded.')), {once:true});
        player.load();
      });
    } else if (player.readyState < 1) {
      await new Promise(resolve => player.addEventListener('loadedmetadata', resolve, {once:true}));
    }
    player.playbackRate = speed;
    player.currentTime = previewTimings[0].start;
    paintPreviewAyah(0);
    player.ontimeupdate = () => {
      const elapsed = player.currentTime;
      let current = previewTimings.findIndex(timing => elapsed >= timing.start && elapsed < timing.end);
      if (current < 0) {
        for (let index = previewTimings.length - 1; index >= 0; index--) {
          if (elapsed >= previewTimings[index].start) { current = index; break; }
        }
      }
      if (current < 0) current = 0;
      if (current !== previewIndex) paintPreviewAyah(current);
      const first = previewTimings[0].start, last = previewTimings[previewTimings.length - 1].end;
      syncTimeline(player);
      if (elapsed >= previewTimings[previewTimings.length - 1].end) {
        player.pause();
        player.currentTime = previewTimings[0].start;
        paintPreviewAyah(0);
        syncTimeline(player);
        setPlaybackIcon(false);
      }
    };
    await player.play();
    setPlaybackIcon(true);
  }

  fetch('/api/reciters').then(response => response.json()).then(({reciters}) => {
    reciterList.replaceChildren();
    reciters.forEach((reciter, index) => {
      reciterById.set(reciter.id, reciter);
      const item = document.createElement('li');
      item.className = 'reciter-option flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-50 text-gray-700 cursor-pointer transition-colors';
      item.dataset.name = reciter.name; item.dataset.id = reciter.id;
      const name = document.createElement('span'); name.className = 'text-sm font-medium'; name.textContent = reciter.name;
      const type = document.createElement('span'); type.className = 'text-[11px] text-gray-500 bg-gray-100 px-2 py-0.5 rounded-md'; type.textContent = reciter.style;
      item.append(name, type);
      if (index === 0) item.classList.add('bg-brand-50/70');
      item.addEventListener('click', () => {
        selectedReciter = reciter.id;
        $('selected-reciter-name').textContent = reciter.name;
        updatePreviewReciterName(reciter.name);
        $('reciter-dropdown').classList.add('hidden');
        hideRenderedVideo();
      });
      reciterList.append(item);
    });
    const selected = reciterById.get(selectedReciter);
    if (selected) {
      $('selected-reciter-name').textContent = selected.name;
      updatePreviewReciterName(selected.name);
      reciterList.querySelector(`[data-id="${CSS.escape(selectedReciter)}"]`)?.classList.add('bg-brand-50/70');
    }
  }).catch(() => { reciterList.textContent = 'Could not load reciters.'; });

  $('reciter-trigger').addEventListener('click', event => {
    event.stopPropagation();
    $('reciter-dropdown').classList.toggle('hidden');
    if (!$('reciter-dropdown').classList.contains('hidden')) $('reciter-filter-input').focus();
  });
  document.addEventListener('click', () => $('reciter-dropdown').classList.add('hidden'));
  $('reciter-dropdown').addEventListener('click', event => event.stopPropagation());
  $('reciter-filter-input').addEventListener('input', event => {
    const query = event.target.value.toLowerCase();
    document.querySelectorAll('.reciter-option').forEach(item => { item.hidden = !item.textContent.toLowerCase().includes(query); });
  });
  $('preview-sample-btn').addEventListener('click', async () => {
    const button = $('preview-sample-btn');
    button.disabled = true;
    try {
      await startRecitationPreview();
    } catch (error) { showError(error.message); }
    finally { button.disabled = false; }
  });

  [['start-inc', startInput, 1], ['start-dec', startInput, -1], ['end-inc', endInput, 1], ['end-dec', endInput, -1]].forEach(([button, input, delta]) => {
      $(button).addEventListener('click', () => {
      input.value = Math.max(Number(input.min), Math.min(Number(input.max), Number(input.value || 1) + delta));
      scheduleVerseLoad(input);
    });
  });
  [startInput, endInput].forEach(input => {
    input.addEventListener('input', () => scheduleVerseLoad(input));
    input.addEventListener('change', () => scheduleVerseLoad(input));
  });
  ayahText.addEventListener('input', () => {
    hideRenderedVideo(); scenePlanRequest++; scenePlanManual = false; clearTimeout(scenePlanTimer);
    scenePlanTimer = setTimeout(() => updateScenePlan().then(() => paintPreviewAyah(0)).catch(showError), 250);
  });
  surahSelect.addEventListener('change', () => {
    startInput.value = 1; endInput.value = 1; scheduleVerseLoad();
  });

  document.querySelectorAll('.aspect-ratio-btn').forEach(button => button.addEventListener('click', () => {
    ratio = button.dataset.ratio;
    document.querySelectorAll('.aspect-ratio-btn').forEach(item => item.classList.remove('selected-ratio'));
    button.classList.add('selected-ratio');
    updateCanvasSummary();
    syncPreviewAspectRatio();
    setWallpaperPreview();
    scenePlanManual = false;
    updateScenePlan().then(updateCaptionPreview).catch(showError);
    hideRenderedVideo();
  }));

  $('export-resolution').addEventListener('change', () => {
    $('custom-resolution-fields').classList.toggle('hidden', $('export-resolution').value !== 'custom');
    updateCanvasSummary(); hideRenderedVideo();
    scenePlanManual = false; updateScenePlan().then(updateCaptionPreview).catch(showError);
  });
  ['custom-width','custom-height'].forEach(id => $(id).addEventListener('input', () => {
    updateCanvasSummary(); hideRenderedVideo();
    clearTimeout(window.customSizePreviewTimer);
    window.customSizePreviewTimer = setTimeout(() => updateScenePlan().then(updateCaptionPreview).catch(showError), 250);
  }));
  $('export-fps').addEventListener('change', () => { updateCanvasSummary(); hideRenderedVideo(); });
  $('export-quality').addEventListener('change', () => { updateQualityDescription(); hideRenderedVideo(); });
  $('export-encoder').addEventListener('change', hideRenderedVideo);
  $('export-crf').addEventListener('input', () => {
    $('export-crf-value').textContent = $('export-crf').value; hideRenderedVideo();
  });
  ['audio-bitrate','audio-sample-rate'].forEach(id => $(id).addEventListener('change', hideRenderedVideo));
  updateQualityDescription(); updateCanvasSummary(); updateEncoderCapabilities();

  document.querySelectorAll('.background-choice').forEach(button => button.addEventListener('click', () => {
    backgroundMediaCategory = 'image';
    setBackgroundMediaCategory('image');
    theme = button.dataset.theme;
    $('background-sequence-template').value = '';
    $('sequence-enabled').checked = false;
    updateBackgroundSequenceSelection();
    clearTimeout(builtinSequencePreviewTimer);
    document.querySelectorAll('.background-choice').forEach(item => item.classList.remove('selected-background'));
    button.classList.add('selected-background');
    const preview = $('preview-background');
    $('background-file').value = '';
    clearCustomBackgroundPreview();
    $('background-file-name').textContent = 'PNG, JPG, WEBP, MP4, MOV or WEBM';
    preview.className = 'absolute inset-0 bg-cover bg-center preview-background';
    setWallpaperPreview();
    hideRenderedVideo();
  }));
  function filterBackgrounds() {
    const query = $('background-search').value.trim().toLowerCase();
    const category = $('background-category').value;
    document.querySelectorAll('.background-choice').forEach(button => {
      const matchesText = button.textContent.toLowerCase().includes(query);
      const matchesCategory = category === 'all' || button.dataset.category === category;
      button.hidden = backgroundMediaCategory !== 'image' || !matchesText || !matchesCategory;
    });
  }
  function setBackgroundMediaCategory(category) {
    backgroundMediaCategory = category === 'video' ? 'video' : 'image';
    const isVideo = backgroundMediaCategory === 'video';
    $('background-image-tab').classList.toggle('selected', !isVideo);
    $('background-video-tab').classList.toggle('selected', isVideo);
    $('background-image-tab').setAttribute('aria-selected', String(!isVideo));
    $('background-video-tab').setAttribute('aria-selected', String(isVideo));
    $('background-image-gallery').classList.toggle('hidden', isVideo);
    $('background-video-gallery').classList.toggle('hidden', !isVideo);
    $('background-file').accept = isVideo
      ? 'video/mp4,video/quicktime,video/webm,video/x-m4v'
      : 'image/png,image/jpeg,image/webp';
    $('background-video-selection').textContent = selectedBackgroundVideoTemplate
      ? `${backgroundVideoTemplates[selectedBackgroundVideoTemplate]?.name || 'Bundled video'} selected · source audio muted`
      : backgroundClipRows.some(row => row.file?.type?.startsWith('video/'))
      ? backgroundClipRows.filter(row => row.file?.type?.startsWith('video/')).map(row => row.file.name).join(' · ')
      : 'No video selected yet. Choose a licensed video file above or here.';
    filterBackgrounds();
  }
  $('background-image-tab').addEventListener('click', () => setBackgroundMediaCategory('image'));
  $('background-video-tab').addEventListener('click', () => setBackgroundMediaCategory('video'));
  document.querySelectorAll('.background-video-choice').forEach(button => button.addEventListener('click', () => {
    setBackgroundMediaCategory('video');
    selectBackgroundVideoTemplate(button.dataset.videoTemplate);
  }));
  $('choose-video-background').addEventListener('click', () => {
    setBackgroundMediaCategory('video');
    $('background-file').click();
  });
  $('background-search').addEventListener('input', filterBackgrounds);
  $('background-category').addEventListener('change', filterBackgrounds);
  document.querySelectorAll('.background-sequence-choice').forEach(button => button.addEventListener('click', () => {
    applyBackgroundSequenceTemplate(button.dataset.sequenceId);
  }));
  document.querySelectorAll('.video-template-choice').forEach(button => button.addEventListener('click', () => {
    applyVideoTemplate(button.dataset.templateId);
  }));
  $('reset-viewer-template-btn').addEventListener('click', () => applyVideoTemplate(selectedTemplateId));
  $('quran-text-template').addEventListener('change', event => applyQuranTextTemplate(event.target.value));
  ['show-surah-title','show-ayah-number','surah-name-template','ayah-number-template','surah-color','ayah-color','surah-align','ayah-number-align','surah-font-id','ayah-number-font-id','surah-placement','ayah-number-placement']
    .forEach(id => $(id).addEventListener('change', () => {
      hideRenderedVideo(); updateScenePlan().then(updateCaptionPreview).catch(showError);
    }));
  ['surah-scale','ayah-number-scale','surah-opacity','ayah-number-opacity'].forEach(id => $(id).addEventListener('input', () => {
    hideRenderedVideo(); updateCaptionPreview().catch(showError);
  }));
  $('background-file').addEventListener('change', () => {
    const files = [...$('background-file').files];
    if (!files.length) return;
    setBackgroundMediaCategory(files[0].type.startsWith('video/') ? 'video' : 'image');
    $('background-sequence-template').value = '';
    updateBackgroundSequenceSelection();
    $('background-file-name').textContent = files.length === 1 ? files[0].name : `${files.length} background items · sequence ${$('sequence-enabled').checked ? 'enabled' : 'off (first item active)'}`;
    renderUploadedBackgroundPreview(files);
    $('background-video-selection').textContent = files.some(file => file.type.startsWith('video/'))
      ? files.filter(file => file.type.startsWith('video/')).map(file => file.name).join(' · ')
      : backgroundMediaCategory === 'video' ? 'Choose a supported video file to preview and render.' : 'No video selected yet.';
    hideRenderedVideo();
  });
  $('sequence-enabled').addEventListener('change', () => {
    renderBackgroundClipList();
    if (backgroundClipRows.length) playPreviewSequenceItem(0);
    else playBackgroundSequenceTemplate(0);
    hideRenderedVideo(); scheduleProjectAutosave();
  });
  $('transitions-enabled').addEventListener('change', () => {
    renderBackgroundClipList();
    if (backgroundClipRows.length) playPreviewSequenceItem(previewClipIndex);
    else playBackgroundSequenceTemplate(0);
    hideRenderedVideo(); scheduleProjectAutosave();
  });
  ['default-background-transition','background-transition-duration','background-transition-color','sequence-loop'].forEach(id => {
    $(id).addEventListener('change', () => {
      if (id === 'default-background-transition' || id === 'background-transition-duration') renderBackgroundClipList();
      hideRenderedVideo(); scheduleProjectAutosave();
    });
  });
  $('background-animation-enabled').addEventListener('change', () => {
    updateBackgroundAnimationPreview(); hideRenderedVideo(); scheduleProjectAutosave();
  });
  ['background-motion-direction','background-animation-preset','background-animation-intensity','background-animation-duration','background-animation-speed','background-animation-start'].forEach(id => {
    $(id).addEventListener('input', () => {
      updateBackgroundAnimationPreview(); hideRenderedVideo(); scheduleProjectAutosave();
    });
    $(id).addEventListener('change', updateBackgroundAnimationPreview);
  });
  $('background-atmosphere-enabled').addEventListener('change', () => {
    updateBackgroundAnimationPreview(); hideRenderedVideo(); scheduleProjectAutosave();
  });
  ['background-atmosphere-intensity','background-atmosphere-duration','background-atmosphere-speed','background-atmosphere-start'].forEach(id => {
    $(id).addEventListener('input', () => {
      updateBackgroundAnimationPreview(); hideRenderedVideo(); scheduleProjectAutosave();
    });
    $(id).addEventListener('change', updateBackgroundAnimationPreview);
  });
  ['background-fit','background-crop-x','background-crop-y'].forEach(id => {
    $(id).addEventListener('input', scheduleWallpaperPreview);
    $(id).addEventListener('change', () => { setWallpaperPreview(); hideRenderedVideo(); });
  });
  $('background-speed').addEventListener('input', () => {
    const rate = Number($('background-speed').value);
    backgroundClipRows.forEach(row => { row.speed = rate; });
    $('preview-background-video').playbackRate = rate;
    $('preview-background-video-blur').playbackRate = rate;
    renderBackgroundClipList(); hideRenderedVideo();
  });
  $('background-loop').addEventListener('change', () => {
    $('preview-background-video').loop = $('background-loop').checked;
    hideRenderedVideo();
  });
  $('background-audio-enabled').addEventListener('change', hideRenderedVideo);
  $('background-audio-volume').addEventListener('input', event => {
    $('background-audio-volume-label').textContent = `${Math.round(Number(event.target.value)*100)}% · Quran recitation remains primary`;
    hideRenderedVideo();
  });
  ['background-brightness','background-contrast','background-saturation','background-overlay-color','background-overlay-opacity'].forEach(id => {
    $(id).addEventListener('input', () => { updateBackgroundAdjustments(); hideRenderedVideo(); });
    $(id).addEventListener('change', () => { updateBackgroundAdjustments(); hideRenderedVideo(); });
  });
  $('wallpaper-jump').addEventListener('click', () => $('background-options').scrollIntoView({behavior:'smooth',block:'center'}));
  $('toggle-safezone-btn').addEventListener('click', () => $('safezone-overlay').classList.toggle('hidden'));
  $('caption-style').addEventListener('change', () => { hideRenderedVideo(); updateCaptionPreview().catch(() => {}); });
  $('caption-position').addEventListener('change', () => { hideRenderedVideo(); updateCaptionPreview().catch(() => {}); });
  ['text-bg-enabled','text-bg-color','text-bg-opacity','glow-type','glow-radius'].forEach(id => {
    $(id).addEventListener('input', () => { hideRenderedVideo(); updateCaptionPreview().catch(() => {}); });
    $(id).addEventListener('change', () => { hideRenderedVideo(); updateCaptionPreview().catch(() => {}); });
  });
  $('wrap-width').addEventListener('change', event => {
    wrapWidth = Number(event.target.value); hideRenderedVideo(); scenePlanManual = false;
    updateScenePlan().then(updateCaptionPreview).catch(showError);
  });
  ['arabic-font','max-lines'].forEach(id => $(id).addEventListener('change', () => {
    hideRenderedVideo(); scenePlanManual = false;
    updateScenePlan().then(updateCaptionPreview).catch(showError);
  }));
  $('show-surah-title').addEventListener('change', () => {
    scenePlanManual = false; updateScenePlan().then(updateCaptionPreview).catch(showError);
  });
  $('show-quran-text').addEventListener('change', () => {
    updateCaptionPreview().catch(showError); hideRenderedVideo(); scheduleProjectAutosave();
  });
  const viewerLayerControls = [
    'viewer-title-enabled','viewer-title-icon-enabled','viewer-header-surah-enabled','viewer-header-surah-language','viewer-header-range-enabled','viewer-header-range-language','viewer-header-range-format','viewer-header-qari-enabled','viewer-title-text','viewer-title-template','viewer-title-color','viewer-title-opacity','viewer-title-size','viewer-title-position',
    'show-translation','translation-text','translation-color','translation-size','translation-bg-enabled','translation-bg-color','translation-bg-opacity',
    'show-waveform','waveform-style','waveform-color','waveform-count','waveform-speed',
    'show-reciter-badge','reciter-label','reciter-color','reciter-background','reciter-opacity',
    'show-progress','progress-color','progress-track-color','progress-height',
  ];
  const refreshViewerLayerControls = () => {
    updateViewerLayerPreview(); hideRenderedVideo(); scheduleProjectAutosave();
  };
  viewerLayerControls.forEach(id => {
    $(id).addEventListener('input', refreshViewerLayerControls);
    $(id).addEventListener('change', refreshViewerLayerControls);
  });
  document.querySelectorAll('.caption-color-choice').forEach(button => button.addEventListener('click', () => {
    captionColor = button.dataset.color;
    document.querySelectorAll('.caption-color-choice').forEach(item => item.classList.toggle('selected-caption-color', item === button));
    hideRenderedVideo();
    updateCaptionPreview().catch(() => {});
  }));
  $('preview-scrubber').addEventListener('input', event => {
    const player = activePlayer();
    if (player.src && Number.isFinite(player.duration)) { player.currentTime = Number(event.target.value); syncTimeline(player); }
  });
  $('preview-volume').addEventListener('input', event => {
    const volume = Number(event.target.value);
    $('voice-preview-audio').volume = volume;
    $('rendered-video').volume = volume;
  });
  ['voice-preview-audio', 'rendered-video'].forEach(id => {
    const player = $(id);
    ['loadedmetadata', 'timeupdate', 'durationchange'].forEach(name => player.addEventListener(name, () => syncTimeline(player)));
    player.addEventListener('play', () => { setPlaybackIcon(true); });
    player.addEventListener('pause', () => { setPlaybackIcon(false); });
  });
  $('rewind-preview').addEventListener('click', () => {
    const player = activePlayer();
    if (player.src && Number.isFinite(player.currentTime)) player.currentTime = Math.max(player === $('voice-preview-audio') && previewTimings.length ? previewTimings[0].start : 0, player.currentTime - 10);
  });
  $('playback-toggle').addEventListener('click', () => {
    const rendered = $('rendered-video');
    if (!rendered.classList.contains('hidden') && rendered.src) {
      if (rendered.paused) rendered.play().catch(error => showError(error.message)); else rendered.pause();
      return;
    }
    if (!$('voice-preview-audio').src || $('voice-preview-audio').paused) startRecitationPreview().catch(error => showError(error.message));
    else { $('voice-preview-audio').pause(); setPlaybackIcon(false); }
  });
  const speeds = [1.0, 1.15, 0.9]; let speedIndex = 0;
  $('speed-cycle-btn').addEventListener('click', () => {
    speedIndex = (speedIndex + 1) % speeds.length; speed = speeds[speedIndex];
    $('speed-cycle-btn').textContent = `${speed.toFixed(2).replace(/0+$/,'').replace(/\.$/,'')}x`;
    $('speed-indicator').textContent = `${speed}x (${speed === 1 ? 'Natural' : 'Adjusted'})`;
    $('voice-preview-audio').playbackRate = speed;
  });
  $('api-toggle-btn').addEventListener('click', () => $('api-panel').classList.toggle('hidden'));
  $('copy-curl-btn').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText('curl -X POST http://127.0.0.1:5000/api/generate -F "surah=55" -F "ayah_start=13" -F "ayah_end=16" -F "reciter_id=mishary_alafasy" -F "aspect_ratio=9:16" -F "theme=misty_forest" -F "transition=crossfade" -F "caption_style=classic" -F "speed=1.0"'); $('copy-status').textContent='Copied!'; }
    catch { $('copy-status').textContent='Clipboard unavailable'; }
  });

  function updateRenderProgress(job) {
    $('render-status').className = 'rounded-lg px-3 py-2 text-sm bg-brand-50 text-brand-800';
    $('render-status-message').textContent = job.message || 'Rendering video…';
    $('render-progress-row').classList.remove('hidden');
    $('render-progress').value = Number(job.progress || 0);
    $('render-progress-percent').textContent = `${Math.round(job.progress || 0)}%`;
    $('render-phase').textContent = job.phase || job.status;
    const speed = Number(job.render_speed_fps);
    const remaining = Number(job.estimated_remaining_seconds);
    if (speed > 0 && Number.isFinite(remaining)) {
      $('render-estimate').textContent = `Measured estimate: about ${formatTime(remaining)} remaining at ${speed.toFixed(1)} rendered FPS. Approximate; encoding speed can vary.`;
      $('render-status-message').textContent = `${job.message || 'Rendering video…'} · ${speed.toFixed(1)} FPS · ~${formatTime(remaining)} left · elapsed ${formatTime(Number(job.elapsed_seconds || 0))}`;
    } else {
      $('render-estimate').textContent = 'Render estimate: Estimating from measured encoder speed…';
    }
  }

  async function waitForRender(job) {
    while (true) {
      const response = await fetch(job.status_url, {cache:'no-store'});
      const snapshot = await response.json();
      if (!response.ok) throw new Error(snapshot.error || 'Render status is unavailable.');
      updateRenderProgress(snapshot);
      if (snapshot.status === 'complete') return snapshot.result;
      if (snapshot.status === 'failed') throw new Error(snapshot.error || 'Video render failed.');
      if (snapshot.status === 'cancelled') {
        const error = new Error('Rendering cancelled.'); error.cancelled = true; throw error;
      }
      await new Promise(resolve => setTimeout(resolve, 450));
    }
  }

  $('render-cancel-btn').addEventListener('click', async () => {
    if (!activeRenderJobId) return;
    const button = $('render-cancel-btn'); button.disabled = true;
    try {
      const response = await fetch(`/api/jobs/${encodeURIComponent(activeRenderJobId)}/cancel`, {method:'POST'});
      const snapshot = await response.json();
      if (!response.ok && response.status !== 409) throw new Error(snapshot.error || 'Could not cancel render.');
      if (snapshot.status === 'complete') {
        $('render-status-message').textContent = 'The video completed before cancellation was received.';
      } else {
        $('render-status-message').textContent = snapshot.message || 'Cancellation requested…';
      }
    } catch (error) { showError(error.message); }
    finally { button.disabled = false; }
  });

  $('generate-video-btn').addEventListener('click', async () => {
    const button = $('generate-video-btn'), status = $('render-status'), original = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="material-symbols-outlined animate-spin">progress_activity</span><span>Preparing render…</span>';
    status.className = 'rounded-lg px-3 py-2 text-sm bg-brand-50 text-brand-800';
    $('render-status-message').textContent = 'Preparing selected ayahs, recitation, and video settings…';
    $('render-progress-row').classList.add('hidden');
    $('render-estimate').textContent = 'Render estimate: Estimating from measured encoder speed…';
    $('render-cancel-btn').classList.add('hidden');
    activeRenderJobId = null;
    try {
      await updateEncoderCapabilities(true);
      const selectionAtExport = verseSelectionKey();
      const verses = loadedVerseSelection === selectionAtExport ? previewAyahs : await loadVerses(true);
      if (loadedVerseSelection !== verseSelectionKey()) {
        throw new Error('The ayah range changed while preparing the video. Please export again.');
      }
      const form = new FormData();
      form.set('ayah_text', ayahText.value); form.set('aspect_ratio', ratio); form.set('reciter_id', selectedReciter);
      form.set('resolution', $('export-resolution').value);
      form.set('custom_width', $('custom-width').value); form.set('custom_height', $('custom-height').value);
      form.set('fps', $('export-fps').value); form.set('quality', $('export-quality').value);
      form.set('encoder', $('export-encoder').value);
      form.set('crf', $('export-crf').value); form.set('audio_bitrate', $('audio-bitrate').value);
      form.set('audio_sample_rate', $('audio-sample-rate').value);
      form.set('transition', $('transition-style').value); form.set('caption_style', $('caption-style').value);
      form.set('theme', theme); form.set('speed', speed);
      form.set('template_id', selectedTemplateId);
      form.set('show_surah_title', $('show-surah-title').checked);
      form.set('show_ayah_number', $('show-ayah-number').checked);
      const viewerFormFields = {
        'show-quran-text':'show_quran_text','viewer-title-enabled':'viewer_title_enabled',
        'viewer-title-icon-enabled':'viewer_title_icon_enabled',
        'viewer-header-surah-enabled':'viewer_header_surah_enabled',
        'viewer-header-surah-language':'viewer_header_surah_language',
        'viewer-header-range-enabled':'viewer_header_range_enabled',
        'viewer-header-range-language':'viewer_header_range_language',
        'viewer-header-range-format':'viewer_header_range_format',
        'viewer-header-qari-enabled':'viewer_header_qari_enabled',
        'viewer-title-text':'viewer_title_text','viewer-title-template':'viewer_title_template',
        'viewer-title-color':'viewer_title_color','viewer-title-opacity':'viewer_title_opacity',
        'viewer-title-size':'viewer_title_size','viewer-title-position':'viewer_title_position',
        'show-translation':'show_translation','translation-text':'translation_text',
        'translation-color':'translation_color','translation-size':'translation_size',
        'translation-bg-enabled':'translation_bg_enabled','translation-bg-color':'translation_bg_color','translation-bg-opacity':'translation_bg_opacity',
        'show-waveform':'show_waveform','waveform-style':'waveform_style','waveform-color':'waveform_color',
        'waveform-count':'waveform_count','waveform-speed':'waveform_speed',
        'show-reciter-badge':'show_reciter_badge','reciter-label':'reciter_label',
        'reciter-color':'reciter_color','reciter-background':'reciter_background','reciter-opacity':'reciter_opacity',
        'show-progress':'show_progress','progress-color':'progress_color',
        'progress-track-color':'progress_track_color','progress-height':'progress_height',
      };
      Object.entries(viewerFormFields).forEach(([id,key]) => {
        const element = $(id);
        form.set(key, element.type === 'checkbox' ? String(element.checked) : element.value);
      });
      form.set('surah_template', $('surah-name-template').value);
      form.set('ayah_number_template', $('ayah-number-template').value);
      form.set('surah_color', $('surah-color').value); form.set('ayah_color', $('ayah-color').value);
      form.set('surah_scale', $('surah-scale').value); form.set('ayah_number_scale', $('ayah-number-scale').value);
      form.set('surah_align', $('surah-align').value); form.set('ayah_number_align', $('ayah-number-align').value);
      form.set('surah_font_id', $('surah-font-id').value); form.set('ayah_number_font_id', $('ayah-number-font-id').value);
      form.set('surah_opacity', $('surah-opacity').value); form.set('ayah_number_opacity', $('ayah-number-opacity').value);
      form.set('surah_placement', $('surah-placement').value); form.set('ayah_number_placement', $('ayah-number-placement').value);
      form.set('caption_position', $('caption-position').value);
      form.set('text_bg_enabled', $('text-bg-enabled').checked);
      form.set('text_bg_color', $('text-bg-color').value);
      form.set('text_bg_opacity', $('text-bg-opacity').value);
      form.set('glow_type', $('glow-type').value); form.set('glow_radius', $('glow-radius').value);
      form.set('caption_color', captionColor); form.set('wrap_width', String(wrapWidth));
      form.set('font_id', $('arabic-font').value); form.set('max_lines', $('max-lines').value);
      form.set('surah', surahSelect.value); form.set('ayah_start', startInput.value); form.set('ayah_end', endInput.value);
      form.set('video_title', $('video-title').value.trim());
      form.set('scene_overrides', JSON.stringify(previewScenes.map(scene => ({
        ayah_number:scene.ayah_number, text:scene.text,
        ...(scene.manual_duration_fraction ? {duration_fraction:scene.duration_fraction} : {}),
      }))));
      form.set('background_fit', $('background-fit').value);
      form.set('crop_x', $('background-crop-x').value); form.set('crop_y', $('background-crop-y').value);
      form.set('background_speed', $('background-speed').value);
      form.set('background_loop', $('sequence-enabled').checked ? $('sequence-loop').checked : $('background-loop').checked);
      form.set('sequence_enabled', $('sequence-enabled').checked);
      form.set('background_sequence_template', $('background-sequence-template').value);
      form.set('background_video_template', selectedBackgroundVideoTemplate);
      form.set('transitions_enabled', $('transitions-enabled').checked);
      form.set('default_background_transition', $('default-background-transition').value);
      form.set('background_transition_color', $('background-transition-color').value);
      form.set('background_animation_enabled', $('background-animation-enabled').checked);
      form.set('background_motion_direction', $('background-motion-direction').value);
      form.set('background_animation_preset', $('background-animation-preset').value);
      form.set('background_animation_intensity', $('background-animation-intensity').value);
      form.set('background_animation_duration', $('background-animation-duration').value);
      form.set('background_animation_speed', $('background-animation-speed').value);
      form.set('background_animation_start', $('background-animation-start').value);
      form.set('background_atmosphere_enabled', $('background-atmosphere-enabled').checked);
      form.set('background_atmosphere_intensity', $('background-atmosphere-intensity').value);
      form.set('background_atmosphere_duration', $('background-atmosphere-duration').value);
      form.set('background_atmosphere_speed', $('background-atmosphere-speed').value);
      form.set('background_atmosphere_start', $('background-atmosphere-start').value);
      form.set('background_audio_enabled', $('background-audio-enabled').checked);
      form.set('background_audio_volume', $('background-audio-volume').value);
      form.set('background_brightness', $('background-brightness').value);
      form.set('background_contrast', $('background-contrast').value);
      form.set('background_saturation', $('background-saturation').value);
      form.set('background_overlay_color', $('background-overlay-color').value);
      form.set('background_overlay_opacity', $('background-overlay-opacity').value);
      if ($('sequence-enabled').checked) {
        backgroundClipRows.forEach(row => form.append('background_clips', row.file));
        form.set('background_clip_settings', JSON.stringify(backgroundClipRows.map(row => ({
          start:row.start, end:row.end, speed:row.speed, duration:row.duration,
          transition:row.transition, transition_duration:row.transition_duration,
        }))));
      } else if (backgroundClipRows[0]) {
        form.append('background', backgroundClipRows[0].file);
      }

      const response = await fetch('/api/generate', {method:'POST', body:form});
      const accepted = await response.json();
      if (!response.ok) throw new Error(accepted.error || 'Render could not be started.');
      activeRenderJobId = accepted.job_id;
      $('render-cancel-btn').classList.remove('hidden');
      const result = await waitForRender(accepted);
      activeRenderJobId = null;
      status.className = 'rounded-lg px-3 py-2 text-sm bg-emerald-50 text-emerald-800';
      $('render-progress-row').classList.add('hidden');
      $('render-cancel-btn').classList.add('hidden');
      const fallbackMessage = result.fallback_reason ? ` · fallback: ${result.fallback_reason}` : '';
      $('render-status-message').replaceChildren(document.createTextNode(
        'Video ready · ' + (result.encoder_name || 'CPU · x264') + fallbackMessage + ' · MP4 playback verified · ' + result.width + '×' + result.height + ' · ' + (result.fps || 30) + ' FPS · ' + result.duration.toFixed(1) + ' seconds · ' + result.reciter + ' · ' + verses.length + ' ayahs · ' + (result.scene_count || previewScenes.length) + ' scenes. ' + (result.timing_note || '')));
      lastDownloadUrl = result.download_url;
      if (!$('video-title').value.trim()) $('video-title').value = result.download_title || '';
      const link = document.createElement('a'); link.id = 'result-download-link'; link.className = 'font-semibold underline'; link.href = result.download_url; link.textContent = 'Download MP4';
      refreshDownloadLink();
      $('render-status-message').append(link);
      $('youtube-metadata-panel').classList.remove('hidden');
      loadYoutubeMetadata().catch(error => { $('metadata-copy-status').textContent = error.message; });
      const video = $('rendered-video'); video.src = result.download_url; video.classList.remove('hidden');
      video.volume = Number($('preview-volume').value); video.load();
      button.innerHTML = '<span class="material-symbols-outlined">check_circle</span><span>Video Ready</span>';
    } catch (error) {
      activeRenderJobId = null;
      if (error.cancelled) {
        status.className = 'rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-700';
        $('render-status-message').textContent = error.message;
      } else {
        status.className = 'rounded-lg px-3 py-2 text-sm bg-red-50 text-red-700';
        $('render-status-message').textContent = error.message;
      }
      $('render-progress-row').classList.add('hidden');
      $('render-cancel-btn').classList.add('hidden');
      button.innerHTML = original;
    } finally {
      button.disabled = false;
    }
  });

  $('export-preview-btn').addEventListener('click', () => $('generate-video-btn').click());

  $('save-project-btn').addEventListener('click', () => saveNamedProject());
  $('saved-projects').addEventListener('change', () => {
    const selected = Boolean($('saved-projects').value);
    $('open-project-btn').disabled = !selected; $('delete-project-btn').disabled = !selected;
  });
  $('open-project-btn').addEventListener('click', () => openNamedProject().catch(error => setProjectStatus(`Could not open project: ${error.message}`, true)));
  $('delete-project-btn').addEventListener('click', () => deleteNamedProject().catch(error => setProjectStatus(`Could not delete project: ${error.message}`, true)));
  $('undo-project-btn').addEventListener('click', () => undoProjectChange().catch(error => setProjectStatus(`Undo failed: ${error.message}`, true)));
  $('redo-project-btn').addEventListener('click', () => redoProjectChange().catch(error => setProjectStatus(`Redo failed: ${error.message}`, true)));
  $('save-custom-template-btn').addEventListener('click', saveCustomDesign);
  $('custom-template-list').addEventListener('change', () => {
    const selected = Boolean($('custom-template-list').value);
    $('apply-custom-template-btn').disabled = !selected; $('delete-custom-template-btn').disabled = !selected;
    $('export-custom-template-btn').disabled = !selected;
    if (selected) $('custom-template-name').value = customDesignRecords().find(item => item.id === $('custom-template-list').value)?.name || '';
  });
  $('apply-custom-template-btn').addEventListener('click', () => applyCustomDesign().catch(error => setProjectStatus(`Could not apply design: ${error.message}`, true)));
  $('delete-custom-template-btn').addEventListener('click', deleteCustomDesign);
  $('export-custom-template-btn').addEventListener('click', exportCustomDesign);
  $('import-custom-template-btn').addEventListener('click', () => $('custom-template-import-file').click());
  $('custom-template-import-file').addEventListener('change', async event => {
    const file = event.target.files?.[0];
    try { await importCustomDesign(file); }
    catch (error) { setProjectStatus(`Template import failed: ${error.message}`, true); }
    finally { event.target.value = ''; }
  });
  document.addEventListener('input', event => {
    if (event.target.closest('main') && !EXCLUDED_PROJECT_FIELDS.has(event.target.id)) scheduleProjectAutosave();
  });
  document.addEventListener('change', event => {
    if (event.target.closest('main') && !EXCLUDED_PROJECT_FIELDS.has(event.target.id)) scheduleProjectAutosave();
  });
  document.addEventListener('click', event => {
    if (event.target.closest('.video-template-choice,.background-choice,.caption-color-choice,.aspect-ratio-btn,.reciter-option,#speed-cycle-btn,.background-clip-actions')) scheduleProjectAutosave();
  });

  $('preview-sample-btn').setAttribute('aria-label','Audition selected reciter voice');
  $('selected-reciter-name').textContent = reciterById.get(selectedReciter)?.name || 'Mishary Rashid Alafasy';
  updatePreviewReciterName($('selected-reciter-name').textContent);
  $('voice-preview-audio').volume = Number($('preview-volume').value);
  initializeProjectWorkspace().catch(error => {
    console.error('Could not initialize project workspace:', error);
    setProjectStatus(`Workspace could not initialize: ${error.message}`, true);
    applyVideoTemplate(selectedTemplateId); setWallpaperPreview(); updateSurahInfo();
    loadVerses().then(updateCaptionPreview).catch(showError);
  });
})();
