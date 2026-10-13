# Nature editing and guessing-game sound audit

## Player-visible defect

The delivered theater build `c6f3a650aaaa` omitted 15 observed sounds during
ordinary collage editing: animal selection, fact dismissal, clear prompts,
filter/category changes, and switching between day and night. The editing
handlers did not call the existing sound output callback. Removal and erase
effects already played correctly.

The correction uses the original resource 1008 for the observed control clicks
and resource 1042 for day/night changes. Selection of a value shares the
attribute handler, so it produces one cue. Disabled categories and edits during
an erase animation remain guarded before sound dispatch. No new timing model
or CPU simulation is introduced.

## Reference and reproduction

`capture_nature_audio_journey.py` observes active digital sources at the existing
safe native video callback. It replays the existing ordinary editing and quiz
captures without changing their input or native memory. The observer can miss
same-source restarts between callbacks; source coverage is not a complete event
count or whole-waveform claim.

The instrumented captures are `nature-edit-audio-native-a` and
`nature-quiz-audio-native-a`. Their uninstrumented controls are respectively
`nature-edit-native-a` and `nature-native-journey-c`. The comparator requires
identical complete recorded audio, video callback timeline, saved images,
actions and checkpoints. Both controls pass.

Baseline evidence:

- `nature-edit-audio-baseline-a/report.json`: 15 missing of 17 observed sources.
- `nature-quiz-audio-baseline-a/report.json`: all 57 observed sources present.

Browser observation wraps the production start/stop methods while preserving
their arguments, results and output path. Matching requires decoded PCM identity,
hardware playback rate and order within each input interval. Adjacent native
cues separated by more than two ticks cannot be matched to a same-tick browser
replacement without failing the audit.

The editing comparison has no unmatched browser starts. The quiz comparison
has eight unmatched browser starts (clicks and guessing hints), retained in its
report for follow-up. The callback observer cannot establish whether each is
an extra browser sound or a native event missed between observations. They are
not silently accepted as proof of full sound parity.

## Candidate verification

Candidate `a44564be50d4bbc7c18bae9195eedb77f9d2f56db08b50645ad7e1af722d7342`
passes `nature-feedback-check-a/report.json`: all 17 editing and 57 quiz
observed sources occur in order at the original rates, with no flagged same-tick
replacement. All 21 editing and 14 quiz/prize/room-return full RGB checkpoint
comparisons and active gameplay states pass.

The separate `verify_nature_feedback_output.py` drives visible animal selection
and day/night controls through the production mixer. Both controls are silent
on the old build (`nature-feedback-output-baseline-a`). On the candidate,
their first 2,000 and 12,000 output samples respectively match the original
recording after one bounded alignment per cue, with no gain fit
(`nature-feedback-output-fixed-a`). This confirms audible output as well as
dispatch. It does not establish input latency or entire-waveform parity.

`verify_nature_audio_events.py` is registered in the integrated regression
runner. Full event timing, repeated-source completeness, entire rendered audio
and intermediate image timing remain open. The existing strict nature failures
are retained. Delivered as the served build after all 82 suites passed in one complete
batch and all 183 environment states passed. All 23 additional comparisons
retain their prior pass/fail outcomes without execution errors. The prior live
files are backed up in `nature-feedback-delivery-a`; the HTTP hash matches.
The strict completion gate remains required and full parity remains false.

Post-delivery `completion-gate-bk.json` confirms the served build and all 82
regression results, while failing completion for the retained native journey,
strict timing, audio and integration requirements. The overall goal remains
active.
