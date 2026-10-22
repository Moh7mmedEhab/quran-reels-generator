"""Shared presets and frame transforms for optional still-image motion."""

import math

IMAGE_ANIMATION_PRESETS = {
    "static": {"name": "Static image", "description": "Keep the background still.",
               "zoom": (1.0, 1.0), "pan_x": (.5, .5), "pan_y": (.5, .5)},
    "cinematic_zoom": {"name": "Cinematic zoom", "description": "A very slow, smooth push toward the scene.",
                       "zoom": (1.0, 1.09), "pan_x": (.5, .5), "pan_y": (.5, .5)},
    "slow_pan_left": {"name": "Slow pan left", "description": "A gentle horizontal camera move.",
                      "zoom": (1.08, 1.08), "pan_x": (1.0, 0.0), "pan_y": (.5, .5)},
    "slow_pan_right": {"name": "Slow pan right", "description": "A gentle horizontal camera move.",
                       "zoom": (1.08, 1.08), "pan_x": (0.0, 1.0), "pan_y": (.5, .5)},
    "slow_pan_top_to_bottom": {"name": "Move top to bottom", "description": "A gentle vertical drift.",
                               "zoom": (1.08, 1.08), "pan_x": (.5, .5), "pan_y": (1.0, 0.0)},
    "slow_pan_bottom_to_top": {"name": "Move bottom to top", "description": "A gentle vertical drift.",
                               "zoom": (1.08, 1.08), "pan_x": (.5, .5), "pan_y": (0.0, 1.0)},
    "gentle_movement": {"name": "Gentle movement", "description": "A restrained zoom with a small diagonal drift.",
                        "zoom": (1.025, 1.06), "pan_x": (.42, .58), "pan_y": (.58, .42)},
    "floating_camera": {"name": "Floating camera", "description": "A slow, subtle floating movement.",
                        "zoom": (1.055, 1.075), "pan_x": (.3, .7), "pan_y": (.38, .62)},
    "parallax_depth": {"name": "Parallax depth", "description": "A slow forward move with a mild vertical shift.",
                       "zoom": (1.04, 1.105), "pan_x": (.44, .56), "pan_y": (.62, .38)},
}

MOTION_DIRECTIONS = {
    "static": "static",
    "left_to_right": "slow_pan_left",
    "right_to_left": "slow_pan_right",
    "top_to_bottom": "slow_pan_top_to_bottom",
    "bottom_to_top": "slow_pan_bottom_to_top",
}


def resolve_motion_preset(direction, preset_id):
    """Return the active preset for an explicit direction or legacy preset UI."""
    if direction == "preset":
        return preset_id
    if direction not in MOTION_DIRECTIONS:
        raise ValueError("Choose static, a supported movement direction, or the saved preset.")
    return MOTION_DIRECTIONS[direction]


def image_motion_values(preset_id, progress, intensity=1.0):
    """Return a zoom and crop position that always stays inside the image."""
    preset = IMAGE_ANIMATION_PRESETS.get(preset_id, IMAGE_ANIMATION_PRESETS["static"])
    if preset_id == "static":
        return 1.0, .5, .5
    intensity = min(1.0, max(0.0, float(intensity)))
    # The caller supplies a cosine-eased phase so each repeated move joins smoothly.
    phase = min(1.0, max(0.0, float(progress)))
    zoom_start, zoom_end = preset["zoom"]
    zoom = 1.0 + (zoom_start - 1.0 + (zoom_end - zoom_start) * phase) * intensity
    x_start, x_end = preset["pan_x"]
    y_start, y_end = preset["pan_y"]
    return zoom, x_start + (x_end - x_start) * phase, y_start + (y_end - y_start) * phase


def image_animation_phase(elapsed, cycle_duration, speed=1.0, start_time=0.0):
    """Return an eased, ping-pong camera phase without a jump at cycle edges."""
    elapsed = float(elapsed)
    start_time = float(start_time)
    cycle_duration = max(.01, float(cycle_duration))
    speed = max(.01, float(speed))
    if elapsed < start_time:
        return 0.0
    cycle = ((elapsed - start_time) * speed / cycle_duration) % 1.0
    return (1.0 - math.cos(2.0 * math.pi * cycle)) / 2.0


def ambient_light_position(progress):
    """Return a gentle diagonal path that stays within the image bounds."""
    phase = min(1.0, max(0.0, float(progress)))
    return .08 + .84 * phase, .12 + .55 * phase
