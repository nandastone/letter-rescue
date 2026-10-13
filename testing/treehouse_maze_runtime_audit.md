# Musical maze runtime audit: transient behavior

2026-09-27. Research only; no runtime changes. Audited `treehouse-demo/music-maze.js` against original overlay1 and resident source, the two earlier maze research reports, and native callback recordings. Frozen audited source is `testing/output/treehouse/research-maze-audit/audited-music-maze.js`, SHA256 `374a9d33a2bf4372131844d6906d76f62fe2c604186d8cfca7a4d90f14f03bed`.

Existing settled-scene and drawer-position comparisons remain useful. They do not exercise the missing first frames, audio-dependent waits, input interruptions, or transient redraw states below. Addresses are overlay1 unless marked resident.

## 1. Victory controls and repeated entry skip required choreography

**Runtime:** `click()` calls `reset()` immediately for win control7 and `leave('music')` immediately for right control6/ladder2. `reset()` only animates when `introduced` is false; subsequent resets instantly put the player at the new node center.

**Original:** 52D9..537D:

* New maze: update history, left control red18ticks then white (85D1); frog voice and frog walks out left; player voice and player walks out left; initialize ordinary maze7062 and bring player in from direction2. Do not replay the large-scene first tutorial here.
* Return: update history, right control red18ticks then white (85FF); voice; player follows scene9's direction1 ladder path; then leave.
* Every fresh piano→maze entry calls862D(introduction=true) at5242. The session's first flag controls the tutor and whether player disappears directly or walks left after the large-scene frog departs. It does not mean all later entry animation is omitted.

**Action:** separate fresh-entry, new-round initialization, win-new-round exit, and win-return sequences. Readable buttons should call the same transition entry points as canvas controls. Keep settled win behavior disabled until the arrival playback completes.

## 2. Walking omits each segment's stationary frame0 and delay

**Runtime:** `walk()` initializes frame0, immediately moves one step/increments toframe1, then yields. `walkFrogLeft()` does the same and hardcodes3ticks.

**Original:** incoming799A..79BF and outgoing7B70..7B95 call resident825D for **each segment**. 825D sets the animation delay, resets shared counter to−1, draws frame0 without movement, and waits. Only then do the loops move a fixed step through8299 and wait. Therefore every segment has one additional stationary initial frame and one additional animation delay. Normal left/right delay2, up/down3, climb16. All exported current path distances divide evenly by step size, so no remainder workaround is needed.

First-scene frog exits left78pixels. It uses animation4/delay2, not the runtime's3. Native duration is initial2+39×2=80ticks, excluding sound/call overhead; current helper takes39×3=117ticks and lacks the initial frame.

**Action:** show frame0 and yield the table delay before the movement loop. Preserve the source's frame reset at each segment. Reuse that logic for the shortened frog-left path instead of a differently timed helper.

## 3. Frog pointer begins one pixel too high

**Runtime:** `pointFrog()` uses `fy` for the rectangle's bottom when computing pointer start Y.

**Original:** resident809E registers a frog with rect `(fy-38,fx-17,fy+1,fx+18)`. Overlay8288 reads bottom from state9C6 at82BF and uses it in all four offset cases. The runtime's center `(fx,fy-19)` is correct for these positive coordinates, but bottom must be `fy+1`.

| Case | Correct startY |
| --- | --- |
|Right/below|fy−10|
|Right/otherwise|fy−17|
|Left/above|fy−17|
|Left/otherwise|fy−9|

Keep the current X offsets and staircase algorithm. Changing the initial Y also changes the later integer path, so shifting the finished sprite by1 is insufficient.

## 4. Reward roller and falling note skip inclusive endpoints

**Runtime:** `reward()` increments roller from60 before its first yield, decrements before the first retraction yield, and increments fallingY from107 before its first yield.

**Original:** 74F8..7551 extends at x=`60..76+13*index` inclusive, each1tick. 7698 onward retracts the exact same sequence in reverse, including its far endpoint and60. 75A0..765A draws fallingY=`107..finish` inclusive, each2ticks. Native draws the final ledger during the final falling frame and starts sound10025 in that frame, before its2tick wait. Runtime suppresses ledger for all falling frames, changes to `landed` after that wait, then sounds landing.

**Action:** yield the initial roller60; include far endpoint on retraction; yield initial note107. Each half of roller currently lacks1tick and falling lacks2ticks. On the final falling draw, use the final ledger flag and start landing sound before its wait. Keep the documented original low-note uninitialized-local caveat separate from this established off-by-one error.

## 5. Visible auditions color the wrong pixels

**Runtime:** `choiceSequence()` and `introduction()` hold `feedback=direction` throughout candidate audio, making the entire candidate box red. There is no current-note state in `candidateEvents()`/`stepAudio()` or `draw()`.

**Original:** ordinary sign click54B9 first flashes the box once via6A13. It then restores the box and calls5BB0(showNotes=true). For notation,5BB0 calls6AC0 to draw only the currently playing note/accidental red, restoring that glyph black afterward (rhythm5C44..5CFC and corresponding pitch branches). Timbre type4 takes5C03→3BEF and does **not** color its icon box during audition. Tutor first populates a white candidate at72E9..72FC, then auditions it; the tutor has no initial whole-box red flash.

The native `intro-native-contact.png` confirms white revealed instrument boxes throughout tutor progression. This differs from the runtime's red icon candidate during75ticks.

Collected-score replay also needs event highlighting:6C8F with showNotes1 calls6E8C(index,12), waits, then6E8C(index,0). Replay button is red during its operation (53B5..53F4). Large victory playback84C8 uses the shared advanced song player2EB7, with its normal current-note red rendering. Current maze `note()` always uses black and exposes neither played-note nor replay-button state.

**Action:** separate short box flash, visible individual-note audition, invisible target audition, collected-score playback and full-score playback. Do not use one `feedback` box-fill field for all of them.

## 6. Audio duration and instrument errors change phase boundaries

**Runtime:** timbre audition is always75ticks. Correct early guess plays1005 and waits60ticks. Notation and song playback use `instrument()` from the piano. `challenge()` starts target audio immediately, before incoming movement; the caller starts it again after movement.

**Original:** timbre3BEF temporarily clears the sample's loop flag and waits for sample completion through577E, then restores it. Early correct guess80BC starts1005 through7072 and explicitly waits577E. 5BB0 prepares instrument9 for notation;6C8F prepares9 and calls20C5 with9;84C8 also prepares9 for the full song. New-stage source generates/redraws the scene, walks in, **then** calls5BB0 for the target (5556..557D).

`sample-times.json` was independently decoded from original sound resources:

| Sample | Samples/rate | Nominal base-rate duration |
| --- | --- | ---: |
|DIGISND1005 correct guess|38475/11000|209.86ticks|
|VOICES12038|10245/11000|55.88ticks|
|VOICES12016|5168/11000|28.19ticks|
|VOICES12037|9216/11000|50.27ticks|
|VOICES12008|21426/11000|116.87ticks|

These are decoded PCM durations, not claims about every backend's resampling/end-interrupt boundary. They establish why fixed60/75 waits cannot reproduce the original. Sample12008 normally loops;3BEF explicitly makes its audition finite.

**Action:** expose finite sample completion/duration from the audio interface, force no-loop for timbre auditions, use instrument9 for maze notation/song playback, and defer challenge target until arrival. Include the source's conditional2tick gaps after notation/song notes when that backend's630C condition applies; current event totals have no such gap.

## 7. Wrong song guess redraws drawer contents prematurely

**Runtime:** `guess()` immediately sets guessLocked; the wrong branch immediately adds the slot to `eliminated`. Every render then removes its icon. The question button stays red with its glyph whenever `chooser` is true, including the frog reaction and closing.

**Original:** after audition,8053 sets lock. 8076 clears the entire question rectangle white. 8095 sets the elimination byte, then83EB runs frog disappointment. There is no drawer repaint after setting that byte, so the selected red-bordered picture stays visible throughout the frog reaction and remains in the backing image used for closing. It disappears when a later drawer is newly composed.

Native evidence: `wrong-guess-native-contact.png` and `wrong-guess-native-frames.json`, extracted from the untouched `research-music-maze/guess-and-win` timeline. Runs2550 and2700 show the selected lower-right picture still present while the frog appears/reacts; the question button is blank. Opening position hashes cannot detect this post-selection state.

**Action:** separate persistent elimination from the current drawer's displayed slot snapshot, and separate question-button visual state from `chooser`. Set lock after selected melody, blank the button before frog/closing.

## 8. Idle hint differs from second-error hint; timer resets are incomplete

**Runtime:** every900ticks `update()` calls `flashHint()`, flashing only the correct direction three times. Wrong completion updates targetDue but often leaves hintDue. `hearTarget()`, `hearSong()`, drawer dismissal and wrong guess do not reset both timers at completion.

**Original:** idle branch5899..58CF loops direction0..3 and calls6A13 **once per direction**, supplying each direction's attempted flag so gray candidates restore gray. Only second/subsequent errors5814..5827 flash the correct direction three times. All handled normal interactions return through5870→826D, resetting timer201A=900 and2018=360. Target playback remains a blocking/interruption-aware operation; timers are reset after it returns.

**Action:** implement separate all-sign idle reminder and correct-answer error hint. Reset both deadlines after handled input/playback/chooser completion, using completion time. Existing stale hintDue can immediately reveal the answer after one wrong choice or after closing a long-open drawer.

## 9. Ordinary clicks cannot skip the tutor or accelerate walks

**Runtime:** `click()` discards every non-exit input while `motion` exists. `hearSong()` creates audio outside a motion phase, so other gameplay remains available during that playback. Escape in app.js calls `closeGuess()`, which itself refuses when busy, leaving some chooser-related motion unresponsive.

**Original:** tutor7248 tests return values from incoming movement, auditions and waits (730B,7326,7344,7364,737F). On interruption it removes frog, checks global exit/return, otherwise redraws fully revealed signs and proceeds with player entry. It does not replay the entire tutorial or silently ignore the click. Movement77C6/7AA6 tracks5697's input result: depending on its interrupt flag it either returns/removes actor, or completes remaining steps without waits. Full song playback and sampled sound waits similarly return when interrupted.

**Action:** give each phase a source-derived input disposition: skip tutor, accelerate nonabortable path, abort allowed path, finish audio, dismiss chooser, leave scene. Do not make every animation either globally locked or immediately abandoned. Exercise ordinary pointer clicks during tutor approach/reveal, player entry, wrong song playback and drawer close before claiming cancellation parity.

## Evidence scope and useful next comparisons

This report is a source audit with selected original-frame inspection, not an assertion of a newly passing runtime comparison. No runtime or verification code was edited. Existing original recordings and independent24-position drawer comparison remain unchanged. Scratch contains the frozen source, decoded audio metadata, and two native contact sheets with frame references.

Suggested focused comparison order: first incoming segment frame0; intro frog-left duration; one pointer from each relative quadrant; reward index0 and7 inclusive endpoints; tutor timbre white box and notation red glyph; wrong-guess frog with retained picture/blank question; win-return ladder; ordinary-click tutor skip; idle four-sign reminder. These target visible states absent from the40 successful journey checks.
