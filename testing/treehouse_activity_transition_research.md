# Room ↔ activity teleport transitions

Primary-source research, 2026-09-27. No runtime files changed. This closes the resident `5233/5338 → TH980 → TH1100+variant` feature identification and sound-ownership question.

## Sources and evidence

- Original executable: `testing/output/treehouse/disassembly/unpacked.bin`, SHA256 `f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f`. Hex addresses below refer to `research-resources/main-disassembly.txt`.
- Original TH.DAT SCR, SHAP, SHPL resources: `testing/output/treehouse/extracted-v2/manifest.json`. Machine-readable original scripts: `research-activity-transitions/scripts.json`.
- Implementation table: `testing/treehouse/activity-transition-poses.json`. For each SCR it supplies every displayed pose, absolute actor coordinates, original SHAP IDs, dimensions, palette, authored delay, sound operands and callback operands. It is a static resource interpretation, **not yet an independently pixel-compared reconstruction**. `nominal_tick` sums authored display delays; it excludes opcode service/load time and audio-tail waits.
- Ordinary native capture: `testing/output/treehouse/research-activity-transitions/native-a/`. `driver.json` records inputs, per-callback read-only state/audio headers; `frames.jsonl` supplies every original frame; `audio.wav` is the shared native audio stream. `native-events.json` links state/sound transitions directly to frames. Capture script: `research-activity-transitions.py`; analysis: `research-activity-transitions/analyze.py`.
- Starting state: `entry-verified-a/state/after-click.state`, SHA256 `9eea3d004a365f901fc653e633fd497b9024256fd646b93d4c649839e4e4d391`. All four branches restore this state, move/click normally, enter the activity, click the normal top-right Exit control, and return. No RAM modifications. The first branch has native run1826..2151 for outgoing motion and2787..3246 for return. Eight entry/return captures completed.

## What the user does

This is the normal room-to-activity teleport, always used on the original main path. It is visually a glowing ring opening beneath the child, the child turning into a blue bubble, and the bubble travelling to the chosen activity. The reverse sequence brings the child back and closes the ring.

|Room target|Hotspot|Room rectangle (top,left,bottom,right)|Entry handler|Variant|Outgoing SCR|Return SCR|Restore animation background on completion|
|---|---:|---|---|---:|---:|---:|---:|
|Piano/music|1|(175,7,200,106)|12F0|0|1100|1104|1|
|Nature booklet|2|(99,122,119,147)|132D|1|1101|1105|1|
|Theater curtain|13|(121,49,145,77)|1367|2|1102|1106|0|
|Board game|14|(181,138,200,223)|13A4|3|1103|1107|1|

The last column is wrapper `419D` argument `bp+C`, **not sound enable**. All eight1100-family scripts have sound enabled (`bp+A=1`, copied toDS5822 at4332). Earlier working notes mistook this parameter for sound; native theater capture decisively confirms10032/10033/10035 are played. The differing parameter preserves the final closed theater curtain.

Each handler calls `38BC(1)` first. This clears deferred wakeDS5826; if pose4 is sleeping, scene5 performs interrupted wake action22 and refreshes status, while the other branch removes object8 through857B. It then sets pose0 and reschedules fatigue. `5204` next calls585B: pose1 performs action30, pose2 performs action29, both returning the child to central pose0. There is no hunger/fatigue threshold preventing entry. Source:38BC..3923,585B..588D,12F0..13DB; pose/action model in `treehouse_character_research.md`.

The input is one ordinary click. Cursor hiding begins at520D and ends5300;530D hides it again for return until5437. No room hotspot dispatch runs inside the synchronous transition. The generic SCR interpreter does not cancel these scripts on another click/key: wrapper cancellation at487E applies only to base70; first-frame early exit is not requested. The later audio wait577E and explicit60-tick pauses can be interrupted by input, so do not implement a universal click-to-skip of the entire teleport. Source:4855..48BD, runtime timing report §4.

## Outgoing state sequence

`5204` receives `(variant, restoreBackground)` in source push order. Its ordered actions:

1. Hide pointer; center/wake child as above. Load TH shape group980. SetDS5520=1 (enable foreground-object compositing) andDS5254=1 (draw standing child over the ring on each display).
2. Start DIGISND1015 at5233. Run TH SCR980 with its own SCR sound disabled, no restore-on-completion, all other placement flags0. This opens/pulses the ring. SCR980 has no authored sound instructions. Its18 displayed shapes,8 ticks each, are relative `1,2,3,4,5,6,7,8,9,6,7,8,9,6,7,8,9,6`; authored duration144ticks.
3. SetDS55F4=1 and redraw child through39BF(1,1,1,1,0,0), then clear55F4 and5254. This captures the child’s backing with the open-ring relative shape6 already present. Free the loaded980 group (captured background retains the ring).
4. Board only:61FF(1) saves/draws open board inlet at rectangleDS03D6 `(184,160,195,169)`, using TH900 relative shape27 = SHAP927, palette900. Native screenshots show the opening on the board beneath the character.
5. SetDS5528=DS01C8=168, the central child’s bottom/depth threshold. Run loaded TH1100 group, SCR1100+variant, exact authored rectangle, callback5442, sound enabled1 and completion restore flag from table.
6. ClearDS5528 and5520. Board only: wait60ticks (interruptible56DB), then61FF(0) restores the board inlet backing.
7. Save variantDS5A10; show cursor. The room caller then waits another60ticks (interruptible56DB), tears down room3217 and invokes the activity overlay. After overlay returns it calls1F24 with bp+6=0, which redraws the room and runs the return sequence.

Source:5204..530A,12F0..13DB,61FF..62D0. At normal activity arrival pose0 persists, andDS5A10 records which return script to use. The child is temporarily absent visually; this is not a new persistent character pose.

## Return state sequence

Room rebuild `1F24` with bp+6=0 deliberately omits drawing the child. It loads group980 at2209..2216, saves the ring’s clean underlying rectangleDS0216 `(162,150,174,197)` intoDS5252, draws normal room objects, then calls530D at22BA. It releases group980 after530D returns.

1. Hide cursor. Board only: open inlet through61FF(1).
2. SetDS5520=1. Start DIGISND1015 at5338. SetDS5A1C=1 and play SCR980 (no standing-child overlay:DS5254 is still0). Completion forcibly stops1015 through419D cleanup4A82, then clearDS5A1C.
3. SetDS5528=168 and run TH1100+variant+4 with callback5442 and sound enabled1. Restore-background flag is1 except theater0. The bubble travels to the central ring; callback operand1 restores the child behind the transformation.
4. ClearDS5528, set5254=1, play SCR981 (reverse ring sequence) with SCR sound disabled. Shapes: `6,9,8,7,6,9,8,7,6,9,8,7,6,5,4,3,2,1`,8 ticks each,144ticks.
5. Clear5254 and5520. SetDS529C=1, call39BF(1,1,1,1,0,0), clear529C. This redraw unions the character backing with the ring rectangle, restores clean floorDS5252, captures new child backing and draws the child, removing the ring completely. FreeDS5252.
6. Board only: wait60ticks and restore inlet through61FF(0). Show cursor. Caller refreshes portrait/need status through575D/579B, then returns to normal room loop.

Source:2196..22D4,530D..5437,39BF..3C0F.

## Exact rendering ownership

TH SHPL980 declares firstSHAP981,count9; SHPL1100 declares firstSHAP1101,count11. The numeric table expands relative SCR shape numbers accordingly. Ring origin is(x150,y162), rectangle width47,height12. Open still is SHAP986 at(150,162), palette980. SCR1100-family uses its own authored bounds and absolute offsets, **not character-pose offsets**.

|SCR|Bounds (t,l,b,r)|Displayed poses|Authored duration|
|---:|---|---:|---:|
|980,981|(162,150,174,197)|18 each|144 each|
|1100|(118,38,180,187)|13|91|
|1101|(108,135,175,187)|13|117|
|1102|(118,49,175,187)|18|162|
|1103|(118,150,184,187)|13|91|
|1104|(118,38,180,192)|13|91|
|1105|(106,40,172,199)|12|84|
|1106|(118,38,180,197)|18|162|
|1107|(118,38,190,197)|13|91|

Standing child draw uses the selected BOY/GIRL still, not a shape in TH1100. Ring pass setsDS5254 so rendererC9ED draws ring actors first, then39BF child, then foreground room objects. DS5520 enables the object pass; object.bottom>DS5528 qualifies, current scene membership must match and it must intersect the dirty rectangle. SourceCA77..CB47.

In outgoing110x, the child initially remains in the animation backing. SCR callback0 happens when relative shape5 (blue transformation) is displayed:5442 restores saved child backingDS5310, which contains the open ring but no child, then redraws all overlapping current-scene room objects. Callback1 during return invokes8EE4 to restore objects’ backing, draws the open ring + child through39BF with55F4=1, then redraws all overlapping room objects. The callback swaps the animation surface/viewport so the background change persists across following frames. Source5442..5575,3AED..3B49.

Theater has a second special background path at44D5..44F4: when base1100 andvariant%4==2, restoreDS55EE (room curtain background captured before the closed curtain is drawn at20F8..212x). Thus curtain actors1109..1111 animate over the bare opening. Restore-on-completion=0 keeps the final closed curtain. Music/nature/board restore their final animation backing at4ACF..4B14 so the last travelling bubble does not remain visible.

For a retained canvas implementation, model these callbacks as changes to the clean transition background, render current SCR actors, then the foreground object pass. Merely appending all sprites to normal `renderRoom()` would leave the child visible after callback0, lose the ring after the980 group is released, and paint the wrong curtain backing.

## Sound ownership and measured timing

1015 is an actual whole-buffer looping sample: native header `(flags129, rate11000, bits8, count12768, loopStart0, loopEnd0)`. Its duration cannot determine when to stop it. Outgoing starts it before980 and **does not stop it at980 completion** because wrapper base980 skips general cleanup. It continues until the first sound in110x replaces it on the shared digital channel. Return starts1015 for980 andDS5A1C forces stop at the end of980 before110x begins. Source5233,5338,4A56..4AB2; native driver trace confirms both.

|SCR|Sound sequence|Callback (byte offset → operand)|
|---:|---|---|
|1100|+69:10034; +146:10035|+87→0|
|1101|+69:10034; +146:10035|+87→0|
|1102|+34:10032; +113:10033; +190:10035; +259:10032|+131→0|
|1103|+54:10034; +156:10035|+87→0|
|1104|+24:10035; +126:10033|+122→1|
|1105|+24:10035; +116:10033|+112→1|
|1106|+39:10032; +88:10035; +180:10033; +254:10032|+176→1|
|1107|+24:10035; +126:10033|+122→1|

All110x wrappers wait for their final sound using577E(0), then forcibly stop it before completing. Consequently transition duration exceeds sum of displayed-frame delays, notably theater. A click/key can terminate this *audio tail* wait. 10032 sample count11320,10033 count8024,10034 count16248,10035 count11584, all digital11000Hz/8-bit, no loop. SCR980/981 themselves are silent.

Native baseline absolute tick table below includes loading/service time, not just authored delays. Capture callback ticks may observe a change one callback after the CPU performs it. All branches have identical initial room tick2562 and click after a20-callback pointer movement.

|Branch|1015 first observed|First replacing sound|Second sound|Outgoing busy cleared|Saved variant updated|
|---|---:|---:|---:|---:|---:|
|Music|2589|2765:10034|2800:10035|2863|2863|
|Nature|2589|2771:10034|2816:10035|2878|2878|
|Theater|2589|2756:10032|2801:10033;2846:10035;2891:10032|2952|2952|
|Board|2589|2758:10034|2807:10035|2870|2929 (extra board pause)|

Music return:1015 active3407, forcibly off3552;10035 begins3556;10033 begins3612; sound off and ring close begins3656; busy clears3800. Nature return:1015 active3407/off3552,10035 at3556,10033 at3605,ring-close begins3648,busy clears3793. Theater return has its overlay curtain closing before room redraw:1015 active3439/off3584;10032 at3586,10035 at3613,10033 at3676,10032 at3721; ring-close3782,busy clears3927. Board return matches music sound/ring times then has its own final60-tick inlet pause. See native-events.json for image paths and runs.

## Completion scope and limits

The ordinary boy/central-pose path is captured for all eight directions. Exact girl/sleeping/off-center entry frames were not captured here; their prerequisite action paths are directly established by source and existing character research. The table is ready for resource-driven rendering, but no whole-frame pixel-equality claim is made for a new transition renderer. The native captures provide those targets. Runtime implementation remains the parent agent’s work.

## Follow-up: callback mutation is not a presentation

The parent’s initial resource renderer matched all192 distinct return states, while each outgoing path had one326-pixel child-removal discrepancy: displayed pose4 for music/nature/board, pose7 for theater. Source audit resolves this without adding a deadline to generic callbacks.

The opcode16..19 handler `BFD4..C023` has **no clock/deadline check**. It calls the selected callback atC019, advances the script pointer3, and jumpsC363 to immediate dispatch. Thus callback0 executes after the preceding frame has been displayed but before the next frame’s deadline. This is correct interpreter behavior.

Callback5442 writes only the animation backing image. At544B..545C it selects the animation instance asDS205A and calls70B6. Routine70B6 swaps far pointers atinstance+00/+02 with+2E/+30 (`70BF..70EA`), selecting the backing buffer. Callback5442 then restoresDS5310 or draws the child/objects. At5537..554C it resets the origin, swaps pointers back and restores the previous surface. It expands the animation dirty rectangle at554F..556B. It never copies the modified backing to the physical destination.

Only display opcode1 checks `now >= lastDisplay+delay` (`BE03..BE30`) and callsC78A. That routine composesC9ED if needed (`C7A9..C7B8`), then copies the dirty region from the animation surface to its destination (`C7C3..C7FB`, sourceinstance,destinationinstance+2C). Therefore visible child state and displayed actor slots must be committed together at an actual display boundary.

Implementation consequence: keep callback-updated `pendingChildVisible` as backing state, and copy it to displayed child visibility **inside the actual opcode1 presentation step**. Do not read the immediately mutated backing state while painting the old `Animation.display` slots. Do not delay every generic callback until its deadline; callbacks may update nonvisual state and are immediate in the executable.

One additional distinction: native opcode7 (`BFBD..BFD1`) callsC9ED to prepare the offscreen composition and setsinstance+56=1; it does not present it. In the current JavaScript interpreter `snapshot()` also runs for opcode7. A hook attached indiscriminately to every `snapshot()` is therefore not an exact presentation hook. Hooking the opcode1/frameUpdates increment explicitly avoids that ambiguity. An `update()` call may consume a display and the following callback in one host tick, so latching only after the complete update returns can still select the future child state.
