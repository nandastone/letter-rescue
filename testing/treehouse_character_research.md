# Treehouse character and movable objects: original implementation

Primary-source research, 2026-09-27. This follows `treehouse_room_followup.md`; it does not change the runtime.

## Sources and evidence conventions

- Original executable: `testing/output/treehouse/disassembly/unpacked.bin`; main code offsets below are hexadecimal image offsets, as printed in `research-resources/main-disassembly.txt`.
- DS data is at image offset `0x321D0`. The original settings segment is `3169`, image offset `0x31690`. Both relocate when loaded. The pinned native fixture has image base `0x220`, hence DS RAM base `0x323F0` and settings RAM base `0x318B0`.
- Original TH/BOY/GIRL resources: `testing/output/treehouse/extracted-v2/manifest.json`, extracted from the pinned original archive. `research-character/object-atlas.png` displays the actual object art and `object-table.json` contains exact IDs and initial room rectangles.
- All native captures here restore an ordinary earlier save state and then use mouse input or elapsed emulation. No native RAM is modified. `research-character/drag-a/run.json`, `sleep-a/run.json`, and `wake-a/run.json` record the input and starting-state hashes; each directory retains callback timelines, unique original frames, final RAM, and native states.
- All rectangles in tables are `(top,left,bottom,right)`, with exclusive bottom/right. Tick durations are the original 60 Hz clock, not DOSBox's roughly70 Hz callbacks.

## Character state and script resolution

| Field | Address | Meaning |
| --- | --- | --- |
| Hunger | DS5282 word | 1..5, higher means hungrier |
| Fatigue | DS581C word | 1..5, higher means more tired |
| Pose/location | DS5688 word | Table below |
| Next hunger update | DS568E dword | Absolute game tick |
| Next fatigue update | DS5576 dword | Absolute game tick |
| Sleeping wake hour/minute | DS5526 / DS5592 words | DOS wall-clock time |
| Deferred wake | DS5826 word | Wake requested while a modal activity is running |

Boot initializes each need to `random(0..2)+1` (`005BF..005DC`). The captured initial fixture happens to have both1; this is not a universal fixed initial value.

| Pose | Hit rectangle, DS01C4+pose*8 | Still relative shape, DS01EC | Meaning supported by source/native art |
| ---: | --- | ---: | --- |
|0|(119,152,168,186)|1|Central standing location|
|1|(116,211,165,245)|1|Right standing location, beside fruit|
|2|(123,20,172,54)|1|Left standing location, tired reminder location|
|3|(94,200,143,230)|4|Telescope pose|
|4|(105,32,153,59)|15|Sleeping on left side|

Main `392B` selects character action:

```text
resolved = action
if exemption[action] == 0:
    if pose == 2: resolved += 100
    if pose == 1: resolved += 200
script = 20500 + resolved
```

Exempt actions from DS01F6 are `{0,1,2,3,4,5,13,15,23,24,25,26,27,31}`. All other actions0..31 resolve by current pose. **Exempt actions reuse the base script and ARE relocated** at `42A6`/`51AA`: pose1 translates `(x+59,y-3)`, pose2 `(x-132,y+4)`. Nonexempt actions use their separately authored+100/+200 scripts and are NOT additionally relocated. The chosen BOY/GIRL archive and the already-loaded20500 shape/palette handle are passed by `392B`.

During wrapper setup, before playback begins, the wrapper updates pose based on `resolvedAction % 100` (`4662..4757`, jump table4725; playback loop begins4855):

| Action | Resulting pose |
| --- | --- |
|6,7,8,9,14,28|1, except preserve current pose when `action - characterSex == 6`|
|16|2|
|18,20|4|
|19|3|
|21,22,29,30|0|
|Everything else|Preserve|

`characterSex` is the word at settings segment+A14, not part of the saved STATUS.DAT block below. It is **0=boy,1=girl**:00935 indexesDS0248 to stringsDS01AC=`BOY.DAT` andDS01B4=`GIRL.DAT`. This conditional must use the original value; do not infer that every refused fruit always moves the character. Current native fixture has value0. The attempted orange coordinate in `drag-a` actually picks up an already present movable banana20; read-only final object records establish this. Thus that capture covers refused apple/grapes/banana, not a verified refused orange.

The hit-rectangle table above is the raw binary table. Boot `0078C..007C0` adjusts sex0's rectangle TOPS only: poses0,1,2 add4, pose3 adds5; pose4 is unchanged. Sex1 uses the raw table. Use the selected-character adjustment before hit testing and drawing standing poses.

### Action meaning from callers

| Action | Original trigger |
| ---: | --- |
|1..4|Consume fruit types17..20 while hunger>1|
|5|Consume a nut when hunger==5|
|6..9|Fruit types17..20 offered while hunger==1|
|10|Nut offered while hunger<5; creates/increments object14|
|11|Worm type12 offered when bird object15 absent|
|12|Worm type12 offered when bird15 exists|
|13|Hunger warning when old value3|
|14|Urgent hunger reminder when old value>=4|
|15|Fatigue warning when old value3|
|16|Urgent fatigue reminder when old value>=4|
|17|Pillow offered when fatigue<4|
|18|Start sleep|
|19|Enter telescope; source141D waits60ticks then opens view|
|20|Click sleeping character; stays asleep|
|21|Natural wake|
|22|Interrupted wake|
|23|Click awake character with hunger<4 and fatigue<4|
|24|Offer object2|
|25|Offer object5; DS5272 special visual flag set|
|26|Offer object3|
|27|Offer object4|
|28|Return from telescope|
|29|Return from left location to central location|
|30|Return from right location to central location|
|31|Click family portrait while awake|

Character click handler `011F2..01268` tests a rectangle inset4pixels from the currently saved character bounds. Sleeping plays20. Otherwise fatigue>=4 takes priority: decrement fatigue then call its update routine, producing the corresponding reminder without a net counter increase. Next comes hunger>=4 with the analogous behavior. Otherwise action23. DS0216 is a separate central-floor click area that calls585B, returning pose1 via30 or pose2 via29.

## Need timers

Hunger update5578 first schedules `now+7200`. If old hunger==3 it plays13. If old hunger>=4 it schedules `now+3600` and normally plays14; if currently pose2, it first plays29. If fatigue==5 the urgent hunger branch suppresses the reminder and decrements hunger before the final increment. Finally increment hunger, capped5.

Fatigue update564E first schedules `now+14400`. If old fatigue==3 it plays15. If old fatigue>=4 it schedules `now+3600` and normally plays16. If hunger==5 it suppresses the urgent reminder and decrements fatigue before the final increment. Finally increment fatigue, capped5.

Outside the room these update branches issue the corresponding voice prompts through4C0F rather than room animations. The fatigue prompt also depends on whether the pillow is in the room or outside.

Setters57D9 and581A clamp their input1..5 and restart their respective normal7200/14400tick schedules. Warning cross-schedule helpers575D/579B postpone the other need's due time to `now+600` when the other need>=3 and its low-word signed time difference is<600. Main113E bypasses both periodic need updates while pose4.

## Sleep and waking

Offering pillow object8 when fatigue>=4 removes the object and calls4D6F. It reads DOS time, schedules wake at current minute+2 if seconds<=30, or+3 if seconds>30, carrying the hour modulo24. In-room it updates the nap note (`35FA`) then plays18; outside it assigns pose4 directly. It speaks the wake time and calls the fatigue setter with1 after the sleep animation and speech finish. An intermediate frame may already show pose4 but still fatigue4.

Wake38BC clears DS5826. If currently sleeping, in-room it plays action `21+interrupted`, clears the nap note, then assigns pose0. Outside the room it returns pillow object8 to the room and assigns pose0. Finally fatigue becomes `1+3*interrupted`: natural wake1, interrupted wake4. Snapshotting midway through action22 can therefore misleadingly show the previous fatigue1.

The clock routine checks wake hour/minute; modal activity defers the wake via DS5826. Music/nature/theater/board/telescope entry calls38BC(1), so these activities interrupt sleep. Clicking the sleeping character itself plays20 and does not wake them. The nap-note hotspot speaks scheduled wake time while sleeping; while awake it speaks the no-nap response.

Native evidence: `sleep-a` waits and feeds original fruit whenever hunger rises, until fatigue4, then drags the pillow at `(111,139)` onto the character. `asleep.png` shows the left sleeping pose and the original written wake time. This reaches sleep entirely through ordinary play. The first settled food screenshots also demonstrate that food increases fatigue and resets hunger. `wake-a` independently restores the asleep state for both branches: music entry settles at pose0/fatigue4; waiting10000callbacks settles naturally at pose0/fatigue1. Both match the source rule. See `wake-a/state/interrupted-settled.png` and `natural-settled.png` plus their RAM snapshots.

## Object model and exact IDs

Object count is DS556C, records DS5830, capacity21, stride20bytes:

| Offset | Type | Meaning |
| ---: | --- | --- |
|+0|u16|Type0..20|
|+2|u16|State; not universally quantity|
|+4|u16|Room flag:1 inside,0 outside|
|+6,+8,+10,+12|i16×4|Current rectangle|
|+14|u16|Saved background handle, transient pointer|
|+16|u32|Due game tick|

Creation857B reuses an existing type when present, otherwise appends;8637 initializes. Room initial rects are DS07BE+8*type; outside rects DS0866+8*type. Default graphics select a palette via DS05F6[type] and a relative shape via DS0936[5*type+(state%10)]. Palette handles are groups870,900,930. A table entry0 is not an actual shape to draw.

| Type | Asset-supported description | Palette | Relative shapes for state0..4 | Draggable |
| ---: | --- | ---: | --- | --- |
|0|Dragon egg|870|1,12,13,14,15|No|
|1|Paper airplane|870|29,18,0,0,0|Yes|
|2|Magnifying glass|870|0,20,21,22,23|Yes|
|3|Cup-shaped food reward|870|0,10,0,0,0|Yes|
|4|Lollipop|870|0,24,0,0,0|Yes|
|5|Caterpillar|870|0,25,26,0,0|Yes|
|6|Balloons|900|0,5,6,7,0|Yes|
|7|Potted flower|900|0,9,10,11,12|Yes, except state5|
|8|Patterned pillow|900|13,18,0,0,0|Yes|
|9|Bag labeled Nuts|930|0,8,9,0,0|No|
|10|Wastebasket|930|0,10,11,12,13|No|
|11|Nut|930|0,7,0,0,0|Yes|
|12,13|Worm, room/outside variants|930|0,14,15,0,0|Yes|
|14|Nut pile|930|0,3,4,5,6|No|
|15|Blue bird|930|0,24,25,0,0|No|
|16|Timed outside food object; special renderer|870|0,0,0,0,0|No|
|17|Orange|900|0,14,0,0,0|Yes|
|18|Apple|900|0,15,0,0,0|Yes|
|19|Grapes|900|0,16,0,0,0|Yes|
|20|Banana|900|0,17,0,0,0|Yes|

The tiny patterned object at the radio is the pillow, despite its pinwheel-like appearance at1×. Its semantics are explicit in9620 and native sleep capture.

### Drop onto character, jump table969F

Disabled while character sleeps. The hit target uses the current pose rectangle, not always the central rectangle. Consumed means remove the dragged instance before playing the action.

| Object | Handler | Result |
| --- | --- | --- |
|2|94D2|Consume, action24, recreate type2 in room|
|3|94F6|Consume, action26, hunger=1, fatigue+1|
|4|951D|Consume, action27, hunger=1, fatigue+1|
|5|95D7|Consume, setDS5272=1, action25, then special object5 handlerA7D0|
|8|961E|Consume; fatigue>=4 starts sleep, else action17|
|11|9544|Consume; hunger==5:action5,hunger−1,fatigue+1; otherwise action10 andA5F1 creates/increments type14 capped4|
|12|9587|Consume; if15exists:action12 thenAC01; else action11 thencreate13 outside|
|17..20|9644|Consume; hunger>1:action(type−16),hunger−2,fatigue+1; elseaction(type−11),no need change|
|Other types|96C5|No character-specific action; normal placement behavior|

All need changes use clamping setters and therefore restart timers. Removal before an action does **not** always mean the object disappears permanently: the SCR callbacks below put refused fruit and the pillow back into the scene at the correct animation boundary.

### Essential character SCR opcode10 callbacks

Main392B supplies callback4ED3 to the SCR wrapper. Original opcode`0x10` invokes it with its u16 argument. Exact script byte offsets for both characters and all alternate versions are recorded in `research-character/script-callbacks.json`; callback semantics are source4ED3..51A7:

| Argument | Effect |
| ---: | --- |
|0..3|Create fruit type17+arg in room. If arg==characterSex, use left94,bottom146; otherwiseleft245,bottom142. Preserve fruit's initial width/height to calculate right/top. Draw it into the animation backdrop.|
|4|Create pillow8 in room at its normal rectangle and draw. Used by action17,21,22.|
|5|Create pillow8 outside, overwrite itsrect withDS03B4 `(182,122,196,134)`, draw.|
|6|Erase and remove LAST object record.|
|7|Erase LAST object record; decrement itsstate; redraw ifnonzero, otherwise remove.|
|8|Create object5 in room; overwrite rectangleDS03BC `(142,162,153,185)`, apply currentpose relocation51AA; draw. Used by action25.|
|9|Find bird15, promote it tolast ifneeded, incrementstate, redraw. Used by action12.|

Each callback renders through the animation's local buffer: set target from callback handle, draw/mutate, resetclip, and copy the result into its retained backdrop (`5169..51A7`). A renderer that only updates object state after SCR completion misses frames and can erase the new object on subsequent display updates.

For the character resource set, arguments0..3 occur in actions6..9 respectively;4 in17/21/22;8 in25;9 in12. The callback routines5..7 also support other script callers. The callback data file is an exact resource extraction, not a guessed timing table.

### Click dispatch, main9D82 and jump tableA268

| Types | Handler | Behavior |
| --- | --- | --- |
|0|A179|Three state increments with30tick waits; final state increment, animationA8FE, remove|
|1|A14C|Sound1018, A8FE animation, remove|
|2|A04D|Sound10028; increment/draw three times,8ticks each; resetstate1|
|3,4,8,11,17..20|9D8D|No special click action; redraw if necessary|
|5|A23F|A7D0 special interaction|
|6|9DC0|Sound10011; temporary state+10 for4ticks, then state−9 (net+1); remove atstate4, else redraw|
|7|A0F5|Unless state5, cycle1..4; sound1007; redraw|
|9|9E38|If nut11alreadyexists, ADE8 fetches it; else bagstate+1, createsnut11, moves through five DS0A5E rectangles4ticks each, thenbagstate−1|
|10|9F3E|If worm12exists, ADE8 fetches it. State1 branch opens basket over3×8ticks, callsA746 three times8ticks apart, thenB572. Otherwise resetbasketstate1, createworm12 and enteritsdrag handler|
|12,13|9DAA|B815 worm-specific animation|
|14|A24D|611D nut-pile environment behavior|
|15|A171|BC78 bird-specific behavior|
|16|9DB5|BBAD timed-food behavior|

Type0's loop wait is exactly30ticks (`A1F6`), unlike the8tick type2 loop. Follow-up source artwork identifies type0 as a dragon egg (TH882–887), type2 as a magnifying glass (large reward TH873), and type5 as a caterpillar that transforms into a chrysalis then butterfly (TH895–898). Full special animation recipes are now in [object completion research](treehouse_object_completion_research.md), with original asset sheets under `research-object-completion/`.

### Placement surfaces and outside transitions

General drag9141 waits15ticks to distinguish a click from a drag; non-draggable types go straight to click dispatch. State5 flower and outside paper airplane also go straight to click dispatch. Drag movement uses the original sprite and pointer offset; the object is promoted to the end of the rendering order.

Surface tables DS06F2 contain eleven rectangles per scene. The second bank is inside-room. The handler checks them ascending using the dropped object's bottom-center point and settles its bottom to that surface height. Open calendar disables inside surfaces0..2; inside surface5 is skipped. A flower falling>60pixels, or dropped on inside surface9, sets state5 and plays sound1034.

Inside surface9 transfers objects outside: foods3,4,17..20 become timedfood16; nut11 becomes/increments pile14; worm12 becomes13 if absent; other types become outside objects at their standard outside rectangles. Outside surface2 returns objects to room; outside surface1 removes the object and runs an exterior reaction (type2->SCR1004, pillow8->SCR1003, othersSCR1005+sound10002). Inside surface0 sends types5/12 throughA2A7 after placement.

Due times fromB8A3: balloons48ticks; nut11 `(random(0..10)+6)*60`; timedfood16 `(random(0..60)+120)*60`; other types due immediately. These timers are not interchangeable.

## Object overlap and environment animation evacuation

Main8CF4 finds only balloon object6. It expands the incoming animation rectangle vertically by2pixels, leaves itsx unchanged, then moves the balloon2pixels every2ticks until strict positive-area overlap ends. Flag0 moves down; nonzero moves up. The generic script wrapper43AC uses flag0 only for group1080 (spider); other groups use1. Original rectangle helper resident4134 proves expansion `(top−2,left,bottom+2,right)`; intersection resident83B4 treats touching edges as no overlap.

8B45 redraws and promotes the changed object to the last array entry; its return value is the new index.8CF4 must use that updated index. It preserves DS5528 around evacuation.

The redraw path8F7F grows a dirty rectangle to include eligible intersecting objects' old saved-background rectangles (handle+0x10) and their new rectangles. It repeats passes until the transitive overlap union stops growing.8EE4 erases eligible intersecting backgrounds in reverse order;8DBB redraws objects ascending. Other objects are not physically pushed by balloon evacuation.

EligibilityAD72 always includes balloons. For other types: ifDS5522!=0 require object.top>DS5528; otherwise require object.bottom>=DS5528. The helpers also filter object.roomFlag equal to `(scene==5)`.

## STATUS.DAT persistence

Original file in the pinned archive is2704bytes (`0xA90`). Save7CDD and load7DCB implement this exact layout:

| File offset | Length | Memory source/destination |
| --- | ---: | --- |
|0000|08EA|Segment3169:0048 settings block|
|08EA|0002|DS556C object count|
|08EC|01A4|DS5830, all21 object records (including unused slots)|

No header, version, checksum, or per-record serialization appears. It writes raw little-endian memory, including the transient background-handle and due-tick fields. Successful reads/writes require all three byte counts to match. A failed or missing load runs defaults7ECF: zero the08EA settings bytes, initialize activity defaults, zero object count, create nuts9 and basket10 in the room.

Boot normalizes object records (`038A..053B`): ensure pillow8 exists; delete flower7ifstate5; remove transient bird15; clamp balloon6 tostate1..3, flower7andpile14 to1..4, reset other states to1. Runtime pointers/backgrounds are rebuilt. Do not treat the raw saved background handles as reusable addresses in a port.

HungerDS5282, fatigueDS581C, poseDS5688, their timers, sleeping time, and robot-prizeflagsDS55F8 are outside both serialized blocks. These are session state, not persisted by this routine. Character selection at settings+A14 is also outside the block ending at+932. The block contains settings/activity state rather than the entire settings segment.

## Remaining precision work

- Object identities, special animation recipes, and outside squirrel/bird/worm/nut-pile source handlers are covered by [object completion research](treehouse_object_completion_research.md); its remaining native trajectory comparisons are tracked there.
- Confirm both boy and girl alternate scripts at every action boundary; current ordinary-input references use characterSex0.
- STATUS.DAT byte-level fields within the08EA settings block still need a complete independent schema; the container and object record schema above are exact.
