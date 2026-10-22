# Bundled video backgrounds

This folder contains three silent, six-second MP4 loops for the Video
background gallery. They are generated locally from the existing, credited
photo assets documented in `../backgrounds/SOURCES.md`.

Rebuild the files with:

```bash
python scripts/build_background_video_templates.py
```

The script uses the installed FFmpeg and local background files. It does not
download media.
