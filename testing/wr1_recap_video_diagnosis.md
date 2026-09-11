# Five-pixel recap divergence

The failing reference was native counter 4905, compared with clone source frame
4904 under VGA scanout. All five differing pixels belong to the recap picture's
dissolve: native pixels are white, while the clone retains their old color.

The cause was **out-of-order timestamps from two different clocks**, not a
demonstrated VGA phase error. During recap, `original_elapsed` is a paused main-loop
timer. `_present_original()` used it to submit the scene, while
`present_original_recap()` used the active `original_recap.elapsed` timer to submit
the new overlay. Both calls occurred in the intended order but their timestamps
reversed that order in the video queue.

Actual pre-fix submissions at source frame 4902:

| Submission order | Picture | Timestamp, seconds | Timer remainder, seconds |
| --- | --- | ---: | ---: |
| 1 | Old picture in scene submission | 65.1218734166332 | 0.0121265833711777 |
| 2 | Picture with the five pixels erased | 65.1205124658429 | 0.0134875341614160 |

The video clock correctly sorted writes by timestamp. Consequently it applied
the erased image first, then overwrote it with the old image 1.361 ms later. This
left precisely these pixels wrong: (174,41), (189,43), (187,49), (184,52), (190,62).
The trace is saved in `testing/output/recap-video-diagnosis/submissions.json`,
with original runtime output in `capture.log`. Neither is runtime input.

Three hypotheses were considered: writing the wrong page(s), delayed recap work,
and initial VGA phase. WR1 disassembly at 5c0d..5cdb shows the scene draw, current
page selection, Benny drawing, picture-buffer dissolution, and copy back to that
page. It does not support adding a write to both video pages. The clone's timestamp
trace directly exposed the incorrect active timer; no phase search or expected
frame offsets were needed for the fix.

`player.gd` now uses the recap timer while recap is active. Scene and overlay
submissions consequently share the same logical event time and preserve call
order. The ordinary gameplay clock, RNG consumption, animation state transitions,
native fixtures, and video sorting rules are unchanged.

## Regression and verification

`testing/test_wr1_presentation.gd` exercises the actual recap -> player scene
callback -> recap overlay callback chain. It supplies a stale main timer and a
different active recap timer, then checks that the scene cannot be timestamped
after its replacement. This failed before the fix (7 checks, 1 failure) and passed
afterward (7 checks, 0 failures), in about three seconds with the GPU.

```powershell
& $env:GODOT --path . --script testing/test_wr1_presentation.gd -- --original-rules
just parity --scenario recap --vga-scanout
```

The original recap comparison now has **3/3 exact images**, including all 64,000
pixels of the previously failing image, and **369/369 exact state comparisons**.
Its 213 admission-timing differences remain failures, as before. Evidence:
`testing/output/parity/recap-clock-fixed/`. The isolated recap checks also pass
(3,435 checks), preserving renderer state, waits, RNG calls, and skip behavior.

The architectural lesson is that a suspended main-loop timer cannot timestamp
drawing performed by another active sequence. Keeping the video queue independent
made this observable; the regression now tests both callers together.

Initial phase remains unmeasured in older recordings, and CPU drawing costs remain
incomplete. Pixel agreement at the captured frames does not establish exact
continuous video timing. With the actual recap bug fixed, both live play and
replays use scanout by default; snapshot presentation remains an explicit option.

Final full default-scanout validation is in
`testing/output/parity/recap-clock-fixed-all/`: **50/50 exact images** and
**2,913/2,913 exact state comparisons**, with no input differences or execution
errors. All 17 scenarios use VGA scanout; no snapshot fallback is used. The same
533 admission-timing differences still fail the timing gate.
