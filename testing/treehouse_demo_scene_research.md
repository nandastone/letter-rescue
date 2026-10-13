# Treehouse demo scene reconstruction

Date: 2026-09-27. Primary sources: the pinned DOS v1.1 executable and DAT files,
the existing `entry-verified-a` original captures, and the parent's
`demo-telescope` capture. No emulator was run by this research slice. Binary
identities are recorded in [the first-stage report](treehouse_first_stage.md).
All coordinates below refer to the original 320 by 200 framebuffer.

## Exterior: an exact reconstructed frame

The following composition reproduces `entry-verified-a/state/title.png` with
**zero differing RGB pixels out of 64,000**, including its mouse cursor. This
comparison concerns one reconstructed frame, not startup timing or every-frame
gameplay parity. The scratch result is
`output/treehouse/research-scenes/title-reconstructed-with-cursor.png`.

| Archive | SHAP | SHPL | X | Y | Role |
| --- | ---: | ---: | ---: | ---: | --- |
| TH64 | 1 | 0 | 0 | 0 | Opaque exterior background |
| TH64 | 2 | 0 | 2 | 0 | Title sign |
| TH64 | 3 | 0 | 0 | 109 | Copyright sign |
| TH | 12 | 6 | 10 | 52 | Monochrome credits, foreground black |
| TH | 8001 | 8000 | 80 | 105 | Boy upper body |
| TH | 8002 | 8000 | 82 | 150 | Boy lower body |
| TH | 8001 | 8001 | 128 | 109 | Girl upper body, palette override below |
| TH | 8047 | 8001 | 130 | 154 | Girl lower body |

Except for the opaque background, zero source indices are transparent. The
monochrome credit image's nonzero bits are black. TH SHAP 10 through 17 contain
the complete original credit text as bitmaps; they are not host-font text.

### Girl palette modification

Routine `0x59C0`, called during exterior setup at `0xBC5`, modifies palette
entries 9 and 10 for the girl. The original image at `0x2EAB4` contains RGB6
bytes `[4,34,63,2,23,42]`. After bit replication these are `(16,138,255)` and
`(8,93,170)`. Applying the on-disk SHPL 8001 alone misses this modification.
The first six bytes at that location and the call's two-color count are direct
executable evidence, while the exact frame comparison independently validates it.

SCR 8000 and 8001 are the idle boy/girl scripts. Their first slot configurations
produce the positions above. Entry scripts 8002/8003 use the same shape group
starting at SHAP 8001; select palette 8000/8001 according to character.

### Original arrow cursor recovered from the executable

The unpacked executable at `0x310B0` contains a 68-byte cursor definition:

- Two signed little-endian 16-bit hotspot coordinates, both -1.
- Sixteen little-endian 16-bit AND-mask rows at `0x310B4`.
- Sixteen little-endian 16-bit foreground-mask rows at `0x310D4`.

Read bits most significant first. For the observed arrow, an AND bit of one
preserves the destination. An AND bit of zero paints black, or paints the
selected foreground when the corresponding foreground-mask bit is one. The
foreground is palette color 14, RGB `(255,255,85)`, in these captures. The
negative hotspot gives a draw origin of `(pointerX+1,pointerY+1)`. Original title
pointer `(160,100)` therefore draws at `(161,101)`. This recovered definition
accounts for all 95 previously differing title pixels.

## Interior composition

Original setup routine `0x1F24` selects background group SHPL 4, its first shape,
and installs the room's other palettes. The complete base is **TH64 SHAP 5,
SHPL 4**, at `(0,0)`.

The following overlays are established by original setup calls and/or exact
nonzero-pixel matching against `entry-verified-a/state/after-click.png`:

| Archive | SHAP | SHPL | X | Y | Role |
| --- | ---: | ---: | ---: | ---: | --- |
| TH | 176 | 170 | 195 | 32 | Cloud |
| TH | 905 | 900 | 96 | 43 | Balloons |
| TH | 1109 | 1100 | 49 | 121 | Theater curtain |
| TH | 919 | 900 | 236 | 117 | Fruit bowl |
| TH | 917 | 900 | 246 | 117 | Banana over bowl |
| TH | 918 | 900 | 106 | 132 | Small pinwheel |
| TH | 1256 | 1250 | 211 | 84 | Nest part, draw before next row |
| TH | 1251 | 1250 | 211 | 81 | Nest part |
| TH | 1201 | 1200 | 162 | 28 | Screen calendar marking |
| TH | 1228 | 1200 | 132 | 21 | Calendar corner |
| TH | 938 | 930 | 284 | 159 | Nuts |
| TH | 940 | 930 | 5 | 159 | Wastebasket |
| TH | 926 | 900 | 151 | 182 | Board detail |
| BOY | 20501 | 20500 | 152 | 123 | Selected character |

Fruit SHAP 919 by itself has 20 differing foreground pixels. Drawing SHAP 917
over it resolves those pixels; its placement also agrees with the original
interactive fruit region. Do not modify the bowl's bitmap to match a screenshot.

### Original bitmap font and date

TH FONT 1 begins with first/last character bytes `00 D9`. A table of 218
little-endian 16-bit offsets begins at byte 10. Each table entry points to a
SHAP-format monochrome glyph in the same resource. Empty control glyphs have
zero dimensions and must be handled before calling the strict SHAP decoder.
For example ASCII `A` points to `0x47F`, a 9 by 6 raw monochrome glyph; ASCII
`0` points to `0x377`, also 9 by 6.

Drawing `Jan. 1, 1992` at `(71,25)` with foreground `(255,85,85)`, advancing by
each glyph's width with no additional spacing, matches every original foreground
pixel in the reference date. Keep the original bytes and rendering available
alongside any modern readable text option.

### Digital clock

Routine `0x2F86` draws SHPL 1200 glyphs with opaque mode 0. Digits zero through
nine are SHAP 1215 through 1224. SHAP 1225 is the colon, 1226 the blank leading
hour position, and 1227 the leading one. For the actual reference **12:39**:

| SHAP | X | Y |
| ---: | ---: | ---: |
| 1227 | 95 | 110 |
| 1217 | 97 | 110 |
| 1225 | 102 | 110 |
| 1218 | 104 | 110 |
| 1224 | 109 | 110 |

The launch configuration's intended noon time must not be substituted for the
observed clock; opaque glyph comparison identifies 12:39 in this capture.

### Chalk primitives

Routine `0x2785` fills the chalk regions and eraser; `0x31DE` selects the chalk
color. In the reference, six horizontal strips occupy inclusive y=93..94 and
inclusive x ranges 63..72, 75..84, 87..96, 99..108, 111..120, 123..132. Their
RGB values, in order, are white, `(255,0,0)`, `(247,247,32)`, `(101,4,255)`,
`(8,170,0)`, `(255,199,199)`. The eraser has x=136..147: white at y=92 and
`(170,170,170)` at y=93..94, with black side columns x=135 and x=148.

### Remaining static discrepancy

With these assets and primitives, bitmap date, clock, and original cursor, the
room matches except for **one pixel at `(33,152)`**: the reference is white and
the TH64 background gives `(219,219,219)`. Its cause remains untraced. Preserve
this as a reported mismatch; do not patch an unexplained coordinate or exclude
it from an exact comparison. The reference's pointer is `(95,145)`, verified
from RAM DS:2064/2066, so its arrow origin is `(96,146)`.

## Hotspots and telescope activity

The room's 31 rectangle records begin at original image offset `0x2E938`.
Each record is four signed words `(top,left,bottom,right)`; lower/right bounds
are exclusive. Setup `0x1F24` installs table offset 0x48 in segment 0x2E8F.
Piano index 1 is `(175,7,200,106)`; telescope index 5 is `(102,167,157,228)`.
The room dispatch jump table is at `0x1804`, indexed after subtracting one;
piano branches to `0x12F0`, telescope to `0x141D` and then `0x2534`.

Telescope routine `0x2534` selects a view index 0..3. It clears to black, centers
the first image from SHPL `780 + 2*index` in the full screen, and adds the
original exit icon TH SHAP 8 / SHPL 6 at `(304,1)` with zero transparency.

| Index | Background SHAP / SHPL | View | Animation SCR / SHPL |
| ---: | --- | --- | --- |
| 0 | 781 / 780 | Planets | 800 / 800 |
| 1 | 783 / 782 | Monster | 820 / 820 |
| 2 | 785 / 784 | Birdbath | 840 / 840 |
| 3 | 787 / 786 | Birdcage | Special live-pet branch; not recovered here |

SCRs 800, 820, and 840 use only opcodes 00, 01, 03, 07, 9n, Bn, and Cn. Their
original bounds are `(55,105,110,197)`, `(88,150,96,168)`, and
`(52,99,104,224)` respectively. The original enters a replay loop; a click inside
the view's active rectangle reruns the animation, while a click outside or
Escape returns. Its active rectangles are stored at DS:`0x358 + 8*index`.

## Evidence paths and scope

- Original resources: `output/treehouse/extracted-v2/manifest.json` and its
  hash-checked resource payloads.
- Executable: `output/treehouse/disassembly/unpacked.bin`; source-address
  browsing aid: `output/treehouse/research-resources/main-disassembly.txt`.
- Script payloads: `output/treehouse/disassembly/scripts.json`.
- Reference captures: `output/treehouse/entry-verified-a/state/title.png`,
  `after-click.png`, and corresponding RAM dumps.
- Parent's original telescope observation:
  `output/treehouse/demo-telescope/state/telescope.png`.
- Research renderings: `output/treehouse/research-scenes/`.

These findings establish scene composition and a bounded activity path. They
do not establish complete activity logic, all animation start times, audio
parity, or full-game fidelity.
