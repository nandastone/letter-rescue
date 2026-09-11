# Long native routes on levels 3 and 4

These are fresh recordings of WR1.EXE running in the instrumented DOSBox Pure
core through RetroArch. Level and difficulty selection use the game's own menus;
there are no native memory writes. Both clone replays start from the untouched
post-load checkpoint at counter 580. Counters 580–620 calibrate only the initial
idle clock; loading duration is excluded. Initial VGA phase is measured.

| Route | Character / difficulty | Seconds | Completed native updates | Distinct player cells | Rescues |
| --- | --- | ---: | ---: | ---: | ---: |
| level3_long | Girl / medium | 58.785 | 534 | 284 | 6 |
| level4_long | Boy / medium | 70.199 | 743 | 415 | 4 |

Level 3 spans raw player cells X39–112, Y17–40; level 4 spans X1–95,
Y35–56. The routes include direction changes, jumps, ladders, books, wrong
matches, slime presses, enemy encounters and repeated rescues. They are useful
exploration routes, not complete level solutions. The collision-only offline
planner does not simulate enemies, so native rescues change its intended path.

## Improvements driven by these captures

1. **Mistakes persist across rescues.** The native completed state retains
   DS:0334. Rebuilding the clone level reset its matching model and incorrectly
   cleared this count. That could later grant the perfect-match bonus after a
   mistake. The cached restart now retains it; a fresh level still starts at zero.
   Before the fix, level 4 matched only 51/743 states; the remaining 692 differed
   solely in this count. Afterwards all 743 match.
2. **Slime buckets use the current tileset.** The clone hardcoded BACK3 tile 238.
   Level 4 uses BACK2, where the bucket's opaque surrounding pixels are grey.
   The wrong atlas produced 61 cyan pixels per visible bucket. These now match.
3. **Backdrops are rendered.** Level 3 uses DROP4; the clone previously ignored
   this level field. WR1 renderer file AD34 tests DS:AF8A, then AD3E–AD54 copies
   the full 320×200 backdrop at screen (0,0), without camera scrolling. The clone
   now draws it behind the tiles. The extracted PNG's 87/171 colour components
   are normalized to the native 85/170 VGA output by
   `tools/extract_wr1_backdrops.py`. Level 3's checkpoint now matches all pixels.
   DROP3 is also available for the other backdrop levels, not yet route-verified.

Primary static evidence: `testing/output/wr1_backdrop_disasm.txt`, disassembled
from the executable hash below. Runtime evidence remains the untouched native
boundaries and images in `testing/fixtures/wr1_level{3,4}_long_*`.

## Gameplay versus input sampling

In the frontend-timed level 3 replay, the first gameplay divergence is update
255: WR1 admits it at counter 2546 while the clone admits it at 2547. A jump
release falls between those admissions. WR1 consumes up=true, the clone
up=false; their jump phase and height then differ. This eventually changes
rescues and leaves only 504 clone updates within the 534-update recording.
Those 30 missing updates remain explicit failures in the ordinary report.

The additional `parity-logical` check supplies **only** the four directional bits
and latched slime request observed at each native update entry. Later observed
positions, scores, RNG, actor states, and timestamps never enter the engine.
This is a separate control-by-update test of the actual playable game, not a
claim of wall-clock or pixel parity. Both full routes pass: **534/534 and
743/743** completed gameplay states, including the rescue endpoints.

`testing/output/parity/long-logical-first/report.json` records that result.
`testing/test_wr1_long_routes.py` replays both routes and deliberately removes
the jump at update 255 as a negative control. The real game then diverges at
255 in both input and vertical state. The test checks this failure, not merely
the engine's exit code. The combined focused regression run passed 13 tests
with Godot enabled; log: `testing/output/long_routes_regression_tests.log`.

The timed comparison remains independent, including exact native screenshots.
Latest full-suite report: `testing/output/parity/long-routes-final-all/report.md`.
The existing 17 routes retain 2,913/2,913 state and 50/50 image comparisons.
The full 19-route timed report records 3,927/4,160 compared states, 30 missing
clone updates, 65/73 exact images, and zero execution/evidence errors. The new
routes contribute 6/11 and 9/12 exact images. These timed results remain distinct
from the 1,277/1,277 control-by-update gameplay result above.
The new slime-request probe additionally reveals a pre-validation startup latch
difference at tick 2 in eight older overlapping recordings; gameplay outcomes
remain unchanged. Timing remains a failing diagnostic in the strict report.

Level 4 has residual screenshot differences during rescue and at an update
boundary. Counter 900 includes a small native sprite remnant; counters 1200 and
5500 show differing displayed poses/scroll. These are not counted as matches.
Level 3's later timed screenshots additionally inherit its missed jump.
Its counter-1200 image also has a 25-pixel actor-region difference before that
jump; this small presentation discrepancy remains unresolved.

## Reproduction

```
just parity --scenario level3_long --scenario level4_long
just parity-logical --scenario level3_long --scenario level4_long --output testing/output/parity/long-logical-new
```

Each output directory must be new. The first command preserves native frontend
input timing and checks screenshots. The second excludes wall time and pixels.

The maintained route plans are
`testing/fixtures/wr1_level3_long_plan.json` and `wr1_level4_long_plan.json`.
Regenerate a plan with Godot headless, script `tools/plan_wr1_exploration.gd`,
followed by `-- 3 OUTPUT.json` (or level 4). Plans are inputs only, not expected
outcomes. Rebuilding the native replay uses:

```
python tools/build_wr1_difficulty_replay.py testing/output/exploration_controlled.replay testing/output/wr1_level3_long.replay --difficulty medium --level 3 --frames 4800 --route testing/fixtures/wr1_level3_long_plan.json --route-start 630 --slime-window 820 824 --slime-window 1000 1004 --slime-window 1400 1404 --slime-window 1900 1904 --slime-window 2500 2504
python tools/build_wr1_difficulty_replay.py testing/output/exploration_controlled.replay testing/output/wr1_level4_long.replay --difficulty medium --character boy --level 4 --frames 5600 --route testing/fixtures/wr1_level4_long_plan.json --route-start 633 --slime-window 820 824 --slime-window 1100 1104 --slime-window 1500 1504 --slime-window 2100 2104 --slime-window 2800 2804
```

Capture using `tools/capture_wr1_replay.py` with `--start-frame 350`,
`--generic-keyboard-port 2`, `--run-between-samples`, and a full
`--instruction-trace`. End level 3 at 4700 and level 4 at 5500. Samples include
580, 620, 900, 1200, 1600, 2000, 2500, 3000, 3500, 4000, 4500, plus the end;
level 4 also includes 5000. Screenshot all those counters except 620.
Preserve the new capture manifest and trace; do not overwrite existing evidence.

`tools/prepare_wr1_exploration.py` accepts `--capture`, `--trace`, `--replay`,
`--name`, and `--level`. It hashes the entire trace, checks provenance, prepares
the existing strict post-load fixture, and copies the independently captured
images. It refuses to overwrite existing fixture files.

## Provenance

- Executable SHA256: `b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`.
- Core SHA256: `c28f7bc568f3607c32640f5fa208d2ba1c72cb9334822b0b276487f1e6c23728`.
- Core source revision: `db325ff427e3d0df2e6c38bc75b00b6771e03b38`; fixed 27,000 cycles/ms.
- Level 3 replay SHA256: `897f2c9a31c903ebf5b4aa0c3c400181399cd14777d8cdca2260dae6409059fe`.
- Level 3 full trace SHA256: `166f4056a0dbf6b8f2cbc18d28563b8a07df7ad39049ef93a639592a816c6dc2`.
- Level 4 replay SHA256: `5db6995cd58d81da3a47e655656044d07570e6dfa036b09b181ae1dc8206ac60`.
- Level 4 full trace SHA256: `407e015b70b8b6d87c28da9c007ce280b02e278111c0028f6054053260999f60`.

Full captures, configurations, logs, and traces remain under
`testing/output/wr1_level{3,4}_long_native*`. The original demo investigation is
deferred until after this work, as requested.
