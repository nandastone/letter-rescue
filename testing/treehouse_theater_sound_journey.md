# Theater sound and selection presentation

The integrated sound audit found player-facing omissions in the served
`b0b73bf1f6f0` build: option clicks, new-token travel, curtain opening/closing,
and the associated waits before phrase narration. The spoken phrases were
present, but 33 of 73 observed original sound sources had no corresponding
browser dispatch in their input interval.

## Original evidence

`capture_theater_audio_journey.py` reuses the ordinary-input theater journey.
It reads the current digital source at the existing safe video boundaries;
it does not patch game code or alter inputs. Original decoded PCM hashes
identify the sound resources. The resulting `theater-audio-native-a` capture
matches the uninstrumented `theater-native-journey-e` control in all 29 saved
RGB screenshots, the complete WAV, video callback timeline, actions and
checkpoint states (33 comparisons). Thus the observations did not change the
recorded playthrough.

The observer can miss a repeated start of the same source between video
boundaries. The event comparator therefore requires each observed source in
order while permitting additional browser calls. It verifies those observed
cues; it cannot establish complete event counts, exact scheduling or full
rendered audio parity. Both limitations are included in the reports.

Baseline: `theater-audio-baseline-a/report.json` fails with 33 missing cues.
Candidate C: `theater-audio-events-c/report.json` matches all 73 observations.
The corresponding full journey matches all 29 RGB checkpoints and compared
gameplay/random state. The 14-checkpoint notebook journey also passes.

## Runtime implementation

- Options, category headings and decoration selection dispatch original 1008.
  Opening the editor lets this short click finish before the curtain sound
  replaces it. An earlier candidate dispatched both in the same tick; the
  retained `theater-audio-overlap-baseline-c` comparison fails that case. The
  correction waits its data-derived four ticks (sample duration 3.65 ticks).
- New Mix Up choices move the original token from notebook to rail with sound
  10035 before narration. Motion uses resident 6DA9's Manhattan stepping,
  publishing every eight steps with four ticks per draw. Existing rail swaps
  use the same motion. A manually dropped notebook token does not fly again.
- Place/time changes close and reopen the curtains with sound 10032. The
  previous stage remains visible until the close completes. Both directions
  use the original three eight-tick stages (overlay 158F/16AD) and stop the
  curtain sound when the movement completes.
- Choice narration follows the presentation and uses the existing actor/place
  blink and action preview. A time choice blinks the weather; a performance
  still runs its animation. Its final 20-tick pause retains the idle weather
  picture. Overlay 48B2/48FC/4949/49B7 defines those paths.
- Entering opens the curtains; returning to the room first closes them.
  If that close completes during `advance()`, the new room transition owns
  the rest of that tick. Room reminders cannot start halfway through it.

The initial candidate exposed that last same-tick room-update defect. Its
29 checkpoint images matched, but the return reminder assertion failed.
Candidate C corrects the update handoff and passes that assertion. Candidate D
also replaces an initial diagonal interpolation with the already recovered
original Manhattan token path.

## Verification changes

An independent output check drives the actual visible Start the theater button
and renders the production mixer offline with the game clock controlling event
scheduling. `theater-click-audio-baseline-e` fails (attack correlation 0.124);
`theater-click-audio-fixed-g` matches all 2,000 measured original attack samples
exactly after one bounded alignment, with no gain fitting. This confirms that
the restored click reaches the output. It does not prove absolute input latency
or the complete curtain waveform.


Several historical fixtures assumed choices and curtains completed instantly.
Their static editor snapshots now wait for the original sequence. The notebook
add snapshot is compared, without masks or pixel tolerance, within its recorded
post-drop game-tick interval; that old snapshot catches a live preview. Its
interval comes from the original RAM snapshots, and the match tick is reported.
This is frame membership, not an exact-time claim. The whole ordinary-input
notebook journey independently preserves all 14 final checkpoint comparisons.

The desktop/touch journey wait conditions now include pending presentations,
token motion and previews. They deliberately disable animation frames and
must advance those sequences themselves. The old failed batch is retained.

`verify_theater_audio_events.py` adds the complete theater RGB/state/observed
sound-source comparison to the regression suite. The optional presentation
audit in `verify_theater_native_journey.py` separately reports every original
display represented or missing within each input interval, including partial
redraws. It does not hide those gaps behind passing endpoint checks.

## Delivered status and remaining work

Delivered `c6f3a650aaaadfff02e787cf202a959ff6e25f8568c1a5da561fffd6f9437c55`. All 81 suites pass in
one complete batch, plus 183 environment states. All 23 additional native/strict
reports completed without execution errors and retain their known failures.
Backups and the served-file hash proof are in `theater-presentation-delivery-a`.

The full presentation diagnostic represents 309 of 580 interval-local
unique original images (baseline 201). No images are masked or tolerated;
missing displays remain explicit. This is unshifted input-interval membership,
not exact presentation timing or a percentage of game completion. Candidate G
also delays sentence repaint until its token/stage presentation commits.

Full audio waveforms, absolute native event timing, repeated-source start
completeness and all strict presentation gaps remain open. The complete-clone
gate remains failed.
