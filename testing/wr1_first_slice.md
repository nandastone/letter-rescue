# First original-rules implementation

2026-09-07. The clone now has an opt-in original-rules player, camera, player
animation and background animation. The existing default mode remains available.

## Results

- **Starting image: 0 differing pixels out of 64,000** against
  `testing/sentinels/smoke_start.png`, at the initial original-rule state. The new
  sprite metadata and coordinate projection replace the old empirical placement.
- **Legacy image: 0 changed pixels** against an isolated copy of the pre-change
  working-tree scripts. Existing user edits to the idle sprite and game rendering
  were preserved. Both comparisons use RGB pixels, not PNG file-byte equality.
- **26 native movement updates agree exactly:** eight walking updates and 18
  full-jump updates, checking render/world/grid coordinates, phase, facing, sprite
  and camera from the same captured starting states. The jump rises 72 pixels.
- **305 model checks pass**, including the native fixtures, release/re-press,
  climbing, ceiling contact, asymmetric side collision, simultaneous directions,
  idle transitions, facing lag, camera boundaries and background phase cycling.
- The full player scene passes the same 26 native updates plus screen projection,
  sprite selection, nominal clock and no-backlog-after-stall checks.
- Live keyboard walking and jumping worked in the new mode. A 350-physics-frame
  replay completed and emitted 60 state records (initial state plus 59 updates).

The native jump was newly recorded for this pass: Up at replay frames 420–479,
without horizontal input. The 18 movement changes occur at 425–524. The native
background trace independently showed frame 0 at 549–553, frame 1 at 554–558 and
frame 2 at 559–562. These are frontend replay indices, not logical-update counts.

The original's initial facing was resolved dynamically: the captured level-1 jump
starts facing right, frame9. This supersedes choosing left solely from the setup
function's earlier facing write.

## Implementation

- [wr1_motion.gd](../scripts/wr1_motion.gd) owns integer movement, original animation
  state and camera/render steps. Input axes remain separate; vertical decisions
  precede left and right attempts. There is no gravity integration or
  move_and_slide in this mode.
- [player.gd](../scripts/player.gd) samples input at the nominal original rate,
  applies the state to the existing player node, and optionally writes JSONL.
- [camera.gd](../scripts/camera.gd) projects world coordinates with the recovered
  offsets and no smoothing in original mode.
- [game.gd](../scripts/game.gd) loads original attributes and updates animated
  background cells at the original render point. The background phase carries
  across reloads of the same player instance; full restart/transition parity is
  still outside this slice.
- [extract_wr1_rules.py](../tools/extract_wr1_rules.py) generates 15 raw attribute
  maps and 26 exact atlas frames for each character from the researched data. The
  current clone uses the girl atlas. Legacy maps and sprites are not regenerated.

Background timing is based on [additional disassembly](wr1_background_animation_research.md):
one phase advance per original renderer call, not six Godot physics ticks. Fresh
render phase 1 matches the saved starting image. Saved-state continuation must use
the captured phase instead of assuming 1.

## Run

With Godot on PATH, from the repository root:

```powershell
# Start directly in the level using original rules.
godot --path . res://scenes/game.tscn -- --original-rules

# Optional per-update numeric state log; the parent output directory must exist.
godot --path . res://scenes/game.tscn -- --original-rules --state-trace testing/output/live_wr1.jsonl

# Native-state acceptance and actual player/camera integration checks.
godot --headless --path . --script res://testing/test_wr1_motion.gd
godot --headless --path . --script res://testing/test_wr1_integration.gd -- --original-rules

# Capture the initial original-rule image with the fixed presentation clock.
godot --path . --fixed-fps 70 --script res://testing/capture_wr1.gd -- --original-rules --settle-frames 3 --capture-output D:/Work/letter-rescue/testing/output/original_rules_initial.png
```

Omitting --original-rules selects the unchanged legacy simulation. Import newly
generated PNGs in Godot before running a fresh checkout. The generator requires
the researched WR1.EXE and level files plus the already-decoded CHARS/STATIC sheets.

State rows contain logical tick, Godot physics frame, exact held inputs used by
that update, render/world/grid coordinates, jump and animation counters, camera
and background phase. Tick 0 is an initialization record, with an empty held map.
The native reader now also records background phase at DS:41be.

## What this does not establish yet

This proves the recovered state transitions for the selected traces, and the
initial rendered image. It does **not** establish whole-game frame-for-frame
parity from boot. The nominal timer is scheduled on Godot's 70 Hz physics clock,
retaining fractional remainder during normal scheduling and dropping backlog
after a stall. Exact original IRQ phase, rendering cost and modal delays still
need synchronization through the comparison harness.

The larger game retains its existing interaction logic: book rewards/art removal,
HUD updates, word matching, enemies, slime, sound and death transitions still need
work. In particular, the known level-1 matching blocker remains. Safe out-of-map
behavior is defined for the clone rather than reproducing undefined DOS memory
reads. Sixteen-bit overflow and all transition-specific renderer calls are not
modeled.

Accelerated headless replay exits report outstanding audio playback resources.
The same warning was reproduced in legacy mode; the numerical tests and graphical
captures exit cleanly. Audio lifetime during accelerated shutdown was not changed.

## Evidence

Saved native observations are in
[walking fixture](fixtures/wr1_left_walk.json) and
[jump fixture](fixtures/wr1_full_jump.json). Each records the starting state and
expected updates independently of the clone implementation.

Generated evidence under testing/output includes original_full_jump_trace.json,
original_background_trace.json, original_rules_initial.png and its state JSON,
baseline_before.png, baseline_after.png, original_slice_image_checks.json and
original_preview_trace.jsonl. The baseline copy uses saved pre-change working-tree
scripts, including the user's uncommitted rendering changes, rather than HEAD.
