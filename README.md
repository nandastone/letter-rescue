# Letter Rescue

A word-matching educational platformer for kids, built with [Godot 4.6](https://godotengine.org/).

Players explore side-scrolling levels, collect letters, and match words to pictures — all while avoiding enemies (Gruzzles) and hazards. Inspired by the classic DOS game *Word Rescue*.

## Gameplay

- **Explore** platformer levels with running, jumping, and ladder climbing
- **Reveal** words hidden inside question blocks
- **Match** each word to the correct picture block
- **Avoid** Gruzzles — or freeze them with slime!
- **Collect** mystery letters to uncover bonus words
- **Progress** through the 15 recovered WR1 levels at Easy, Medium, or Hard difficulty

## Controls

| Action | Keys |
|--------|------|
| Move | Arrow keys / WASD |
| Jump | Up / W |
| Drop through platform | Down / S |
| Use slime | Space / Enter |

## Running

1. Install [Godot 4.6](https://godotengine.org/download)
2. Open the project in the Godot editor
3. Press F5 to run

### In a browser

Every push to `main` that touches the game publishes a web build to
<https://nandastone.github.io/letter-rescue/> (see `.github/workflows/web.yml`).
It always runs the original rules; add URL flags for the other options, e.g.
`?clear-text`, `?skip-intro` or `?mute-original-audio` (combine with `&`).
In Chrome, the install icon in the address bar adds it as an app. `just web`
builds the same thing locally into `build/web/`.

### Original mode

Use `just run-original` for recovered Word Rescue gameplay and artwork, now
including the original startup, menus, player profiles, ending, music and
PC-speaker effects. Add `--skip-intro` to go straight to name entry, or `--mute-original-audio`
for silent play. See [audio implementation and verification](testing/wr1_audio_research.md)
for source evidence and remaining fidelity limits.

Use `just run-clear` (or `just run-original --clear-text`) for Clear Text mode.
It keeps the original rules and draws gameplay text, scores, bonuses, word cards,
menus, instructions, intro and ending text at the window's resolution. Text uses
the bundled [Andika literacy font](https://software.sil.org/andika/design/), with
room for descenders and the original hidden-letter rules on Hard. No font
installation is needed. `just run-original` retains the original pixel display.
Both commands accept `--skip-intro`. The target word fits inside its original
beveled panel. Illustrated screens keep their pictures and frames with readable
lettering over the original text areas.

In original mode, arrows move/jump/climb, Ctrl also jumps, and Space/Alt use
slime. Escape opens the menu and resumes the same paused game. During play,
H shows help, W shows the word list, S selects sound, Q asks to quit, and +/−
change game speed. Menu letters select their labelled entries; Keyboard Redefine
sets Right, Left, Up, Down and Slime in order (choose Y to activate/save them).
Remapped keys take precedence over shortcuts; unshadowed default controls remain
available. The preserved original help artwork swaps the Ctrl/Alt labels;
the controls above follow the measured executable behavior.
The Joystick menu enables a connected gamepad's left stick/D-pad and A/B slime.

Enter a name of up to eight letters, digits or underscores, then select the girl
or boy. Returning names load native-format `.wr1` profiles from Godot's
`user://wr1/` directory (Windows: `%APPDATA%/Godot/app_userdata/Letter Rescue/wr1/`).
Profiles save the level, words, score and controls; they restart the saved level.
Run Demo plays all fifteen original demos in sequence, with title/story
interludes. Any key returns to the menu and preserves the suspended live game.
See [frontend source and verification](testing/wr1_frontend_research.md).

## Original-game regression suite

Run `just parity` to play all 15 original Word Rescue demos in their native order
and compare gameplay state, controls, timing, endings, and sampled screenshots
against the saved DOSBox captures. Each demo starts after loading from one
checkpoint. Python with Pillow and Godot are required; `PYTHON` and `GODOT`
can override their paths.

The demos replace the earlier manually authored level routes as the maintained
suite. Results and difference images go to `testing/output/parity/`. For a focused
run, use `just parity --scenario demo_level6`. See the
[parity workflow](testing/wr1_parity_workflow.md) for coverage and reproduction.

Use `just parity --clear-text` to exercise the readable display with the same
15 demos. Gameplay state, inputs and timing still compare directly to DOSBox.
Pixel comparisons use the preserved 320×200 reference video stream; separately
saved `*_clear.png` files show the actual readable display and are **not** claimed
to match the original pixels. See [Clear Text design and checks](testing/wr1_clear_text.md).

Ordinary-play observations and the recovered level-title screens are documented
in [ordinary gameplay research](testing/wr1_ordinary_play_research.md).
Fresh games now use the recovered random initialization; recordings preserve
their initial seed, loaded profile, and speed/difficulty changes. See
[startup verification](testing/wr1_startup_research.md).

Supplemental frontend, attract and audio checks use the real Godot scene and
retained native screen fixtures. Set `GODOT`, then run
`python -m unittest testing.test_wr1_frontend testing.test_wr1_attract testing.test_wr1_audio testing.test_input_replay`.
These include visible-window and mixer tests; they supplement the fifteen demos.

## Project Structure

```
scenes/          Scene files (.tscn)
scripts/         GDScript source files
assets/
  audio/sfx/     Sound effects
  fonts/         Bitmap font
  pictures/      Word-picture images
  sprites/       Character and object sprites
  tiles/         Tileset graphics
data/levels/     Level data (JSON) — ep1, ep2, ep3
tools/           Python utilities for level conversion and asset generation
```

## License

All rights reserved.
