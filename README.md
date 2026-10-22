# Quran Reels Generator v1.2

Release 1.2.0 of a light-theme Flask studio for rendering the complete Quran in Arabic with 20 reciters and 25 timed recordings. MoviePy creates MP4 output at 9:16, 16:9, or 1:1, with optional camera movement and crossfades. PIL renders Arabic captions with right-to-left shaping and bidirectional text processing. The app includes twenty-three wallpapers, sixteen caption colors, and four long-ayah wrap widths; users can upload image or video backgrounds or securely import a public image URL.

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

## Local image generation with ComfyUI

Image generation uses a ComfyUI server on the same machine by default. Install
ComfyUI, place a compatible checkpoint in `ComfyUI/models/checkpoints`, start
its server on port `8188`, then set these values in the project `.env` file (or
the server environment):

```dotenv
COMFYUI_BASE_URL=http://127.0.0.1:8188
COMFYUI_CHECKPOINT=Realistic_Vision_V6.0_NV_B1_fp16.safetensors
COMFYUI_TIMEOUT_SECONDS=300
```

The image generator has two main choices: local ComfyUI, which does not use an
image-service API, or Pollinations online. Pollinations online has a no-key
classic option and a separate authenticated API option. The classic
`image.pollinations.ai` option does not require an API key, but it is maintained
separately and its availability or model list may change. For the current
`gen.pollinations.ai` API, get a
server-side key from
[enter.pollinations.ai](https://enter.pollinations.ai);
set `POLLINATIONS_API_KEY` in `.env`. The model picker loads the live image
catalog and honors the models allowed by the configured key. Its default model
is `black-forest-labs/flux.1-schnell`; override it with
`POLLINATIONS_IMAGE_MODEL`. Pollinations requests spend Pollen according to the
selected model and key budget. The key is used only by the server and is not
exposed to the browser.

The checkpoint name must match a file installed in ComfyUI. The default is
`Realistic_Vision_V6.0_NV_B1_fp16.safetensors`, an SD 1.5 model. The generator
sends a built-in text-to-image workflow to ComfyUI's HTTP API and creates
portrait 576×1024, landscape 1024×576, or square 768×768 images. Generated images and
JSON metadata are saved under `<QURAN_REELS_OUTPUT_FOLDER>/generated-images`
and can be selected as video backgrounds. Use a persistent output volume in
deployments where the application filesystem is ephemeral. ComfyUI and the
chosen model run on your own hardware; generation speed depends on that hardware.

```bash
gunicorn --workers 1 --threads 4 --timeout 600 run:app
```

The renderer uses one background worker by default so concurrent exports do
not exhaust memory. Keep the output directory on persistent storage and apply
the retention and access controls required by your deployment.

The renderer uses bundled Amiri, Noto Naskh Arabic, Noto Sans Arabic, and Noto Kufi Arabic in regular and bold weights. The font picker includes live samples and a Reset Typography action. Uthmani Arabic text for all 114 surahs (6,236 ayahs) is included in `static/data/quran_uthmani.json`. The app fetches the chosen reciter's chapter recording and verse timing from MP3Quran.net, then advances one ayah at a time at its recitation boundary. This requires an internet connection. Twenty reciters provide 25 distinct timed recordings, grouped by reciter and labeled with the recording style and verified riwayah when available. A live preview can audition the selected range and update the displayed ayah with the recitation. The Image and Video background tabs include twenty-three still wallpapers and three silent MP4 loops generated locally from the credited bundled photos; users can also upload image or video backgrounds. Public JPEG, PNG, and WEBP image URLs can also be imported into a persistent gallery. URL imports reject private and local network destinations, pin DNS-resolved public IPs, recheck every redirect, limit downloads to 25 MB, verify image bytes, and preserve the original image file and detected dimensions. Source background audio is off unless enabled. The selected surah and ayah range must match the number of Arabic text lines entered when you edit the captions.

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
