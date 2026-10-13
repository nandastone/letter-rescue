# Calendar controls and continuous room journey

## Original input capture

`capture_room_journey.py` restores one ordinary room snapshot. It pops the
balloon through three ordinary clicks, opens the calendar, dismisses it through
the page, browses next/previous days, closes it, changes the cloud, uses the
clock/spider/nest, draws two chalk strokes, declines and accepts erasure, and
opens/closes the calendar again. It never writes original RAM.

`room-native-journey-c` and `-d` repeat in inputs, decoded state, all images,
callback timeline and audio (`room-native-repeat.json`). Earlier attempts `-a`
and `-b` stopped at an incorrect assertion that clicking above the open page
would close it; their evidence is preserved.

## Reproduced calendar defects

1. **Canvas hit behavior.** Original resident `11C9..11EF` closes an open page
   when the pointer is in `(top28,left162,bottom110,right283)`, after object hit
   handling. A click there does not activate the obscured cloud/nest. The flap
   handler `156A..1574` does nothing while already open. The browser previously
   ignored a click on the page's cloud area and toggled from above the page.
   The isolated close replay starts with an exact full-RGB open page, then
   fails in both the image and open-state field on the old build.

2. **Completion side effects.** Opening the normal calendar calls BC43 after
   unrolling. Closing calls B95C, which reschedules the room environment and
   object timers. The runtime now reports calendar slide completion to the
   existing resident scheduling operations. Blank confirmation-page opening
   does not perform the normal calendar-open reset. Closing also resets the
   cloud countdown to 300 ticks, preventing an immediate extra cloud step.

3. **Date narration.** Resident `1521..1582` updates the date, closes an open
   page, speaks the date and then opens the new page. Browser date browsing
   previously skipped speech and opened immediately. It now uses the existing
   original voice-fragment queue, then opens when that queue completes. The
   room remains occupied during reading and rolling. The date strip and
   readable calendar control share this sequence.

The callback is an operation completion hook; it does not replay native event
schedules or execute DOS instructions.

## Evidence and limitations

- Old close failure: `calendar-close-baseline-a`.
- Hit-region correction alone: `calendar-close-click-a` (image fixed, random
  state still wrong).
- Complete close correction: `calendar-close-fixed-a`.
- Date narration/ordering: `calendar-next-fixed-a`.
- Final ten-checkpoint calendar sequence: `calendar-journey-fixed-a`.
- Full room comparison on candidate `36849cc7af88`: `room-native-check-d`.

The ten calendar checkpoints match full RGB images, gameplay/object fields and
random state. `verify_calendar_journey.py` registers that scope. Existing room
component tests now wait for narration plus rolling when browsing dates; their
calendar content, date arithmetic, Today, mobile layout and close assertions
remain intact. Direct flap unrolling still takes seven two-tick steps.

The complete room comparison remains failing from the clock checkpoint onward,
starting with a missing random-state side effect. Later environment timing,
cloud and chalk images still need investigation. These full-journey failures
remain required completion evidence. Neither the passing calendar checkpoints
nor the speech dispatch establishes full waveform or exact presentation parity.

## Delivery and next reproductions

Build `36849cc7af88` is served after all 67 registered suites ran together and
passed, plus 183 environment image states. Candidate/served hashes match;
`calendar-delivery-a` preserves the prior live build and verification. Existing
strict board/nature/yard failures were rerun and retained. The full room
comparison is now another explicit failed completion input.

Short `room-clock-baseline-b` and `room-chalk-baseline-b` initialize the original
closed-mouth portrait sprite 931 at their starting snapshots, then use ordinary
inputs without later resets. Their starting images are exact. Earlier `-a`
attempts omitted that retained portrait sprite and differed by ten pixels;
those fixture failures are preserved. Clock completion then differs only in
random state. The white stroke differs in RNG and by 54 pixels. These are the
next bounded reproductions, alongside narration interruption/navigation checks.
