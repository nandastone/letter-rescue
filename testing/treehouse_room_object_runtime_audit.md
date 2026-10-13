# Room object runtime audit: concrete differences

Research-only audit, 2026-09-27. No runtime edits. Runtime snapshot: `testing/output/treehouse/research-room-flight-audit/audited-room-character.js`, SHA256 `1438dd0825466243bbcdf43c1e007f98059137b6b1c405d1dddef68d5092b484`. The implementation is being corrected concurrently; findings describe that snapshot, not necessarily the current source.

Primary source is pinned `source/The_Treehouse_1991.zip` (SHA256 `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`) and its `disassembly/unpacked.bin`, under `testing/output/treehouse`. Addresses below are **image offsets**, not D51-relative offsets. DS is image321D0. Native recordings use ordinary input/restoration and read-only RAM. Runtime probes use a separate JavaScript instance and do not change original game memory.

## 1. Bird flight uses the wrong animation pair and orientation

`birdFlight` originally selected950 when source.y>destination.y and mirrored when source.x>destination.x. Both are reversed.

At AABE, bp+12 points to source and bp+E to destination (confirmed by forwarding at ABB0 to6DA9). AACD compares destination.y against source.y; moving down chooses TH930 relative20/21 = TH950/951. Otherwise choose relative16/17 =946/947. Add2 when carrying. AB2C mirrors when destination.x>source.x.

**Independent pixel proof:** `research-room-flight-audit/bird-summon-sprite-matches.json` contains ten exact matches against the original `research-object-completion/basket/frames` screenshots. These are the visible nontransparent bird pixels, not a whole-frame comparison. Example native run2042, original tick2769, x258/y74, trajectory step80: TH950 unmirrored matches all180 visible pixels; reversed runtime candidate differs170 pixels. Run2051, tick2777, x252/y78: TH951 matches187 pixels; reversed candidate differs145. All ten corrected candidates differ0.

The extraction/comparison script is `research-object-completion/audit-bird.py`; do not rerun it against modified runtime if preserving the audited snapshot. The earlier object completion report's two comparisons have been corrected.

## 2. An open calendar can permanently block an outdoor object

Both `departure` and `worm` set room.target28 and wait until room.height<=28 without checking scene. `app.js` advances `room.update` only inside. `room.leave()` preserves height/target. Therefore opening the calendar, leaving, and activating a qualifying outdoor object can leave the object task waiting forever.

Original departure A9D6–A9FA and worm B82B–B849 guard calendar closure by phase5 (inside). Guard the wait with the scene check. Conversely, clicking the perched bird must close the calendar **before** flight: BC86–BC92 explicitly does this, while the audited `clickObject(15)` flies immediately.

Independent `research-room-flight-audit/control-flow-probes.cjs` records both the outdoor worm and left-side airplane still busy after1000 ticks with height98/target28. Results are in `control-flow-probes.json`. These isolate the runtime wait; the original behavior is established by the source branches.

## 3. Nest feeding mirrors the bird AND the worm

AC89 sets DS5278=1, then creates/draws the carrying nest bird, redraws its state1, creates/draws worm12, and consumes the worm through A2A7. Only AD34 clears5278. Renderer A4E4 jumps to its mirror path when5278 is set, irrespective of object type.

The audited runtime has no corresponding flag. Apply the mirror throughout the temporary nest bird/worm sequence, including worm12 at rect(74,240,86,257). Merely mirroring type15 leaves the food pixels wrong. Nest bird rect is(70,222,90,247), state2 then1. Clear the flag after worm consumption, before the final flight.

Source confidence is high. The extra ordinary `research-room-flight-audit/nest-capture` run did **not** reach the intended nest route; it captured worm pickup/fly-away. `nest-mirror-matches.json` is empty and is not positive pixel evidence for nesting.

## 4. Caterpillar flight starts before the feeding animation finishes

Audited callback8 creates caterpillar5 and immediately calls `runObject(departure)`. `update` suspends active character animation while objectTask exists, so the remaining eating/handling poses freeze until the butterfly has left.

Original95D7–9602 sets5272, runs392B(action25) to completion, clears5272, and only then invokes A7D0. Callback8 itself only creates/places/draws the caterpillar (4ED3 callback dispatch; DS03BC adjusted by51AA).

This is not a harmless final-frame callback: `research-room-flight-audit/caterpillar-postcallback.json` extracts both original SCR20525 tails. Callback8 is at byte53; subsequent code includes an initial1×10 wait, shape100, sound10126, 2×10 frames, shape102, 2×10 frames, shape100,1×10, and shape101 with boy2×10/girl1×10 before terminator105. Start departure from action25's completion callback, retaining only object creation in callback8.

## 5. Fall is skipped before nest consumption and scene transfer

`place` early-returns for room surface0 nest, room surface9 chute, outside surface2 return, and outside surface1 discard. Native handling first computes the landing target, animates descent at9A46–9A67 when below the release position, writes the landed rect at9A78–9A8E, then dispatches these special outcomes: nest9AA6, chute9AFC, outside return9BCB.

In particular, `nestConsume` currently eats a worm/caterpillar at the release coordinates rather than after it lands on the nest. Sequence generic/plane fall first, then the selected surface's consequence. For outside discard, original9915–992B substitutes the animation destination from DS07A2/07A4; do not use the normal surface bottom for that route. Plane zigzag is suppressed for room surface9 at9961–9967.

## 6. Object state export truncates the broken pot and empty shell

Build code exports five words per type, but renderer A444 indexes state%10 into a table with stride5. These intentionally overlapping words are needed:

| Type | Ten original words starting at DS0936+10*type |
| --- | --- |
|0 egg|1,12,13,14,15,29,18,0,0,0|
|7 flower|0,9,10,11,12,13,18,0,0,0|

Thus egg state5 uses TH899 (relative29 in TH870), and flower state5 TH913 (relative13 in TH900). Export ten accessible words or preserve the flat table's indexing.

Also, AA04–AA18 redraws egg state5 **before flight**. Audited `departure` sets hidden=true for every type, prematurely removing the shell. Leave the egg's state5 shell visible until the final erase/delete; other departing types do erase their stationary artwork first.

## 7. Refused nut creates the pile in the wrong scene

Audited `offer(11)` action10 completion calls `create(14)` with default inside=true. Original A637–A641 passes inside=0 to857B. Existing piles increment to at most4; newly created piles must be outside. Creating the pile inside makes its room rectangle appear and changes which later squirrel sequence can display it.

## 8. Worm scene transfer preserves the wrong identity

Outside surface2 must erase/remove type13, find type12, and create type12 inside only if absent (9BDD–9C03). Audited code keeps type13 and merely sets inside=true. Later basket/worm lookup specifically searches12, so this can create duplicates and choose the wrong bird interaction.

Room surface9 likewise removes12 and creates outside13 only if no13 exists (9B51 onward). Audited in-place type mutation can leave two13 records when an outside worm already exists. Preserve the original destination deduplication rather than simply changing type/scene on the dragged record.

## 9. Generic long-fall sound begins too early

98D2 compares the fall distance to0x32; 98DB excludes airplane1, then98E4 plays10021. Audited generic `fall` uses>36. Correct threshold is>50;36 belongs to the separate plane zigzag condition9949. Flower break remains>60.

## 10. Ambient flyby incorrectly deletes the persistent perched bird

Original AABE accepts a specific existing bird index; negative means do not erase/delete an object record. Ambient flyby B9C6 passes−1 atBAB4, including outdoors. Audited `birdFlight` removes whichever type15 record exists unconditionally.

A room bird can persist while the player is outside. An outdoor ambient flyby must not delete it. `control-flow-probes.json` confirms the audited call does remove an indoor bird. Give birdFlight an explicit optional object to remove (or index equivalent). Summon and ambient flyby remove none; actual departure/worm transfer callers pass the intended bird. Outside worm pickup separately removes an existing bird as specified at B69E, so retain that deliberate cleanup.

## Findings checked without a new discrepancy

Food callback frames `arg<4 ? 6-arg :0` match original SCR1300 progression6,5,4,3,0. Pile callback7 and nut callback6 operate on the last object; promoting the serviced object before starting SCR1402/1403 preserves that contract. The full original scripts should continue to own their callback times. These checks do not establish whole-frame equality for all food/squirrel transients.
