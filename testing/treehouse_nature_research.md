# Treehouse nature activity reconstruction — 2026-09-27

Primary sources: pinned DOS v1.1 executable/overlays and original `modules.dat`.
Addresses below are byte offsets in **overlay 2's body**, except where explicitly
identified as main-image offsets. The body starts at EXE file `0x34C00` and is
16,221 bytes. Static browsing aid:
`output/treehouse/research-resources/overlay2-disassembly.txt`.

The original activity has an animal exploration/collage screen and a separate
animal identification game. Treating it as one generic sorting puzzle would
omit the original interaction model.

## Entry and original reference

Interior hotspot 2 is `(top99,left122,bottom119,right147)`. A safe logical point
is `(134,108)`. Main routine `0x132D` reaches overlay entry zero through the
encoded overlay call at main `0x1352`. The retained native capture is
`output/treehouse/demo-nature/state/nature.png`, with RAM and a complete frame
sequence in the same capture directory.

Overlay entry zero loads SHPL 5000, 5100, 5200, 5300 for animals; SHPL 5400 for
screen graphics; SHPL 5650 for controls. STRL 5000 determines animal count (92).
It constructs the exploration screen with `0x0F66` and immediately enters its
input loop; there is no mandatory options dialog before exploration.

## Exact first screen reconstruction

`output/treehouse/research-nature/render.py` independently reconstructs the
native reference using original resource graphics, font, cursor and the
operations below. The resulting `reconstructed.png` matches **64,000/64,000 RGB
pixels**, including the pointer at `(134,108)`. No reference pixels are used in
constructing that image. This confirms one static state, not temporal parity.

Initial native state from RAM, segment corresponding to main image `0x31690`:
`+B6=0` (day), `+B8=0` (backbone attribute), `+BC=0` (no backbone), `+BA=3`
(insects), and `+CA/+CC=0` (empty day/night scenes).

| Operation | Resources / coordinates |
| --- | --- |
| Opaque screen background | modules SHAP 5401 / SHPL 5400, `(0,0)` |
| Seven attribute buttons | SHAP 5651..5657 / SHPL 5650, centered in rectangles 1..7 |
| Attribute button background | SHPL 5650 color 8 for selected; color 2 otherwise |
| Current attribute value | Original bitmap font, black text centered in rectangle 12 |
| Class icon cells | Available white; selected SHPL 5650 color 8; unavailable EGA color 7 `(170,170,170)` |
| Class icon | SHPL 5650, centered in rectangles 14..23; mapping below |
| Current class name | STRL 5208+dayNight, selected class+1; centered horizontally, top at y=99 |
| Matching animal miniatures | Original animal palettes; flow layout from `(8,107)` |
| Bottom three controls | SHAP 5659..5661 / SHPL 5650, centered in rectangles 9..11 over palette color 2 |
| Day environment | SHAP 5501 / SHPL 5500, `(127,4)` |
| Exit icon | TH SHAP 8 / SHPL 6, `(304,1)` |

The original centering helper uses `floor((left+right)/2)-floor(width/2)` and
its vertical equivalent. It is not always equal to `left+floor((right-left-width)/2)`.
All sprite overlays here use source-index-zero transparency.

For night, use SHAP 5501 / SHPL 5501 at `(127,4)`, clipped to
`(top39,left127,bottom196,right317)`, then SHAP 5511 / SHPL 5510 at `(128,4)`.
The day/night source rectangle is `(4,127,196,317)`. These operations are in
`0x0CD3..0x0DEC`; night composition awaits an independent native frame check.

## Tables for implementation

`output/treehouse/research-nature/tables.json` contains extracted, structured
records. Read the binary at build time or preserve their provenance if adopting
this JSON as maintained data.

Animal metadata begins at **main image `0x30218`**, 92 records, 12 bytes each:

| Byte | Meaning |
| ---: | --- |
| 0..6 | Seven attribute value indexes |
| 7 | Active time: 0 day, 1 night |
| 8 | Animal class index in STRL 5208 (day) or 5209 (night) |
| 9 | Graphics group 1..4; palette ID = `4900+100*group` |
| 10 | Large image relative index; actual SHAP ID = palette ID + byte 10 |
| 11 | Miniature image relative index; actual SHAP ID = palette ID + byte 11 |

Animal name is STRL 5000 at zero-based animal index. Its fact strings are
STRL `5100+animalIndex`; read strings directly from original resources.

Seven visible exploration attributes correspond to STRL 5300 entries 0..6:
backbone, body temperature, wings, legs, skin, breathing organ, food. Values
come from STRL 5200..5206. The identification game also uses the eighth
attribute, active time, from STRL 5207.

Class names come from STRL 5208 (9 day classes) or 5209 (10 night classes).
For ordinary icons, the **relative** SHPL 5650 indexes by class are:

- Day: `[20,21,25,23,24,26,22,27,30,20]` (the final unused slot is disabled).
- Night: `[20,21,25,23,24,26,28,27,29,31]`.

Actual SHAP is `5650+relativeIndex`. Original table is main image `0x30898`,
interleaved bytes `[day0,night0,day1,night1,...]`, each storing index minus 20.

Original category-icon exceptions at `0x122A..0x12F9` use an animal miniature
instead of the generic icon:

| Time | Class | Attribute / value | Animal index |
| --- | ---: | --- | ---: |
| Night | 0 | Legs / two | 60 (Bat) |
| Night | 0 | Wings / has wings | 60 (Bat) |
| Night | 7 | Skin / smooth skin | 70 (Slug) |
| Day | 0 | Legs / two | 63 (Human) |
| Day | 6 | Legs / four | 79 (Turtle) |
| Day | 6 | Skin / armor | 79 (Turtle) |

## Filtering, selection and facts

Only the currently selected attribute applies as a filter; previous attribute
values are remembered independently but are not combined into a multi-filter.
Click a different attribute to select it. Click the selected attribute again,
or click the value text, to cycle that attribute's value modulo its STRL count.
Every filter change clears the selected class and its animal list.

A class is enabled if at least one original animal matches the current time,
selected attribute and value (`0x1626`). Clicking an enabled class selects it,
then `0x13CA` enumerates matching animals in original table order. Miniatures
start at x=8,y=107; when `x+width>122`, set x=8 and advance y by the maximum
height of the previous row. Horizontal spacing is one pixel. Dynamic hitboxes
are each miniature's actual dimensions, retained separately from static UI
rectangles.

Selecting a miniature highlights it, changes the value line to its name, and
shows a fact in the upper animal-list rectangle. Original fact selection uses
STRL index 0, the resource helper's random-entry convention. It preserves the
previous list to restore when dismissing the fact (`0x1D3E`, `0x1E0E`).

## Collage interaction

Animals can be dragged from the miniature list onto the environment. Source
`0x059E..0x07C5` uses the large image dimensions and initially centers it under
the pointer. Drops must overlap the environment's interaction rectangle
`(top5,left131,bottom195,right315)`, then the sprite rectangle is constrained to
fit inside it. There is a 40-animal limit **per day/night scene**.

Existing objects are hit-tested from the last placed backward (`0x07D1`), can
be dragged to a new position, and are removed if dropped wholly outside the
environment. The objects have separate day/night arrays; changing the sun/moon
preserves both collections. Clicking the sun/moon (rectangle 13) toggles time
only when no placed animal is hit at that point.

Bottom controls: index 9 invokes print handling (disabled if native printing
unavailable); index 10 clears the active scene after confirmation, with a Ctrl
branch for clearing both; index 11 enters the separate identification game.
The exploration screen has no recovered score or win condition: it is a
filterable encyclopedia and animal collage.

Original ambient movement alternates large SHAP index and large SHAP index+1.
After the 240-tick interaction idle countdown expires, the event loop examines
objects round-robin and toggles their alternate-image flag when their scheduled
time arrives (`0x0BAF..0x0C85`). Scheduling routine `0x1924` uses random(360)+120
ticks for flag 0 and random(120)+30 ticks for flag 1. Exact PRNG timing and
repaint scheduling are not yet independently compared.

## Static exploration rectangles

Original table: main image **`0x30668`**, 27 records of four signed words,
`(top,left,bottom,right)`, with exclusive bottom/right.

| Index | Bounds | Meaning |
| ---: | --- | --- |
| 0 | `(1,304,23,320)` | Exit |
| 1..7 | `(12,9+16*i,25,24+16*i)` for i=0..6 | Attribute icons |
| 8 | Duplicate of 7 | No-op in exploration dispatch |
| 9 | `(175,18,195,42)` | Print |
| 10 | `(175,53,195,77)` | Clear |
| 11 | `(175,88,195,112)` | Identification game |
| 12 | `(31,4,42,126)` | Cycle attribute value |
| 13 | `(7,142,40,176)` | Day/night toggle |
| 14..18 | `(50,5+25*i,67,25+25*i)` for i=0..4 | Class row 1 |
| 19..23 | `(72,5+25*i,89,25+25*i)` for i=0..4 | Class row 2 |
| 24 | `(98,6,166,124)` | Animal list / heading |
| 25 | `(5,131,195,315)` | Environment manipulation |
| 26 | `(48,3,91,127)` | Dismiss selected fact |

## Identification game: recovered rules and next rendering work

Exploration button 11 calls `0x2A2F`. This loads shared SHPL 5600 and
groups 20100 (player) and 20200 (player portrait/options) from the selected
BOY/GIRL archive; friend groups 22100/22200 and robot groups 24100/24200
come from TH.DAT. The active
opponent animation group is `20100+2000*role`, where role 0 is the selected
character, 1 the friend and 2 the robot. Group 5600 is in `modules.dat`.

The options screen `0x22D3` offers **Play with a friend** / **Play with the
robot**, per-human **Help for ...** checkboxes, and PLAY. This wording is baked
into SHAP 5404 and 5405, not guessed from gameplay. The retained nature RAM has
opponent role 2, player help=0, friend help=0, robot help=1. Changing the opponent
does not immediately start the game; PLAY (options rectangle 10) exits the
options loop with return zero.

Options use eleven rectangles at main image `0x301C0`; the panel is SHAP 5404
/ SHPL 5400 at `(6,3)`, with SHAP 5405 at `(34,49)`. Friend selection shows a
second help label at `(34,67)`. Options rectangles, quiz rectangles, and panel
bounds are included in `research-nature/tables.json`.

Quiz screen uses SHAP 5402 / SHPL 5400 at `(0,0)`. Its 39 rectangles begin at
main image **`0x30740`**. Setup `0x1A8D` adds SHAP 5609 / SHPL 5600 at `(171,3)`;
then SHAP 5601 at `(181,108)` and `(252,151)` for the player positions. It adds
original exit, back/options controls, and eight vertical attribute buttons.
The initial screen, options modal, and first human turn have now each been
independently composed with **zero differing pixels out of 64,000**; see below.

### Candidate generation and state

Routine `0x2084` builds eight candidates independently for each of two players.
Each candidate is randomly selected from all 92 animals. Before accepting a
candidate, it compares all **eight** attribute bytes to each prior candidate;
if all eight match, it rejects the choice and retries. This rejects duplicate
attribute vectors, including different species with identical answers. Thus
all candidates can be distinguished by the available questions.

Each player gets a random secret candidate index 0..7. Both candidate masks
start at `0xFF`; both previously asked attribute masks start at zero. Selection
of the starting player is random except robot mode initializes player index 1.
Original state locations:

| State | Location |
| --- | --- |
| Candidate animal IDs, player-major, 8 each | segment `3169`, offset `0006`, u16 |
| Secret candidate index, 2 players | segment `3169`, offset `0992`, u16 |
| Current player 0/1 | main DS `5250` |
| Asked attribute mask, 2 players | main DS `52DC`, u16 |
| Remaining candidate mask, 2 players | main DS `52EE`, u16 |
| Available questions this turn, 8 flags | main DS `52A2`, u16 |
| Guess mode | main DS `557C` |
| Opponent role | segment `3169`, offset `03FE` |
| Help flags for roles 0,1,2 | segment `3169`, offsets `0400,0402,0404` |

Segment addresses are before DOS relocation; actual live pointers must account
for executable load segment and the libretro memory-map translation.

### Turns, questions, elimination and guesses

At the turn action (`0x2F8F..0x304B`), the game switches current player, clears
the eight available-question flags, and picks **three distinct
attributes**, preferring unasked attributes until the mask is exhausted.
The selection helper is passed a temporary copy of that player's asked mask. These
three attributes are visually enabled on the right-hand illustration.

Clicking a left-side attribute button (hotspots 1..8) is informational: it
shows STRL 5300's heading and STRL 5310's explanation. Asking a question uses
right-side hotspot 12..19 and must be one of the three available attributes.
The answer is the secret animal's original attribute value. The asked mask
is updated, and the answer is displayed using STRL 5200+attribute.

If help is enabled for the current role, the code at `0x3363..0x3427`
automatically clears each remaining candidate whose selected attribute value
differs from the secret's. Otherwise the player can manually toggle candidate
cross-out controls (hotspots 28..35). Those toggles do not themselves alter
original animal data.

Ordinary candidate clicks (20..27) display its identity/class and the selected
available attribute information. In guess mode (`DS:557C != 0`), the clicked
candidate must still be in the remaining mask. At `0x365E..0x367D`, comparing
its index with the player's secret index determines success and invokes the
winning routine `0x39E4`. Wrong guesses play the role's offset-11 animation;
with help enabled they remove the guessed candidate from the remaining mask
(`0x36BB..0x36EE`). Play continues. The robot asks randomly among available
questions, or guesses when only the secret's bit remains.

The game also has original reveal/turn presentation and celebration scripts,
which must be recovered before claiming a complete faithful quiz. Above are
static control-flow findings, not a report that the quiz has been rebuilt or
that every branch has a native reference capture. In particular, PRNG
reproduction, right-side animation
callback behavior, private information presentation between human turns, and
all presentation timing remain work.

## Native capture and exact composition follow-up

Three independent static reconstructions match the original in all 64,000
pixels, including the cursor. Scratch scripts and output PNGs live under
`testing/output/treehouse/research-nature/`:

| Original state | Independent renderer | Differing pixels |
| --- | --- | ---: |
| `quiz-capture/state/quiz-ready.png` | `quiz-render.py` | 0 |
| `quiz-capture/state/quiz-options.png` | `options-render.py` | 0 |
| `quiz-roll-capture/state/quiz-roll.png` | `quiz-roll-render.py` | 0 |

The renderers decode original resource assets; the post-roll renderer reads
candidate IDs and question flags from original RAM as state inputs, not pixels.
This establishes static composition, not animation timing or PRNG parity.
Separate fresh captures can yield different candidate arrays even with matching
input prefixes, so matching route names alone does not identify matching state.

### Initial quiz screen

Initial empty cards are correct. `DS:529E = -1` waits for the first die action.
Coordinates in this list are `(x,y)`; rectangles retain `(top,left,bottom,right)`.

- SHAP 5402 / SHPL 5400, opaque at `(0,0)`.
- SHAP 5651..5658 centered in quiz rectangles 1..8, fill SHPL 5650 index 2.
- SHAP 5609 / SHPL 5600 at `(171,3)`.
- SHAP 5601 / SHPL 5600 at `(181,108)` and `(252,151)`.
- Back SHAP 5665 at rectangle 9 origin `(284,1)`; options SHAP 5664 at
  rectangle 11 origin `(265,1)`, both SHPL 5650.
- TH SHAP 8 / SHPL 6 at `(304,1)`.
- Die frame SHAP 5669 opaque `(137,8)`; SHAP 5667 opaque `(141,12)`.
- Original cursor AND/OR masks: main image `0x310B4` / `0x310D4`, drawn at
  pointer coordinates plus `(1,1)`.

### Options modal

Draw the quiz base, then SHAP 5404 / SHPL 5400 at `(6,3)`, then SHAP 5405
at `(34,49)`. TH SHAP 24202 / SHPL 24200 is centered in options rectangle 2
`(14,11,39,32)` with fill SHPL 5400 index 10 `(255,235,195)`. BOY SHAP 20201
/ SHPL 20200 is centered in rectangle 7 `(46,106,62,120)` with the same fill.
The selected robot checkbox is monochrome TH SHAP 9 at `(35,32)`, foreground
EGA light red `(255,85,85)`, transparent index zero. This recipe is for the
captured boy/robot/default-help state; friend selection uses its corresponding
original resource groups and the second help row.

### Active human turn

Start with the quiz background and controls but omit the die. Draw each of
the current player's eight candidate miniature assets centered in rectangles
20..27 on white. The cross-out controls use SHAP 5662 centered in rectangles
28..35 with fill SHPL 5400 index 6 `(113,101,89)`.

For each enabled question, the following table gives the relative SHAP ID in
SHPL 5600. If nonzero, fill its question rectangle (12+attribute) white and draw
that background shape at the rectangle's origin. Then draw the attribute icon
(SHAP 5651+attribute, SHPL 5650) at its listed position.

| Attribute index | Background SHAP relative to 5600 | Icon `(x,y)` |
| ---: | ---: | --- |
| 0 Backbone | 0 | `(296,65)` |
| 1 Body temperature | 12 | `(227,76)` |
| 2 Wings | 14 | `(263,58)` |
| 3 Legs | 11 | `(199,64)` |
| 4 Skin | 13 | `(183,176)` |
| 5 Breathing organ | 0 | `(236,14)` |
| 6 Food | 0 | `(236,112)` |
| 7 Time | 10 | `(190,21)` |

Source tables: main image `0x308AC` (eight u16 background IDs), `0x308BC`
(eight signed word `(y,x)` coordinate pairs). Initial boy pose is BOY SHAP
20101 / SHPL 20100 at `(138,47)`, from SCR 20100's first pose. Guess frame
SHAP 5669 is opaque `(137,82)`; question mark SHAP 5666 is centered in the
inset rectangle `(86,141,103,158)` on white.

### Questions and original state observations

Resident question selection helper `0D51:4201` (main image `0x11711`) picks
`random(count-1)` as its starting index, then probes forward cyclically while
the corresponding bit is set. It marks the selected bit. If it reaches its
starting position after finding every bit set, it resets the mask to the
supplied reset mask (zero here), then continues. The caller makes three
selections using a local copy of the asked mask and additionally rejects any
question already enabled this turn. Consequently the distribution is not a
uniform draw from remaining questions, and questions can repeat after
exhaustion. Exact PRNG reproduction remains open.

Captured `quiz-answer-capture/state/quiz-answer` has the human body-temperature
answer **Cold blooded**. `DS:529E = 1`, asked mask `0x02`, remaining mask `0xFF`:
Help was off. Next die action yields `robot-answer`, with **No legs**, phase 1,
robot asked mask `0x08`, remaining mask `0x04`. That single remaining bit is the
robot's secret candidate. This confirms both normal end-of-turn behavior and
automatic elimination for the robot. These captures were generated by
`quiz-answer-route.json`; original native callbacks and state files accompany
the PNGs.

### Exploration fact text: exact native layout

`nature-explore/state/animal.png` displays deer, STRL 5101 **entry index 2**:

> A male deer's antlers are made of bone.  They are shed and replaced every year.

The two spaces after the first sentence are preserved. FONT 1 starts at
`(5,49)` with line advance 10 and wraps as follows:

```text
A male deer's antlers are
made of bone.  They are
shed and replaced every
year.
```

`fact.py` produces **zero differing pixels across the 124 by 43 fact rectangle**.
Resident text wrapper `0D51:3CED` (main image `0x111FD`) applies horizontal inset
2 and vertical inset 1 for this alignment, so fact rectangle `(48,3,91,127)`
becomes width 120 at `(5,49)`. FONT 1 header fields yield line advance
`7 + 2 + 1 = 10`. Core wrapping at main image `0x159A2` permits breaks after
hyphens as well as spaces. Preserve original inter-word spacing and measure
with the original glyph widths.

### Exact normal answer and completed win screens

Two more independent reconstructions now match all 64,000 pixels:

| Original state | Independent renderer | Differing pixels |
| --- | --- | ---: |
| `quiz-answer-capture/state/quiz-answer.png` | `quiz-answer-render.py` | 0 |
| `quiz-win-capture/state/correct-guess.png` | `quiz-win-render.py` | 0 |

Normal answer rendering uses the quiz base, cards and markers, without a
character, active question decorations, or guess control. The die returns.
For each answered attribute, FONT 1 black text starts at `x=30,y=7+14*index`.
Routine `0x1C01` derives its answer slot from that attribute's icon rectangle,
shifting left/right by 23 then extending its width by 83. The answer is vertically
centered in that row. Footer rectangle DS `0x0DBE`, main image `0x32F8E`, is
`(125,8,135,164)`: center the answer text at horizontal center 86, glyph y=126.
The original affirmative thumb SHAP 5662 / SHPL 5650 sits at
`(86-floor(textWidth/2)-12,125)`. This is the captured affirmative answer state;
other feedback branches must use their original markers, not assume thumbs-up.

The native winning capture was made by restoring
`quiz-answer-capture/state/robot-answer.state`, clicking die, clicking the guess
control, reading the resulting original secret index (4), and clicking that
candidate. **No original RAM was modified.** `capture-win.py` records the
restored state hash, content/core hashes, chosen target, and every follow-up
input action in `quiz-win-capture/run.json`. Native `DS:55EA = 2` confirms the
original win branch. The secret in this capture is animal 44, Dragonfly.

The completed winning screen retains the current cards/markers and shows all
eight secret-animal attribute values at `x=30,y=7+14*index`. Footer text is the
animal's name, centered in `(125,8,135,164)`, without a thumb. The die frame
SHAP 5669 remains at `(137,8)`; its inset `(12,141,29,158)` is white and contains
TH SHAP **922 / SHPL 900**, centered. There is no character in the completed
captured frame.

Win routine `0x39E4` plays shared SCR 5600 using current-player argument,
reveals the selected animal's entire attribute set via `0x3E6E`, draws its
large image via `0x3B56`, then plays role SCR `20100+2000*role` and sets result
phase 2. The animal is horizontally centered, top-aligned in its player's
rectangle:

| Player | Reveal rectangle | Final flattened shrub |
| ---: | --- | --- |
| 0 | `(108,180,153,243)` | SHAP 5608 at `(181,134)` |
| 1 | `(151,251,196,314)` | SHAP 5608 at `(252,177)` |

The full original shrub animation is in `disassembly/scripts.json`, SCR 5600.
Its final shape 8 is offset `(1,26)` from the script's top/left. The opposing
player's shrub remains the initial SHAP 5601.

There is a subtle original restore order that matters for pixel fidelity.
Guess setup at `0x30E3` saves the animation backdrop in handle `DS:5742`. After
SCR 5600 flattens the shrub, win code `0x3A60..0x3A64` **restores that earlier
backdrop**, then draws the secret animal and captures a new backdrop for the
celebration. In the captured human win, the restored rectangle is
`(115,238,147,261)`. It overlaps and removes exactly 16 pixels from the flattened
shrub. This is explained by the original rectangle restore, not a per-pixel
patch. The independent renderer restores a region of its own decoded background;
it never copies original screenshot pixels.

Original backdrop rectangles begin at DS `0x0D76` / main image `0x32F46`:

| Role / variant | Bounds |
| --- | --- |
| Human | `(115,238,147,261)` |
| Friend | `(139,231,166,259)` |
| Robot | `(137,229,170,256)` |
| Alternate human | `(112,238,147,261)` |

This recipe establishes a complete correct-guess static outcome. The native
capture also retains every intervening frame for subsequent animation parity.
