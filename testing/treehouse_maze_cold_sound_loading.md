# Maze ending: cold sound loads and prepared payloads

## Original boundary evidence

`capture_maze_ending_boundaries.py` restores the pinned `correct-6.state` and
replays the remaining original pointer actions through the completed victory
song. It observes routine entry/return boundaries without modifying guest RAM
or profiling individual instructions. A separate run uses the same core and
input with observation disabled.

Evidence: `maze-ending-boundaries-a`, `maze-ending-boundaries-control-a`, and
`maze-ending-sound-payload-a` under `testing/output/treehouse/`.
The payload capture additionally records the 19 sound-load entry/return pairs.
All ordinary control comparisons pass: callback timeline, final checkpoint
images/RAM and captured WAV. The native reference remains unchanged.

The earlier dispatch audit localized deficits around chooser opening, closing
and victory scene construction. The new call boundaries show:

| Operation | Start tick | End tick | Measured load duration |
|---|---:|---:|---:|
| Cached frog disappearance sound 10034 | 18092 | 18092 | 0.0490 ms |
| Cold drawer-open sound 1004 | 18183 | 18187 | 63.9529 ms |
| Cached collected-song instrument 12009 | 18235 | 18235 | 0.0644 ms |
| Cold drawer-close sound 1003 | 18311 | 18316 | 89.9895 ms |

The frog disappearance itself takes exactly 30 game ticks, followed by its
60-tick explicit wait. The eight-note collected melody takes exactly 64 ticks;
instrument restoration takes less than 0.01 ms. These observations eliminate
those operations as the source of the earlier multi-tick deficits. Sound
loading, chooser preparation and scene construction need clock integration.
The final scene's construction spans ticks 18846–18857 before actor arrival.
These times are offline comparison evidence, never runtime constants.

## Implemented preparation correction

`OriginalSoundLoading.prepare()` previously changed allocation sizes and the
prepared flag but left the source cache's payload compressed. It now writes the
decoded PCM into that same handle's shared payload map, changes codec 255 to 8,
and updates the sample count from the compressed stream. Rate, flags and loop
boundaries are preserved. The stream's count takes precedence over the old
header count, including original resources where they differ.

The decoder follows resident E964; header writes follow E915/E920. It runs
without any instruction-work module. The existing cached, nondigital and raw
PCM branches retain their semantics. Malformed compressed input is rejected
before allocation is changed.

`verify_sound_payload_loading.py` checks the production
`OriginalStartupResources.loadSound()` composition against the 19 native load
boundaries, starting each isolated comparison from its original initial state.
It compares returned handles, allocation/ownership state, near heap and exact
payload hashes. The catalog's semantic cached-handle word is serialized for
comparison; all other captured directory bytes remain checked, including slack.
These fixtures are test inputs, not runtime data.

- The reconstructed baseline model matches the previously recorded model hash
  `7356e4b338faf4f368ae01212c8d3b372e22b9abc83c38f738298778c202b9c1`.
  It fails exactly the two cold compressed sound payloads.
- Corrected model: **341 checks pass**, including all 19 original loads, all
  273 compressed digital asset payloads against the independent Python decoder,
  ordinary original controls, and three malformed/header/wrapping checks.
- Continuous startup through retained SND 0: **98 native comparisons and six
  focused checks pass**.
- Existing continuous resource regression: **104 memory checkpoints, 79 shapes,
  12 scene phases and 2,399 sound loads pass**. It retains its original scope;
  it does not newly prove every payload byte or generated whole-game lifetimes.

The first payload-check attempt left the catalog hash unchanged when its
semantic cache handle changed, causing three false catalog-payload differences.
That report is preserved as `maze-sound-payload-check-a`. The revised verifier
serializes the actual model directory handle and keeps the entire byte
comparison. The baseline then fails only the two compressed payloads, and the
corrected model passes (`maze-sound-payload-check-b`).

## Delivery and remaining work

A fresh build is byte-identical to served build `d2ecc31d6a0a`.
The playable game does not yet use this resource loader; no timing correction
has been delivered. The 23-tick early victory song and all other strict failures
remain open. Next connect semantic cold-load/cache operations and scene drawing
to the game clock, preserving input interruption and cache lifetime behavior.
Do not change melody tempo or add measured delays for individual sound IDs.
