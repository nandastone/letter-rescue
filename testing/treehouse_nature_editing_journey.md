# Complete nature editing journey

## Original reference and browser replay

`capture_nature_editing.py` restores the pinned original's empty exploration
screen once and drives 21 ordinary mouse checkpoints: place a day animal,
dismiss its fact, move it, decline erase, switch to night, place/remove/replace
a night animal, restore day, confirm animated erase, restore night, and change
the food filter and class. Original game RAM is only read.

`nature-edit-native-a` and `nature-edit-native-b` match in all checkpoint states,
PNGs, full callback timelines and recorded audio (`nature-edit-native-repeat.json`).
`verify_nature_editing_native.py` installs that initial empty screen once in the
browser, then replays the ordinary inputs. It compares whole-image membership
and active filter, collage geometry and RNG state without subsequent resets.

## Demonstrated defects

1. **Moving an existing animal opened a fact panel.** The original instead
   dismisses the fact panel (overlay 2, 0829–082F), retains the collage object,
   and reschedules its idle animation after a successful drop (0AEF–0AF4).
   The browser reused thumbnail selection, consuming a fact random draw and
   displaying unwanted text. The fix separates existing-object drag behavior
   and reschedules the retained object after its drop. Removing an object does
   not schedule it. `nature-edit-check-a` shows 4,613 differing pixels at the
   first moved-object checkpoint; candidate A makes this checkpoint exact.
2. **Declining/accepting a nature confirmation scheduled a room event.**
   The shared modal close handler consumed a random draw through
   `resident.scheduleAmbient()`. The original confirmation consumes none;
   this changed subsequent animal fact selection. Nature exploration questions
   now return without that room event. Candidate B matches all checkpoints
   through night replacement, including the previously different fact text.
3. **Day/night switching omitted animal timer initialization.** Original
   screen redraw calls 1924 for each animal in the restored scene
   (0E2A–0E55). The browser now schedules each restored animal. Candidate C
   matches all 21 images and all checked state/RNG values.
4. **Dragging a placed animal out was silent.** The original removal branch
   calls sound 10034 (08FE–0902). A normal-control test preserved the real
   sound callback while observing dispatch: the baseline removed the animal
   with no sound; candidate D dispatches 10034 exactly once. The correction
   is limited to existing-animal removal, the demonstrated native branch.

The changes follow original activity operations; there are no extra random
draws inserted to force particular seeds, and no recorded schedules in runtime.

## Save and reload

`verify_nature_editing_save.py` starts from normal character selection and uses
visible controls and scaled-canvas drags to create and move both collages,
decline single/both-scene erase, reload, remove an animal, confirm animated
erase, then reload again. Eleven assertions pass. Both geometry and remembered
filters persist; erased animals stay erased. No gameplay state is installed.

## Candidate and evidence

Candidate C SHA-256:
`9ac447f3b30f643adc55c922be4f80d453a482eece786b2dd365f29ffb00c117`.

Final candidate D (includes removal sound) SHA-256:
`e9af2b698fce8aec436c97f7052384f3aeb0f8d8ab8bf7059de2b8364f2d812c`.

- `nature-edit-check-a`: baseline, visible facts and RNG failures.
- `nature-edit-check-b`: existing-object drag correction only.
- `nature-edit-check-c`: confirmation correction added.
- `nature-edit-check-d`: complete 21-checkpoint image/state/RNG comparison passes.
- `nature-edit-save-a`: all 11 ordinary-control save/edit checks pass.
- `nature-remove-sound-baseline-a` / `nature-remove-sound-fixed-b`: omitted
  removal sound reproduced and corrected through normal controls.
- `nature-edit-check-f`: complete native editing comparison on candidate D.

Two attempted checks (`nature-remove-sound-fixed-a`, `nature-edit-check-e`)
started before the asynchronous candidate D build had finished. They failed
with a missing HTML file, before exercising the game. Their empty output
directories remain preserved; the completed-build runs above replace them.

All three verifiers are registered in `verify_all.py`. Whole-game acceptance still
requires the integrated regression and delivery reports, plus resolution of
previously documented open comparisons.

## Remaining scope

Checkpoint image membership does not prove exact presentation timestamps or
audio equivalence. Native audio repeatability only establishes the reference.
The removal check proves sound dispatch, not waveform or exact start/stop timing.
Full day/night idle-animation and remaining sound coverage stay
open, as do broader cross-activity transitions.

## Delivery

`nature-edit-regression-b` passes all 56 suites on candidate D, and
`nature-edit-environment-b` passes all 183 image states. `nature-edit-delivery-a`
records the matching served hash and backup of the previous playable build.
The original board/theater and strict timing failures remain in the completion
verification; `completion-gate-ar.json` records the incomplete overall status.
