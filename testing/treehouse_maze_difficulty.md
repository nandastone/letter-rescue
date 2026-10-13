# Maze adaptive difficulty survives reentry

## Player-facing defect

Two fresh ordinary-input sessions, desktop and touch, reproduce both directions
of the defect on candidate `9a67a26e9613`: two correct answers enable advanced
mode, but returning to the piano and reentering restores easy mode. Reloading
correctly restores the saved advanced preference; after a wrong answer selects
easy mode, another piano exit/reentry incorrectly restores advanced mode.

Evidence: `testing/output/treehouse/maze-difficulty-baseline-a/report.json`.
Four of twelve checks fail, with no JavaScript errors. The test reads answers
and advances animation ticks; all gameplay and navigation uses visible controls.

## Cause and correction

The original uses one shared difficulty word, also used by the advanced
preference (overlay 1 shared offset A8). See the pinned-source recovery in
`treehouse_maze_generation_research.md`, Persistent fields and defaults.
Existing native cross-activity tour evidence also retains advanced mode on maze
reentry (`maze-activity-tour-state-e2`, final checkpoint).

The browser cached the entry difficulty in `initialAdvanced` when loading the
activity. Adaptive answers changed `hard` and the saved preference but left that
cache stale. `reset` restored the stale value on each reentry. The correction
updates the entry value together with the current difficulty and preference.
The settings panel and save import already update both values together.

`verify_maze_difficulty.py` covers easy-to-advanced adaptation, piano reentry,
browser reload, advanced-to-easy adaptation and another reentry, on mouse and
touch. It is registered as the 87th regression suite. Delivered `2d29766c93dda302b3e0c0d618a36f40eec6f91a92bbfbf2655a77206093869b`. All 12 focused checks and all 87 regression suites pass. See `maze-difficulty-delivery-a/report.json`. This is a gameplay/persistence fix; exact presentation
timing and complete native fidelity remain separate open requirements.


## Candidate verification

Candidate `2d29766c93dda302b3e0c0d618a36f40eec6f91a92bbfbf2655a77206093869b` passes all 12 focused mouse/touch checks (`maze-difficulty-fixed-a`). The full 87-suite regression passed before delivery. The native activity tour retains the five image and ten room-object mismatches, with final maze reentry matching; all 58 sound sources/rates match between inputs. The served build is now `2d29766c93dd`; its HTTP hash matches the candidate.


All 87 regression suites pass on the delivered build, including 12 new desktop/touch difficulty checks. All 183 environment states pass. The paired activity tour retains the same five image and ten room-object mismatches, with final maze reentry matching. All 58 observed tour sounds match sources/rates between inputs. Strict timing remains failed. Other supplemental comparisons retain their previous-build hashes and are explicitly historical, not newly verified.
