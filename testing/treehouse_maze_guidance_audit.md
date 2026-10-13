# Maze guidance, victory and replay follow-up

Research-only bounded audit, 2026-09-27. No runtime edits. Audited source snapshot: `testing/output/treehouse/research-maze-guidance/audited-music-maze.js`, SHA256 `9747ea37cc0223c6462c631bfc146dbbbeb8d1931f5ecbe767428548043c246c`. Parent implementation continued during research; findings refer to that snapshot.

Primary source is original overlay1 in `research-resources/overlay1-disassembly.txt`, with exported original tables in `testing/treehouse/music-maze-tables.json`. All offsets below are overlay1 unless qualified. Native captures use ordinary input and read-only RAM. `research-maze-guidance/{new-control,idle-controls}/run.json` contains source-state/content/core digests and actions. The original restore point is the existing completed playthrough `correct-7.state`.

## 1. Automatic sound replay continually postpones idle guidance

Snapshot `update()` calls `hearTarget()` at targetDue; `listen()` then calls `resetIdle()`, resetting both target360 and hint900 deadlines. Consequently every automatic target audition postpones the hint deadline again, making the four-sign idle reminder unreachable under uninterrupted ordinary idle.

Original independent countdown semantics:

| Event | Source | Reset at completion |
|---|---|---|
| Handled ordinary user action |5870→826D|Target2018=360 and hint201A=900|
| Automatic target audition |58E2–58F4|Target2018=360 only|
| Automatic four-sign reminder |58A3–58CF|Hint201A=900 only|

When both deadlines have expired, hint has priority. After the hint completes, the next main-loop pass plays the still-expired target audition. Do not reset the target timer as part of the automatic hint.

This clarifies the earlier transient audit's blanket statement about reset-after-playback: that statement applies to the **handled user-input branch**, not the distinct automatic branches.

The four-sign reminder itself is correctly ordered0,1,2,3. Each6A13(direction,attempted,1) flashes red12ticks, then restores gray if attempted or white otherwise. There is no additional white wait between different signs. The correct-answer error hint is separate:6A13(correct,0,3) gives red12/white12/red12/white12/red12/white, after second or later error (5814–5827).

## 2. Victory reminder is missing

Original main loop checks victory scene17 at5878. If hint timer expires, **5887–5893→8BC4** performs:

1. Left/new-maze control red18ticks, then white (85D1).
2. Wait12ticks.
3. Right/return control red18ticks, then white (85FF).
4. Set hint timer201A=900 (8BE4).

An ordinary click on otherwise-unused victory background also invokes8BC4 at539C. It does not choose a control or change the song book.

The snapshot's update only runs reminders in phase `play`, and `click()` returns silently for unused win background. Add the same reminder generator for both entry paths. Native `idle-controls/state/after-01.png` has left red; `after-25.png` both white; `after-40.png` right red; `after-60.png` both white. RAM confirms all six song IDs unchanged. `native-control-evidence.json` records sampled color/timer values.

## 3. Replacing a won song must not change its visible victory page

Snapshot `endControl()` correctly calls `replaceSong()` before flashing the chosen control. But `song`, `title`, and draw's icon resolve directly from `songs[secret]`. Thus this mutation immediately changes the winner title, icon and score while still showing the victory page during the control flash and departures.

Original **52EA/5350→8ADB** updates the six-slot book at that time, but the already-loaded active SONG resource and displayed winner page remain the won song until the next scene is constructed. Preserve an active/displayed song identity independently of the mutable book slot through departure; select the new active song during the next round setup.

Native proof: `new-control` begins with book `[13,20,15,1,23,5]`, selected slot4. At `pressed` that slot already equals14, and remains14 throughout the control flash. Nevertheless the entire displayed header/icon region x30..241,y13..36 has **zero changed pixels** relative to before, including after30 while the frog is walking out. These measurements are in `native-control-evidence.json`. The book mutation is not deferred, and the screen is not repainted with song14.

## 4. Victory frog ascent uses the wrong delay

Snapshot `victory()` sets animation5 but yields `animation_delay[4]`, which is2ticks. Original **86B1–86BA** indexes the delay using local animation5. Original table DS542+5 is3ticks.

There are exactly36 upward moves, two pixels per move. Correct ascent time is108 native ticks; the snapshot takes72. Source86A8 limits36 and86FB/8702 passes animation5 to resident8299. Use delay5, not delay4. This finding is directly source/table-backed; a newly synchronized complete ascent comparison was not run here.

## 5. New-round frog left exit is shortened incorrectly

Snapshot `endControl(true)` invokes `walkFrogLeft(frogPoint[1]+16)`. On the victory screen frogX=130, so this travels146pixels and stops at−16.

Original **52F4–5308** invokes7AA6(direction0,actor1,interrupt1). The scene9 direction0 path is162pixels plus16 terminal extension, total **178pixels**. Outgoing7AA6 moves the actor from its current location; it does not reset it to scene9's player center. Starting frogX130 therefore ends at−48. With one initial2tick frame and89 two-pixel movements at2ticks, this portion takes180ticks; the snapshot's146pixel walk takes148.

The first introductory frog-left exit really is78pixels, because **88E4** temporarily subtracts100 from path distance and8905 restores it. That special case is not applied when leaving a completed maze. Keep the current victory frog origin and use the full178pixel distance; its invisible tail still delays the following player departure and RNG voice call by32ticks.

## 6. Small replay feedback omission before any notes are earned

Snapshot's replay-hit branch calls `hearSong()` only when earned is nonzero and otherwise returns without visual response. Original **53B5–53F4** always colors the replay button red. With zero notes,53DF waits12ticks and then restores its normal disabled gray color via7038/6FB0; with notes, it plays the collected melody before restoring. The original gray control is therefore still responsive to a click. This is a small visible feedback omission, not a missing music workflow.

## Scope

Existing fixes for wrong-guess retained drawer contents, blank question button, note-level audition highlights, introduction and ordinary walking were present in the snapshot and were not re-reported as missing. Scene exit through app.setScene already replaces a won song and persists state, so the top-right exit is not incorrectly reported as losing replacement history. No complete waveform/backend parity claim or exhaustive cancellation audit is made here.
