# Board offer, roll, and ending sequences

Primary sources: pinned DOS v1.1 executable, overlay3 and original sound/shape resources. Main image addresses refer to `testing/output/treehouse/research-resources/all-disassembly.txt`; overlay addresses refer to `overlay3-disassembly.txt`. Research only; no runtime changes or guest RAM mutations.

## Native evidence

`testing/output/treehouse/board-sequence-capture.py` restores ordinary-input states, moves/clicks the mouse, and records every DOSBox video callback. Evidence root: `testing/output/treehouse/research-board-sequences/`.

|Directory|Restored state|Action and outcome|
|---|---|---|
|money-choice|research-boardgame/turn-b/state/move-2.state|Click(265,58), choose12c over11c; balance10→22.|
|chips-choice|research-boardgame/chip-carry-a/state/turn-1-move-0.state|Click(244,132), choose4chips over2; balance15→19.|
|human-roll|research-boardgame/chip-carry-a/state/chip-started.state|Click(94,58); roll2; capture all three car blinks.|
|robot-winning-choice|research-rewards/robot-win/state/turn-21-roll.state|Click(269,50), choose11c over12c; robot balance46→57, goal50, winner.|

Each contains `run.json` with restore SHA, actions and read-only callback state samples; `frames.jsonl` with original game ticks and PNG filenames; `unique.json` listing first occurrence of each unique image; `contact.png`; before/after serialized states and RAM. These are native frame fixtures, not rendered approximations. `car-transitions.json` records repeated car blink frames (which a unique-image listing alone cannot represent). `sound-durations.json` contains source PCM lengths, requested rates, and hardware-rounded durations for the speech IDs.

`fixture-index.json` indexes29 named full native frame copies in each sequence's `fixtures/` directory, including before/flash/reveal/feedback/transfer, all six blink states, and both winner balance treatments.

The winning fixture uses the original robot dashboard but ordinary user input to select its pending offer, just as the preexisting robot-win capture did. It does not fabricate a win state. A fresh losing native sequence has not been captured here; loss sequencing below is directly from the executable.

## 1. Selected offer: distinct render stages

Overlay3 **2EA6–2FA2** passes six arguments to2FBF: `(panel, amount, revealNumbers, background, paleCoins, drawOR)`. Positive Money selection is not pale until the later credit routine.

1. **Flash selected offer:** set timer0=12. Render selected panel with revealNumbers0, background12(red), paleCoins0, drawOR1 (**2EA6–2EC8**). Other panel stays untouched; the landing narrative stays visible. Start nonblocking sound **10052 for panel0**, **10051 for panel1** (2ED3 base10051+1−panel). Wait using interruptible5697 (**2EDC–2EE0**).
2. **Restore selected offer white:** same arguments except background15 (**2EE5–2F01**), still unrevealed. This can appear for a single native video callback.
3. **Chips only:** replace right-pane bag4414 with **SHAP4415**, palette4400, drawmode10, whitebackground15, centered in original right pane modified by top+20 and bottom−40 (**2F13–2F45**). With the current Chip rectangles that is `(top118,left274,bottom156,right313)`. Redraw OR using33A2, wait30ticks through56F7. This occurs regardless of which offer was selected. Both formulas still have their unknown field(s).
4. **Reveal both:** selected pane white15; other pane gray7. Both revealNumbers1, paleCoins0, drawOR1 (**2F5C–2FA2**). All chip art and both complete addition formulas are visible; Money shows both amounts with ordinary dark coin images. Return selected panel.
5. **Clear narrative and pause:** feedback helper38B6 calls2C90, which removes the narrative panel and leaves its narrow top rim; sets timer0=30 and waits interruptibly5697 (**2CA9–2D31**). Other board pixels and offer panes stay.
6. **Comparison narrative and speech:** draw comparison via2D3C, restoring the normal panel shape, then serialize the comparison sound sequence below. Wait24ticks56F7 after feedback returns (**1F05–1F0D**).
7. **Speak selected amount** with mainD303. Only after speech finishes, enter Money20F7 or Chips2392.
8. **Money credit starts:** redraw selected panel white, revealed, paleCoins1, drawOR1 (**2100–2112**). These are the alternate coin sprites4436…4441. Start sound10035 nonblocking, then bag4414 travels to counter. Unselected pane stays gray with ordinary coins. Chips credit has no pale coin stage.

Header removal2C90 fills `game_rects[3]=(0,111,31,221)` with theme background and draws MODULES **4007** at(111,0), leaving its narrow rim. Restoring the panel2D3C draws **4006** at(111,0) before centered text inrect4. Both are ordinals of the shared4000 shape list; they are not dashboard4200 art. The closed Chip bag4415 is37×27 and therefore draws at **(275,124)** when centered in the rectangle above.

### Native stage tick evidence

|Stage|Money|Chips|
|---|---:|---:|
|Before selection|7489|10451|
|Red flash first published|7490|10452|
|White unrevealed first published|7501|10463|
|Closed bag4415|—|10464|
|Both numbers revealed|7502|10494|
|Narrative removed|7503|10494|
|Comparison panel restored|7532|10524|
|Pale coins / first chip starts transfer|7770|10751|

Some original draws span successive video callbacks; the slight overlap in reveal/clear stages is real capture evidence. Follow source ordering, rather than inserting an artificial full-frame delay between every draw call.

## 2. Comparison speech and exact waits

Overlay **38B6–39D1** selects comparison index `mode*2 + (chosenAmount > otherAmount ? 1 : 0)`, except equal amounts use4. It first clears the panel for30ticks as above, then draws the corresponding original text:

|Index|Text meaning|Blocking sound sequence|
|---:|---|---|
|0|LESS money|11163, wait10,11158, wait10,11159|
|1|MORE money|11163, wait10,11160, wait10,11159|
|2|FEWER chips|11163, wait10,11166, wait10,11155|
|3|MORE chips|11163, wait10,11160, wait10,11155|
|4|Both were SAME|11151|

Each sound uses resident57A9, **not** nonblockingE5E2. Then the caller waits24ticks and speaks the amount. The10/24 waits use56F7 and are not cut short by its input callback.

Resident **57A9 / main12CB9** starts the sound through1BAF2 and waits through578E/main12C8E until1BAB2 reports that sound is no longer playing. Its event callback can abort playback. It has no hardcoded fixed duration. Use the original sample duration returned by the sound system, rounded to scheduling ticks; preserve the original single digital channel. Do not launch all sound IDs in one update, since each new sample would cut off the previous one.

`sound-durations.json` records both requested-rate durations and original Sound Blaster rounding (`actualRate = 1,000,000 / floor(1,000,000/requestedRate)`). Main resident56F7 maps to12C07: services input callbacks but ignores their return until timer expires. Resident5697 maps to12BA7: callback return aborts its wait. This distinction also applies to roll blinks and clearing the narrative.

## 3. Number and currency speech

Main **D166–D300** is a compositional number speaker, not one complete sample per integer. Exact source tables at main DS0AE2 and0AF6:

```
tens  = [30, 0, 20, 13, 14, 15, 6, 7, 8, 19]
teens = [10, 11, 12, 13, 14, 15, 6, 7, 8, 19]
```

These values are added to11000. For board amounts, the leading-tens flag is0. Equivalent sequence generator follows; `sound(id)` waits for completion, `wait(5)` is56F7. Missing resource11000 is a no-op sound request, not spoken zero.

```js
function* number(n, leadingTens = false) {
  if (n >= 100) {
    yield* number(Math.floor(n / 100), false);
    yield wait(5); yield sound(11029); // hundred
    n %= 100;
    if (n) { yield wait(5); yield sound(11150); yield wait(5); }
  }
  if (n) {
    if (n >= 10 && n < 20) {
      yield sound(11000 + teens[n % 10]);
      if (n >= 13) { yield wait(5); yield sound(11027); }
    } else {
      if (n >= 20 || leadingTens) {
        yield sound(11000 + tens[Math.floor(n / 10)]);
        yield wait(5);
      }
      if (n >= 20) { yield sound(11022); yield wait(5); }
      yield sound(11000 + n % 10);
      if (n % 10 === 8) yield sound(11021);
    }
  }
  yield wait(5); // even number(0) waits, with no spoken numeral
}
```

MainD40A calls around number pieces only toggle the room portrait in scene5. They do not add board visuals or fixed waits.

Main **D303–D407** first returns immediately unless DS2119 bit0 is enabled. For negative values: blocking11167, wait30; then use absolute magnitude.

- **Chips:** `number(amount,0)`;11154 if amount1, otherwise11155.
- **Money:** if dollars nonzero, `number(dollars,0)` then11156 singular/11157 plural. If dollars and cents both nonzero,11150 immediately after that sample. If cents nonzero, `number(cents,0)` then11152 singular/11153 plural. There is no extra hardcoded gap between currency noun and11150, beyond their blocking sample durations. Zero Money emits no number or noun.

Example goal50c:11015,wait5,11022,wait5, missing11000,wait5,11153. Example4chips:11004,wait5,11155. Example$1.25:11001,wait5,11156,11150,11020,wait5,11022,wait5,11005,wait5,11153.

### Landing and prepayment placement

The landing narrative is drawn at1D56, then **1D6B–1D6F** plays blocking **1027 for a negative amount**, **1028 for a positive amount**. This precedes reward pane handling. For a payment, the requestedPaycaption is drawn first, then **1E7D–1E80** callsD303 with the original negative requested amount. Only after it finishes does1E94/1E9F enter Chip24A2 or Money21B4. Therefore the11167 prefix,30tick gap, and number/currency speech run while the requestedPaycaption is present and before the incoming hand or insufficient-funds wait. Clamping does not change this spoken requested amount.

## 4. Human post-roll blink

Overlay **026A–02D5** checks role viaA98. Robot role2 skips this path. Human or friend:

1. Capture current car rectangle from saved-background objectDS568C+16 using82E2.
2. Repeat three times: restore retained road backgroundDS568C using438B, wait12 via56F7; restore captured car rectangle using438B, wait12 via56F7.
3. Free temporary car snapshot436C, then resume movement input. Road arrows/reminder input does not start until all six waits finish.

Native `human-roll` car rectangle is `(117,152,136,177)` (25×19). Pixel hashes in `car-transitions.json` alternate at original ticks:

```
4439 hidden
4451 visible
4463 hidden
4475 visible
4487 hidden
4499 visible
4511 final wait ends (source deadline)
```

The original result die remains visible and unchanged while only the car patch blinks. Hiding the whole node or rebuilding the road without its other retained objects would differ.

## 5. Win and loss order

After transfer and gameOver calculation, overlay **1F9D–20E3** releases car backing without erasing current car1698(0), then clears narrative using2C90 (interruptible30ticks).

**Win, nonzero balance:** blocking1005; draw `This player WON!`; blocking11164; if balance exceeds goal, blocking11161; mainD303(goal); then draw red balance strip and updated digits. Only after this, remaining=−1 and reminder timer=0 expose the award button through the main loop. There is no separate wait inserted between win speech pieces beyond number-helper waits and natural sample durations.

**Loss, zero balance:** redraw zero balance on white; draw `This player LOST!`; toggle logical active player to the opponent. There is **no loss speech or sound call** in20BA–20DA. Keep losing dashboard/car visible. Set remaining=−1, reminder timer=0. The logical toggle determines who gets the prize.

Native winning fixture:

|Callback|Original tick|Published frame|
|---:|---:|---|
|2161|124027|Balance57; comparison narrative still visible.|
|2162|124027|Narrative removed.|
|2459|124282|WON panel appears after the30tick clear and winning effect1005.|
|2693|124482|Red57 balance and red award control appear after win prefix, exceeded-goal phrase and50c speech.|
|2706|124493|Award control returns white after its first reminder flash.|

The callback timing includes original drawing/event/sample overhead; source wait counts are authoritative for implementation, and the complete native timeline provides visual ordering references.

## 6. Bounded loss-capture attempt

`board-loss-capture.py` made a separate ordinary-input attempt from original friend options, selecting Money and prioritizing reachable payment nodes each turn. Its complete25turn route and captures are in `research-board-sequences/money-loss/`. Despite the directory's intended target name, this route **ended in a win**, balances60/20, and must not be cited as loss evidence. It did not produce a losing fixture or near-zero payment. No further state search or RAM alteration was used. The loss ordering in section5 remains explicitly source-derived.

## 7. Money bag coordinates and travel

Main **6BF4–6C2B** is a point-offset helper, not a sprite-centering helper: output.x=rectangle.left+argumentX and output.y=rectangle.top+argumentY. Positive overlay **2131–2152** and negative **22F6–2310** pass offsets25,24. Fixed counter endpoint is image **308E0**, words `(y48,x204)`.

- Top offer credit: SHAP4414 top-left **(251,43)→(204,48)**.
- Bottom offer credit: **(251,133)→(204,48)**.
- Payment: **(204,48)→(251,43)**.

SHAP4414 itself is37×27. The offsets25,24 are authored positioning constants; do not subtract half its dimensions or the previous hardcoded12 from the pane center. The older payment audit's inferred destination255,48 has been corrected.

Main **6DA9–706F**: let dx=abs(targetX−x),dy=abs(targetY−y),error=floor(dx/2) (or−1 when dx0), and step0. Draw at start, every8 individual Manhattan steps, and exact destination. After each draw including the destination, wait4ticks. Then if not finished: when error>=0 move x bysignX and subtractdy; otherwise move y bysignY and adddx. Incrementstep and loop. Both bag calls pass identical first/alternate sprite and eraseAtEnd1. Source starts timer before constructing and publishing the draw; it busy-waits the remaining timer after publishing (**6E89**, **7006–7010**).

Top credit visible positions:

```
step0  (251,43)
step8  (244,44)
step16 (236,44)
step24 (229,45)
step32 (222,46)
step40 (215,47)
step48 (208,48)
step52 (204,48)
```

Negative payment:

```
(204,48),(211,47),(219,47),(226,46),
(233,45),(240,44),(247,43),(251,43)
```

Bottom credit:

```
(251,133),(248,128),(245,123),(242,118),(239,113),
(236,108),(234,102),(231,97),(228,92),(225,87),
(222,82),(219,77),(216,72),(214,66),(211,61),
(208,56),(205,51),(204,48)
```

Native `money-choice` confirms opaque original bag pixels at(229,45),(222,46),(215,47),(208,48),(204,48) with **zero differing sprite pixels**. Earlier three positions overlap the native yellow cursor. Per-callback results are in `research-board-sequences/bag-positions.json`. The current runtime's Manhattan travel loop already matches this stepping; the incorrect point construction caused the flight discrepancy.

## 8. Resolved mystery-node art is retained

Native `chips-choice` had a37pixel difference under its car when reconstructed only from current RAM. Active node8 has static base type25(questionmark), but DS59DA now says24(positive reward). Source **1CCC–1D0E** resolves the mystery by changing DS59DA to24 or26; it does **not** call node redraw149E or otherwise repaint the road icon. The old questionmark remains in the retained car background and visible outside the car.

Independent original-asset reconstruction of the rectangle `(x74,y115)-(103,138)`:

|Node art|Car art|Differences against native|
|---|---|---:|
|4425 mystery|4445 horizontally flipped|0|
|4424 positive|same|37|
|4426 payment|same|36|

Keep displayed road types separate from resolved logical types, or preserve the active node's pre-resolution visual type until board regeneration. For a snapshot model reconstructed after landing, current RAM alone is insufficient: a static base25 active node resolved to24/26 retained visual25. Gold23 nodes are not mystery resolutions and must remain23. This is the source of all37 unchanged differences across the Chip offer sequence.
