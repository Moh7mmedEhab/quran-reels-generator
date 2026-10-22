import math
import struct
import wave
from io import BytesIO

import pytest

from app import audio_sources
from app.quraa_data import RECITERS_BY_ID


class FakeAudioResponse:
    headers = {"Content-Length": "4"}

    def __init__(self):
        self._chunks = iter((b"test", b""))

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def read(self, _size=-1):
        return next(self._chunks)


TIMING_ROWS = (
    {"ayah": 28, "start_time": 520000, "end_time": 560060},
    {"ayah": 29, "start_time": 560060, "end_time": 601240},
    {"ayah": 30, "start_time": 601240, "end_time": 612620},
    {"ayah": 31, "start_time": 612620, "end_time": 642000},
)


def test_single_ayah_audio_ends_at_its_selected_end_not_after_next_ayah(monkeypatch, tmp_path):
    monkeypatch.setattr(audio_sources, "_get_surah_timings", lambda *_args: TIMING_ROWS)
    requested_urls = []

    def open_audio(request, timeout):
        requested_urls.append(request.full_url)
        assert timeout > 0
        return FakeAudioResponse()

    monkeypatch.setattr(audio_sources, "urlopen", open_audio)
    track = audio_sources.download_recitation(
        RECITERS_BY_ID["mishary_alafasy"], 18, 29, 29, tmp_path,
    )

    assert track.start == 560.06
    assert track.end == 601.24
    assert track.ayah_durations == [41.18]
    assert sum(track.ayah_durations) == pytest.approx(track.end - track.start)
    assert "018.mp3" in requested_urls[0]
    assert track.path.read_bytes() == b"test"


def test_multi_ayah_audio_ends_at_final_selected_ayah_boundary(monkeypatch, tmp_path):
    monkeypatch.setattr(audio_sources, "_get_surah_timings", lambda *_args: TIMING_ROWS)
    monkeypatch.setattr(audio_sources, "urlopen", lambda *_args, **_kwargs: FakeAudioResponse())

    track = audio_sources.download_recitation(
        RECITERS_BY_ID["mishary_alafasy"], 18, 29, 30, tmp_path,
    )

    assert track.start == 560.06
    assert track.end == 612.62
    assert track.ayah_durations == [41.18, 11.38]
    assert sum(track.ayah_durations) == pytest.approx(track.end - track.start)


@pytest.mark.parametrize("recording_id,expected_read_id", [
    ("abdul_basit_mujawwad", 51),
    ("husary_warsh", 120),
    ("husary_duri", 269),
    ("husary_qalun", 270),
])
def test_alternate_recordings_use_their_own_timing_read(monkeypatch, recording_id, expected_read_id):
    requested = []

    def fake_timings(surah, read_id):
        requested.append((surah, read_id))
        return (TIMING_ROWS[1],)

    monkeypatch.setattr(audio_sources, "_get_surah_timings", fake_timings)
    rows = audio_sources.get_recitation_timings(RECITERS_BY_ID[recording_id], 55, 29, 29)
    assert rows == [TIMING_ROWS[1]]
    assert requested == [(55, expected_read_id)]


def test_pinned_qud_catalogs_provide_verified_style_and_surah_coverage():
    from app.qud_timings import available_surahs, get_chapter_audio_url, get_recitation_timings

    murattal = RECITERS_BY_ID["minshawi"]
    mujawwad = RECITERS_BY_ID["minshawi_mujawwad"]
    islam = RECITERS_BY_ID["islam_sobhi"]
    assert "server10.mp3quran.net/minsh/055.mp3" in get_chapter_audio_url(
        murattal["timing_slug"], 55)
    assert "Almusshaf-Al-Mojawwad/055.mp3" in get_chapter_audio_url(
        mujawwad["timing_slug"], 55)
    assert 4 not in available_surahs(islam["timing_slug"])
    assert len(available_surahs(islam["timing_slug"])) == 106
    for recording in (murattal, mujawwad, islam):
        rows = get_recitation_timings(recording["timing_slug"], 55, 13, 14)
        assert [row["ayah"] for row in rows] == [13, 14]
        assert rows[0]["end_time"] <= rows[1]["start_time"]


def test_qud_ayah_stitcher_discards_unselected_audio_and_concatenates_only_windows(tmp_path):
    import numpy as np

    sample_rate = 44100
    samples = []
    for index in range(sample_rate * 2):
        seconds = index / sample_rate
        if .1 <= seconds < .4:
            value = int(10000 * math.sin(2 * math.pi * 440 * seconds))
        elif 1.6 <= seconds < 1.9:
            value = int(10000 * math.sin(2 * math.pi * 880 * seconds))
        else:
            value = 0
        samples.append(value)
    source = tmp_path / "source.wav"
    with wave.open(str(source), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    output_path = audio_sources._stitch_qud_ayah_windows(source, [
        {"start_time": 100, "end_time": 400},
        {"start_time": 1600, "end_time": 1900},
    ], tmp_path, "test_qari", 55)
    with wave.open(str(output_path), "rb") as rendered:
        assert rendered.getnchannels() == 2
        assert rendered.getframerate() == 44100
        assert rendered.getnframes() / rendered.getframerate() == pytest.approx(.6, abs=.02)
        frames = np.frombuffer(rendered.readframes(rendered.getnframes()), dtype="<i2")
    mono = frames.reshape(-1, 2).mean(axis=1)
    assert np.sqrt(np.mean(mono[: sample_rate // 4] ** 2)) > 4500
    assert np.sqrt(np.mean(mono[-sample_rate // 4:] ** 2)) > 4500


def test_qud_download_track_is_rebased_to_the_actual_stitched_audio(monkeypatch, tmp_path):
    sample_rate = 44100
    samples = []
    for index in range(sample_rate * 2):
        seconds = index / sample_rate
        if .1 <= seconds < .4 or 1.6 <= seconds < 1.9:
            value = int(10000 * math.sin(2 * math.pi * 440 * seconds))
        else:
            value = 0
        samples.append(value)
    encoded = BytesIO()
    with wave.open(encoded, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    source_bytes = encoded.getvalue()

    class Response:
        headers = {"Content-Length": str(len(source_bytes))}

        def __init__(self):
            self.chunks = iter((source_bytes, b""))

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def read(self, _size=-1):
            return next(self.chunks)

    from app import forced_alignment, word_alignment

    monkeypatch.setattr(audio_sources, "urlopen", lambda *_args, **_kwargs: Response())
    monkeypatch.setattr(audio_sources, "get_recitation_timings", lambda *_args: [
        {"ayah": 13, "start_time": 100, "end_time": 400},
        {"ayah": 14, "start_time": 1600, "end_time": 1900},
    ])
    monkeypatch.setattr(word_alignment, "get_chapter_word_timing", lambda *_args: pytest.fail(
        "QUD must stay paired with its pinned MP3Quran audio."))
    monkeypatch.setattr(forced_alignment, "forced_align_arabic_audio", lambda *_args: (
        None, "Local forced alignment is disabled."))
    track = audio_sources.download_recitation(
        RECITERS_BY_ID["minshawi"], 55, 13, 14, tmp_path,
        expected_ayahs=["الْحَمْدُ", "لِلَّهِ"],
    )
    assert track.start == 0
    assert track.end == pytest.approx(.6, abs=.02)
    assert track.ayah_durations == pytest.approx([.3, .3])
    assert track.timing_source == "qud_ayah"
    with wave.open(str(track.path), "rb") as rendered:
        assert rendered.getnframes() / rendered.getframerate() == pytest.approx(.6, abs=.02)
