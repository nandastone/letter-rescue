# Sixth parity pass: pickups, rescue, letters, animated pictures, rewards

This pass extends gameplay beyond the first moving screen. The comparison still
uses one initial native state plus the same frontend input stream. Future native
states and update schedules are never supplied to the game.

## Implemented and measured

- **Slime buckets:** raw markers, original background restoration, five points,
  and difficulty-specific refill (easy 5 uses, medium 3, hard 2). The easy native
  refill replay matches all 100 completed updates, including the spent-use count
  returning from 1 to 0 at the bucket.
- **Empty slime:** ten-render lifetime, original position, cooldown, and the
  40×40 effect from `SLIME.WR`. The effect also occurs when targeting an actor
  after all five uses have been spent.
- **Death/rescue:** original descent, lift, black-screen pause, and return walk.
  The native probe has seven descent draws, sixteen ascent draws, fifteen IRQs
  of black-screen hold, and six-frame walking animation with four-IRQ waits.
  All 23 internal rescue renderer states match. The measured sequence takes
  194 IRQs (approximately 2.02 seconds).
- **Respawn:** preserves score, RNG, motion phase, idle/walk counters, actor-slot
  timers, action timer, and background animation. Reloads pickups and the puzzle,
  chooses new rotations/mystery word, and randomizes all ten actor slots,
  including inactive ones. All 200 completed updates across a death and restart
  match the native trace. The 13 observed RNG calls produce rotations 3/4,
  mystery index 1, and final state `3482209081`.
- **Mystery letters:** original glyphs, positional markers, removal, ordered
  prefix, and repeated-character semantics. An out-of-order letter is still
  consumed and pays five points. The last correct letter pays 100, replacing the
  ordinary five, and restores all slime. A short wrong-order/correct-order probe
  matches 100 completed updates. A full out-and-back CUP route matches **319/319**,
  including completion at score 215 and slime usage dropping from 2 to 0.
- **Picture animation:** the optional `WORD2.WR1` artwork, eight-render timers
  staggered initially `[0,3,5,8,10,13,15]`, and per-slot frames. These advance even
  when cards are hidden. Matched pictures in the HUD animate by word index.
  Missing second images fall back to the first, as the loader does.
- **Floating rewards:** original twenty-render lifetime, palette alternation,
  world position, offscreen cancellation, and bonus captions. All reward counters
  are included in the 319-update native comparison.
- **Exit artwork:** the original 32×40 doorway replaces the placeholder sprite,
  text, colour modulation, and pulse. End-of-level behavior is still being traced.

The all-seven-matches route additionally matches **761/761 completed updates**,
including all seven matches without mistakes and the 500-point perfect bonus
(score 740). This exposed and fixed the sixth-match popup position: the original
clears its last-contact exclusion, but the reward must retain the actual target
coordinate. The fixture explicitly ends before the Benny recap branch at the
next grounded admission; it does not claim parity across that cutscene.

Together with the fifth-pass runs, this covers **1,827 exact completed updates**
across nine input sequences. Field coverage varies with trace vintage; the full
CUP fixture includes the new picture, letter, and reward fields.

## Pixel results and timing limits

`fixtures/wr1_roof_pixels.json` records two additional complete 320×200 native
screens with **0/64,000 differing pixels**, at native counters 1317 and 1323
(clone source frames 1316 and 1322). These exercise the policeman's alternate
picture, the original U glyph, collection, the score popup, and the HUD prefix.
The black-screen rescue hold also matches exactly at native counter 785 / clone
source 784 (`fixtures/wr1_rescue_hold.png`).

These do **not** establish continuous frame parity. The full CUP route has five
one-frontend-frame admission differences, at logical ticks 94, 214, 238, 269, and
294; all held inputs and completed states agree. The death run has additional
one-frame discrepancies after the cached-level reload resets the IRQ gate.
`fixtures/wr1_death_timing_residual.json` records those residuals for regression
detection; the runtime does not read it. Intermediate rescue frames and DOS
palette/page transitions are not yet pixel-exact. Some native screenshots show
video behind the paused memory or a partially updated scanout; these are retained
as diagnostics, not silently shifted to obtain a match.

## Evidence and reproduction

Binary: WR1.EXE SHA-256
`b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`.
The observation-only core remains pinned to DOSBox Pure 1.0-preview5 commit
`db325ff427e3d0df2e6c38bc75b00b6771e03b38`.

Key file offsets:

| Behavior | EXE offsets |
| --- | --- |
| Pickup dispatch / letter removal and prefix | a34e..a602 |
| Slime-bucket refill | a611..a7c5 |
| Five-point pickup tail | aa86..ab1f |
| Rescue / black hold / return walk | 4ce1..4e6c; 5862..594b |
| Cached-level reset and ten actor slots | 4e6d..50e7 |
| Mystery selection and placement | 730a..75ad |
| Rescue source rectangles | 91bb..9258 |
| Picture timers and optional second file | ab25..ac27; 6286..6337 |
| Floating reward raster | bfc0..c10c |
| Raw exit contact | 3d46..3d72 |
| Exit animation and next-level branch | 3da3..409b |

`tools/build_wr1_feature_replay.py` reproduces `refill`, `death`, `letters`, and
`letters-complete` from `testing/output/exploration_controlled.replay`. Rebuilt
refill/death BSV files were byte-identical to the captured originals. The
experimental `level-complete` probe accepts
`--plan testing/fixtures/wr1_level_complete_actions.json`.

The full CUP fixture currently comes from `testing/output/wr1_rewards_native`
(`.json` plus `.jsonl`). Its replay bytes are
`testing/output/wr1_letters_complete.replay`. `prepare_wr1_boundaries.py` validates
the trace hash and calibrates only the initial idle window. Every maintained
fixture includes source/EXE/core/trace provenance.

Run Python checks with `GODOT` set:

```text
python -m unittest discover -s testing -p "test_*.py" -v
```

Run the Godot suites `motion`, `matching`, `integration`, `interactions`,
`gruzzles`, `rescue`, and `letters` using:

```text
godot --headless --path . --script testing/test_wr1_rescue.gd -- --original-rules --mystery-word cup
```

For the roof captures:

```text
godot --path . --fixed-fps 70 --script testing/capture_wr1_replay_frames.gd -- --original-rules --mystery-word cup --replay testing/fixtures/wr1_letters_complete_replay.json --capture-source-frames 1316,1322 --capture-directory ABSOLUTE_OUTPUT_DIRECTORY
```

## Remaining work

The substantial remaining gaps are original exit/level-transition behavior,
drip hazards on later levels, native startup seeding and level-load RNG, broader
difficulty/character coverage, and continuous timing/presentation parity. The
spawn mask's render-page order was corrected from the renderer disassembly but
still needs its own native pixel fixture; the late slime puddle and exhausted
target effect also need dedicated pixel coverage. Existing accelerated audio
shutdown leaks are still restricted to the known collect/reveal/wrong WAVs.

The full-match run also retains correct/unlock WAVs when accelerated shutdown
occurs immediately after the final match; its regression test explicitly checks
those file identities. Forty Python tests and all seven Godot suites are the
current verification set (see `testing/output/wr1_sixth_tests.log`).

### Benny recap discovery

After the seventh match, `DS:032b` becomes 1. At the next update with supporting
tile 0x73/0x74, main code `383c..3848` calls `01a3:151c` (file `594c`) and jumps
back to the main gate without completing/incrementing that admission. This is
why the full trace ends with a partial main update during the recap. The explicit
`--through-tick 761` fixture preserves/hash-checks the complete raw trace and
reports the two later instruction observations excluded from its scope.

The recap disables picture animation, sets the player to frame0/facing-left,
descends with Benny, transfers each matched picture, adds white random pixels
to it, and rises again. Its twenty dissolution draws per word each consume
**80 RNG calls** (40 x/y pairs), or **11,200 calls for all seven words**. This must
be reproduced before claiming next-level RNG parity. The main routines are
`594c..5d84`, the eight-IRQ render helper `5d85..5eb7`, and interrupt polling
`5fad..6005`. Benny sprites use twelve 22-byte records starting at DS:0556;
records0..8 come from BENNY1.WR, records9..11 from BENNY2.WR.

The user's pre-existing `player_idle.png` rendering adjustment is preserved.
