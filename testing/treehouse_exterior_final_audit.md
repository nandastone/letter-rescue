# Final bounded exterior/runtime audit

2026-09-27. Research only against the current `treehouse-demo/{app,exterior,room-character}.js` and pinned original resident listing `output/treehouse/research-resources/main-disassembly.txt`. No runtime edits. This follows `treehouse_exterior_completion_audit.md`; the previously reported controls, credits, hollow nuts, cursor, window scripts, and yard sleep route are now implemented.

## Concrete remaining findings

### 1. Hollow natural wake takes the indoor branch

Current `RoomCharacter.wake()` directly creates the pillow only when `scene()==='outside'`; hollow instead queues action21. Original **38D5–390A** checks `scene==5`: only inside plays21/22; **all other scenes** create type8 inside and skip the full-body wake animation. Reachable route: offer pillow while tired, leave to yard, enter hollow, remain until wake time. Current result is an invisible indoor animation and busy delay in the squirrel room, with pillow return delayed until its callback. Correct branch is inside versus every non-inside scene. Hollow clock loop **3DB1–3DBD** explicitly calls2F86 with wake service enabled, so sleep continues there.

### 2. Sleeping early return disables environmental events

Current update returns from the pose4 branch before environment/shelf service. Native **D8E** and **6C0** call8742 during both awake and asleep loops. Original **874B–875F** gates on selected character and absence of chalk tool, not sleep. Sleep is checked only for the indoor spoken-status random branch at **88B2–88C1**. Birds, nest/spider, pond, food expiration and squirrel-pile visits remain active during naps. Keep sleep suppression on needs and friend speech while allowing the environmental service.

### 3. Indoor shelf nut is serviced in yard

Current `update()` enters its shelf-nut search even in selected outside mode, after the non-inside early-return condition. A type11 nut whose inside rect is on the shelf can therefore expire while the player is in the yard and play SCR1403 over the yard. Native **8762–876E** explicitly gates this entire nut check on scene5, then **87E4–880B** dispatches1403. Gate the shelf-nut branch on inside. General exterior timed pile1402 is separate and remains valid.

### 4. Initial chooser draws and accepts saved exterior objects

Current `outside()` calls `resident.drawObjects(screen,false)` unconditionally, and outside `activate()` calls `resident.begin(x,y)` before checking `selected`. Original setup **B69–CCB** draws objects only in the selected branch (**CB4–CC3**), and original input **6F2–711** calls object hit serviceA83A only when DS5692!=0. A saved or retained exterior paper airplane, egg, flower, food or nut pile can appear and respond on the initial two-child welcome screen in the runtime. Ordinary reproduction: transfer an object outside, use “Choose another friend” (or reload with saved outside objects), then inspect/click it before choosing a friend. Gate object drawing and object hit dispatch to selected mode; retain the objects for the subsequent selected yard.

## Exact resident-loop order for the sleep fix

|Scene|Ordering|
|---|---|
|Inside5|D29:2F86 natural-wake/time service → clock/cloud maintenance → D8E:8742 → drawing-tool/input service →113E hunger then fatigue.|
|Outside4|5DF:2F86 natural wake → initial credits if unselected →61F fatigue then hunger and679 idle-window reminder when selected/awake →6C0:8742 →18CD input.|
|Hollow14|3DB1:2F86 with wake enabled →3DC2:18CD input. No8742 environmental service.|

Within8742, the inside shelf-nut branch precedes the general random-ambient deadline; timed food and long squirrel-pile handling follow. Sleep alone must not prevent those calls. Busy scripted animations and modal sound waits still own control until their native calls complete. Natural wake is checked before these ordinary environmental events, but not by reentering through a blocking script.

No new issue found with hollow Escape routing: although key dispatch passes `inside`, current `navigateScene()` explicitly redirects that hollow route to outside. This was checked before listing findings.
