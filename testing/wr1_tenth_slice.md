# Tenth pass: medium/hard hazards, pit rescue and the boy

This pass extends the independent post-load comparison to level 14, **Slime
Factory: Bottling**, with medium and hard difficulty and both characters.
It verifies **446 completed gameplay updates** and **18 full 320x200 images**.
All measured states and entry inputs match. Exact video timing is still an
open issue: **122 admissions are one video frame early** across the four runs.
These residuals are explicitly retained, without shifting comparisons.

## Native setup and synchronization

`tools/build_wr1_difficulty_replay.py` selects difficulty through the original
Escape/D menu, then uses the original Z+L level selector to choose 14. Boy
selection uses Right while the character picker is visible, before Enter.
It changes only recorded controls; there are no guest RAM edits.
The route is `testing/fixtures/wr1_drip_route_plan.json`, 46 movement updates
planned against the already recovered map collision rules. The native game
provides independent evidence of the resulting movement and interactions.

Native counter 559 still displays the loading title. Counter 560 is the first
complete level image for these captures. Every replay starts with one state
at that boundary. There are no later state injections or resynchronizations.
Loading duration, including cached reload title screens, remains excluded.

The checkpoint now restores and draws normal visible enemies and drips without
advancing their state. Enemy animation indices in completed state point to
the *next* frame, so initial presentation uses the preceding index. All ten
enemy cadence slots are preserved, including inactive slots: medium's reset
can introduce a third enemy whose slot timer survived from an earlier map.

Clock phase still has to agree with the idle prefix. A read-only PIT probe now
also measures the hardware timer epoch directly at the initial handoff. Its
period and phase are validated against those idle observations. No later
hardware samples or native admission schedule are copied into clone input.

## Recovered behavior and rendering fixes

- **Pit rescue:** EXE 3d72 compares raw player gy with map height. At or below
  the bottom row it jumps to 40a6, sets death, subtracts 8 from the screen y
  anchor, and enters rescue before cell scanning, actor updates or ordinary
  rendering. The clone previously fell beyond height + 4 and performed those
  updates. Raw gy is not rolled back. The corrected full rescue and reset
  match 73 native completed states.
- **Trace validation:** this pit path has admission hooks 444/447 and completion
  d72, without the three normal render hooks. The parser accepts it only with
  observed rescue entry 8b1, return 969 and death set. Missing ordinary hooks
  still fail validation.
- **Drips:** sprite records at DS:cfc refer to video page 2 while **BENNY2.WR**
  occupies that page. Reading CHARS.WR instead produced fragments of player
  sprites. BENNY2's PNG palette has 87/171 channel values, normalized to the
  live EGA 85/170 palette; drip transparency is palette 9. Falling, forming and
  impact sprites now use the correct source and transparency.
- **Rescue/character palette:** CHARS index 6 displays EGA brown. This fixes
  Benny's rescue colors and the boy's boots. Boy's inclusive rescue source
  rectangle is 73 pixels wide, but the planar image displays 72; cropping to
  its whole-byte width removes the extra black pixel verified in native images.
- **Cached reset score box:** the cached reset repaints the HUD but skips the
  fresh loader's score-print path at 6d13. The clone now leaves this box blank
  until another score-producing event. Fresh level setup still prints it.
- **Character replay metadata:** a measured boy checkpoint now selects the boy
  atlas and rescue image; an explicit `--character` override remains available.

## Evidence and remaining timing differences

| Maintained fixture prefix | Scenario | Updates | One-frame timing residuals | Exact images |
|---|---|---:|---:|---:|
| `wr1_medium_pit` | Girl, medium, bottom-of-map fall, rescue and restart |73|7|0|
| `wr1_medium_drip` | Girl, medium, drip impact, rescue and restart |130|51|7|
| `wr1_hard_drip` | Girl, hard, nine enemies, two enemy deaths and restarts |113|13|5|
| `wr1_boy_drip` | Boy, medium, drip impact, rescue and restart |130|51|6|

All fixtures live in `testing/fixtures/` with replay, boundaries and explicit
timing-residual JSON files. Pixel manifests hash the native images and identify
their capture. The medium drip collision sets drip 0 frame 2 at raw player (28,60).
The hard route dies before reaching the drip; it is enemy-death coverage,
not a claim of hard-mode drip impact coverage.

The authoritative full native captures are:

- `testing/output/wr1_medium_pit_native.json` and `.jsonl`.
- `testing/output/wr1_medium_drip_pit_native.json` and `.jsonl`.
- `testing/output/wr1_hard_drip_pit_native.json` and `.jsonl`.
- `testing/output/wr1_boy_drip_native.json` and `.jsonl`; additional boy images
  are from `wr1_boy_drip_pixels_native.json` and `.jsonl`.

The `pit` suffix in the drip capture names denotes the **PIT timer probe**,
not a pit death. Some raw screenshot probes deliberately landed near update
completion or during loading; those are preserved as diagnostics and are not
included as passing pixel pairs. Hard's comparison interval ends at source
frame 1444, before either game starts the next update outside the fixture.

The first remaining medium timing mismatch is native admission 915 versus
clone 914. At frontend call 915 the native game timer already reads 8, but the
main loop has not yet admitted its update. The direct PIT measurement rules
out choosing another phase within the previous calibration bounds as a general
fix. The original IRQ handler increments that timer at 4352, invokes its music
driver at 43fa and returns later. New observation-only hooks at 4352,43f8,43fc
and 442a are being used to measure this service delay. This is active gameplay
timing research, not an attempt to reproduce loading duration. The follow-up
[IRQ investigation](wr1_irq_research.md) confirms a 0.660 ms music-driver call
carrying the first discrepant admission across a frontend handoff.

## Verification

`testing/test_wr1_difficulty.py` runs the actual Godot engine, checks initial
state, completed state, entry inputs, explicit timing residuals and full images.
It also rejects missing ordinary hooks and incomplete short rescue paths.

The full Python suite passed **56 tests** in 136.8 seconds before adding the
boy cases. The expanded difficulty tests plus the level-two regression suite
then passed **8 tests** in 34.5 seconds, including all 446 states and 18 new images.
All **twelve Godot model/integration suites** passed, and `git diff --check`
passed. Logs are `testing/output/wr1_tenth_full_tests.log`,
`wr1_boy_difficulty_tests.log`, `wr1_tenth_godot_suites.log` and
`wr1_tenth_diff_check.log`.

Example native input generation:

```powershell
python tools/build_wr1_difficulty_replay.py testing/output/exploration_controlled.replay testing/output/wr1_medium_drip.replay --difficulty medium --frames 1900 --route testing/fixtures/wr1_drip_route_plan.json --route-start 673
```

Native capture uses `tools/capture_wr1_replay.py` with Generic Keyboard port 2.
Its optional `--sample-frames` skips unnecessary RAM reads while retaining a
continuous instruction trace. The core patch now includes the timer observer
in `src/hardware/timer.cpp` as well as the CPU/frontend hooks.

Remaining scope includes exact IRQ/render delivery timing, more later-level
routes, native hard drip impacts, ending behavior, original menus and audio.
The project is substantially closer, but is not yet an exact clone.
