# Complete theater journey and saved decoration fix

## Scope

The pinned original is driven from a saved room through theater options, four
sentence choices, an invalid performance, correction, a valid performance,
decoration placement, scenery/weather changes, shuffle/correction and room
return. `capture_theater_journey.py` records ordinary mouse clicks and held drags.
There are no writes to original game RAM. The browser comparison installs one
initial room snapshot, then uses those inputs without further state or RNG resets.

`theater-native-journey-e` and `-f` repeat all 29 checkpoint PNGs, the complete
19,436-callback timeline and audio exactly. The comparison is recorded in
`theater-native-journey-repeat.json`. Earlier captures remain preserved: the
first missed the theater hotspot, the second expected the wrong options scene,
and the next two retained a stale frontend image at the initial checkpoint.
Waiting 60 frames after restore lets the original redraw before capture.

## Delivered corrections

**Sentence wrapping.** “The baby blows bubbles at the beach during a storm.”
incorrectly kept “a” on its first line. The original searches backward starting
before the fitted character count (overlay 4, 2CD0–2CEA). The browser now uses
`lastIndexOf(" ", end-1)`. The minimized full-image difference was 746 pixels;
the corrected comparison is exact. Font metrics and sentence content are intact.

**Decoration coordinates.** A pointer on a scaled canvas could create a prop at
fractional coordinates. The binary save reloads integer positions, visibly
changing geometry. New props now start on the original integer pixel grid.
`verify_theater_prop_save.py` reproduces this through visible controls, a drag,
exit and full reload. The baseline changes position on reload; the fixed build
retains the entire saved theater state, including exact prop coordinates.

## Evidence and limits

Candidate SHA-256:
`3d7c96f509e1e3ea11df0710e8a2abbf9ddacc5f8de7fae8c2075b43371fe2d3`.

- `theater-wrap-baseline-a` / `theater-wrap-fixed-a`: original text defect and fix.
- `theater-prop-save-baseline-a` / `theater-prop-save-fixed-a`: reload defect and fix.
- `theater-wrap-regression-b`: all 53 registered suites pass together.
- `theater-wrap-environment-b`: all 183 environment image states pass.
- `theater-native-check-d`: all 29 reference images occur in their corresponding
  generated intervals; theater selection, token order, validation, actor and prop
  geometry match. The complete report still fails because room-return RNG differs:
  expected 4031028557, actual 741076434. This remains an open integration issue.
- `theater-wrap-strict-b`: existing nature timing discrepancy remains at 614/984
  exact callbacks, with 12 missing display changes.

Image membership does not prove exact presentation timestamps. Repeatable native
audio is a reference fixture, not evidence of browser waveform parity. Complete
theater audio/timing and return continuity remain open. No captured images or
recorded input/timing schedules have been added to the game runtime.
