# Live play and executable comparison — 7 September 2026

Follow-up: [runtime tracing now works](wr1_runtime_research.md), including stable
original memory reads and replay-frame counters. [Animation/RNG research](wr1_animation_research.md)
adds exact sprite rules and random-state information. The missing-trace statements
below describe the earlier exploration pass; basic tracing is no longer blocked.

Desktop play now works in both games. Physical scan-code holds using PyDirectInput
work alongside computer-use window selection and screenshots. RetroArch also needs
Game Focus on. We played both games through walking, jumping, book contacts, word
reveals and wrong matches. The original additionally showed an enemy encounter,
rescue animation and return to the start. These observations are exploratory,
not synchronized replay proof.

The strongest result is a concrete target recovered from WR1.EXE: integer movement
on an approximately 12 Hz clock, discrete camera following, and a matching state
machine different from the clone's current implementation. The existing first-frame
rendering work was preserved; no gameplay files were edited.

## Input problem resolved

[Input investigation](desktop_input_research.md) records experiments, sources and
the working procedure. The original sender produced a logical arrow but a physical
Pause key, with down/up about 1.3 ms apart and zero held physics ticks. A 120 ms
PyDirectInput hold produced the correct physical Right across nine probe ticks.
The reusable [input helper](../tools/game_input.py) checks the selected foreground
window and releases attempted keys in cleanup.

Both games visibly responded to walking and simultaneous right/up holds. This
supersedes the earlier report saying only scripted exploratory play was possible.

## Movement differs structurally

[Movement research](wr1_movement_research.md) identifies coordinate writes,
keyboard state, timer setup, collision samples and instruction order:

- Original: 8 pixels per gameplay update. PIT divisor 12,428 and an eight-interrupt
  gate imply nominally 12.000945 updates/sec, or 96.0076 walking pixels/sec.
- Ordinary held jump: nine 8-pixel rising steps, up to 72 pixels, followed by
  8-pixel falling steps. Release falls immediately; early re-press can resume the
  remaining rise window. Holding through landing jumps again.
- Vertical motion precedes separate left and right attempts. Collision reads
  specific cells in the raw 8-pixel attribute grid. Attribute 0x74 participates
  in climb patterns as well as support.
- Clone: 120 pixels/sec with floating-point gravity, jump cutting, coyote time and
  Godot collision response. Changing a few constants cannot reproduce all those
  original rules.

The [position-only reference](wr1_movement_reference.py) transcribes the recovered
movement block without changing the game. Nine [behavioral checks](test_wr1_movement_reference.py)
pass, covering jump height, release/re-press, auto-repeat, climbing, ceiling,
both horizontal keys and the asymmetric wall loop. Its transcription was checked
separately against the disassembly. These are assembly-derived acceptance examples,
**not runtime trace comparisons**. Animation, camera, interactions and 16-bit
overflow remain outside this model.

## Camera changes apparent jump height

[Camera research](wr1_camera_research.md) recovers one 8-pixel step per axis per
original renderer invocation, with horizontal render-X target 144 and bottom-Y
dead band 108–132. Initial and runtime bounds differ. Most calls follow a game
update; additional transition calls matter for exact parity.

The clone interpolates camera position every presentation update. **Correction:**
the earlier statement that its jump was higher relied on independently selected
screenshots. Those cannot establish world-space apex height because the original
scrolls vertically while jumping. The binary's 72-pixel ordinary-jump result is a
stronger target than that visual impression.

## Books collect internally, but their display is stale

The original visibly awards 5 points and removes each starting book. The clone's
instrumented live run started with 24 book entities. A 700 ms right hold moved the
player from x=39 to approximately x=123, removed two book entities and changed the
internal score to 20. The displayed score remained zero and the books stayed drawn.

**Correction:** the earlier inference that clone book pickups failed was wrong.
Confirmed differences are the 10-point reward instead of 5, missing removal of
background-stamped book art, and static HUD methods. The HUD deliberately stubs
dynamic score, slime, current-word and completion displays during the pixel rebuild.
An unchanged HUD is not evidence of unchanged gameplay state.

Temporary instrumentation: `output/live_game_inspector.gd` and score-change log
`output/live_inspector.log`. Its live JSON is overwritten and can reflect later
death/respawn; its final contents are not the original pickup snapshot.

## Current level-1 matching cannot complete

The [audit](audit_matching.gd) instantiates the production WordManager and block
scenes with the actual level-1 words. All **42 distinct ordered pairs fail**.
All seven picture textures are missing from the path the block loader uses.
Live clone play likewise showed text fallback instead of the original pictures.

[Matching research](wr1_matching_research.md) establishes the original model:

- Seven stable slots each have separate word and picture identities, calculated
  with two different cyclic offsets. Every source has a target at another slot.
- Success consumes only the source's word. Completed sources remain picture
  targets for later words. Seven successful sources unlock the exit.
- Wrong matches restore the source's availability and spawn a Gruzzle at the
  target. There is a last-touch suppression rule and a six-success exception.
- Success awards 20 points, with a 500-point bonus after seven if there were no
  mistakes. The clone currently awards 50 per match.

The clone assigns the same identity to each block's word and picture, then requires
another block with an equal word. Seven distinct words make that impossible.
Removing both blocks on success would also be wrong if identities were fixed.
The converter already sorts question locations by original numeric slot; preserve
that association explicitly when extending the data.

## Next implementation sequence

1. **Introduce an opt-in original-rule simulation.** Preserve the first-frame
   baseline. Retain raw attribute values and slot IDs, make coordinate origins
   explicit, and integrate integer movement on the original clock. Start with flat
   walking and ordinary jump/release/re-press away from interactions and climbable
   geometry. Log logical update, position, phase, sprite and camera.
2. **Apply camera and animation at original update points.** Use the recovered
   thresholds and frame sequences. Check world position stays invariant during
   camera-only changes. Handle extra transition renders separately.
3. **Make interactions and displays agree.** Implement independent word/picture
   identities and consumed-source state, restore extracted pictures, and validate
   seven-match completion. Fix book reward/disappearance and implement dynamic HUD
   drawing using original glyphs. Check both internal state and pixels.
4. **Repair deterministic replay alignment.** Compare the first divergent logical
   update, expanding from walking to jump, collision, camera and matching. Control
   character, difficulty, content, speed setting, RNG and word/picture offsets.
   Do not align by video frame number alone.
5. **Expand binary research to enemies, slime and transitions.** Live enemy
   interaction is observable, but its full state machine, death/restart semantics
   and timing were not recovered in this pass.

The first implementation should be integer movement, rather than another gravity
tuning pass. A full decompiler is optional: focused 16-bit disassembly has already
recovered small, directly testable algorithms. Runtime coordinate/phase traces
are the next stronger verification.

## Replay findings retained for the later harness pass

Earlier exploration used native `smoke.replay` and a separate controlled BSV2
route: 350 setup frames followed by 420 frames, with right at relative 70–249,
up at 140–167 and left at 280–349. Captures are under `output/`;
`playthrough_comparison.png` uses independently selected snapshots.

The production reader returned 2,082 frames from a recording declaring 1,309.
A temporary strict reader reached exact EOF at 1,309 and recovered held inputs.
The initial checkpoint length already includes metadata (the reader skips two
extra bytes); keyboard records are 12 bytes, not 10; later checkpoint lengths
must be read from their records. See `output/exploration_bsv.py` and the primary
[RetroArch replay source](https://github.com/libretro/RetroArch/blob/master/input/bsv/bsvmovie.c)
and [input structures](https://github.com/libretro/RetroArch/blob/master/input/input_driver.h).
The production reader was unchanged while desktop play was prioritized.

RetroArch restarted recording at resolution changes: 770 emulation frames yielded
744 recorded video frames. Video output cannot supply exact tick labels without
explicit mapping. A 70 Hz capture also samples a roughly 12 Hz game clock.

## Reproduce diagnostics

With Python and Godot on PATH, from the repository root:

```powershell
python -m unittest discover -s testing -p test_wr1_movement_reference.py -v
godot --headless --path . --script res://testing/audit_matching.gd
```

Expected reference result: nine passing checks. Expected current-clone audit:
42 attempts, zero successes, seven missing pictures. The audit diagnoses a blocker;
that output is not a desired regression expectation.
