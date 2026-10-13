# Treehouse object and environment completion research

Primary-source follow-up, 2026-09-27. Complements `treehouse_character_research.md`; no runtime changes.

## Evidence and conventions

Original pinned archive: `testing/output/treehouse/source/The_Treehouse_1991.zip`, SHA256 `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`. Code addresses are hexadecimal offsets in `testing/output/treehouse/disassembly/unpacked.bin`, with DS at image321D0. Listings are `research-resources/main-disassembly.txt`; direct decoding is necessary at jump tables. Native capture DS is RAM323F0, because the fixture loads the image at220.

Scratch evidence is `testing/output/treehouse/research-object-completion/`: `tables.json` holds original table values; `environment-scripts.json` contains complete parsed original SCR streams; the art sheets show original decoded pixels. Captures use ordinary mouse input, save-state restoration, and elapsed emulation only. RAM reads record outcomes; no memory is changed.

All points below are `(y,x)`, rectangles `(top,left,bottom,right)` with exclusive bottom/right. Waits are original60Hz ticks; capture callback counts are not ticks. `R(n)` means an inclusive integer0..n.

## Original object identities

Large TH871..876 rewards and TH882..898 transition art resolve earlier ambiguous names:

| Type | Identity | Evidence |
| ---: | --- | --- |
|0|Dragon egg|TH882 egg,883 cracked egg,884 head,885 hatching dragon,886/887 flying dragon|
|1|Paper airplane|TH872 large prize; TH888 still and889 flying|
|2|Magnifying glass|TH873 large prize; earlier reward report's “blue gift” identification was incorrect|
|5|Caterpillar|TH895 caterpillar,896 chrysalis,897/898 butterfly|
|7|Potted flower|Four flower states and broken pot|
|9|Bag of nuts|Produces type11|
|10|Wastebasket|Opens, attracts bird, and produces type12|
|12/13|Room/outside worm|Separate identity for scene routing|
|14|Outside nut pile|State1..4 is quantity|
|15|Bluebird|State2 depicts carrying food|
|16|Outside food|Generic shared food art consumed by SCR1300|

`large-rewards.png` and `special-flight-art.png` are lossless enlarged art evidence. Types3/4 are dessert/lollipop,6 balloons,8 pillow,11 nut,17..20 fruit; their ordinary character offers remain covered by the character report.

## Shared flight renderer: resident6DA9

This is a one-axis-per-iteration integer trajectory, not ordinary simultaneous-axis Bresenham. Start at source; let `dx=abs(target.x-source.x)`, `dy=abs(target.y-source.y)`, signed steps sx/sy. Error starts `floor(dx/2)` if dx is nonzero, otherwise−1. At each iteration draw if iteration%step==0 or at destination. After a draw, wait the supplied delay. To move: if error>=0, x+=sx and error−=dy; otherwise y+=sy and error+=dx. Increment iteration and repeat through destination.

Frame A is used when iteration%(2*step)==0, otherwise B. Thus the destination frame is chosen from its actual iteration index. Each draw restores previous saved background, captures the next background, draws mode10, and transfers the union damage rectangle. The final erase flag restores the last background. DS57DC enables redraw of an overlapping balloon above the moving sprite. Respect clipping and the final cleanup; merely interpolating every delay produces different frames.

## Egg, airplane, caterpillar

### Common departure A8FE

DS0A0A has two relative flight ordinals per type: egg16/17, airplane19/19, caterpillar27/28, all in TH870. Center the first flight shape in the current object rectangle using6CEE. If the object's left edge is<160, mirror both shapes horizontally, close the room calendar, and clip right to283 in the room; destination is DS05E4 `(48,312)`. Otherwise fly to DS05E0 `(88,-30)` without that mirror/clip change. Egg redraws its state5 before flight; other objects restore their old background first. Set57DC during6DA9, with erase1, delay10, step16, then restore clipping and release temporary shapes.

### Egg click A179

Play1031. Three times: increment state, redraw, wait30ticks. This displays states2,3,4. Play1036; increment to5; use A8FE; restore object background and delete its record. Renderer A444 mirrors egg states2..4 when its left edge<160, while the state1 egg remains unmirrored. Native `clicks` captures confirm state3 at `disc-clicked-50`, and deletion by `disc-clicked-170`; the legacy `disc-*` labels predate identification.

### Airplane click A14C and falling route9940

Click plays1018, flies through A8FE, then deletes the record. Outside airplanes are click-only; inside they can be dragged.

If an inside drag releases more than36pixels above its landing height, except transfer surface9, its landing animation is three segments. With start S and vertical fall d: P1=S+(dy=trunc(d/4),dx=-40); P2=P1+(dy=trunc(d/2),dx=80). Fly S→P1; horizontally mirror the plane; fly P1→P2; restore its orientation; fly P2→landing. Each segment uses identical A/B frame, erase1, delay3, step6. These are offsets:6BF4 adds the supplied dx/dy to the input point. Generic object falls use delay1,step6; plane does not receive generic long-fall sound10021.

### Caterpillar A7D0

Increment state1→2 (chrysalis), redraw, wait30ticks; play1022; fly through A8FE as butterfly and delete the object. The boolean argument controls original background restoration, not the trajectory.

Offering type5 to the child removes it, sets DS5272, and runs character action25. Its SCR callback8 recreates type5 at DS03BC `(142,162,153,185)`, relocated by the current character pose; clears5272; then invokes A7D0. Dropping caterpillar or worm into room surface0 invokes nest consumption A2A7 (chirp, erase, chirp, remove).

## Flower A0F5

Click cycles state1→2→3→4→1. Broken state5 remains5. Every click plays1007 and redraws, including a broken pot. A drag falling>60pixels, or landing on room transfer surface9, sets state5 and plays1034. Broken flower is not draggable and is removed during later room initialization.

Native `clicks/flower-clicked-50` is state2; `flower-cycle-0/1/2` are3/4/1. Drag from(267,103) to(205,50) then release settles at rect `(147,194,173,217)`, state5 (`flower-drop`). Full callback frames retain the falling/break sequence.

## Bag of nuts9:9E38

If nut11 exists, ADE8 highlights that existing nut; no duplicate is produced. Otherwise increment bagstate1→2, redraw, play1014, preload10038, create/draw nut11. Wait4ticks, then redraw nut at each of these rectangles with4ticks per step; play10038 at index2:

| Step | Rectangle |
| ---: | --- |
|0|(152,271,161,283)|
|1|(146,255,155,267)|
|2|(153,244,162,256)|
|3|(162,237,171,249)|
|4|(178,232,187,244)|

Finally find the bag again, decrement state back to1, redraw. ADE8, for an object in the current scene, closes an overlapping calendar, promotes object to last z-order, then blinks erase12ticks/redraw12ticks three times.

Nut11's next automatic retrieval is `now+(R(10)+6)*60`. The room scheduler retrieves it only if its rectangle is fully contained in DS07A6 `(178,226,187,250)`. Promote it to last, then play TH **SCR1403**, SHPL1400, callback4ED3. SCR1403 bounds are `(168,207,200,297)`; opcode10hex at byte238 calls argument6 and removes the last object. The original script owns the squirrel trajectory/timing. Native `clicks/nuts-out` and `nuts-fetch` prove one nut remains after a second bag click.

## Wastebasket10:9F3E

If room worm12 exists, highlight it through ADE8. Otherwise:

* Closed state1: play1001; three increments/redraws separated by8ticks (2,3,4); play1010; toggle via A746 three times, waiting8ticks (3,4,3); summon a bird with B572.
* Any open state: set basketstate1 and redraw; create room worm12 at DS07AE `(160,6,172,23)`; save background; show cursor; enter worm drag9141 using the original click point. Releasing normally leaves the worm there.

Native `basket/basket-open` contains basketstate3 and perching bird15; `basket-worm` contains basketstate1 and worm12 at the exact DS rectangle. `basket-worm-150` preserves the worm after the ambient bird has departed. Clicking that worm then removes it through the bird feeding route (`worm-click`, `bird-settled`). The earlier `clicks/basket-worm` was interrupted by the due nut animation; use isolated `basket` captures for this interaction.

## Worm and bird routes

### Worm click B815

Hide cursor. A64A finds room12/outside13 and promotes it to last. Play1010; twice display state+1 for12ticks then state−1 for12ticks. Close room calendar. Play12025. If bird15 exists or scene is outside, B5D9 takes the worm; otherwise B572 summons a bird and leaves the worm. Show cursor.

### Bird flight AABE

Use TH930, relative frame pair base/base+1. Base=20 when target.y>source.y, otherwise16; add2*variant (variant1 is carrying food). Mirror both when target.x>source.x. Corrected by independent native pixel comparisons in treehouse_room_object_runtime_audit.md. Existing bird index>=0 is erased/deleted before the flight. Begin full viewport clip, optionally set left163 and/or right283 according to the caller flags. DS57DC is1 during6DA9(erase1,delay8,step10). Restore clip, free both sprites, and reschedule ambient time.

### Summon B572; click BC78

B572 does nothing if bird15 already exists. Otherwise close calendar, fly `(48,312)`→`(95,218)` with right clip283, variant0, then create room birdstate1 at `(95,218,115,243)`.

Clicking perched bird closes calendar, plays12025, and flies `(95,218)`→`(32,132)` with left clip163, variant0, deleting the bird record.

### Take worm B5D9

Target is worm top-left plus `(dy=-6,dx=2)`. Source is the room perch `(95,218)` if bird exists, otherwise `(48,312)`; outside source is `(10,350)` and any existing bird record is removed. Fly source→target with no side clipping, variant0. Remove worm, create birdstate2 in current scene with its rectangle translated to target; draw and wait20ticks.

If outside, calendar open, or R(1)!=0: fly target→`(88,-30)`, no side clipping, variant1, deleting the bird. Otherwise enter AC01 nest feeding.

### Nest feeding AC01

Hide cursor, close calendar, chirp3C12. The character-offer branch first flies carrying bird from perch `(95,218)` to DS0A86 `(86,200)`; normal worm-taking uses its supplied source. Fly to DS0A8A `(74,222)` with caller clipping flags, variant1. Set DS5278=1 to force bird artwork orientation. Create room birdstate2 at DS0A8E `(70,222,90,247)`, draw; chirp; decrement birdstate and redraw. Create room worm12 at DS07B6 `(74,240,86,257)` and invoke A2A7 (chirp, erase, chirp, delete). Clear5278, play12025, fly nest point→`(48,312)` with right clip283, variant0; show cursor.

## Nut pile14 and outside food16

A5F1 creates outside pile14 or increments quantity capped4. Its scheduled consumption time is `now+(R(60)+120)*60`; BB48 also reschedules the existing room nut and ambient time. On611D, promote pile to last. If currently inside, decrement quantity, remove at0, play10037. If outside, invoke **SCR1402**, SHPL1400, callback4ED3; opcode10hex at byte241 passes7, decrements the last object's quantity and redraws/removes it. SCR1402 bounds `(142,208,199,284)`. Keep its complete original stream.

Food16 is created when types3,4,17..20 are dropped through inside surface9. Its normal shape is TH1300 ordinal7, drawn at the object rectangle top-left. Schedule `now+(R(60)+120)*60`. On due BBAD:

* If currently inside: start480tick timer, play10017, wait for the timer, stop sound, delete food record.
* Outside: set DS5776 to object index and DS5A1C=1; play SCR1300 with loaded group DS57BE/TH1300 and callbackA2D6; clear5A1C; release object background and delete record.

SCR1300 bounds `(181,269,194,343)`. Its callbacks are byte227 arg0,595 arg1,1013 arg2,1431 arg3,1744 arg4. Each callback restores the script backdrop and erases the food; args0..3 redraw ordinals6,5,4,3 respectively; arg4 leaves no food. Copy the revised backdrop back to the script work surface, then restore draw origin/target. Applying changes only to the main canvas lets food reappear beneath the animation.

## Placement / transition table

Use the full original two-bank surface table in `tables.json`. Match the dropped object's bottom-center in ascending order. Room surface5 is skipped and open calendar disables0..2. Transfer surface9 is `(0,240,400,380)`, but earlier shelves take priority. Drop below those shelves to reach outside.

Room surface9: foods→16; nut11→pile14; worm12→13 if absent; other types move outside at their original outside rectangles. Outside surface2 `(0,221,62,254)` returns to room. Outside surface1 `(0,-80,192,104)` discards via targetpoint `(170,50)` and runs reactions: magnifier2→SCR1004, pillow8→SCR1003, others→SCR1005 and sound10002.

## Environment scheduler8742

Active only with DS5692!=0 and DS15E8==0. It services balloons inside, due nut retrieval, ambient event, due food16, and due pile14. DS531C ambient deadline is reset by BC43 to `now+(R(10)+20)*60`.

Inside ambient R(7) uses the jump table at image88D7:

| Random index | Action |
| --- | --- |
|0,1|If worm12 exists click/wiggle/feed it throughB815; else if bird15 exists fly it awayBC78; otherwise bird flybyB9C6|
|2,3|Nest chirp3C12|
|4,5|Nest animation4CCC|
|6|Spider604F (TH SCR1080)|
|7|Character reminderD02C unless sleepingpose4|

Open calendar forces index7. It does not suppress the entire ambient event.

Outside R(7):0..3→608C, cycling TH SCR1000/1001/1002 and wrapping DS5570 modulo3;4,5→take outsideworm if present, otherwise bird flyby;6→TH SCR1060;7→no action. SCR1000/1001/1002 bounds `(171,15,200,78)`, `(177,15,199,107)`, `(173,15,200,89)`; SCR1060 bounds `(81,122,101,142)`. Use extracted streams and their original shape groups.

B9C6 flyby: outdoors uses endpoints `(10,350)` and `(88,-30)` with a random swap. Indoors R(1)!=0 uses `(48,312)` to either `(32,132)` or `(88,-30)`, random swap; right clip283, and left clip163 when either endpoint is `(32,132)`. Indoor R(1)==0 chooses one of `(32,132)`, `(48,312)`, `(88,-30)` and invokes nest feedingAC01 with left clip iff first endpoint, right clip iff second. Reschedule ambient after completion.

## Native evidence inventory and limits

`clicks`: reward-derived egg hatching/flight/deletion; all four flower states, falling and broken pot; bag/nut creation and duplicate blink; later automatic squirrel retrieval. `basket`: isolated basket opening, bird arrival, worm extraction and worm feeding. Each folder has input/restoration hashes in `run.json`, every callback in `frames.jsonl`, exact screenshots/RAM/states under `state`, and deduplicated original frames under `frames`.

Source recovery above is complete enough to implement the listed state transitions. Native visual parity still requires replaying/aligning each trajectory; this report does not claim callback-aligned comparison for an implementation. Airplane/caterpillar native fixtures were subsequently captured below.


### Completed outdoor fixture

`outdoor` drags original fruit20 from(254,124) to(287,186), producing food16 at `(181,269,190,289)`; gets nut11 from the bag and drags(238,182)→(277,186), producing pile14 at `(185,248,197,269)`; clicks ladder(275,190) and waits12000callbacks outdoors. `outside` preserves both objects; `outdoor-consumed` has neither. All intermediate original frames cover SCR1402 pile retrieval and SCR1300 food consumption without modifying RAM. Scene entry reschedules food's deadline (native12858 before exit→12327 after exit); do not retain a stale absolute timer blindly across scene setup.

`prize-variants` records twelve restores of the same earned-prize state with different ordinary waits before chooser entry; all produce `[2,6,7,0,3,4]`. Elapsed time alone does not advance this prize RNG sequence, so these are not airplane/caterpillar fixtures.


### Earned airplane and caterpillar fixtures

`prize-next` starts from the prior ordinary awarded-prize state, clicks(150,20) to start a new quiz, clicks Guess(149,94), reads the original secret without changing it, selects that card, and clicks the winner badge. The second earned chooser contains `[6,5,0,1,2,7]`.

`flight-prizes` independently restores this earned chooser, selects slot3 for airplane1 and slot1 for caterpillar5, returns to the room and clicks the actual object. Native initial rectangles are airplane `(159,68,176,112)` and caterpillar `(165,48,176,71)`. `clicked-5` is chrysalis state2; `flying-1/5` and `settled-1/5` have removed the respective record after departure. Original transient flight frames are in the full timeline, even where a checkpoint occurs after flight completion. `room-1.state` and `room-5.state` are reusable ordinary ready states for further comparison.


`flight-drag` adds two ordinary drag routes. Airplane drag(90,167)→(140,55) and release follows the three-segment landing animation and retains type1 at `(159,119,176,163)`; `plane-landed` is its settled checkpoint. Caterpillar drag(60,170) onto the native pose0 character rectangle center(169,145) runs character action25 and butterfly departure; type5 is absent in `caterpillar-offered` and `caterpillar-offer-settled`, with all intermediate original action/flight frames retained.
