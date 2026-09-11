# Ordinary gameplay and level cards — 2026-09-09

## Scope and observations

Played an untouched WR1.EXE in DOSBox Pure through the ordinary menus, two
deaths, all seven level-one matches, Benny's recap, the exit and level two.
Easy difficulty, girl, player name A. Physical keyboard input only; the emulator
was paused between bounded actions for observation. No teleports or memory writes.

The clone was manually exercised through walking, jumping, a wrong match, death
and respawn. Its existing ordinary exit input recording was also run as a one-off
diagnostic. These are different playthroughs, not a same-input parity claim.
The fifteen original demos remain the maintained gameplay suite.

Findings:

- Death retains score and the level's mistake count, resets books, and chooses
  new word/picture rotations, mystery word and enemy types. The native HUD can
  temporarily show no score after death even though memory retains it. In this
  session the first death retained 15 points; collecting the next book displayed
  20. The clone reproduced that behavior.
- Native level-one completion reached 290 points, 20 books and one mistake.
  The successful attempt matched source blocks in order 0, 2, 5, 3, 1, 6, 4;
  the words were gun, cop, pen, toe, cup, rat, pot. Benny's recap produced the
  key, and using the exit entered Gruzzleville Waterworks normally.
- The separately recorded clone exit route completed 6,164 input frames and
  reached level two with its expected score 740 and cleared matches/mistakes.
  That score is not compared with the native 290-point playthrough.
- Fresh-map title cards were missing from the clone. They are now reproduced
  from the executable's title table and drawing routine.
- Live input recording counted time in menus/loading, while replay excluded it.
  Recording now uses the same gameplay-readiness gate and saves the starting
  level/difficulty/character instead of the values at the end of a multi-level session.
  A real recording → replay integration test reproduces every logged gameplay
  state across a walk and jump, after spending time in the menu and title card.
- At this stage ordinary startup randomization was incomplete: fresh clone sessions used
  deterministic fallback values, while native startup seeds from DOS date/time.
  This is now addressed in [fresh-game startup research](wr1_startup_research.md).
  Name entry, character selection and introductory screens remain gaps.

## Level-card recovery and implementation

Executable SHA256:
`b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`.
File offsets below refer to that exact executable, with DS initialized data at
file `0x24f50`.

`tools/extract_wr1_level_titles.py` reads fifteen pairs of far string pointers at
DS:00BE (file `0x2500e`) into `data/wr1/level_titles.json`. The renderer at
file `0x8361..0x845b` clears the page to EGA gray, draws the black-bordered cyan
rectangle `(40,58)..(279,84)`, and uses the existing native 8x8 text font.
The heading starts at `(128,62)` even for Level 10 and above; the name is centered
at y=72 using `160 - 4*length`.

The routine clears the keyboard latch DS:c48b. The first-start flag DS:017c
adds a wait of at most 300 IRQs, or until a new key press. It then clears the
flag. With PIT reload 12428 and clock 1193182 Hz this is about 3.125 seconds.
Later fresh-map cards cover loading without an added delay. Cached death resets
do not call the fresh loader and do not show a card.

`scripts/core/wr1_level_title.gd` renders the card in the presentation layer while
gameplay physics is disabled. The game hides it after the new gameplay page is
ready. Native-input replays skip this UI: their measurements still start after
loading. Loading time is not a fidelity target.

Verification:

- Native level-two screenshot versus clone card: **0 differing pixels out of
  64,000**, full 320x200 RGB comparison.
- All fifteen extracted title pairs render successfully.
- Integration test checks keyboard dismissal, timeout, physics/readiness while
  the card is visible, no card on cached respawn, and the fresh-load UI seam.
- Actual visible Play → level-one card → gameplay was inspected successfully.

Run `python -m unittest testing.test_wr1_level_title -v` with `GODOT` set to the
Godot console executable. This focused UI test supplements the demo suite; it
does not restore the earlier ordinary routes to the suite.
`python -m unittest testing.test_input_replay -v` also passes all four checks,
including the new live recording round trip and existing frame-zero scheduling.

The full sequential run `just parity --output
testing/output/parity/level-titles-20260909 --timeout 900` completed all fifteen
demos: **22,460/22,460 states, 196/196 images, all controls and all terminal
states/timings exact**. There were no missing updates or execution/evidence
errors. The strict command returns 1 for the same three ordinary-admission
timing residuals as before: demo 6 tick 1474 and demo 13 ticks 662 and 956.
They remain visible failures, not an allowlist. Full results are in that output
directory's `report.md` and `report.json`.

## Evidence

The maintained image is `testing/fixtures/wr1_level_title_02.png`; its provenance
and hashes are in `testing/fixtures/wr1_level_title.json`. It is copied byte for
byte from the native capture, not reconstructed from decompiled instructions.

Session artifacts are under `testing/output/normal-play-20260909/` (ignored):

- `native.replay`: orderly finalization produced a valid BSV2 movie with
  **53,121 frames**, matching its header. SHA256
  `bfaf405c17d941eb0e1fcf810f0065b945257751c79a785b1c698f24565b4ff4`.
- `native-after-death.json`, `native-second-restart.json`, `native-level2.json`:
  read-only memory snapshots. Native level-two snapshot has score 290, zero
  books/mistakes/matches and player world position `(608,416)`.
- `WORD-260909-085605.png`, `WORD-260909-085639.png`: recap and key.
- `WORD-260909-085723.png`: native level-two title reference.
- `WORD-260909-085753.png`: native level-two entry.
- `clone-live-inputs.json`, `clone-live.jsonl`: manual clone death/respawn.
- `clone-exit.jsonl`: separate saved ordinary exit-route diagnostic.
- `title-routine.txt`, `loader-full.txt`, `startup-disassembly.txt`,
  `seed-followup.txt`: disassembly used in this investigation.

The native recording is retained for later ordinary-input experiments; this
session does not claim that every frame in it has been compared with the clone.

### Physical-key movie playback requires Game Focus

The first reproduction attempt with the existing capture helper stopped at the
name prompt. The movie itself contains the expected physical keyboard events:
`A` down/up at frames 3005/3012, followed by Enter at 3966/3974. Valid BSV framing
alone therefore does not establish that inputs reach the game on playback.

RetroArch commit `69a4f0e`, `input/bsv/bsvmovie.c:bsv_movie_poll`, routes stored
keys through `input_keyboard_event`. In `input/input_driver.c:7275..7336`, that
function can reject key-down callbacks bound to hotkeys or RetroPad buttons
unless Game Focus is enabled. The live session had enabled Game Focus with
Scroll Lock; the replay helper had not restored this frontend setting.

`tools/capture_wr1_replay.py --game-focus` now adds
`input_auto_game_focus = "1"` to its isolated, unsaved configuration and records
the setting in its evidence JSON. Host input remains disabled. Existing demo
capture behavior is unchanged unless this explicit option is supplied.
With the original movie bytes unchanged, the focused reproduction passes name
entry and reaches character selection. The full reproduction completed six
snapshots through counter 53120 and reached level two with score 290, RNG
1576920362, rotations 6/5, cleared matches/mistakes and world position `(608,416)`.
Both the first-death screenshot at 39840 and the level-two entry screenshot at
53120 match the original live screenshots with **zero differing pixels**.

This establishes route and sampled-image reproduction, not complete native-state
parity throughout the movie. At the first-death checkpoint the idle entity timer
is 3832 in playback versus 4148 live; all other captured game fields match there.
The final live snapshot was at counter 53121, one later than the replay's last
sample 53120; its timer is 3 versus 2, with the other captured game fields equal.
Replay flags and snapshot bookkeeping naturally differ. Keep these distinctions
when using this movie for subsequent diagnostics.

Reproduction artifacts are `native-focused-reproduction.json`, its `_frames/`
directory and `native-focused-reproduction-trace.jsonl` in the session output
directory. The unfocused failed attempt is retained under `native-reproduction`
for comparison. The maintained demo references were not modified.

## Startup RNG follow-up

This section records the initial investigation. The subsequent implementation,
1,552 original-code timestamp checks and native starts on all three difficulties
are now complete; see [fresh-game randomization](wr1_startup_research.md).

The existing recurrence and 16-bit seed handling are documented in
`wr1_animation_research.md`. Further source inspection established:

- File `0x9b32` seeds after startup input initialization. File `0x97c7` reseeds
  after returning from the demo to restore an ordinary session.
- Date/time conversion at `0x247ae` uses whole seconds, ignores hundredths,
  and combines a 1980 baseline (`0x12cea600`), year/month/day and time-of-day.
- It calls timezone setup at `0x24b67`. This reads the DOS **TZ** environment
  variable (DS:63cc), not the host operating system's timezone configuration.
  Without a valid TZ value, the code sets offset 18,000 seconds and enables
  daylight handling, with EST/EDT names.
- Daylight selection at `0x24d4c..0x24e23` checks April through October. Its
  April calculation changes after year 1986 from the last Sunday to the first
  Sunday; October uses the last Sunday. The boundary-hour checks are 02:00.
  This is the bundled C runtime's historical rule, not a request to adopt
  current timezone rules. Controlled native cases are still needed before
  translating this into the clone's startup behavior.
- Consequently `host Unix time & 65535` alone is not established as the correct
  seed. Seed conversion and the sequence of random calls both need validation.
- Fresh loaders consume random numbers while decoding map enemy types, which
  are later overwritten by the ten-slot initialization. Those seemingly unused
  calls still change subsequent word/enemy behavior.

Next useful experiment: observe the seed and first untouched post-load state
under controlled DOS date/time for Easy, Medium and Hard, then reproduce the
full call sequence in live startup while preserving measured replay checkpoints.

The focused replay also yielded `native-first-update.json`, the first ordinary
update entry at frontend counter 15446 (before the update executes). Its RNG is
3342764813, word/picture offsets 5/6, mystery index 6, starting enemy type 3 and
word cursor 28. Reversing the LCG finds candidate 16-bit seed 20716 at 17 calls;
it is the only 16-bit candidate within the first 200 reverse steps. This is an
inference from state and the recovered recurrence, not a captured seed call.

The recovered fresh-load call sequence accounts for those 17 calls: one word
rotation, one accepted picture rotation, four overwritten map-spawn types,
one mystery selection and ten final enemy-slot types. The first word-list group
does not consume RNG. The existing `wr1_gruzzles.restart(..., fresh_level=true)`
and `wr1_words` reproduce the native RNG, rotations, mystery selection, first
enemy type, words and cursor when run with that candidate seed in the ignored
`fresh-start-probe.gd`. The production startup path is unchanged; this result
narrows the next implementation to seed initialization and using the recovered
fresh-load path, followed by validation across dates and difficulties.
