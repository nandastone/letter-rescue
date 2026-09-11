# Native demos: maintained gameplay parity suite

The default `just parity` suite is now all 15 demos, in the original order:
4, 1, 10, 12, 14, 15, 2, 5, 8, 11, 9, 3, 6, 13, 7. Missing evidence is an
error. The manually authored level routes have been retired from the default
suite; their tools and native evidence remain historical research material.
The saved suite covers 22,460 ordinary updates, 196 reference screenshots, and
15 terminal observations. All measured states, inputs, endings and screenshots
have passed; three strict admission-counter differences remain.

## Findings while expanding the suite

- Level 4 now passes 1,624 ordinary states, consumed inputs, all 11 sampled
  images, admission timing and terminal rescue timing. The prior pilot below
  records the earlier red result. The complete result is
  `output/parity/demo-level4-clock-complete/report.md`.
- Level 15 passes 851 ordinary states, all seven sampled images and its ending.
- Level 14 passes 1,217 ordinary states, all 11 sampled images and its ending
  after correcting picture animation order and using a displayed checkpoint.
- All fifteen native recordings, decoded controls, post-load checkpoints,
  ordinary/terminal states and sampled screenshots are now preserved. Boundary
  evidence is losslessly compressed; old uncompressed copies remain in output.
- Focused runs have passed levels 4, 1, 10, 12, 14, 15, 2, 5, 8, 11, 9, 3 and 7.
  Level 6's last screenshot now passes its focused capture. Level 13's recap
  and terminal timing now pass. Three isolated ordinary admission comparisons
  remain open: level 6 tick 1474, level 13 ticks 662 and 956.
- The completed sequential all-fifteen run is in
  `output/parity/all15-background-capture/`, using one rendered playback per demo
  for both state and screenshots. All 22,460 ordinary states, consumed controls,
  15 endings (including their timing) and its 175 screenshots passed, with no
  missing captures or engine errors. The strict gate exits 1 for the three
  admission differences above; 13 of 15 demos pass every dimension.
- A subsequent close-up check added 21 consecutive reference frames around
  those three admissions. All 21 match without shifting frames. Five repeated
  control screenshots and their paused states agree with the previous native
  recordings, and both clone traces equal the corresponding full-run prefixes
  exactly. These frames and hashed acquisition records are now in the maintained
  pixel manifests, increasing the default coverage to 196. This is the original
  175-image full batch plus validated supplemental prefixes, not a second full
  batch with 196 captures. See its `expanded-evidence.md` for the combined record.
  Green sampled screenshots do not establish equality for every displayed frame.

The combined playback was checked against the prior level-15 headless run:
all 853 trace rows were identical, and all seven images and the terminal return
passed. The initial `all15-demos-scene-work` batch preserved two offscreen-death
work-planner errors (levels 14 and 15); both were corrected and passed focused
reruns. That earlier mixed-code batch is not the final suite result.

The subsequent batch was paused by the user after eight passing demos. Levels
8 and 11 lost screenshots while their gameplay continued. A short level-11
experiment reproduced that failure by minimizing the window at source 1000:
source 1009 was missing although gameplay reached 1020. The capture loop now
explicitly draws the viewport after process callbacks instead of waiting for a
normal window redraw. The regression compares all requested images and entire
state traces across three window modes; all are identical. Captures still read
Godot's actual framebuffer. The runner starts its windows minimized.

### Music and frontend clocks

Music repeats can delay IRQ service long enough for PIT edges to coalesce. The
game clears its entire timer when admitting an update; preserving a fractional
eight-tick remainder incorrectly admits later work early. `wr1_music_clock.gd`
uses the recovered music/OPL/PIC instruction work from a single initial hardware
checkpoint, rather than future native admission times.

The frontend follows the VGA callback queue and millisecond handoff, including
float32 rescheduling. Its advertised refresh rate alone is insufficient.
CPU block completion at a millisecond boundary remains a source of subframe
uncertainty; this is kept visible in the strict admission checks.

The three remaining long-run admission differences were isolated using the
native completed update immediately before each disputed gate as a **test-only**
checkpoint. The recovered idle/IRQ/dispatch model then predicts all three
next-admission CPU cycles exactly (zero-cycle error). The gameplay run still
uses only its original post-load checkpoint. This local experiment points to
omitted main-update CPU work losing the instruction/block phase carried into
later idle waits; it does not justify replaying later checkpoints in the game.
Adding idle polling alone did not remove the long-run failures and was reverted.

`test_wr1_demo_update_work.gd` preserves those three windows as a roughly
two-second diagnostic (214 assertions). Movement, contact and renderer work
each use their own native stage-entry state, and their combined instruction
cost reproduces the completed-update hardware state. The following idle wait
now starts from that **computed** hardware result, with the initial timer reset,
and reaches the next admission at the exact CPU cycle. It does not load the
observed completed-update checkpoint. This is still narrower than a complete
gameplay prediction from one checkpoint: intermediate contact and renderer
entry data remain test inputs. It does not close the full-run timing failures.
`prepare_wr1_demo_update_work.py` records the source hashes and original windows.

Control experiments distinguish the effects. Starting at each preceding native
admission, the current instantaneous-main/coarse-idle clock is early by 14, 23
and 4 CPU cycles respectively, reproducing the full-run errors. Recovered idle
polling with main work omitted gives errors of 0, -4 and +12 cycles. Including
the recovered stage work and idle path gives 0, 0 and 0. Merely committing the
clock's pending instruction count leaves every full-prefix mismatch unchanged.
These experiments are preserved under `output/probe_clock_*` and
`output/demo_admission_{baseline,commit}.log`. No speculative clock adjustment
was applied to gameplay. Integration must account for main work and idle phase
together and keep frontend handoff on that same timeline.

The repeatable clock-only probe is `just clock-probe LEVEL UPDATE_COUNT OUTPUT`.
Level 6 through 1,476 admissions reproduces the single counter difference;
level 13 through 958 reproduces both. A ten-admission control passes, and a
prefix reaching recap is rejected. Reports under `output/clock-probe-maintained-*`
record the same -14/-23/-4 cycle differences and exit nonzero. This is a
diagnostic shortcut, not a second gameplay suite or an allowed residual list.

Integration has explicit unfinished instruction paths: contact matching
outcomes and pickups; active enemy and slime work; rescue scoring during world
rendering; and updates to the live speaker sequence. The existing three-window
diagnostic covers inactive speakers, no drips/slime request, and offscreen
enemies. Its zero-cycle result cannot establish those missing paths. The live
music and frontend clocks also need one shared main-work timeline before the
diagnostic can be promoted to an exact runtime clock.

The contact pickup boundary is a far call at file C544/C6C3 to
`06DD:0B7E` (file A34E), not a fixed-cost counter increment. The dispatcher
clears the touched attribute at A392 and selects mystery letters (A3A1), books
(A7C5), or slime buckets (A611). Those paths restore saved background tile
coordinates, perform graphics copies, and may redraw HUD text or change score
and speaker state. A66F..A69D applies the difficulty-specific slime refill and
calls the meter renderer. A93E increments the book count and branches at twenty.
These offsets were checked directly against the supported executable hash;
they identify the work to model, not newly validated runtime timing behavior.

`tools/index_wr1_trace.py` builds an offset/time index beside a raw JSONL trace.
It makes these small native windows accessible without repeatedly scanning
gigabyte recordings. Queries read the original bytes, reject changed source
files, and never substitute indexed state into the runtime.

The demos do not all start with the same CMF. The initial 16-byte driver header
distinguishes WR1.6 but cannot distinguish WR1.4 from WR1.5. New captures also
read 64 immutable bytes of the loaded CMF from paused RAM. These distinguish
all three assets without consulting future gameplay or timing. The reader
accounts for DOSBox Pure's relocated game/OS memory descriptors. Ambiguous old
captures require an explicit, independently verified `--music` asset.

### Gameplay and rendering fixes

The 20-book hint paints the mystery word into saved page 5. The next collected
letter paints only its prefix (A59D..A5FD); clearing the whole footer erased the
uncollected hint. The HUD now preserves that suffix. The native level-10 crop
failed the GPU regression before the fix and passes afterwards.

The loader caches picture locations by its column-major map scan. B781 uses
that location ordinal for animation, while matching uses each cell's stable
attribute ID. Sorting blocks by matching ID and using the same index for their
animation gave bats, ants and other pictures the wrong phase. The clone now
maps matching IDs to the original location order. Matched HUD pictures retain
their separate word-index phase, as AB25..AC27 do.

Recap helpers reset the game timer before each wait. They must count serviced
IRQs, and drawing must stop while an IRQ handler runs. Ignoring that preemption
could finish a drawing call before the next timer reset and lose a whole wait
tick. The serviced-clock recap restores level 12's exact ordinary and terminal
timing. Rescue waits also count serviced IRQs, fixing one-frame terminal
differences on levels 9 and 3 without changing their gameplay states.

### Scene-dependent drawing work

The fixed recap workload from the earlier level-one experiment understated
level 13's scenic renderer. Six timer resets fell on the wrong side of an IRQ;
the recap ended about 64 ms early. `wr1_scene_work.gd` now adapts the current
scene to the recovered renderer work planner, including scenic backgrounds,
empty animated-tile calls, reward text, actors, and foreground lists. Benny
blits use the loaded sprite geometries. Remaining outlined-panel and dissolve
pixel operations use shared IRQ-free workload estimates, with their ranges
and provenance in `data/wr1/recap_overlay_work.json`. The transfer loop retains
its earlier separate profile. These are operation costs, not per-demo delays.

The first level-13 recap world draw matches the native return CPU cycle and
hardware state exactly from its entry checkpoint: 243 assertions in
`test_wr1_demo_renderer.gd`. The full recap's last drawing is within about
one microsecond of the native observation; all 1,627 ordinary states, thirteen
sampled images and the terminal return match. Two earlier admission counters
remain separate failures.

Ordinary presentation uses complete world work where the planner supports the
scene, and its explicit minimum-work fallback elsewhere. Entrance drawing and
rescue scoring remain unsupported full-work paths. No
native future renderer state enters the actual game. Scenic restoration fixed
level 11's stale pose. Level 6 exposed repeated entries in its foreground list:
Godot stores one tile per coordinate, but DOS performs every listed blit,
including duplicates. Preserving those duplicate workloads moved the page
switch past the VGA latch and fixed the counter-2000 camera screenshot.

The graphics planner now also follows both forward and backward unaligned EGA
copy paths (`13D7C..1413D`). HUD picture slots are spaced 23 pixels apart, so their
copies frequently cross byte boundaries. `test_wr1_demo_copies.gd` checks six
native copies in each direction, with 925 assertions covering return cycles,
hardware state and clipped arguments. The fixture is preserved by
`prepare_wr1_demo_copies.py`. This removes the prior HUD-animation fallback.

Static instruction-span expansion is cached within each work planner. In the
repeated native recap-draw experiment, construction fell from approximately
66 ms to 17 ms; state still chooses each branch, and hardware execution is
unchanged. Graphics, movement, contacts, text and the demo-derived hardware
experiments all retained their exact results. Skipping unsampled GPU display
frames did not materially improve playback speed and remains an output-only
experiment, outside the maintained runner.

### Sprite layers and native mask bytes

The original draws normal actors before foreground tiles, then slime afterwards
(BA38, BD6A, BD79..BF50). Pooled slime sprites now use that later layer, fixing
the level-8 ladder overlap.

The level-3 screenshot isolated 21 wrong pixels in slime frame 8. A paused
post-load RAM capture preserved all nine loaded AND/OR image pairs. Decoding
the native buffers corrected twenty EGA colour-6 pixels and one opaque black
mask pixel. `wr1_slime_assets.json.gz` preserves the buffers; the extractor and
`test_wr1_native_sprites.py` reproduce and check all nine assets. Level 3 now
passes 1,347 updates, ten sampled screenshots and its terminal timing.

### Isolated native acquisition

A failed level-6 recapture consumed only 172 inputs because live Ctrl/Alt/Shift
release events leaked into the recorded demo and triggered its keyboard abort.
The BSV contained no such events. Native acquisition now selects RetroArch's
null host input driver, and preparation rejects keyboard activity within the
demo. The isolated retry consumed the full route and reached its normal death.
The failed and contaminated attempts remain preserved as failed evidence.
The null driver is implemented in RetroArch's
[input-driver source](https://raw.githubusercontent.com/libretro/RetroArch/master/input/input_driver.c).

## Original pilot history

The original demos are useful regression routes. This pilot decodes WR1.D3,
launches it through the real Run demo menu, independently checks its input bytes
against the instruction trace, and replays the same bytes in the actual clone.

## Measured result

- **1,624/1,624 ordinary gameplay updates match**, after one untouched post-load
  checkpoint at counter 500. Positions, motion, contacts, scores, matching,
  actors, RNG, and render-driven animation state use the existing parity fields.
- The **terminal pit rescue's state and consumed controls also match**. Demo
  main returns after rescue without reaching the ordinary D72 completion hook,
  so this is an explicit separate comparison, not a fabricated ordinary update.
- **10/11 sampled images match exactly**, including the initial screen and a
  frame during the terminal rescue. Counter 9000 remains a timed presentation
  difference. This is sparse image coverage, not an all-video-frames claim.
- The strict timed gate remains red: 619 ordinary admission-counter differences;
  final rescue completes at native counter 10190 versus clone 10189. Gameplay
  controls are read by update in the original demo itself, so these shifts do
  not change the consumed controls as they can in frontend-keyboard routes.
- Fresh state runs of all 19 previous scenarios retain their previous results.
  This includes the already known timed-input divergence on `level3_long`.
- 17 focused Python tests passed with the real Godot checks enabled. The GPU
  presentation regression passed 9 checks. Its new partial-refill assertion was
  observed failing before the fix and passing afterwards.

Evidence: `testing/output/parity/demo-level4-verified/report.md`,
`testing/output/parity/demo-regression-states/report.json`,
`testing/output/demo_tests.log`, and `testing/output/demo_refill_{before,after}.log`.
Earlier red runs remain in `testing/output/parity/demo-before` (no demo adapter)
and `demo-level4-first` (the meter bug still present).

## Input format, confirmed from the executable

Addresses below are **file offsets** in WR1.EXE SHA256
`b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`.

The loader at 964A–96AC opens `wr1.d<level index>` and reads up to 4000 bytes
into the far buffer at DS:9840. At each admitted main update, 3727–379C reads
one byte indexed by SS:BP-2. It tests the stop bit before applying any controls.
40CF increments the index after the ordinary update finishes.

| Bit | Input |
| --- | --- |
| 01 | Up / jump |
| 02 | Down |
| 04 | Right |
| 08 | Left |
| 10 | Slime request |
| 20 | Stop before executing this update |

The two high bits are unused in the supplied files; the decoder rejects them
in playable bytes rather than guessing an extension. A stop byte may have other
bits set: they are not applied. Bytes after the **first** stop are not played.

All 15 files were decoded. Their sizes, hashes, playable lengths and trailing
byte counts are saved in `testing/fixtures/wr1_demo_inventory.json`. Notably,
WR1.D8 contains 71 bytes after its first stop marker. WR1.D10 is the shortest,
with 462 playable updates; it has not yet been captured or clone-verified.

## Launch and demo-specific rules

The original menu has a Run demo entry (index 11). This capture opens the menu
with Escape at frontend frame 400, moves up twice at 420 and 430, then presses
Enter at 450. All frontend controls are released from 454 onward. The original
then supplies its own demo controls. No executable or game memory is patched.

The menu starts from the current level index and uses the DS:00A0 permutation:
`3,0,9,11,13,14,1,4,7,10,8,2,5,12,6` (zero-based levels). Thus the fresh level-1
session starts the level-4 demo. This is why the first pilot uses D3 rather than
the shortest file.

The binary and runtime capture confirm:

- 9711 forces DS:017E to 2: **hard difficulty**. 9728 clears DS:026D, the used
  slime count. These are distinct fields; clearing 026D does not select easy.
- 4EA7–4EAD fixes word rotation 3 and picture rotation 2. These values are also
  observed in the initial checkpoint.
- 34AD, 36E4 and 3714 seed RNG with 200 around entry/loading. More importantly,
  50F4–5105 reseeds with 200 on **every entity update**, after contacts and before
  slime processing. The clone's demo adapter reproduces that exact placement.
- Wrong-match spawns at C4AE–C4C8 use `slot % 4` and consume no random number.
  The clone applies this only in demo mode. Fresh map decoding also temporarily
  uses slot types at 667C–6690; reset then assigns randomized types at 5094.
  The post-load checkpoint captures the final initial actor setup.
- 40C8–40CD returns from demo main after a rescue instead of restarting the level.
  The replay process likewise ends after completing the rescue. The original
  menu/attract screens and restoration of the previous player session are outside
  this gameplay adapter's scope.

This does not change ordinary gameplay's RNG, enemy selection, or controls.
The replay contains only decoded input bits plus its single initial state;
later native states remain exclusively in the comparison fixture.

## The ending is a death, not the stop marker

WR1.D3 is 1634 bytes: 1633 input bytes followed by 20. In this recording, the
original executes inputs 0–1630 as ordinary completed updates, then input 1631
falls into the pit. It completes the rescue and leaves demo mode without reading
input 1632 or reaching the terminator. All 1632 consumed bytes — **8160 input
bits** — agree with the decoded file. Seven idle updates precede the clone's
checkpoint; the compared ordinary span is therefore 1624 updates.

The parser requires the terminal admission and observed rescue lifecycle, and
preserves them as `demo_terminal`. It does not discard an arbitrary partial
instruction group. `01A3:0969` is file 4D99, the **start of the return walk**,
not the end of rescue. The terminal comparison uses the last observed
`01A3:0A0C` at file 4E3C, after the final walk wait, when X has reached the saved
spawn X. Subsequent screen erasure and function return do not change the compared
gameplay fields. The final pose is X48/Y120, sprite 17; score 950, death true.

## Ordinary-game bug exposed by the demo

At counters 2000 and 3000, the clone's slime meter differed by one four-pixel
column at X33/Y20–23. Bucket pickup at A69D calls helper 5EB8, which fills pink
through `41 - used*4` **inclusively**. Successful slime use instead erases from
that boundary. The clone already distinguished reset from use but sent refills
through the use path. Refills now call the inclusive-fill path too. This fixes
ordinary hard/medium partial refills as well as the demo images.

The GPU regression exercises the real collectible callback: hard mode restores
two uses, column 33 is pink and column 34 is black. No native screenshots were
modified to obtain the match.

## Reproduction

```
python tools/decode_wr1_demo.py GAME/WR1.D3 testing/output/demo_decoded.json
python tools/build_wr1_demo_replay.py testing/output/exploration_controlled.replay testing/output/demo_frontend.replay --frames 12000
just parity --scenario demo_level4 --timeout 240
```

Capture the frontend replay with `tools/capture_wr1_replay.py`, the instrumented
core and original game directory. Use `--start-frame 350 --end-frame 11000`,
`--run-between-samples`, and samples 500, 510, 1000, 2000, 3000, 4000, 5000, 6000,
7000, 8000, 9000, 10000, 10500, 11000. Capture screenshots at those counters
except 510, and supply a full `--instruction-trace` path. The existing native
recording is `testing/output/wr1_demo_level4_native.replay`; its full capture,
trace, configuration, log and images share that prefix. The capture command
closes only its own RetroArch process.

Prepare a new fixture directory with `tools/prepare_wr1_demo.py --capture ...
--trace ... --replay ... --demo GAME/WR1.D3 --directory NEW_DIRECTORY`. The tool
hashes the full trace, validates paused snapshots against frontend observations,
checks native controls against the demo file, and calibrates only the idle prefix.
It refuses to overwrite existing fixture files.

Pilot hashes:

- WR1.D3: `5bd580c29de9f0e10ef1865ef7a4437ea30325e3c3e74a11e35fed964cff47aa`.
- Frontend replay: `6d84ea265a62f764877dd9ae56ceb5befbbb7815da7f5d70afeae8de405fbfde`.
- Full native trace: `5e89cbc476f1fca11660f2e66990bd69e733c4884ab87c462a55b18379f06f44`.
- Instrumented core: `c28f7bc568f3607c32640f5fa208d2ba1c72cb9334822b0b276487f1e6c23728`.

The full ordinary state, terminal state and sampled-image results establish that
the approach works for this demo. Other demos, every displayed frame, audio,
menus and attract-mode transitions remain unverified.
