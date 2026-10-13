# Balloon drift after returning to the room

## Result

The remaining first-return mismatch is an early start, not an incorrect
ordinary balloon movement rate. On served build
`377179be2807525d7c010e2da7e8b517d073be2f930b69d59cb9ff2836850df1`:

| Observation | Original tick | Browser tick | Browser lead |
|---|---:|---:|---:|
| Balloon timer reset during room rebuild | 19289 | 19258 | 31 ticks |
| First balloon movement after the return | 19681 | 19647 | 34 ticks |
| Subsequent movement intervals | 49 ticks | 49 ticks | Same cadence |

The first thirteen subsequent movement intervals match. The original idle
capture independently shows the same 49-tick spacing before a spider event
moves the balloon down in a separate two-tick clearance sequence.

These results point to room-rebuild/return scheduling as the source of the
lead. They do not yet attribute every tick to a particular operation. The
34-tick lead is evidence, not a runtime constant to insert. The ordinary
movement rule should remain unchanged. Original main `89BD..8B36` checks
`now > due`, moves the balloon, then resets its deadline through `B8A3`.

## Reproduction

`capture_balloon_schedule.py` restores an existing original snapshot and
replays ordinary inputs. Its optional observer reads position, deadline,
pointer and room flags while the emulator worker is held at video callbacks.
It does not modify RAM or instructions.

- `balloon-return-schedule-a`: first maze-to-room return, 25 observed changes.
- `balloon-idle-schedule-a`: room idle path, 72 observed changes.
- `balloon-return-control-a` and `balloon-idle-control-a`: same snapshots and
  actions without the observer.
- `balloon-schedule-control-proof-a.json`: all 359 control checks pass,
  including complete PNG/WAV inventories, file hashes and callback timelines.

The browser comparison adds optional `--observe-room` diagnostics to
`verify_maze_navigation.py`. It records state after each ordinary advance;
it does not change inputs or fidelity acceptance. Example:

```powershell
python tools/treehouse/verify_maze_navigation.py --html testing/output/treehouse/playable/index.html --reference testing/output/treehouse/maze-activity-tour-native-a --observe-room --output NEW_OUTPUT
```

`balloon-tour-observation-a` preserves the previous comparison's images,
checks, final states and native input schedule exactly. It still fails with
23/27 image matches and ten balloon-state mismatches. The four missing room
images remain missing. `balloon-return-diagnosis-a.json` records the measured
lead, equal cadence and observer-control comparisons.

## Remaining work

### Rebuild operation boundaries

The follow-up `room-rebuild-boundaries-a` records loading/drawing boundaries
on the same return. `room-rebuild-control-proof-a.json` passes 316 checks
against both a trace-disabled run and the ordinary capture core: complete
ordinary PNG/WAV inventories and callback timelines are identical. Extra
`live/` images produced by the trace observer are diagnostic snapshots and
are excluded from that ordinary-output inventory.

The rebuild begins at tick 19258; timers reset and the return animation begins
at tick 19289. Elapsed rebuild time is 530.384 ms. Catalog preparation accounts
for 112.447 ms and background drawing for 227.007 ms of that interval. This
locates the lead in original loading/drawing work, rather than a missing
explicit animation pause. It does not supply a general runtime timing model.

No captured delay is inserted into the browser. This investigation is retained
as evidence for the open timing issue; subsequent implementation work returns
to demonstrated input/gameplay/visual/audio differences. Instruction equality
is not a separate deliverable.

Reconstruct the room-rebuild and return scheduling from their actual operations
and verify the timing across other returns. A delay chosen solely to fit this
one capture would not establish the required behavior. No runtime files or
live build were changed during this diagnosis; full fidelity remains open.
