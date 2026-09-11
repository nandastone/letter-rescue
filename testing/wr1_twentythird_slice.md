# Twenty-third slice: pickups, tile animation and doors

The continuous renderer work model now reaches file B5F6. Python and Godot
match all 75 captured entry-to-door-section intervals, including 862 generated
graphics calls, their arguments and entry/pre-return hardware checkpoints,
the overall timing endpoint, animation phase and entrance countdown.

This is a work/timing result for the captured route, not a new framebuffer
comparison or proof of a complete update. Question/word/picture rendering,
player/enemy drawing and the remainder of the renderer still follow B5F6.

## Pickup and animated-tile section

`RendererWork.tiles` extends the background-cache model from B191 through B368.
It checks the seven mystery-pickup positions against the original tile-space
viewport, generates page-2 atlas copies for visible pickups, advances DS:41BE
once, and traverses the animated-cell list. Animation wraps after phase 3,
even when there are no visible animated cells. Duplicate list coordinates are
processed individually with the same phase.

The observer records seven pickup coordinate pairs from DS:B8EF/B97D, the
animation phase, DS:9E72 count and DS:C18B/C26B coordinate pairs. The initial
tile-source table comes from the existing background snapshot. The stage probe
is renderer 0812:0848 (file B368).

Evidence: `testing/output/wr1_tiles_work_native.json/.jsonl/.map` and
`testing/fixtures/wr1_renderer_tiles.json.gz`. All 75 captured states have 15
animation entries. Initial phases 1, 2 and 3 appear 19 times each, and phase 0
18 times. The added section generates 20 pickup copies and 94 animated-tile
copies. Together with earlier renderer work this is 832 calls. Intervals span
16,348..43,679 guest cycles.

## Exit and temporary entrance

`RendererWork.doors` extends B368 through B5F6. It computes original camera
projection offsets, checks exit visibility and generates the clipped exit
copy when visible. It then processes the entrance timer at DS:C3DD. A nonzero
timer decrements once per renderer invocation. At ten or below, drawing page
zero suppresses the entrance draw; otherwise the original visibility and
clipping path runs.

The native exit and entrance clipping paths differ at their bottom edge: the
exit's signed expression subtracts four attr cells, while the entrance's
subtracts five. The models preserve those separate expressions rather than
assuming identical clipping. Both use source page 5 and the character value at
DS:018E (the observer's legacy field name is `theme`).

The observer records that character value, exit DS:99B0/9AF2, entrance
DS:AEBE/B88C and countdown.
The stage is renderer 0812:0AD6 (file B5F6). Evidence:
`testing/output/wr1_doors_work_native.json/.jsonl/.map` and
`testing/fixtures/wr1_renderer_doors.json.gz`.

The 75 intervals cover initial timer values 59 down through 1 once each and
zero 16 times. There are 30 visible entrance copies: 26 at full 32x40 size and
four progressively clipped at the top. The exit remains offscreen, so its
visible drawing path is source-derived but not verified here. The late blink
branches execute after the entrance has left view; this is not visual coverage
of a blinking on-screen entrance. No timer-body entry occurs inside the
measured entry-to-door intervals. Their duration is 16,374..43,720 guest cycles.

The full cumulative call counts are 653 copies, 75 drawing-page selections,
75 fill-style changes and 59 filled rectangles. Each model starts with one
renderer-entry checkpoint. Subsequent checkpoints and recorded calls are only
expected outputs; they are never supplied as timing/path inputs.

## Validation

- 36 focused Python tests pass in 37.792 seconds, covering executable catalogue
  extraction and previous hardware/music/IRQ/keyboard/graphics fixtures plus
  all four renderer intervals. Log:
  `testing/output/wr1_twentythird_python_tests.log`.
- Godot passes 386,455 cumulative renderer checks with zero failures across
  the opening, background, tile and door fixtures. Log:
  `testing/output/wr1_renderer_doors_godot.log`.
- The maintained observation patch reverse-applies cleanly to the core checkout.

Next is the question/word/picture renderer at B5F6, then player and enemy work.
Full background rebuilds, additional scrolling directions, visible exit/blink
coverage and interrupts during rendering still need verification. The runtime
admission gate and earlier 122 one-frame residuals remain open. Original PCM,
all routes/characters/difficulties/levels, menus and ending remain incomplete.
Loading duration is still excluded; comparisons begin at the first playable
level frame. The exact-clone goal remains active.
