# Maintained parity suite: the fifteen original demos

Run `just parity` to run all fifteen demos sequentially, in the original attract-loop order: 4, 1, 10, 12, 14, 15, 2, 5, 8, 11, 9, 3, 6, 13, 7.
Use `just parity --scenario demo_level4` for a focused rerun. `GODOT` and `PYTHON` can override the executable paths; Python needs Pillow.

The earlier hand-authored routes are retired from the default suite at the user's request. Their captures, fixtures, research notes, and specialized diagnostic tools remain historical evidence. The fifteen demos are the maintained actual-game regression suite. Missing demo evidence is an error, never an omitted or skipped test.

Each demo uses controls decoded from its original WR1.D file. The clone receives one untouched post-load checkpoint, including initial music/IRQ/VGA state. It receives no future native gameplay states, timestamps, or images. The renderer and gameplay clock remain separate. Native death and door-exit returns are checked separately because the original bypasses its ordinary completed-update hook.

Each demo starts one fresh rendered Godot process. That same playback records gameplay state and screenshots, and continues through the terminal return after the last screenshot. Every run writes an immutable output directory under `testing/output/parity/`, containing:

- `report.md` and `report.json`, with separate state, input, timing, terminal, and pixel verdicts.
- Per-demo clone traces, exact commands (`game_command.json`), and complete engine logs (`game.log`).
- Every mismatch, with surrounding update context and native/clone/difference image panels.
- Native capture, replay, demo-file and image hashes.

Test windows start minimized. Requested screenshots explicitly render the real viewport after the scene's process callbacks; they do not depend on normal window redraws. Minimization must not lose captures or advance gameplay. `testing/test_wr1_capture.py` verifies identical images and state with visible, initially minimized, and subsequently minimized windows.

Exit 0 means all measured comparisons passed; 1 means divergence; 2 means an execution or evidence error. The full suite must contain all fifteen demos to claim completion. Godot is mandatory. No frame shifts or known-difference allowlists are applied.

The image score covers only reference screenshots listed in each pixel manifest, not every video frame. Audio output, attract-menu transitions, and unsampled pixels remain outside that score. Initial loading time is excluded. Check every completed gameplay update, consumed control, and observed terminal state; keep timing differences visible independently.

Native recordings use `tools/build_wr1_demo_replay.py`, `tools/capture_wr1_replay.py`, and `tools/prepare_wr1_demo.py`. Preserve raw evidence and source hashes. See [demo research](wr1_demo_research.md) for binary offsets and format semantics.

Boundary fixtures use lossless gzip (`wr1_demo_levelN_boundaries.json.gz`); no state fields are removed. Python evidence readers also resolve the older `.json` spelling to its compressed counterpart. Replay files and pixel manifests remain ordinary JSON. Raw uncompressed traces and capture images stay in `testing/output/` as acquisition evidence.

Native acquisition disables RetroArch's host input driver while BSV supplies the recorded controls. The preparer rejects live keyboard activity during a demo; a stray host modifier release must never be accepted as a short successful route.

The pixel manifests include 21 close-up frames around the remaining admission
differences in levels 6 and 13, for 196 reference images total. Supplemental
captures retain their complete acquisition JSON and its hash. The runner checks
that the capture completed, used the same original replay, and actually sampled
the specified counter. Those close-ups matched with no frame shifts; the three
admission-counter differences remain failures independently of their images.

For clock research, use `just clock-probe 6 1476 testing/output/clock6-NEW.json`
and `just clock-probe 13 958 testing/output/clock13-NEW.json`. These replay the
live clock classes from the initial checkpoint without starting gameplay or
rendering. The baseline exposes one and two counter differences respectively
and exits nonzero. Reports preserve predicted admissions and source hashes.
An optional fourth argument selects an experimental clock script. The tool
refuses to overwrite evidence or cross recap, rescue, exit or interrupted
admissions. Its result measures only the requested ordinary clock prefix;
`just parity` remains the gameplay gate.


## Completed frontend/audio regression, 2026-09-09

The final full sequential run is
`testing/output/parity/frontend-final-20260909/report.md` (JSON alongside it).
All15 demos completed:22460/22460 gameplay states, all consumed controls,
all15 terminal states/timings, and196/196 sampled viewport images match.
There are no missing updates or execution/evidence errors. The strict command
exits1 for the unchanged timing residuals: demo6 tick1474 (9242/9241), demo13
tick662 (4497/4496) and tick956 (6214/6213), native/clone counters respectively.
No offsets or residual allowlists were applied.

The separate frontend suite has46 exact native screen/popup comparisons and
checks actual viewport composition. Integration tests cover the real final-level
exit handler, all three ending pages, restarting level1, loading another saved
player, remapping priority/default fallbacks, and isolated save destinations.
Attract tests cover natural completion, interludes, all fifteen starts, visible
restoration with and without a suspended game, and cancellation before deferred
launch. Mixer, replay roundtrip, OPL, recap and seeded-startup checks also pass.
The detailed limits above still apply; this is not whole-game or PCM perfection.
