# Word Rescue Parts 2 and 3: port assessment

Date: 2026-09-23. Scope: feasibility and recommended approach; no game code changed.

## Recommendation

Reuse the recovered simulation, import each episode's content, and keep episode
selection independent of the existing Legacy/Letter Rescue presentation choice.
Modernisation has not removed the original implementation. It does mean that the
default game's final pixels and wall-clock admissions are not a native-parity
target. Validate original behaviour through Legacy and inspect the modern result
separately. A complete cycle-exact reconstruction of both new episodes should be
an optional fidelity goal, not a prerequisite for adding them to Letter Rescue.

## What remains reusable

- `scripts/core/game.gd:85` selects either the retained legacy presentation or the
  modern presentation. Both use the same movement, matching, enemy, pickup,
  rescue and exit models in `scripts/core/`.
- `scripts/game/smooth_motion.gd` offsets sprites/camera for interpolation and
  clears those offsets before physics ticks. It does not rewrite logical positions.
- `scripts/core/vocabulary.gd` routes Legacy directly to original words/pictures;
  modern vocabulary is an adapter in `scripts/game/krsna_vocabulary.gd`.
- `scripts/core/game.gd:89` only attaches smooth motion and berserker mode outside
  Legacy. The power-up's extra stride is explicitly modelled in
  `scripts/core/wr1_motion.gd`; Legacy uses the original one-step stride.
- `tools/run_wr1_parity.py` explicitly launches `--legacy` against immutable native
  checkpoints, state traces, timing evidence and sampled screenshots.

These are source-code observations, not proof that WR2/WR3 rules are identical to
WR1. See [original-file investigation](wr2_wr3_source_research.md) for the native
episode comparisons and unresolved differences.

The supplied registered WR2/WR3 builds each contain **20 playable levels**:
the map files and title strings extend through level 20, and the native level
selection and completion comparisons use 20 instead of WR1's 15. This is 40
additional levels for this source set. Their movement instruction sequences also
closely match WR1, with relocation-like operand differences; this supports reuse
but does not establish full executable or timing equivalence.

## Modern differences are deliberate

`scripts/core/game_manager.gd:27` uses 240 Hz physics admission for the default
game. `scripts/game/game_presentation.gd` skips VGA/page-flip emulation and
drawing-cost accounting. `scripts/core/game.gd:617` only attaches the recovered
recap drawing-cost model in Legacy. New font rendering, word/picture replacements
and the optional power-up also make the modern game a different comparison target.
Therefore, screenshots of Letter Rescue cannot establish original pixel parity.
None of this requires undoing the modern game to import the other episodes.

## Actual port work

| Area | Existing assumption | Required change |
| --- | --- | --- |
| Episode selection | Launch arguments select presentation only | Episode descriptor selected before frontend/game creation; keep presentation as a separate setting |
| Maps | `level_loader.gd` loads `data/levels/`; `game.gd:341` separately loads `data/wr1/` rules | Episode paths for both geometry and raw rule maps |
| Words and pictures | `wr1_words.gd` reads one word stream; `wr1_pictures.gd` names WR1 archive entries | Episode word stream and picture resolver; apply modern substitutions afterwards |
| Scenery and sprites | Global tileset/backdrop paths and WR1 sprite names in `game.gd`/`player.gd` | Episode art tables; share only assets verified identical |
| Progression | `MAX_LEVELS = 15`, save decoding/clamping and frontend checks also assume 15 | 15 for the supplied WR1, 20 each for the supplied WR2/WR3, used consistently |
| Saves | `wr1_profiles.gd` saves under `user://wr1/` with `.wr1` and `high.wr1` | Episode-specific progress/high scores; explicitly preserve existing profiles and option-import behaviour |
| Frontend | WR1 titles, story, ending, readable-page cleanup and cached assets | Episode frontend data, cache separation and appropriate Clear Text layouts |
| Audio/demos | One audio manifest and `data/wr1/demos/`; attract-loop modulus 15 | Episode manifests, demo order and available demos |
| Extraction | Converter detects WR1/2/3 but chooses the first present and loops only 15 levels | Explicit episode selection and verified level count; avoid output-name collisions |
| Native evidence | EXE hashes, offsets, hooks and tables are WR1-specific | Identify corresponding WR2/WR3 routines and capture new evidence; do not rename WR1 fixtures |

The existing converter is a useful starting point, not a complete port command.
For example, `tools/extract_wr1_rules.py` and `tools/extract_wr1_level_titles.py`
deliberately reject an executable other than the researched WR1 hash. Maintain
equivalent version checks when supporting additional executable builds.

## Suggested sequence

1. Inventory the supplied binaries, archives, level counts, vocabulary, title and
   ending tables. Compare movement/matching/enemy routines before assuming shared
   rules. Resolve malformed/duplicate map markers against the native loader.
2. Introduce a small episode descriptor with WR1 defaults; leave simulation code
   shared unless a measured episode difference requires a variant.
3. Import one representative level from each new episode, including its words,
   art and raw attributes. Compare native movement, contacts, matching, hazards,
   rescue and exit using Legacy; then inspect modern text and smooth movement.
4. Import all confirmed levels and finish episode choice, saves, story/ending,
   audio and demos. Check progression and completion, plus unusual map features.
5. Retain the WR1 regression baseline; add episode-specific native comparisons.
   If full pixel/cycle parity is desired, expand native capture and timing work
   explicitly rather than assuming WR1's cost model proves WR2/WR3 timing.

## Validation and limits

The existing full-run record in [parity workflow](wr1_parity_workflow.md) reports
22,460/22,460 states and 196/196 sampled images matching on 2026-09-09, but three
one-counter timing residuals in demos 6 and 13. It explicitly says the strict full
suite exits 1. This assessment does not turn that historical run into a clean or
exhaustive parity claim.

Fresh audit: Godot 4.6.1 import passed. The default-game smoke check passed with
900 frames, 65 logical updates, 637 moving frames, and a 1.60-pixel 99th-percentile
drawn step.

Fresh focused Legacy check: `demo_level4` passed with 1,624/1,624 measured states,
11/11 sampled images, and no input, timing, terminal or execution differences.
See [audit report](output/parity/episode-audit-20260923/report.md). This was one
representative demo, not a new full fifteen-demo run. No WR2/WR3 gameplay was run.
