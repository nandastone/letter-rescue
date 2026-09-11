# Hard-mode drip impact and restart

The new `hard_drip_impact` scenario uses the original menus to select hard mode
and level 14, follows the existing drip route, and presses slime on source frames
750–753. The shot removes the enemy that killed the previous hard-mode route
before it could reach the drip. No original-game memory is edited.

The comparison starts at the first displayed playable level frame, counter 560.
Counters 560–619 form the idle calibration prefix. Only the initial checkpoint
and recorded inputs enter the clone; subsequent original states are expectations.
At update 65 (native admission 938), drip 0 hits the player at `(28,60)` and
changes to impact frame 2. Rescue returns and the completed update is observed
at counter 1061. The fixture ends at counter 1400, after restart and before a
later enemy rescue begins. It contains 122 completed updates and 14 images.

## Actual game fixes

- **Cached restart retained reward state:** native reward coordinates `(35,33)`
  survive the death reset. The clone discarded the popup object while rebuilding
  the level and reset them to zero. Cached restart now retains that object;
  advancing to a new level still creates a new one. The EXE fresh-loader clears
  DS:014c/014e at 6cdd, while the cached death path does not. This removes all
  57 post-restart state mismatches in the new scenario.
- **Slime meter after restart:** EXE 5eb8–5efd fills pink through
  `41 - used*4` inclusively. Successful slime use at 5256–52a5 instead erases
  starting at that coordinate. The clone used the erasure geometry for both,
  losing one pink column (four pixels) after restarting with slime already used.
  The HUD now uses the reset geometry on setup and updates only when the used
  count changes. Native counters 1100 and 1200 now match completely.
- **Actor drawing order:** the clone put enemies and drips behind the player.
  The original draws player (B9EC–BA38), enemies (BA38–BBA0), drips
  (BBA0–BC5E), then foreground (BC5E onward). Distinct Godot layers now preserve
  that order even when actors are spawned later. This makes the drip/player
  overlap images at counters 937 and 945 exact and corrects enemy/player
  layering at counter 1400, where a timing difference still remains.

The focused comparison improved from **65/122 to 122/122 exact states** and
**4/14 to 8/14 exact images**, with no compared input differences. The 45
admission timing differences remain; the strict suite still fails. Six images
around impact/rescue also remain different and are preserved as failing
references, not dropped or shifted. Do not describe the route as pixel-perfect.

As a diagnostic only, five of the six remaining images match an earlier clone
frame within four source frames after the layering fix. Counter 940 has no
whole-frame match because scanout mixes two renders: its top 150 rows and bottom
50 rows match different clone frames, yielding an exact 64,000-pixel
reconstruction. See [the timing investigation](wr1_impact_timing_diagnosis.md). These
adjacent-frame matches are **not** accepted by the strict comparison. The saved
diagnostic is `testing/output/hard_impact_pixel_diagnostics_layers/diagnostics.json`.

Before/after reports:

- `testing/output/parity/hard-drip-impact-before/report.md`
- `testing/output/parity/hard-drip-impact-layers/report.md`
- Final full regression: `testing/output/parity/hard-drip-impact-final/report.md`

## Capture and reproduction

Generate the native recording:

```powershell
python tools/build_wr1_difficulty_replay.py testing/output/exploration_controlled.replay testing/output/wr1_hard_drip_impact.replay --difficulty hard --frames 1500 --route testing/fixtures/wr1_drip_route_plan.json --route-start 673 --slime-window 750 754
```

Authoritative complete native evidence is
`testing/output/wr1_hard_drip_impact_complete_native.json`, `.jsonl`, `.map`, and
the `_frames` directory. The manifest records executable, core, source replay,
trace, capture and image hashes. The earlier `wr1_hard_drip_impact_native` capture
is retained as a diagnostic: it ends inside the subsequent enemy rescue and was
correctly rejected as an incomplete update sequence.

The native capture command uses `tools/capture_wr1_replay.py`, counters 350–1400,
Generic Keyboard port 2, sparse running capture, and screenshot counters
559, 560, 760, 900, 937, 938, 939, 940, 945, 960, 1000, 1050, 1100, 1200, 1400.
Counter 559 is loading evidence; it is excluded from gameplay image comparison.
The replay converter starts at 338, ends at 1400, and uses the observed source
rate 70.086304 Hz. `prepare_wr1_level_start.py` then uses level 14, start counter
560 and calibration end 620.

The boundary parser now accepts either the original six-hook sequence or the
complete newer nine-hook sequence, including contact/entity boundaries A23,
A39 and A3E. Missing or reordered hooks still fail. Explicit completed-update
prefixes count completion hooks rather than assuming six instructions per tick.

Run the maintained actual-game reproduction with:

```powershell
just parity --scenario hard_drip_impact
```

Run all scenarios with `just parity`. Missing Godot is an error; known timing
residuals do not turn a failing comparison green.

## Final validation

The full 17-scenario run completed without execution/evidence errors:
**2,913/2,913 state comparisons**, no compared input differences, and
**44/50 exact images**. All 36 previously matching images remain exact; the six
image failures belong to the new hard-impact route. There are 533 validation
admission timing differences across the overlapping scenarios, so the command
correctly exits 1. The 11 targeted parser, fixture, and report tests also passed.
