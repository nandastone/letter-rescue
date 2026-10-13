# Nature, chalkboard, and board games delivery

## Play this build

The local demo is served at **http://127.0.0.1:8767/**. Refresh an existing tab.
The same game is a portable, offline HTML file at
`output/treehouse/playable/index.html` relative to this directory.

Build SHA256: `1052fab3facf045c8ff8b4fc6580c178eae1db3e6cab3924c0cb35c7d9eef87d`.
Size: 10,549,747 bytes. Original package SHA256:
`53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`.

This is an independent JavaScript implementation using 2,337 decoded original
shapes, 356 original animation scripts, fonts, strings, and PCM samples.
Native screenshots and emulator machine code are not part of the game runtime.

## Added in this continuation

- **Nature exploration:** all 92 animals, original attributes/classes/facts,
  selection and filtering, day/night scenes, animal dragging and ambient poses.
  Each scene holds up to 40 animals. Readable controls provide facts, placement,
  clear and undo without replacing the original bitmap text.
- **Animal guessing:** friend or robot, eight distinct candidates per player,
  questions, optional automatic elimination, manual crossing out, guesses, and
  the original shrub/celebration resource animations on a win.
- **Chalkboard:** six original colors, exact 2×2 chalk, 6×10 eraser, native
  movement clamp, tool cursors, clipping, tray changes, and retained drawings.
  Balloons move out of the way when a tool is selected. An enlarged pad adds
  continuous mouse/touch strokes, undo and reversible clear.
- **Money and Chip board games:** recovered 24-node directed graph, weighted
  rolls, three goal levels, original reward/payment formulas, friend and robot
  turns, reward comparisons, win/loss rules, and interactive chip carries and
  borrowing. The child chooses rewards on robot turns too. Arrow keys drive,
  Space rolls, and Enter confirms a pending exchange.
- **Theater improvements:** recovered director and phrase playback stages,
  actor blink, place flash, weather sequencing, invalid-sentence feedback,
  options and decorations, actor hold-to-drag, and proper prop removal/clamping.

No separate native writing/typewriter activity was found. The original writing
surface is a bitmap chalkboard; this build preserves that activity.

## Verification of this exact build

All eight reports below identify the same build SHA256. The consolidated,
tracked results are in [nature_boardgame_verification.json](treehouse/nature_boardgame_verification.json).

| Area | Behavioral checks | Exact image evidence |
| --- | ---: | --- |
| Base scenes and music | 90 | 3 complete frames, 1 score region |
| Theater | 107 | 10 complete frames |
| Nature exploration | 101 | 5 complete frames |
| Theater continuation and nature quiz | 40 | 13 complete frames |
| Chalkboard | 11 | 8 board/tray regions |
| Board games | 10 | 14 complete frames; 1 retained transient mismatch |
| Boy entrance | — | 73/73 checked render states |
| Theater performance | — | 38/38 display changes, matched in order |

**359 behavioral checks passed**, with no browser exceptions. The checks include
30 complete animal guessing games and 60 complete friend board games across both
modes and all goals (484 board-game turns), robot movement, recursive borrowing,
carry chains, keyboard/mouse/touch support inherited from the base suite, and
mobile layouts. There are **45 exact full-frame comparisons** plus nine exact
region comparisons. These are specified reference states, not a full-game proof.

The extra board-game `turn-b/next-turn` reference is a native frame taken during
reward delivery. It still differs by **778 pixels** because delivery animation
is incomplete. Its difference image and count remain in the report. The separate
settled robot reward reference matches every pixel. No pixel tolerance or
exclusion mask was used to turn the transient mismatch into a pass.

Native random deals/layouts are read as ordinary game state from captured RAM
for reference comparisons. The browser independently composes those states
from original resources. Behavioral checks also play newly generated games.

## Fidelity work still open

- Native callback scheduling, partial-screen transfers, complete audio mixing,
  and exact timing remain unproven. Theater's ordered image match does not prove
  callback timing equivalence; entrance evidence is image membership only.
- Board-game delivery carts, moving money bags, dashboard performances, chip
  transfer motion/timing, full payment and win/loss presentation, and original
  replay dialogs are incomplete. Carry/borrow rules and checked carry screens
  are implemented; the entire exchange animation is not yet equivalent.
- Nature inspection/definition panels and quiz robot/reveal timing need further
  comparisons. Nature currently uses an independent random generator; board
  games use the recovered original LCG but a browser seed and a separate call
  sequence. Neither claims deterministic DOS random-stream parity.
- Theater's native sentence token dragging, correction interactions, and file
  saving/loading are incomplete. The large sentence reorder controls work.
- Music ensembles, advanced original music editing, pet simulation, additional
  room interactions, the dynamic original clock/date, and other remaining game
  behavior still need reconstruction. The fourth telescope view is static.
- Original chalk clearing uses a browser confirmation rather than a pixel-exact
  reconstruction of the native dialog. Enlarged-pad interpolation and undo are
  deliberate modern input additions. Drawings persist within the open game.

## Source and reproduction

See [nature research](treehouse_nature_research.md),
[chalkboard research](treehouse_writing_research.md),
[board-game research](treehouse_boardgame_research.md), and
[theater playback research](treehouse_theater_playback_research.md).
Capture routes are preserved under `treehouse/routes/`; selected native board
state records are in `treehouse/boardgame_reference_states.json`.

Rebuild and verification commands are in the [demo README](../treehouse-demo/README.md).
Generated game assets, captured RAM, screenshots, and detailed difference images
remain under ignored `testing/output/treehouse/`. The existing Letter Rescue
project has not been modified.
