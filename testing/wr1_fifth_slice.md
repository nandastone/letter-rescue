# Fifth slice: gruzzles and slime

The opt-in `--original-rules` mode now runs gruzzles through the recovered WR1
integer update loop. The controlled walk/jump, wrong-match spawn, slime hit, and
slime miss replays match **347/347 completed states**, including actors, RNG,
player motion, camera, animation, word/book state, score, and background phase.
Two actual **320×200 gameplay images match every pixel**. This extends the earlier
first-frame rendering match into moving gameplay and a slime action.

| Replay | Completed states | Validation with entry frame and inputs |
|---|---:|---:|
| Controlled walk/jump | 64/64 | 50/50 |
| Wrong-match spawn | 83/83 | 69/69 |
| Slime hit | 100/100 | 85/86 |
| Slime miss | 100/100 | 85/86 |

Each replay excludes its known startup-Enter admission difference from timing
validation, while still comparing the completed state. Both longer slime runs
also expose the same **update94 entry-frame residual**: clone source input885
(worker886), native worker887. There is no input or completed-state difference.
The comparator continues to report this as a failure of exact entry timing.
No future tick schedule or expected actor states are fed into the clone.

## Recovered behavior

`scripts/core/wr1_gruzzles.gd` implements entity/action function file50e8..585c and
renderer ba38..bf50 from the pinned WR1.EXE hash recorded in earlier reports.
It uses the same logical update as the player, after word/book contacts and
before camera/rendering. Normal rendering increments the animation index only
for visible actors; the slime renderer advances slime state even offscreen.

- Borland RNG: `(state * 0x015a4e35 + 1) & 0xffffffff`, returning bits16..30.
- Easy difficulty overrides the initialized cadence4 with **6**, and sets the
  decision parameter to14. Medium uses6/2 and hard2/1 (parameter/cadence).
  Easy horizontal random-choice divisor is therefore **-2**, as in signed IDIV.
- Timers increment for offscreen actors, which otherwise remain frozen. They
  are initialized to **0..9**, including inactive slots, and are **not moved**
  when another actor's arrays are compacted into their slot.
- Normal motion uses raw8px cells, the original collision rectangles, support
  rules, random-call order, nine rising updates, and cell-based player contact.
- Wrong matches use the shared RNG for type, state64, animation0, jump-1, and the
  original target grid. State falls to35, then becomes normal on the next update.
  Full capacity replaces slot9. The slot timer is retained.
- Slime requires eight entity updates since the last accepted action and no
  active slime animation. It scans columns in the facing direction, rows from
  cameraY through cameraY+20, and then slots. It does not use a radial distance
  limit or a line-of-sight test. Successful uses increment the five-use counter.
- Slime freezes the normal animation at0, advances through24 render states,
  gives10 points once, then removes the finished actor when outside the active
  rectangle. Requests while busy/cooling down are discarded. Empty requests
  still set the player action pose and reset the cooldown.
- Original actor contact now reaches the clone's existing death handler. The
  original death animation/restart timing is still a separate, unfinished slice.

Replays restore **only measured initial actor state, slot timers for active
actors, and RNG**, through `original_entity_start`. The difficulty values were
confirmed by the extended observation-only core. Ordinary unmeasured play uses
a deterministic seed1; native DOS time seeding and startup RNG consumption are
not claimed to match. The tested replays are level1/easy.

## Render checks

`tools/extract_wr1_gruzzles.py` reads the executable's sprite records. Gruzzle
art comes from STATIC with **cyan/index11** transparency. Slime comes from the
separate SLIME sheet with **blue/index9** transparency and a sourceY offset80.
Pink/index13 is visible artwork in both. The first extraction attempt used the
wrong transparent color and sheet; actual captures caught and corrected these.

Normal actor top-left is `(16+8*(gx-cameraX), 9+8*(gy-cameraY))`. Slime uses a
64px higher anchor and the renderer's clipping conditions. Spawn blinking draws
the black AND mask on alternate render pages; that path is ported from the
binary but has not yet received a dedicated pixel comparison.

The slime meter's four-pixel erasure and the collectible's tile238 sprite/origin
were corrected while comparing the scene. Native snapshots at counters620 and
628 match clone inputs619 and627: **0 differing pixels out of64,000 each**.
The second contains the slime effect, player pose, gruzzle, and depleted meter.
Fixtures: `wr1_actor_frame_620.png`, `wr1_actor_frame_628.png`, and hashes in
`wr1_actor_pixels.json`. Side-by-side review image:
`testing/output/wr1_actor_compare_628.png` (original left, clone right).

The attempted counter660 image does not match: returned native video still
predates paused memory/camera. Its raw capture remains in output. This is not
counted as a successful pixel comparison or silently shifted to another frame.

## Evidence and validation

The native core adds read-only fields for difficulty/cadence, action request,
busy/death flags, slime used, and reward. Original game bytes remain unchanged;
the installed DOSBox Pure core is untouched. The separate tracing DLL retains
the fourth-pass source revision and patch, with the updated callback source.

New fixtures are `wr1_spawn_{replay,boundaries}.json`,
`wr1_slime_hit_{replay,boundaries}.json`, and
`wr1_slime_miss_{replay,boundaries}.json`. Each records source BSV, EXE, core, and
instruction-trace hashes. Raw capture pairs live under ignored `testing/output`:
`wr1_spawn_native`, `wr1_slime_hit_native`, and `wr1_slime_native` (the miss).
The latter two were captured through counter922; spawning through822.

`tools/build_wr1_slime_replay.py` reproduces the two940-frame slime BSVs from the
existing770-frame controlled replay. `--hit` selects presses620..623,640..643,
850..853; without it presses580..583,600..603,850..853. Both preserve the original
movement inputs and initial savestate. Playback is forward only, with zero
backrefs. Convert with `tools/replay_to_json.py --start-frame 338`, preserve the
measured70.086304 source FPS and initial background0, then use the fourth-pass
capture and boundary-preparation commands. Clock calibration still uses only
idle counters350..419.

All **35 Python tests** and **five Godot suites** pass. The latter cover305
motion checks,2458 matching checks,26 native integration updates plus projection,
107 scene interaction checks, and10 actor edge conditions. Fault injection now
also proves that actor timer or RNG corruption fails despite matching player
state. Slime regressions explicitly retain update94's timing discrepancy.
Verbose accelerated runs retain the existing audio shutdown leaks (collect,
wrong, reveal WAVs); tests reject unrelated resource/script errors.

## Remaining work

1. Port raw-cell slime-bucket pickup/refill and its background/attribute restore.
   The visible bucket is now correct, but collection still uses the legacy
   Area2D path and does not yet replenish the new original slime counter.
2. Add dedicated spawn-blink and later slime/puddle pixel fixtures. Verify the
   type2/frame3 sprite record's inconsistent right edge before claiming all art.
3. Recover missed/empty-action effect rendering, full death/respawn behavior,
   medium/hard and other levels, and demo RNG resets.
4. Resolve the scheduling residual before longer interactive input sequences.
   At native frontend887, PIC12704.000185ms already has timer8, but the gameplay
   loop enters at12704.019741ms in the next launched worker. Earlier idle entries
   also show occasional CPU delays. This is a main-loop admission issue near a
   frontend handoff; merely retuning movement or fitting to this late tick would
   not establish a general fix.
