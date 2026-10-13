# Browser output level correction

The production Web Audio graph attenuated every digital sound by 0.4. The
pinned original's Bass A-note capture has approximately unity digital gain.
Existing native research established that difference; this pass measures the
actual browser graph and removes the extra attenuation.

## Measurement

`tools/treehouse/verify_audio_output.py` loads the immutable browser build and
renders its real `playPitch(9,11)` / `OriginalAudio` nodes in an
`OfflineAudioContext` at 48 kHz. The readiness guard sees a running context while
the graph is scheduled before offline rendering; buffer decoding, playback
rate, looping, gain and scheduled stop are production code.

The first 100 ms are compared with both short and long original Bass A-note
captures. Normalized correlation selects the recording offset within a bounded
2,000-sample window. Neither signal is amplitude-normalized for the level test.
This separates capture latency from the amplitude defect; it does not verify
input-to-sound timing. Native input event offsets come from `driver.json`.

| Measurement | Previous build | Corrected candidate |
|---|---:|---:|
| Browser level relative to native | 0.399959 | 0.999898 |
| Attack correlation | 0.999972 | 0.999972 |
| Unscaled residual RMS, signed 16-bit units | 3138.49 | 39.11 |
| Effective sample rate | 11111 Hz | 11111 Hz |

Both native branches produce these results. The graph also becomes silent
after its explicitly scheduled forced stop. The amplitude pass criterion is
within 5% of native and attack correlation above 0.99. These are bounded
audio-level checks, not exact waveform acceptance. The existing strict visual
timing gate is unchanged.

## Evidence and limits

- Baseline: `output/treehouse/audio-output-baseline-a/report.json` fails both
  attack-level checks on `805cd0adac74`.
- Correction: `output/treehouse/audio-output-fixed-a/report.json` passes all
  four checks on `4b59ef60e033`.
- Both directories retain the actual rendered browser PCM as `browser.wav`.
- Reference: `output/treehouse/research-audio-note-c/state/audio.wav`, SHA-256
  `b45384669e7fe1400ddfb0fc04b7392a9d732e1ec89ce33729253c392e4eeef1`.
- Native provenance and earlier rate/stop analysis:
  `treehouse_audio_note_completion_research.md`.

The shared production gain is now 1. Browser/OS volume still controls listening
volume. This fix does not claim that every sound's full waveform is exact.
Browser resampling differs from the reference mixer, and original stop decay,
long-note loop phase, all instruments, speech/effects and gameplay sound timing
remain to compare. No native audio recording is used for runtime playback.

## Delivery

Candidate `4b59ef60e033` is now the live build. All 47 regression suites and
183 environment reference states pass. Strict nature timing remains 614/984
with 12 unrepresented native display changes. The served HTML hash matches the
verified candidate. Evidence: `output/treehouse/audio-output-regression-a/report.json`
and `output/treehouse/audio-output-delivery-a/report.json`.
