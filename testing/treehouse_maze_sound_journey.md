# Maze automatic-hint input and sound journey

## Player-visible defect

The original accepts a sign press that interrupts its automatic sound reminder.
The browser stopped the reminder and consumed the press. In the paired route,
the sixth correct sign was consequently lost, leaving the player one puzzle
behind and preventing the recorded journey from reaching victory.

The original source returns from automatic audition at overlay1 58F1 to its
main input loop at 524A. The native route confirms that its interrupting press
also starts the chosen sign's feedback and audition. Candidate
`032490fa50b5a1e7141a3910f30d3e6a934fecfb91776c76ffc534bc0d0e3e8b`
tracks the automatic audition's lifetime and completes that generator before
dispatching the same canvas press. Cancellation clears the flag. Manual replay,
tutorial and movement retain their existing interruption rules.

## Original recording and browser replay

`capture_maze_audio_journey.py` starts from the pinned original settled maze
snapshot, makes one wrong choice, then eight correct choices, and lets the
victory song complete. Sound observation reads the active original PCM source
at the established video callback. It does not modify the original game.

`maze-audio-control-b` and `maze-audio-native-b` have identical actions,
checkpoint states, all eleven PNGs, full captured WAV and callback timeline.
The first capture attempt (`*-a`) retained a stale pre-restore frontend image
at its initial checkpoint. Attempt B waits for fresh video before that capture;
the original failed browser reports remain available.

`native_input_schedule.py` derives press/release and checkpoint intervals from
the actual native callback ticks. The browser starts from one original model
snapshot and receives actual canvas inputs. It does not reset model state
between choices or extend waits until animations settle.

Baseline `maze-audio-browser-control-b` matches through correct-4 and then
diverges. Candidate `maze-audio-browser-fixed-a` matches all eleven full RGB
checkpoint images (membership within their input intervals) and all compared
gameplay/random state, ending at completed victory. These are not exact
presentation-timestamp results.

## Sound evidence and retained differences

`maze-audio-input-comparison-a` matches all 184 observed original sound
sources/rates in order between player inputs. There are 197 browser starts;
the 13 unmatched starts remain in the report. Adjacent same-source native
restarts may not be visible to the observer, so this is not event-count parity.

The final victory screenshot introduces no new input. Its song is compared
across the complete preceding input interval, while the raw checkpoint splits
are also retained. The browser starts that song early: three notes cross the
checkpoint boundary early, and the raw split comparison has ten unmatched
native observations. This timing difference has not been waived or fixed.
`maze-audio-comparison-fixed-a` preserves the failed split comparison.

Whole rendered waveforms, exact sound timing, fresh original entry and
cross-activity continuity remain open. This audit adds source coverage and
fixes a concrete input defect; it does not establish complete maze fidelity.

## Regression and delivery

`verify_maze_audio_events.py` preserves the full paired route as regression
coverage. `verify_maze_hint_input.py` additionally enters a fresh game through
ordinary controls on desktop and touch, waits for its automatic hint, and
presses the correct canvas sign once. It checks immediate sign feedback and
exactly one earned note. All 84 suites pass in one immutable-build batch, including a paired original-scheduled maze journey and fresh desktop/touch hint input. All 183 environment states pass; 23 additional reports retain their prior outcomes. Known strict/native failures remain.

Delivered as `032490fa50b5a1e7141a3910f30d3e6a934fecfb91776c76ffc534bc0d0e3e8b`; served HTTP hash and backups verified. Delivery report: `testing/output/treehouse/maze-hint-delivery-a/report.json`.

The focused baseline fails both sign-feedback and earned-note checks on desktop
and touch; the candidate passes all eight checks. Reports are
`maze-hint-input-baseline-a` and `maze-hint-input-fixed-a`. The cause was a shared
busy-state branch treating an automatic reminder like user-requested playback.
Earlier journeys waited for all animation to settle before clicking, so they
could not expose this interaction. The recorded-input and fresh idle-timer
checks now exercise it without installing a busy state.
