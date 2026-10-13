# Treehouse fidelity follow-up — 2026-09-27

Primary evidence: the pinned DOS v1.1 unpacked executable, extracted original
DAT resources, and retained `entry-verified-a` frame timeline and RAM. This
research does not change the demo runtime or generate new native captures.

## Interior mismatch resolved by an original rectangle operation

The unexplained white pixel at `(33,152)` comes from a **whole-rectangle fill**
performed by the original program. No resource correction or pixel exception
is needed.

- Interior initialization calls `0x35FA` from `0x2266`, with both arguments zero.
- `0x3603..0x3610` takes the room hotspot table pointer and adds `0xA0`, selecting
  record 20. The original words at image `0x2E938 + 20*8` are
  `(top=140,left=4,bottom=153,right=34)`.
- The captured room's `DS:5688` is zero. With argument zero, the checks at
  `0x3698..0x36A8` choose `0x36B3`, which calls `0D51:7F08` at `0x36BD`
  with that rectangle and color 15 (white).
- Therefore the room should fill the entire half-open rectangle
  `x=4..33,y=140..152` with white as part of scene composition.

Applying precisely that rectangle to the independently reconstructed interior
changes exactly one RGB pixel, `(33,152)`, from `(219,219,219)` to white. The
result matches all **64,000 / 64,000** pixels of the retained original
`entry-verified-a/state/after-click.png`, including the recovered cursor.
This is a static frame comparison, not an animation timing result.

Scratch evidence:

- `output/treehouse/research-fidelity/interior-native-rectangle.png`
- `output/treehouse/research-fidelity/interior-rectangle-evidence.json`

The original white area is part of the small clock/date panel at the left of
the room. The alternate branch at `0x36AB` calls `0x37AB` to draw clock glyphs;
the same routine also has other scene-mode branches. The fill should retain its
meaning as a scene operation rather than become a magic pixel correction.

## Entrance is three sequential scripts

The current demo's direct transition from a frozen welcome pose to SCR 8002 or
8003 omits two original animations. Character selection at `0x0767` stores
index `0` for boy or `1` for girl. The accepted character branch then calls
`0x415F` three times:

| Call site | Group | Script offset | Boy route | Girl route |
| --- | ---: | --- | ---: | ---: |
| `0x083A` | 8000 | selected index | 8000 | 8001 |
| `0x0899` | 8000 | opposite index | 8001 | 8000 |
| `0x0902` | 8000 | selected index + 2 | 8002 | 8003 |

These are synchronous calls: `0x415F` forwards to `0x419D`, whose loop
`0x4855..0x48BD` invokes interpreter `0xBDA0` until completion. Each greeting
runs before the next begins. The unselected character remains in its last
pose while the selected character walks into the tree.

The setup calls at `0x0C0B`, `0x0C3F`, and `0x0C6B` pass the stop-after-first-
frame argument. In `0x4868..0x487B`, the flag selects an early exit when global
frame-update count `DS:5586` equals one. Thus the welcome scene initially
presents first poses; it should not automatically run both greeting scripts
concurrently.

The greeting scripts 8000/8001 each contain fifteen updates with 7-tick waits,
for 105 ticks including the final completion wait. Boy entrance 8002 contains
44 updates / 308 ticks; girl entrance 8003 contains 34 updates / 238 ticks.
These totals come directly from opcode-01 repeat and delay operands. They are
semantic durations, excluding resource loading and draw/caller overhead.

## What the native frame sequence establishes

The route applies the mouse button starting at run 1830. The first changed
image is run 1831 at original PIT tick 1532. The retained sequence shows the
boy greeting, girl greeting, and boy entrance in that order, then the interior.
A contact sheet of every changed image from runs 1820 through 2600 is saved as
`output/treehouse/research-fidelity/entrance-sequence.png`.

Adjacent callbacks sometimes capture partially completed software drawing:
for example runs 1868/1869, 1893/1894, and 2030/2031. Runs 2030 and 2031 both
have the same original PIT tick 1701 but different RGB images. This directly
shows that a PIT tick alone cannot uniquely determine the presented native
frame. The timeline also retains scene-transition frames with black areas and
partial incoming room data; those are part of the strict reference.

Consequently an all-callback comparison needs more than advancing the SCR
interpreter once for each distinct timer value. It must preserve the original
application sequence, start times, sprite dirty/background operations, and
presentation during drawing (or explicitly distinguish a completed-render
comparison from full native presentation equality). Do not silently discard
those callbacks or align each frame to its nearest-looking native frame and
call the result full temporal parity.

The current synchronized original capture remains reproducible: sampling RAM
and framebuffer at the video callback gives a stable original reference. That
synchronization does not make the game's software drawing atomic at the
hardware presentation boundary.

## Measured content parity for all boy-entry script updates

A separate scratch renderer (`output/treehouse/research-fidelity/analyze.py`)
reconstructs the exterior from original SHAP and SHPL resources, applies the
recovered girl palette modification, and evaluates every opcode-01 update of
scripts 8000, 8001, and 8002 in the sequential call order above. It contains no
native screenshot pixels in its reconstruction. It paints the other character
in the appropriate first or last greeting pose and uses original bounds and
zero transparency / opaque modes.

All **74 / 74** reconstructed full-frame script updates have an exact RGB
counterpart in the retained original entrance sequence, including all 64,000
pixels. Those updates represent **65 distinct images**. The report is
`output/treehouse/research-fidelity/entrance-semantic-matches.json`; it records
each script, update index, semantic relative tick, and every matching native
run index. Selected endpoint images are saved beside it.

Of the 629 native callbacks in the inspected range `[1831,2460)`, 611 are equal
to one of those independently reconstructed images. Eighteen are not:
`1868,1893,2022,2030,2038,2138,2146,2171,2179,2220,2253,2302,2343,2392,2434,2442,2450,2459`.
These observations establish complete script-pose content coverage for this
boy-entry slice. They do **not** establish 611 correct callback timestamps:
the lookup searches the whole bounded reference interval and repeated poses
can match multiple moments. The eighteen transient images remain strict
comparison failures; the subsequent scene transition is outside this measured
range and remains unimplemented in this scratch renderer.

The unchanged original background/title/credit composition matches throughout
this measured entrance slice. No changing-credit behavior is needed to explain
these captured frames. Future comparison should first retain the recovered
sequential scripts and initial freezes, then record original animation entry,
update, dirty transfer and presentation events to resolve their exact ordering.
