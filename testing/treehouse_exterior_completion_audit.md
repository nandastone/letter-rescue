# Exterior completeness audit

2026-09-27. Bounded research against the pinned DOS v1.1 executable and original DAT resources, compared with `treehouse-demo/app.js`, `room-character.js`, and `preferences.js`. No runtime changes. Main addresses refer to `output/treehouse/research-resources/main-disassembly.txt`; overlay5 addresses refer to that directory's `overlay5-disassembly.txt`. The interrupt encoding `CD 3F 07 74 00` resolves to **overlay5:0074**, not a nonexistent seventh MZ overlay. Source identities are in `treehouse_executable_research.md`.

Native evidence: `output/treehouse/research-exterior-audit/{native,credits-window}`. Reproduction scripts `capture.py` and `capture-credits.py` restore existing ordinary-play states and issue only mouse input/waits. RAM is read only. Each capture includes complete frames, saved states, RAM, and recorded input actions. Activity transitions and telescope handoffs were deliberately excluded.

## 1. Returning outside is a separate mode, currently missing

Main **ACE–D13** sets scene4. Before friend selection, DS5692=0 and there are nine hotspots; afterwards there are seven. The initial mode draws the title, copyright, credits and two children. The selected mode draws only TH64 SHAP1, cloud, and exterior objects; it has neither child nor title/copyright. `native/state/outside.png` is an ordinary return from the room demonstrating this distinction.

Selected ladder click goes directly through main **743 → 75D → 953 → D16**, avoiding greeting and climbing scripts. Room return goes through **95D → ACE(1)** and resets reminder timer201A to10800. `native/state/room-again.png` demonstrates the ordinary selected return route. Current `setScene('outside')`, `outside()`, `activate()` and `enter()` always recreate initial chooser/entry behavior; the sidebar “Choose another friend” is consequently standing in for the original exit-to-yard control.

Fresh mode also accepts Ctrl+ladder as a shortcut (main743–7CC); lower priority than the missing normal return route.

## 2. Exterior click controls are absent

The nine rectangles are at image2E8F0; each is `(top,left,bottom,right)`, exclusive. Only indices0–6 remain active after choosing a friend. Original dispatch is at mainA62. Object hit testing occurs before these controls.

| Index | Rectangle | Original action | Current coverage |
|---|---|---|---|
|0|2,45,52,122|Cloud: increment sharedB4 modulo7; call2425(1); sound1044.|Cloud change exists inside, but outside neither draws nor accepts it.|
|1|64,232,184,290|Ladder: selected friend returns straight to room.|Missing.|
|2|78,132,106,164|Birdhouse: main60E0 runs TH SCR1060, schedules ambient.|Script used by random ambient; click missing.|
|3|128,202,160,230|Hollow: A2F enters resident scene14/main3D39, described below.|Whole reachable scene missing.|
|4|177,14,200,92|Pond: main608C plays TH SCR1000+cycle, then cycle=(cycle+1)%3.|Random ambient exists; click missing.|
|5|6,5,35,38|Sun: main9EE plays **TH SCR1301**, SHPL1300; schedule ambient.|Missing. Do not play food-eating SCR1300.|
|6|33,217,64,258|Window: main96F calls4B50, or sleeping snore sequence.|Missing.|
|7|105,80,184,128|Initial boy selection.|Covered.|
|8|109,128,188,174|Initial girl selection.|Covered.|

All non-ladder exterior novelty actions are gated on DS5692 being nonzero. Cloud2425 centers relative shape`1+cloud` of **TH SHPL170** in rectangle0; redraw restores the clean sky first. SharedB4 is the same cloud selection used inside. Pond cycle DS5570 resets0 on every selected exterior setup atC9E. Sun source9EE passes base1300, variant1; native SCR1301 bounds are `(13,12,28,31)`.

`native` captures exercise hollow, sun, birdhouse, pond and ladder; intermediate frames are retained, so settled screenshots need not visibly show a short animation.

## 3. Squirrel hollow is a complete omitted interaction

Entry main**3D39** loads TH SHPL1400, draws **SHAP1448** opaque@(0,0), and TH SHAP8/SHPL6 exit@(304,1). Initial nut count is0 on every visit. Native `hollow.png` is the exact blank entry screen; `nut1.png`, `nut2.png`, `nut3.png` are cumulative native placements. The two sleeping squirrels and hanging sign are interactive.

Geometry at image2E8F0+19C:

|Index|TLBR|Effect|
|---|---|---|
|0|81,138,109,184|sound1019, TH SCR1401/SHPL1400; upper squirrel|
|1|95,102,126,148|sound1019, TH SCR1400/SHPL1400; lower squirrel|
|2|131,206,164,263|Toss one nut, maximum3 per visit|
|3|26,154,73,224|Play blocking DIGISND20001; stop audio afterwards|
|4|18,82,198,271|Stay-inside region, no action|

Escape or a click **outside rectangle4** exits. Otherwise dispatch the first matching rectangle0–4. Entry background is restored after exit via ACE(0). There is no persistent nut reward or shared exterior nut-pile mutation in this routine.

Nut sequence **3E66–3F08**:

1. If local count==3, do nothing. Get TH **SHAP937** (shared **SHPL930**, relative7). DS5780 is initialized with930 at main597–5A4; DS577E is the separate900 handle. The earlier version of this report incorrectly identified907/900.
2. Source top-left `(x234,y140)`. Destination selected by preincrement count: `(220,99)`, `(195,77)`, `(219,78)`; data DS0386/038A.
3. Increment local count. Play sound10035. Animate via6DA9 with erase=1, delay=8, step=12, preserving the underlying close-up.
4. Play sound10033 and draw TH **SHAP1447**/SHPL1400 at destination offset(-4,-4): `(216,95)`, `(191,73)`, `(215,74)`, mode10.

Native `squirrel-one.png` and `squirrel-two.png` are settled followups; the saved callback frames contain the wake movements. Original SCR1400 bounds `(81,132,126,177)` and SCR1401 use the same bounds, with authored sprite offsets. The native view is titled “Home Sweet Home”, so this is separate from the outside nut-pile visit animation1402.

## 4. Title credits are frozen at panel2

`outside()` always draws TH SHAP12@(10,52). Original mainB73 sets DS57DA=-1 and calls overlay5:0074(0); unselected exterior idle main5EE–61A calls0074(1) once its long-clock deadline expires.

The routine restores TH64 SHAP2@(2,0), advances `credit=(credit+1)%8`, and draws monochrome **TH SHAP10+credit** (SHPL6 relative4+credit). Display duration is600ticks for credit0 and360ticks for every other panel. Rendering coordinates are `(x,y)`:

|credit|shape|position|
|---|---|---|
|0|10|12,60|
|1|11|12,55|
|2|12|10,52|
|3|13|10,52|
|4|14|10,52|
|5|15|26,50|
|6|16|24,49|
|7|17|27,57|

At first setup draw directly. Subsequent changes update only TLBR`(46,10,99,148)` (DS142C), preserving children/copyright outside this rectangle. Foreground color is0 in VGA; source switches to15 for graphics modes3/4. All eight panels independently captured under `credits-window/state/credit-0.png` through `credit-7.png`.

## 5. Exterior friend window and idle prompts are missing

Window handler **96F–9B8**: if sleeping (pose4), play DIGISND10123 twice, waiting30ticks after each. Otherwise call4B50. This chooses a status variant in priority order:

|Condition|Variant|
|---|---:|
|fatigue>=4, pillow not inside|2|
|fatigue==4, pillow inside|3|
|fatigue>=5, pillow inside|4|
|otherwise hunger==4|5|
|otherwise hunger==5|6|
|otherwise|7|

Pillow existence/inside check is type8 lookup86F8 followed by record+4. Fatigue branches set fatigueDue=now+3600; hunger branches set hungerDue=now+3600. **4C0F** loads selected BOY/GIRL SHPL20400, initializes SCR20400, runs **20400 → 20400+variant → 20401**, restoring its saved window backing at completion. It resets timer201A to10800 and callsBC43 (ambient scheduling). Native `credits-window/state/window-active.png` and `window-ended.png`, plus intermediate callbacks, capture the normal variant7 path.

Outside mainloop **61F–6B1** also services fatigue deadline first, then hunger deadline, while selected and awake. Existing `RoomCharacter.update()` early-returns outside after environment processing, so neither need advances there. Reuse native need progression but select outside status scripts rather than indoor body actions:

- hunger3 → variant5; hunger>=4 → variant6 (5578–564D).
- fatigue3 → variant3 with inside pillow, otherwise2; fatigue>=4 →variant4 with inside pillow, otherwise2 (564E–575A).
- Existing other-need==5 suppression and cross-deadline spacing remain applicable; these are not unconditional prompts.
- When both needs<4, awake, and timer201A reaches0: automatically run variant7 (**679–6B1**). This is a separate10800tick window reminder, not the20–30second environment animation timer.

The runtime already has environment scheduling, random pond/birdhouse motion, worm/bird behavior, food and squirrel-pile events. Those do not cover the friend-window reminder or need timers. Sleeping wake/time semantics should continue to use existing clock behavior; this audit did not validate every sleeping wake edge.

## Scope limits / lower priority

Native Escape on exterior calls the DOS shutdown routine D51:54E8 (main6DC). Web Escape currently does nothing there. A browser does not need DOS process exit, so this is not grouped with missing game content above. Preferences already expose sound, printing, maze level, save/load, help and native speed preference; this slice found no additional concrete omitted gameplay workflow there.

The findings above are source/capture-backed omissions, not an assertion that every remaining resident path has been exhaustively verified.

## Followup: credit4 presentation boundary and hollow help

The original `credits-window/state/credit-4.png` was captured after DS57DA became4 but before the new graphics buffer was presented. Its RGB pixels are **identical to credit-3.png (0 differences)**. This is a reference-capture timing issue, not a credit4 source exception. Restoring the unmodified `credit-4.state` and waiting61 callbacks produces `credits-followup/state/credit4-settled.png`: index4, tick2238, showing Susan Greene / Jenny Martin / Muffy Vaslo. The stale reference had index4 at tick2186. The corrected full frame differs from the stale frame by659pixels, bounded x66..145,y52..94. Use the settled reference for credit4. `capture-followup.py` reproduces the restore/wait and help capture.

Hollow F1 uses **context19** (TXT41119). The scene14 word in the main5DC7 jump table is5D9A; that branch maps selected DS5692!=0 to19 at5DAC. Native `credits-followup/state/hollow-help.png` confirms the generic THE TREEHOUSE panel: “To play, just move the cursor to any object and click. Explore and have fun!” The runtime default selected19 is correct.

## Followup: nut flight sprite and retained cursor

Nut SHAP937 is12x9 pixels. Independently drawing it with SHPL930 over native run2031 (the pre-click hollow with pointer at229,145) reconstructs **all six entire native flight frames with zero differing RGB pixels**:

|Native run|Top-left x,y|Whole-frame different pixels|
|---:|---|---:|
|2066|234,140|0|
|2075|231,131|0|
|2084|228,122|0|
|2093|224,114|0|
|2103|221,105|0|
|2112|220,99|0|

Each reference is located by `run` in `native/frames.jsonl`. The cursor remains visible at229,145 through the complete nut flight. Main6DA9 contains no mouse hide/show; caller3E66 does not hide it either. Hiding it merely because this flight is busy introduces a visible mismatch.

## Followup: leaving while asleep and waking outside

Ordinary native route and evidence are in `sleep-yard/`, reproduced by `capture-sleep-yard.py`. It restores the prior human-play `research-character/sleep-a/state/asleep.state`, clicks the room ladder, clicks the exterior window, waits, then returns inside. `sleep-state-summary.json` extracts source-backed state without modifying RAM.

- `asleep-outside`: scene4, pose4, fatigue1, no pillow object. Room exit **128A–12BB** only calls cleanup3217, resets the pointer and returns. Caller95D redraws the yard. It does **not** call38BC or any wake action. Do not interrupt sleep on room→yard or yard→room navigation.
- `snore-ended`: still scene4, pose4, fatigue1, no pillow object. Exterior window clicks preserve sleep.
- Natural wake is checked by shared clock **3181–31D3** when its wake-service argument is enabled. Source checks pose4 and either DS5826 deferred flag or current **minute==DS5592**. Modal flagDS52E2 defers by setting5826=1. Otherwise it callsCD40(-1,-1,1) (wake announcement DIGISND11028, no time digits), then38BC(0).
- **38BC–3923** clears deferred5826. In scene5 it plays action21 (natural) or22 (interrupted) and clears the nap note. Outside scene5 it instead invokes857B(type8,inside1): return/create the pillow **inside** at its default `(132,106,146,118)` TLBR. It performs no outside character wake animation. Then pose becomes0 and fatigue is set to`1+3*interrupted`; setter581A also schedules fatigueDue=now+14400.
- `naturally-awake-outside`: scene4, pose0, fatigue1, pillow `[type8,state1,inside1,132,106,146,118]`. `returned-awake` retains that pillow after ladder return to scene5.

Wake hour/minute words retain their old values in native RAM after waking; pose gates their use. Clearing a runtime wakeTime is a valid representation if future rendering and checks use pose consistently. Native minute-only matching is an implementation detail to consider separately from the user-visible sleep-preservation fix.
