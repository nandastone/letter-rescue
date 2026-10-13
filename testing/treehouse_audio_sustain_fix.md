# Sustained instrument playback rate

## Scope

This comparison uses ordinary original-game controls to select instruments,
play short/sustained notes, and release them. It measures the production browser
audio graph against the pinned original capture backend. It does not attempt
CPU instruction equivalence or use recorded native audio in the game.

## Reproduced difference

The browser already rounds a requested sample rate through the original sound
driver's hardware divisor. The pinned reference mixer additionally advances its
source cursor in 14 fractional bits at 48 kHz. Omitting this second rounding
causes increasing phase drift during sustained notes, despite close attacks.

For example, Bass A requests 11000 Hz, the hardware divisor produces 11111 Hz,
and the reference mixer advances by floor(11111 * 16384 / 48000) = 3792 units.
Its effective rate is 11109.375 Hz. The browser previously rendered 11111 Hz.

The baseline, controlled rate-only probe, and production fix each render real
`playPitch`/`OriginalAudio` nodes in an OfflineAudioContext at 48 kHz. One
attack alignment is retained for all later windows; there is no per-window
realignment or gain scaling.

| Instrument, A note | Baseline correlation at 2 s | Corrected correlation at 2 s |
| --- | ---: | ---: |
| Bass | 0.9469 | approximately 1.0000 |
| Piano | 0.7069 | 0.9922 |
| Clarinet | 0.2991 | 0.9994 |

These measurements establish waveform drift and its cause. They are not a
subjective listening test or a claim that the small pitch difference is audible.

## Runtime correction

`OriginalAudio.renderRate` applies the reference mixer's rate quantization when
setting a source's playback rate. The original hardware rate remains available
as `voice.rate`; actual rendering uses `voice.renderRate`. Graceful-release
loop/tail calculations use the rendering rate consistently. The game's piano,
editor and song paths retain their original forced-stop semantics.

## Capture and regression

- `capture_instrument_audio.py` selects instruments through the original family
  menus and captures short A, sustained A and high E notes. It records driver
  activity, headers, release flags, input/audio positions, and pinned hashes.
- `instrument-audio-native-a/b` repeat the initial four-instrument, twelve-note
  route exactly in driver observations, callback timeline and audio. See
  `instrument-audio-native-repeat.json`.
- `instrument-audio-native-all-a` stops when an overlapping portrait click
  selects Flute instead of instrument 12. The corrected capture chooses points
  unique to each portrait's original hit rectangle. This was a driver error;
  no game input behavior was changed for it.
- `instrument-audio-native-all-b` captures all 42 instrument/family choices,
  three cases each, through normal input. This broader run is separate from the
  repeated four-instrument control.
- `instrument-audio-compare-a`, `instrument-audio-rate-probe-a`, and
  `instrument-audio-fixed-a` retain the baseline, rate-only experiment, and
  corrected production output.
- `verify_audio_sustain.py` fails on the old build and passes all 56 checks on
  the candidate. It covers original sample/loop metadata, effective rate, and
  the twelve-note waveform windows at correlation >0.99 and gain within 5%.

Candidate SHA:
`1dde9b9a90a5dcf09649a52e549fd71ced7775158e1de7ecc9fb6217a780f2f3`.

## Remaining fidelity

Browser resampling differs from the reference's linear interpolation, and
forced buffer stop still lacks the reference mixer's short stateful DC decay.
Full waveforms, complete stop/replacement transitions, timing and other output
paths remain open. Diagnostic all-instrument comparisons preserve their actual
measurements without turning the focused regression threshold into a full-game
audio acceptance claim.

## All-instrument diagnostic result

`instrument-audio-all-baseline-a` and `instrument-audio-all-fixed-a` both render
all 126 native cases. `instrument-audio-all-summary-a.json` verifies all rates,
sample lengths and loop metadata. Across 257 non-silent waveform windows, the
median later-window correlation improves from 0.91173 to 0.99976. Windows below
0.99 fall from 129 to three: Balloon (instrument 39), short/long attack and its
0.5-second sustained window. Their correlations remain about 0.9873–0.9884.
Those failures are retained; the diagnostic does not claim full waveform parity.

## Delivery

`audio-rate-regression-a` passes all 63 registered suites together;
`audio-rate-environment-a` passes all 183 environment image states.
`audio-rate-delivery-a` preserves the previous build/report and confirms the
served file matches the candidate SHA. The all-instrument diagnostic is
included in completion verification with full waveform parity false.
