# Treehouse maze completion: introduction, frog, drawer, and victory

Primary-source follow-up, 2026-09-27. Supplements [the maze model/rendering research](treehouse_music_maze_research.md), including its ten exact static native frames. Runtime untouched.

- [Choreography tables and ordinary-input intro observations](treehouse/maze-completion-tables.json).
- [Complete opening-drawer comparison](treehouse/maze-drawer-comparison.json): **24 independently generated 320×200 frames, all exact**,1,536,000 compared pixels, no differences.
- Scratch root `testing/output/treehouse/research-maze-completion/`.
- `intro-capture/` contains a new uninterrupted native first entry:40 snapshots at80-callback intervals, full callback timeline, state/RAM, hashes and ordinary mouse actions. `capture-intro.py` restores a piano state and clicks the bucket; no guest memory edits.
- `render-drawer.py guess-open <barY>` independently reconstructs each transitional drawer position from original resources and observed gameplay model; native callbacks are used only for exact RGB hash comparison.

All instruction addresses are overlay1 unless marked resident. Maze data is image2F9F0; shared state31690; resident DS321D0. Original pinned ZIP SHA-256 is `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`.

## Corrections to earlier high-level descriptions

**The player does not walk to a clicked sign before the reward.** Source55CC/57B4 registers **actor1, the frog**, at that sign's `sign_actor_targets` footpoint. The player remains at the node center. The frog appears, points/reacts, and disappears; afterward the player walks along the chosen exit path.

First-entry guidance does **not** start with four populated signboards. Renderer5929 draws their frames/arrows but skips candidate contents while maze data+5D3 is1. The tutor reveals left, up, right, down in order. First-introduction flag is then cleared before tutor playback, so the initial partial display requires a revealed-sign mask separate from that flag.

## Animation engine: timing and serial state

Resident825D begins an animation: set delay from DS+542, reset shared frame counter DS+5542 to-1, draw frame0 through8299, wait. Resident83F0 plays all frames once. Existing exported first/count/mirror/reverse tables remain authoritative.

Each one-shot animation's duration is `frameCount*frameDelay`, including the first frame. Pose3 is a static frame with zero delay. The original frame counter is shared across actors; choreography is serialized, so interleaving two independently incrementing actor counters can select different native frames.

Use native ticks for these timings. DOS video callbacks are approximately70Hz in these captures, while the observed tick stream advances at approximately60Hz. Do not treat one callback or one browser animation frame as one native tick. Exact capture `original_tick` values accompany the observed states in the numeric table.

| Animation | Actor | Frames | Delay | Duration |
|---|---|---:|---:|---:|
|8 reaction|Player|3|6|18 ticks|
|9 jump|Player/frog|8|4|32 ticks|
|10 climbing|Player|2|16|32 ticks per two-frame cycle|
|11/12 point left/right|Frog|3|8|24 ticks|
|13 appear|Frog|5|6|30 ticks|
|14 disappear, reverse13|Frog|5|6|30 ticks|

`8986(actor)` starts sound10033, plays animation13, sets pose3, then waits12 ticks. `89C5(actor)` starts10034, plays reverse14, then restores/frees the actor's saved background. `8A1A(actor,count)` repeats: sound10045, full jump9, sound10046, pose3, wait12. Thus each repeated jump has32+12 ticks plus call overhead.

## First entry, scene9

Source51B6 calls862D(introduction=true), then7062 starts the actual maze.

1. Draw MODULES2350/SHPL2340 at0,0: the large blank two-staff scene. Draw its empty score and two side controls. During this introduction the win-only song picture/title/global exit are omitted.
2. Register frog at footpoint `(y150,x42)`, pose3: its raster origin is `(25,112)`.
3. Play a frog voice, then bring the player into node9 by reversing its **direction1 ladder path**. The player starts above the ladder, climbs down in9-pixel steps using animation10, then follows the ordinary2-pixel walking segments to footpoint `(150,162)`.
4. Play a frog voice. Frog exits left. The source temporarily reduces node9-left path distance162 by100, since the frog starts120 pixels left of the usual node center; after its62+16 pixel travel the path constant is restored.
5. On the first visit, remove the player directly. On later entries, play a voice and walk the player out left before switching scenes.

Representative native references:

| Snapshot | Visible state |
|---|---|
|`intro-01`|Player near ladder top, frog waiting bottom-left|
|`intro-02`|Player partway down ladder|
|`intro-04`|Player traversing lower ladder path|
|`intro-05`|Player approaches large-scene center|
|`intro-06`|Frog leaving left, player centered|

Actor rectangles in the snapshots can outlive the actor's saved background handle. A retained rectangle alone does not mean that actor is visible after removal.

## Tutor demonstration in the first ordinary node

Sources7062..717C,7248..73B7,5929..5A81.

1. Initialize secret song, stage/node/challenge. Render ordinary scene with blank sign contents, since first-intro flag+5D3 is still1.
2. Clear+5D3 before running7248, so the demonstration runs only once per loaded original session.
3. Frog enters through direction2 (right) path to the ordinary node center. Player is absent.
4. For direction0,1,2,3:
   - Point the frog toward the candidate-box center. Target is `(signY+13,signX+14)` except up uses `(signY+23,signX+14)`.
   - Populate that candidate box in white.
   - Audition that candidate with visible per-note red emphasis where relevant (`5BB0(direction,showNotes=true)`).
   - Wait30 ticks.
5. After all four, wait90 ticks.
6. Play the correct target with `showNotes=false`, so target sound does not reveal the correct sign. Wait30 ticks.
7. Play a frog voice, then frog walks out through the correct exit.
8. Player enters from direction2/right, settles in pose3. Play target again invisibly and start idle timers900/360.

The first capture's ordinary node is2. `intro-07`..`09`: frog arriving from the right; `intro-10` shows only left candidate; `intro-12` shows the next reveal; `intro-17` shows all four; `intro-22`..`25` frog follows the correct exit; `intro-26`..`28` player enters; `intro-29` onward is settled gameplay.

Guidance movement/auditions/waits check for interruption. If interrupted, the caller removes frog, checks global exit/return, otherwise redraws the fully populated scene and continues with player entry. Do not restart the entire introduction after a simple skip.

## Frog pointing sprite and exact trajectory

Source8288..83E8, resident6DA9..706A. This is a moving small pointer sprite in addition to the frog's pointing pose.

Let frog rectangle be `(top,left,bottom,right)`, `cx=(left+right)//2`, `cy=(top+bottom)//2`. Determine right if `targetX>cx`. Play frog animation12 for right or11 for left (24 ticks).

Pointer shape and starting top-left:

| Relation to frog | TH shape / SHPL22000 | Start `(x,y)` |
|---|---|---|
|Right and below, targetY>cy|22050|(cx+10,bottom-11)|
|Right otherwise|22051|(cx+8,bottom-18)|
|Left and above, targetY<cy|22050|(cx-22,bottom-18)|
|Left otherwise|22051|(cx-21,bottom-10)|

Start sound1016. Move this shape from start to target via the original integer staircase, drawing every8 coordinate steps and at the final endpoint, with1 tick between drawn positions. Restore the previous sprite background each draw and remove the final sprite after arrival. Then frog returns to pose3.

Exact resident movement algorithm:

```text
dx=abs(targetX-x); dy=abs(targetY-y)
sx=sign(targetX-x); sy=sign(targetY-y)
error = dx ? floor(dx/2) : -1
step=0
loop:
  atEnd=(x==targetX && y==targetY)
  if step%8==0 or atEnd: draw; wait1tick
  if atEnd: break
  if error>=0: x+=sx; error-=dy
  else:        y+=sy; error+=dx
  step++
restore final background
```

This advances one coordinate per internal step, not both at once. Replacing it with floating-point linear interpolation produces different intermediate pixels.

## Correct sign choreography

Source54B9..579B. A sign press first flashes its candidate once (red12ticks, restore), auditions it visibly, then waits12ticks.

For a correct answer:

1. Increment correct streak; switch difficulty to1 exactly when streak reaches2.
2. Register frog at `sign_actor_targets[node][direction]`. Run appearance8986 (30+12ticks).
3. Gray the other not-already-attempted candidates. Preserve the chosen candidate and already attempted state.
4. Frog points to fixed reward target `(y106,x67)` using the moving pointer above.
5. Run reward roller/drop73B8 for the **current zero-based earned note index**.
6. Wait24ticks, run frog disappearance89C5 (30ticks), wait60ticks.
7. Increment earned-note count. If complete, open auto-reveal chooser and enter victory.
8. Otherwise play the collected melody, wait12ticks, sound10045, player animation8 (18ticks), sound10046, pose3, wait12ticks.
9. Play a frog voice, walk player outward through chosen path, update graph node, generate challenge, redraw, enter via stored reverse direction, play new target, reset idle timers.

The earned count changes **after** the visible note drop, frog disappearance, and60tick wait. Updating count at animation start changes which controls/replayed notes are available during the transition.

### Reward roller/drop timing

Recovered earlier; source73B8 confirms:

- `travelCount=17+13*noteIndex`.
- Roller2353 positions x=`60..60+travelCount-1`, y104,1tick each.
- Wait20ticks.
- Falling note at x=`87+13*noteIndex`, y=`107..147-smallPitchOffset` inclusive,2ticks each. Sound1000 at drop start,10025 at landing. Only the final position draws its ledger line.
- Wait20ticks.
- Retract roller through the same positions in reverse,1tick each. Sound1002 accompanies extension and retraction.

One source detail remains a parity caveat for unusual low notes:73EA reads its local notation flag before the later assignment at7425 while deciding the ledger. The ordinary settled renderer is established, but do not silently infer that this transitional uninitialized local is always the current flag. Native low-note transition captures would be needed to reproduce that edge case exactly.

## Wrong sign choreography and hints

Source579E..583E and83EB..84C7:

1. Reset streak0/difficulty0.
2. Register frog at that sign's actor target and run appearance (30+12ticks).
3. Wait30ticks.
4. Twice: frog pose15, sound10051, wait10; pose3, wait10; pose16, sound10052, wait10; pose3, wait10.
5. Wait30, then disappearance30ticks.
6. Gray selected candidate. Increment wrong-attempt count. From the second error onward, flash correct sign3times.
7. Mark selected direction attempted and reset idle timers.

Flash6A13 alternates red12ticks and original white/gray; between flashes wait12ticks, with no trailing extra wait after the final restore. Three flashes total60ticks. Do not gray the wrong sign before the frog sequence if matching native frame order.

## Song chooser opening and closing: all opening positions verified

Source7C84..826C. Final static recipe remains in prior maze research. The complete source-based opening renderer now matches native callback RGB hashes at **every** one of24 positions.

```text
opening barY = 106,104,102,...,60       24 positions
closing barY = 62,64,66,...,106        23 positions
frame delay = 2 native ticks
```

For each transitional frame, restore the underlying maze, draw top bar2354 at `(95,barY)`, drawer2355 at `(95,barY+4)`, and its six icons translated by `barY-60`. Clip drawer/bar contents to `(top60,left95,bottom112,right177)`. Draw handle2356 at fixed `(95,107)`. Question button remains red. The original uses backing-store transfers, but independent recomposition produces exactly the same pixels for all24 opening frames.

Sounds1004 open,1003 close. Closing uses the same geometry at the increasing bar positions; its exact source path is decoded, but the report's full-frame hashes validate opening frames specifically.

Inside the open chooser:

- Selecting a picture highlights it via771F: expand its20×22 rectangle by2 pixels, fill red, redraw the opaque icon. Audition the selected introductory melody; reload the secret SONG afterward.
- Wrong selection sets the guess lock and elimination byte, invokes disappointed frog83EB at fixed `(y135,x197)`, then closes.
- Correct early selection sets lock, plays sound1005 and waits for it, closes, then player jumps `SONG.shortLength-earnedNotes` times.
- Auto-reveal calls771F for the correct slot three times, plays earned melody, waits12ticks, closes, then player jumps **once**.
- The three auto-reveal calls do not include a12tick flashing delay or alternating restore in771F; do not automatically substitute the sign-flash animation for this routine. They repaint the same red picture frame.

## Victory transition

Source862D(introduction=false), after chooser returns success:

1. Register frog at the current node's **up-sign actor target**, regardless of the last clicked direction. Wait24ticks, run appearance8986.
2. Frog jumps once, plays voice, then walks up36 iterations ×2pixels =72pixels, using animation5/delay3. Remove frog.
3. Play voice; player exits through the current node's **up path**.
4. Draw large scene9 background2350, global exit, full song picture/title, two-staff full score, side controls. This exact settled rendering is already verified by `research-music-maze/render-win.py`.
5. Register frog at `(y150,x130)`, pose3.
6. Bring player in through node9 direction3, i.e. from below, ending at `(150,162)`.
7. Replay the full advanced song through84C8, temporarily forcing advanced1/repeat0 and restoring previous flags afterward.
8. Only after that playback returns, set phase17 and enter the victory-control loop. During arrival/playback it is still phase8; do not enable ordinary maze decisions against scene9.

### Victory control choreography

Source52D9..539E:

- **New maze (left control7):** update song history, flash control red for18ticks then white; frog voice and frog exits left, then another voice and player exits left. Free current song and call7062 to start a new ordinary maze. This does not replay the large-scene first-entry sequence.
- **Return piano (right6 or ladder2):** update history, flash right control18ticks, play voice, player follows node9 direction1 path up the ladder, then return.
- **Score8:** replay full advanced song.
- Escape/global exit updates song history and leaves through the appropriate outer path.

Node9 direction1 includes climbing direction4,9pixels/step, animation10. The ordinary direction labels alone are insufficient for this route; use the six-direction path/step tables exported by the earlier research.

## Implementation scope and remaining parity checks

The source now provides a concrete queue of phases and tick delays for first entry, tutoring, correct/wrong feedback, note reward, guessing, victory and return. Existing path/actor tables and exact static renderers can be reused. Persist first-introduction/revealed-sign state separately, and treat frog/player as separate actors with explicit visibility.

Verified directly: uninterrupted introduction ordering and actor positions, static scenes, and all24 opening drawer frames. Source-derived but not yet exhaustively compared: all frog pointer paths, reward low-note edge cases, sample completion delays, interruption during movement, complete closing-drawer callback timing, and each victory transition frame. The native callback recordings retain the evidence needed for those comparisons.
