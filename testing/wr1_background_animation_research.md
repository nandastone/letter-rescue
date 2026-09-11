# WR1 background animation clock

2026-09-07. Static analysis of [WR1.EXE](<D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)/WORD/WR1.EXE>), SHA256 `b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`. Addresses are file offsets unless prefixed `DS:`. No gameplay code changed.

**Animated background tiles advance one of four frames on every original renderer invocation.** The counter is `DS:41be`, initialized to zero in the executable. It is incremented before drawing, and no per-level reset was found. This replaces the empirical assumption of one frame per six 70 Hz physics ticks.

## Exact code and state

[Renderer evidence, including the complete animated-tile loop](output/wr1_bganim_b191.txt):

```text
0xb226  inc word ptr [DS:41be]
0xb22a  mov ax,[DS:41be]
0xb22d  cmp ax,3
0xb230  jle 0xb238
0xb232  mov word ptr [DS:41be],0
```

The following loop draws the animated cells. Its source X is the cell's normal background-atlas X plus `16*frame` (`0xb29d–0xb2a8`, repeated for the right edge at `0xb2ee–0xb2fb`). Source Y remains unchanged. The source graphics page is 3 at `0xb326`; the blit is at `0xb359`.

```python
# Once per invocation of original renderer 0812:0005 (file 0xab25).
background_frame += 1
if background_frame > 3:
    background_frame = 0

for i in range(animated_count):
    tx, ty = animated_x[i], animated_y[i]  # 16-pixel background grid
    if visible(tx, ty):
        sx = background_source_x[tx][ty] + 16*background_frame
        sy = background_source_y[tx][ty]
        blit(source_page=3, rect=(sx, sy, sx+15, sy+15),
             destination=(tx*16+16-camera_x*8,
                          ty*16+32-camera_y*8))
```

The modulo-four increment is unconditional: it happens even if the animated list is empty or all its cells are offscreen. It occurs once for the whole list, not once per cell. Duplicate coordinates therefore draw the same phase twice; they do not advance the animation twice.

| DS location | Meaning |
|---|---|
| `41be` | Global animation phase 0..3, initialized word 0 at file `0x2910e`. |
| `9e72` | Animated-cell count. |
| `c18b + 2*i` | Animated-cell X in 16-pixel tile units. |
| `c26b + 2*i` | Animated-cell Y in 16-pixel tile units. |
| `8b13 + 4*tx` | Far pointer to source-X table column; row entry is a word at offset `2*ty`. |
| `8ccf + 4*tx` | Equivalent source-Y table column. |

[Loader evidence](output/wr1_bganim_67c0.txt) stores the animation count at `0x6814`, X at `0x6844`, and Y at `0x6856`. The later count at `0x6870` is `DS:a928`, with coords `DS:ad76/aec0`; that is the **separate foreground-tile list**. The prior EXE research mistakenly inspected that later list as animation. Its redraw after player rendering at `0xbc63–0xbd6f` contains no animation offset because it is not the animated-background loop.

Parsing the local original `WR1.S0` with the existing level decoder yields 11 animation entries and zero foreground entries. The first two animation entries both refer to background cell `(2,6)`, consistent with the tree/owl region under investigation. The earlier report's zero-animation claim for level 1 resulted from reading the foreground count.

## Timing and ordering

The normal update calls the renderer at file `0x3d9e`, after player movement, matching/pickup interaction processing, and entity/action processing. Within the renderer, the camera is adjusted at `0xac27–0xacb2`; base background rendering follows; then the animation phase increments at `0xb226` and animated tiles are drawn. Player rendering happens later at `0xb9f3–0xba33`. Thus the phase of a completed gameplay frame includes that frame's increment.

At the default timer threshold, this produces approximately 12.000945 animation frames/sec and a four-frame cycle of approximately 0.333307 seconds. It follows the original game renderer's invocation cadence, including speed-setting changes and additional transition renders; it is not independently driven by 70 Hz refresh. Six 70 Hz ticks correspond to about 11.667 frames/sec, so the clone's empirical clock necessarily drifts.

## Startup phase and exact convergence

The initialized phase is zero, so a fresh first renderer invocation draws phase 1; subsequent invocations draw 2, 3, 0, 1, and so on. The only direct references found to `DS:41be` in gameplay code are the increment, wrap, and source-coordinate reads above. No level-load or restart reset was found. Earlier demo/render activity can therefore change the starting phase of a later level or savestate.

For a runtime comparison, capture `DS:41be` in the same stable native state sample as the player/camera. If the clone is reproducing that already-completed native frame, draw the sampled phase without incrementing it. Increment once when executing the next original-equivalent renderer/update. This avoids an off-by-one introduced by treating a post-render savestate as a pre-render state.

The phase/address, four-frame rule, source offsets, and ordering are high-confidence static findings. The exact phase of the user's chosen savestate still requires its live memory value. Other transition render counts should be traced when those transitions are implemented; they need not be guessed to complete the first ordinary walking/jumping comparison.
