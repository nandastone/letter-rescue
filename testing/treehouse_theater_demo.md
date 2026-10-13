# Sentence theater milestone — 2026-09-27

The independent playable build now includes the original sentence theater.
Generated file: `output/treehouse/playable/index.html`, **10,475,400 bytes**.
SHA-256: `6711f79b4a92547eabd43ca0f9109c347fee96e4c15bebbd887a74eb5c9eb43b`.
The live local server serves this file at `http://127.0.0.1:8767/`.

## Playable additions

- Enter via the room curtains or **Put on a play**.
- Choose eight actors, eight actions, six locations, and four time settings.
- Perform all 64 actor/action combinations using the original SCR programs.
- Hear original DIGISND spoken phrases; location palettes and weather use the
  recovered tables and original artwork.
- Build sentences using original notebook icons or large readable word lists.
- Rearrange sentence parts, receive grammar feedback, add decorations, and drag
  actors and decorations. The original limit of 20 decorations per place is kept.
- Retain the music activity, both character routes, telescope views, mobile
  layout, text size controls, and optional local read-aloud.

The browser runs the reconstructed JavaScript interpreter and decoded assets.
It does not execute the DOS program, run an emulator, or display captured frames.

## Fidelity improvements

Recovered overlay-4 numeric tables are extracted directly from the pinned
unpacked executable by `build_demo.py`. This includes original hit rectangles,
actor offsets, stage placement, palettes, preview positions, weather timing,
and curtain shapes. The built-in FONT 0 is decoded from image offset `0x2EAC0`;
FONT 1 comes from the resource archive.

Native rendering details now reproduced include category fill colors, integer
centering, transparent backdrops, two-line sentence wrapping, and the original
second-line leading-space centering quirk. See the disassembly evidence in
[theater research](treehouse_theater_research.md).

The interior's former one-pixel mismatch is fixed by reproducing the original
whole-rectangle white fill. The entrance now performs the selected greeting,
the other greeting, and the selected character's walk in sequence, hiding the
cursor while they run. See [fidelity research](treehouse_fidelity_followup.md).

## Verification

All reports identify the exact build hash above. The verified candidate and
delivered portable file are byte-identical.

| Evidence | Result |
| --- | --- |
| [Existing demo regression](treehouse/demo_theater_regression.json) | 90 checks passed; no browser exceptions |
| [Theater checks](treehouse/theater_verification.json) | 107 checks passed; no browser exceptions |
| Title, interior, initial music room | 0 differing pixels in each 320×200 image |
| Theater intro and empty editor | 0 differing pixels in each image |
| Actor list, baby selected, action list, bubbles selected | 0 differing pixels in each image |
| Location list, jungle selected, time list, night selected | 0 differing pixels in each image |
| [Boy entrance image comparison](treehouse/entrance_verification.json) | All 73 checked render states match complete native images |

Theater behavior checks exercise all 64 actor/action combinations, all 24
place/time combinations, grammar constraints, optional phrases, decoration
limits and dragging, readable controls, actual browser audio startup, a complete
performance, navigation, and a 390px mobile viewport. The existing regression
also exercises the normal real-time entrance loop, music input, instruments,
songs, recording, and telescope views.

Lossless frames, differences, and browser screenshots are retained under
`output/treehouse/theater-verification-c/` and
`output/treehouse/demo-verification-theater/`. A complete native capture input
route is checked in at [theater-sentence.json](treehouse/routes/theater-sentence.json).
The ten theater comparisons use retained captures under `demo-theater`,
`theater-edit`, `theater-baby`, `theater-places`, and `theater-night`.

Reproduce checks with the commands in [the demo README](../treehouse-demo/README.md).

## Remaining reconstruction work

This is a larger playable slice; complete game parity remains the objective.
The image comparisons do **not** establish frame timing or whole-game parity.
The entrance check establishes image membership, not chronological callback
alignment. Native partial-draw transfer frames and precise scheduler timing are
not yet reproduced. The theater's complete animated performances have behavior
coverage, but have not yet undergone aligned frame-by-frame comparisons.

Theater file save/load, original correction interactions, possum directing
animations, phrase highlighting during performance, contextual narration
variants, and exact prop drag/release behavior remain incomplete. Actor dragging
uses recovered whole-sprite stage bounds; immediate dragging is a demo input
choice. Decorations currently clamp while moving, whereas the original permits
dragging outside and removes an out-of-stage decoration on release. Modern
sentence-order controls are functional but do not yet reproduce every native
Mix-Up interaction. Performance sound/animation ordering and mixed audio output
are not proven native-equivalent.

Writing, board games, pets, ensembles, advanced music editing, and other original
activities remain to be implemented. The interior retains the reference clock
and date. Original assets and generated HTML remain in ignored output folders;
the existing Letter Rescue game is unchanged.
