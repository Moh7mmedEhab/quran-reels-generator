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


def test_source_chapter_is_downloaded_once_for_different_ayah_ranges(monkeypatch, tmp_path):
    monkeypatch.setattr(audio_sources, "_get_surah_timings", lambda *_args: TIMING_ROWS)
    requested_urls = []

    def open_audio(request, timeout):
        requested_urls.append(request.full_url)
        return FakeAudioResponse()

    monkeypatch.setattr(audio_sources, "urlopen", open_audio)
    first = audio_sources.download_recitation(
        RECITERS_BY_ID["mishary_alafasy"], 18, 29, 29, tmp_path,
    )
    second = audio_sources.download_recitation(
        RECITERS_BY_ID["mishary_alafasy"], 18, 30, 31, tmp_path,
    )

    assert len(requested_urls) == 1
    assert first.path == second.path
    assert first.persistent and second.persistent
    assert first.start == 560.06 and second.start == 601.24
    assert first.end == 601.24 and second.end == 642


def test_verified_word_selection_trims_audio_timeline_and_boundary_text(tmp_path):
    track = audio_sources.AudioTrack(
        tmp_path / "chapter.mp3", "https://audio.example/chapter.mp3", 10, 19,
        [5, 4],
        [
            [{"start": .2, "end": .6}, {"start": .9, "end": 1.3},
             {"start": 1.7, "end": 2.1}, {"start": 2.4, "end": 2.8},
             {"start": 3.3, "end": 3.8}],
            [{"start": .2, "end": .5}, {"start": 1.1, "end": 1.6},
             {"start": 2.1, "end": 2.5}, {"start": 3.0, "end": 3.4}],
        ],
        "quran_foundation_word", "Matching recording word timing.",
    )

    selected, text, word_ranges = audio_sources.select_audio_word_range(
        track, ["a b c d e", "f g h i"], ayah_start=10,
        start_word=3, end_word=2,
    )

    assert (selected.start, selected.end) == pytest.approx((11.7, 16.6))
    assert selected.ayah_durations == pytest.approx([3.3, 1.6])
    assert sum(selected.ayah_durations) == pytest.approx(selected.end - selected.start)
    assert text == ["c d e", "f g"]
    assert word_ranges == [(3, 5), (1, 2)]
    assert selected.word_timings[0][0]["start"] == 0
    assert selected.word_timings[1][-1]["end"] == pytest.approx(1.6)


def test_manual_word_selection_uses_explicit_offsets_and_marks_approximate(tmp_path):
    track = audio_sources.AudioTrack(
        tmp_path / "chapter.mp3", "https://audio.example/chapter.mp3", 10, 19,
        [5, 4], None, "mp3quran_ayah", "Ayah boundaries only.",
    )

    selected, text, _ranges = audio_sources.select_audio_word_range(
        track, ["a b c d e", "f g h i"], ayah_start=10,
        start_word=2, end_word=3, mode="manual",
        manual_start=4.25, manual_end=7.75,
    )

    assert (selected.start, selected.end) == pytest.approx((14.25, 17.75))
    assert selected.ayah_durations == pytest.approx([.75, 2.75])
    assert text == ["b c d e", "f g h"]
    assert selected.timing_source == "manual_audio_trim"
    assert "manually entered" in selected.timing_note


def test_partial_automatic_selection_rejects_unmatched_word_timing(tmp_path):
    track = audio_sources.AudioTrack(
        tmp_path / "chapter.mp3", "https://audio.example/chapter.mp3", 0, 5,
        [5], None, "mp3quran_ayah", "Ayah boundaries only.",
    )
    with pytest.raises(audio_sources.AudioSourceError, match="Verified word timestamps are unavailable"):
        audio_sources.select_audio_word_range(
            track, ["a b c"], ayah_start=1, start_word=2, end_word=3,
        )


def test_chapter_only_recording_keeps_full_surah_and_marks_estimated_captions(monkeypatch, tmp_path):
    requests = []

    def open_audio(request, timeout):
        requests.append(request.full_url)
        assert timeout > 0
        return FakeAudioResponse()

    monkeypatch.setattr(audio_sources, "urlopen", open_audio)
    monkeypatch.setattr(audio_sources, "probe_audio_duration", lambda _path: 90.0)
    reciter = RECITERS_BY_ID["salman_alotaibi"]
    verses = ["بِسْمِ اللَّهِ", "الْحَمْدُ لِلَّهِ", "الرَّحْمَٰنِ",
              "مَالِكِ يَوْمِ الدِّينِ", "إِيَّاكَ نَعْبُدُ", "اهْدِنَا", "صِرَاطَ الَّذِينَ"]

    track = audio_sources.download_recitation(
        reciter, 1, 1, 7, tmp_path, expected_ayahs=verses,
    )

    assert requests == ["https://cdn.mp3quran.net/audio/salman-otaibi/r1/001.mp3"]
    assert track.start == 0
    assert track.end == 90
    assert len(track.ayah_durations) == 7
    assert sum(track.ayah_durations) == pytest.approx(90)
    assert track.timing_source == "chapter_estimate"
    assert "approximate" in track.timing_note
    assert "Partial ayah ranges are disabled" in track.timing_note
    assert track.path.read_bytes() == b"test"


def test_mishary_tarawih_recording_uses_its_explicit_surah_map(monkeypatch, tmp_path):
    requests = []

    def open_audio(request, timeout):
        requests.append(request.full_url)
        assert timeout > 0
        return FakeAudioResponse()

    monkeypatch.setattr(audio_sources, "urlopen", open_audio)
    monkeypatch.setattr(audio_sources, "probe_audio_duration", lambda _path: 49.0)
    verses = ["بِسْمِ اللَّهِ", "الْحَمْدُ لِلَّهِ", "الرَّحْمَٰنِ",
              "مَالِكِ يَوْمِ الدِّينِ", "إِيَّاكَ نَعْبُدُ", "اهْدِنَا", "صِرَاطَ الَّذِينَ"]

    track = audio_sources.download_recitation(
        RECITERS_BY_ID["mishary_alafasy_tarawih_1427"], 1, 1, 7, tmp_path,
        expected_ayahs=verses,
    )

    assert requests == [
        "https://media.assabile.com/assabile/recitations_7892537823/mp3/"
        "mishary-rashid-alafasy/mishary-rashid-alafasy-001-al-fatiha-21471-7383.mp3"
    ]
    assert track.start == 0
    assert track.end == 49
    assert len(track.ayah_durations) == 7
    assert track.timing_source == "chapter_estimate"
    assert "approximate" in track.timing_note


@pytest.mark.parametrize(("reciter_id", "surah_number"), [
    ("salman_alotaibi", 1),
    ("mishary_alafasy_tarawih_1427", 1),
    ("mishary_alafasy_dorai", 97),
])
def test_chapter_only_recording_rejects_partial_ranges_before_fetch(
        monkeypatch, tmp_path, reciter_id, surah_number):
    monkeypatch.setattr(audio_sources, "urlopen", lambda *_args, **_kwargs: pytest.fail(
        "A chapter-only recording must not fetch audio for a partial ayah selection"))
    with pytest.raises(audio_sources.AudioSourceError, match="complete Surah"):
        audio_sources.download_recitation(
            RECITERS_BY_ID[reciter_id], surah_number, 2, 3, tmp_path,
            expected_ayahs=["الْحَمْدُ", "لِلَّهِ"],
        )


def test_mishary_dorai_recording_uses_its_own_source_url_and_reports_coverage():
    from app.audio_sources import get_audio_url

    reciter = RECITERS_BY_ID["mishary_alafasy_dorai"]
    assert get_audio_url(reciter, 12) == "https://cdn.mp3quran.net/audio/mishary-alafasy/r2/012.mp3"
    assert reciter["riwayah"] == "Al-Duri 'an al-Kisa'i"
    assert reciter["available_surah_numbers"] == [12, 14, 25, 87, 97, 99]


def test_mishary_california_murattal_is_a_distinct_partial_source_catalog():
    from app.audio_sources import get_audio_url

    main = RECITERS_BY_ID["mishary_alafasy"]
    alternate = RECITERS_BY_ID["mishary_alafasy_california"]
    assert alternate["name"] == "Mishary Rashid Alafasy"
    assert alternate["name_ar"] == "مشاري بن راشد العفاسي"
    assert alternate["style"] == "Murattal"
    assert alternate["riwayah"] == "Hafs 'an Asim"
    assert alternate["timing_provider"] == "chapter_only"
    assert alternate["read_id"] is None
    assert alternate["recording_name"] == "Hafs 'an Asim - California Murattal (1430 AH)"
    assert alternate["available_surah_numbers"] == [number for number in range(1, 115) if number != 44]
    assert len(alternate["audio_urls_by_surah"]) == 113
    assert get_audio_url(alternate, 1) == (
        "https://media.assabile.com/assabile/recitations_7892537823/mp3/"
        "mishary-rashid-alafasy/mishary-rashid-alafasy-001-al-fatiha-21377-648.mp3"
    )
    assert get_audio_url(alternate, 55) == (
        "https://media.assabile.com/assabile/recitations_7892537823/mp3/"
        "mishary-rashid-alafasy/mishary-rashid-alafasy-055-ar-rahman-21385-864.mp3"
    )
    with pytest.raises(audio_sources.AudioSourceError, match="no verified audio"):
        get_audio_url(alternate, 44)
    assert get_audio_url(alternate, 114) != get_audio_url(main, 114)


def test_mishary_california_download_uses_its_own_per_surah_recording(monkeypatch, tmp_path):
    requests = []

    def open_audio(request, timeout):
        requests.append(request.full_url)
        assert timeout > 0
        return FakeAudioResponse()

    monkeypatch.setattr(audio_sources, "urlopen", open_audio)
    monkeypatch.setattr(audio_sources, "probe_audio_duration", lambda _path: 83.0)
    verses = ["بِسْمِ اللَّهِ", "الْحَمْدُ لِلَّهِ", "الرَّحْمَٰنِ",
              "مَالِكِ يَوْمِ الدِّينِ", "إِيَّاكَ نَعْبُدُ", "اهْدِنَا", "صِرَاطَ الَّذِينَ"]

    track = audio_sources.download_recitation(
        RECITERS_BY_ID["mishary_alafasy_california"], 1, 1, 7, tmp_path,
        expected_ayahs=verses,
    )

    assert requests == [
        "https://media.assabile.com/assabile/recitations_7892537823/mp3/"
        "mishary-rashid-alafasy/mishary-rashid-alafasy-001-al-fatiha-21377-648.mp3"
    ]
    assert track.start == 0
    assert track.end == 83
    assert len(track.ayah_durations) == 7
    assert track.timing_source == "chapter_estimate"
    assert "approximate" in track.timing_note


def test_salman_surah_16_uses_verified_way2quran_override():
    from app.audio_sources import get_audio_url

    reciter = RECITERS_BY_ID["salman_alotaibi"]
    assert 16 in reciter["available_surah_numbers"]
    assert len(reciter["available_surah_numbers"]) == 76
    assert get_audio_url(reciter, 16) == (
        "https://media.way2quran.com/slman-al-atyby/hafs-an-asim/016.mp3"
    )
    assert get_audio_url(reciter, 1) == (
        "https://cdn.mp3quran.net/audio/salman-otaibi/r1/001.mp3"
    )


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
