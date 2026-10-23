from app.scenes import clip_scene_overrides_to_word_ranges


def test_word_range_projection_keeps_intersected_scene_settings():
    rows = [
        {"scene_id": "first", "ayah_number": 10, "text": "a b", "locked": True,
         "manual_duration": 2.5},
        {"scene_id": "middle", "ayah_number": 10, "text": "c d", "locked": False,
         "manual_duration": 3.25},
        {"scene_id": "last", "ayah_number": 10, "text": "e f", "locked": True,
         "manual_duration": 4.0},
    ]

    clipped = clip_scene_overrides_to_word_ranges(
        ["a b c d e f"], 10, rows, [(3, 5)],
    )

    assert [(row["scene_id"], row["text"]) for row in clipped] == [
        ("middle", "c d"), ("last", "e"),
    ]
    assert clipped[0]["manual_duration"] == 3.25
    assert clipped[0]["locked"] is False
    assert clipped[1]["manual_duration"] == 4.0
    assert clipped[1]["locked"] is True
    assert rows[0]["text"] == "a b"
    assert rows[2]["text"] == "e f"
