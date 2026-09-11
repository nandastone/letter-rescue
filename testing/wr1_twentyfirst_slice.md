# Twenty-first slice: display page and renderer opening

The display-page model matches all 64 native calls in Python and Godot. A new
renderer planner also matches all 75 captured openings, from entry through
picture-counter updates, camera adjustment and drawing-page selection. The
planner generates the nested calls and their timing from the initial state;
recorded calls and later checkpoints are assertions only.

## Display page

`GraphicsWork.display_page` covers file `17606..17695`, stopping before the outer
RETF 2. It resolves the live device, checks the video mode, writes the game's
selected display page at DS:4879, and invokes BIOS INT 10/AH=5. The logical
result includes BIOS active page and display-start offset as well as game state.

The DOSBox callback performs eight host port writes while counting as one guest
callback instruction: four CRTC writes select display start and four update
the cursor. This is visible in the captured core's `INT10_SetActivePage` and
`INT10_SetCursorPos` implementations in `src/ints/int10_char.cpp`. Both models
use that operation count and the existing 19-cycle OUT cost. No measured call
duration is supplied to the work planner.

The observer retains BDA page, start, page size, columns, CRTC port and cursor
positions. Evidence is `testing/output/wr1_display_work_native.json/.jsonl/.map`
and the hash-checked fixture `testing/fixtures/wr1_display_work.json.gz`.

## Renderer opening

`tools/wr1_renderer_work.py` and `scripts/wr1_renderer_work.gd` generate original
instruction paths from file `AB25` through the return from drawing-page
selection at `ACC5`. The model preserves signed word comparisons, animation
counter wrap, camera thresholds and the original one-eight-pixel-step-per-axis
behavior. It generates drawing-page arguments and includes the nested helper's
outer RETF, which independent primitive fixtures intentionally stop before.

The new native stage probe is renderer segment 0812, IP 01A5. Renderer entry
and this stage include camera/player coordinates, dimensions, selected page,
seven picture counters, phases, HUD slots and two sets of source rectangles.
`prepare_wr1_renderer_prefix.py` retains the initial hardware/device checkpoint
and subsequent expected state and child boundaries separately.

Evidence is `testing/output/wr1_renderer_prefix_native.json/.jsonl/.map` and
`testing/fixtures/wr1_renderer_prefix.json.gz`. There are 75 completed openings:
29 without camera movement, 33 scrolling downward and 13 scrolling right and
down. Each generates one drawing-page selection. All have picture animation
enabled, but all seven HUD slots are unoccupied, so no animated HUD copy is
generated. These openings include additional transition renders beyond the
64 complete ordinary updates in earlier graphics profiles; they are not 75
complete updates.

Verification checks the complete prefix state and hardware endpoint, plus the
generated call's arguments, entry hardware/time and pre-return hardware/time.
It starts from one checkpoint for each entire opening, rather than resetting
the clock at the child call. There are no timing offsets or future trace paths
in the planner.

Left/up camera branches and occupied animated HUD slots need additional native
coverage. The planner generates HUD source page 4 and destination page 5 from
the actual push order at ABFF..AC19. Non-byte-aligned copies still explicitly
fail in the copy primitive. No claim is made for those unverified paths.

## Validation

- 32 focused Python tests pass in 22.889 seconds, including extraction against
  the original executable and previous music, IRQ, idle, keyboard and graphics
  fixtures. Log: `testing/output/wr1_twentyfirst_python_tests.log`.
- Godot graphics: 173,038 checks, zero failures, covering 129 drawing-page
  selections, 1,050 aligned copies, 198 masked draws and 64 display selections.
  Log: `testing/output/wr1_display_godot.log`.
- Godot renderer: 24,892 checks, zero failures, covering all 75 opening
  endpoints and child-call boundaries. Log:
  `testing/output/wr1_renderer_prefix_godot.log`.
- The maintained observation patch reverse-applies cleanly to the captured
  DOSBox Pure source checkout.

The renderer is only modeled through ACC5. Background scrolling/tile work,
remaining renderer decisions, game-update work and interrupt delivery during
updates still need composition with the verified idle clock. The runtime's
approximate admission gate and prior 122 one-frame residuals remain open.
Audio PCM, broader gameplay/level coverage, menus and ending remain open too.
Loading duration remains outside comparison scope: synchronization starts at
the first playable level frame. The exact-clone goal remains active.
