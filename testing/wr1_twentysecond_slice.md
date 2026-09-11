# Twenty-second slice: fills and continuous background redraw work

The renderer planner now matches all 75 native entry-to-background-cache
intervals in Python and Godot. It generates 718 graphics calls from the initial
camera, picture, tile-table and graphics state. Every call's arguments, entry
and pre-return hardware/timing, and the complete interval's endpoint match.
The clock is not reset at nested graphics calls.

This extends the previous opening model from file ACC5 through B191. The
renderer still continues beyond B191; this is not a full-update timing result
or a new pixel-comparison result.

## Recovered fill primitives

Three newly observed helpers support scrolling:

- `fill_style`, file F508..F557: pattern, color and transparency state. The
  planner stops before its outer RETF 6.
- `fill_rect`, file F174..F3CE: rectangle normalization, fill-style dispatch,
  temporary color state, the nested raw fill and restoration. The supported
  game path is a solid filled rectangle (mode 2), with no coordinate transform,
  outline, pattern or non-copy raster operation. It stops before RETF 10.
- `fill_raw`, file CE38..CF1B then D2FA..D3A0: dispatches through the live mode
  record, computes EGA byte positions, emits register writes and fills rows.
  It includes the coordinate helper at D2D1 and stops before RETF 8. It models
  instruction work, not framebuffer contents. Initialization and clipping are
  still unsupported; current samples have both already resolved/disabled.

The hardware block runner now recognizes a far indirect jump (`ljmp`) as a
block terminator, as required by the raw fill's dispatch at CF1B. No timing
constant was fitted to the capture.

Authoritative evidence is `testing/output/wr1_fill_work_native.json/.jsonl/.map`
and `testing/fixtures/wr1_fill_work.json.gz`. Its 64 complete ordinary updates
contain 128 fill-style changes, 58 wrapper fills and 58 nested EGA fills. Of
the rectangles, 45 cover the 288x8 bottom strip and 13 the 8x152 right strip.
All sampled fills are byte aligned and have no intervening timer IRQ. The
source-derived partial-byte and coordinate-reordering paths need further
native coverage. The original other graphics calls remain in the fixture.

## Renderer composition

The new observer records the live far-pointer source-X/source-Y tile columns,
background color and full-redraw flag. It adds renderer stage 0812:0671
(file B191). `prepare_wr1_renderer_background.py` verifies the capture hash,
CPU configuration, mapped callbacks, nested call pairing and renderer return
address. It preserves the initial entry checkpoint separately from all expected
calls and endpoints. The calls in the fixture are not planner inputs.

The planner performs the original sequence:

1. Picture counters, camera steps and drawing-page selection from slice 21.
2. Shift the cached background from page 2 to the current drawing page.
3. Set fill style and clear newly exposed horizontal/vertical strips.
4. Look up the newly exposed tile columns/rows. Skip cells whose source X is
   negative; generate source-page-3 copies for the other cells.
5. Copy the updated 288x152 viewport back into page 2.

Evidence is `testing/output/wr1_background_work_native.json/.jsonl/.map` and
`testing/fixtures/wr1_renderer_background.json.gz`. There are 75 completed
intervals, including transition renderer invocations: 29 stationary, 33 scrolling
down and 13 scrolling right/down. These generate 509 copies, 75 drawing-page
selections, 75 fill-style changes and 59 filled rectangles. Intervals span
14,615..42,601 guest cycles. No timer-body entry occurs inside these intervals.

All observed full-redraw flags are zero. The full-rebuild branch explicitly
remains unsupported. Left/up scroll paths are recovered from source but not
native-verified here. More varied routes, interruptions and full rebuilds still
need coverage; matching this fixture does not establish those paths.

## Validation and remaining work

- 34 focused Python tests pass in 27.230 seconds, including original-executable
  catalogue extraction, previous clock/music/IRQ/keyboard tests, all graphics
  fixtures and both renderer fixtures. Log:
  `testing/output/wr1_twentysecond_python_tests.log`.
- Godot graphics: 213,671 cumulative checks, zero failures. Log:
  `testing/output/wr1_fill_godot.log`.
- Godot renderer: 131,875 cumulative checks, zero failures, covering 75 opening
  and 75 background intervals and their generated child-call boundaries. Log:
  `testing/output/wr1_renderer_background_godot.log`.
- The observation patch reverse-applies cleanly to the captured core checkout.

Next is the pickup and animated-background work beginning at B191, then the
rest of renderer and game-update composition. The runtime admission gate is
still approximate and its earlier 122 one-frame residuals remain unresolved.
Original audio PCM, broader routes/characters/difficulties/levels, menus and
ending remain incomplete. Comparisons continue to synchronize after loading
at the first playable frame. The exact-clone goal remains active.
