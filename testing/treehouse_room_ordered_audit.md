# Ordered room-object fidelity audit

Research only, 2026-09-27. No runtime edits. Candidate compared: HTML SHA256 `df41e84e167642964c6767d8b95a4ae8c0c9f369d4616a51863ef5a50366ac43`. Runtime source snapshot: `testing/output/treehouse/research-room-ordered-audit/audited-room-character.js`. Parent corrections proceeded during this audit; findings describe this captured candidate.

## Reproduce the whole-frame basket route

```powershell
python testing/output/treehouse/research-room-ordered-audit/compare-basket.py --html testing/output/treehouse/completion-build/index.html --output testing/output/treehouse/ordered-basket-next
```

Output must be a new directory. It contains `basket-comparison.json`, independent runtime PNGs and differences. Native references are fixed at `research-room-ordered-audit/native-basket/`; `capture-basket.py` regenerates them into a new capture directory when that script's output name is changed.

The native capture restores ordinary `entry-verified-a/state/after-click.state`, waits60 callbacks, moves pointer to(14,167), captures `before`, holds the left button10 callbacks, then waits240. Each callback and image is retained. State records and original ticks are observed read-only; original RAM is never modified.

The comparison initializes object identities/states/rectangles, character pose/sex/needs, clock minute, cloud and pointer solely from **before.ram-0**. It then invokes `resident.begin(...pointer)` and advances the actual object generator. It does not replace object position/state from later native RAM. Whole64000pixel RGB frames are compared in **strictly increasing native presentation order**, not unordered membership. Native screenshot pixels are comparison targets only, never renderer inputs.

The fixture holds unrelated ambient/needs/cloud/balloon timers during the bounded object action and fixes the displayed clock at its initial native minute. This isolates the original blocking object action. It is not a full-room scheduler or callback-perfect timing assertion; duplicate presentations and subframe transition composites are not required to match. Native full frame `before` and the independently initialized baseline match exactly.

### Result on df41e84e

**16 of18 distinct rendered states match exactly in native order.** All11 visible flight positions and the final perch match the entire native frame, with zero differing pixels. Remaining2 states each differ by2 pixels only.

| Runtime tick | Basket state / bird top-left | Native original tick | Difference |
|---:|---|---:|---:|
|0|Basket2|2650|0|
|8|Basket3|2657|0|
|16|Basket4|—|2|
|24|Basket3|2674|0|
|32|Basket4|—|2|
|40|Basket3|2690|0|
|88|Bird278,64|2739|0|
|96|Bird272,68|2746|0|
|104|Bird265,71|2754|0|
|112|Bird258,74|2763|0|
|120|Bird252,78|2770|0|
|128|Bird245,81|2778|0|
|136|Bird238,84|2787|0|
|144|Bird232,88|2794|0|
|152|Bird225,91|2802|0|
|160|Bird218,94|2811|0|
|168|Bird218,95|2818|0|
|176|Perched bird15|2827|0|

Native tick sampling occurs at video callbacks, so first appearance can vary by one tick around a native draw. Do not infer an exact CPU-level duration from this table alone; the source supplies the8tick basket/flight waits.

## Finding 1: basket state4 needs its original damage clip

The candidate draws black at **(23,165)** and **(23,166)**. Native pixels there are respectively RGB `(138,65,0)` and `(97,56,0)`, unchanged room artwork.

The basket's saved rectangle is TLBR `(159,5,180,23)`, so x23 is outside it. Main9F98 redraws each state through **A377**. At A398–A3B4, A377 obtains the union of saved backing-image bounds and object bounds; this temporary surface controls the update region. The state4 asset's overhanging pixels do not reach the screen. The simple runtime `drawObjects()` blits the entire asset without this clip.

Apply the basket's own record rectangle while drawing this transient state. The native proof is specifically for type10; this audit does not justify globally clipping every object and effect to its record bounds. `runtime-016.png` and `diff-016.png` retain the evidence, with an identical discrepancy at tick32.

## Finding 2: open-basket press must transition directly into worm dragging

Main **9FE5–A044** closes the already-open basket, creates worm12 at DS07AE `(160,6,172,23)`, prepares its saved background, shows the pointer, and calls **9141** with the same input point. The user can keep the button held and pull the worm out in one gesture.

The audited runtime's `basket()` creates the worm but never initializes `resident.drag`. Pointer movement during that press has no effect, requiring a release and second press to pick up the worm.

Ordinary native proof: `native-basket-drag/`, reproduced by `capture-basket-drag.py`:

1. Restore the completed basket/bird state; move to(14,167).
2. Hold left25callbacks: worm exists at `(160,6,172,23)`.
3. While still held, move to(70,155),20callbacks: the worm follows the pointer.
4. Release and wait200: worm12 settles at **(164,62,176,79)**.

The folder contains `before`, `held`, `dragged`, `released` PNG/RAM/state and complete ordinary input history. Runtime should preserve original pointer-to-worm offset and use the usual placement path on release, not center the worm under a new press.

## Placement findings rechecked on the current source

These earlier source findings remained unfixed in the audited candidate. They were sent to the parent with exact formulas while it implemented corrections.

### Outdoors surface0 aliases discard surface1

Main **976A–9773** changes selected outdoor surface index0 to1 **before** computing the fall target and dispatch. Table0 `(0,-80,280,104)` contains table1 `(0,-80,192,104)`. The runtime uses ascending `findIndex` and does not remap, making its `index===1` discard branch effectively unreachable for normal left-edge drops. Normalize outside0→1, then use surface1's bottom192.

### Outdoor discard overrides the flight point, not the final record rectangle

Main **9915–992B** substitutes DS07A2/07A4, whose signed words are **(y170,x50)**, for the animation destination. These are **sprite top-left coordinates**, not bottom-center coordinates. The candidate instead flies vertically to the surface's bottom.

Let the release rectangle be `(top,left,bottom,right)`, selected surface bottom be `S`, and `d=S-bottom`. The normal translated record rectangle is `(top+d,left,S,right)`. For outdoor discard, fly from `(left,top)` to **(50,170)**. Main9A78 still writes the normal translated record rectangle before subsequent discard/removal handling. Ordinary non-plane flight at9A3B only runs when destinationY exceeds sourceY. The final discard reaction remains magnifier→SCR1004, pillow→SCR1003, other→SCR1005 plus sound10002.

### Airplane exception and precise zigzag

Plane zigzag requires type1 and `d>36`, **except inside surface9**, suppressed at **9952–9967**. Candidate `fall()` lacked the surface identity and always zigzagged at that height.

For a qualifying plane:

```text
S = (releaseLeft, releaseTop)
P1 = S + (-40, trunc(d/4))
P2 = P1 + (80, trunc(d/2))
end = outdoorDiscard ? (50,170) : (landedLeft,landedTop)
fly S→P1; mirror; fly P1→P2; unmirror; fly P2→end
```

All3 segments use step6 and delay3. The delta for intermediate offsets remains the original surface fall distance even when the final destination is overridden for discard.

### Worm chute must preserve destination uniqueness

Main **9B5A–9B7D** deletes room worm12, searches for outside worm13, and creates outside13 only if absent. Candidate changed `object.type=13` in place, allowing duplicate13 records and retaining the wrong source record identity. The reverse outside13→inside12 path already followed deletion/lookup semantics.

### Nest cleanup was already correct in the candidate

`feedNest()` ends with `birdFlight(...)`; that helper's default `removeExisting=true` removes the currently registered type15 before beginning departure. No additional missing-bird deletion was found there. Do not add duplicate cleanup based only on the absence of an explicit remove call in `feedNest()`.
