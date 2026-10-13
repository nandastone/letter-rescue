# Original digital audio in the playable browser build

Delivered `b0b73bf1f6f0cd7720d9f7b28cedaafa364cb543f117038cc557c14254deb4de`. All 80 registered suites pass in one
complete immutable-build batch, plus all 183 environment states. Previous live
files are backed up in `audio-mixer-delivery-a`; the served HTTP hash matches.
This work fixes the actual sound renderer and input lifecycle. Full fidelity
remains unproven.

## Runtime changes

`treehouse-demo/audio-mixer.js` implements the single original digital channel
in an AudioWorklet. It consumes decoded original SND samples, pitch rates and
loop bounds. It uses the pinned reference mixer's 14-bit linear interpolation
and four signed-16-unit steps toward silence. The reference implementation is
`testing/output/treehouse/capture-core/src/hardware/mixer.cpp` (`AddSamples`
and `AddSilence`). No captured waveform or reference event schedule is runtime
input. Replacement voices retain the channel's interpolation state.

`OriginalAudio` in `treehouse-demo/app.js` queues start, stop and release commands
with their requested sample times and ownership IDs. Worklet initialization
runs independently of game input. A note released before initialization
completes remains cancelled. Releasing an older key cannot stop its replacement.
The self-contained HTML includes the worklet through a data URL, supporting
both local files and the HTTP demo. The rendering context is 48 kHz; conversion
by the browser or output device is outside the measured renderer.

## Evidence and its limits

- `audio-stop-baseline-a/report.json`: the previously delivered renderer fails
  all three nonzero stop-tail cases because it cuts immediately to zero.
- `audio-stop-fixed-b/report.json`: actual production playback follows the
  native observed four-unit decay at three different stop phases. These checks
  prove the decay law, not the absolute timing of a native key release.
- `audio-mixer-all-b/report.json`: 126 note cases across all 42 instruments;
  all 336 measured waveform windows are sample-exact. There is one attack
  alignment per note, no gain fitting and no independent alignment per window.
  The previously mismatching Balloon windows now match. Windows are not a
  claim of complete unaligned waveform or whole-game audio parity.
- `audio-mixer-output-b/report.json`: both measured Bass attacks match exactly,
  with unit gain. The forced-stop assertion now allows the demonstrated native
  decay before requiring silence; it formerly required an immediate cut.
- `audio-mixer-lifecycle-d3/report.json`: 18 checks on actual keyboard, sound
  toggle and focus handlers, with a real AudioContext and analyser, pass across
  standalone-file and HTTP origins. Includes deliberately delayed module
  loading, cancellation before readiness, replacement ownership and silence.

The full regression incorporates `audio_instruments`, `audio_stop` and
`audio_mixer_lifecycle` alongside the existing audio and gameplay suites.
Fresh results for the exact delivered HTML are required before promotion.

## Regressions found during this work

Candidate C waited for module loading inside `unlock()`. Its complete 79-suite
batch exposed missed first clicks and keys in six suites. That failed batch is
preserved in `audio-mixer-regression-c/report.json`. Candidate D initializes in
the background and queues commands, including cancellation. Its focused demo,
music editor and delayed-initialization lifecycle checks pass. A full 80-suite
run is required; focused passes do not replace that run.

Offline rendering needs an explicit message-port barrier before rendering
starts, otherwise the offline context can finish before all commands arrive.
`flushCommands()` supplies that barrier. An earlier lifecycle fixture also used
animation-frame polling while deliberately disabling animation frames; it now
uses explicit 20 ms polling. Historical failed reports are retained.

## Remaining audio work

Whole-journey native audio comparison remains open: speech and effects, sound
replacement during actual gameplay, absolute start/stop timing and complete
waveforms without attack alignment. The audio ledger remains in progress.
Other known gameplay, image and timing failures are retained when promoting
this sound improvement. Neither the instrument-window count nor the regression
suite count is a percentage of game completion.

## Integrated delivery evidence

`audio-mixer-regression-d/report.json` contains all 80 passing suites, including
the fresh instrument, stop and lifecycle results for the delivered build.
`audio-mixer-comparisons-d.json` records 23 additional reports with no execution
errors. Full money loss, chip partial clearing, yard/egg balloon timing, nut
phase, held-worm pixels and strict nature presentation remain failed. These
reports are retained in `testing/treehouse/completion_verification.json`.
The previous candidate C failures remain available and are not aggregated
into the passing D batch.
