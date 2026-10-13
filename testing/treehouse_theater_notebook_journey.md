# Theater notebook journey

## Result

The existing playable build `1dde9b9a90a5` reproduces all 14 original notebook
checkpoints, including full RGB images, selection, token order, validation and
random state. No runtime change was required. The comparator starts from one
original blank-editor snapshot and uses mouse input thereafter, without
intermediate state or seed resets.

The journey covers:

- Rejecting an unselected notebook token dropped outside the sentence rail.
- Adding all four categories into specified rail slots, choosing phrases with
  the original random sequence.
- Rejecting a sentence with its action before its subject.
- Correcting its order and performing it.
- Dragging an already selected notebook category without adding another token.
- Returning a rail token after a drop onto the stage.
- Removing the subject by dropping it on the notebook, restoring it with a new
  randomly chosen subject, and performing the restored sentence.

The complete original capture repeats exactly across 12,299 video callbacks:
inputs, decoded state, checkpoint images, timeline and recorded audio agree.
Both browser replays pass. This establishes checkpoint image membership and
gameplay continuity; exact presentation timestamps and browser audio waveforms
remain separate open requirements.

## Evidence

- Capture tool: `tools/treehouse/capture_theater_notebook.py`.
- Original captures: `output/treehouse/theater-notebook-native-a` and `-b`.
- Repeat comparison: `output/treehouse/theater-notebook-native-repeat.json`.
- Browser comparisons: `output/treehouse/theater-notebook-check-a/report.json`
  and `theater-notebook-check-b/report.json`.
- Registered suite: `verify_theater_notebook.py`.

At this coverage milestone there were 64 registered suites. Its completion bundle combined the previous
63-suite integrated run with this separately repeated check on the identical
HTML. It did not claim a new 64-suite batch run. Known board, redraw, sound and
timing failures remain in the completion bundle.

The subsequent payment correction delivery `c6795ecc633c` reran all 65 suites
together, including this notebook journey; all passed.
