# Seventh parity pass: recap, exit, later levels, drips and word loading

Follow-up: [the eighth pass](wr1_eighth_slice.md) reduces the recap timing gap,
extends reset-state coverage, and verifies a complete level-two screenshot.

The original-rules game now proceeds through the seventh match, Benny's recap,
the exit animation, and automatic entry into the next map. All fifteen maps
initialize through that transition path. Run it with `just run-original` or
Godot's `-- --original-rules` arguments.

This is still a work in progress: the recap returns about ten video frames early,
so the complete exit route does not yet have continuous same-input parity.

## Recovered behavior

### Benny recap

`scripts/wr1_recap.gd` follows executable offsets `594c..5eb7`. The seventh match
sets a pending flag; the next grounded admission starts the recap. The player
stops while the original renderer continues advancing its animation counters.
The helper's approach, seven transfers in completion order, dissolves, and
departure produce **180 renderer calls** in the captured route: 40 helper draws
and 140 dissolve draws. Explicit waits total **1,580 IRQs**.

Each dissolve consumes 40 random x/y pairs, in that order. Across seven words,
this is **11,200 RNG calls**, taking the observed seed from `1527080467` to
`520533843`. Skipping with Escape waits for key release and does not consume
randomness belonging to unvisited events. Native Q handling remains unported.

The helper uses twelve extracted Benny sprites. Its panel shows the original
picture and BIOS-font word; transferred pictures expose the corresponding gold
key segment in the HUD. The HUD's last picture column now draws above the side
chrome. Native picture animation remains disabled when the recap returns and
is enabled again on a map reset.

`wr1_recap_stages.json` records the entry, all 180 renders, and return.
The pure model passes **3,426 checks**. The full live run agrees on **1,130
completed gameplay states**, comprising the previously covered 761-state prefix
and 369 states after the recap. The maintained post-recap fixture deliberately
contains only those 369 states; it does not duplicate the earlier fixture.

Three independently captured complete 320×200 screens match exactly:

| Native capture counter | Clone input source frame | Differing RGB pixels |
| --- | --- | --- |
| 4887 | 4886 | 0 / 64,000 |
| 4894 | 4893 | 0 / 64,000 |
| 4905 | 4904 | 0 / 64,000 |

The indexing convention is the existing capture-counter versus input-frame
convention, not a fitted shift. The three images contain different Benny/panel/
dissolve states. `wr1_recap_pixels.json` records their hashes; the Python suite
replays the actual Godot renderer and compares all RGB bytes.

**Timing limit:** the first resumed update enters at clone source frame 5941
versus native 5951. By native frame 8101 the clone is about eleven frames ahead.
Native transfers spend approximately 26.4 ms per word in pixel copying, and
dissolve drawing takes roughly 4.12–4.37 ms per draw. These CPU costs and their
interaction with interrupt phase are not modeled. No arbitrary delay or future
native update schedule was inserted to conceal the discrepancy.

### Exit and next map

Offsets `3dad..3fa9` establish the raw contact predicate: unlocked door, player
column in `[door_x - 1, door_x]`, and row `door_y + 5`. One extra world render
precedes five door blits, each separated by twelve IRQs. If no enemy was
successfully slimed, six more twelve-IRQ bonus flashes follow. World animation
does not advance during those door blits.

The observed “Bonus #2 / 500” caption does **not** change the score: the captured
route remains at 740, and the inspected branch contains no score write.
The caption currently approximates the flashing artwork; it has not passed a
native pixel comparison.

The next map loads automatically, preserving score, RNG, motion phase,
idle/walk counters, background frame, and actor-slot timers. It updates map
dimensions and distinguishes a fresh spawn from a cached death respawn.
Fresh map decoding consumes one random type per spawn even though reset later
overwrites those types. The captured level-two loader consumes **17 random
calls**, ending at seed `3921914530`, rotations 5/6, and mystery index 4.

`test_wr1_exit.gd` passes **181 checks**; a real-engine replay checks automatic
level-two entry, position, score, random state, words, and animation enablement.
The entire exit replay does **not** have exact state parity: the early recap
return admits additional idle updates, and 70 paired updates differ on that
route. Its final spawn/random choices agree. After level fifteen, the current
implementation returns to the menu; the original ending is not implemented.

### Dripping hazards

Recovered load/update/draw routines are `66db..672b`, `5309..53c6`, and
`bba0..bc5e`. Maps 7, 14, and 15 have drips. Their maximum y is an absolute
8-pixel grid coordinate, not a falling distance. The first update moves three
cells and changes frame 0 to 1; subsequent updates move one cell, with wrapping
to the stored origin. Easy difficulty ignores player contact. Medium/hard use
strict bounds and select frame 2 on impact.

Drips run after slime processing and before the actor loop. They consume no RNG.
Their frame slots persist across fresh maps; cached death restarts retain their
current positions as well. Three extracted original sprites replace the timed
placeholder hazards in original mode.

The native probe enters map fourteen with the game's own Z+L selector, typing
14 and Enter. It uses a polled Generic Keyboard on controller port 2 alongside
the existing port-0 input. No guest memory is patched. All three drip states
agree over **101 updates**, and the model passes **501 checks**, including the
strict medium/hard contact edges. Native medium/hard impact and rendered drip
pixels still need measurement.

### Word stream and tilesets

The static converter assumed eight words per level and exhausted the list before
the final maps. Native offsets `7170..7309` instead read **seven words from a
persistent byte cursor**; the mystery word is selected from those seven.
When fewer than 56 bytes remain, the loader seeks to the beginning and skips
`rand() % 9 + 1` words. That random call occurs after puzzle rotation selection
and before the discarded map-enemy type choices. A cached restart keeps the
current words and cursor.

`data/wr1/word_list.json` preserves the source bytes, including line endings,
with their SHA-256. `scripts/wr1_words.gd` implements that stream. Original mode
uses it during transitions; static level JSON now supplies seven nonempty,
cyclic defaults for modern mode. Those static defaults are not represented as
the native random EOF sequence.

The native word probe alternates the original level selector between maps 14
and 1 sixteen times. Selecting the current map would merely take the cached
restart path. All sixteen fresh loads agree on words, byte cursor, final RNG,
rotations, and mystery index (**114 checks**). The observed EOF transition goes
from cursor 497 to 40 and selects `rat gun cup cop hat dog arm`.

Each original map also loads its recorded BACK tileset instead of always using
BACK3. A real-engine test traverses all fifteen maps, checks both tile layers,
seven valid words, model/hazard initialization, and a death restart on each map:
**211 checks pass**. This is initialization coverage, not fifteen full native
playthroughs or pixel comparisons.

## Reproduction and verification

Native evidence uses WR1.EXE SHA-256
`b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`,
RetroArch 1.22.2 (`69a4f0e`), DOSBox Pure 1.0-preview5
(`db325ff427e3d0df2e6c38bc75b00b6771e03b38`), and the checked-in trace extension.
`tools/wr1_core_trace.patch` includes the corresponding normal/dynamic CPU hooks
and read-only input observations. The compiled core and raw captures remain
under ignored `testing/output`; maintained fixtures record source hashes.

New/extended tools:

- `extract_wr1_gruzzles.py`: Benny and drip sprite tables.
- `extract_wr1_words.py`: byte-preserving word stream.
- `build_wr1_feature_replay.py`: recap pause, extended exit route, drips and
  sixteen-load word probes, retaining the controlled replay's savestate.
- `capture_wr1_replay.py --generic-keyboard-port 2`: native level selector input.
- `prepare_wr1_recap.py`, `prepare_wr1_words.py`: reduced evidence fixtures.
- `prepare_wr1_boundaries.py`: recognizes interrupted gameplay admission around
  the recap and rejects malformed/incomplete lifecycle traces.

Final verification: **46 Python tests pass**, including live Godot replay and
pixel tests, and **all twelve Godot suites pass**: motion, matching,
interactions, gruzzles, letters, rescue, integration, recap, exit, drips, words,
and levels. `git diff --check` passes. Existing accelerated-audio shutdown
warnings are accepted only when their resource identities match known sound
files; script errors and arbitrary resource errors still fail the tests.

The largest remaining parity work is interrupt/CPU timing through recap and
transitions, later-map visual comparisons, native medium/hard and boy coverage,
startup/menu/ending behavior, and sound timing. The original-rules option remains
separate from the existing modern physics mode.
