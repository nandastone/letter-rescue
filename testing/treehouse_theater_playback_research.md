# Treehouse DOS 1.1: theater performance playback

## Evidence and address conventions

Primary sources are the original executable and data in
`output/treehouse/source/The_Treehouse_1991.zip`, its unpacked image at
`output/treehouse/disassembly/unpacked.bin`, and the original emulator replay
`output/treehouse/theater-night/frames.jsonl`. The instruction listings are
`output/treehouse/research-resources/overlay4-disassembly.txt` and
`output/treehouse/research-resources/all-disassembly.txt`.
Unless explicitly marked resident, addresses below are offsets in overlay 4.
Resident far calls `D51:xxxx` correspond to unpacked offset `0xD510 + xxxx`.
State offsets refer to the segment held at DS:4AE8; DS offsets refer to the
main data segment. Resource IDs are decimal. This note supplements
[the theater data/renderer research](treehouse_theater_research.md).

## Performer control and sequencing

The director/possum control is rectangle `(top155,left61,bottom200,right99)`.
Handler `0xD01` does the following, in order:

1. Clear any previously displayed feedback (DS:527E).
2. Save previous validation result, validate using `0x413A`, store new result
   at state:930.
3. Call `0x24F2(valid)` for the clap/idle/happy sequence below.
4. If the old result was nonzero and the new result is zero, display correction
   feedback with `0x4220(oldResult)`.
5. Call `0x259D(valid)` to present all selected categories in sentence order.
6. Draw director idle for a valid sentence or sad for an invalid sentence.
7. For invalid sentences, wait 30 ticks, play sound 1030, and display feedback
   with `0x4220(0)`.

An incomplete or badly ordered sentence still speaks its selected phrases.
It disables the actor/stage demonstrations. It must not simply reject Play.
The selected category heading, thumbnails, and colored left label remain
visible throughout normal playback. The native pointer remains at the director
in the reference replay; playback does not globally hide it.

### Director frames

`0x2453(commit,index)` restores saved background DS:59D4 then draws shape
`index+1` from loaded group 3034 at `(x61,y155)`.

| State | Index | SHAP ID | Duration / transition |
| --- | ---: | ---: | --- |
| Resting | 0 | 3035 | Before performance; after valid completion |
| Clap | 1 | 3036 | 16 original ticks, sound 1009 starts here |
| Pause | 0 | 3035 | 32 original ticks |
| Happy | 2 | 3037 | Selected after pause only when valid; retained during phrases |
| Sad | 3 | 3038 | Selected after invalid phrase presentation |

These constants and order come directly from `0x24F2`; the 16 and 32 tick waits
use `D51:56F7`. Callback/frame boundaries can add one observed tick.

### Category dispatcher

`0x259D` loops four entries of state:8EA (category order), skipping categories
whose selected index at state:40A is negative. It dispatches:

| Category | Call | Valid-sentence effect |
| --- | --- | --- |
| Subject (0) | `0x31FB(chooseUI=0,visual=valid)` | Blink actor while speaking |
| Action (1) | `0x32E9(chooseUI=0,preview=0,actor=valid)` | Run selected full actor SCR |
| Place (2) | `0x345E(chooseUI=0,visual=valid)` | Flash backdrop palette |
| Time (3) | `0x364F(chooseUI=0,blink=0,animate=valid)` | Run weather animation |

Immediately after a valid action finishes, the dispatcher sets timer 1
(DS:2018) to 120 ticks. It continues presenting place/time. Once all categories
finish, it waits for the remainder of timer 1 (`D51:5697`), then `0x3A5F`
restores the actor background and draws the actor's idle shape. Thus actor
restoration belongs to the end of the full performance, and the minimum tail
is 120 ticks measured from action completion. Place/time consume that same
running timer; do not add an unconditional two-second delay after the last
phrase. `D51:5697` checks timer expiration while polling input.

Every category sets DS:55F6 to its category number, updates its Mix Up token
(`0x43B0`), highlights its phrase (`0x3078`), performs narration/effect, waits
for sound completion (`D51:577E`), unhighlights, resets DS:55F6 to -1 and updates
the token again. The action and time routines have additional details below.

## Narration and fallback sound IDs

`0x2553(category,wait,extra)` requests resource
`3000 + 10*category + selectedIndex + extra` through `D51:E5E2`, then optionally
waits with `D51:577E`. Normal recorded phrase voices are in **DIGISND**; VOICES
is the instrument archive. Do not remap ordinary action phrases by +100.

For actions (`0x32E9`), the +100 / +3 cases are conditional on **bit 0 of
DS:2119 being clear**. In that branch, small action preview uses extra=100;
full actor performance uses extra=3 only for Bronto (actor2) taking pictures
(action5), otherwise extra=0. With bit0 set, all action narration uses extra=0.
The native Sound Blaster replay has DS:2119=3. Resident `0x19852..0x198E9`
establishes this byte as installed audio-driver capability flags, not the
sentence's speech preference. The bit0 branch also sets DS:5A1C for the action
wrapper, which changes its sound cleanup at resident main `0x4A6A`.

For invalid sentences, narration is blocking and stage demonstrations do not
run. If capability bit0 is clear, routines add a 60-tick fallback wait where
there is no visual demonstration. No browser speech synthesis is involved in
the original behavior.

## Subject blink

`0x31FB` starts narration without waiting when visual=true, then:

```text
count = 0
repeat:
    restore actor background (hide actor)
    wait 12 ticks
    draw actor idle
    if count >= 2 and no sound is active: break
    wait 12 ticks
    count += 1
wait sound
```

The minimum visual interval is 60 ticks: three hidden halves and two visible
halves. The final idle draw can coincide with the next category transition.
The loop tests all active sound via `D51:C505(0,0)`. The interruptible 12-tick
wait is `D51:56DB`; do not confuse these waits with browser render frames.

## Action

`0x2765` invokes the existing SCR engine with group `3200+100*actor`, script
index equal to selected action. The full resource ID is therefore
`3200+100*actor+action`. The original script supplies frame/timing/sound order;
there is no fixed outer duration and no outer repeat. `0x32E9` waits for its
sound cleanup, clears action highlighting, and returns to the dispatcher.
The minimum 120-tick post-action timer and final actor idle restoration are
owned by `0x259D`, not by the SCR callback. Standalone action preview calls
`0x1F0C` instead and uses the small action group.

## Place palette flash

`0x345E` only uses the visual flash when `visual && DS:206A == 5` (the native
VGA display mode). It obtains palette allocation group 8, skips the first
entry, and copies 15 RGB6 colors. The bright palette is computed componentwise
`min(63, original+6)`. Alternate bright and original at 12-tick intervals,
using the same three-cycle minimum and sound-finished exit test as the subject.
Restore the original palette before returning. Actor, UI, and text palettes
are not globally brightened.

## Time/weather

`0x364F` starts narration, runs `0x3169` when animate=true, waits for sound, then
waits **20 additional ticks** (`D51:56F7`) before unhighlighting. Its separate
blink flag is used for non-performance interactions and alternates absent/
first weather frame with 12-tick halves, following the subject loop rule.

`0x3169` uses the table at DS:10BA (see previous note). Frame numbers below are
one-based within weather group 3120:

| Time | Idle frame | Total frames | Tick interval | Performance order |
| --- | ---: | ---: | ---: | --- |
| Day | 1 | 3 | 12 | 2,3,1 |
| Night | 4 | 2 | 30 | 5,4 |
| Eclipse | 6 | 7 | 12 | 7,8,9,10,11,12,6 |
| Storm | 13 | 7 | 10 | 14,15,16,17,18,19,13 |

The final first-frame draw is restored after the intermediate frames. Weather
placement uses the place/time table already recovered in the renderer note.
At weather-animation start `D51:8806(1)` selects CURS1; after restoring the
first weather frame `D51:8806(0)` selects CURS0. Resident `0x15D16` proves this
is a cursor-resource selector, not a hide/show call.

## Exact phrase highlighting

`0x3078(category,on)` visits every sentence fragment whose category at
DS:5594 matches. Fragment rectangles are DS:5790, string offsets DS:576C,
lengths DS:52FA, count DS:568A, sentence buffer DS:55FE.

For each fragment, draw its original substring at `(left+1,top)` in the category
color, then draw the same substring at `(left,top)` in black. Category colors
are SHPL3000 indices `[6,12,14,10]`. This is a **one-pixel colored right shadow**,
not a colored phrase rectangle and not replacement-colored glyphs.
Unhighlight uses background DS:5A16 for the shifted pass, then black for the
normal pass. Both wrapped fragments of a category are highlighted together.
Text uses FONT1 with glyph origin at rectangle top (renderer baseline top+7).
Preserve original spaces, including the known leading-space wrap quirk.

## Validation and feedback

`0x413A` yields 0 valid, 2 neither subject nor action, 3 subject missing,
4 action missing, 5 action precedes subject, 6 a selected category lies between
subject and action. Where/time are optional. `0x4220(previousResult)` clears
the choice strip and renders STRL3070 indexed by
`currentResult + (previousResult in [3,4] ? 1 : 0) + 1` using one-based STRL
indexing. It draws up to two monochrome help icons from DS:13AE at coordinates
DS:13BE; invalid ordering codes5/6 also draw category tokens using proposed
correct order from `0x4498`. DS:527E then records that feedback occupies the
strip. These branches are recovered from code; missing-both and missing-action
feedback are additionally checked in the follow-up native replays below.

### Feedback resource and icon table

STRL3070 is in MODULES.DAT. The first two strings are respectively
“You fixed the mixed-up sentence!” and “You fixed the sentence!”; the second
is selected when the previous failure was missing exactly one required part.
Result2 says both parts are needed, result3/4 says one part is needed, result5
asks for subject directly before action, result6 proposes a corrected order.
The original fixed-width gaps accommodate these SHPL3000 group shape indices:

| Validation result | First icon (index,x,y) | Second icon (index,x,y) |
| ---: | --- | --- |
| 2 | 18,135,18 | 19,178,18 |
| 3 | 18,149,18 | none |
| 4 | 19,149,18 | none |
| 5 | 18,138,18 | 19,213,18 |
| 0,6 | none | none |

These are direct DS:13AE byte-table and DS:13BE signed-word-table values,
selected at `0x42BA..0x4307`. Shape indices are one-based within the loaded
UI group, not absolute SHAP resource IDs.

## Native replay references

The original replay constructs: **The baby blows bubbles in the jungle at
night.** It selects WHEN last, then clicks the director. The choice strip and
left WHEN label remain selected. All run/callback numbers below come from
`output/treehouse/theater-night/frames.jsonl`; original_tick is the recorded
original PIT-based timer. Do not interpret run as a 60-Hz original tick.

| Run | Tick | Visible transition |
| ---: | ---: | --- |
| 5519 | 4685 | Before click, idle director |
| 5521 | 4686 | Clap |
| 5541 | 4703 | Idle pause |
| 5578 | 4735 | Happy director, subject shadow begins |
| 5648 | 4795 | Action shadow, actor SCR begins |
| 5838 | 4958 | Action shadow cleared |
| 5839 | 4959 | Place shadow begins |
| 5911 | 5020 | Time shadow begins, alternate night frame |
| 5946 | 5050 | First night frame restored |
| 5986 | 5084 | Idle director; all phrase shadows cleared |

Frames at transition callbacks can capture partially completed framebuffer
writes. Stable subject alternations are hide run5579/tick4736, show5592/4747,
hide5606/4759, show5620/4771, hide5634/4783. Stable place alternations are
bright5841/4960, original5855/4972, bright5869/4984, original5883/4996,
bright5897/5008. The first bright write follows the initial phrase-shadow
callback. Choose stable callbacks when comparing a completed draw operation.

Exact image paths and phase metadata are saved in
`output/treehouse/research-theater/playback-reference-events.json`; the compact
contact sheet is `output/treehouse/research-theater/playback-phases.png`.
`playback-color-transitions.json` records phrase-color pixel counts
(subject62/action99/place88/time58 for this sentence). Director classifications
in `playback-director-transitions.json` compare the nontransparent source shape
pixels while excluding the native pointer overlap solely for classification;
they are not an assertion of complete framebuffer parity.

## Remaining uncertainty

Timing constants, IDs, sequence, phrase rasterization, and palette formula are
instruction-derived. The valid replay corroborates the major transitions and
12/30-tick intervals. Further native replays are needed for invalid ordering
feedback, audio-capability fallback paths, Mix Up correction transitions, and
input interruption behavior. None of those should be claimed pixel exact from
this single valid replay.

## Invalid feedback native follow-up

Two additional original emulator routes and their complete callback timelines
are now in `output/treehouse/research-theater/invalid-empty-a` and
`output/treehouse/research-theater/invalid-actor-a`. Inputs are recorded in their
run.json files and in the sibling invalid-empty-route.json / invalid-actor-route.json.
The former clicks the director with no choices; the latter selects the baby
then clicks the director with no action, place, or time.

Named native frames are `state/invalid-empty.png` and `state/invalid-actor.png`.
Both end with the sad possum, no selected left category label, and cleared
heading/choice artwork. The subject-only sentence remains on the bottom strip,
lowercase and without punctuation; no actor blinking occurs during its reading.

The strip clear uses the parchment background in rectangle16
`(top15,left73,bottom42,right294)` and rectangle17
`(top4,left132,bottom12,right244)`. Feedback text uses **FONT1**, black,
**glyph top20**, centered with `x=73+floor(221/2)-floor(width/2)`. This comes from
rectangle16 translated down five pixels via D51:8242 (a translation, not an
inset), then top-aligned and horizontally centered via D51:3CB0.

- Empty sentence: STRL3070 item3, width199, origin `(84,20)`.
- Actor-only sentence: STRL3070 item5, width170, origin `(98,20)`.

All spaces in the original strings are retained, including seven-space icon
gaps. Decoding FONT1 and comparing predicted black glyph pixels against each
native strip, excluding only the icon bounding rectangles, yielded **zero
missing or additional glyph pixels** for both cases. This verifies text origin,
width, font, and spacing. The icon placements in the preceding table match the
native screenshots: SHAP3018 at135,18 and SHAP3019 at178,18 for empty; SHAP3019
at149,18 for actor-only.

| Empty route run/tick | Event |
| --- | --- |
| 4051 /3428 | Clap3036 |
| 4070 /3444 | Idle3035 |
| 4108 /3477 | Sad3038; no selected phrases to read |
| 4146 /3509 | Feedback text and icons visible |

| Actor-only route run/tick | Event |
| --- | --- |
| 4441 /3762 | Clap3036 |
| 4460 /3778 | Idle3035 |
| 4497 /3810 | Subject phrase highlighted; actor remains visible |
| 4551 /3856 | Subject phrase unhighlighted |
| 4552 /3857 | Sad3038 |
| 4590 /3889 | Feedback text and icon visible; category selection cleared |

Exact image paths for every unique post-click frame are saved in
`invalid-empty-events.json` and `invalid-actor-events.json` beside the routes.
The original code requests a 30-tick post-sad wait; the named callback first
showing finished feedback is 32 ticks later due to resource loading/drawing.
No runtime code was changed for these captures. Invalid ordering and correction
feedback, plus audio fallback paths, still require additional native coverage.

## SCR cursor visibility follow-up

The resident main wrapper `0x415F` delegates to `0x419D`. Its cursor lifecycle
is explicit:

1. `0x41D5..0x41D9`: select CURS1 before loading/preparing the script resource.
2. `0x442B`: call D51:857A, resident `0x15A8A`, to hide the software cursor.
3. `0x4430..0x4456`: select CURS0 while hidden for ordinary theater playback.
   Other engine modes use CURS3/4 according to DS:15E8; ordinary theater uses0.
4. Execute the SCR and clean up sound/background/resources with cursor hidden.
5. `0x4B3D`: call D51:8822, resident `0x15D32`, to show the cursor again.

Thus the busy cursor is visible during resource preparation but the pointer
is hidden throughout the actor animation. Choosing CURS0 alone does not make
it visible: hide/show are separate reference-counted routines. Weather uses
CURS1 while visible and does not call this SCR wrapper's hide routine.
This explains the remaining pointer-only differences in the parent's 38-state
playback rendering comparison. Rendering-state order and actual event timing
remain distinct claims; a matching ordered frame sequence alone does not prove
identical PIT timing.
