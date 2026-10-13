# Maze drawer sound preparation

## Player-visible change

Opening and closing the song chooser for the first time now allow the original
compressed sound decoder's work to finish before starting the sound and drawer
movement. The previous complete screen remains visible during preparation.
Subsequent uses of a prepared sound start immediately. Canvas clicks cannot
skip preparation. Melody tempo is unchanged.

The candidate is `09b8bf3819b343109cf09fd6b2848a87b91bbfefe35454294551e602e344724f`.
Delivered after all 94 regression suites and 183 environment states passed.
Previous live files are backed up, and the served HTTP SHA matches the candidate.

## Implementation and evidence

`sound.py` computes intrinsic decoder work while reading the original compressed
bitstream. The builder stores that work alongside the decoded PCM. The browser
converts work to game ticks using the pinned reference platform's 10,000 cycles
per millisecond. There are no sound-specific measured delay constants.

`OriginalAudio.prepareDecoder()` tracks previously prepared sounds. The maze
drawer yields the preparation work before changing its image or starting audio.
The offline native-journey adapter imports prepared sound identities from the
single initial native snapshot; those snapshots are never product runtime data.

- All 273 compressed assets agree with the independent JavaScript implementation
  in PCM, consumed bytes and intrinsic work (`sound-decoder-cost-c/report.json`).
- Fresh desktop and touch journeys pass 36 checks, including input during cold
  preparation, warm reuse and preserved earned notes
  (`maze-cold-sound-input-b/report.json`).
- The previous live build fails 18 checks under the same harness
  (`maze-cold-sound-baseline-a/report.json`).
- The complete original-scheduled maze journey retains all 11 RGB/gameplay
  checkpoints and all 184 observed original sound sources/rates
  (`maze-cold-sound-journey-a/report.json`).
- The final song starts 13 ticks early rather than 23; one observation is 14
  ticks early. The maximum early offset elsewhere remains 25 ticks. The exact
  timing report remains failed (`maze-cold-sound-journey-a/dispatch-timing.json`).

All report paths above are under `testing/output/treehouse/`. The A and B
candidate builds are byte-identical.

## Explicit remaining gaps

This is decoder work only. Original file reads, allocations, checksum work,
interrupt work, fractional CPU phase and scene drawing are not included in this
wait. The prepared set does not yet implement original resource eviction.
Other audio paths register prepared sounds but do not yet consume their decoder
work. Full resource lifetimes, full event timing and unaligned audio comparisons
remain open. This change does not establish full maze or whole-game parity.
