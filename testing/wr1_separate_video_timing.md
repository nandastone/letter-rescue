# Gameplay and presentation separation

Current result after the recap timestamp fix: **50/50 images and 2,913/2,913
states match with VGA scanout on every scenario**. There are still 533 admission
timing differences. See `testing/output/parity/recap-clock-fixed-all/` and
[the diagnosis](wr1_recap_video_diagnosis.md). Earlier runs below are historical.

`scripts/wr1_presentation.gd` now owns displayed images. Gameplay still executes
the recovered motion, actor, animation, and interaction updates in their existing
order. Each logical drawing call submits an owned image; displaying it does not
run those updates again. Rescue, recap, exit, and level-reset drawing also submit
images. The first image is prepared before replay inputs are admitted.

Live play and replays now both use the independent video clock. Older recordings
without measured VGA phase use an assumed phase, which the report labels explicitly.
`--snapshot-video` retains the previous presentation policy for comparison;
`--vga-scanout` explicitly selects the default hardware policy: two page images,
page selection/retrace latch, four timed
50-row reads, and a completed image returned before the next frontend interval.
It can produce an image containing parts of two different page writes.

Run the same evidence checks under either policy:

```powershell
just parity
just parity --scenario hard_drip_impact --vga-scanout
just parity --snapshot-video
```

The report records each scenario's presentation policy and whether its initial
video phase was measured, and retains failing timing and pixel
comparisons under both policies. No frame shifts or exemptions are applied.

## Limits

This is a separation of responsibilities, not a completed CPU timing model.
Ordinary submissions still have zero drawing duration. The separate work model
must eventually timestamp actual page writes, including scene drawing and Benny's
later blits, and account for IRQ/music work that delays main-loop admission.
The corrected snapshot adapter plus VGA scanout matches all 14 hard-impact
reference images (previously 8/14), including the mixed scanout at counter 940.
This does not establish exact drawing durations: the same image can result from
multiple write times within a scanout interval. Admission timing still has 45
differences on that route. See `testing/output/parity/separate-video-scanout/`.
Forcing scanout across all 17 scenarios gives 2,913/2,913 matching states and
49/50 matching images, compared with 44/50 under snapshot presentation. The
remaining recap image differed at five pixels. That difference was subsequently
traced to reversed recap submission timestamps and fixed; see
[the recap diagnosis](wr1_recap_video_diagnosis.md). The missing initial VGA phase
was not the demonstrated cause. All 533 admission timing differences remain visible.
The full forced-scanout result is in
`testing/output/parity/separate-video-scanout-all/`.

Post-load replay metadata supplies only the initial display page and, when
observed, the initial VGA phase. `hard_drip_impact` has measured VGA phase; older
fixtures have only the page and use a phase-zero approximation. No subsequent
native states or expected images are injected. Loading time is not simulated.

The synchronous snapshot path flushes tile/transform changes and rebuilds the
Godot Sprite2D and simple HUD draw commands before reading the backbuffer without
swapping it to the window. This is necessary because Godot defers draw-command
updates after texture changes. See Godot's
[CanvasItem redraw queue](https://github.com/godotengine/godot/blob/4.6-stable/scene/main/canvas_item.cpp)
and [Sprite2D drawing](https://github.com/godotengine/godot/blob/4.6-stable/scene/2d/sprite_2d.cpp).
The adapter supports this game's Sprite2D, scale-mode TextureRect, ColorRect, and
TileMapLayer rendering; adding custom `_draw()` nodes requires extending it.
Internal draws are excluded from replay screenshot frame counting. Headless state
checks do not attempt GPU readback.

`testing/test_wr1_video_clock.gd` checks checkpoint validation, owned input/output
pixels, delayed page selection, a row-150 mixed frame, and invariance to host call
partitioning. These are mechanism checks; they do not establish native parity.

`testing/test_wr1_presentation.gd` runs on the GPU and checks new sprites, frame
changes, replacement textures, immutable earlier images, and unchanged gameplay
state across several captures within one callback. All five checks passed.

The forced snapshot policy's full comparison is preserved in
`testing/output/parity/separate-video-verified/`: 2,913/2,913 state comparisons,
44/50 images, 533 validation timing differences, no execution/evidence errors.
It preserves the previous baseline. Eight video-clock checks and two engine input
integrity checks passed; the latter detect changed jump inputs and verify that
focus release cannot change replayed controls.

The earlier automatic-policy run is in
`testing/output/parity/separate-video-auto/`: 2,913/2,913 state comparisons and
50/50 images, with the same 533 validation timing differences and no execution
errors. This is a **mixed-policy** result: hard-impact uses measured VGA scanout;
the other 16 older recordings use snapshot presentation. It must not be presented
as 50/50 images under the full hardware policy. That run predates the recap-clock
fix and the removal of automatic snapshot fallback.
