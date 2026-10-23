"""Verified Quran recordings with source-specific coverage and timing metadata."""

import json
from pathlib import Path

SOURCE = "MP3Quran.net"
SOURCE_CATALOG_URL = "https://www.mp3quran.net/eng/api/"
TIMING_API_URL = "https://www.mp3quran.net/eng/timing-api"
ALL_SURAHS = tuple(range(1, 115))
ISLAM_SOBHI_QUD_SURAHS = (*range(1, 4), 5, 6, 8, *range(10, 37), 38,
                          *range(41, 45), *range(46, 65), *range(66, 115))
QUD_TIMING_SOURCE = "Qur'anic Universal Audio v3.2.0"
QUD_TIMING_SOURCE_URL = "https://github.com/QUD-Technologies/quranic-universal-audio/releases/tag/v3.2.0"
ASSABILE_TARAWIH_PAGE = "https://www.assabile.com/mishary-rashid-alafasy/moshaf/hafs-tarawih"
ASSABILE_MISHARY_CALIFORNIA_CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "static" / "data" / "recitations" / "mishary_alafasy_california_catalog.json"
)


def _load_assabile_mishary_california_catalog():
    try:
        catalog = json.loads(ASSABILE_MISHARY_CALIFORNIA_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("The verified Mishary Alafasy California recording catalog is unavailable.") from exc
    urls = catalog.get("audio_urls_by_surah") if isinstance(catalog, dict) else None
    if (not isinstance(urls, dict)
            or set(urls) != {str(number) for number in ALL_SURAHS if number != 44}
            or any(not isinstance(url, str) or not url.startswith("https://media.assabile.com/")
                   for url in urls.values())):
        raise RuntimeError("The Mishary Alafasy California recording catalog has invalid audio coverage.")
    return catalog


ASSABILE_MISHARY_CALIFORNIA_CATALOG = _load_assabile_mishary_california_catalog()
ASSABILE_MISHARY_CALIFORNIA_URLS = ASSABILE_MISHARY_CALIFORNIA_CATALOG["audio_urls_by_surah"]
ASSABILE_MISHARY_TARAWIH_URLS = {
    1: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-001-al-fatiha-21471-7383.mp3",
    32: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-032-as-sajda-21469-3746.mp3",
    33: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-033-al-ahzab-21467-1696.mp3",
    34: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-034-saba-21466-4638.mp3",
    35: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-035-fater-21468-9043.mp3",
    36: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-036-ya-sin-21470-6345.mp3",
    37: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-037-as-safaat-21465-4744.mp3",
    38: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-038-sad-21464-8396.mp3",
    43: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-043-az-zoukhrouf-21463-9304.mp3",
    44: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-044-ad-doukhan-21461-2591.mp3",
    50: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-050-qaf-21460-4527.mp3",
    55: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-055-ar-rahman-21458-6330.mp3",
    56: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-056-al-waqi-a-21462-8864.mp3",
    57: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-057-al-hadid-21459-7168.mp3",
    67: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-067-al-moulk-21457-9771.mp3",
    68: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-068-al-qalam-21456-97.mp3",
    69: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-069-al-haqqah-21455-5917.mp3",
    70: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-070-al-maarij-21454-5772.mp3",
    78: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-078-an-naba-21453-5428.mp3",
    79: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-079-an-nazi-at-21445-3841.mp3",
    80: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-080-abasa-21446-2097.mp3",
    81: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-081-at-takwir-21447-996.mp3",
    82: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-082-al-infitar-21448-1741.mp3",
    83: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-083-al-moutaffifin-21449-6854.mp3",
    84: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-084-al-inshiqaq-21450-8234.mp3",
    85: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-085-al-bourouj-21451-552.mp3",
    86: "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/mishary-rashid-alafasy-086-at-tariq-21452-4918.mp3",
}


def _record(record_id, reciter_id, name, recording_name, reading_style, riwayah,
            read_id, audio_base_url, *, available_surahs=ALL_SURAHS,
            timing_slug=None, timing_source=SOURCE, timing_source_url=TIMING_API_URL,
            name_ar=None, timing_provider=None, source_reciter_id=None,
            source_recording_id=None, source_url=None, recording_page_url=None,
            source=SOURCE, usage_rights=None, audio_url_template="auto",
            audio_urls_by_surah=None, audio_url_overrides_by_surah=None,
            audio_provider_overrides_by_surah=None):
    """Keep audio, coverage, source and timing metadata together."""
    timing_provider = timing_provider or ("qud" if timing_slug else "mp3quran")
    return {
        "id": record_id,
        "group_id": reciter_id,
        "name": name,
        "name_ar": name_ar or RECITER_NAMES_AR[reciter_id],
        "recording_name": recording_name,
        "style": reading_style,
        "riwayah": riwayah,
        "read_id": read_id,
        "source_reciter_id": source_reciter_id,
        "source_recording_id": source_recording_id,
        "audio_base_url": audio_base_url,
        "audio_url_template": (f"{audio_base_url}{{surah:03d}}.mp3"
                                if audio_url_template == "auto" else audio_url_template),
        "audio_urls_by_surah": ({str(number): url for number, url in audio_urls_by_surah.items()}
                                 if audio_urls_by_surah else None),
        "audio_url_overrides_by_surah": (
            {str(number): url for number, url in audio_url_overrides_by_surah.items()}
            if audio_url_overrides_by_surah else None
        ),
        "audio_provider_overrides_by_surah": (
            {str(number): provider for number, provider in audio_provider_overrides_by_surah.items()}
            if audio_provider_overrides_by_surah else None
        ),
        "audio_format": "mp3",
        "audio_delivery": "per_surah",
        "timing_granularity": "surah_only" if timing_provider == "chapter_only" else "ayah",
        "supports_ayah_selection": timing_provider != "chapter_only",
        "available_surah_numbers": list(available_surahs),
        "available_surahs": len(available_surahs),
        "source": source,
        "source_url": source_url or SOURCE_CATALOG_URL,
        "recording_page_url": recording_page_url,
        "usage_rights": usage_rights or "MP3Quran.net terms apply; no separate redistribution license is stated.",
        "timing_provider": timing_provider,
        "timing_slug": timing_slug,
        "timing_source": timing_source,
        "timing_source_url": timing_source_url,
    }


RECITER_NAMES_AR = {
    "abdul_basit": "عبدالباسط عبدالصمد",
    "abdullah_basfar": "عبدالله بصفر",
    "abdur_rahman_sudais": "عبدالرحمن السديس",
    "abu_bakr_shatri": "أبو بكر الشاطري",
    "ahmed_ajmi": "أحمد العجمي",
    "ali_hudhaify": "علي الحذيفي",
    "fares_abbad": "فارس عباد",
    "hani_rifai": "هاني الرفاعي",
    "husary": "محمود خليل الحصري",
    "idris_abkar": "إدريس أبكر",
    "islam_sobhi": "إسلام صبحي",
    "maher_muaiqly": "ماهر المعيقلي",
    "minshawi": "محمد صديق المنشاوي",
    "mishary_alafasy": "مشاري بن راشد العفاسي",
    "muhammad_ayyub": "محمد أيوب",
    "mustafa_ismail": "مصطفى إسماعيل",
    "nasser_qatami": "ناصر القطامي",
    "saad_ghamdi": "سعد الغامدي",
    "salah_bukhatir": "صلاح بو خاطر",
    "shuraim": "سعود الشريم",
    "yasser_dosari": "ياسر الدوسري",
}


RECITERS = [
    _record("mishary_alafasy", "mishary_alafasy", "Mishary Rashid Alafasy",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 123,
            "https://cdn.mp3quran.net/audio/mishary-alafasy/r1/",
            source_reciter_id=123, source_recording_id=123),
    _record("mishary_alafasy_dorai", "mishary_alafasy", "Mishary Rashid Alafasy",
            "Rewayat AlDorai A'n Al-Kisa'ai - Murattal", "Murattal",
            "Al-Duri 'an al-Kisa'i", None,
            "https://cdn.mp3quran.net/audio/mishary-alafasy/r2/",
            available_surahs=(12, 14, 25, 87, 97, 99),
            timing_provider="chapter_only", timing_source="No published ayah timings",
            timing_source_url="https://www.mp3quran.net/api/v3/ayat_timing/reads",
            source_reciter_id=123, source_recording_id=124,
            source_url="https://www.mp3quran.net/api/v3/reciters?language=eng&reciter=123"),
    _record("mishary_alafasy_california", "mishary_alafasy", "Mishary Rashid Alafasy",
            ASSABILE_MISHARY_CALIFORNIA_CATALOG["recording_name"],
            ASSABILE_MISHARY_CALIFORNIA_CATALOG["style"],
            ASSABILE_MISHARY_CALIFORNIA_CATALOG["riwayah"], None,
            "https://media.assabile.com/assabile/recitations_7892537823/mp3/",
            available_surahs=tuple(ASSABILE_MISHARY_CALIFORNIA_CATALOG["available_surah_numbers"]),
            timing_provider="chapter_only",
            timing_source=ASSABILE_MISHARY_CALIFORNIA_CATALOG["timing_source"],
            timing_source_url=ASSABILE_MISHARY_CALIFORNIA_CATALOG["timing_source_url"],
            source_recording_id=ASSABILE_MISHARY_CALIFORNIA_CATALOG["source_recording_id"],
            source="Assabile.com",
            source_url=ASSABILE_MISHARY_CALIFORNIA_CATALOG["source_url"],
            recording_page_url=ASSABILE_MISHARY_CALIFORNIA_CATALOG["recording_page_url"],
            usage_rights=ASSABILE_MISHARY_CALIFORNIA_CATALOG["usage_rights"],
            audio_url_template=None,
            audio_urls_by_surah={int(number): url for number, url in ASSABILE_MISHARY_CALIFORNIA_URLS.items()}),
    _record("mishary_alafasy_tarawih_1427", "mishary_alafasy", "Mishary Rashid Alafasy",
            "Hafs 'an Asim - Tarawih prayer recitations 1427 (27 Surahs)",
            "Tarawih prayer", "Hafs 'an Asim", None,
            "https://media.assabile.com/assabile/recitations_7892537823/mp3/mishary-rashid-alafasy/",
            available_surahs=tuple(ASSABILE_MISHARY_TARAWIH_URLS),
            timing_provider="chapter_only", timing_source="No verified per-ayah timings",
            timing_source_url=ASSABILE_TARAWIH_PAGE,
            source_recording_id="recitations_7892537823",
            source="Assabile.com", source_url=ASSABILE_TARAWIH_PAGE,
            recording_page_url=ASSABILE_TARAWIH_PAGE,
            usage_rights=("Assabile offers free MP3 downloads; a separate audio redistribution license "
                          "is not stated."),
            audio_url_template=None, audio_urls_by_surah=ASSABILE_MISHARY_TARAWIH_URLS),
    _record("abdul_basit", "abdul_basit", "Abdul Basit Abd us-Samad",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 53,
            "https://cdn.mp3quran.net/audio/abdulbasit-abdulsamad/r3/"),
    _record("abdul_basit_mujawwad", "abdul_basit", "Abdul Basit Abd us-Samad",
            "Almusshaf Al Mojawwad - Almusshaf Al Mojawwad", "Mujawwad", None, 51,
            "https://cdn.mp3quran.net/audio/abdulbasit-abdulsamad/r1/"),
    _record("minshawi", "minshawi", "Mohamed Siddiq Al-Minshawi",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 112,
            "https://server10.mp3quran.net/minsh/",
            timing_slug="mohammed_siddiq_al_minshawi_mp3quran",
            timing_source=QUD_TIMING_SOURCE, timing_source_url=QUD_TIMING_SOURCE_URL),
    _record("husary", "husary", "Mahmoud Khalil Al-Husary",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 118,
            "https://cdn.mp3quran.net/audio/mahmoud-husary/r1/"),
    _record("husary_mujawwad", "husary", "Mahmoud Khalil Al-Husary",
            "Almusshaf Al Mojawwad - Almusshaf Al Mojawwad", "Mujawwad", None, 119,
            "https://cdn.mp3quran.net/audio/mahmoud-husary/r2/"),
    _record("husary_warsh", "husary", "Mahmoud Khalil Al-Husary",
            "Rewayat Warsh A'n Nafi' - Murattal", "Murattal", "Warsh 'an Nafi'", 120,
            "https://cdn.mp3quran.net/audio/mahmoud-husary/r3/"),
    _record("husary_duri", "husary", "Mahmoud Khalil Al-Husary",
            "Rewayat Aldori A'n Abi Amr - Murattal", "Murattal", "Al-Duri 'an Abi Amr", 269,
            "https://cdn.mp3quran.net/audio/mahmoud-husary/r4/"),
    _record("husary_qalun", "husary", "Mahmoud Khalil Al-Husary",
            "Rewayat Qalon A'n Nafi' - Murattal", "Murattal", "Qalun 'an Nafi'", 270,
            "https://cdn.mp3quran.net/audio/mahmoud-husary/r5/"),
    _record("maher_muaiqly", "maher_muaiqly", "Maher Al-Muaiqly",
            "Almusshaf Al Mojawwad - Almusshaf Al Mojawwad", "Mujawwad", None, 133,
            "https://cdn.mp3quran.net/audio/maher-muaiqly/r3/"),
    _record("yasser_dosari", "yasser_dosari", "Yasser Al-Dosari",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 92,
            "https://cdn.mp3quran.net/audio/yasser-dosari/r1/"),
    _record("saad_ghamdi", "saad_ghamdi", "Saad Al-Ghamdi",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 30,
            "https://cdn.mp3quran.net/audio/saad-ghamdi/r1/"),
    _record("abdur_rahman_sudais", "abdur_rahman_sudais", "Abdur-Rahman as-Sudais",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 54,
            "https://cdn.mp3quran.net/audio/abdulrahman-sudais/r1/"),
    _record("shuraim", "shuraim", "Saud ash-Shuraim",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 31,
            "https://cdn.mp3quran.net/audio/saud-shuraim/r1/"),
    _record("muhammad_ayyub", "muhammad_ayyub", "Muhammad Ayyub",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 109,
            "https://cdn.mp3quran.net/audio/muhammad-ayyub/r1/"),
    _record("abu_bakr_shatri", "abu_bakr_shatri", "Abu Bakr ash-Shatri",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 4,
            "https://cdn.mp3quran.net/audio/abubakr-shatri/r1/"),
    _record("mustafa_ismail", "mustafa_ismail", "Mustafa Ismail",
            "Almusshaf Al Mojawwad - Almusshaf Al Mojawwad", "Mujawwad", None, 288,
            "https://cdn.mp3quran.net/audio/mustafa-ismail/r2/"),
    _record("ali_hudhaify", "ali_hudhaify", "Ali al-Hudhaify",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 74,
            "https://cdn.mp3quran.net/audio/ali-hudhaifi/r1/"),
    _record("hani_rifai", "hani_rifai", "Hani ar-Rifai",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 89,
            "https://cdn.mp3quran.net/audio/hani-rifai/r1/"),
    _record("fares_abbad", "fares_abbad", "Fares Abbad",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 81,
            "https://cdn.mp3quran.net/audio/fares-abbad/r1/"),
    _record("nasser_qatami", "nasser_qatami", "Nasser al-Qatami",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 86,
            "https://cdn.mp3quran.net/audio/nasser-qatami/r1/"),
    _record("idris_abkar", "idris_abkar", "Idris Abkar",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 12,
            "https://cdn.mp3quran.net/audio/idrees-abkar/r1/"),
    _record("salah_bukhatir", "salah_bukhatir", "Salah Bukhatir",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 46,
            "https://cdn.mp3quran.net/audio/salah-bukhatir/r1/"),
    _record("abdullah_basfar", "abdullah_basfar", "Abdullah Basfar",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 60,
            "https://cdn.mp3quran.net/audio/abdullah-basfar/r1/"),
    _record("ahmed_ajmi", "ahmed_ajmi", "Ahmed Al-Ajmi",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 5,
            "https://cdn.mp3quran.net/audio/ahmad-ajmi/r1/"),
    _record("minshawi_mujawwad", "minshawi", "Mohamed Siddiq Al-Minshawi",
            "Almusshaf Al Mojawwad - Almusshaf Al Mojawwad", "Mujawwad", "Hafs 'an Asim", None,
            "https://server10.mp3quran.net/minsh/Almusshaf-Al-Mojawwad/",
            timing_slug="mohammed_siddiq_al_minshawi_mujawwad_mp3quran",
            timing_source=QUD_TIMING_SOURCE, timing_source_url=QUD_TIMING_SOURCE_URL),
    _record("islam_sobhi", "islam_sobhi", "Islam Sobhi",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", 253,
            "https://server14.mp3quran.net/islam/Rewayat-Hafs-A-n-Assem/",
            available_surahs=ISLAM_SOBHI_QUD_SURAHS,
            timing_slug="islam_sobhi_mp3quran",
            timing_source=QUD_TIMING_SOURCE, timing_source_url=QUD_TIMING_SOURCE_URL),
    _record("salman_alotaibi", "salman_alotaibi", "Salman Al-Utaybi",
            "Rewayat Hafs A'n Assem - Murattal", "Murattal", "Hafs 'an Asim", None,
            "https://cdn.mp3quran.net/audio/salman-otaibi/r1/",
            name_ar="سلمان العتيبي",
            available_surahs=(1, 2, 3, 10, 11, 14, 16, 19, 23, 25, 32, 36, 38, 39, 40,
                              46, 48, 50, 52, 55, 56, 58, 59, 61, 62, 63, 64,
                              *range(66, 115)),
            timing_provider="chapter_only", timing_source="No published ayah timings",
            timing_source_url="https://www.mp3quran.net/api/v3/ayat_timing/reads",
            source_reciter_id=240, source_recording_id=240,
            source_url="https://www.mp3quran.net/api/v3/reciters?language=eng&reciter=240",
            recording_page_url="https://way2quran.com/ar/reciters/slman-al-atyby",
            source="MP3Quran.net + Way2Quran.com",
            usage_rights=("MP3Quran.net and Way2Quran.com offer this recording for streaming and download; "
                          "a separate audio redistribution license is not stated."),
            audio_url_overrides_by_surah={
                16: "https://media.way2quran.com/slman-al-atyby/hafs-an-asim/016.mp3",
            },
            audio_provider_overrides_by_surah={16: "Way2Quran.com"}),
]

RECITERS_BY_ID = {reciter["id"]: reciter for reciter in RECITERS}
