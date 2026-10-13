# Telescope rendering and input

## Reproduction and cause

The uninterrupted activity tour on delivered build `a89b3f65ac50` still had
1,379 differing pixels at `telescope-visit`, including the circular border and
the alien. `activity-tour-current-h` reproduces that result.

The smaller ordinary-control regression `verify_telescope_centering.py` enters
the treehouse, approaches the telescope, selects the alien view and lets its
animation finish. It uses the original checkpoint's pointer position and
compares every RGB pixel. The old build fails with the same 1,379 differences
in `telescope-centering-baseline-b`; candidate A passes with zero differences
in `telescope-centering-fixed-a`.

The cause is integer centering. Original main routine `2534` draws the telescope
background through `6C2E`; helper `6CEE..6D45` subtracts the truncated half of
each shape dimension from the destination center. The browser rounded the
remaining space instead. Those expressions differ for odd dimensions:

```
original x = 160 - floor(width / 2)
previous x = floor((320 - width) / 2)
```

`telescopeView` now uses the original expression in both axes, as the shelf
view already did. No animation timings or sprite origins changed. No original
screenshots or recorded schedules are runtime inputs.

The initial focused-test attempt used the distribution archive hash where
the capture records the repackaged emulator-content hash and stopped before
running. `telescope-centering-baseline-a` is retained; the verifier now checks
the pinned reference package hash. It does not relax the pixel comparison.

## Integrated evidence

Candidate A:
`5d5acf282507f82b12c0cb3f732dbc291c0b0ce79d37485966d0fa3785796d0c`.

`telescope-centering-tour-a` applies the full original activity tour after one
initial snapshot. Its telescope checkpoint now matches, improving image
membership from 22/27 to 23/27. All previously matching images remain matched.
Four room-return image failures and ten object-state mismatches remain; the
complete tour report correctly fails. Active activity state and shared random
state remain matched.

`telescope-centering-environment-a` passes all 183 room animation states.
All 92 suites pass. The candidate is delivered; previous live files are backed up in `telescope-centering-delivery-a` and its served HTTP hash is verified.
The new centering regression is registered in `verify_all.py`.

This correction proves the original final alien image and its occurrence in
the continuous tour. It does not establish exact telescope animation timing
or resolve the remaining room-return and strict presentation failures.


## Background restoration and all four original views

`capture_telescope_views.py` restores the original board-room checkpoint and
uses ordinary room clicks to visit all four telescope views. It reads the
visited-view mask solely to label captures. On the first attempt, a room action
consumed the fourth entrance click; `telescope-views-native-a` is retained as an
incomplete capture. The capture now retries through ordinary input after its
wait. Complete captures B and C use the same commands and inputs.

Candidate A fixed the alien and planets completely. The shelf already matched.
The birdbath improved from 4,842 to 141 differing pixels, exposing a blue ripple
left by the final SCR display. Original telescope wrapper calls at 2735..2765
select background restoration after playback. The browser retained the last
animation display indefinitely. Candidate B draws completed ordinary views
from their background again; the special live robot shelf retains its display.

Candidate B is
`45006b553fd5494c28363a3e14b306a8e865def999a04409326649aaaa549d44`.
`telescope-views-fixed-b` matches all four complete RGB images. The baseline
and intermediate failures remain in `telescope-views-baseline-a` and
`telescope-views-fixed-a`. `verify_telescope_views.py` is suite 91. It exercises
fresh browser entrance and visible view buttons, comparing final images; it
does not claim the original random view selection or animation timing.


The repeated original captures B/C agree on all 409 PNG/WAV files, input
actions, checkpoint states and the complete callback timeline (417 checks in
`telescope-views-repeat-a.json`). Candidate B retains 23/27 tour images, the
same ten object-state mismatches and four room-return image failures in
`telescope-centering-tour-b`. Its environment comparison passes 183/183.

The subsequent input audit began with the original's four view rectangles:
`[55,105,146,216]`, `[55,107,145,214]`, `[42,86,159,235]`, and
`[34,77,168,243]` (top,left,bottom,right), read at DS:0358. Main `26D5..26F3`
uses the selected rectangle to choose replay versus exit. The current browser
uses one rectangle for every ordinary canvas view. The following section records the paired original/browser reproduction and
correction. The final-image tests alone do not cover input decisions.


## Per-view replay and exit rectangles

The input audit reproduced a concrete behavior defect. Original capture
`telescope-input-native-a` restores each completed native view and issues an
ordinary click immediately outside or inside its left edge. All eight cases
choose the destination specified by that view's original rectangle.

`verify_telescope_input.py` replays the actual observed pointer coordinates in
sixteen fresh browser mouse/touch sessions. Candidate B fails eight checks in
`telescope-input-baseline-a`: outside clicks replay the three ordinary views,
and inside shelf clicks leave it. The other eight pass.

Candidate C extracts all four original rectangles at build time and uses the
selected view's half-open rectangle to choose replay versus exit. Its SHA is
`377179be2807525d7c010e2da7e8b517d073be2f930b69d59cb9ff2836850df1`.
This is suite 92. The original click captures and browser test read state only;
no game or random state is assigned during browser journeys.


Candidate C passes all sixteen original-destination mouse/touch checks in
`telescope-input-fixed-a`. The original input capture repeats identically in
B: all 324 image/audio files, eight cases and callback timeline match
(`telescope-input-repeat-a.json`, 329 checks). The unchanged room environment
passes 183/183, and the continuous tour remains 23/27 with the same failures.
The 91-suite candidate B run was deliberately cancelled after candidate C
superseded it; completed B results are retained, and no complete B batch is
claimed. The final candidate C run includes all 92 suites.
