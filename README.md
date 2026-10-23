# Quran Reels Generator v1.7

Release 1.7.0 constrains scene resizing to the effective selected audio range by default, keeps later scene durations intact, and exposes explicit overrun behavior when bounds are unlocked. Scene word allocations can be adjusted with a number field and step buttons after unlocking. New centered layouts use a 50% vertical caption center, and the background gallery includes additional credited high-resolution stills and silent motion loops. Existing saved layout values are preserved.

This light-theme Flask studio renders Quran reels in Arabic with 22 reciter profiles and 31 recordings. MoviePy creates MP4 output at 9:16, 16:9, or 1:1, with optional camera movement and crossfades. PIL renders Arabic captions with right-to-left shaping and bidirectional text processing. Optional Saheeh International English translations can be shown beneath each ayah. The app includes twenty-three wallpapers, sixteen caption colors, and four long-ayah wrap widths; users can upload image or video backgrounds or securely import a public image URL.

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

The renderer uses bundled Amiri, Noto Naskh Arabic, Noto Sans Arabic, and Noto Kufi Arabic in regular and bold weights. The font picker includes live samples and a Reset Typography action. Uthmani Arabic text for all 114 surahs (6,236 ayahs) is included in `static/data/quran_uthmani.json`. The app fetches the selected reciter's recording and matching ayah timing, then advances each caption at its recitation boundary. Twenty-two reciter profiles provide 31 recordings, grouped by reciter and labeled with their verified edition, style, and riwayah. Mishary Alafasy has a full Hafs Murattal, the 113-surah California Murattal edition, 27 Tarawih surahs, and six Al-Duri surahs. Salman Al-Utaybi has 76 verified surahs. Recordings without matching ayah timestamps can only be selected by complete Surah, and the app labels their caption timing as approximate. Minshawi Murattal, Minshawi Mujawwad, and Islam Sobhi use pinned QUD v3.2.0 verse timing files paired with their MP3Quran source URLs; selected ayah windows are clipped and stitched so unselected recitation is excluded. The other existing recordings retain their MP3Quran timing lookups. See [the timing data attribution](static/data/recitations/qud-v3.2.0/NOTICE.md) and [audio source and reuse notes](static/assets/audio/README.md). A live preview can audition the selected range and update the displayed ayah with the recitation. English translations are optional, default off, and use Saheeh International through AlQuranCloud with a local chapter cache. The Image and Video background tabs include twenty-four still wallpapers and four silent MP4 loops generated locally from the credited bundled photos; the Midnight Coast still is 2000 × 3009, and its silent motion loop is H.264 at 1440 × 2560 and 24 fps. Both derive from an existing Uran Wang ocean photo under the Unsplash License, documented with dimensions and source in `static/assets/backgrounds/SOURCES.md`. Users can also upload image or video backgrounds. Public JPEG, PNG, and WEBP image URLs can also be imported into a persistent gallery. URL imports reject private and local network destinations, pin DNS-resolved public IPs, recheck every redirect, limit downloads to 25 MB, verify image bytes, and preserve the original image file and detected dimensions. Source background audio is off unless enabled. The ayah text editor accepts one non-empty Arabic line per selected ayah. Individual scene display text can be shortened, edited, or left intentionally blank without changing canonical Quran source data.

The **Auto-Split Tall Ayahs** action measures shaped Arabic using the selected font, size, output ratio, resolution, text width, and caption style. It creates editable single-line scenes, keeps at least three Arabic words per scene when a readable division allows it, preserves settings on matching chunks, and asks before replacing other edited arrangements. Word-timed recitations follow validated word boundaries; other recitations keep continuous audio with the existing approximate scene timing.

Surah and ayah decorations start disabled in a new studio project. When enabled, each can use a separate font, style, color, opacity, alignment, above/below placement, and X/Y offset. The caption group has its own X/Y position sliders, and each element has a position reset that leaves other settings intact. Position coordinates scale to the selected aspect ratio and resolution. The background color overlay remains disabled by default and starts with black at 0% opacity.

For optional word-synchronized phrase scenes, configure Quran Foundation Content API credentials and a matched chapter-reciter ID map:

    export QURAN_FOUNDATION_CLIENT_ID="your-client-id"
    export QURAN_FOUNDATION_CLIENT_SECRET="your-client-secret"
    export QURAN_REELS_QF_RECITER_MAP='{"mishary_alafasy":123}'

The map must use Quran Foundation chapter-reciter IDs for the matching selected reciter. Credentials remain server-side. The integration checks canonical Uthmani words and segment counts against the local Quran text; missing, invalid, or mismatched timings fall back to ayah-level timing and are reported. As an optional local fallback, install WhisperX and set `QURAN_REELS_FORCE_ALIGN=1`. The Arabic CTC aligner maps times against a normalized copy of the known Quran words and keeps the original text for display. It uses CUDA when available; set `QURAN_REELS_WHISPERX_DEVICE=cpu` or `cuda` to choose explicitly, and `QURAN_REELS_WHISPERX_MODEL` to override WhisperX's Arabic alignment model. WhisperX and its model weights are not part of the default requirements because they add a large PyTorch/model download. If the local aligner is absent, fails, omits words, or reports low confidence, complete ayahs use ayah-level timing. Edited Arabic display text stays separate from the canonical source and remains renderable. Scenes whose words no longer map to the source skip word alignment, use a clearly labeled approximate interval, and show a non-blocking warning that spoken audio may differ. Translation is cleared and marked for review rather than invented. An empty ayah-level text line is rejected with clear guidance; an intentionally blank individual scene remains supported.

The scene editor groups captions by a configurable word count and submits those exact displayed scenes as the render source of truth. Split, merge, and per-scene word-count edits preserve the original Quran words. Every exported phrase boundary follows validated word timestamps from the selected recitation. If those timestamps are unavailable, an unsplit ayah uses its ayah timing and split or edited scenes use labeled approximate durations. The export preserves the exact displayed scene text and canonical Quran source data remains unchanged.

Generated MP4s are saved in `static/outputs/` and downloaded through the app. Downloads use the editable video title as their sanitized filename. Treat this folder as user data when deploying; add retention and access controls appropriate to your deployment.

## Optional YouTube and TikTok publishing

Publishing is a separate, explicit action shown after a full-quality render. It
reuses that rendered MP4 and the existing bilingual surah metadata. YouTube
starts as **Private**. TikTok starts with **Upload to inbox as a draft**; the
user must open TikTok, review the draft, and finish publishing there. Rendering
and downloading remain available when publishing is not configured.

The app does not have user accounts. Connected credentials are isolated by a
random id in each signed browser session and stored in a private SQLite database
under `instance/` (or `QURAN_REELS_PUBLISHER_DB`). OAuth access and refresh
tokens are Fernet-encrypted at rest. Configure a stable `QURAN_REELS_SECRET_KEY`
and a separately managed `QURAN_REELS_TOKEN_ENCRYPTION_KEY`; keep both outside
Git, and back up the encryption key securely. A new encryption key cannot read
tokens encrypted with the old key. Set `QURAN_REELS_COOKIE_SECURE=1` when the
site is served over HTTPS. Use the documented one-worker Gunicorn setup because
render and publishing workers are process-local. Upload status is stored in
SQLite and survives browser refreshes. Upload work continues while the app
process is running; an application restart interrupts active transfers, so
refresh provider status before retrying an interrupted operation.

### YouTube setup

1. Create or select a Google Cloud project and enable **YouTube Data API v3**.
2. Configure the OAuth consent screen and add the intended test users while the
   consent screen is in testing.
3. Create an OAuth **Web application** client. Add the exact callback URL
   `https://your-domain.example/oauth/youtube/callback` as an authorized redirect
   URI. Google accepts loopback HTTP redirect URIs for local development; use
   the exact URI configured in the Cloud Console.
4. Set `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REDIRECT_URI`.
   The app requests `youtube.upload` to upload videos and `youtube.readonly` to
   identify the authorized channel. The YouTube API project may need Google's
   API compliance review before uploads work for general users.
5. Optionally set `YOUTUBE_DEFAULT_CATEGORY_ID` (defaults to `10`, Music).

### TikTok setup

1. Register a web app in the TikTok for Developers portal. Add **Login Kit** and
   **Content Posting API**, then register the exact HTTPS redirect URL
   `https://your-domain.example/oauth/tiktok/callback` in Login Kit.
2. Add/obtain `user.info.basic` and `video.upload` scopes. Set
   `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, and `TIKTOK_REDIRECT_URI`.
   TikTok may require approval before these scopes can be used by the app.
3. The default inbox upload sends the MP4 to TikTok and reports when it is ready
   in the creator's inbox. The draft endpoint does not accept caption metadata;
   the user can review the generated caption in this app and must add or adjust
   it while finishing the TikTok workflow.
4. Direct posting is off by default. To enable its UI, first configure Direct
   Post in the Content Posting API, receive approval for `video.publish`, and
   complete any required TikTok audit; then set `TIKTOK_DIRECT_POST_ENABLED=1`.
   Reconnect the account so it grants the new scope. TikTok requires the app to
   query the creator's current privacy options; the UI uses those options and
   defaults to `SELF_ONLY`. Unaudited clients are restricted by TikTok to
   private visibility.

Create a Fernet key and place it in your deployment secret manager (not in the
repository):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

The matching variable placeholders are in `.env.example`. Real Google/TikTok
client credentials, registered callback domains, approved scopes, and a real
authorized test account are required for external uploads; automated tests use
mock provider responses and do not publish videos.

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
