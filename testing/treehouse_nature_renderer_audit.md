# Nature quiz renderer audit: concrete sequence corrections

2026-09-27. Read-only runtime inspection against original executable/resources and ordinary-input native captures. No runtime files changed by this research task. Parent is applying findings concurrently; this report names the reviewed snapshot rather than claiming every finding remains present in the newest runtime.

Reviewed source snapshot: `output/treehouse/research-nature-audit/nature-quiz-reviewed.js`, SHA-256 `b58a055615881aad691856272a8b21bfb2b91321eb17248fcf1ddf69758a2f46`. It already includes the winner-role restoration correction sent at the beginning of this review.

## Reproducible evidence

Scratch root `testing/output/treehouse/research-nature-audit/`:

- `fixtures.py`: extracts bundled original assets and reads cards, secrets, remaining masks, player and pointer from original native RAM snapshots. No original memory writes.
- `fixtures.json`: also records native asked masks at DS52DC/52DE. The current file includes three new question fixtures.
- `render.cjs`: evaluates the frozen runtime and original asset data under a minimal ImageData shim, producing RGBA buffers.
- `compare.py`: renders original cursor where visible and compares complete native 320×200 RGB images.
- `question-native.py`: ordinary restore/click capture for one temperature question. Successful capture directory is **question-native-c**. It waits three callbacks at each stable display count before saving, avoiding a RAM/VGA capture boundary mismatch.
- `render-question-corrected.cjs`: scratch-only application of the two question corrections below. No changes to the actual runtime.

The first exploratory question-native run stopped on a rejected zero-frame capture; question-native-b captured immediately when the RAM counter changed, before VGA presentation caught up. Neither is the settled display-count reference. Use **question-native-c**.

### Measured full-frame differences

| Native reference | Reviewed renderer | Scratch corrected renderer |
|---|---:|---:|
|Settled human win|0|unchanged|
|Settled wrong guess, selected=-1 and native learned mask|0|unchanged|
|Second animal revealed, robot candidates visible|2611|all differences are eliminated-card background fills|
|Guess reference at animation/input boundary|271|225 control-background pixels plus46 pixels from adding a pointer to a frame where it is absent|
|Temperature script display10, threshold11|400|**0**|
|Temperature script display11, callback fired|485|**0**|
|Temperature script display12|400|**0**|

Question scratch corrections are precisely: hide the guess button rectangle `(137,82,162,107)` while asking; keep the old question icon through display11 and remove it on display12. All three corrected comparisons are zero over64,000 pixels, including actor sprites, scene, other decorations, and all panels. Native pointer is hidden during these three animation captures.

## 1. Question threshold changes the next displayed frame, not the current one

**Reviewed code:** `perform()` calls `Animation.update()`, then immediately sets `questionHidden` when `frameUpdates>=questionThreshold`.

**Original:** main **BE33** calls **C78A** to render the display, then **BE36** increments DS5586. Wrapper **48A5–48BA** subsequently calls **4E9E**. At threshold equality, **4E15** edits the retained backdrop and marks DS5296; this does not replace the already-presented frame. The edited backdrop participates in the next animation display.

**Native evidence:** temperature threshold11, rolehuman. At DS5586=11 and DS5296=1, the visible frame still contains the85 nontransparent question-icon pixels. They disappear at display12. `threshold-crop.png` shows original display10/11/12 above the reviewed renderer equivalents.

**Action:** retain a pending backdrop change at equality; expose it only on the next display update. With the current stateless recomposition approach, `frameUpdates > threshold` gives the measured result. Keep the existing threshold table; its values are correct. Do not increment the recovered table itself or change the script frame count.

## 2. Guess control remains visible during a question and appears too early on turn entry

**Reviewed code:** any `phase==='question'` draws the normal guess frame and icon, including `enterTurn()` and `question()` generators.

**Original:** overlay **3240** calls **2A0B**, filling entire guess-control rectangle white before the question animation. During turn entry, the enabled control is drawn only after the three question decorations have been revealed (**2FD5–303B** and subsequent control call).

**Evidence:** precisely400 differing control pixels in each sampled question frame. White-filling `(137,82,162,107)` resolves those pixels independently of the threshold fix.

**Action:** model guess-control visibility separately from the broad question phase. Hide during entry and ask; enable after the third question; use highlighted fill after entering guess mode. The native waiting-guess inner background is solid **RGB(255,85,85)**, not MODULES5650 palette12's orange color. Overlay **3088–3092** passes logical screen color12 to **299D**, which centers originalSHAP5666 in the inset rectangle.

## 3. Second reveal needs a clean shrub backdrop and deferred displayed player

**Reviewed code:** `revealOther()` immediately switches `this.player`; `draw()` uses it for cards/all secret answers. The unrevealed shrub bit remains clear until the animation ends, so `draw()` draws staticSHAP5601 and then the flattening animation over it.

**Original:** overlay **2D32** changes internal currentplayer, but **2D59** runs SCR5600+player before **2D6F/2D7E/2D92** redraw information and candidates. Previously displayed panels remain intact through the animation. SCR5601's original frame sequence is transparent SHAP5601, then5603,5604,5605,5606,5607,5608 at progressively lower coordinates. It requires the original clean scene backdrop, not a permanent intact shrub underneath.

**Actions:**

- Preserve a `displayPlayer` through the second shrub animation; switch displayed cards/facts/footer only afterward.
- Suppress static shrub drawing for `otherReveal` while its SCR runs, even before setting the revealed bit.
- Keep the first winner's flattened shrub, animal and saved-background repair untouched by changing the inspected player.

## 4. Saved guess rectangle belongs to the winner, not the inspected role

This was fixed by the parent during review. The earlier code selected `guess_restore_rectangles[this.role()]`, which changed from boy to robot on the second reveal. Source DS5742 is saved at **30E3**, updated for the winner at **39E4**, and reused during that winner's celebration/retreat. It does not become a robot background because the other secret is inspected.

Correct role for the final first-shrub repair is `winner===0 ? 0 : opponent`, with the chosen human sex selecting boy/girl rectangle. Native settled human win, and the whole right scene after second reveal, match exactly with this correction.

## 5. Wrong guess temporarily becomes an unwanted candidate inspection

**Reviewed code:** `guess(index)` sets `selected=index`. For a wrong guess it leaves that value during `perform(11)`, `perform(9)`, and the60tick delay; `draw()` treats any nonnegative selected index outside won phase as an inspection panel. `enterGuess()` also does not clear a preexisting inspection or definition.

**Original:** overlay **3074–3085** explicitly clears a temporary inspection before guess entry. Wrong-guess **3683–3739** runs reaction and retreat while preserving normal learned answers; it does not call candidate inspection343C.

**Action:** clear selected/definition state at guess entry and before the wrong-guess reaction, not only in final cleanup. The settled wrong native fixture is exactly reproduced with selected=-1 and its original askedmask; that does not establish the current generator's transient selection as correct.

## 6. Winner retreat is missing the foreground divider; ribbon appears early

**Reviewed code:** celebration and retreat use `winAnimation.draw(surface)` directly. They bypass the divider composition in `actorScript`. Ribbon is drawn for every won stage except shrub, including celebration.

**Original:** the common retreat **36F1–3739** sets DS57C0=true. The wrapper clears `(134,42,167,80)` white, draws the actor, then main **CB4A–CBAA** overlays MODULES5403 at `(166,41)` when dirty bounds intersect the divider. This is required for the returning actor to pass behind the stage edge. Ribbon is drawn by **377D** calling **28CE**, after retreat finishes.

**Action:** apply the same clear/sprite/foreground order during winner retreat as during ordinary `perform(9)`. Draw ribbon only after retreat; its celebration-stage appearance is premature.

## 7. Answer footer is delayed until after all result waits

**Reviewed code:** the answer string is assigned after the question SCR, but the footer is gated by `phase==='answered'`. That phase is set only after36ticks, every18tick help elimination, and the final60ticks.

**Original:** source **32C1–3346** sets the asked bit and draws the learned row/footer before the36tick wait. Subsequent help elimination and60tick wait retain that visible answer.

**Action:** distinguish an available displayed answer from final turn cleanup; show its footer immediately after the SCR completes. Keep the existing wait values and elimination order.

## 8. Crossed-out candidate backgrounds must be gray

**Reviewed code:** each candidate calls `center(...,0xffffffff)` unconditionally, while its adjacent mark reflects remaining bits.

**Original evidence:** `research-nature-completion/capture-a/state/second-animal.png` and its independently reconstructed zero-difference source renderer. Candidates with remainingbit0 have **RGB(170,170,170)** background; remainingbit1 useswhite. This accounts for exactly2611 differences in the reviewed second-animal frame; all right-scene and text pixels already match.

**Action:** choose white/gray fill from the remaining mask before drawing original transparent animal thumbnail. Parent reported this change applied during review.

## Cursor follow-up correction

The original `guess-mode.png` is at a presentation boundary: RAM has already entered guessmode, but its captured VGA frame has no pointer. It does **not** show a white pointer. Running one additional ordinary callback after restoring the corresponding state presents the normal yellow cursor, without changing DS2060 from14. Full source and new hover evidence are in [cursor follow-up](treehouse_nature_cursor_followup.md).
