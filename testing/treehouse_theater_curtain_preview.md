# Theater curtain and preview presentation

## Observed defects and original behavior

The served `09b8bf3819b34` build matches 348/580 original theater images in the
continuous input-driven journey. All 29 endpoint images and gameplay states
match, but some complete intermediate screens are missing.

Pixel diagnostics identified these implementation errors:

1. Small action previews leave the normal cursor visible. Overlay 4 `1F0C`
   calls resident `415F` at `1F8F`, the same wrapper as full actor animation.
   That wrapper hides the pointer during script execution and shows it again
   afterward. Preparation's separate busy-cursor interval is not yet modeled.
2. Starting the editor removes the options immediately. The original closes
   the curtains over the options, replaces the scene, opens the curtains, then
   draws the editor's director.
3. Moving curtains appear behind rail controls in the browser. The original
   `158F`/`16AD` prepare the stage and overlay each curtain image. Both routines
   select CURS1 while moving and restore CURS0 afterward.
4. Each movement stage repaints the action card (`14E0` calling `1E76`) and,
   for regular scene changes, the director (`2453`). The director restore uses
   a background captured after the fully open curtain draw (`143E..145C`),
   rather than simply painting a transparent director over moving curtains.

The runtime now implements those presentation states from original resources
and rectangles. It adds no captured frames or fixed delays. Curtain stages
retain their original eight-tick waits. Stopping presentation clears all new
flags, including interruptions from readable controls.

## Verification

- The first cursor-only candidate restores seven complete original preview
  images without losing any previous native image match.
- The combined curtain/options candidate restores another seven complete
  images. Intermediate candidates retain all 29 endpoint images, gameplay and
  random states, and all 73 observed original sound sources/rates.
- `verify_theater_presentation_controls.py` checks 57 fresh mouse/touch
  conditions: all eight action previews per session, actual pointer movement
  and full RGB cursor visibility on desktop, editor entry, option interruption,
  and leaving during a curtain change. Candidate C passes all 57; the delivered
  baseline fails 32. The first checker tested a place change before its token
  had arrived; it now advances the actual token sequence before checking the
  following curtain phase. The failed attempt is retained.
- Thirty-seven restored original images are now explicit fixtures, checked by the
  existing shuffle/presentation suite alongside its 35 required shuffle images.
- Nearest-image diagnostics only locate defects. Acceptance still requires
  complete RGB equality with no masks, tolerances or replacement screenshots.

The final candidate restores 37 images overall: theater entry +2, editor +5,
small action preview +7, first place/time selection +4 each, beach/storm/jungle
changes +4 each, and room return +3. It matches 385/580 observed native images
without losing a previous match. All 29 endpoint/gameplay checks and 73 observed
sound sources/rates pass. Candidate D's broad batch was deliberately stopped
when superseded by E; its incomplete results are not acceptance evidence.

Current final candidate: `50db501cceb7b595f169978c2660d91e6346540992d7f20d2d85bb5d2e462542`
in `testing/output/treehouse/theater-curtain-candidate-e/index.html`.
Its full journey, all 95 regression suites and 183 environment states pass.
This candidate is now the served build. Partial redraws, preparation delays,
exact presentation timestamps and whole-journey waveforms remain open.

The cross-activity tour retains the same 23/27 exact images and identical
gameplay/object states and input schedules. Its first matching theater entrance
image moves from browser tick 4142 to 4150: the busy cursor now remains until
the final curtain wait completes. Both timestamps remain in the reports; this
is not equal-input-latency evidence. The initial delivery guard compared those
timestamps as well as image results and rejected the promotion before any live
file changed. The revised guard explicitly records this single difference and
still requires all image/state outcomes and inputs to remain identical.


## Delivery (2026-09-29)

Delivered `50db501cceb7b595f169978c2660d91e6346540992d7f20d2d85bb5d2e462542`. All 95 regression suites and 183 environment states pass. Theater small previews now hide the cursor; curtains preserve the prior stage/options, cover the rail, use the busy cursor and restore the director background. All 57 fresh mouse/touch checks pass; the previous build fails 32. Exact native theater image membership improves from 348/580 to 385/580, restoring 37 complete images without losing a previous match. All 29 endpoint/gameplay checkpoints and 73 observed sound sources/rates pass. The remaining 195 theater images and exact timing remain open. Strict nature remains 614/984 callbacks with 12 missing displays; the cross-activity tour retains 23/27 images and ten balloon-state differences. Money-loss RNG, resource lifetimes and whole-session audio/timing remain unresolved; full fidelity is not established. The served HTTP hash matches; prior live and verification files are backed up.
