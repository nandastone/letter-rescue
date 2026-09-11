"""Position-only transcription of WR1.EXE's movement block.

See wr1_movement_research.md for byte offsets and limitations. This is an
executable research artifact, not a replacement player controller. Call once per
original gameplay update; no dt, camera, animation, interactions, or RNG here.
The attr callback receives original 8-pixel grid coordinates. Bounds behavior
belongs to the caller; this transcription does not invent out-of-map tiles.
Python integers omit 16-bit overflow; use valid original map coordinates.
"""

from dataclasses import dataclass, replace
from typing import Callable

PIT_HZ = 1_193_182
PIT_DIVISOR = 12_428
DEFAULT_TIMER_THRESHOLD = 8
NOMINAL_UPDATE_SECONDS = PIT_DIVISOR * DEFAULT_TIMER_THRESHOLD / PIT_HZ


@dataclass(frozen=True)
class Position:
    """x/y are render X/bottom Y. phase=16 is settled, not startup (phase=0)."""
    x: int
    y: int
    gx: int
    gy: int
    phase: int = 16
    facing: int = 0


@dataclass(frozen=True)
class Held:
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False


def step(state: Position, held: Held, attr: Callable[[int, int], int]) -> Position:
    """Transcribe 0x37c5–0x3cdb, preserving instruction order and quirks."""
    x, y, gx, gy, phase, facing = (
        state.x, state.y, state.gx, state.gy, state.phase, state.facing
    )
    support = attr(gx + 1, gy)
    if support not in (0x73, 0x74):
        support = 0

    if held.up:
        climbing_up = (
            (support == 0x74 and attr(gx + 1, gy - 2) == 0x74)
            or (attr(gx + 1, gy - 1) == 0x74
                and attr(gx + 1, gy - 3) == 0x74)
        )
        if climbing_up or support:
            phase = 0
        if phase < 9:
            y -= 8
            gy -= 1
            for col in range(gx, gx + 3):
                if attr(col, gy - 4) == 0x73:
                    y += 8
                    phase = 16
                    gy += 1
                    break
        else:
            y += 8
            gy += 1
    elif support == 0 or (held.down and support == 0x74):
        # Climb-down detection changes animation only, omitted in this model.
        if attr(gx, gy - 1) == 0x73:
            gx += 1
            x += 8
        if attr(gx + 2, gy - 1) == 0x73:
            gx -= 1
            x -= 8
        y += 8
        gy += 1

    phase = min(phase + 1, 16)
    if held.left:
        x -= 8
        gx -= 1
        for row in range(gy - 4, gy):
            if attr(gx, row) == 0x73:
                gx += 1
                x += 8
                break
        facing = 1
    if held.right:
        x += 8
        gx += 1
        for row in range(gy - 4, gy):
            if attr(gx + 2, row) == 0x73:
                gx -= 1
                x -= 8
                # Intentional missing break in original; re-read shifted gx.
        facing = 0
    return replace(state, x=x, y=y, gx=gx, gy=gy, phase=phase, facing=facing)
