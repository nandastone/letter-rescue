# Treehouse DOS 1.1: theater token input and sentence correction

## Primary evidence

All behavior below comes from the original executable in the pinned `The_Treehouse_1991.zip` (SHA256 `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`), its overlay 4, and ordinary mouse input replays. No native game RAM was patched.

- Instruction listing: `output/treehouse/research-resources/overlay4-disassembly.txt`; offsets in this note are overlay 4 unless explicitly marked resident.
- Resident drag implementation: `output/treehouse/research-resources/main-disassembly.txt`, `0x67F2..0x6AD5`.
- Data: `output/treehouse/disassembly/unpacked.bin`; main DS starts at image `0x321D0`, theater state starts `0x31690`.
- Native evidence: `output/treehouse/research-theater-followup/correction-capture` and `correction-edge-capture`; every named image has matching emulator state and RAM snapshots, and the full callback timeline is retained.
- Reproduction helpers: sibling `capture-correction.py` and `capture-edge.py`. They boot normally, restore the ordinary-input `theater-props/state/editor-options.state`, and feed only mouse events. Each run.json records source state hash, core/content hashes, exact actions, observed order/selection/validation/pointer, and main image base.

The earlier `drag-capture` was exploratory: its misleading labels `corrected` and `shuffle` used the two controls in reverse and did not wait for all shuffle motion. Use the two correction captures above for comparisons.

## Controls and coordinate rules

Rectangles are `(top,left,bottom,right)`, bottom/right exclusive. Original table starts at image `0x30C80`.

| Rect index | Rectangle | Purpose |
| --- | --- | --- |
| 21 | (49,105,64,125) | Shuffle (SHAP3012) |
| 22 | (47,243,61,268) | Correct sentence order (SHAP3013) |
| 23 | (49,141,69,162) | Token slot 0 |
| 24 | (49,164,69,185) | Token slot 1 |
| 25 | (49,187,69,208) | Token slot 2 |
| 26 | (49,210,69,231) | Token slot 3 |

The overlay jump table at `0x1247` maps rect21 to `0xEF9`, rect22 to `0xDBE`, slots23..26 to `0x9B1`. The correction and shuffle controls do nothing when Mix Up is off.

Token shapes SHAP3003..3006 are all exactly 21 by 20 pixels. Their palette is SHPL3000. Thus the token origin is exactly the slot's left/top, also equivalent to the current centered renderer.

## Dragging existing rail tokens

Entry `0x3CD4`, called only in Mix Up mode.

1. If the category in this slot has no selection, return without dragging.
2. Select/show that category's heading, choice art, and colored label via `0x4A26` immediately on press. This also clears old feedback when switching category.
3. Wait while held for 15 original ticks (`DS:2016=15`). If released before expiration, execute the category preview instead of a drag.
4. After the hold, clear the source slot with the rail background color `DS:5536`, then invoke resident drag `0x67F2` with callback `0x3CA9` (draw SHAP3003+category).
5. Drag uses the original pointer-to-token offset, not center snapping. Movement must exceed 2 pixels in either axis relative to the initial pointer before the resident routine updates the token. It draws the full token, restoring its previous background each time.
6. Fullscreen drag clamps token top-left to x in `[2,318−width]`, y in `[2,198−height]`; for these tokens x2..297 and y2..178. Pointer position itself is not clamped to the rail.
7. On release, use the **pointer coordinates**, not token overlap, to decide the result:
   - Pointer x < 67: remove that category's selected choice (`selection[c]=-1`). Preserve the order array. Clear prior validation to0, return director to idle, update stage and sentence. Deleting subject also clears its loaded actor assets; deleting place clears current props display. Other category selections remain.
   - Otherwise, pointer inside another slot23..26: **swap** the two order entries. This is not an insertion/move of intermediate items. The displaced token travels back to the original slot through `0x404C` if its category is selected.
   - Pointer in its own slot or outside all slots with x>=67: restore original token and order. A drop on the stage is not deletion.
8. Redraw sentence when deletion or swap occurred. A swap **does not recompute/clear the previous validation result**; that stored result remains available for correction-success feedback on the next Play.

Source lines: `0x3D03..3D28` category/choice; `0x3D58..3D8D` hold; `0x3D8D..3DCF` drag; `0x3DD6..3EF4` delete; `0x3EFC..3FDB` swap/restore; resident `0x688E..68BB` threshold and `0x6954..69AA` bounds.

The source makes a held token visible at its starting top-left before movement. In `swapped-drag.png`, the original subject slot is blank and the dragged subject overlaps the action slot; the normal pointer remains visible.

### Short click previews

`0x3FDE..4044` dispatches:

- Subject: `0x31FB(chooseUI=1,visual=1)` (speak and actor blink).
- Action: `0x32E9(chooseUI=1,preview=1,actor=0)` (speak and small action preview).
- Place: `0x345E(chooseUI=1,visual=1)` (speak and palette flash).
- Time: `0x364F(chooseUI=1,blink=1,animate=0)` (speak and time blink).

Clicking the sentence's displayed phrase fragments uses the same category dispatch at `0x4CE..56F`. These phrase clicks do not drag words; the rail tokens own dragging.

## Dragging an unselected category from the notebook

The left category picture rectangles8..11 first show the category's choices. When Mix Up is enabled **and that category has no selected phrase**, they additionally call `0x466A`.

That handler uses the same 15-tick hold and resident drag threshold/bounds. The 21x20 token is initially centered in its left category rectangle. Drop on a rail slot swaps this category's current order position with the destination slot, then picks a random phrase in that category: subject/action range0..7, place0..5, time0..3. It applies the choice through `0x48B2/48FC/4949/49B7`, including its original preview. A drop outside all four slots restores the left token without selecting a phrase. Already-selected categories do not start this notebook drag.

Ordinary native capture `correction-edge-capture/state/add-place.png` demonstrates restoring a deleted place by dragging notebook WHERE `(35,106)` onto slot0 `(151,59)`. The original random result in this run is place0, with all other selections preserved. Seed/call parity remains a separate issue.

## Correction algorithm

`0x413A` validation already matches the demo's semantic rules: subject and action required; action must follow subject; selected place/time cannot split them. Empty slots between them are allowed.

The proposed order returned by `0x4498` **does not simply place subject/action at the start**:

```js
const result = order.slice();
const subject = order.indexOf(0), action = order.indexOf(1);
if (action > 0 && selection[result[action - 1]] < 0) {
  swap(result, action - 1, subject);
} else if (subject < 3 && selection[result[subject + 1]] < 0) {
  swap(result, subject + 1, action);
} else if (validation === 5) {
  // Slide action right to immediately after subject.
  for (let i = action; i < subject; i++) result[i] = result[i + 1];
  result[subject] = 1;
} else if (validation === 6) {
  // Slide action left to immediately after subject.
  for (let i = action; i > subject + 1; i--) result[i] = result[i - 1];
  result[subject + 1] = 1;
} else {
  result = originalValidOrders[randomInclusive(5)];
}
```

The fallback table at DS:113A contains `[0,1,2,3]`, `[0,1,3,2]`, `[3,0,1,2]`, `[2,0,1,3]`, `[2,3,0,1]`, `[3,2,0,1]`. Ordinary correction calls for validation5/6 do not need the fallback.

Native example with place unselected: order `[0,3,2,1]`, selection `[0,0,-1,1]` corrects to `[2,3,0,1]`, producing “At night the baby blows bubbles.” The empty slot immediately before action receives subject, rather than moving action to the start. This is `fills-before-action.png` in correction-edge-capture.

### Correct button behavior

Handler `0xDBE..EF6` first recomputes and stores validation.

- Valid0: temporarily save heading and choice strip, clear them, show STRL3070 item8 “This sentence order is okay.” in the choice rectangle, wait120 ticks with interruptible polling, then restore both saved areas. No permanent feedback state or order change.
- Missing2/3/4: show the ordinary incomplete-sentence feedback (same as Play feedback), without performing.
- Bad order5/6: clear old feedback if any, apply `0x461F` (copy `0x4498` proposal to order, clear feedback and validation), redraw all four token slots and the sentence. No full performance and no automatic success phrase. Category selection/choice strip remains as it was unless feedback had cleared it.

### Play after a manual correction

Play `0xD01` saves old validation, computes new validation, claps/pauses, then if old !=0 and new==0 calls `0x4220(old)` **before reading the sentence**. This clears the category strip and displays:

- STRL3070 item2 (“You fixed the sentence!”) if old3 or4;
- item1 (“You fixed the mixed-up sentence!”) for other prior nonzero failures.

It persists after performance. `correction-edge-capture/state/success-feedback.png` verifies item1 after bad-order feedback, manual rail swap, then Play. Keep previous validation separately from the currently displayed feedback; simply clearing the visible feedback on a drag must not destroy this state.

Bad-order feedback5/6 draws the proposed corrected monochrome tokens SHAP3018+category, centered in slot rectangles translated up23px, and keeps the actual colored tokens unchanged on the rail. The proposal must use the exact algorithm above.

## Shuffle

Handler `0xEF9..1017` repeats **five** swaps. Each swap draws two independent random indices0..3, rejecting equality by redrawing only the second index. It clears the first slot, moves its selected token to the second, clears the second if empty, moves the displaced selected token back, swaps order entries, and redraws the sentence after each pair. At the end it recomputes validation. Empty categories are included in the permutation.

Token travel routine `0x404C` draws source and destination top-left from the respective slot rectangles; plays sound10035 (`0x2733`); calls resident `0x6DA9` with final arguments0,4,8. The recovered interpolation and timing are given below. Native shuffle can last beyond250 capture callbacks; use the1400-callback stable replay. Do not present instant shuffle as frame-perfect motion.

## Reference states for implementation comparison

All paths below are relative to `output/treehouse/research-theater-followup`.

| Directory / state | Selection | Order | Stored validation | Observed purpose |
| --- | --- | --- | ---: | --- |
| correction-capture / swapped | 0,0,1,1 | 1,0,2,3 | 0 | Token swap before Play |
| correction-capture / invalid-order | 0,0,1,1 | 1,0,2,3 | 5 | Bad order feedback + proposed tokens |
| correction-capture / corrected | 0,0,1,1 | 0,1,2,3 | 0 | Correct button stable result |
| correction-capture / separated | 0,0,1,1 | 0,2,1,3 | 0 | Place separates required words |
| correction-capture / invalid-gap | 0,0,1,1 | 0,2,1,3 | 6 | Gap feedback + proposed tokens |
| correction-capture / gap-corrected | 0,0,1,1 | 0,1,2,3 | 0 | Gap corrected |
| correction-capture / deleted-time | 0,0,1,-1 | 0,1,2,3 | 0 | Drag left deletes time |
| correction-edge-capture / manually-corrected | 0,0,1,1 | 0,1,2,3 | 5 | Previous failure survives swap |
| correction-edge-capture / success-feedback | 0,0,1,1 | 0,1,2,3 | 0 | Successful manual correction |
| correction-edge-capture / gap-feedback | 0,0,-1,1 | 0,3,2,1 | 6 | Empty-slot preference proposal |
| correction-edge-capture / fills-before-action | 0,0,-1,1 | 2,3,0,1 | 0 | Empty slot before action filled |
| correction-edge-capture / add-place | 0,0,0,1 | 2,3,0,1 | 0 | Notebook drag randomly selects place |
| correction-edge-capture / outside-drop | 0,0,0,1 | 2,3,0,1 | 0 | Stage drop preserves token |

For full RGB comparisons, use actual pointer values recorded in run.json rather than intended target coordinates: DOS scaling commonly lands one pixel to either side. Reference stage actor is baby, action bubbles, place jungle(index1) except where removed/readded, time night(index1) except where removed. Both Mix Up and Props are on; no props were placed.

## Remaining precision work

Native static screens and semantic state changes are captured. This note does not claim complete drag-motion frame parity, shuffle interpolation parity, identical original random choices, or audio/timer synchronization. It also does not cover save/load file dialog behavior. Those are separate work items rather than reasons to approximate the interaction rules above.

## Token travel interpolation recovered

Resident `0x6DA9..706F` is now decoded. Theater `0x404C` passes a draw spacing of8 pixel-steps and a4-tick wait per displayed position. Source and destination shapes are identical for tokens, so the helper's alternating-frame support has no visible effect here.

The helper walks a Manhattan approximation to a straight line, one coordinate unit at a time:

```js
let x = sourceX, y = sourceY, step = 0;
const dx = Math.abs(targetX - x), dy = Math.abs(targetY - y);
const sx = targetX < x ? -1 : 1, sy = targetY < y ? -1 : 1;
let error = dx ? Math.floor(dx / 2) : -1;
for (;;) {
  const done = x === targetX && y === targetY;
  if (done || step % 8 === 0) {
    // Restore previous token background; save new background; draw token.
    displayToken(x, y);
    waitOriginalTicks(4);
  }
  if (done) break;
  if (error >= 0) { x += sx; error -= dy; }
  else { y += sy; error += dx; }
  step++;
}
```

All rail-to-rail motion is horizontal, so its visible x positions are simply sourceX, then increments of8 toward destination, then exact destination. One-slot travel (23px) therefore displays positions source, source±8, source±16, destination, each with a4-tick wait. Two/three-slot travel similarly includes its exact final position. The routine leaves the final token displayed (theater passes eraseFinal=0). Sound10035 starts before the motion. Resource/draw callbacks can add observed latency, so the source tick waits do not prove callback-count parity.

The shuffle handler moves the source token to destination first, then the displaced token back, then swaps the model entries and redraws sentence. In a user drag, the dragged token is already placed at its destination; only the displaced token travels back. An empty displaced category has no travel animation.
