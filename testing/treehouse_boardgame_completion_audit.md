# Board game completion audit: payments, exchange and endings

2026-09-27. Read-only audit of `treehouse-demo/boardgame.js` and `board-motion.js` against original overlay3/main disassembly. No runtime edits. Parent is applying findings concurrently, so the discrepancies below describe the initially reviewed implementation.

Primary sources: `output/treehouse/research-resources/overlay3-disassembly.txt`, `main-disassembly.txt`, `all-disassembly.txt`, original extracted MODULES/TH resources, and new ordinary-input captures. No guest RAM writes.

## Native evidence

| Directory below `output/treehouse/` | Reference | Result |
|---|---|---|
|`research-board-audit/native/state/`|`payment-wait.png`|Chips player0 pays4, balance25→21; open hand remains, Pay4 caption, four transferred ones|
|`research-board-audit-money/native/state/`|`payment-settled.png`|Money player0 pays1cent, balance10→9; open hand remains, penny and Pay1Cent caption|
|`research-board-audit-exchange/native/state/`|`exchange-options.png`|Click actual Options hotspot `(309,31)` while carrying: remains exchange scene25|
|same|`exchange-escape.png`|Esc while carrying: remains scene25, balances unchanged|

Drivers are `board-audit-native.py`, `board-audit-money.py`, and `board-audit-exchange.py` under `output/treehouse/`. Each evidence root retains `run.json`, input actions/restores/hashes, native frames and read-only RAM. The first Chip capture's earlier `exchange-options` clicked `(300,60)`, which is **not** the options hotspot; use the dedicated `research-board-audit-exchange` evidence for the cancellation claim.

`research-board-audit/payment-render.py` independently draws original assets/font and compares the entire active payment panel:

- Money `(left226,top19,right308,bottom102)`: **0 different pixels**.
- Chips `(226,98,265,196)`: **0 different pixels**.

The renderer uses no screenshot pixels as input. Results are retained in `payment-panel-comparison.json`, with enlarged independent panel PNGs.

## 1. Negative payments use a retained open hand

The reviewed payment paths skipped original overlay3 **3A1B**. The existing positive-offer delivery cannot simply be reused unchanged: its shape and return behavior differ.

### Exact negative-hand recipe

Call3A1B arguments are `(mode,unused0,offerFlag0)`, corresponding to bp+A,bp+8,bp+6. It uses original MODULES **SHAP4301 / SHPL4300**, transparent index0. Positive offers instead use4302.

| Parameter | Money | Chips |
|---|---:|---:|
|Clip rectangle, native top/left/bottom/right|`19,226,102,320`|`98,226,194,320`|
|Hand Y|29|119|
|Hand X trajectory|320,316,…,232|320,316,…,232|
|Wait per position|2ticks|2ticks|
|Final hand position|232,29|232,119|

Source **3A70–3A88** computes `y=clip.top+11*mode+10`. **3A8B–3AEA** draws each position over the retained pre-hand backdrop. On flag0, **3AED–3AF3** jumps directly to cleanup: **no outbound return animation**, no positive-offer sound1024, and the hand's final pixels remain. Source **3B72–3BCC** is the outbound branch for positive offers only.

This routine does not clear the whole offer area. It preserves the existing white pane and prewritten Pay caption. The only payment pane is game rectangle14: Money upper pane, Chips left pane. The other pane remains blank from the board composition. Do not draw OR for a payment.

### Caption before hand arrival

Source **1E38–1E78** writes the negative amount through formatter **33EE**, originalFONT1, black. Inset the payment rectangle horizontally4pixels; bottom align. Horizontal alignment is centered for Money and right aligned for Chips.

- Money: text origin `x=267-floor(textWidth/2)`, **y93**.
- Chips: text right edge **261**, **y187**.
- Examples independently verified: `Pay 1 Cent`, `Pay 4`.

Chips payment has **no addition rule, plus sign, unknown amount, or resulting-total line**. The reviewed `drawRewards()` reused the positive comparison layout, making this a settled-screen mismatch, not merely a transition difference.

## 2. Money debit: precise order and greedy coin timing

Source **21B4–238F**:

1. Convert absolute requested amount into **greedy** denominations100,50,25,10,5,1 (**21CE–220D**). This is separate from the randomized decomposition used for ordinary positive offers. Do not show these coins yet; the prewritten Pay caption is already visible.
2. If requested payment exceeds balance: set gameOver, wait60ticks (**2222–2230**). If balance is already0, return at2245 with the requested Pay caption intact and no hand/bag. Otherwise clamp actual payment to balance and recompute greedy coins (**2248–22A2**).
3. Run the incoming retained hand, Money mode, flag0 (**22B0**).
4. Subtract actual payment and redraw balance (**22B3–22CA**). Wait60ticks (**22CD–22D5**).
5. Play10035. Move MODULES4414 money bag from **(204,48)** to **(251,43)**, source step interval8/delay4/eraseAtEnd1 (**22DA–2343**). Main6BF4 adds offsets25,24 to the pane's left/top; these arguments are not dimensions for centering. This corrects the earlier inferred(255,48) endpoint.
6. Play1024. Only now call **2FBF** with negative actual payment, reveal1, background−1 (retain existing pixels), ordinary coin variants, no OR (**2350–2382**). This draws the greedy coin grid and replaces the caption with actual `Pay …` if it was clamped. The hand remains.

The reviewed implementation showed the coin grid immediately and `???` while phasepayment, then switched to Pay at settlement. It also showed the lost heading before the actual debit ended. Preserve the requested Pay caption during the hand/bag sequence; reveal coins and final clamped caption after bag arrival; defer the loss heading to settlement.

## 3. Chip debit: paid cells accumulate after arrival

Source **24A2–263F**:

1. Set paid-cell count DS52EA=0 (**24B6**).
2. If request exceeds balance, set gameOver and clamp a local actual-payment variable to balance (**24BC–24DE**). Unlike Money, this branch has no extra60tick insufficient-balance wait.
3. Run retained hand3A1B in Chips mode, flag0 (**24E1–24EF**).
4. Process units, tens, hundreds. Borrow first if needed. Subtract the denomination from balance and update that stack; sound1025; wait20ticks (**2551–2592**).
5. Take destination cell index DS52EA and increment it before travel (**25E3–25E7**). Cell rectangle is original13×13 grid at `(226+13*(cell%3),98+13*floor(cell/3))`.
6. Travel the denomination chip4422/4421/4420 from stack `(left,41)` to that cell, step8/delay2/**eraseAtEnd0**. Sound1023; wait20ticks (**2597–2624**). The chip is retained at destination after arrival.

The paid counter increments before travel because it allocates the destination; it is not permission to display the destination chip before arrival. Keep in-flight and committed paid cells separate. The reviewed renderer drew all requested-payment chips immediately and the positive comparison totals.

The Chip Pay caption remains the originally requested amount: **24A2** clamps only the local transferred amount, and does not rerun33EE/2FBF. Therefore an insufficient-funds case transfers only the available balance while keeping the original request caption. This last clamped-caption detail is source-derived; the new ordinary Chip fixture is a non-loss4chip payment.

## 4. Exchange is modal and its flash fills the stack interior

Native carry/borrow loops temporarily use scene25. **28BA–2954** and **2A68–2AF8** only finish on an input event whose current pointer is inside the requested stack rectangle. Options and Esc do not exit these loops. The dedicated native capture confirms both are ignored and balances remain `[25,20]`.

The reviewed `BoardGame.click()` handles Options before checking exchange, and the app always offers a Game options button. This opens options during a required trade. Source Options cancellation **is** supported during positive reward selection (**2E67–2E7B**, return−2), so blocking all options everywhere would also be wrong. Apply blocking during motion/payment/exchange; retain the original reward-choice cancellation path.

Original hint/commit animation2776 calls interruptible wait5697; input may shorten the current shape sequence. The exchange loop still validates the clicked stack afterward. Do not interpret an arbitrary key as approval of the trade. The browser's explicit readable trade button/Enter can be retained as a deliberate input improvement, but it is additional to the original pointer-position validation.

For the6tick flash, stack painter **1A91**, flag1, sets its internal stack background to logicalred12 (**1B70–1B99**), fills the expanded stack interior, and redraws chips. It is not an outline. Red regions are:

- Hundreds: x226…249, y37…71.
- Tens: x251…273, y37…71.
- Ones: x275…298, y37…71.

Digit-label rectangles keep their separately supplied white background. The reviewed `exchange.flash` painted only top and bottom red lines at the unexpanded stack edges.

## 5. Winning and losing settlement, active player and speech

After debit/credit finishes, **1F93** tests gameOver. It calls1698(0), releasing the car background **without restoring** it, then2C90 to reset the message panel.

### Win, balance nonzero

1. Sound **1005** (**1FBB–1FBF**).
2. Draw `This player WON!` (**1FC4–1FCB**).
3. Sound **11164** (**1FCE–1FD2**).
4. If balance exceeds goal, sound **11161** (**200F–2013**).
5. Call main **D303(goal)** to speak the goal amount.
6. Fill the digit strip logicalred12 and redraw balance (**2020–20B2**): Money `(144,64,209,75)`; Chips `(226,75,299,87)`. Chips wins require the red digit-strip treatment too; the initially reviewed code only used red in Money.

MainD303 is conditional on speech enable bit DS2119&1. For negative values it speaks11167, waits30ticks, then speaks the absolute amount. Chips delegates number speech toD166 and appends11154singular/11155plural. Money speaks nonzero dollars throughD166 plus11156/11157, inserts11150 when both dollars and cents are nonzero, then cents throughD166 plus11152/11153. For the positive win goal there is no negative prefix.

### Loss, balance zero

1. Redraw zero balance white (**20BA–20C4**).
2. Draw `This player LOST!` (**20C7–20CE**).
3. Toggle logical active playerDS52D8 to the opponent (**20D1–20DA**), without rebuilding the visible dashboard/car. This makes the opponent the prize recipient.

Both branches then set reminder timer201A=0 and remaining5276=−1 (**20DD–20E3**). The next reminder loop draws the award control. The existing port can represent the loss toggle with separate displayed player and prize recipient; blindly changing its single player field would incorrectly repaint the losing dashboard and car. Its current `openPrizes()` already computes the opposite recipient correctly, so preserve that behavior.

Selecting a prize starts a fresh game with existing settings; the source and existing reward report already establish this path. No additional replay dialog is needed.

## 6. Other small source-backed gaps

- **Selection timing:** chosen offer flashes red for12ticks via2EA6–2F01; Chips then briefly presents shape4415 and waits30ticks (**2F13–2F57**) before revealing both numeric offers. Feedback38B6 is followed by another24tick wait (**1F05–1F0D**) before spoken amount and credit transfer. Reviewed `choose()` starts credit immediately without these stages.
- **Human post-roll blink:** source **027B–02CA** blinks the car three times with12tick halves before accepting movement. Reviewed rolling code goes directly to move after the last roll face.
- **Dashboard replay hotspot:** game rectangle1 `(top0,left46,bottom32,right110)` calls39D4 while not gameOver (**0147–0164**). Reviewed `click()` does not dispatch it.
- **Horn hotspot:** game rectangle5 `(43,0,81,59)` calls19D3, which plays sound1012 (**012E–0141**, **19DC–19E0**). Reviewed `click()` does not dispatch it.

These last timing/hotspot findings are direct disassembly comparisons; this audit did not add new native captures for each one.

## 7. Exact resident line wrapping and preserved spaces

Main image **159A2** supplies consumed line lengths to the multiline renderer **17828**. Its semantics explain the payment narrative mismatch while preserving the already matched ordinary board headings. This is not a general whitespace-trimming algorithm.

At **159BA–159CC**, add the next character's measured advance to the current line width and test unsigned `width > limit` **before consuming that character**. If it overflows, return the latest legal break length, or the consumed length if no legal break has been recorded. At **159CE–159D3**, consume the character and return immediately if it is CR, including CR in the consumed length. At **159D5–159F5**, update the latest legal break:

- A consumed hyphen always creates a break immediately after it.
- Left or center alignment: a consumed space **or a next character that is space** creates a break immediately after the consumed character.
- Right alignment: only a consumed nonspace whose next character is space creates a break (plus the hyphen rule above).

For centered labels, this means both sides of each space are legal breaks. A space that fits can remain at the end of a wrapped line, contributing its advance to centering. A space that itself overflows remains **unconsumed** and begins the next line, also contributing its advance. Do not trim either edge. Thus the payment first line `You need to get a new` fits its 98px rectangle at 97px, and the overflowing following space belongs to line two. The retained leading 3px space explains the observed second-line visible glyph origin x132, rather than the x130 obtained by centering the trimmed 72px text.

Equivalent core logic (alignment −1 left, 0 center, +1 right):

```js
function originalLineLength(text, limit, alignment, advance) {
  let consumed = 0, width = 0, legalBreak = 0;
  while (consumed < text.length) {
    const char = text[consumed];
    width += advance(char);
    if (width > limit) return legalBreak || consumed;
    consumed++;
    if (char === '\r') return consumed;
    const nextIsSpace = text[consumed] === ' ';
    if (char === '-' || (alignment <= 0
      ? char === ' ' || nextIsSpace
      : char !== ' ' && nextIsSpace)) legalBreak = consumed;
  }
  return consumed;
}
```

The caller **17870–1788C** stores precisely this length, advances the source by exactly that length, and stops if the result is zero. It never strips whitespace between lines. The measured line width includes all retained spaces. Center origin **17928–17931** is `left + floor(rectWidth/2) - floor(lineWidth/2)`.

There is one alignment-specific rendering adjustment, **178E7–1790E**, which does **not** apply to centered labels: for left alignment only, on a line whose start differs from the original string start, remove one initial space if the preceding source character was not CR. Remove a second initial space only if the preceding source character was a period. This is an adjustment to the line's drawing pointer and length, after wrapping, not global trimming or advancing the next line's source. Right alignment receives no such adjustment.

Source evidence: `research-resources/all-disassembly.txt` at the image addresses above; single-character advance helper **152B2** delegates to the same width routine **17962** used for final alignment. Parent's independent payment glyph match supports the retained-space result; no new guest-memory mutation or constructed native state was used.

## 8. Zero-balance payment edge cases

Both debit functions compare `requested > balance`, not `requested >= balance`, before setting gameOver. Paying exactly the available balance leaves an active game with zero funds, so a later payment at zero is reachable through ordinary play.

- **Money:** **2222–2245** sets gameOver, waits60ticks, then returns immediately if balance is zero. No incoming hand, bag, greedy coin reveal, or caption rewrite occurs. Retain the original requested `Pay …` caption. The reviewed `moneyDebit()` clamps `rewards` to zero and enters result, causing the renderer to print `Pay 0`; that needs a zero-balance caption exception.
- **Chips:** **24CE–24E1** clamps the local amount to zero and still invokes the retained incoming hand. There is no insufficient-funds60tick wait. The reviewed port passes `-Math.min(balance,request)`, giving negative zero, and tests `t.sign<0` to decide whether to run the incoming hand; JavaScript's negative zero fails that condition. Track debit intent separately from amount sign, or use the existing payment context. No chip cells are deposited, and the requested `Pay …` caption remains.

These edge cases are source-derived; this audit has not yet captured a native zero-balance payment.
