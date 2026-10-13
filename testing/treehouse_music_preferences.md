# Listening settings across songs and score modes

## Observable defect

The browser kept one listening instrument and reloaded speed from the stock
SONG resource when rebuilding the music controls. Changing songs therefore
carried the wrong instrument forward and lost speed edits. Notation edits also
changed the shared stock record, affecting both score modes.

`music-preferences-baseline-a` reproduces this with an uninterrupted original
journey. Moving from song 20 to song 21 should select instrument 24 at speed 4.
The old browser keeps instrument 12 from the initial snapshot. Revisiting song
21 also loses its edited speed. The ordinary-control baseline
`music-preferences-ui-baseline-a` fails on its first song selection.

## Original behavior and implementation

Overlay 1 loader 3258 obtains speed, instrument and notation from executable
geometry tables at 075F, 0791 and 07C3. Each has 50 entries: 25 for each score
mode. The build now extracts those defaults from the pinned executable. The
browser makes independent session records for the two listening books and
updates the active record through both canvas and readable controls.

Changing pages and score modes loads that record's instrument and speed.
Entering composition preserves listening preferences, and returning restores
the selected listening record. Song selection itself remains shared between
score modes, as observed in the original's four selection bytes.

These listening preferences are executable memory, outside STATUS.DAT. They
reset on a fresh program load. The saved page still restores, and loading it
now initializes the correct instrument. `music-preferences-ui-reload-c` records
the intermediate defect: the saved page was correct but instrument 11 survived
instead of song 21's default 24. Candidate D fixes that initialization.

## Idle animation

The same reference journey exposed control refreshes restarting the idle-eye
timer. Original page/score changes retain its deadline. Music controls now
reset that timer only on entry from another activity. The original main loop
at 00F3–0113 starts the idle animation strictly after its deadline; the browser
now uses the same comparison. This corrects the observed blink and the random
draw that schedules its next occurrence.

## Evidence

- `music-preferences-native-a` and `-b`: 11 checkpoints driven by ordinary
  clicks from one original snapshot. Checkpoint state/inputs, all PNGs, complete
  callback timeline and audio repeat identically; see
  `music-preferences-native-repeat.json`.
- `music-preferences-check-c`: all 11 full-RGB and active-state/random
  checkpoints pass. No per-checkpoint reset or image masking.
- `music-preferences-ui-d`: 11 ordinary-control checks pass, including
  independent speed/instrument/notation, composition return, room return and
  full browser restart. No gameplay-state installation.
- `verify_music_preferences.py` and `verify_music_preferences_native.py` are
  registered with the complete regression runner.

Candidate D SHA:
`fb6652aa720a42d1873d6dcb545e061b6a7496020e3950ac92d06b6bc4c39f09`.
Its integrated run and delivery are recorded in the completion ledger after
verification. This closes the settings behavior under test; full audio waveform
and presentation timing fidelity remain separate requirements.

## Delivery

`music-preferences-regression-b` passes all 60 suites together on candidate D.
`music-preferences-environment-b` passes all 183 environment image states.
`music-preferences-delivery-a` backs up the prior build and confirms the live
HTTP response has the verified SHA. Existing strict failures were rerun and
retained. The game is not marked complete.
