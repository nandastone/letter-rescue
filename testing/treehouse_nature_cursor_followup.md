# Nature quiz cursor and final audit follow-up

2026-09-27. Original executable disassembly, read-only RAM and ordinary input only. No runtime edits.

## Cursor result: yellow, with a transient absent-pointer frame

There is **no white-cursor rule** in the captured guessing/hover sequence. The earlier46-pixel discrepancy was an incorrect interpretation of a diff image: the native frame contained plain background at those locations because the cursor was absent.

The original `research-nature/quiz-win-capture/state/guess-mode.png` was captured at a RAM/VGA presentation boundary after guess-entry animation. Its RAM already has DS557C=1 and DS57C0=0, but its last presented image has no arrow. Restoring that `.state` and advancing **one callback** yields the normal yellow arrow.

### Source rule

- Cursor foreground is DS2060; initialized to logical color **14** at main **01B0**.
- The cursor renderer at main image **15DCB–15DD0** passes DS2060 to the final OR-mask drawing operation. The black/foreground masks come from the selected CURS resource; ordinary CURS0 uses the builtin68-byte record at image310B0.
- Main animation wrapper **442B** calls residentD51:**857A** to hide the pointer before playback, and main **4B3D** calls residentD51:**8822** to show it after cleanup.
- Resident857A is image15A8A; it updates the nested cursor visibility state DS2062. Resident8822 is image15D32. This is a visibility operation, not a color change.
- Native DS2060 remains **0x000E** for the old guess boundary, normal human turn, win, second reveal, and all newly captured hover states. Logical14 is standard VGA yellow **RGB(255,255,85)** here.

### Ordinary native evidence

Driver: `output/treehouse/research-nature-audit/cursor-native.py`. Restore hash, exact inputs and DS observations are in `cursor-native/run.json`.

| New capture | Input | Yellow cursor foreground pixels in20×20 pointer crop | DS2060 |
|---|---|---:|---:|
|`state/one.png`|One callback after restore|54|14|
|`state/wait.png`|20 further callbacks, no movement|54|14|
|`state/move-on-guess.png`|Move one logical pixel, remain over guess button|54|14|
|`state/move-card.png`|Move away from guess button|54|14|
|`state/return-guess.png`|Return to guess button|54|14|

`cursor-crops.png` contains these five original crops. `research-nature-audit/cursor-three.png` contrasts the old pointer-absent boundary image with normal human-turn and win arrows.

Implementation consequence: use ordinary yellow when the stable guessing screen is interactive. Suppress the pointer during native-equivalent SCR playback. Do not add any white hover state to match the old boundary screenshot. For stable guess-screen comparisons use `cursor-native/state/one.png` or `wait.png`.

## Latest audit fixes checked

Read-only reinspection of `treehouse-demo/nature-quiz.js` confirms the following were applied during the parent task:

- Question backdrop removal uses `frameUpdates > threshold`.
- Guess control is hidden during the ask/turn generators, and highlighted during guess entry/waiting.
- Second reveal suppresses the static shrub and retains displayed player until animation completion.
- Saved first-reveal rectangle is selected by winner role.
- Wrong guess clears selected candidate before its reaction; cleanup also clears it.
- `enterGuess()` now clears selected and explanation state. This appeared during the follow-up, after the first read.
- Winner retreat applies stage clear and foreground divider; ribbon waits until cleanup.
- Answer footer can render during result waits through `answerDisplay`.
- Eliminated candidates have gray backgrounds.

These checks establish presence of the corrections; this follow-up did not repeat every dynamic route against the changing implementation.

## Remaining concrete issue: candidate inspection after winning

New ordinary reference: `research-nature-audit/postwin-native/state/robot-card-inspected.png`, driver `postwin-native.py`. It restores the already captured two-animal-revealed state, moves to the first candidate `(20,151)`, clicks, and waits. Original result:

- Current inspected player is1 (robot); winphase DS55EA=1 remains set.
- Panel mode DS57D8 becomes−1 (candidate inspection).
- The left panel shows **Insects / Darkling Beetle**, its original large image, and **Has wings / Has armor / Eats plants**.
- The previously revealed secret-name footer is cleared.

Current reviewed code has three barriers to this original behavior:

1. Candidate clicks call `choose()` only when role is notrobot.
2. Candidate-inspection rendering requires `phase !== 'won'`.
3. `cleanup()` and `guess()` discard `available`, losing the three question facts needed for these inspection rows.

Source **343C–34A7** checks guessing state before selecting normal candidate inspection; it does not reject won state or opponent role. **34B7–34CA** clears the footer when replacing complete-reveal panel99. Source **3ADB** disables question decorations, but does not zero question flags DS52A2; the next turn rebuilds them. Preserve logical question choices separately from visible decorations.

Actionable fix: allow post-win candidate inspection for both displayed players; render its panel over the complete-answer panel, retain the existing shrubs/ribbon, show the three retained question facts, and suppress the complete-reveal footer until a shrub is clicked to restore secret information.

## Remaining concrete ordering issues

1. **Inspection already open when revealing the other shrub.** `revealOther()` clears selected/explanation before SCR starts. Original **2D59** runs SCR first and only then calls information renderers **2D6F/2D7E/2D92**. Preserve the entire displayed left panel/footer during second-shrub animation, including any inspection or definition, then replace it afterward.
2. **Turn entry displays the next player's cards and learned answers early.** `roll()` immediately switches `player`, and `draw()` uses that player during `perform(0)`. Original **2F9B** starts turn entry before the calls that repaint learned answers/candidates. The same `displayPlayer` approach used for second reveal should preserve old cards/answers until turn-entry SCR completes. Source sequence is documented in `treehouse_nature_completion.md`; this ordering claim is disassembly-derived, not a newly captured animation comparison.
