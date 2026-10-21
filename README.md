# Quran Reels & Shorts Generator

A light-theme Flask studio for rendering the complete Quran in Arabic with a choice of 20 qaris. MoviePy creates MP4 output at 9:16, 16:9, or 1:1, with a gentle Ken Burns zoom and optional crossfades. PIL renders Arabic captions after right-to-left shaping and bidirectional text processing. Twenty generated wallpapers, sixteen caption colors, and four long-ayah wrap widths are included; users can also upload a still image.

## Run locally

1. Use Python 3.10 or newer and install FFmpeg.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   . .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
3. Start the Flask app:

   ```bash
   python run.py
   ```
4. Open http://127.0.0.1:5000.

The renderer uses `static/assets/NotoNaskhArabic-Regular.ttf`. Uthmani Arabic text for all 114 surahs (6,236 ayahs) is included in `static/data/quran_uthmani.json`. The app fetches the chosen qari's chapter recording and verse timing from MP3Quran.net, then advances one ayah at a time at its recitation boundary. This requires an internet connection. A live preview can audition the selected range and update the displayed ayah with the recitation. You can upload a custom wallpaper; audio always comes from the selected qari. The selected surah and ayah range must match the number of Arabic text lines entered when you edit the captions.

Generated MP4s are saved in `static/outputs/` and downloaded through the app. Treat this folder as user data when deploying; add retention and access controls appropriate to your deployment.

## HTTP API

`GET /api/surahs` returns all surah metadata, `GET /api/verses?surah=55&start=13&end=14` returns Arabic text, `GET /api/reciters` returns the 20-reciter catalog, and `GET /api/backgrounds` lists the presets. `GET /api/backgrounds/<theme>/preview?ratio=9:16` returns the wallpaper crop used by export. `GET /api/reciters/<id>/timings?surah=55&start=13&end=14` returns synchronized ayah boundaries. `POST /api/generate` accepts multipart form data (`surah`, `ayah_start`, `ayah_end`, `reciter_id`, `aspect_ratio`, `theme`, `transition`, `caption_style`, `caption_color`, `wrap_width`, `speed`, plus optional `ayah_text` and `background`). Successful renders return a JSON object with dimensions, duration, audio presence, and `download_url`.

## Tests

```bash
pytest
```

Arabic shaping tests skip when the shaping packages are not installed; install the full requirements to run them.
