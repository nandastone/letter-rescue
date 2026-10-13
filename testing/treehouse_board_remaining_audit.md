# Remaining board audit after payment and win fixes

Scope: read-only comparison of current `boardgame.js` / `board-motion.js` against original overlay3 and ordinary-input native captures. Runtime is being updated concurrently; findings describe the reviewed implementation, not a claim that subsequent parent edits remain unfixed.

Primary source: `research-resources/overlay3-disassembly.txt`. New evidence root: `testing/output/treehouse/research-board-final-audit/`. Recorder script: `board-final-audit-capture.py`. No native RAM writes and no runtime edits.

## 1. Landing RNG order changes actual rewards and messages

**Observed implementation:** `land()` picks the narrative before calling `amounts()`. Original **1D13–1D1D** generates amounts through34B5, then **1D2A–1D36** chooses the narrative. Mystery resolution comes first in both.

Concrete native proof from existing ordinary-input states:

- `research-boardgame/chip-carry-a/state/roll-1.ram-0`: DS5290 seed **FB9450BA**, destination node8 currently mystery25.
- Original RNG bounds: **[1,4,1,1,15]**. Results: **[1,0,1,0,14]**. This resolves positive24, produces offers **[4,2]**, then narrative14, **You drove a neighbor to the store!**
- Final seed **F93E33E9** matches `turn-1-move-0.ram-0` exactly. Its image shows those offers and narrative.
- Reviewed runtime order uses bounds **[1,15,4,1,1]** and gets results **[1,1,0,0,0]**, producing **[4,3]** and narrative1, **You fastened your seat belt!**

The final seed is identical in this case, so checking only the final seed or rendering a model reconstructed from final RAM misses the gameplay discrepancy. Machine-readable evidence: `landing-rng-proof.json`.

**Second RNG issue:** runtime calls randomized `coins()` for both Money and Chips. Original **1D74–1D80** skips all coin decomposition/randomization when mode is Chips. Extra RNG consumption occurs when a Chip offer reaches a denomination subject to random reduction (25 or above). Guard `rewardCoins` generation by Money mode.

## 2. Offers are exposed early during the landing sound

`land()` assigns `rewards`, then `landing()` yields blocking1028 before `deliver()` changes `motion.panels` to0. Until then `panels===null`, so `drawRewards()` exposes both offers, which subsequently disappear when the delivery begins.

Original order **1D20–1D6F** is: clear header2C90 for30ticks; restore narrative panel and text; blocking1028; then delivery3A1B exposes offers. New ordinary native `landing-positive/` captures:

|Callback|Tick|Native frame|
|---:|---:|---|
|1921|9480|Header cleared to rim; offer panes blank.|
|1957|9511|Landing narrative visible; offer panes still blank.|
|1976|9528|Delivery begins; offer panes still blank.|
|2000|9548|Hand partway into right pane; both offers still concealed.|

Set offer visibility before yielding the landing sound, and preserve the original header clear phase before the new narrative. The capture's `unique.json` and `contact.png` cover the full entry sequence.

## 3. Idle offer and route prompts are missing

### Offer choice

Original **2E16–2E2E** calls331C when timer201A reaches0, then resets it to300. **331C–339F** flashes panel0 red12ticks then white, followed by panel1 red12ticks then white. It preserves hidden numbers and ordinary coins/bag. Nonblocking effects are10052 for panel0 and10051 for panel1. Waits5697 are interruptible; a selection event remains available to the choice loop.

Runtime `update()` only schedules hints in ready/result, so waiting at an offer choice has no visual or audible reminder. New `offer-reminder/` capture contains complete red top at tick7727 and red bottom at7739, followed by white and repetition. It uses no input after restoring the waiting state.

### Movement

Original **3BEE–3C22** dispatches15A7 when movement remains; it then sets timer201A=300. **15A7–15F5** walks the four adjacency entries in original directional order and calls14D8 for every valid neighbor. **14D8–159A** saves the node region, draws centered SHAP4427 with palette4400/mode10, redraws the actual node icon149E on top, shows12ticks, and restores the saved region. This is a red ring around the normal icon, not replacement with a red icon.

Runtime has no hint branch in phase`move`. Existing `research-board-sequences/human-roll/` provides native pulses at4512,4524 after the blink sequence. New `movement/` clicked an unreachable node11, which first flashes that requested node, then flashes legal neighbors through3BEE after path search fails. Runtime currently only changes its readable notice for that invalid target.

## 4. Movement lacks the target flash and arrival pauses

Every valid node click first calls14D8 (**0483–0488**), giving the requested target's12tick red-ring pulse before moving. Adjacent movement17EE is followed by another12ticks (**04CA–04D2**) before decrementing remaining and repainting the die. For a multi-edge path, **0533–056A** waits12 after each edge, decrements/repaints the die, then waits12 again before the next edge.

Current `move()` starts `nextEdge()` immediately. At arrival `update()` immediately decrements and either starts the next edge or lands, omitting these pauses. `landing-positive/` demonstrates a real one-edge click: red target first published9391, first movement9402; arrival9465, header-clear/zero-die9480. Source timer counts are authoritative; callback publication can differ by one tick.

## 5. Clicking during feedback should shorten the current speech

Current busy `click()` ignores all input except the required exchange. Original blocking sound57A9 services the event callback via578E and can stop the current sample; subsequent scripted sounds continue in sequence. This is different from accepting a second reward choice or skipping the complete transfer.

New `skip-feedback/` restores the same original reward state, chooses top offer, waits80callbacks, then makes one ordinary second click during comparison speech. Relative to first red selection frame:

- Baseline `research-board-sequences/money-choice`: balance updates after **313ticks** (7490→7803).
- Additional-click capture: balance updates after **295ticks** (7504→7799).

Both outcomes are balance22 with the same chosen offer. The second click shortened the active speech by18ticks. The capture records the exact action list and every frame; it did not change timers or sound state through RAM.

## 6. The26pixel winner fixture difference is a partial counter redraw

Native `robot-winning-choice` callback2161 has the final balance digits57 but only six unit coins; the seventh unit coin's top two rows have not yet been written. Its26pixel difference against the complete renderer is x192…205,y48…49, all **white native pixels versus the final black/brown coin pixels**. Bag originx204 cannot explain pixels192…203.

Source **19EB–1A3F** rebuilds stacks/digits through1A91 in separate drawing operations. By callback2162 the final stack is present and the header is clearing. This is captured rendering progress, not retained bag art. Use the next callback for a settled balance reference; do not add a bag-retention workaround. Enlarged diagnostic crops: `counter-model.png`, `counter-native.png`.
