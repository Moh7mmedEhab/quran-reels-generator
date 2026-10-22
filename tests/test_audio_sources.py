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
