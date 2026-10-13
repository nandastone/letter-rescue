# Maze return to the treehouse

## Player-visible defect

The original has two distinct controls during the maze: the top-right treehouse
exit at `(311,10)` leaves the music activity entirely; the adjacent control at
`(291,10)` returns to the piano. The browser previously sent both to the piano.
The treehouse exit remains available after winning, when it must also replace
the solved song and persist the resulting song list and history.

The fix separates these controls in `MusicMaze.click`. `navigateScene` treats
the maze as part of the music activity when returning to the room, preserving
the original room-return animation without playing the piano bucket transfer.
Existing `setScene` logic finalizes a won round and saves before leaving.

## Evidence

Candidate: `8a107c9eb4a91d13b19b36312d0fae0932eb965d011477836abffd7e5aec067b`.
All paths below are beneath `testing/output/treehouse/`.

- `maze-navigation-global-a`: original ordinary maze exit.
- `maze-navigation-piano-a`: original adjacent piano-return control.
- `maze-navigation-victory-a`: original treehouse exit after victory.
- `maze-navigation-baseline-a`: old browser goes to the wrong scene.
- `maze-navigation-fixed-a` and `maze-navigation-victory-fixed-a`: each matches
  all 14 complete RGB checkpoint images, destination, shared random state,
  song list and song history. Six checkpoints in each still have the balloon
  one movement step ahead. These complete comparisons remain **failed**.
- `maze-navigation-exit-baseline-a`: both new desktop/touch treehouse-exit
  journeys fail on the old build; the five prior piano-return journeys pass.
- `maze-navigation-exit-a`: seven fresh ordinary-input wins, exits and reloads
  pass all 53 checks. Includes desktop/touch treehouse exit, readable piano
  return, canvas piano return, Back and interruption during a song replay.
- `maze-navigation-audio-comparison-a` and
  `maze-navigation-victory-audio-comparison-a`: both native observation controls
  retain identical full WAV, callback frames, saved images, actions and states.
  All three observed sound sources/rates occur in order between player inputs.
  One cue crosses the checkpoint boundary in each browser replay; the raw
  mismatch is retained. This does not establish absolute sound timing or
  complete waveform parity.

The replay starts from one original snapshot and then applies the recorded
mouse inputs and elapsed game ticks. There are no per-checkpoint state resets.
Screenshot equality here means occurrence within the corresponding input
interval; it does not establish identical presentation timestamps.

## Delivery

All 85 registered suites pass in one immutable-build batch, including 53 ordinary maze exit/save/reload checks. All 183 environment states pass. The 23 additional comparisons retain prior outcomes. Both new maze exit replays match all 14 RGB images and preserve destination, random state and song history; six balloon-state timing mismatches per route remain explicit failures.

Delivered as `8a107c9eb4a91d13b19b36312d0fae0932eb965d011477836abffd7e5aec067b`; previous live files are backed up and HTTP hash verified. See `maze-navigation-delivery-a/report.json`. Existing strict presentation and other native journey
failures remain open. CPU instruction equivalence is not a deliverable.
