# WR1.EXE camera and coordinate projection

2026-09-07. Static analysis of [WR1.EXE](<D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)/WORD/WR1.EXE>), SHA256 `b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`. Addresses are file offsets unless prefixed `DS:` or explicitly written as a far pointer. No gameplay or running session was changed.

**The camera takes at most one 8-pixel step per axis on each original rendering-routine invocation. Horizontal following targets player render X=144; vertical following uses player bottom Y thresholds 108 and 132. There is no interpolation.** Both player screen coordinates are adjusted by the opposite amount, preserving world position.

Primary evidence is the executable's [camera instruction block](output/wr1_camera_ac27.txt), [full renderer opening](output/wr1_camera_ab25.txt), [initial camera placement](output/wr1_camera_6550.txt), and [main-loop call order](output/wr1_camera_3d72.txt). See [movement research](wr1_movement_research.md) for MZ relocation arithmetic and the approximately 12 Hz default gameplay cadence.

## Runtime variables and boundaries

| Variable | Meaning |
|---|---|
| `DS:8480`, `DS:8482` | Camera X/Y in 8-pixel attr-grid units. |
| `DS:662e`, `DS:6630` | Player render X and bottom Y in original 320x200 screen pixels. Player sprite top-left is `(X,Y-32)`. |
| `DS:83f6`, `DS:83f8` | Player world attr-grid X/Y. Not modified by the camera block. |
| `DS:9778`, `DS:9792` | Attr-grid width/height, twice the background-grid dimensions. |

The camera block is at `0xac27–0xacb2`, inside renderer `0812:0005`, which maps to file `0xab25` (`0x2a00 + 0x812*16 + 5`). It runs before the level/world drawing paths.

```python
# Exact normal camera block; all values are integer words.
background_screen_dx = 0
background_screen_dy = 0

# Horizontal first, and only one branch can fire.
if camera_x > 0 and player_render_x < 144:
    camera_x -= 1
    player_render_x += 8
    background_screen_dx = 8
elif camera_x < attr_width - 36 and player_render_x > 144:
    camera_x += 1
    player_render_x -= 8
    background_screen_dx = -8

# Then vertical; bottom Y, not sprite top/center Y.
if camera_y > 0 and player_bottom_y < 108:
    camera_y -= 1
    player_bottom_y += 8
    background_screen_dy = 8
elif camera_y < attr_height - 19 and player_bottom_y > 132:
    camera_y += 1
    player_bottom_y -= 8
    background_screen_dy = -8
```

Instruction evidence:

- Left: `0xac31` tests camera X against zero, `0xac38` compares player X to `0x90`, `0xac40/0xac44` decrement camera and add eight to render X.
- Right: `0xac50–0xac5a` tests against attr width minus `0x24`, `0xac5c` compares player X to `0x90`, `0xac64/0xac68` increment camera and subtract eight from render X.
- Up: `0xac72` tests camera Y against zero, `0xac79` compares bottom Y to `0x6c`, `0xac80/0xac84` decrement camera and add eight to bottom Y.
- Down: `0xac90–0xac9a` tests against attr height minus `0x13`, `0xac9c` compares bottom Y to `0x84`, `0xaca4/0xaca8` increment camera and subtract eight from bottom Y.

All threshold comparisons are signed. Equality causes no scroll. There is no loop to clamp the player back into a target region and no velocity/delta-time calculation: even if far outside the target, only one step is taken in this invocation. At a level edge the player can move away from the screen-follow target because that axis cannot scroll further.

On the usual 8-pixel position lattice, stable bottom-Y positions within the vertical dead band are 112, 120, and 128. A rising character at bottom Y=104 causes the camera to move up and the displayed character bottom to return to 112; a falling character at 136 returns to 128 after downward camera movement. Thus comparing player screen-Y alone can underestimate actual jump distance considerably.

## World position and projection

Each camera step leaves these values invariant:

```text
player_world_render_x = player_render_x + 8*camera_x
player_world_render_y = player_bottom_y + 8*camera_y
```

These invariants include the original screen-origin offsets; they are useful for comparisons even before choosing a clone's world origin.

For background/entity grid coordinates, the renderer computes projection offsets at `0xb368–0xb387`:

```text
screen_offset_x = 16 - 8*camera_x
screen_offset_y = 32 - 8*camera_y
```

The background tile loop independently uses `camera_x // 2`, `camera_y // 2` as 16-pixel tile indices and camera parity times eight as half-tile pixel offsets (`0xacc5–0xad31`). Each scroll therefore moves the world by eight pixels, even though the art grid is sixteen pixels.

The player has its own anchor convention. Reconstructing its grid coordinates uses:

```text
gx = trunc_toward_zero((player_render_x - 16)/8) + camera_x - 1
gy = trunc_toward_zero((player_bottom_y - 31)/8) + camera_y
```

This conversion is at `0x50bf–0x50e0`. The camera block does not change `gx/gy`, only the redundant screen coordinates and camera offsets. In a clone it is reasonable to store world coordinates and derive screen coordinates, provided the original 8-pixel update rules and anchor offsets remain exact. Do not shift the world position when applying camera movement.

## Initial placement differs from runtime bounds

Level-load placement at `0x6550–0x65f6` uses header start coordinates in the 8-pixel grid:

```python
camera_x = min(max(start_x - 18, 0), attr_width - 37)
camera_y = min(max(start_y - 11, 0), attr_height - 20)
saved_camera_x = camera_x
saved_camera_y = camera_y

player_render_x = (start_x - camera_x)*8 + 16
saved_player_render_x = player_render_x
player_bottom_y = (start_y - camera_y)*8 + 32
saved_player_bottom_y = player_bottom_y
player_bottom_y += 8
```

The `min(max(...))` spelling preserves the code's clamp order, including its behavior for hypothetical maps smaller than the viewport. Actual level sizes should be used for normal tests.

The initial maximum camera values are **width-37 and height-20**, but runtime following permits **width-36 and height-19**. Do not silently unify them.

For an unclamped starting location, initial player render X is 160. Subsequent render invocations can move the camera right by one cell each until player render X reaches 144, even without horizontal input. Whether a captured "first gameplay frame" occurs before or after that settling depends on the surrounding call sequence and capture boundary. Preserve a proven starting-frame match until the chosen reference point is clear.

A restore path at `0x6167–0x617c` copies saved camera and player coordinates back into live variables, then jumps to `0x6e36`. The saved Y is the value before the initial `+8` adjustment. This is direct byte-level evidence; the complete death/restart path and later placement effects have not been traced, so it should not be simplified into a claim that every respawn is exactly eight pixels higher.

## Invocation order and timing

Normal gameplay order is:

1. Vertical movement, horizontal movement, and exit/bottom checks in the main gameplay function.
2. Matching/pickup interaction routine `097a:000a` = file `0xc1aa`, called at `0x3d7e`.
3. Entity/action routine `01a3:0cb8` = file `0x50e8`, called at `0x3d99`.
4. Rendering routine `0812:0005` = file `0xab25`, called at `0x3d9e`; its camera block runs before world drawing.

The default main-loop cadence is nominally approximately 12 updates/sec, so a following camera normally advances in 8-pixel steps at that cadence. However, this executable also calls the same renderer at `0x3dbc`, `0x58a3`, `0x58fe`, `0x5c0d`, and `0x5dad`, inside other gameplay/transition paths. Camera movement is tied to these invocations, not directly to the VGA refresh or the PIT interrupt.

For a modern clone, applying this camera block on every 70 Hz presentation frame would accelerate camera settling and change transitional behavior. Apply it at the matching original game-update/render point. Track extra render invocations separately when implementing the corresponding transitions; merely matching an average follow speed is insufficient for exact frame parity.

## Remaining limits

The normal camera thresholds, bounds, step size, coordinate writes, order, and projection are high-confidence static findings from a small straight-line branch block. No runtime trace was captured in this research pass. Exact presentation/capture boundary, border clipping behavior, background buffering optimizations, all transition-call timing, and full restart flow remain outside this bounded result.

Useful checks for the eventual implementation are threshold equality and one-step overshoot, both level edges, an ordinary jump while scrolling vertically, idle camera settling from initial placement, and a transition that renders without normal movement. The player-world invariants above should remain unchanged by every camera-only step.
