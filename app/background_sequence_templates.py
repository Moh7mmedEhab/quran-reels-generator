"""Prebuilt five-scene background sequences made from bundled, credited photos.

These are image-based motion scenes, not stock video footage. Each still is
animated and transitioned by the same MoviePy background sequence renderer
used for user-uploaded image/video sequences.
"""

BACKGROUND_SEQUENCE_TEMPLATES = {
    "nature_in_motion": {
        "name": "Nature in Motion",
        "description": "Five calm landscape scenes with gentle camera movement.",
        "transition": "crossfade",
        "transition_duration": 0.7,
        "animation_preset": "gentle_movement",
        "animation_intensity": 0.45,
        "animation_duration": 18,
        "animation_speed": 0.8,
        "loop": True,
        "scenes": [
            {"theme": "misty_forest", "duration": 7},
            {"theme": "cloud_morning", "duration": 7},
            {"theme": "golden_dunes", "duration": 7},
            {"theme": "desert_dawn", "duration": 7},
            {"theme": "sapphire_horizon", "duration": 7},
        ],
    },
    "mosque_at_dusk": {
        "name": "Mosque at Dusk",
        "description": "Five illuminated mosque and courtyard scenes in a quiet palette.",
        "transition": "crossfade",
        "transition_duration": 0.75,
        "animation_preset": "cinematic_zoom",
        "animation_intensity": 0.4,
        "animation_duration": 20,
        "animation_speed": 0.75,
        "loop": True,
        "scenes": [
            {"theme": "masjid_night", "duration": 7},
            {"theme": "olive_garden", "duration": 7},
            {"theme": "jade_courtyard", "duration": 7},
            {"theme": "marble_arch", "duration": 7},
            {"theme": "turquoise_mosaic", "duration": 7},
        ],
    },
    "moonlit_horizons": {
        "name": "Moonlit Horizons",
        "description": "Five celestial scenes with restrained floating camera motion.",
        "transition": "dissolve",
        "transition_duration": 0.8,
        "animation_preset": "floating_camera",
        "animation_intensity": 0.35,
        "animation_duration": 22,
        "animation_speed": 0.7,
        "loop": True,
        "scenes": [
            {"theme": "sahara_moon", "duration": 7},
            {"theme": "midnight_blue", "duration": 7},
            {"theme": "lavender_twilight", "duration": 7},
            {"theme": "crescent_garden", "duration": 7},
            {"theme": "aurora_drift", "duration": 7},
        ],
    },
    "waterside_reflections": {
        "name": "Waterside Reflections",
        "description": "Five water and atmosphere scenes, softly graded for readable captions.",
        "transition": "fade_black",
        "transition_duration": 0.65,
        "animation_preset": "slow_pan_right",
        "animation_intensity": 0.3,
        "animation_duration": 24,
        "animation_speed": 0.65,
        "loop": True,
        "scenes": [
            {"theme": "ocean_calm", "duration": 7},
            {"theme": "sapphire_horizon", "duration": 7},
            {"theme": "pearl_dawn", "duration": 7},
            {"theme": "rose_sand", "duration": 7},
            {"theme": "plum_evening", "duration": 7},
        ],
    },
}

DEFAULT_BACKGROUND_SEQUENCE_TEMPLATE = "nature_in_motion"
