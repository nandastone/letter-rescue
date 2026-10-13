# Treehouse DOS v1.1 theater reconstruction

Date: 2026-09-27. Primary sources are the preserved DOS executable and its
`modules.dat`, statically unpacked and decoded by the maintained tools. Parent
captures at `output/treehouse/demo-theater/` independently show the original
activity. This note distinguishes recovered rules from unverified timing.

Binary identities are in [the first-stage report](treehouse_first_stage.md).
All overlay addresses below are offsets in **overlay 4's body**, beginning at
EXE file offset `0x3DA00`; its entry is `0x31`. The data segment (DS) begins at
unpacked main-image offset `0x321D0`. These are original image offsets, before
DOS relocation. Source browsing aids are
`output/treehouse/research-resources/overlay4-disassembly.txt` and
`main-disassembly.txt`; extracted raw tables are in
`output/treehouse/research-theater/tables.json`.

## Activity and startup

This is a sentence-building theater. The actor, action, location, and time are
independent choices. It is not a fixed story selector. Overlay 2 is the nature
sorting activity; overlay 4 contains the theater's 3000-series resources.

Entry `0x31` loads graphics and calls `0x1354` to construct the screen, then
`0x1B6B` to display the initial options stage. During this stage there are only
four active rectangles: exit, Mix Up, Props, and PLAY. The visible notebook's
category buttons are inactive until PLAY is pressed. `0x1D18` handles PLAY,
returns from the options loop, and enables the normal editor. This accounts
for the parent's observed inactive WHO OR WHAT button on first entry.

The normal editor uses 29 rectangles at **unpacked image `0x30C80`**, four
signed words per rectangle `(top,left,bottom,right)`. Right and bottom are
exclusive. The options loop uses a separate four-record table at `0x30D98`.

| Options control | Rectangle |
| --- | --- |
| Exit | `(1,304,23,319)` |
| Mix Up | `(81,184,88,192)` |
| Props | `(97,184,104,192)` |
| PLAY | `(133,185,146,201)` |

## Original choices and text

All strings below are recovered from original `modules.dat` STRL resources;
stored phrase strings have trailing spaces for sentence concatenation.

| Category | STRL | Choices in original index order |
| --- | ---: | --- |
| Who or what | 3000 | the baby; our crazy car; Bronto; Look-A-Lot; Bonga Bot; Sharpy Shark; Mister Bones; my favorite teacher |
| Does what | 3010 | blows bubbles; exercises; grows hair; juggles; jumps; takes pictures; eats pickles; spins |
| Where | 3020 | on top of the desk; in the jungle; at the beach; on Moon Miranda; at a party; in the middle of nowhere |
| When | 3030 | every day; at night; during an eclipse; during a storm |

STRL 3050 contains the four grammatical explanations; STRL 3060 contains the
five all-caps category headers, including PROPS. STRL 3070 contains validation
feedback. Strings should be read directly from assets, not recopied as a
separate translation source.

Sentence builder `0x2B16` concatenates each selected phrase in the current
category order, removes the trailing space, and, when both subject and action
exist, capitalizes the first character and adds a period.

Validator `0x413A` has the following results:

| Code | Meaning |
| ---: | --- |
| 0 | Valid sentence ordering |
| 2 | Both subject and action missing |
| 3 | Subject missing |
| 4 | Action missing |
| 5 | Action precedes subject |
| 6 | Another selected phrase lies between subject and action |

Where and when are optional. The subject must immediately precede its action
among present sentence parts. A time or place before the subject, or after the
action, can still be grammatical. This is more permissive than requiring the
fixed four-category order. Functions `0x4498` and `0x461F` construct corrections.
Exact correction selection/randomness is not yet independently replayed.

## Selection and controls

Normal category icon rectangles have indices 8 through 11. Their label
rectangles have indices 12 through 15. Clicking a label displays grammar
explanations (`0x2316`); clicking the icon displays choices (`0x4A26`).

| Category | Icon rectangle | Label rectangle |
| --- | --- | --- |
| Subject | `(29,14,51,61)` | `(51,14,60,61)` |
| Action | `(61,14,83,61)` | `(83,14,92,61)` |
| Place | `(93,14,115,61)` | `(115,14,124,61)` |
| Time | `(125,14,147,61)` | `(147,14,156,61)` |

The shared choice strip is `(15,73,42,294)` (index 16). `0x1AD3` divides it into
equal integer-width rectangles for choices, except that the subject icon
renderer at `0x20D6` replaces their bounds with the actual icon widths, spaced
five pixels apart. All choices use the strip's full vertical span for clicks.

Exact choice rendering in `0x20A4`:

- Subject: SHPL 3980 shapes 1..8, first x=75 and subsequent x increased by
  previous shape width+5; y=42-height. Click rectangles start two pixels left
  of the rendered shape and have its width.
- Action: SHPL 3050 shapes 35..42 at `(x,y)` positions `(73,19)`, `(105,18)`,
  `(128,22)`, `(156,19)`, `(179,19)`, `(206,21)`, `(238,19)`, `(266,18)`.
  The original table is DS:`0x109A`, storing `(y,x)` pairs.
- Place: each group's second shape centered in its 36-pixel-wide strip cell,
  drawn opaque with that group's daytime palette.
- Time: SHPL 3120 shapes 20..23 centered in 55-pixel-wide cells, transparent.

Other important original regions:

- Index 0: exit `(1,304,23,319)`.
- Index 1: activity options `(24,299,43,319)`; handler `0x5B4` reopens Mix Up/Props.
- Index 7: possum `(155,61,200,99)`.
- Index 18: small action-preview area `(97,265,122,305)`.
- Index 20: sentence text `(176,100,195,300)`.
- Indices 23..26: four Mix Up token slots `(49,141,69,162)`,
  `(49,164,69,185)`, `(49,187,69,208)`, `(49,210,69,231)`.

The actor onstage can be dragged. `0x27A4` constrains its bounds and saves its
translation per place in state `0x3169:8CE`. Changing actor clears these offsets
(`0x48B2` calls `0x2AD0`). Props likewise have draggable rectangles and are stored
per place. This is original behavior; a simple select-and-play implementation
does not yet reproduce all the editing features.

## Graphics and composition

All groups here are in **MODULES**, except the shared small UI glyph group in TH.
Group-relative shape indices are one-based. SHPL entries select palettes and
may share the same shapes with different colors.

| SHPL | First SHAP | Count | Role |
| ---: | ---: | ---: | --- |
| 3000 | 3001 | 31 | Small theater UI art |
| 3034 | 3035 | 5 | Possum and startup option art |
| 3040 | 3041 | 9 | Full theater background and four curtain stages |
| 3050 | 3051 | 42 | Small action-preview figure and action icons |
| 3100 + 3 × place + variant | 3101 + 3 × place | 2 | Place background and thumbnail |
| 3120 | 3121 | 23 | Time icons and animations |
| 3145 | 3146 | 26 | First prop collection |
| 3175 | 3176 | 24 | Second prop collection |
| 3200 + 100 × actor | 3201 + 100 × actor | varies | Actor shapes |
| 3980 | 3981 | 8 | Small actor-selection icons |

`0x1354` draws SHPL 3040 shape 1 opaque at `(0,0)`. It adds SHPL 3000 shape 22
at the exit rectangle, shape 16 at the options rectangle, shapes 14/15 at bottom
button rectangles 3/4, and other state-dependent UI. Curtain routine `0x14E0`
uses shape-pair data at `0x30D88` and positions at `0x30D68`; it always draws
SHPL 3040 shape 9 at `(259,73)`. Open and close routines `0x158F`/`0x16AD` use
three 8-tick stages each. They play sound 10032 (`0x2730`).

### Actor placement and animation

For actor index `a` and action `v`, original playback calls
**SCR `3200 + 100*a + v`**, using SHPL `3200 + 100*a` (`0x2765`). All 64
combinations exist. Additional SCR 3610 exists but is not a ninth selectable
action. An actor's idle image is shape 1 of its group.

All 64 regular actor scripts use only opcodes 00, 01, 90, B0, and C0. Their
soundtrack is controlled by the activity. Small action-preview SCR 3056 also
contains opcode 10 with operand zero at byte offset 53; the original invocation
supplies no callback. Additional SCR 3610 uses sound 10024 four times.

Actor screen position is deliberately data-driven, not centered generically:

1. Read actor base rectangle at DS:`0x136E + 8*a`.
2. Read `(dy,dx)` at DS:`0x128E + 4*(8*(place+1)+a)`; place -1 is the empty
   stage. The seven rows cover empty stage and the six places.
3. Add the saved per-place drag translation.
4. Idle shape origin is translated bounds `(left,top)` plus `(dx,dy)` read
   from DS:`0x126E + 4*a` (stored as vertical then horizontal words).

Main resident code **`0x42BE..0x4332`** performs the same translation on the SCR
rectangle before animation. Do not replace its bounds by the actor's larger
idle rectangle: each action has its own bounds. Example: baby bubbles SCR 3200
has `(189,291,224,327)` and empty-stage offset `(-105,-119)`, yielding script
origin `(172,84)` in `(x,y)`. Its first B0 is `(2,9)`, so the initial shape is
drawn at `(174,93)`.

The exact recovered placement arrays are exported in the scratch tables JSON.
For a durable build, extract these arrays from the pinned unpacked executable.

Selecting an action changes the **small preview figure**, not the full actor's
animation (`0x48FC`, `0x32E9`). The small preview uses SHPL 3050, SCR `3050+v`.
Its idle shape index comes from DS:`0x106A`:
`[7,14,31,24,4,22,17,1]`. It is centered inside UI rectangle 18 and then shifted
by the signed `(dy,dx)` pairs at DS:`0x107A`.

### Places and time

Backdrop draw routine `0x29C2` draws the first shape of the selected place group
at **`(96,51)`**. `0x2946` selects its palette variant from DS:`0x1266`:

| Time | Variant |
| --- | ---: |
| Every day | 0 |
| At night | 2 |
| During an eclipse | 1 |
| During a storm | 1 |

Without time, variant 0 is used. These are original palette alternatives, not
modern tint filters. The corresponding palettes share the same backdrop pixels.
The backdrop uses **draw mode 10, zero transparency**, supplied by the caller
at `0x1804`; `0x29EF` forwards that mode. Its zero-valued top-edge pixels preserve
the already drawn theater artwork. Treating the entire backdrop as opaque
introduces the observed 55 black pixels along y=51, x=99..153 in the jungle
comparison. This is an asset compositing rule, not a coordinate-specific patch.

Time animations use SHPL 3120. DS:`0x10BA` stores four records of four words:

| Time | Choice icon index | First stage frame | Frame count | Ticks per frame |
| --- | ---: | ---: | ---: | ---: |
| Day | 20 | 1 | 3 | 12 |
| Night | 21 | 4 | 2 | 30 |
| Eclipse | 22 | 6 | 7 | 12 |
| Storm | 23 | 13 | 7 | 10 |

`0x3169` plays first+1 through first+count-1, then restores the first frame.
Placement is `(y,x)` from DS:`0x10DA + 4*(4*max(place,0)+time)`; actual rendering
is `0x19E1`. Time graphics are drawn before props and actor. Their positions
vary by backdrop, so do not center them generically either.

### Props

Props are selected per place. DS tables `0x101E`, `0x102A`, `0x1036` contain:

- First group-relative index: `[1,1,9,17,10,18]`.
- Number of choices: `[9,8,8,8,8,9]`.
- Group selector: `[0,1,1,1,0,0]`, where 0 is SHPL 3145 and 1 is SHPL 3175.

Renderer `0x37F2` encodes a prop as `(groupSelector << 8) | shapeIndex`.
Each of six backdrops stores up to 20 placed props: rectangle arrays at
`0x3169:41E + 8*(20*place+prop)` and IDs at `0x3169:7DE + 2*(20*place+prop)`.
Counts are at `0x3169:412 + 2*place`. Rendering preserves list order (`0x3825`).
Full drop/overlap/removal behavior remains to be traced and replayed.

## Voices and playback

Routine `0x2553` computes spoken phrase IDs as
`3000 + 10*category + selectedChoice + extraOffset`. Actor/place/time normally
use zero offset. Some action-reading branches use 100 or 3 as an offset
depending on the playback context; these should not be guessed away.
The phrase recordings are in **DIGISND**; the similarly named VOICES archive
contains the instrument voice samples in this package.

Playback `0x259D` traverses the current four-category order and invokes the
subject, action, place, and time presentation handlers, skipping unset choices.
It is a sequence of spoken/highlighted phrases with the appropriate visual
demonstration, not just simultaneous audio plus one animation. Selecting an
individual phrase also reads and demonstrates it. Runtime video/audio timing
still requires matched original captures.

The editor's perform control is the possum, rectangle index 7. Its handler
`0xD01` validates the sentence, animates the possum, then calls `0x259D` with
the flag indicating whether validation succeeded. A valid sentence runs the
actor animation once; completion restores its idle appearance (`0x3A5F`).
An invalid sentence still reads the present words with the demonstration flag
disabled, then shows feedback. There is no outer performance-repeat loop.
Enter/Space are the shared input system's click-at-current-pointer behavior,
not a theater-wide Play shortcut.

## Known limits

The tables, IDs, coordinate formulas, and rules above are direct binary
derivations. They have not all been independently validated against replayed
original frames. In particular, mixed-up sentence corrections, prop editing,
all voice special cases, and complete palette/callback timing remain open.
The original captures establish the modal startup distinction; the parent is
capturing selection and completed sentences for renderer comparisons.

## Exact text and centering follow-up

The parent's theater comparisons exposed different heading and body fonts.
Overlay `0x23C6` selects the saved default font through DS:57C4, draws the
category heading, then restores the resource FONT 1 via DS:20B2. Initialization
at main `0x1C4` preserves the default before loading TH FONT 1.

**FONT 0 is embedded in the unpacked executable at `0x2EAC0`, length `0x5F7`.**
The built-in resource record at `0x3166A` confirms its type, ID, pointer, and
length. It is not in TH.DAT. Its header is:

- First/last character: 27 and 126 (bytes 0 and 1).
- Ascent 7, descent 2, line gap 1 (words at offsets 2,4,6).
- Extra horizontal advance 1 (word at offset 8).
- 100 little-endian u16 glyph offsets beginning at offset 10.

Each embedded glyph begins `<u16 height,u16 width,u16 stride>`, followed by raw
one-bit MSB-first rows. The stride word is **not SHAP compression flags**.
ASCII A at relative offset 723 has height 7, width 6, stride 1, row bytes
`78 cc cc fc cc cc cc`. Space has height zero and width two. Advance is glyph
width plus the font's extra horizontal advance; FONT 1 has zero extra advance.
Resident renderer `0x153D5` and width function `0x17995` establish this rule.

The heading is horizontally centered in `(4,132,12,244)`, at glyph y=4 and
x=`188-floor(totalAdvance/2)`. Every glyph's extra advance, including the last,
is counted. Decoding the embedded FONT 0 and drawing `WHO OR WHAT` with width
73 at `(152,4)` yields **zero black-pixel differences** in the native heading
region from `theater-edit/state/actors.png`. The generated diagnostic glyph
JSON is `output/treehouse/research-theater/font0-glyphs.json`; builds should
decode the pinned executable directly.

The sentence uses FONT 1. Routine `0x2B16` wraps it at the last space that fits
the 200-pixel area. Both lines are centered independently with
`x=100+floor((200-lineWidth)/2)`. A single line has glyph top **180**. When it
wraps, the first line has top **176** and the second **186**. These come from
baselines 187,183,193 respectively and FONT 1 ascent 7 (`0x2D0E`, `0x2E84`).

The second line has an original spacing quirk. At `0x2E65`, its width is measured
starting immediately **after** the separator space. At `0x2ED8`, that separator
is restored; the draw loop begins at the separator itself. Consequently center
the second line using its text without the leading space, but render the
separator followed by that text at the calculated origin. FONT 1's space is
three pixels wide, shifting the visible second-line glyphs three pixels right.
This accounts for the 62 text-pixel differences in the parent's night capture.
The original sentence hit rectangle starts at x=188 for the invisible separator
and ends at x=215 for the second line `night.` in this capture.

Category label highlighting (`0x1FA2`, `0x200F`) fills the full label rectangle
and redraws its original monochrome bitmap centered within it. Selected colors
are indices **[6,12,14,10] in SHPL 3000**, recovered from DS:104A. The alternative
four-color mode uses DS:1052. Observed subject fill is `(255,186,0)` and action
fill `(32,24,255)`.

Shared image centering `0x6CEE` computes each coordinate as
`floor((minimum+maximum)/2)-floor(imageDimension/2)`. This differs by one pixel
in odd cases from `minimum+floor((regionDimension-imageDimension)/2)`.
Consequently the native bubbles preview, SHAP 3057 (35 by 21), is at `(269,101)`:
the helper centers it within `(97,265,122,305)`, then adds `(dx=1,dy=2)`.
All nontransparent pixels match the native `theater-places/state/bubbles.png`
at that position. Use the same centering helper for place/time thumbnails.

## Drag constraints follow-up

The actor drag call at `0x2858` passes DS:116A, rectangle `(74,103,165,261)`.
Main `0x68E9..0x694C` clamps the entire dragged rectangle inside that limit,
subtracting its width/height from the right/bottom limits. The argument 2 is a
movement threshold in pixels. The actor handler waits 15 original ticks to
distinguish a hold/drag from a quick click; a quick click invokes the subject
presentation (`0x28E9`).

Props can initially be dragged across the full screen. On release, overlay
`0x36E..0x3CF` checks overlap with DS:1172, `(53,103,165,261)`. A prop with no
overlap is removed; an overlapping prop is constrained back into the stage.
