# WR1 replay parsing, synchronization and longer comparison

Follow-up: [instruction-boundary tracing and clock correction](wr1_fourth_slice.md)
now resolves the movement timing differences documented below.

2026-09-07. The walk/jump/return comparison is now reproducible from a strict BSV2
reader, measured native snapshots and the actual Godot replay path. Movement rules
were not retuned in this pass. Replay input delivery and clock interpretation were
corrected. This establishes sampled state agreement, **not full-frame pixel parity**.

## Result

Captured 366 consecutive native frontend boundaries, counters 350 through 715,
from the controlled 770-frame replay. A separate capture of counters 590 through
605 reproduced all 16 snapshots exactly, including timer and actor fields.

The aligned clone executes 74 logical updates over its 432-frame slice. Of these,
62 fall within the native capture; the other 12 are explicitly outside coverage.
Comparison uses each clone update's actual input frame and the corresponding
native completed-frame counter, without searching for a better offset.

| Compared state | Exact samples |
|---|---:|
| Player/grid/world/camera position | 60 / 62 |
| Jump phase, player sprite and facing | 60 / 62 |
| Books, score, active word/index, matches, mistakes, offsets | 62 / 62 |
| Animated background phase | 57 / 62 |
| All of the above simultaneously | 57 / 62 |

These totals include 12 sampled updates from the idle calibration interval.
For the 50 subsequent validation updates, position/motion match 48/50,
interaction state 50/50, and all fields together 45/50.

The five non-exact samples match the relevant fields one native frontend frame
later. They remain failures in the strict report. Input frames 447 and 593 have
position/sprite differences; 523, 558 and 704 have background-only differences.
The persistent eight-pixel offset previously caused by the release at input frame
600 is gone with IRQ-phase calibration. The remaining differences still expose
limits of the nominal clock and immediate clone renderer. For example, native
counter 448 still has timer 7 and world X 80, while the clone has admitted its
next update and reached X 88; native counter 449 reaches X 88. Do not describe
this as proven CPU/render latency alone: emulator timing and gate admission also
need to be resolved.

Evidence: [native samples](fixtures/wr1_controlled_native.json),
[converted replay and synchronization settings](fixtures/wr1_controlled_replay.json),
[clock calibration](fixtures/wr1_controlled_clock.json), and the generated
[strict comparison report](output/controlled_comparison.json).

## What changed

* `tools/bsv_replay.py` validates the 40-byte v2 header, 12-byte keyboard records,
  both checkpoint layouts, all bounds, exact EOF and the declared frame count.
  The existing smoke recording contains **1309 frames**, not the old parser's 2082.
* `tools/replay_to_json.py` maintains independent keyboard and gamepad state,
  preserves simultaneous actions and carries held keys into trimmed slices.
  Idle gamepad samples can no longer cancel held keyboard input. Conflicting
  polled values within a frame are rejected. Callback pulses entirely within one
  native frame are still reduced to the final held state; this is a frame-boundary
  converter, not an emulator keyboard-controller model.
* `scripts/input_replay.gd` waits for level construction before consuming frame 0,
  runs before Player, and flushes injected events before that physics iteration.
  An engine test caught and now guards against losing a press on the final frame.
* Original-rule replays can specify measured `source_fps`,
  `original_clock_phase_seconds`, and `original_start_background_frame`.
  Ordinary live play retains its normal delta and startup behavior. Settings are
  explicit replay metadata, not changed movement constants.
* `tools/capture_wr1_replay.py` starts and closes its own RetroArch process,
  verifies the executable, advances exactly one frontend frame at a time and
  saves partial captures as incomplete on failure. Frame advancement polls for
  completion instead of assuming a fixed 50 ms host delay is sufficient.
* `tools/compare_wr1_traces.py` rejects incomplete captures, missing frames,
  duplicates, missing fields, mismatched source hashes and stale clone traces
  from an edited replay JSON. Adjacent-frame matches are diagnostics only.

## Frame numbers and clock evidence

In RetroArch build `69a4f0e`, `bsv_movie_next_frame()` increments the counter
**after** `core_run()`. Thus zero-based input frame N produces native completed
counter N+1. Clone `source_frame` keeps N; reports expose `native_completed_frames`
separately. This conversion is established by the pinned
[run loop](https://github.com/libretro/RetroArch/blob/69a4f0e/runloop.c) and
[BSV implementation](https://github.com/libretro/RetroArch/blob/69a4f0e/input/bsv/bsvmovie.c).
Keyboard/checkpoint layouts also follow that implementation and
[input_driver.h](https://github.com/libretro/RetroArch/blob/69a4f0e/input/input_driver.h).
Godot's [input flushing API](https://docs.godotengine.org/en/stable/classes/class_input.html#class-input-method-flush-buffered-events)
is verified here through actual engine behavior, not just a mocked scheduler.

The core log reports `70.086304` after WR1 switches to 320x200. This is consistent
with DOSBox Pure's [frame-rate selection](https://github.com/schellingb/dosbox-pure/blob/1.0-preview5/dosbox_pure_libretro.cpp),
which uses the render source rate unless overridden. Godot still runs one replay
iteration per 70 Hz physics tick, but each original simulation iteration accounts
for **1 / source_fps** seconds. Movie output remains at Godot's requested rate;
this does not correct the existing video extraction/resampling pipeline.

The selected input slice begins at frame 338. Native background phase there is
0. The initial IRQ phase is calibrated **only from the idle interval 350..419**,
before right movement begins at input 420. With IRQ period 12428/1193182 seconds,
each snapshot gives a half-open interval:

```text
k = entity_timer * 8 + timer
elapsed = (native_completed_counter - source_start_frame) / source_fps
k * IRQ_period - elapsed <= phase < (k + 1) * IRQ_period - elapsed
```

Intersecting 70 observations gives [0.013850430395288327,
0.013985784392049894) seconds; the replay uses its midpoint. This assumes the
entity timer counts ordinary updates with no intervening slime/reset path.
It is not a universal game clock. Fitting render-page edges instead missed the
input-release boundary; a completed render and the IRQ gate are different events.
The first native update also waits for startup input. The clone enters ordinary
gameplay directly: initial menu/prompt transitions, including the Enter pulse at
input 343, are not validated by this comparison.

## Reproduce

With Python and the Godot console executable available as `python` and `godot`:

```powershell
python tools/calibrate_wr1_clock.py --native testing/fixtures/wr1_controlled_native.json --fps 70.086304 --source-start-frame 338 --calibration-start 350 --calibration-end 420 --output testing/output/clock.json
godot --headless --fixed-fps 70 --path . -- --original-rules --mystery-word cup --replay testing/fixtures/wr1_controlled_replay.json --state-trace testing/output/controlled_aligned.jsonl
python tools/compare_wr1_traces.py --native testing/fixtures/wr1_controlled_native.json --clone testing/output/controlled_aligned.jsonl --replay testing/fixtures/wr1_controlled_replay.json --output testing/output/controlled_comparison.json
```

The comparator currently exits **1**, correctly reporting the five non-exact
samples. Exit 2 means invalid comparison inputs. The replay and native snapshots
are retained in the repository, so this comparison does not require recapturing
the original. The source BSV hash is included for provenance; the exploratory
BSV under ignored output must be retained or regenerated to capture anew.

Validation: 26 Python tests pass, including three actual Godot replay tests.
The existing Godot suites also pass: 305 movement checks, 2458 matching checks,
26 native integration updates with projection/sprite/clock checks, and 107
interaction checks. Accelerated full gameplay replay still reports the previously
documented audio-resource shutdown warning; the short replay tests and game-rule
suites exit cleanly.

## Next boundary

The new trace includes native gruzzle arrays and render/display page markers.
[Further disassembly](wr1_update_boundary_research.md) identifies ordinary-loop
instruction boundaries at file offsets `0x40a4` (after display selection) and
`0x40d2` (before the next loop), plus gruzzle movement, animation and slime state.
Instruction-boundary observation would distinguish gate admission, movement,
render mutation and presentation reliably. Two identical paused memory reads do
not establish a completed logical update.

Next work should use those boundaries to settle timing and then replace legacy
gruzzle/slime behavior using the recovered arrays and rules. Pixels, enemies,
slime, sound, death and level transitions are explicitly outside this report's
agreement counts. There is no new whole-screen pixel-parity claim.
