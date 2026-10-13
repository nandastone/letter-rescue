# Treehouse music editor delivery

2026-09-27. Independent browser build SHA-256:
`9683e2fbfbf29eb30d3950c7db2e4e6ac54e1804f526b2cc3376c632d65d71c6`.

## Added

- Original short and long composition books: 42 writable pages each, plus the
  original stored terminal song and The End artwork.
- Replacing notes, marker dragging, vertical pitch dragging, duration selection,
  dragged rests, per-note erasing, spelling defaults, and repeat playback.
- Original copy, whole-song erase, and random-song confirmations. Copy finds
  the first unused page. Erase preserves tempo, instrument, spelling, and
  duration bytes; deleting notes leaves holes without shifting later notes.
- Editable song names, automatic local saving, and original-format SONGS.DAT
  import/export. Imported 65-byte records, 36-byte CP437 titles and two trailing
  bytes are preserved. Import validates both books before replacing either.
- Readable controls for position, duration, spelling, naming, rests, dialogs,
  download/upload, and browser printing.
- Correct robot shelf telescope view, including the original first display of
  MODULES SCR3610, centering, and clipping.

## Verification

Ten verification reports share the build hash above. Full results are bundled
in [music_editor_verification.json](treehouse/music_editor_verification.json).

**436 behavioral checks passed. 98 complete 320×200 native reference frames and
10 regions match exactly. No browser exceptions were recorded.**

The new editor suite contributes 24 checks and **30** complete frame comparisons
(29 music screens and the robot shelf). It covers replacement, rests, erasing,
spelling, marker/pitch dragging, copy dialogs, page navigation, terminal page,
both 42-page books, reload persistence, real keyboard/buttons, downloads and
file-picker imports. Both the packaged and a natively edited SONGS.DAT round-trip
byte for byte, all 8,688 bytes. Invalid imports leave existing books intact.

The prior nine suites still pass: 73/73 entrance render states and 38/38 theater
display changes in original order, 30 quiz games, 60 board games/484 turns,
all 42 instrument choices, mobile layout, and existing scene comparisons.

These comparisons use complete RGB equality without masks or tolerances.
Idle-eye phases are aligned explicitly and recorded. Cursor behavior includes
the original red cursor remaining visible for one eraser-exit frame until the
next pointer movement. Static equality does not prove timing or audio parity.

## Remaining work

The complete clone is still in progress:

1. Musical maze runtime. Its graph, five challenges, transitions and victory
   model are recovered; ten independent research reconstructions are exact.
2. Remaining room interactions: calendar, clock, clouds, character hunger and
   tiredness, fruit/toy dragging, ambient events and persistent prizes. The
   original needs counters belong to the chosen child, not a separate pet.
3. Music table of contents, listening terminal page, native text-entry flow,
   original print layout, Ctrl+erase-all, dialog face animation, selected-note
   feedback, palette audition and exhaustive input/animation timing comparisons.
   Browser printing and readable title controls are modern conveniences.
4. Nature question/guess/turn sequencing and callbacks; board payment and
   victory/replay presentation; theater save/load and remaining motion checks.
5. Shared scheduling, random-call alignment, audio timing/mixing and exhaustive
   frame sequences. No full-clone parity claim is made.

Primary-source details: [editor](treehouse_music_editor_research.md),
[maze](treehouse_music_maze_research.md), [room](treehouse_room_followup.md).
The previous [delivery](treehouse_fidelity_continuation.md) is retained unchanged
as a historical snapshot.
