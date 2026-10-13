# Treehouse room, calendar, character needs, and telescope follow-up

Primary evidence: pinned original DOS v1.1 image `output/treehouse/disassembly/unpacked.bin`, resource archives in `extracted-v2`, and new ordinary-input native captures under `output/treehouse/research-room-followup/`. Addresses are main-image offsets unless marked DS-relative. No runtime source was edited by this investigation.

## Scope corrections

Two earlier labels were unsupported by original art/control flow:

- The fourth telescope picture is **the robot's prize shelf**, not a bird feeder or birdcage. Module palette3600 and SCR3610 render the robot. Palette960 shapes967..972 are robot-related prizes collected through the robot's victory chooser. The shelf is visible in `telescope-a/state/view-0.png`.
- The resident hunger/fatigue state found here belongs to the **selected boy/girl**, with eating, resting, and speech animations from that character archive. This is not evidence for a separate virtual-pet simulation. There are ambient nest/bird interactions, but no separate pet hunger/growth system has been established.

These distinctions matter: reconstruct the source-supported character and environmental interactions rather than invent a generic pet activity.

## Native captures

`room-clicks-a` restores `entry-verified-a/state/after-click.state` independently for16 clicks. Its `run.json` records each restore and exact mouse input; no RAM mutation occurred. Settled states and intervening frame sequences are retained. Sheet `room-clicks-a/sheet.png` is an overview only, not runtime art.

`telescope-a` uses four ordinary consecutive telescope visits, retaining all frames and snapshots. View order in this run:

| Capture | View |
| --- | --- |
| view-0 | Robot's shelf |
| view-1 | Planets |
| view-2 | One-eyed green alien |
| view-3 | Birdbath |

`calendar-render.py` independently reconstructs the calendar content rectangle for January1 and January2. January2 and January1 via the date-strip input each match all pixels in the121x70 content rectangle. The direct-flap January1 capture includes the pointer over the text (86 pixels) that the content-only recipe intentionally does not compose; this is not a claim of a full-screen match.

`telescope-render.py` independently reconstructs the complete empty-prize robot-shelf screen with the still robot, original cursor and exit icon: **0 differing pixels over320x200**. Original assets/source operations only; no captured pixels used as input.

## Room hotspot dispatch

Table: main0x2E938,31records of four signed16-bit words `(top,left,bottom,right)`, exclusive bottom/right. Dispatch: main0x1804,30u16 entries corresponding to indices1..30. Structured transcription: `research-room-followup/tables.json`.

| ID | Region | Bounds | Handler / behavior |
| ---: | --- | --- | --- |
|0|Exit ladder|(177,242,200,305)|Leave room|
|1|Piano|(175,7,200,106)|0x12F0 music|
|2|Nature booklet|(99,122,119,147)|0x132D nature|
|3|Calendar flap|(20,160,40,283)|0x156A toggle daily-history panel|
|4|Cloud picture|(30,163,80,283)|0x13E1 cycle7clouds; blocked while calendar open|
|5|Telescope|(102,167,157,228)|0x141D telescope|
|6..12|Chalk / eraser|See drawing research|0x16F9 tools|
|13|Theater curtain|(121,49,145,77)|0x1367 theater|
|14|Board game|(181,138,200,223)|0x13A4 board game|
|15|Digital clock|(108,92,118,114)|0x1479 speak current time|
|16|Small pinwheel/radio area|(129,118,146,145)|0x145C sound1013, fallback20000|
|17|Date corner|(21,132,38,154)|0x1521 previous/next day, redraw/speak date and open history|
|18|Date strip|(24,58,35,134)|0x1565 speak date and toggle history|
|19|Naptime note|(120,2,156,36)|0x15E2 speak wake time when sleeping, otherwise generic time request|
|20|Naptime time display|(140,4,153,34)|No direct action|
|21|Spider web|(6,21,27,54)|0x1588 ->0x604F, TH SCR1080/SHPL1080|
|22|Character portrait|(27,4,62,41)|0x159F ->0xD02C character/status speech|
|23|Small nest interior|(81,237,94,260)|0x15A7 ->0x3C12 nest chirp overlay|
|24|Whole nest|(81,211,104,283)|0x15DA ->0x4CCC TH SCR1250/SHPL1250|
|25|Chalkboard clear control|(86,49,97,59)|0x167B confirmation dialog|
|26|Fruit A|(118,247,127,257)|0x1611 draggable object17|
|27|Fruit B|(117,239,127,248)|0x1611 draggable object18|
|28|Fruit C|(119,261,133,274)|0x1611 draggable object19|
|29|Fruit D|(117,246,131,264)|0x1611 draggable object20|
|30|Family portrait|(15,286,91,318)|0x15AF character animation31, or sound20001 during sleep|

Hit-testing iterates table order, so overlapping areas use the earlier index. Some interactions first close calendar or stand the character up. The character and movable objects are handled by earlier branches of the room loop, before this fixed hotspot table. The fruit regions initialize object records and enter the general drag handler; merely clicking the bowl should not immediately consume food.

## Calendar/history panel

Dates are retained as DOS date fields: DS52CC day(byte),52CD month(byte),52CE year(word),52D0 weekday(byte). Time/date are retrieved through DOS runtime helpers; the fixed January1,1992 display in the demo is a reference fixture, not the original behavior.

Daily original history is already in TH STRL1001..1012. Each month contains heading/body pairs in day order: heading index2*(day-1), body index+1. This includes the complete original wording, not externally researched replacements. January1 is DEAR DIARY; January2 is MISSED THE MOON.

- Panel rectangle DS021E = `(28,162,110,283)`.
- Unrolling animation0x3515 draws7heights38,48,58,68,78,88,98, waiting2ticks each. It clears white above the lower edge and draws TH SHAP1201/SHPL1200 at `(162,height)`.
- Fully open content is white `(28,162,98,283)`. Heading FONT1 black centered at x222,y28. Body FONT1 black x164,y39, width118, line step10. Text is clipped to the content region. The content/body rectangle is derived by left+2,top+11,right-1.
- Closing0x341E renders lower-edge heights88,78,68,58,48,38,28, restoring original saved background each step,2ticks each.
- Open state DS5262=1.
- Date strip0x3F44 formats `TH STRL500[month-1] + space + day + ', ' + year`, FONT1 redEGA12 centered in hotspot18. January1,1992 gives x71,y25.
- Corner click compares `x-left` to `bottom-y`: if `x-132 < 38-y`, go to previous date, otherwise next. It closes an open panel, moves the day, redraws/speaks date, and reopens history.
- Previous date lower bound is **January1,1980** (`0x40C7..40E6`). Month/year changes use DOS validity checks; increment and decrement routines temporarily validate dates then restore the actual DOS date. The browsed history date should therefore not overwrite the host operating-system date.
- Clicking the cloud increments selection modulo7 only when the panel is closed, plays sound1044, redraws cloud. Cloud shape=TH171+index/pal170; centerx223,centery55 (`0x24C2`,0x22E1). The small calendar lower-edge marking is redrawn over it at(162,28).

## Clock and spoken time

Source0x2F86 updates displayed digits when the DOS minute changes; forced redraw bypasses that check. Twelve-hour display formula `hour12 = hour24 % 12 || 12`.

Clear hotspot15 `(108,92,118,114)` black. Opaque TH/pal1200 glyphs alltop110:

- x95: SHAP1227 ifhour12>9,otherwise1226(blank).
- x97: SHAP1215+(hour12%10).
- x102: SHAP1225(colon).
- x104: SHAP1215+floor(minute/10).
- x109: SHAP1215+(minute%10).

Clock clicking normally invokes resident spoken-time routine0xCD40(hour,minute,0). The alternative that edits DOS hour/minute is guarded by the executable's debug flag DS55EC plus modifier state, and should not be mistaken for normal play.

The naptime note is blank when the character is awake (earlier fidelity research). Sleeping sets a wake-up time to current time+2minutes ifseconds<=30,else+3minutes, carrying the hour modulo24 (`0x4D6F`). When displayed minute reaches the wake minute, normal clock servicing wakes the character via0x38BC; modal states defer this through DS5826.

## Character hunger/fatigue and drag objects

Source0x5578,0x564E,0x57D9,0x581A,0x9495..96C5.

| State | Storage | Behavior |
| --- | --- | --- |
| Hunger | DS5282,1..5 | Normal advancement every7200ticks(2minutes); at3 warning animation13; at4+ urgent animation14 and repeat every3600ticks |
| Fatigue | DS581C,1..5 | Normal advancement every14400ticks(4minutes); at3 animation15; at4+ urgent animation16 and repeat every3600ticks |
| Character pose | DS5688 |0standing,1/2other poses,4sleeping; exact labels for1/2 need native capture |

Warnings advance the counter, capped5. If the other need is already5, a competing urgent counter is reduced before the final increment. Cross-counter schedule helpers0x575D/579B ensure at least600ticks between pending urgent reminders. Need setters clamp1..5 and restart their normal schedule.

Fruit objects17..20 dropped into the current character rectangle:

- If hunger>1, play character animation objectID-16 (1..4), subtract2hunger clamped1, increment fatigue clamped5.
- If hunger==1, play animation objectID-11 (6..9), consuming/removing the dragged object without reducing hunger further.
- These paths are disabled while sleeping.

Object8(the pinwheel-sized sleep object at106,132) dropped on the character starts sleep iffatigue>=4,otherwise plays character animation17. Other collectible objects have distinct handlers; the complete object-interaction matrix remains beyond this slice.

Movable object array DS5830: stride20bytes, countDS556C. Each record begins type(u16),quantity(u16),roomFlag(u16),rectangle4*i16,backgroundHandle(u16),scheduledTime(u32). Creation0x8637 copies initial rectangles from DS07BE+8*type for room objects and DS0866+8*type otherwise. Picking fruit selects types17..20. Every object should retain this domain identity instead of being rendered as an interchangeable icon.

Character action selector0x392B resolves SCR20500+action for chosen BOY/GIRL, adding100or200 for certain alternate poses unless the byte exemption tableDS01F6[action] says otherwise. Therefore simply playing20500+action for all states is insufficient.

## Nest and spider: environmental interactions

- Spider hotspot21 closes the calendar ifneeded, then TH SCR1080/SHPL1080. Native bounds(0,0,84,283), with existing sprite interpreter and original backdrop handling. This is a one-shot environment animation.
- Nest outer hotspot24 clears its local rectangle to the sky color DS59D6, captures backdrop, runs TH SCR1250/SHPL1250, releases saved background, restores normal idle scheduling. Bounds(74,207,104,281).
- Inner nest hotspot23 plays sound1041 and alternates TH SHAP920/921(pal900) at(241,82),8ticks each, while sound plays and up to180ticks; restores original nest backdrop afterward (`0x3C12..3D2E`). This is not a feeding/growth interaction.
- Family portrait hotspot30 ordinarily requests character action31; sleeping branch plays sound20001.

## Telescope: exact fourth-view recipe and reward linkage

All four view names supported directly by visible assets:

| Index | Suggested readable label | Original background | Animation |
| ---: | --- | --- | --- |
|0|The planets|TH SHAP781/SHPL780|TH SCR800/pal800|
|1|A little alien|TH SHAP783/SHPL782|TH SCR820/pal820|
|2|The birdbath|TH SHAP785/SHPL784|TH SCR840/pal840|
|3|The robot's shelf|TH SHAP787/SHPL786|MODULES SCR3610/pal3600|

The original contains no recovered title strings for these scenes. These are descriptive labels grounded in the original art, not claimed original text.

Selection0x2534 uses the shared random-mask helper, maskDS52F6, range4: unseen views are preferred until the cycle exhausts. This should not always open a fixed view2.

For view3:

1. Start black320x200. Clip scene composition to `(34,77,168,243)` (DS0370).
2. Draw SHAP787/SHPL786 centered in the full320x200 screen. (Black remainder stays outside circular view.)
3. For i0..5 whose DS55F8+i byte is nonzero, draw TH SHAP967+i /SHPL960 at the following `(x,y)`:
   `(103,67),(157,103),(130,104),(107,103),(132,66),(149,77)`.
   Source indexesDS0674=[7,8,9,10,11,12] relative to SHPL960; positionsDS0340 are stored(y,x).
4. Initialize MODULES SCR3610, palette3600, original bounds(175,283,222,333) but relocate to origin **(181,93)**. Wrapper relocation sets bottom140 and centerx206, yielding width50,height47. On initial entry, stop after **one display update**, leaving robot's first pose. That pose is SHAP3601 at(191,102).
5. Restore full-screen rendering, draw TH exitSHAP8/pal6 at(304,1), then original cursor.
6. Clicking within active rectangle(34,77,168,243) runs fullSCR3610 only if any prize flag is true. With no prizes, the stillrobot stays. Outside orEsc returns. For indices0..2, active rects are in `tables.json`, and click replays corresponding SCR.

Initial stop-after-first-display behavior is explicit main0x4868..487B. Full replay passes that flag0 at0x2723. This is why the previous demo's empty shelf omitted a visible robot even before any prizes were earned.

### Winner reward integration

Shared victory chooser0xAEC7 takes role as one of its arguments. Role2(robot) selects palette960 and exactly six persistent prize choices (`0xAED5..AF02`,0xB03F..B062). When a prize is selected, `0xB273..B27B` sets DS55F8[selected]=1 and **DS52F6=7**, so the next telescope visit selects the only unseen mask bit, index3. Existing flags are not toggled off. The chosen prize also participates in the normal winner presentation.

The six small shelf icons represent original robot items; larger selection images are TH SHAP961..966. First is explicitly drawn as a floppy disk labeled “Bongo Box Program”; remaining visual identification should use those original images rather than guessed names. The shelf should be populated from game reward state, not a separate pet inventory.

## Implementation priorities from these findings

1. Correct fourth-view label and initialrobot; exact full-screen native reference is ready.
2. Calendar/day browsing with original daily stories and modern readable pane.
3. Dynamic clock plus original speech routines; deterministic reference clock remains necessary for comparison runs.
4. Cloud cycling and nest/spider/portrait one-shots.
5. Character hunger/fatigue with general drag-object interaction matrix and original alternate-pose scripts.

The complex movable-object system, reward chooser animation, character sleep/alternate-pose sequences, and all timing/audio paths still require dedicated source/native comparisons before claiming whole-room equivalence.

Persistence clarification from dedicated rewards research: robot shelf flags DS55F8 are retained during the running session but are **outside STATUS.DAT's three serialized regions**. They are not proven to survive program relaunch; source serialization indicates they do not. See `treehouse_rewards_research.md` for exact chooser rules, file layout, native victory/selection/shelf captures, and an actual native theater STATUS.DAT save.
