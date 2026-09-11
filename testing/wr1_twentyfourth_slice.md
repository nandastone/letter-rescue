# Twenty-fourth slice: matching objects and player rendering work

The renderer planner now reaches file BA38, after both player image passes.
Python and Godot match 75 native intervals starting at renderer entry, including
1,075 generated graphics calls and every call's arguments, entry/pre-return
hardware/timing and the overall endpoint. This composes the preceding camera,
background, pickup, animation and door work with matching-object and player
rendering. It does not yet cover the rest of the renderer or a full game update.

## Question marks, words and pictures

`RendererWork.matching` covers B5F6..B9EC. The ordinary path checks each of the
seven locations' live attribute bytes, skips consumed words and suppresses the
last-touched location. It then applies the original visibility and screen-edge
clipping branches and generates the page-5 question-mark copy.

Active-word mode takes its separate original path. It compares grid coordinates
with the selected source, selects the active word rectangle there, and draws
pictures at other locations using `(attribute + picture_offset) % 7` and that
location's current picture phase. The source page is 4. Words use 64x16 clipping
limits; pictures and question marks use 24x24 limits. The planner preserves the
branch ordering, signed comparisons and integer division from the executable.

The new observer captures mode/index, selected and last-touched coordinates,
picture offset, seven pixel-coordinate/attribute triples and seven word source
rectangles. The attributes are read through the game's live far-pointer column
table. Later trace state is only an expected result, never an input to the
work generator.

The matching stage is renderer 0812:0ECC (file B9EC). There are 50 captured
question-mark states and 25 active-word states. The new section emits 32
question-mark, 25 word and 14 picture draws. All 933 cumulative calls through
this stage match in Python and Godot.

## Player image passes

`RendererWork.player` adds B9EC..BA38. DS:01BD controls visibility. When visible,
the selected DS:01C3 frame chooses the mask and color headers at DS:664A and
DS:734A plus 128 times the frame number. The destination is the camera-adjusted
player X and player bottom Y minus 32. The two passes use raster operations 1
and 2, respectively. Both include the masked-sprite helper's outer RETF when
composed into renderer work.

The entry snapshot contains the two source pointers and their 52-byte headers.
The work model derives each draw from these initial images and the generated
camera state. It does not take a later captured image header or future draw
arguments as input.

The player stage is renderer 0812:0F18 (file BA38). The 75 cases contain 71
visible and four hidden states, generating 142 player image calls. Captured
frame indices are 0, 1, 9, 22, 23 and 25. All 1,075 cumulative graphics calls
through the player stage match. The intervals span 17,547..57,976 guest cycles;
no timer-body entry occurs inside them.

## Evidence and validation

The authoritative capture is
`testing/output/wr1_matching_work_native.json/.jsonl/.map`. The hash-checked
fixtures are `testing/fixtures/wr1_renderer_matching.json.gz` and
`testing/fixtures/wr1_renderer_player.json.gz`, produced by
`prepare_wr1_renderer_matching.py` with and without `--player`. Both use the
common renderer fixture preparer to validate source hash, CPU configuration,
callback mapping, nested-call pairing and the renderer return address.

- 38 focused Python tests pass in 53.697 seconds, including original executable
  catalogue extraction and prior hardware/music/IRQ/keyboard/graphics coverage.
  Log: `testing/output/wr1_twentyfourth_python_tests.log`.
- Godot passes 706,287 cumulative checks across the six renderer fixtures, with
  zero failures. Log: `testing/output/wr1_renderer_player_godot.log`.
- The maintained observation patch reverse-applies cleanly to the core checkout.

This work does not add pixel comparison coverage, prove every clipping/frame
combination, or resolve IRQ delivery during rendering. The previous full-redraw,
scroll-direction and visible exit/blink coverage gaps remain. The next source
block, BA38..BC5E, renders enemies and drips. Remaining renderer and update work
must be composed before replacing the approximate runtime admission gate.
The prior 122 one-frame residuals, original PCM, broader gameplay/level coverage,
menus and ending remain open. Loading duration remains excluded and the
exact-clone goal remains active.
