# Timing fidelity: first measured corrections

## Acceptance order

User direction on 2026-09-28: reproduce the original faithfully first; make
improvements afterward. This supersedes the earlier faster-redraw preference.
Original redraw delays and intermediate displays remain part of the target.
Modern readable text is an existing companion to the original framebuffer.

Passing gameplay regressions is not full reconstruction acceptance. Run the
strict timing check separately; its failures remain open work:

```powershell
python tools/treehouse/verify_timing.py --strict --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/timing-strict-new
```

No screenshots are used by the runtime. Captures supply comparison targets only.

## Two reproduced defects

### Candidate-elimination cadence

The original robot question produces six consecutive **31-tick** gaps between
seven eliminations. The previous clone produced six **32-tick** gaps. Sound 1006
contains 1856 decoded samples. Requested rate 8269 maps to effective 8333 Hz through
the original Sound Blaster divisor, giving 13.36397 game ticks of playback.
Rounding playback to 14 before starting an 18-tick countdown introduced the drift.

The generator now retains fractional sample completion and starts the next
countdown from the integer counter at that instant. The actual question sequence
and a minimal three-sound chain both confirm 31-tick gaps. Interruption at tick 5
starts the following 18-tick wait there, ending at 23.

Red evidence: `output/treehouse/timing-baseline-a/report.json` and
`output/treehouse/timing-audio-baseline/report.json`.

### Missing end-of-turn die flash

Overlay 2 cleanup at 3436 calls 3ADB. Its 391D helper sets answered, clears guessing,
and **zeros DS201A**, rather than assigning a 300-tick reminder. The main loop's
2BBF branch immediately invokes 3C9F, which calls 3E27: light die, wait 8, restore.
Only reminder completion sets 300 (3DBA).

The clone reset the timer to 300 during cleanup and omitted this visible step.
It now expires that timer and enters the existing interruptible reminder when
the answer task finishes. The completed native lit frame at run 2789 is matched
over all 64,000 pixels, held 8 ticks, and followed by the restored die.

Red evidence: `output/treehouse/timing-die-baseline/report.json` still matches
38 generated displays but fails the new required native die-flash milestone.
The corrected sequence contains 39 ordered exact displays, with native final
cards, learned answers, player and random seed unchanged.

## Comparison corrections

Telescope approaches and returns now match only inside their own driver input
windows. Previously an identical return frame could match an earlier visit,
making any inferred duration invalid. All 43 displays still match with the
correct bounds; reports include those bounds and native elapsed game ticks.

The timing report records every native display change, including displays the
browser never produces. Checking only that browser frames occur in the native
capture would miss native steps such as the die flash.

## Remaining strict mismatch

Candidate SHA-256:
`fc3148a18435744ce97cb633f7a849d3f745ee9bd8461c4dc39ae59d929e5536`.

The fixed window is original callbacks 1815..2798, anchored at game tick 6496.
The cadence checks pass. **Strict timing fails: 614/984 callbacks match**, with
12 native display changes unrepresented by the clone. No frames are shifted,
excluded, or given a pixel/timing tolerance. The strict command exits 1.

The older build matched 648/984 by this diagnostic: its accumulating cadence
error partly offset earlier redraw delays. The lower raw count after the fix
does not invalidate the independently measured cadence defect, and is not
reported as an improvement in overall alignment.

| Remaining native changes | Observed behavior |
|---|---|
|1895..1900, elapsed 69..73|Turn redraw clears panels, draws robot, and replaces candidate rows progressively.|
|2110..2113, elapsed 253..255|Question-start composition before its first complete actor display.|
|2190,2267,2280,2357|Intermediate animation drawing callbacks.|
|2463,2645|Candidate redraw presentation boundaries.|
|2788, elapsed 833|Cleanup caught before the complete lit die display.|

These require recovery of original drawing order and execution timing, not a
single added delay. Source lead: overlay2 turn calls 287E, 394A, 1E82 at 2FA3..2FB1;
cleanup 3ADB removes question decorations before clearing actor/control areas.

The native capture uses fixed 10,000 emulator cycles, a 70 Hz video callback, and
an approximately 60 Hz PIT game counter. Integer counter sampling does not locate
a callback within a game tick. Inputs polled at callback N execute in the next
emulation interval. Sub-tick presentation alignment is also unresolved.

Strict evidence: `output/treehouse/timing-strict-b/report.json`.
Regression evidence: `output/treehouse/timing-regression-b/report.json`.
Room environment evidence: `output/treehouse/timing-environment-b/report.json`.
All refer to the candidate hash above. Audio waveform/backend equality and
exhaustive input-path coverage remain unproved.
