# Quran Reels Generator v1.3

Release 1.3.0 of a light-theme Flask studio for rendering the complete Quran in Arabic with 21 reciter profiles and 27 recordings. MoviePy creates MP4 output at 9:16, 16:9, or 1:1, with optional camera movement and crossfades. PIL renders Arabic captions with right-to-left shaping and bidirectional text processing. Optional Saheeh International English translations can be shown beneath each ayah. The app includes twenty-three wallpapers, sixteen caption colors, and four long-ayah wrap widths; users can upload image or video backgrounds or securely import a public image URL.

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

The local launcher keeps Flask's debugger and reloader off by default. Set
`FLASK_DEBUG=1` only for local development. `run.py` also exports the WSGI
application as `run:app`; for a Linux deployment, set a stable, private
`QURAN_REELS_SECRET_KEY` and run it behind a TLS-terminating reverse proxy:

## Image generation

The AI Image Generator offers two Pollinations methods. **Pollinations API**
uses the current `gen.pollinations.ai` endpoint and requires a server-side key
from [enter.pollinations.ai](https://enter.pollinations.ai), configured as
`POLLINATIONS_API_KEY` in `.env`. It loads the live image-model catalog; costs
depend on the selected model and the key's budget. The key stays on the server.

**Pollinations Classic · no API key** uses Pollinations' Free API Classic image
endpoint (`image.pollinations.ai`) with its default Flux model. It needs no
Pollinations key or account; availability and rate limits depend on that free
service. This path is selected by default so image generation works without
configuring a key.

Both methods use the prompt as entered and support portrait 576×1024, landscape
1024×576, and square 768×768 formats. Generated image files and JSON metadata
are saved under `<QURAN_REELS_OUTPUT_FOLDER>/generated-images` and can be
selected as video backgrounds. Use persistent storage in deployments where
the application filesystem is ephemeral. The backend still accepts a local
ComfyUI provider for existing direct integrations; the image page presents the
two Pollinations choices above.

```bash
gunicorn --workers 1 --threads 4 --timeout 600 run:app
```

The renderer uses one background worker by default so concurrent exports do
not exhaust memory. Keep the output directory on persistent storage and apply
the retention and access controls required by your deployment.

The renderer uses bundled Amiri, Noto Naskh Arabic, Noto Sans Arabic, and Noto Kufi Arabic in regular and bold weights. The font picker includes live samples and a Reset Typography action. Uthmani Arabic text for all 114 surahs (6,236 ayahs) is included in `static/data/quran_uthmani.json`. The app fetches the selected reciter's recording and matching ayah timing, then advances each caption at its recitation boundary. Twenty-one reciter profiles provide 27 recordings, grouped by reciter and labeled with their verified style and riwayah. Minshawi Murattal, Minshawi Mujawwad, and Islam Sobhi use pinned QUD v3.2.0 verse timing files paired with their MP3Quran source URLs; selected ayah windows are clipped and stitched so unselected recitation is excluded. The other existing recordings retain their MP3Quran timing lookups. See [the timing data attribution](static/data/recitations/qud-v3.2.0/NOTICE.md). A live preview can audition the selected range and update the displayed ayah with the recitation. English translations are optional, default off, and use Saheeh International through AlQuranCloud with a local chapter cache. The Image and Video background tabs include twenty-three still wallpapers and three silent MP4 loops generated locally from the credited bundled photos; users can also upload image or video backgrounds. Public JPEG, PNG, and WEBP image URLs can also be imported into a persistent gallery. URL imports reject private and local network destinations, pin DNS-resolved public IPs, recheck every redirect, limit downloads to 25 MB, verify image bytes, and preserve the original image file and detected dimensions. Source background audio is off unless enabled. The selected surah and ayah range must match the number of Arabic text lines entered when you edit the captions.

Surah and ayah decorations start disabled in a new studio project. When enabled, each can use a separate font, style, color, opacity, alignment, above/below placement, and X/Y offset. The caption group has its own X/Y position sliders, and each element has a position reset that leaves other settings intact. Position coordinates scale to the selected aspect ratio and resolution. The background color overlay remains disabled by default and starts with black at 0% opacity.

For optional word-synchronized phrase scenes, configure Quran Foundation Content API credentials and a matched chapter-reciter ID map:

    export QURAN_FOUNDATION_CLIENT_ID="your-client-id"
    export QURAN_FOUNDATION_CLIENT_SECRET="your-client-secret"
    export QURAN_REELS_QF_RECITER_MAP='{"mishary_alafasy":123}'

The map must use Quran Foundation chapter-reciter IDs for the matching selected reciter. Credentials remain server-side. The integration checks canonical Uthmani words and segment counts against the local Quran text; missing, invalid, or mismatched timings fall back to ayah-level timing and are reported. As an optional local fallback, install WhisperX and set `QURAN_REELS_FORCE_ALIGN=1`. The Arabic CTC aligner maps times against a normalized copy of the known Quran words and keeps the original text for display. It uses CUDA when available; set `QURAN_REELS_WHISPERX_DEVICE=cpu` or `cuda` to choose explicitly, and `QURAN_REELS_WHISPERX_MODEL` to override WhisperX's Arabic alignment model. WhisperX and its model weights are not part of the default requirements because they add a large PyTorch/model download. If the local aligner is absent, fails, omits words, or reports low confidence, complete ayahs use ayah-level timing. An edited multi-scene ayah export is rejected with an actionable message instead of silently replacing the user's segments with the full ayah. Custom caption text disables word alignment because it cannot be safely mapped to canonical word indexes.

The scene editor groups captions by a configurable word count and submits those exact displayed scenes as the render source of truth. Split, merge, and per-scene word-count edits preserve the original Quran words. Every exported phrase boundary follows validated word timestamps from the selected recitation. If those timestamps are unavailable, an unsplit ayah uses its ayah timing, while an edited multi-scene ayah export is refused rather than showing the wrong full-ayah caption or guessing phrase durations.

Generated MP4s are saved in `static/outputs/` and downloaded through the app. Downloads use the editable video title as their sanitized filename. Treat this folder as user data when deploying; add retention and access controls appropriate to your deployment.

## HTTP API

GET /api/version returns the application version. GET /api/youtube-metadata?surah=55&start=13&end=14&reciter_id=mishary_alafasy returns editable Arabic and English YouTube titles, descriptions, tags, and hashtags. GET /api/reciters/<id>/timings returns ayah boundaries and validated word segments when the optional Quran Foundation setup is active. POST /api/generate accepts multipart form data, including an optional video_title and encoder. Renders are asynchronous: poll /api/jobs/<job_id> and download from its download_url.

NVENC encodes H.264 exports when supported by the installed GPU and FFmpeg. MoviePy scene composition still runs on the CPU. Auto mode falls back to x264 if hardware encoding is unavailable or fails.

## Rendering benchmark

A controlled 4-second, two-ayah portrait export was profiled before and after
the MoviePy composite optimization. Both runs used 1080×1920, 30 fps, the
balanced preset, x264 at CRF 23, the same visual effects, and the same audio.
Under the same cProfile instrumentation, render time fell from 23.019 seconds
to 11.795 seconds (48.7% less). Both MP4 files were 304,797 bytes. FFmpeg
decoded all 120 video frames to identical pixel hashes and the AAC audio to the
same PCM hash; ffprobe reported matching resolution, frame rate, duration,
H.264/AAC streams, and file size. This is one short controlled sample, so
longer reels and different effects can have different speedups. The host had no
available NVENC or Intel Quick Sync device, so the benchmark used the software
x264 fallback.

To force an export through NVIDIA NVENC from a terminal, submit a render job and poll its returned job ID:

```bash
curl -sS -X POST 'http://127.0.0.1:5000/api/generate' \
  -F 'encoder=nvidia' -F 'surah=55' -F 'ayah_start=13' -F 'ayah_end=13'
curl -sS 'http://127.0.0.1:5000/api/jobs/<job_id>'
```

Replace port `5000` with the port used by your running server, then replace `<job_id>` with the ID returned by the first request. `encoder=nvidia` fails with a capability error if NVENC is unavailable; `encoder=auto` tries NVIDIA and falls back to CPU x264.

Bundled video loops can be rebuilt from the credited local stills with `python scripts/build_background_video_templates.py`; the script uses the installed FFmpeg and does not access the network.

The original API endpoint overview remains accurate for Quran text, reciter catalogs, wallpaper previews, and render form fields. The asynchronous job lifecycle, optional word-timing fields, metadata endpoint, encoder selection, and title-based downloads are described above.

## Tests

```bash
pytest
```

Arabic shaping tests skip when the shaping packages are not installed; install the full requirements to run them.
