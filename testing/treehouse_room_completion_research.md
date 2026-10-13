# Treehouse room portrait, ambient scheduling, and telescope completion

Primary-source follow-up, 2026-09-27. No runtime changes. Uses the pinned original
DOS v1.1 executable/resources identified in
[runtime research](treehouse_runtime_completion_research.md). All addresses are
linear unpacked executable offsets unless marked DS-relative. Source listing:
[all-disassembly.txt](output/treehouse/research-resources/all-disassembly.txt).

## New native evidence

`output/treehouse/research-room-completion/portrait-b/` restores ordinary native
states, then clicks the portrait while healthy, tired, or sleeping, followed by
independent clock/date clicks. Its `run.json` records inputs, state hashes, and
starting hunger/fatigue/pose; `frames.jsonl` retains every callback and game tick.
No RAM was changed. The initial `portrait-capture` run is also retained, but its
cursor overlaps the mouth; use `portrait-b` for pixel comparisons.

Scripts `capture-portrait-b.py`, `analyze-portrait.py`, and `check-portrait.py` are
under the same research directory. `portrait-transitions.json` identifies the
exact original-frame transitions by comparing each6×11 mouth rectangle to the
decoded original shapes. This compares original asset composition locally,
not an independently reconstructed entire room.

## 1. Portrait speech rendering and the sleeping-frame discrepancy

Hotspot22 is `(top27,left4,bottom62,right41)`; handler159F callsD02C.
The drawing routineD40A changes **only** a6×11 patch:

|State|Resource|Origin|Draw mode|
|---|---|---|---|
|Closed / D40A(0)|TH SHAP931, SHPL930|x25,y43|0, opaque|
|Talking / D40A(1)|TH SHAP932, SHPL930|x25,y43|0, opaque|

DS0B0A contains `(43,25,54,31)`. DS5780 is the palette930 group handle loaded
at597..5A4. D40A operates only when shared phaseB34==5 (inside the room).
It composes the patch with the native backing-buffer and object-overlap helpers,
then copies the affected rectangle to the main screen. It does not select
BOY/GIRL art and does not draw text or a new hunger/fatigue meter.

**The existing `research-character/sleep-a/state/asleep.png` matches all66pixels
of TH931 drawn at(25,43).** Its pixel(26,44) is RGB(190,97,40), exactly the decoded
closed-mouth image. Therefore the static room background is not sufficient after
speech: the close operation leaves this opaque patch in the room. The raw
background's palette/layout differs from the later composed room, so do not
repair a single pixel with a special-case color. Render the complete original
closed-mouth patch when D40A(0) runs. A fresh pristine room may retain its
background portrait until the first such operation; do not force the patch onto
all boot frames without checking that state.

This is speech articulation, **not a fixed12tick or random eye-blink animation**.
Callers switch to talking before individual speech parts and closed afterward.
There is no dedicated portrait-font call in this path. Existing date text remains
FONT1; clock and nap-time digits remain original SHAP1215..1227 as documented in
[room follow-up](treehouse_room_followup.md).

### Observed portrait transitions

The healthy and tired captures produce exact931/932 pixels at every transition.
Times below are original game ticks, not video-frame durations:

|Branch|Talking|Closed|Talking again|Final closed|
|---|---:|---:|---:|---:|
|Healthy native random response|2590|2668|2673|2708|
|Fatigue4|25979|26057|26061|26109|

The source delay between two spoken parts is5ticks. Native callback sampling can
show4ticks between recorded visible frames, because the bitmap was drawn between
presentation callbacks. Use source waits for execution, captured ticks for
comparison windows. The sleeping/clock/date branches contain multiple talking
segments; complete sequences are in `portrait-transitions.json`. A handful of
clock frames are marked `other` because the live composition was between writes;
those are not evidence for a third mouth shape.

## 2. Portrait status selection and sound IDs

D02C first checks DS2119 bit0 (digital sound capability). If unavailable it
returns without artwork, PRNG, or idle-deadline changes. Otherwise it temporarily
sets the wait callback to **resident0:89BD**, which services the moving object6
and returns0. Speech waits therefore keep that movement alive without treating
every key/mouse event as a request to skip the voice.

Priority is different from clicking the full-size character:

1. PoseDS5688==4: speak scheduled wake hour/minute withCD40(hour,minute,1).
2. HungerDS5282>=4: `D4C8(11053)`.
3. FatigueDS581C>=4: `D4C8(11054)`.
4. Otherwise consume one `random(3)` and use the following table.

|Random result|Sequence|
|---:|---|
|0|D4C8(11051)|
|1|D4C8(11052)|
|2|Talking; consume random(1), play11055+result synchronously; closed.|
|3|Three times: consume random(4), play11057+result synchronously, wait30ticks. Then talking; play11062 synchronously; closed.|

`D4C8(id)` is: talking; sound11050 synchronously; closed; wait5ticks;
talking; soundid synchronously; closed. Keep original sound assets rather than
inventing transcripts for the unpublished utterances. These branches report
needs; they do not change hunger/fatigue values.

At normal completion D02C restores wait callbackD51:58E2 and callsBC43, resetting
the ambient gag deadline. Sleeping speech also takes this completion path.
Healthy random result3's first three sounds intentionally have no mouth-on
wrapper; only the final11062 uses the talking pose.

The full-size character's click routine1233 prioritizes **fatigue before hunger**
and can play movement/need SCRs. Keep it distinct from portrait speech.

## 3. Clock and date speech choreography

Time routineCD40(hour24,minute,napFlag) also exits without digital capability.
In the room it uses callback0:89BD during speech; mouth toggling is gated by
D40A's phase check, so these routines can also speak outside the room without
painting a portrait over another activity.

- Normal prefix: talking; sound11023; closed.
- Nap prefix: talking;11028. If hour/minute nonnegative, closed;wait15;
  talking;11026. Then closed. Negative values end here (no scheduled time).
- Valid time: wait15;talking; sound11000+hour12 (hour12=hour24%12 or12).
  Hour8 adds11021. Closed;wait20.
- Speak minute throughD166(minute,1);wait20.
- Talking;11024 forAM or11025 forPM;closed;restore callback.

Number helperD166 has5tick punctuation gaps and source table-driven composites.
Main DS0AE2 tens table is `[30,0,20,13,14,15,6,7,8,19]`; DS0AF6 teens table is
`[10,11,12,13,14,15,6,7,8,19]`, both offsets from sound11000. Zero handling and
the mandatory-leading-tens flag matter for minutes. The full source is
D166..D300; the tables are preserved here to avoid approximate synthesized
number speech. For minute0 it returns after a5tick wait, with no number clip.

Date routineCEC3 uses:

1. Talking; sound11120+weekday (Sunday0);closed;wait30.
2. Talking; sound11099+month (January1);closed;wait12.
3. Talking; ordinal day:
   - day1..12: sound11129+day.
   - day13..19: sound11000+teens[day%10];wait5;sound11142.
   - day20..29:11020; day30..31:11013. If exact20/30 append11143;
     otherwise11022;wait5;sound11129+(day%10).
4. Closed;restoreD51:58E2.

No year is spoken in this routine. This differs from visible date text, which
includes the year. Date/clock speech toggles the same portrait patch; there are
no distinct clock-speaking or hungry face images in D40A.

## 4. Autonomous room scheduling

Main loopD16 services8742 before need updates and fixed-hotspot input handling.
8742 returns immediately unless DS5692!=0 (selected character archive loaded)
and DS15E8==0 (no held drawing/tool selection). Do not let ambient actions begin
while a chalk/eraser tool is selected. The shared clock continues regardless.

### Deadlines and source order

|State|Storage|Reset routine/formula|
|---|---|---|
|Short gag deadline|DS531C/531E u32|BC43: `now+(20+random(10))*60`|
|Long room/object deadline|DS5318/531A u32|BB48: `now+(120+random(60))*60`|
|Object6 motion|object record+16 u32|B8A3: now+48ticks|
|Object11 event|object record+16 u32|B8A3: `now+(6+random(10))*60`|
|Object16 event|object record+16 u32|B8A3: `now+(120+random(60))*60`|

Due checks in8742/89BD are strict **now>deadline** (equality waits). Room-wide
resetB95C callsBC43,BB48,633B(cloud300ticks), then B8A3 for each object belonging
to the current room flag. B8A3 also callsBC43 for every type except6; therefore
one room reset can consume many random values and repeatedly overwrite the
short gag deadline. Preserve this order for random-stream alignment.

8742 services in order:

1. In-room moving object6 callback89BD.
2. In-room object11 if its own due time passed and rectangle passes7194 against
   DS07A6: bring it to the last object slot if required; runTH SCR1403 with
   resident callback4ED3.
3. Short gag deadline branch below.
4. Object16 if its due time passed: BBAD. In room it plays10017 and waits up to
  480ticks through the interruptible wait, then stops audio; outside it has a
   different SCR path.
5. Long deadline:611D. If object14 exists, bring it to the front. In-room,
   decrement its state/count, remove when0, play10037; outside runTH SCR1402.
   Then BB48 schedules the next long event and short gag.

The original object identities/art are exported in
`research-character/object-table.json`; use those identities rather than
calling all objects interchangeable “ambient icons.”

### Short gag selection inside the room

After the short deadline, consume `random(7)` once. If the calendar is open,
overwrite the selected result with7 **after** consuming that random value.
The native dispatch table at88D7 is:

|Result|Handler|Behavior|
|---:|---|---|
|0,1|885C|If object12 exists, B815(0). Else if object15 exists, BC78. Else B9C6 generic bird/worm traversal.|
|2,3|889A→3C12|Nest chirp: sound1041, alternateTH920/921, documented8tick cadence.|
|4,5|88A2→4CCC|Nest TH SCR1250.|
|6|88AA→604F|Spider TH SCR1080, only when calendar closed.|
|7|88B2→D02C|Portrait speech only when not sleeping.|

Normally the chosen handler resetsBC43 on completion. **There is no unconditional
reset in8742.** If result7 is suppressed because the character is sleeping, or
portrait speech immediately returns without digital support, the deadline stays
expired. The next foreground service consumes another random(7). With an open
calendar and sleeping character this can repeatedly consume random calls. A
fixed20second browser interval that always reschedules will not match this edge.

The separate exterior phase has its own selection dispatch88EA onward (gags
SCR1000..1002 and1060); do not reuse the interior table outdoors.

### Object6 pointer-follow movement

89BD moves object6 when its deadline passes; no new random draw is used.
Target=(pointerX,min(pointerY,100)). Compare to current rectangle center.
Default increments are(dx,dy)=(1,1); make the dominant-distance axis2 (Y wins
ties), set an axis0 when its absolute distance<2, otherwise assign direction
sign toward target. Move rectangle, bring object to front or redraw it, and
schedule its next motion atnow+48. The callback always returns0. Speech uses
this callback, which explains ambient movement continuing while a voice plays.

## 5. Telescope visit mask and human character handoff

The telescope mask helperD51:4201 / image11711 is not uniform sampling from the
remaining views. For telescope's parameters(count4,forcedMask0,no callback):

```text
start=random(3)                 # exactly one PRNG call
i=start
while mask & (1<<i):
    i=(i+1)%4
    if i==start: mask=0         # all visited; reset this cycle
mask |= 1<<i
return i
```

This cyclic scan biases an unvisited view according to the gap preceding it.
When all4bits are set it clears and returns the original random starting index.
Robot prize selection writes mask7, forcing next visit3. Save maskDS52F6 for
in-session continuity; it is outside the STATUS.DAT serialized areas.

Main141D performs the complete handoff:

1. `38BC(1)`: interrupt sleep if necessary, restoring standing pose and fatigue4.
2. `392B(19)`: selected BOY/GIRL character walks to telescope. Pose becomes3
   during wrapper setup; use the separately authored starting-pose script.
3. Wait60ticks with interruptible timer0D51:56DB.
4. `3217`: room cleanup, then2534 draws and runs the chosen view (phase12).
5. On outside-click/Esc exit, redraw room with1F24(1,1).
6. `392B(28)`: play telescope-return script. Wrapper sets resulting pose1.

Both actions are nonexempt inDS01F6. For action19, pose0 selects20519, pose2
selects20619, pose1 selects20719. Pose3 on return selects20528; there are no
20628/20728 resources in the selected character archives. Do not relocate these
authored pose-specific scripts a second time.

Full disassembled source scripts are exported in
`output/treehouse/research-room-completion/telescope-scripts.json`.

|Script|Displays|Sum(count×delay)|Boy bounds(top,left,bottom,right)|
|---:|---:|---:|---|
|20519|27|189ticks|(98,152,168,230)|
|20619|45|360ticks|(98,20,172,230)|
|20719|7|98ticks|(98,198,165,245)|
|20528|10|130ticks|(97,192,165,248)|

Girl scripts have matching display counts/timing, with top94 for all four
bounds. Footstep sound10020 appears at authored SCR positions; telescope sound
10025 appears at approach/return positions. These are script timings, not a
claim that wall-clock duration is exactly their sum: rendering lateness and the
SCR yield semantics apply, and entry adds60ticks after its script.

The existing ordinary-input `research-room-followup/telescope-a/` contains all
four visits and returns, retaining their full frame timelines. The robot shelf
still-image and first-display behavior remain as established in the earlier
room note; these new findings fill mask selection and human handoff details.

## Evidence limits

New portrait captures cover healthy, fatigue4, sleeping, clock, and date paths.
The hunger>=4 portrait path is source-established here but not independently
captured in this slice. Native full-screen portrait captures are preserved,
while the exact pixel comparison is scoped to the66pixel patch. Autonomous
tables/deadlines are source-derived; the newly documented suppressed-gag PRNG
edge has not been exhaustively replayed. Use original SCRs and existing object
callbacks for the complex bird/worm branch instead of claiming its complete
choreography is reconstructed by this scheduling table alone.
