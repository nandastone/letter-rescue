# Playable Treehouse demo — 2026-09-27

> Historical first demo. The current build and verification results are in
> [the theater milestone](treehouse_theater_demo.md).

The first independent playable demo is built at
`testing/output/treehouse/playable/index.html`. It is one portable HTML file,
10,447,699 bytes, SHA-256
`47f4fa3b5ef469056266d2d9bb580a94bbb7ac2dcaf29df434abfe4f4d68a184`.

The complete game remains the target. This deliverable covers a playable route
through character selection, the interior, music, and telescope views. It is a
new renderer and game runtime built around recovered resource data; no DOS
emulator, original executable, or recorded screenshots run in the browser.

## What is playable

- Both characters and their original entrance animation scripts.
- Original interior composition and character animation.
- Music keyboard with 17 chromatic keys; mouse, touch, and original key bindings.
- 35 individual instrument choices, original decoded PCM, and audition animations.
- 24 original songs, five tempo choices, and original notation graphics.
- Demo tune recording, local persistence, and playback.
- Four original telescope pictures and three original animation scripts.
- Large reading text, adjustable size, accessible controls, and optional local
  English speech synthesis. Original instrument facts appear in the reading panel.

## Validation performed

The [retained verification report](treehouse/demo_verification.json) records
**89 passing checks**, with no browser exceptions. Playwright exercised both
entrances, every instrument choice and audition, every song, note release,
pointer dragging outside the piano, window blur, saving/replaying a tune,
telescope views, a 390px mobile layout, and the normal real-time animation loop.

The software renderer's full 320x200 RGB frame was compared with native captures:

| Captured state | Different pixels | Exact match |
| --- | ---: | --- |
| Initial exterior/title, pointer (160,100) | 0 / 64,000 | Yes |
| Interior, boy, reference date/clock, pointer (95,145) | 1 / 64,000 | No |
| Initial music room, Bass / Lion Theme, pointer (49,185) | 0 / 64,000 | Yes |
| Initial music score region | 0 / 15,900 | Yes |

The interior difference is at `(33,152)`: the original capture is white and the
decoded background is gray. It has not been masked, tolerated, or patched with
a special pixel. Lossless differences and browser screenshots are retained in
ignored `testing/output/treehouse/demo-verification-delivery/`.

The sound decoder covers all 283 digital resources. The Bass PCM is independently
equal to all 9,861 bytes of the original sample in live guest memory. Browser
resampling, gain, release ramps, and final mixed audio are not established as
native-equivalent.

These checks establish static rendering and playable behavior in this slice.
**Full frame-by-frame clone parity has not been established.** Startup scheduling,
all activity rules, all application callbacks, original editing behavior, and
audio mixing still require reconstruction and comparison. The clock/date are
currently held at the captured reference state.

## Reproduce

See [demo build/play instructions](../treehouse-demo/README.md). With the earlier
capture core and prepared ZIP in place, the additional native music reference is:

```powershell
python tools/treehouse/capture.py testing/output/treehouse/source/reference-v1.zip testing/output/treehouse/demo-piano --actions testing/treehouse/routes/music-room.json
```

The verifier uses that reference and the earlier `entry-verified-a` reference:

```powershell
python tools/treehouse/build_demo.py
python tools/treehouse/verify_demo.py --output testing/output/treehouse/demo-check-new
```

New output names are required for captures and verification. Original resources,
derived media, and the portable build remain in ignored output directories.
Maintained source is in `treehouse-demo/` and `tools/treehouse/`. No existing
Letter Rescue gameplay files were changed.

## Remaining reconstruction

The next work is complete temporal comparison of these routes, recovery of the
remaining original activity logic, and replacement of demo-specific controls
with faithful original editing behavior plus optional readable UI. Theater,
writing, board games, instrument ensembles, and live pet simulation are not yet
playable here. The fourth telescope picture is static.

Primary-source derivations are in [scene research](treehouse_demo_scene_research.md)
and [music research](treehouse_demo_music_research.md). The
[earlier report](treehouse_first_stage.md) documents resource recovery and original
replay repeatability.
