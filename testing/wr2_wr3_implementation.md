# Episodes 2 and 3: implementation and verification

The content port includes all 40 registered levels and their rules, word/picture
catalogs, tiles, backdrops, sprite overrides, titles, story/endings, music mappings
and twelve distinct native input demos. `scripts/core/episode.gd` resolves content
while retaining Part 1's existing paths. Browser URLs select content: `/` for
Part 1, `/?episode=2` for Part 2 and `/?episode=3` for Part 3. Desktop launches
use `--episode 2` or `--episode 3`. There is no in-game episode picker.
Profiles and high scores use separate `.wr1`, `.wr2`, `.wr3` files, and recordings
store their episode. Clear Text, smooth motion, custom vocabulary and berserker mode
use the same modern presentation across episodes.

## Reproduction and checks

Run `python tools/import_episodes.py "D:/path/to/registered/files"`, then
`python tools/build_episode_clear_manifests.py`. The importer checks executable
hashes before using recovered offsets and records source hashes in manifests.
It does not rewrite Part 1 content. Pillow is required.

Verified locally with Godot 4.6.1:

- `tools/smoke_episodes.gd`: all 55 real game scenes load, update physics and
  complete matching through the interaction model; all original and modern
  pictures load; last exits/endings and independent profile/high-score storage
  pass. This is integration coverage, not a natural playthrough of every map.
- `tools/smoke_episode_sessions.gd`: registered level-20 warps, six demo starts
  per episode, cancellation and restoration of a live game, words and physics
  rate pass. Both smoke scripts run in the web and release CI workflows.
- `tools/capture_episode_port.gd`: graphical first/last maps and matching cards,
  all startup/story/ending screens and menus inspected.
- All twelve imported demos run headlessly to completion without script errors.
- Web export succeeds. `tools/test_episode_web.mjs build/episode-port
  testing/output/episode-web` checks the default launch and episode query URLs,
  name entry, menu and movement in Chrome for all three parts without runtime errors.
  Set `PLAYWRIGHT_MODULE` to a playwright-core module URL if it is not installed.
- Existing frontend/replay tests: 7 passed; clean-art/Clear Text tests: 2 passed.
- Focused Legacy `demo_level4` parity: 1,624/1,624 states and 11/11 sampled
  images match, with no input, timing, terminal or execution differences.
  The complete fifteen-demo parity suite was not rerun for this port; its
  previously documented timing residuals are not claimed to be resolved.

Runtime captures/reports are under `testing/output/episode-port-visual`,
`episode-web`, `episode-demos`, and `parity/episode-port-wr1`. No new native
WR2/WR3 frame-by-frame parity claim is made. The native evidence below establishes
the content format and selected episode-specific initialization differences.

## Native source evidence

2026-09-23. Primary artifacts are the WR2/WR3 executables and archives in
`D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)`. Hashes and overall
methodology are in `testing/wr2_wr3_source_research.md`. `output/episode-native-research/tables.json` contains
machine-readable titles, sprite records, native demo order, startup placement,
and initialization policies. The selected disassemblies in that output directory retain direct
instruction evidence. No original artifacts were modified.

## Final-cell markers

WR2 loader `0x6a07..0x6aa4` fills the complete doubled-width × doubled-height
attribute grid. Its `0x6bd6..0x6c37` coordinate-cache scan visits all x columns,
then all y rows; every attribute below seven is appended with no seven-entry
guard. WR2 S1/S2 and WR3 S0 contain an additional matching ID at the final
bottom-right cell, hence an eighth cached location. Native seven-picture
consumers still iterate only seven. Preserve the raw marker and take the first
seven column-major positions for picture-location metadata. Do not overwrite
the proper location by assigning the duplicate marker to its slot ID.

## Tables and artwork

WR2 DS base `0x24eb0`, title-pair table DS:`0xc0`; WR3 DS base `0x24ef0`,
title-pair table DS:`0xbc`. Twenty heading/name pairs each. Sprite table offsets
are WR1 offsets plus `0x36` (WR2) or `0x32` (WR3). Every rectangle, size and
source-page field in the 12 Benny, 9 slime, 16 gruzzle, 52 player, and 3 drip
records matches WR1; internal pointer fields differ with relocation.

Both episode STATIC.WR images differ from the WR1 original only inside
`[16,120,96,24]`. This changes gruzzle frames 0–3. Exact original-image comparison
confirms player, rescue, Benny, slime and drip imagery is unaffected. Comparing
against already palette-normalized exported WR1 PNGs can incorrectly report
extra differences: compare decoded original PCXs consistently.

WR2/WR3 `.20,.22,.23,.24,.25,.26,.30..34,.10` are pixel-identical to their WR1
counterparts. WR2 `.11` is pixel-identical to WR1 `.12`. New title cards and WR3
FSTORY endings were visually transcribed into `data/episodes/wrN/clear_*.json`.
The clear title variants intentionally use a plain blue top panel, preserving
the lower landscape and part ribbon, because the original logo is integrated
into the scenery. The normal pixel-art variant retains the complete image.
`tools/build_episode_clear_manifests.py` reproduces the derived manifests.
Contact sheets and clear-preview images are local QA artifacts; final layout
was checked using the Godot renderer as described above.

Startup placements are `(60,30),(0,0),(32,12),(60,30)`, pages `0,1,0,0`.
Threshold table before each stage is `0,7,12,8,0`; displayed-card dwell until the
next stage is therefore `7,12,8,0` seconds, with native loading/input behavior.
Registered startup does not add WR1's runtime shareware/version overlay.

Story is `.30..34` for both episodes. WR3 `.35` exists but is not part of the
five-page native story sequence. WR2 ending is `.10,.11`; WR3 ending is `.10`,
`FSTORY1.WR`, `FSTORY2.WR`, `FSTORY3.WR`. All ending images load at `(0,0)` onto
alternating pages. Both registered endings pass zero to the menu, so they do
not force WR1's automatic Ordering entry.

## Demos

Both tables begin DS:`0x94` and have twenty entries, wrapping after twenty.
WR2 repeats zero-based levels `4,0,10,12,14,19`; WR3 repeats `2,6,8,9,18,19`.
All twelve source files decode with the existing per-update input bits and
`0x20` stop marker. Demos are controls, not embedded word/state snapshots.

Native wrappers at WR2 `0x9628`, WR3 `0x966e` select Hard difficulty 2, boy 0,
and requested level. Main `0x34a9` seeds RNG with 200. Rotations are picture 2,
word 3 (WR2 `0x4e85/0x4e8b`, WR3 `0x4ecb/0x4ed1`). Mystery index is forced to 2
(WR2 `0x72f7`, WR3 `0x733d`). The demo map-loader branch assigns spawn types
`slot & 3` without consuming RNG, but later reset unconditionally performs ten
`rand()%4` draws, including inactive slots. This mirrors the existing recovered
engine's two separate phases; setting slot types only is insufficient.

WR2 `0x61b0..0x61be` skips the next-word loader in demo mode unless the special
flag is set. Thus current session words/cursor are retained. The recorded
control files do not establish one canonical seven-word set for their level.
Use current episode words and source-derived initialization; do not inject WR1
measured checkpoints or future states.

## Malformed WR2 music source

`wr2.5` is 2,709 bytes, SHA256
`0acabe9727b784fc7b4b5e17b7ae1a82640b142e6bb94a112714cf34b9f933be`.
The original ZIP has identical contents. It begins `52 00`, not `43 54`.
Original loader `0x410c..0x41fe` reads the first word and demands `0x5443`
(`CT`) at `0x4198`; it disables music on failure at `0x41f0`. Therefore this
file is not supported as compressed music by the local original executable.
The port explicitly maps this music slot to silence; other valid episode tracks
reuse byte-identical WR1 recordings. No replacement source was acquired.

## Bounded native acquisition attempt

Launched the pre-existing RetroArch DOSBox-pure 1.0-preview5 against a task-owned
WR2 copy under `native/1992/WR2`, with task-owned config, screenshot and save
paths. Original files were not modified. A native core screenshot successfully
captured the Word Rescue Part 2 title (`native/1992/-260923-084445.png`).

Gameplay acquisition was blocked by desktop input access: the Computer Use
activation returned `GetCursorPos failed: Access is denied. (0x80070005)`;
refreshing the returned window captured desktop wallpaper instead of its game
surface. No key injection was attempted after that failure. The owned RetroArch
process received its network QUIT command and was then stopped by its owned PID.
Consequently this pass
does not supply first-playable-screen or movement evidence for WR2/WR3. The
existing frame/state acquisition harness is WR1-hash/address specific and was
not expanded into a new harness for this bounded spot-check.
