# Treehouse room/calendar delivery

2026-09-27. Current independent browser build SHA-256:
`9838fc4657fc3ffb14e17927129a154c28d9583aecd9237d9a2fa629e32f74b3`.

## Playable additions

- The calendar opens/closes with its original roller artwork and seven movement
  steps. It displays the original daily heading and history text.
- A readable panel offers previous/next day, Today, and Close. Read aloud includes
  the calendar when a local English voice is installed. All 366 leap-year daily
  entries are present. Day navigation handles month/year boundaries and respects
  the original January 1980 lower limit without changing the computer's date.
- The room starts on the local date and displays a live 12-hour clock using the
  original digit sprites. Clicking the clock gives a readable time announcement.
- Clicking the cloud cycles the seven original pictures; the open calendar
  blocks this interaction. The pinwheel/radio hotspot plays its recovered sound,
  and the original exit ladder returns outside.
- The previous music editor and musical maze additions remain available.

## Verification on this build

All twelve suites pass: **471 behavioral checks, 108 exact complete native frames,
13 exact regions, and no browser exceptions**. The suite also retains 73/73
entrance render-state matches and 38/38 ordered theater display changes.

New room coverage contributes 18 checks, two exact calendar regions and one exact
cloud region, including its original pointer. The cloud's horizontal position is
read from captured model memory (x198), accounting for the restored core's segment
displacement; no native image pixels are used in rendering. This comparison does
not establish automatic cloud-motion timing.

The ordinary runtime uses the local clock. Base-frame verification injects the
reference DOS date/time (January 1, 1992 at 12:39), keeping deterministic reference
inputs separate from actual play. No pixel tolerances or comparison masks were
introduced. The region comparisons are explicitly limited to the stated bounds.

Full results: [room_verification.json](treehouse/room_verification.json).

```powershell
python tools/treehouse/verify_room.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/room-check-new
```

## Reconstruction work still remaining

- Character hunger/tiredness, fruit/toy dragging, sleep and alternate poses;
  nest/spider/portrait interactions and persistent reward/prize presentation.
- Native spoken time/date, automatic cloud drift, and ordered room/calendar
  transition comparisons. Modern readable time announcements are implemented.
- Maze introduction/frog guidance, sliding chooser, full reward/walking/victory
  choreography, interruption handling, and exact audio/random-call scheduling.
- Music table of contents, listening terminal page, native text-entry/printing,
  Ctrl+erase-all, animated dialog faces, and remaining note/palette feedback.
- Nature question/guess/turn sequencing, board payment/endings/replay, theater
  save/load, and exhaustive motion/audio comparisons throughout the game.

**Full-clone parity remains false.** Earlier release reports retain their own
build hashes and verification results: [music editor](treehouse_music_editor_delivery.md),
[musical maze](treehouse_music_maze_delivery.md),
[preceding fidelity work](treehouse_fidelity_continuation.md).

Source findings: [room research](treehouse_room_followup.md). The cloud source
also maintains a horizontal position: resident0xD50 increments it;0x24C2 initializes
it;0x22E1 draws it clipped to `(30,163,80,283)`. Centering alone does not reproduce
the position after room-loop updates, which explains the initial comparison gap.
