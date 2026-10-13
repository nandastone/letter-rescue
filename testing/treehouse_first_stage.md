# The Treehouse: recovered original and replay baseline

**Follow-up:** a [playable browser demo](../treehouse-demo/README.md) was built
on 2026-09-27. This report records the earlier recovery milestone.

Date: 2026-09-25. Target: preserved DOS **Version 1.1**. The intended end result
is the complete game with an original presentation mode, followed by optional
readable text, input, and rendering improvements. This milestone supplies the
recovered data and repeatable reference; **a playable reconstruction is still
to be implemented**.

## Results

| Work | Observed result |
| --- | --- |
| Original acquisition | Preserved DOS archive obtained and hashed; executable identifies itself as Version 1.1 |
| Resource containers | All 10 DAT files parsed; 3,806 resources pass bounds and checksum validation |
| Graphics recovery | All 2,337 SHAP images decoded with exact compressed-byte consumption and output sizes |
| Static executable unpacking | 226,208-byte main image, 1,386 relocations, five appended overlays |
| Script recovery | All 356 SCR instruction streams framed; 195 PSL sound preload lists parsed |
| Independent parser fixtures | 10 tests passed |
| Original replay | Two fresh startup-to-interior runs agree on all 3,040 video callbacks, all 3,040 sampled original timer values, and recorded audio |

No original source release or existing complete Treehouse reconstruction was
found in the bounded public search. Generic older Mohawk archive code provided
useful structural evidence; game behavior is being recovered from this executable
and observed execution. See the [source assessment](treehouse_port_assessment.md).

The resource extractor preserves exact bytes. One original STRL list declares
25 entries but contains 24; that discrepancy is recorded, not silently repaired.
Successful script framing establishes instruction boundaries, not complete
knowledge of every opcode or activity rule.

## Repeatability evidence

The maintained route is [enter-treehouse.json](treehouse/routes/enter-treehouse.json).
It waits at the title/exterior, selects the boy, and reaches the treehouse interior.
Each run delivers 3,040 video callbacks, containing 190 unique images. Duplicate
images retain their own timeline entries. The comparison checks every callback,
with no frame shifts, similarity tolerance, or mismatch allowance.

Local evidence, relative to the repository root:

- `testing/output/treehouse/entry-verified-a/run.json`
- `testing/output/treehouse/entry-verified-b/run.json`
- `testing/output/treehouse/entry-verified-comparison.json`
- Each run's `frames.jsonl`, lossless images, recorded audio, and diagnostic snapshots

The stock core's input scheduling produced 196 differing frames in repeated entry
routes even though audio matched. A capture-specific DOSBox Pure build now parks
the emulation worker before polling input and copying video/audio, and samples
the original PIT counter inside the video callback. The runner queues keyboard
events until that synchronized poll. Frame skipping is disabled.

The final comparison reports `passed: true`, no provenance differences, no frame
mismatches, and `audio_identical: true`. This demonstrates repeatability for the
recorded route and configuration. It does not establish every activity's coverage,
real-hardware timing equivalence, or parity with a rebuilt game.

## Pinned provenance

| Item | SHA-256 / revision |
| --- | --- |
| Downloaded original ZIP | `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c` |
| Original executable | `16c5623174f0e97ee928790fd6d3e638d5724f3fb2a7794c7d3a48274f1d82d9` |
| Unpacked main image | `f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f` |
| Prepared launch ZIP | `a6cda560d3a7abc0e601b1f19698de5cb3a1aeae2652be14df3492c456289a7c` |
| DOSBox Pure upstream commit | `db325ff427e3d0df2e6c38bc75b00b6771e03b38` |
| Built capture core | `51b29480c3f55ac7840a2009b87a6693693d7f3472718cf9b8e88f0f0ff19bd9` |
| Final capture tool | `6b796f1a1ef478fcc1083a35a22cec7715ad6f1047583a6984781d700ea62d3a` |
| Final libretro adapter | `f2e33e5393d892fe598d8ab3fc530b7762e214e339f0971c40bfbbb921fdf4a5` |
| Each final timeline | `b2dc7af1ffcbe121e351a7b9077be246f77f5faa462b6e16f971c2caa840ba5b` |
| Each final recorded WAV | `a45d01cfde9699e1ea50baf82bbdadf8a369751f78000e8e3ab54ec255995634` |

The original package is linked from the
[Internet Archive preservation record](https://archive.org/details/msdos_The_Treehouse_1991).
The launch ZIP retains original file contents and adds a fixed DOSBox configuration.
Capture runs use 10,000 normal CPU cycles, fixed DOS date/time, direct virtual mouse
input, native reported 70.0863037109375 Hz video, and 48,000 Hz audio.

Original binaries, decoded artwork, emulator checkout/build, and full recordings
are in ignored `testing/output/treehouse/`. The maintained extraction, unpacking,
capture, and comparison tools are in [tools/treehouse](../tools/treehouse/README.md).
No existing Letter Rescue gameplay implementation was changed.

## Reconstruction next

1. Implement the original palette, clipping, sprite compositing, and animation
   interpreter. The recovered title background already matches the original's
   unobstructed pixels, but overlaid sprites and text still need reconstruction.
2. Rebuild startup, character selection, and interior interaction against the
   captured route; compare every emitted frame and report all differences.
3. Expand the route inventory through each activity, including transitions,
   sounds, keyboard/mouse behavior, progression, and exit paths. Recover additional
   executable logic as each route requires it.
4. Add optional readable text and modern input/rendering settings after the
   corresponding original behavior has a verified reference. Keep an original
   presentation mode for comparisons.

Performance changes must preserve game-clock behavior. Readability changes will
intentionally change pixels and need their own checks alongside the original mode.
