# WR1 instruction-boundary tracing and exact movement replay

2026-09-07. **The 50 validation updates now match their native entry frame,
held direction/jump inputs, and completed movement, animation, camera, book,
score, word and background state.** No sample offset search is used.

The error was in the replay clock. DOSBox Pure hands off frames on whole
emulated milliseconds; accumulating an ideal video period put two clone updates
on the wrong side of a frame boundary. The replay now supports an explicit
clock quantum and its phase. Movement rules were not retuned.

## Evidence and scope

| Check | Result |
|---|---:|
| Local unmodified core vs installed core | 13/13 identical memory snapshots |
| Instrumented core vs installed core | 366/366 identical memory snapshots |
| Repeated tracing run | 16/16 memory snapshots and 12/12 instruction records identical |
| Completed state, including idle/walk counters | 64/64 updates exact |
| Validation after idle calibration: entry frame, inputs and completed state | 50/50 exact |
| Original frontend-memory comparison: movement/camera/interaction | 62/62 exact |
| Original frontend-memory comparison: background phase | 59/62 exact |

The completed-state count includes startup/calibration updates. The first native
update waits for Enter and occurs one frontend frame later than the clone's
ordinary simulation starts; the comparator reports it and excludes it from the
50-update validation interval. Ten further clone updates fall beyond the native
instruction fixture. No result here covers pixels, enemy parity, slime rules,
death, sound or level transitions.

The three remaining background mismatches in the frontend comparison are
explained by actual instruction observations. Each starts in one frontend frame
and finishes rendering in the next:

| Logical update | Entry counter | Completion counter | Entry time (emulated ms) | Completion time |
|---|---:|---:|---:|---:|
| 32 | 524 | 525 | 7537.318 | 7539.304 |
| 38 | 559 | 560 | 8037.278 | 8039.185 |
| 63 | 705 | 706 | 10120.448 | 10121.920 |

At completed-update boundaries the background phase agrees in every case.
The clone renders immediately; WR1 takes measurable emulated CPU time to render.
The frontend comparator **still exits 1** for those three differences. We have
not delayed the clone renderer by an arbitrary frame or declared pixel parity.

Fixtures: [native instruction boundaries](fixtures/wr1_controlled_boundaries.json),
[calibrated replay](fixtures/wr1_controlled_quantized_replay.json),
[instrumentation validation](fixtures/wr1_core_trace_validation.json), and the
existing [native memory snapshots](fixtures/wr1_controlled_native.json).
Generated reports: [completed-update comparison](output/wr1_boundary_comparison.json)
and [frontend comparison](output/wr1_quantized_frame_comparison.json).

## Observation point

A separate DOSBox Pure tracing build observes six original instructions before
execution. WR1.EXE and its emulated memory are not patched.

| File offset | Main CS-relative IP | Observation |
|---|---|---|
| 37a4 | 0444 | Admitted update, before clearing the IRQ timer |
| 37a7 | 0447 | Immediately after timer clear |
| 3d7e | 0a1e | Movement complete, before contacts |
| 3da3 | 0a43 | Renderer returned |
| 40a4 | 0d44 | Display selection returned |
| 40d2 | 0d72 | Main iteration incremented, before the back-edge |

The native run uses the **DynX86** decoder at a fixed 27000 cycles, not the normal
interpreter. The patch emits callbacks into translated blocks, preserves flags,
flushes cached general registers and accounts for pending block cycles in the
reported timestamp. It does not add guest instructions or debit guest cycles.
The normal decoder has an equivalent observation point. Other decoder modes and
protected-mode games are not supported by this WR1 probe.

The callback verifies three code signatures and the expected CS/DS relationship
before reading state. It records the main BP locals, original held inputs,
player/contact fields, gruzzle arrays and emulated PIC time. Reading main BP at
these boundaries makes the loop counter and idle/walk indices usable; reading an
arbitrary paused BP would not. Preparation requires all six stages in order and
exactly one main-iteration increment per update.

Sources are pinned to DOSBox Pure `1.0-preview5`, commit
`db325ff427e3d0df2e6c38bc75b00b6771e03b38`. The
[main emulation loop](https://github.com/schellingb/dosbox-pure/blob/db325ff427e3d0df2e6c38bc75b00b6771e03b38/src/dosbox.cpp)
alternates millisecond timer advancement and event processing. Its
[frontend and worker control](https://github.com/schellingb/dosbox-pure/blob/db325ff427e3d0df2e6c38bc75b00b6771e03b38/dosbox_pure_libretro.cpp)
joins the preceding frame and launches the next worker frame before returning.
Consequently, paused memory can be ahead of the video buffer returned by that
frontend call. The trace labels the worker's launching call explicitly; 365
joined-frame observations were checked against corresponding paused memory
snapshots rather than assuming the mapping.

## Clock correction

The nominal frontend rate remains 70.086304 Hz. The idle interval at native
counters 350..419 constrains a millisecond frame-clock offset to
[47.21458891597467, 47.236432613139186). The midpoint and the slice's starting
frame determine `source_clock_phase_seconds`. The update timer phase is then
calibrated against those **quantized emulated times**, yielding
[0.014049687306714354, 0.01419830000787814) seconds.

For replay-relative frame N, the clone uses:

```text
t(N) = ceil((clock_phase + N/source_fps) / quantum) * quantum
frame_duration = t(N+1) - t(N)
```

Here quantum is 0.001 seconds. The original timer accumulator receives that
duration. The replay includes only clock parameters and the original input
events: no future native update schedule or gameplay outcomes are supplied to
the clone. The calibration interval precedes movement input 420.

Disabling quantization while retaining the same input sequence and calibrated
IRQ phase reproduces the two position/animation failures at input frames 447 and
593. This negative control is saved under `output/wr1_clock_negative_*` and
establishes that the regression check detects the actual clock error.

These settings are explicit replay metadata. Live play and older replays retain
their prior clock behavior unless a measured quantum is supplied. Mode changes,
frame skips, multiple savestate epochs and host-dependent auto cycles require
new validation; the preparation tool rejects multiple load epochs.

## Reproduce the comparison

With Python and Godot on PATH:

```powershell
godot --headless --fixed-fps 70 --path . -- --original-rules --mystery-word cup --replay testing/fixtures/wr1_controlled_quantized_replay.json --state-trace testing/output/wr1_quantized.jsonl
python tools/compare_wr1_boundaries.py --native testing/fixtures/wr1_controlled_boundaries.json --clone testing/output/wr1_quantized.jsonl --replay testing/fixtures/wr1_controlled_quantized_replay.json --output testing/output/wr1_boundary_comparison.json
python tools/compare_wr1_traces.py --native testing/fixtures/wr1_controlled_native.json --clone testing/output/wr1_quantized.jsonl --replay testing/fixtures/wr1_controlled_quantized_replay.json --output testing/output/wr1_quantized_frame_comparison.json
```

The boundary comparator exits **0**, reporting 50/50 validation updates and
64/64 completed states. The frontend comparator exits **1** for the three
documented partial-render samples. Both verify the exact replay JSON hash and
source BSV hash; the boundary comparator also checks the instruction-trace hash.

31 Python tests pass, including actual Godot replay regressions and checks that
wrong entry frames, inputs, completed state, missing updates and stale traces
fail. The four existing Godot suites also pass (305 motion checks, 2458 matching
checks, 26 native integration updates plus projection/clock checks, 107 interaction
checks). Accelerated gameplay shutdown retains the previously documented audio
resource warning; no audio lifetime changes were made in this pass.

## Rebuild or extend the tracing core

The patch and callback source are [wr1_core_trace.patch](../tools/wr1_core_trace.patch)
and [wr1_core_trace.cpp](../tools/wr1_core_trace.cpp). They apply to a fresh checkout
of the pinned core revision. The build used portable
[w64devkit 2.9.1](https://github.com/skeeto/w64devkit/releases/tag/v2.9.1), extracted
under ignored `testing/output/w64devkit`; no global compiler installation or
replacement of the installed RetroArch core was needed.

```powershell
# From the repository root, with a fresh pinned core checkout at the target path:
Copy-Item tools/wr1_core_trace.cpp testing/output/dosbox-pure-trace/wr1_core_trace.cpp
git -C testing/output/dosbox-pure-trace apply D:/Work/letter-rescue/tools/wr1_core_trace.patch
$env:PATH='D:/Work/letter-rescue/testing/output/w64devkit/bin;'+$env:PATH
make -C testing/output/dosbox-pure-trace -j 8 SHELL=cmd.exe CXX=g++ STRIP=strip
```

`SHELL=cmd.exe` is required for this Makefile's Windows recipe handling with the
selected toolchain. Callback source is GPL-2.0-or-later, compatible with the core.

To capture, pass the separate DLL to `tools/capture_wr1_replay.py` and add
`--instruction-trace testing/output/wr1_hook_native.jsonl`. The existing required
arguments select RetroArch, game folder, BSV, capture range and output. The tool
sets `DBP_WR1_TRACE_FILE` only for its child and closes that process afterward.

Regenerate the calibrated replay and fixture from a complete paired capture:

```powershell
python tools/prepare_wr1_boundaries.py --capture testing/output/wr1_hook_native.json --trace testing/output/wr1_hook_native.jsonl --replay testing/fixtures/wr1_controlled_replay.json --output testing/output/quantized_replay.json --fixture testing/output/boundaries.json
```

The new seam is useful for the next implementation pass: compare gruzzle/slime
updates at real completed-loop boundaries, then compare rendered pixels at a
clearly defined presentation boundary. Current gruzzle fields are observations,
not a claim that the clone's legacy enemy behavior agrees.
