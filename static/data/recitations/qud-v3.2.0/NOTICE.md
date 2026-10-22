# Recitation timing data attribution

This directory contains pinned catalog metadata and canonical ayah timestamps
from Qur'anic Universal Audio (QUD) release [v3.2.0](https://github.com/QUD-Technologies/quranic-universal-audio/releases/tag/v3.2.0).
QUD's timestamp, segmentation, and catalog work is licensed under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
Attribution: QUD Technologies and contributors, “Qur'anic Universal Audio,”
release v3.2.0, 2026-09-26.

Included recording datasets:

- `mohammed_siddiq_al_minshawi_mp3quran` — Hafs, Murattal, 6,236 ayahs;
  source MP3Quran chapter recordings; dataset SHA-256
  `c69b69cca4d2b320c1129149c0f81bf63390cb5bc8da4362c7f57d86af54d9ce`.
- `mohammed_siddiq_al_minshawi_mujawwad_mp3quran` — Hafs, Mujawwad,
  6,236 ayahs; source MP3Quran chapter recordings; dataset SHA-256
  `a50e04e53b3863162e408c46c8c1a93f65a7ff7c4166314603a0b94fc7429836`.
- `islam_sobhi_mp3quran` — Hafs, Murattal, 5,334 ayahs across 106 surahs;
  source MP3Quran chapter recordings; dataset SHA-256
  `6b6cc24872d936ce15f528da5979b24551441deeb6c5141d63181267e075b239`.

The source recitation recordings are not included here. They remain the property
of their reciters and upstream providers. Audio is fetched from the exact
MP3Quran URLs listed in each QUD catalog. QUD's CC BY 4.0 license applies to
its timestamps and metadata, not to the recordings.

The timing tier is verse-level. The app does not map QUD word indexes onto its
own Arabic text because the datasets use DigitalKhatt v2 tokenization, which
does not consistently match the app's Quran text tokenization.
