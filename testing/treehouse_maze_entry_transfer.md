# Piano and maze transfer

The previous turn delivered the automatic-hint click correction in
`032490fa50b5`. This pass found a separate missing player-visible sequence:
the original piano portrait disappears in smoke, the child descends into the
bucket, and the maze starts. Returning reverses the bucket movement and restores
the portrait in smoke. The browser previously switched screens immediately.

## Original resources and implementation

Overlay1 0DE2–0E69 calls the smoke routine 4E3A and the selected character's
scripts 20300 (enter bucket) and 20301 (return). The smoke uses MODULES palette
2380, shapes 2381–2388, eight ticks per frame, and original position pairs at
music data offset 084B. At smoke frame four the portrait is removed or restored.
The returning child's last bucket frame remains visible for the first four
smoke frames. Candidate A initially omitted that retained child; eight frame
comparisons exposed the omission and candidate B corrects it.

`MazeTransition` uses these resources through the existing renderer and
animation interpreter. It participates in the existing room-travel busy state,
so canvas, readable buttons and keyboard navigation share the sequence. Music
timers wait until the transfer completes. Direct snapshot initialization remains
available to existing comparison fixtures through `setScene`.

Candidate B: `57b4673bf421a0deaf06ba9a624607e650edd38576f1abba84ee71947c923917`.

## Paired journeys

`capture_maze_entry.py` starts from the pinned original piano snapshot, then
uses ordinary inputs for first entry, tutorial, return to piano, second entry,
an interrupting click and final return. A second route skips the first tutorial.
The `maze-entry-control-a` / `maze-entry-audio-a` pair and corresponding
`maze-entry-skip-*` pair have identical images, full WAV, callback timeline,
actions and checkpoint states with and without read-only sound observation.

`verify_maze_entry.py` initializes the browser once from that piano state.
All later pointer actions and waits come from the recording. It records full
RGB images, gameplay/random state and source/rate sound dispatch. No per-step
state installation or clock alignment is used.

In `maze-transfer-frames-b`, all 62 generated transfer compositions occur in
the original recording. The separate transfer regression checks their order.
Candidate A has 54/62 because its returning child vanished too early. The old
build generates neither the smoke nor bucket transfer.

The completed tutorial, return, interrupted reentry and final piano match
image and gameplay/random state. The full route's observed 18 original sound
sources/rates match between inputs, including four formerly missing smoke
sounds. The skipped route matches its 13 observations. This is source coverage,
not full rendered waveform or exact event-time parity.

`verify_maze_transfer_output.py` presses the visible maze-entry control and
renders the production mixer. Candidate B matches all 70,449 samples of the
original smoke cue and decay after one bounded start alignment, with no gain
fitting. The old build is silent. Reports: `maze-transfer-smoke-output-b` and
`maze-transfer-smoke-baseline-a`. Absolute input latency and the complete
journey waveform remain separate requirements.

## Retained fidelity gaps

The full original entrance comparison still fails: one intermediate busy-cursor
image differs, and two intermediate checkpoints observe the random stream on
opposite sides of a voice choice. Stable states subsequently agree. Raw
per-checkpoint sound misses also remain; all observed sounds occur within their
corresponding player-input intervals. Full timing has not been waived.

The transfer regression reports its narrower scope and retains both complete
entrance reports with their failures. The full-game completion gate remains open.
Candidate B's full route matches 45/46 checkpoint images and 44/46 random/state
checkpoints, up from 21/46 images and 36/46 state checkpoints in the old build.
The 129-pixel mismatch is confined to the pointer at intro-15. The remaining
state-timing differences are intro-05 and intro-25. They are recorded under
`maze-first-entry-presentation` in the ledger.

## Input regression

Existing accelerated browser journeys now advance the restored transfer before
pressing the maze's Skip introduction button. They retain their previous
assertions and do not install new game state. Five exit/reload routes pass all
41 checks; fresh desktop/touch automatic-hint input passes all eight checks.
85 suites pass on identical candidate HTML: 84 from the full batch plus the journey rerun after waiting for the restored return animation. The failed batch is preserved; this is not a second complete batch. Original transfer frame order and entrance/exit/skip journeys pass. All 183 environment states pass; 23 additional reports retain prior outcomes. Full entrance reports retain their cursor and intermediate RNG timing failures alongside all previous strict/native failures.

Delivered as `57b4673bf421a0deaf06ba9a624607e650edd38576f1abba84ee71947c923917`; backups and served HTTP hash verified. See `testing/output/treehouse/maze-transfer-delivery-b/report.json`.
