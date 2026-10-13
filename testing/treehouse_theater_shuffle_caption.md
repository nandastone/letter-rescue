# Theater sentence repaint during token swaps

## Visible defect

The original keeps the sentence caption unchanged until both tokens finish a
swap. The clone repainted it after the first token moved, while the second was
still travelling. This affects both Shuffle and manual token dragging.

The current-build baseline is `theater-current-presentation-b/report.json`,
build `2d29766c93dd`. Its ordinary-input original journey matches all 29 endpoint
images and gameplay/random states, but only 309/580 intermediate native images.
The Shuffle interval matches 33/82. A nearest-frame diagnostic finds 35 missing
original images with an identical stage and differences confined to the caption.
That diagnostic locates the cause; it does not relax acceptance or mask pixels.

## Original behavior and implementation

Pinned original overlay 4 `0F88..1004` moves the first token, then the second,
swaps the category-order entries and calls the sentence repaint routine. The
manual drag path swaps entries earlier (`3F44..3F5B`) but likewise waits for the
other token's movement before repainting the caption (`3FB8..3FD8`).

The browser now retains the caption's prior order while `swapTokens` moves the
tokens, then clears that presentation state after the second movement. Stopping
theater presentation also clears it. Sentence data, token placement, the random
stream and sound dispatch are unchanged. No original screenshot or recorded
timing schedule is used by the runtime.

## Verification

Candidate `fe0819316c49aeff41b013108debd70cf1ec7659e4ef49894edcb7d4698b8434`:

- `theater-caption-baseline-a`: all 35 required full-image shuffle checks fail
  on the previous build.
- `theater-caption-proof-a`: all 35 pass over all RGB pixels, without masks,
  tolerances or frame substitution. All 29 original endpoint images and
  gameplay/random states also pass.
- `theater-caption-fixed-a`: Shuffle improves from 33/82 to 68/82 represented
  original images; manual dragging improves from 4/11 to 8/11. Overall original
  image membership improves from 309/580 to 348/580. This is input-interval
  membership, not exact timestamp parity or a percentage of game completion.
- `theater-caption-sound-a`: the observed native sound sequence still passes.

`verify_theater_shuffle.py` registers the 35 complete-frame requirements as the
88th suite. The fixture identifies original reference frames and is used only by
verification. Optional presentation audits now save generated frames and their
hashes for direct comparison. The full 88-suite regression passed. Delivered `fe0819316c49aeff41b013108debd70cf1ec7659e4ef49894edcb7d4698b8434`; the served HTTP hash matches and the previous files are backed up in `theater-caption-delivery-a`.

The 232 remaining intermediate image differences, strict nature timing, complete
audio waveform comparisons and other recorded integration requirements remain
open. The complete-clone gate has not been changed.


All 183 environment states also pass on the candidate. Strict nature remains at 614/984 callbacks and 12 missing displays. No previously matching native theater image was lost. The sound comparison retains all 73 observed sources/rates.
