# Eighth parity pass: drawing time and level-two verification

The recap now returns on the native input frame in the regression route. All
369 post-recap completed states still agree, and the later admission difference
has fallen from approximately ten video frames to **at most one**. This remains
a measured timing approximation, not cycle-exact emulation.

## Cause and correction

The new real-engine test first failed with `5941 != 5951` in about three seconds.
It retains the causal walk/jump/matching input prefix and stops immediately
after the recap. The same test now passes without changing its target frame.

Native instruction-boundary observations show that the game resets its timer
after drawing and waits for a number of PIT interrupt edges. Our recap model
previously added only the explicit waits. Picture transfers take long enough
to cross interrupt edges; ignoring that work advanced subsequent gameplay.

Additional read-only trace hooks measure work after a wait and before the next
reset. They preserve the original replay's instruction states and timestamps:
the checked pre-recap prefix had 4,568 matching observations and zero differences.

`tools/prepare_wr1_recap_timing.py` extracts the work profile from native routine
boundaries. `data/wr1/recap_work.json` contains only aggregate work estimates,
their ranges, and provenance. It contains no input-frame offsets, word-specific
delays, future state values, or update schedule. The 187 individual observations
are retained separately in the test-only `wr1_recap_work.json` fixture.

| Work region | Samples | Median | Observed range |
| --- | --- | --- | --- |
| Helper drawing | 33 | 2.551 ms | 2.549–2.904 ms |
| Helper with picture/word panel | 7 | 3.290 ms | 3.288–3.290 ms |
| Picture transfer and panel save | 7 | 27.122 ms | 27.104–28.002 ms |
| Dissolve drawing | 140 | 4.351 ms | 4.120–4.367 ms |

These measurements apply to the fixed **27,000 DOSBox cycles/ms** configuration.
The model now advances a drawing-work phase, waits for the requested number of
interrupt edges after each reset, and passes the remaining timer phase back to
gameplay. It preserves all 180 renders and 11,200 random calls. Additional
60/70/120 Hz model checks verify that changing host frame rate preserves the
render count and keeps duration within two IRQs of this native sample.

The approximation has a known limit: six native transfers crossed two extra
IRQ edges, while one crossed three. A single median workload does not reproduce
every such variation. Partial pixel-by-pixel transfers also still appear as one
completed blit. We therefore retain explicit timing residuals rather than
claiming every cutscene instant is exact.

## Gameplay and reset results

- First post-recap update: **native and clone source frame 5951**.
- Post-recap state/input comparison: **369/369 exact completed states** and
  matching held inputs. **156/369** admissions also enter on the exact native
  video frame. The other 213 differ by one frame; their tick identities are
  recorded in a test-only residual fixture.
- All three prior recap screenshots still match every RGB pixel after the
  timing change.
- The extended exit route now agrees on **838/838 completed states**, compared
  with 768/838 before this pass. This includes both the timing correction and
  retaining the last word index when resetting the puzzle. Native reset clears
  the active flag but leaves `DS:032e` unchanged.
- The maintained exit fixture covers the **77 updates after the recap**,
  including the transition and first level-two updates. The new native trace
  additionally verifies words, word cursor, drips, level/door/recap flags, and
  whether slime has ever successfully hit an enemy. The comparator now checks
  those fields whenever the native fixture supplies them.

The next map still starts its gameplay updates seven or eight video frames
early: the original loader takes approximately **112.29 ms** in this sample,
where the clone loads synchronously. The door-completion update itself enters
and finishes at matching frontend counters. Loader time is a separate remaining
issue; it was not folded into the recap workload or hidden with a fixed pause.

## Level-two pixels

At **native counter 6500 / clone input source frame 6499**, the complete 320×200
level-two screen has **0/64,000 differing pixels**. This covers the new map,
spawn doorway/player, score 740, `ant` mystery word, question blocks, and HUD
reset. Adjacent screenshots are identical in this stationary scene, so this
result verifies rendering but does not establish loader timing parity.

`wr1_level2_pixels.json` records the native PNG hash and frame convention. The
Python test replays the actual Godot renderer and compares every RGB byte.

## Evidence and checks

Native evidence uses the same executable, emulator revision, controlled
savestate, and unmodified input stream described in the seventh report. The
new trace extension and its decoder patch are checked in. Native work trace:
`203ae48a8504810156fc7dde62a759c6e523333f9a936d5c8ca6b0e8ca85d666`.
New level-two trace:
`d825a9cea8f038617fc552441941e6f7fc4a9f7498b223a3866c18b4949ce2d3`.

Validation commands are the existing Python discovery suite with `GODOT` set
and the twelve `testing/test_wr1_*.gd` suites. The new recap timing test and
level-two pixel test run as part of Python discovery. No frame shifting or
native future-state injection is used by the game.

Final result: **48 Python tests pass** (123.7 seconds), **all twelve Godot
suites pass**, and `git diff --check` passes. The recap model suite now includes
3,435 checks.

Subsequent coverage should exercise moving on level two, native medium/hard
drip impacts, and boy/ending behavior. Run the current build with
`just run-original`.

## Follow-up: exclude loading duration from gameplay parity

The user clarified that comparisons should synchronize at the first fully
rendered, playable level frame. Matching the original loading duration is
outside that scope. The seven-to-eight-frame loading offset above is therefore
an observation, not a gameplay defect to fix with a delay.

Additional observational loader and music-driver hooks found that music-driver
interrupt work contributes substantial, phase-dependent loading cost. No
loader delay was added to the runtime, and the experimental test requiring
the first level-two update on the original absolute video frame was removed.

The next comparison should establish one post-load initial state and clock
phase, schedule identical inputs relative to that boundary, and then compare
continuously without further synchronization or injecting later native states.
The initial check must include actors, RNG, animation phase, words and score
as well as the rendered pixels. A rendered loading screen is not sufficient:
the chosen boundary must also admit gameplay input.

A native level-two walk/jump trace is available in
`testing/output/wr1_level2_motion_native.jsonl`; the corresponding post-load
replay fixture remains to be prepared. Existing full-route results above retain
their original absolute-frame convention and have not been relabeled as a
post-load comparison.

Follow-up completed in [the ninth pass](wr1_ninth_slice.md): the visually
verified counter-6379 checkpoint, independent level-two replay, entrance
countdown fix, and focus-independent recorded movement are now implemented.
