# WR1 completed updates and gruzzle tracing

Static evidence from WR1.EXE SHA256 `b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`. Code addresses below are **file offsets**; `DS:` addresses are data-segment offsets. MZ image starts at file `0x2a00`, main CS is load-relative `0096`, DS is load-relative `2255`. Runtime physical address is `load_base + 16*segment + offset`. These findings require no writes to native memory or clone gameplay.

Reproducible primary evidence: [script](output/wr1_update_boundary_disasm.py), [aligned disassembly](output/wr1_update_boundary_evidence.txt). Capstone's CWDE/CDQ mnemonics in these 16-bit dumps mean CBW/CWD.

## Result: no universal DS completed-tick counter found

There is a useful **render-completion parity marker**, `DS:807c`, and a subsequent **selected display-page marker**, `DS:4879`. Neither is a monotonically increasing tick count. A stable paused snapshot is still allowed to represent a half-finished logical update; two identical memory reads only prove consistency at that paused point.

For ordinary gameplay, the strongest exact instruction boundary is **file `0x40a4`**, immediately after display-page selection returns. The main loop's stack-local demo-input index increments later at `0x40cf`; **file `0x40d2`** is after that increment and immediately before the back-edge. Both boundaries need native instruction-position/breakpoint access for unconditional identification. The current READ_CORE_MEMORY tracing interface does not expose that information.

## Normal update ordering

```text
main loop / input and menu handling
  371b: test timer >= threshold; otherwise back to 34ba
  37a4: timer = 0                    # update START, not completion
  37a7: save previous player X/Y
        vertical/player animation/horizontal movement
  3d7e: contact function c1aa        # books, words, matching, score
  3d99: entity/action function50e8   # gruzzles, slime action, hazards
  3d9e: renderer ab25
        camera; background/picture animation; drawing
        renderer also mutates gruzzle animation, slime state, score!
  c198: DS807c = newly drawn page    # late render commit, parity only
  c1a9: renderer returns
  3da3: main checks exit transition
  409f: select/display page DS807c
  40a4: return from page display     # exact ordinary visual boundary
  40b1: check death flag, possibly run death/reset path
  40cf: increment main [BP-2]
  40d2: back to 34ba
```

The bottom-of-map branch can skip the ordinary renderer/display path (`0x3d79–0x3d7b`, `0x40a6`). Exit/death transitions may make additional renderer calls and change level state before returning to the main gate. Thus `renderer calls == ordinary movement updates` is a restricted assumption, not a property of all sessions.

### Exact instruction locations for future debugger support

| File offset | Unrelocated CS:IP | Meaning |
|---|---|---|
| `0x371b` | `0096:03bb` | Gate test before admitting another ordinary update. |
| `0x37a7` | `0096:0447` | Timer reset completed; movement is about to start. |
| `0x3da3` | `0096:0a43` | Main renderer returned; ordinary movement/contact/entities/render complete. |
| `0x40a4` | `0096:0d44` | Normal display-page call returned. |
| `0x40d2` | `0096:0d72` | Main iteration index increment completed; immediately before main-loop back-edge. |

Set runtime code segment to `load_segment + 0096`. A breakpoint at the gate can also give a completed previous state, but the loop revisits it repeatedly while waiting; it needs admission/iteration deduplication. A breakpoint at `0x40d2` is the most explicit ordinary completed-loop observation, while `0x40a4` is useful when the desired comparison is before death handling.

## Existing memory markers and limitations

| Field | Type | Interpretation and caveat |
|---|---|---|
| `DS:807c` | u16 | Last renderer's completed draw page, normally0/1. Renderer computes `(old+1)%2` at `0xacb2–0xacbc`, writes it only at `0xc198`, after HUD copies. Extra renders also toggle it; two renders alias to no change. |
| `DS:4879` | u16 | GX selected display page. Page setter writes it at `0x1767d` **before** BIOS INT10/AH5 (`0x17681–0x17683`); this is software selection state, not proof the hardware has presented the page. The alternate display backend writes it at `0x1765a`. |
| `DS:41be` | u16 | Background frame0..3, advances within the renderer at `0xb226`, before renderer completion. It is not a completion marker. |
| `DS:0f2e` | u16 | IRQ timer reset at update start (`0x37a4`), also reset by transition/wait code. Its drop is a start edge. IRQ ticks can occur during rendering. |
| `DS:8e8f` | u16 | Main gate threshold, default8. Helpful timing metadata; does not identify which update stage is paused. |
| `DS:0f54` | u16 | Incremented on entity/action function entry at `0x50f0`; reset when an accepted slime action begins at `0x512d`. Useful local progress signal, not a global tick clock. |
| `DS:9790/97a8` | s16 each | Player X/Y saved near update start (`0x37aa`, `0x37b0`). These are screen coordinates at that moment; camera later changes can make naive subtraction misleading. |
| Main `SS:BP-2` | u16 | Demo-input index, incremented at `0x40cf` in normal play as well. Initialized0 at `0x34a6` **only when demo mode DS0146!=0**. In ordinary play the initial value is unspecified; deltas could still count completed iterations once its live stack address is independently established. Wrap/reentry/death handling matter. |

The main function begins at `0x347c`, creates its BP frame, and keeps the index at BP-2. The demo restart branch also resets this index at `0x36f1`; ordinary play bypasses that write (`0x36d9–0x36de`). Other useful locals are idle counter BP-8, right walk index BP-10, left walk index BP-12. **Do not assume the executable's initial MZ SS:SP directly identifies main BP.** Startup/caller stack frames intervene, and BP in a paused nested function is not main BP. A validated stack walk or native CPU registers would be needed before reading these as reliable fields.

### What read-only memory sampling can safely claim

1. Preserve each raw paused snapshot and its exact frontend replay frame. Validate the loaded executable signatures and require two identical region reads as the current tracer already does.
2. Add render page, selected display page, background phase, action timer, previous player coordinates, transition flags, and gruzzle fields. These explain many apparent position/animation disagreements.
3. Treat a render-page edge as a **candidate** completed render. A first post-edge snapshot can be useful operationally, but it is not an unconditional completed-update sample: the frontend slice could already have begun the next update.
4. If render page differs from selected display page, drawing has committed more recently than the display selection. If they agree, this still permits waiting, mid-next-update movement, or any state that aliases the parity bits.
5. Do not equate a timer drop, background-frame change, pixel change, or state stability with one complete update. Do not deduplicate solely by player position: idle/blocked updates and actor-only changes are real updates.
6. Report missed/ambiguous transitions rather than silently treating them as successful exact matches. For a guaranteed long-session comparison, obtain the instruction boundary above, or replay the whole ordinary-update state machine including render mutations against dense native snapshots with explicit intermediate-stage handling.

At the default gate (approximately12logicalupdates/sec), sampling every frontend frame will often bracket an update narrowly enough for practical comparisons. That is empirical sampling resolution, not a proof: slower native cycles, expensive render/transition paths, emulation timing and frontend slice boundaries can change where a pause lands. Stable memory and atomic logical state are different properties.

## Gruzzle trace fields

Read `DS:0237` as count and at most10slots. All arrays below are **10 little-endian signed16 words**, index at base+2*i, except type can conveniently be treated unsigned when validating0..3.

| DS base | Suggested trace name | Established meaning |
|---|---|---|
| `977a` | gruzzle_x | World collision-grid X in8px units. |
| `9794` | gruzzle_y | World collision-grid Y in8px units. |
| `6636` | gruzzle_type | Sprite/body variant0..3. |
| `c3c9` | gruzzle_state | -1 normal;0..23 slime sequence;24 completed slime state;>34 spawn countdown. Do not invent meanings for unobserved25..34. |
| `982c` | gruzzle_animation_index | Normal animation index0..11, incremented **after drawing**. |
| `ab0a` | gruzzle_jump_phase | -1 not rising;0..8 rise phase. |
| `0f40` | gruzzle_move_timer | Increments per visited entity update; controls horizontal attempts. |

Other valuable scalar fields: `DS:021b` horizontal cadence threshold (initialized4), `DS:982a` level/difficulty-related RNG divisor input (runtime value; not initialized file data at that high DS offset), `DS:026b` player death flag, `DS:018a` exit state, `DS:01ac` transition/restart-related flag, `DS:0146` demo mode, `DS:017a` slime sequence/action-busy state, `DS:01bf` animation enable. Use raw names for incompletely decoded flags instead of asserting full semantics.

### Evidence and timing

* Normal setup at `0x5060–0x50b5` copies ten starting positions, sets state=-1, animation=0, random type0..3, jump=-1. Count bounds the active portion.
* Wrong-match spawn at `0xc488–0xc503` appends/reuses slot9 when full, writes target grid X and targetY+1, type `rand()%4` (deterministic slot%4 in demo mode), state64, animation0, jump=-1, then increments count. The count is10max on this path.
* Every visited actor increments move_timer at `0x53cf`. If state>34, decrement it; reaching34 changes state to-1 and processing can continue in that update (`0x53d7–0x5404`).
* Ordinary horizontal attempts occur when move_timer>DS021b and state==-1 (`0x54de–0x54fd`); reset timer0 at `0x5501`. With threshold4 this is an attempt every fifth visited update, subject to spawn/offscreen/state flow. RNG can alter the approach direction (`0x552a–0x5549`).
* Jump phase0..8 decrements Y per update and increments phase; reaching9 resets it to-1 (`0x560b–0x5628`). Collision can cancel it sooner. Jump initiation writes0 at `0x5746`.
* Normal animation maps index through `DS:021d`: `[0,0,1,1,2,2,3,3,2,2,1,1]` (`0xbaa3–0xbab1`). For normal active state, rendering increments index at `0xbb4f` and wraps after11 (`0xbb57–0xbb60`). Therefore completed-state animation_index generally points at the **next** draw, not the just-captured frame. Offscreen actors skip these render increments.
* A successful slime action sets state0 and animation0 (`0x5232–0x523d`). Renderer handles state0..24 at `0xbd84–0xbd9d`, increments state at `0xbe54`, and reaching24 starts a10point reward (`0xbe64–0xbe70`, DS0154 initialized10). Renderer is a gameplay-state mutator; sampling after entity processing but before rendering will miss these changes.
* Normal gruzzle sprite destination top-left is `(16+8*(gx-cameraX),9+8*(gy-cameraY))`, established at `0xbac3–0xbae1`. The Y offset is32−23. A separate slime effect uses a different anchor; do not apply the normal formula to it.

### Array identity and snapshot hazards

Deletion compacts state/X/Y/type/animation/jump arrays (`0x5469–0x54cb`, repeated at `0x5785–0x57e7`), decrements count and backs up loop index so the shifted actor can be visited. **The move-timer array is not shifted by these copies.** Treat slot index as current storage position, not a persistent actor ID. A trace matcher must account for compaction and preserve the original timer-slot behavior.

Count and arrays should be read in the same stabilized snapshot set. Validate count0..10; retain raw arrays if count is invalid rather than indexing outside them. New actor count is incremented after its fields are assigned, whereas deletion overwrites rows before decrementing count: a paused mid-mutation read can be stable but intermediate. The same completed-update sampling limitations apply to gruzzles, score, collision attrs and player position.

## Scope

This pass identifies existing boundaries and diagnostic memory, not a full gruzzle implementation. It does not prove a memory-only exact sampler or change tracing/gameplay code. The immediate useful extension is richer phase/actor diagnostics; the exact long-session boundary requires instruction access or explicitly modeled intermediate execution stages.
