# Playable musical maze delivery

2026-09-27. Build SHA-256:
`061fa409104d75ae789eb4d7dc2c6680edd404f0cb04b2324fd2bf58e997c5de`.

Enter from the music room's original bucket or **Play the musical maze**.
The independent runtime now supports all nine scenes, five sound challenges,
wrong-answer feedback, difficulty changes, collected notes, song guessing,
early wins, full-song victories, replay, and starting another maze. Recovered
paths and character frames animate movement; original samples play the sounds.
Readable controls mirror the sign choices and song pictures.

## Verification

All eleven suites pass on this exact build:

- **453 behavioral checks**, with no browser exceptions.
- **108 complete native frames and 10 regions** match exactly.
- 73/73 entrance render states and 38/38 ordered theater display changes.
- The maze contributes ten complete frames and 17 behavioral checks, including
  **40 completed generated games and 302 turns**, with all five challenge types.
- Existing editor, music, theater, nature, board game and chalk checks still pass.

Full results: [maze_verification.json](treehouse/maze_verification.json).
New command:

```powershell
python tools/treehouse/verify_music_maze.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/maze-check-new
```

Native comparisons cover settled play across all challenge types, the song
chooser, and victory. Observed random choices are supplied as model data only;
all graphics are rendered from original shapes, palettes, fonts and source
geometry. Generated-game checks separately exercise gameplay and render samples
throughout transitions. There are no screenshot assets in the runtime.

## Remaining fidelity work

This is a playable reconstruction, not a completed pixel-perfect clone.
Maze introduction/frog guidance, chooser sliding, disappointed-frog sequences,
complete reward/walking/victory choreography, interruption rules, native random
call order and precise audio timing still need ordered native comparisons and
further implementation. Static frame equality does not establish those claims.

The remaining room/calendar/clock/character interactions, persistent prizes,
music table of contents and remaining editor details, nature sequencing, board
endings and theater persistence remain on the reconstruction list. See the
[editor delivery](treehouse_music_editor_delivery.md) for those boundaries and
the [maze source research](treehouse_music_maze_research.md) for recovered rules.
