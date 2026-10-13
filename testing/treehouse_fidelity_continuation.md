# Treehouse fidelity continuation — 27 September 2026

## Play

Refresh [the local demo](http://127.0.0.1:8767/). The same portable offline file is
`output/treehouse/playable/index.html` relative to this directory.

Build SHA256: `295b74955d4b6a44308192976994fff5b11fe0e05c10c3d20fb7639ffa0c0c91`.
Size: 10,578,065 bytes. Original package SHA256:
`53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`.

## Changes

- **Board games:** tick-driven original dashboard performances, reward delivery,
  moving moneybags and chips, repeated exchange hints, and animated carry/borrow
  commits. Input waits for the relevant animation. Trades still require a child’s
  choice. The former delivery-reference mismatch of778pixels is now zero.
- **Theater:** original15tick token hold, category swaps, left-side deletion,
  notebook-to-rail selection, stage-drop restoration, animated five-swap shuffle,
  exact empty-slot grammar correction, and remembered validation for successful
  manual-correction feedback. Readable shuffle/correction buttons are included.
- **Nature quiz:** exact attribute definitions and candidate-inspection panels;
  Help prevents manual crossing out; the robot waits for the next die click;
  deduced human answers can trigger automatic guesses. Correct original shrub,
  celebration and retreat SCR IDs are used.
- **Music:** original family selector and seven portrait pages,35 individual
  instruments and seven original ensemble samples, instrument facts/icons and
  waveforms, two-staff notation and playback markers, and original idle eyes.
  Audition voices stop when the audition finishes.

The browser still uses original decoded resources, independently rendered in
JavaScript. Native screenshots and DOS machine code are verification inputs,
never runtime rendering assets. Existing Letter Rescue files were not changed.

## Verification of this exact build

All nine suites identify the build hash above. Full results are preserved in
[fidelity_continuation_verification.json](treehouse/fidelity_continuation_verification.json).

| Suite | Behavioral checks | Exact image evidence |
| --- | ---: | --- |
| Base scenes/music |90|3 full frames,1 score region |
| Theater |107|10 full frames |
| Nature exploration |101|5 full frames |
| Theater interaction/nature quiz |46|31 full frames |
| Chalkboard |11|8 drawing/tray regions |
| Board games |10|15 full frames |
| Music families/advanced notation |47|4 full frames,1 score region |
| Entrance |—|73/73 render states |
| Theater performance |—|38/38 display changes in original order |

**412 behavioral checks passed;68 full-frame and10 region comparisons are exact.**
No browser exceptions were recorded. This includes30 complete animal quiz games,
60 complete board games/484turns, recursive carries/borrows, all42 instrument
auditions, and mobile controls. Comparisons use exact RGB equality without masks
or tolerances. Original random deals are supplied as model data for selected
references; generated games are exercised separately.

The board delivery reference matches at sequence tick86. The advanced music
reference matches idle-eye step5. The notebook-add reference matches the place
preview phase. These are independently generated matching animation states;
native wall-clock alignment has not been proven. Entrance checking establishes
image membership. Theater playback checking additionally establishes order.

## Work still remaining for a complete clone

1. Original music composition: duration/rest palette, note insertion/editing,
   short/long personal song books, copy/save/load, and original persistence.
   Modern recording remains available; two-staff display alone is not that editor.
2. Musical maze, discovered through the original piano’s bucket hotspot.
3. Pet/remaining room interactions, live clock/calendar behavior, and remaining
   telescope behavior.
4. Nature’s complete turn-entry, question, wrong-guess and post-win sequencing,
   question-background callbacks, idle guidance, and ordered native comparisons.
5. Board payment/win/loss/replay presentation and exhaustive dashboard, chip,
   moneybag and exchange-motion comparisons.
6. Theater save/load, all token/shuffle motion comparisons and complete audio
   scheduling. Family-selector fact alternates, selection transitions, and all
   remaining category/portrait references also need verification.
7. Shared DOS scheduling, random-call alignment, audio mixing/resampling, and
   unsupported resource operations. A full pixel-perfect clone is not yet claimed.

Research recipes and source offsets:
[theater](treehouse_theater_followup.md),
[nature](treehouse_nature_followup.md),
[music](treehouse_music_followup.md),
[board game](treehouse_boardgame_research.md).

Reproduction commands are in [the demo README](../treehouse-demo/README.md).
The preceding [delivery report](treehouse_nature_boardgame_demo.md) retains its
earlier hash and the old transient mismatch for an auditable history.
