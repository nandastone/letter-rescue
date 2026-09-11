# Original rules: books, matching and HUD

2026-09-07. Opt-in with `--original-rules`; the default controller is retained.

## Implemented

- Books use the raw attribute scan in the original update order. Loading stamps
  `0x82 + book_index`; collecting clears that byte to `0x20`, restores the saved
  background tile, and awards 5 points. The final book awards 500 instead of 5.
- Word and picture identities use separate cyclic rotations. Successful matches
  consume only the source word; completed sources remain reusable picture targets.
  Mistakes restore the source and spawn a gruzzle below the target. Seven matches
  unlock the door, give 20 each, and give an additional 500 only with zero mistakes.
- Contacts run after movement and before camera/render updates. The row-major scan
  stops on a qualifying question contact, including an excluded source/last-touch
  location. Book pickups continue scanning, and require scan X >= player grid X.
- Score, current word and mystery text use the BIOS 8×8 font extracted from the
  paused original. Completed HUD slots display pictures. Word cards reproduce the
  original 72×18 border, font and anchor. Player sprites draw over these cards.
- Original pictures preserve opaque backgrounds, pad short decoded borders to 24×24,
  and correct the archive decoder's yellow index 6 to the gameplay palette's brown.
- Clone JSONL traces now include score, book count and matching state.

The implementation follows [matching research](wr1_matching_research.md) and
[HUD/book research](wr1_hud_books_research.md). The live font extraction tool is
[extract_wr1_font.py](../tools/extract_wr1_font.py); it reads memory only.
DOSBox Pure's mapping for memory above 640 KiB is documented in its
[primary source](https://github.com/schellingb/dosbox-pure/blob/main/dosbox_pure_libretro.cpp),
`DBP_ReportCoreMemoryMaps`. See [runtime notes](wr1_runtime_research.md).

## Verified against the original

- Twelve native rightward updates, replay frames 425–489, match player world/grid
  coordinates, sprite, score and collected-book count. Books are collected at
  world X 80, 112, 144, producing scores 5, 10, 15. Fixture: `fixtures/wr1_books_walk.json`.
- A separate native sequence selects source slot 0 (CUP with rotations 5/0), then
  touches slot 4 (GUN), producing one mistake and clearing active-word mode.
  Fixture: `fixtures/wr1_matching_events.json`.
- Exact native pixels match for score 5, current word CUP, the 24×24 GUN picture,
  and the unobscured 52×18 portion of the CUP word card. The actual graphical
  preview also matches the whole 72×34 player-over-card region at (104, 80).
- Initial 320×200 reference frame remains identical when the actual mystery word
  is explicitly set to `pot`. The old chrome had `pot` baked in even though the level
  data says `hat`; the new HUD displays actual state. This explains the intentional
  difference when launching without the reference override.

Pixel fixture provenance is in `fixtures/wr1_interaction_pixels.json`. Native
screenshots can lag the sampled memory update; these are static raster checks,
not proof of synchronized frontend-frame scheduling.

## Checks and reproduction

With Godot on PATH:

```powershell
godot --headless --path . --script res://testing/test_wr1_motion.gd
godot --headless --path . --script res://testing/test_wr1_matching.gd
godot --headless --path . --script res://testing/test_wr1_integration.gd -- --original-rules
godot --headless --path . --script res://testing/test_wr1_interactions.gd -- --original-rules
```

Results: 305 motion checks; 2458 matching checks; 26 native movement updates through
the actual scene; 107 interaction checks, including native rasters, book rewards,
wrong-answer recovery, all-seven completion and the unlocked door. State tests
disable sound playback so accelerated headless execution does not retain the
existing audio backend's pending WAV playback buffers.

Preview the captured interaction:

```powershell
godot --path . --script res://testing/capture_wr1.gd -- --original-rules --character girl --mystery-word cup --interaction-preview --settle-frames 3 --capture-output D:/Work/letter-rescue/testing/output/clone_word_reveal.png
```

Launch interactively:

```powershell
godot --path . res://scenes/game.tscn -- --original-rules --mystery-word pot --state-trace D:/Work/letter-rescue/testing/output/live_wr1.jsonl
```

`--word-offset` and `--picture-offset` default to 5 and 0 from the recorded native
session. They must differ. `--character boy|girl` defaults to girl. These explicit
state settings support comparison; they do not reproduce native startup RNG.

Legacy render regression: with `--freeze-start`, current and pre-change scene
captures are pixel-identical. A normal 20-process-frame comparison differed by
22 pixels inside one animated background tile because process frames do not fix
the number of physics updates. The frozen comparison removes that timing variable.

## Remaining boundaries

This is not full-game parity. Floating reward sprites, two-frame picture animation,
slime meter/rules, mystery pickup interactions, enemy movement/collision/spawn-slot
reuse, death/restart progression and exit rewards still need their original rules.
The original mystery word can depend on startup state; the default level data is
not a synchronized native RNG seed. Viewport-edge word-card clipping also remains
unverified. The preview's remaining pixel differences include the native pause
overlay, floating reward and background animation phase.

Next useful pass: fix production replay parsing and align completed logical
updates, then use numeric state to isolate the next enemy/slime divergence.
