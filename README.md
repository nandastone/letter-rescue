# Letter Rescue

A word-matching educational platformer for kids, built with [Godot 4.6](https://godotengine.org/).

Players explore side-scrolling levels, collect letters, and match words to pictures — all while avoiding enemies (Gruzzles) and hazards. Inspired by the classic DOS game *Word Rescue*.

## Two games

- **Letter Rescue** (the default, `just run`) runs on the recovered Word Rescue
  engine with Clear Text and smooth motion: the original still updates about
  12 times a second in 8-pixel steps, and `scripts/game/smooth_motion.gd` draws the
  movement in between at the display's refresh rate. This is the game that
  changes from here; the demo parity suite does not check it.
- **Legacy** (`just legacy`, or `-- --legacy`) is the pixel-exact Word Rescue
  Part 1 that `just parity` verifies against DOSBox. `just legacy-clear` adds
  Clear Text. Keep it unchanged: changes to shared scripts must keep
  `just parity` green.

## Gameplay

- **Explore** platformer levels with running, jumping, and climbing
- **Reveal** words hidden inside question blocks
- **Match** each word to the correct picture block
- **Avoid** Gruzzles, or slime them!
- **Collect** mystery letters to uncover bonus words
- **Progress** through the 15 recovered WR1 levels at Easy, Medium, or Hard difficulty

## Running

1. Install [Godot 4.6](https://godotengine.org/download) and [just](https://github.com/casey/just)
2. `just run` for Letter Rescue, or `just legacy` for the original

### In a browser

Every push to `main` that touches the game publishes to GitHub Pages
(`.github/workflows/web.yml`):

- <https://nandastone.github.io/letter-rescue/> — Letter Rescue (11 MB pack)
- <https://nandastone.github.io/letter-rescue/legacy/> — the original (59 MB)

URL flags: `?skip-intro`, `?mute-original-audio`, and `?pixel-text` on the
legacy build for its original pixel display (combine with `&`). In Chrome, the
install icon in the address bar adds it as an app. `just web` builds the
default game locally into `build/web/`.

### Desktop

Tagging a release (`git tag v0.1.0 && git push origin v0.1.0`) builds Windows
and Linux versions and attaches them to the GitHub release
(`.github/workflows/release.yml`). Desktop builds contain both games: they
start Letter Rescue, and `-- --legacy` runs the original.

### The recovered frontend

Both games include the original startup, menus, player profiles, ending, music
and PC-speaker effects. Add `--skip-intro` to go straight to name entry, or
`--mute-original-audio` for silent play. See
[audio implementation and verification](testing/wr1_audio_research.md) for
source evidence and remaining fidelity limits.

Clear Text draws gameplay text, scores, bonuses, word cards, menus,
instructions, intro and ending text at the window's resolution. Text uses the
bundled [Andika literacy font](https://software.sil.org/andika/design/), with
room for descenders and the original hidden-letter rules on Hard. No font
installation is needed. The target word fits inside its original beveled panel.
Illustrated screens keep their pictures and frames with readable lettering over
the original text areas.

Arrows move/jump/climb, Ctrl also jumps, and Space/Alt use
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

## Legacy regression suite

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

The default game has its own gate, run in CI and locally with
`godot --headless --fixed-fps 120 --path . --script tools/smoke_default_game.gd`
(add `-- --replay data/wr1/demos/level1.json` for the attract path). It plays
headlessly and checks that updates run and that motion is drawn between them.

Supplemental frontend, attract and audio checks use the real Godot scene and
retained native screen fixtures. Set `GODOT`, then run
`python -m unittest testing.test_wr1_frontend testing.test_wr1_attract testing.test_wr1_audio testing.test_input_replay`.
These include visible-window and mixer tests; they supplement the fifteen demos.

## Project Structure

```
scenes/          Scene files (.tscn)
scripts/core/    Simulation, frontend and HUD shared by both games
scripts/legacy/  The DOS hardware and timing model (VGA scanout, OPL, clocks)
scripts/game/    Letter Rescue's presentation (direct drawing, smooth motion)
assets/
  audio/original/  Original music (CMF + rendered WAV) and speaker effects
  audio/original/ogg/  The same audio compressed for the default build
                   (tools/compress_original_audio.py; 55 MB -> 5 MB)
  extracted/       Graphics extracted from the WR1 data files
  fonts/andika/    Clear Text font
  sprites/         Character and object sprites
  tiles/           Tileset graphics
data/levels/       Level layouts (JSON)
data/wr1/          Recovered WR1 rules, demos and frontend data
testing/           Parity suite, research notes and native fixtures
tools/             Extraction, capture and parity tooling
```

## License

All rights reserved.
