# Theater entrance click boundary

## Confirmed defect and correction

The browser opened the theater for clicks outside its original room hotspot.
The original rectangle is top 121, left 49, bottom 145, right 77, with exclusive
bottom/right edges. The browser previously accepted x 46..81 and y 107..154.

The builder now extracts room table entry 13 from the pinned executable
(`0x2e938 + 13*8`) into `ORIGINAL.theater.room_entrance`. The canvas dispatch
uses the existing rectangle hit helper. The readable theater button is unchanged.

## Paired reproduction

`capture_theater_room_input.py` restores the same original room snapshot for
eight ordinary clicks, one inside and one outside each edge. It reads the
actual mouse coordinates and destination; it never writes original RAM.

| Edge | Outside point → scene | Inside point → scene |
|---|---|---|
| Left | (46,134) → room | (51,134) → theater options |
| Right | (78,134) → room | (73,134) → theater options |
| Top | (62,119) → room | (62,125) → theater options |
| Bottom | (62,148) → room | (62,143) → theater options |

Native captures `theater-room-input-native-b` and `-c` agree in all 311
repeat checks, including 301 PNG/WAV files, actions, state observations and
the callback timeline. `theater-room-input-repeat-a.json` preserves the proof.
Capture `-a` is retained: its initial expectation mistakenly used scene 8
(maze) for the theater options, whose original scene ID is 13. Its captured
observations were not rewritten. The corrected captures also move the left
outside point one pixel right to exercise the browser's old inclusive edge.

`verify_theater_room_input.py` starts sixteen fresh browser sessions. Each
chooses a character using the visible button, finishes the entrance, then
replays one captured point using real mouse or touch input. Only animation
time is accelerated; it does not install state, seeds or destinations.

- Delivered-build baseline `theater-room-input-baseline-a`: 8/16 pass;
  all eight outside mouse/touch clicks incorrectly enter the theater.
- Candidate `theater-room-input-fixed-a`: 16/16 pass with no page errors.
- Candidate SHA-256:
  `d2ecc31d6a0a8f254c519335ffa16739c566806f915fe75f5685203274f06d13`.

The verifier is registered in the complete regression batch. All 93 suites and 183 environment states pass. The candidate is delivered,
with previous live files backed up and the served HTTP hash verified. This check establishes input
destinations; it does not establish exact scene, audio or transition timing.
All broader fidelity failures remain open.
