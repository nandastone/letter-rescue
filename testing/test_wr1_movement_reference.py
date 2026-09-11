"""Behavioral acceptance examples inferred from WR1.EXE, not emulator traces.

Run: python -m unittest discover -s testing -p test_wr1_movement_reference.py -v
"""

import unittest
from wr1_movement_reference import Held, Position, step, NOMINAL_UPDATE_SECONDS


def ground(x, y):
    return 0x73 if y >= 20 else 0


class MovementEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.start = Position(x=64, y=191, gx=5, gy=20)

    def test_twelve_walking_updates_cover_96_pixels(self):
        state = self.start
        for _ in range(12):
            state = step(state, Held(right=True), ground)
        self.assertEqual((state.x, state.y), (160, 191))
        self.assertAlmostEqual(12 * NOMINAL_UPDATE_SECONDS, 1.0, places=3)

    def test_full_jump_rises_72_pixels_and_autorepeats(self):
        state = self.start
        heights = []
        for _ in range(19):
            state = step(state, Held(up=True), ground)
            heights.append(self.start.y - state.y)
        self.assertEqual(heights, [8, 16, 24, 32, 40, 48, 56, 64, 72,
                                   64, 56, 48, 40, 32, 24, 16, 8, 0, 8])

    def test_release_falls_immediately_and_repress_can_resume(self):
        state = self.start
        for _ in range(3):
            state = step(state, Held(up=True), ground)
        state = step(state, Held(), ground)
        self.assertEqual(self.start.y - state.y, 16)
        state = step(state, Held(up=True), ground)
        self.assertEqual((self.start.y - state.y, state.phase), (24, 5))

    def test_saturated_phase_cannot_jump_after_walking_off(self):
        ledge = lambda x, y: 0x73 if y >= 20 and x <= 6 else 0
        state = step(self.start, Held(right=True), ledge)
        state = step(state, Held(up=True), ledge)
        self.assertEqual(state.y, self.start.y + 8)

    def test_ceiling_stops_rise_and_exhausts_phase(self):
        room = lambda x, y: 0x73 if y == 15 or y >= 20 else 0
        state = step(self.start, Held(up=True), room)
        self.assertEqual((state.y, state.phase), (self.start.y, 16))

    def test_climb_pattern_allows_more_than_72_pixels(self):
        ladder = lambda x, y: 0x74 if x == 6 else 0
        state = self.start
        for _ in range(15):
            state = step(state, Held(up=True), ladder)
        self.assertEqual((self.start.y - state.y, state.phase), (120, 1))

    def test_down_passes_74_but_not_73_support(self):
        platform = lambda x, y: 0x74 if y == 20 else 0
        self.assertEqual(step(self.start, Held(), platform).y, self.start.y)
        self.assertEqual(step(self.start, Held(down=True), platform).y, self.start.y + 8)
        self.assertEqual(step(self.start, Held(down=True), ground).y, self.start.y)

    def test_both_horizontal_keys_are_separate_collision_attempts(self):
        wall = lambda x, y: 0x73 if x == 4 or y >= 20 else 0
        state = step(self.start, Held(left=True, right=True), wall)
        self.assertEqual(state.x, self.start.x + 8)

    def test_right_wall_loop_rechecks_shifted_column(self):
        # Deliberate overlap fixture exercises the original's missing break.
        cells = {(8, 16), (7, 17)}
        wall = lambda x, y: 0x73 if (x, y) in cells or y >= 20 else 0
        state = step(self.start, Held(right=True), wall)
        self.assertEqual(state.x, self.start.x - 8)


if __name__ == "__main__":
    unittest.main()
