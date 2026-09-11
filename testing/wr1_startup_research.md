# Fresh-game randomization — 2026-09-09

Fresh live sessions now use WR1's recovered random initialization sequence
instead of the older fixed word/picture offsets and one-enemy RNG shortcut.
New recordings preserve the initial seed so replay reconstructs the same start.
Existing native demo checkpoints and older recording defaults are unchanged.

## Seed conversion

Source executable SHA256:
`b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`.

`scripts/core/wr1_startup.gd` implements the original C runtime conversion at file
`0x247ae..0x248e0`, timezone parsing at `0x24b67..0x24d4b`, and daylight selection
at `0x24d4c..0x24e23`. The game passes only the low 16 bits of the converted
timestamp to its seed routine at `0x23f5f`. Hundredths are ignored.

The DOS runtime defaults to EST/EDT when TZ is absent or invalid. It uses its
historical April/October daylight rule, including the 1987 change in April's
boundary. This is intentionally independent of current host timezone rules.
The parser expects a three-letter zone name followed by a numeric offset;
for example, `JST-9` is accepted, whereas the four-letter `AEST-10` falls back to
the default in the original code. The pure conversion supports these native TZ
inputs for research; ordinary clone sessions use the original default DOS setup.

The clone samples local calendar fields when starting a new game, then converts
them with this routine. Its simplified menu flow is different from the original
startup/name/character flow, so matching the wall-clock instant of the original
seed call is not claimed. Use a known seed to compare independently launched
sessions. Deaths and level advances continue the existing RNG stream.

### Independent machine-code verification

`tools/prepare_wr1_startup_seed.py` loads the original MZ executable into a
16-bit Unicorn CPU, applies its relocation table in memory, and runs the actual
conversion instructions. It supplies DOS date/time structures and substitutes
only `getenv("TZ")`, an external input. The file on disk is not modified.

`testing/fixtures/wr1_startup_seed.json` contains **1,552 original-code results**:
leap days, year boundaries, daylight transition seconds before/at/after 02:00,
years on both sides of the 1987 rule change and 2038, deterministic date samples
through 2099, and valid/invalid TZ strings. Both full 32-bit timestamp results
and low-16-bit seeds match the GDScript implementation. This verifies integer
logic, not instruction timing or the DOSBox host-clock interface.

Regenerate with Python + Unicorn 2.1.4:

```powershell
python tools/prepare_wr1_startup_seed.py --exe PATH/WR1.EXE --output testing/fixtures/wr1_startup_seed.json
```

## Fresh-load sequence

`wr1_gruzzles.start()` resets initialized actor data, seeds the original LCG,
then reproduces the first-game menu sequence:

1. Word rotation `rand()%6+1`.
2. Picture rotation `rand()%7`, retrying while equal to the word rotation.
3. Read the next seven words; randomized skipping occurs only at word-list EOF.
4. Consume one type draw for every map spawn, even though the types are overwritten.
5. Mystery selection `rand()%7`.
6. Ten enemy type draws, including inactive slots.
7. Apply the chosen difficulty. Medium consumes one draw for `2 + rand()%2`;
   Easy activates one enemy and Hard activates every map spawn.

The ordering in step 7 is specific to the first-game flow. The original starts
with initialized difficulty Easy (`DS:017e = 0`), calls the level reset at
`0xa02b`, then enters the menu at `0xa053`. Accepting its difficulty selector
calls `0x8841` from `0x7d53`, adjusting the active count without rerolling mystery
or enemy types. The clone's simplified menu applies the chosen difficulty once.
Repeated visits to the original selector can consume additional draws; replaying
that menu history is outside the current gameplay recording format.

Deaths and subsequent fresh levels retain their different, already recovered
sequence: the loader calls `0x8841` at `0x6e36`, before mystery selection at
`0x70b1` and the ten reset type draws at `0x5094`. A cached death load jumps to
`0x6e36` from `0x617f`, skipping word-list advancement and map decoding. Moving
Medium's draw globally would therefore fix first starts while breaking restarts.

`game.gd` keeps this initial result separate from cached death/next-level state.
That matters: treating the first load as a death restart would try to restore a
player state that does not yet exist and could retain the wrong HUD/word state.

The captured Easy start at native frontend counter 15446 has seed candidate
20716, RNG 3342764813, rotations 5/6, mystery word COP, one enemy of type 3,
and word cursor 28. The seed was inferred by reversing the LCG through the
17 source-derived calls; it was not read at the original seed function.
Control-only variants of the same original BSV snapshot select Medium and Hard.
They establish the same initial rotations, mystery and enemy type sequence.
Medium ends at RNG 1038270386 with two enemies (types 3, 0); Hard ends at RNG
3342764813 with four (types 3, 0, 2, 1). The extra Medium draw is the eighteenth.
The actual live clone scene reproduces all three captured startup cases from
seed 20716, using no measured state injection. Evidence, source hashes and the
added difficulty-selector controls are in `testing/fixtures/wr1_fresh_start.json`.

The Medium comparison first failed with three enemies and mystery POT, then
passed after separating the first-game ordering from the restart ordering.
These captures verify level-one startup fields, not complete menu behavior or
first starts at other levels. Native captures used their original 3000-cycle
BSV setting; no loading-duration or frontend timing claim follows from them.

## Recording and compatibility

New original-rule recordings save `original_start_seed` alongside initial
level, difficulty, character and controls. The round-trip integration test
records ordinary play after time spent in menus/title, then replays it in a new
process and compares every logged gameplay state.

Native replay fixtures continue to restore their untouched post-load state;
older recordings without a seed retain their previous deterministic defaults.
A replay cannot combine a fresh seed with measured actor, level, picture,
music or video checkpoints. Invalid or fractional seeds fail explicitly.

For a reproducible live session:

```powershell
just run-original # ordinary clock-seeded play
just run-original --original-seed 20716 # reproducible fresh start
# To record: add --record PATH/recording.json; F9 saves the recording.
```

`--original-seed` accepts 0 through 65535. Replays use their saved value and reject
a command-line replacement. Explicit older word/picture/mystery research
overrides retain the legacy initialization path and cannot be combined with a
seeded start.

## Checks

With `GODOT` set to the console executable:

```powershell
python -m unittest testing.test_wr1_startup testing.test_input_replay testing.test_wr1_level_title -v
```

These include the original-code timestamp cases, native startup fields on all three difficulties,
seed variation at every difficulty, repeatability for a fixed seed, rejection
of ambiguous replay state, recording round-trip and title lifecycle checks.
The fifteen original demos remain the maintained gameplay regression suite.

The focused command above passed all nine tests after the Medium first-game
ordering correction.

The full `just parity --output testing/output/parity/startup-rng-20260909 --timeout 900`
run completed all fifteen demos: **22,460/22,460 gameplay states, 196/196 sampled
images, all controls and all fifteen terminal states match**. Every scenario
report is identical to the previous `level-titles-20260909` baseline.
The strict command still exits 1 for the same three admission timing differences:
demo 6 tick 1474 (native 9242, clone 9241), and demo 13 ticks 662 (4497/4496)
and 956 (6214/6213). There are no new differences or execution/evidence errors.
See [the full report](output/parity/startup-rng-20260909/report.md).
