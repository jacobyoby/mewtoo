"""Regression tests for Gen 1 text-box detection (profiles from real frames)."""
from unittest.mock import Mock

import numpy as np

from game_state import GameState


def panel(white_frac, mid_frac):
    """Build a 144x160 frame whose bottom 40% matches the given profile."""
    img = np.zeros((144, 160, 3), dtype=np.uint8)
    bottom = img[int(144 * 0.60):]
    rows = bottom.shape[0]
    n_white = int(rows * white_frac)
    n_mid = int(rows * mid_frac)
    bottom[:n_white] = 255                      # flat white
    bottom[n_white:n_white + n_mid] = 128       # dithered mid-tone
    return img


def detector():
    gs = GameState.__new__(GameState)
    gs.pyboy = Mock()
    return gs


def test_text_box_detected():
    # Oak dialog profile: 78% white, 3% mid
    assert detector().detect_text_box(panel(0.78, 0.03)) is True


def test_indoor_scene_not_a_text_box():
    # Bedroom profile: 10% white, 3% mid (mostly dark)
    assert detector().detect_text_box(panel(0.10, 0.03)) is False


def test_outdoor_tiles_not_a_text_box():
    # Pallet Town profile: bright but heavily dithered — 67% white, 28% mid.
    # Brightness alone would false-positive here; the mid-tone test rejects it.
    assert detector().detect_text_box(panel(0.67, 0.28)) is False


class TestDirectionalHold:
    """Directional presses must commit exactly one tile.

    Measured on the real ROM from a Pallet Town save state: holds of 8-16
    frames move exactly one tile per press; an 18-frame hold moves two,
    which made precise navigation impossible.
    """

    def test_directional_press_uses_single_step_hold(self):
        from unittest.mock import Mock
        gs = GameState.__new__(GameState)
        gs.pyboy = Mock()
        gs.BUTTONS = GameState.BUTTONS
        gs.press_button("RIGHT")
        # 12 hold + 4 settle; an 18-frame hold would double-step
        assert gs.pyboy.tick.call_count == 16

    def test_action_buttons_keep_the_short_tap(self):
        from unittest.mock import Mock
        gs = GameState.__new__(GameState)
        gs.pyboy = Mock()
        gs.BUTTONS = GameState.BUTTONS
        gs.press_button("A")
        assert gs.pyboy.tick.call_count == 12  # 8 hold + 4 settle
