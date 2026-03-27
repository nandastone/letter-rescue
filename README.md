# Letter Rescue

A word-matching educational platformer for kids, built with [Godot 4.6](https://godotengine.org/).

Players explore side-scrolling levels, collect letters, and match words to pictures — all while avoiding enemies (Gruzzles) and hazards. Inspired by the classic DOS game *Word Rescue*.

## Gameplay

- **Explore** platformer levels with running, jumping, and ladder climbing
- **Reveal** words hidden inside question blocks
- **Match** each word to the correct picture block
- **Avoid** Gruzzles — or freeze them with slime!
- **Collect** mystery letters to uncover bonus words
- **Progress** through 15 levels across 3 episodes at Easy, Medium, or Hard difficulty

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
