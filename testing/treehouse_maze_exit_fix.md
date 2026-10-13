# Maze victory controls and saved song history

The ordinary-input exit audit found four failures on build `014d9c299a2b`:

- Desktop and touch **Back to the piano** skipped the original victory-control
  flash and climb-out animation.
- Pressing that button during victory-song playback immediately left the maze;
  the original canvas control interrupts playback and remains at victory first.
- Global **Back** replaced the solved song after writing browser persistence,
  leaving the stored song list/history stale until another save or pagehide.

The canvas return route passed and provided an existing working path. The new
`MusicMaze.activateControl()` routes readable victory replay, new-game and
return buttons through the same rectangle-action handler. That preserves its
busy-input behavior, control flash, original departure sequence and song
replacement without maintaining a second version of those rules.

All maze exits now finalize solved-song replacement before `GamePersistence.save`.
`replaceSong()` already guards against duplicate replacement, so the animated
departure's earlier replacement remains safe. Global Back retains its direct
exit behavior; its save now includes the finalized history.

Source basis: original overlay 1 `52D9..537D` and `85FF`, documented in
`treehouse_maze_runtime_audit.md`. The return control flashes for 18 ticks,
plays the frog voice and follows the scene-9 ladder path before leaving.

Evidence:

- `output/treehouse/maze-exit-baseline-a/report.json`: four failing routes and
  passing canvas control.
- `output/treehouse/maze-exit-fixed-a/report.json`: all five routes and 41 checks
  pass on candidate `805cd0adac74`.

Each route wins a fresh game through visible controls before testing exit,
immediate stored song/history values and reload. No gameplay state is installed;
answers are read to choose inputs and the animation clock is accelerated.
This is input/save/sequence evidence, not exact native presentation timing.

Delivered after all 46 regression suites and 183 environment states passed.
Evidence: `output/treehouse/maze-exit-regression-a/report.json`,
`output/treehouse/maze-exit-environment-a/report.json` and
`output/treehouse/maze-exit-delivery-a/report.json`. Strict nature timing remains
614/984 callbacks with 12 unrepresented native display changes, unchanged from
the previous build. Full-clone parity remains unproved.
