# Editable Pixelorama artwork

## Hand-edited boy shotgun artwork — all 26 poses

Authored in Pixelorama 1.2.2 through desktop computer use. No image model or
scripted pixel-writing API was used. Original clean projects remain in
`testing/pixelorama-trial/`.

Files:

- `boy-shotgun.pxo`: editable 26-frame project, 48×40 pixels per frame.
- `boy-shotgun-all-poses.png`: current 1248×40 transparent sheet, original frame order.
- `boy-shotgun-all-poses-preview.png`: editor-exported 4× overview (1344×640),
  four rows per column; frames run down each column, then across.
- `boy-shotgun-simple-wip.png` / `boy-shotgun-simple-preview.png`: approved
  first-pose checkpoint, retained for comparison.
- `boy-shotgun-wip.png` / `boy-shotgun-preview.png`: earlier extended-arm version,
  retained for comparison; not the current project output.

All **26 original poses** are armed: idle, left/right movement, landing,
jumping, reaching and climbing. Weapon placement follows the original pose
and the two-pixel rise on the high running strides. The default game's boy
berserker mode now uses a byte-identical copy at
`assets/sprites/berserker_boy_handdrawn.png`. This is integrated locally, not
released. It is not a drop-in replacement for the older generated 28-frame atlas.

Canvas enlargement adds transparency only: original 24×32 artwork is placed at
(12,8), preserving the bottom-center anchor and original pixel size. A decoded
ARGB comparison of the exported sheet against the padded original confirmed
55–62 changed pixels in each frame, confined to that pose's 21×5 shotgun
bounds. Every pixel outside those bounds matches the original, including
transparency (transparent RGB values are ignored).

The revised pose restores the compact original side-profile arm and hand,
removing the added cyan forearm and second hand. The shotgun sits above the
original grip; silhouette takes priority over anatomical realism.

Layers, top to bottom:

1. `Shotgun + holding arms`: hand-authored gun (legacy layer name), populated
   on all 26 frames. The exported character includes these pixels;
   this is not a runtime-attached weapon.
2. `Layer 1 (copy)`: visible original-body working layer, now locked to protect it.
3. `Layer 1`: hidden, locked original reference layer.

Frame indices and native left/right poses are preserved. The original body
animation was not replaced with copies of the standing character. Runtime
presentation uses native left/right poses without double-mirroring them;
front/back poses and mid-jump direction changes mirror only when needed to
aim in the current direction. A per-pose barrel-tip table positions the flash
and shell effects. Firing retains the movement pose and briefly offsets it by
up to two pixels for recoil; dedicated drawn recoil/pump frames remain future
art work. The shared pump sound, ejected shell, cooldown and gibs are retained.
The girl project and its existing runtime atlas are unchanged.

Export the full sheet using File → Export as → Spritesheet, **all frames**,
visible layers, forward order, one row, **100%** scale. Explicitly set the output
path in the current checkout. The last editor export settings are the enlarged
overview (four rows, Columns orientation, 400%); restore one row and 100%
before exporting the native sheet again.

After an approved export, copy the PNG unchanged to
`assets/sprites/berserker_boy_handdrawn.png` and reimport in Godot. If weapon
placement changes, update `BOY_MUZZLES` in `scripts/game/berserker_art.gd`.
Run `tools/smoke_berserker_mode.gd`: it compares the imported source and runtime
images and checks all 26 poses in both directions through firing, barrel-tip
alignment against the actual gun pixels, shell timing and unarmed restoration.

The earlier `tools/build_berserker_assets.gd` builds image-generated artwork and
is not the source of this hand-edited project. Its legacy output filenames are
separate and cannot overwrite the runtime hand-drawn boy sheet.

## Krsna vocabulary artwork

`krsna-words.pxo` is the editable Pixelorama 1.2.2 source. It has nineteen 24×24
pictures, with **two adjacent frames per picture** (38 frames total), in this order:

1. cow
2. calf
3. milk
4. gopi
5. flute
6. radha
7. lotus
8. krsna
9. butter
10. altar
11. peacock
12. garland
13. boy
14. conch
15. beads
16. tulsi
17. pot
18. crown
19. kirtan

The second batch replaces gun → boy, ghost → conch, scale → beads,
and teepee → tulsi. The last is deliberately one letter shorter. Camera → kirtan
uses the centered dancer. Pot and crown retain their existing words and override
only the default-mode art. Milk replaces wine (not flag). Music, dance and flag
use the original WR1 words and pictures; ghee has been removed. Tulsi shows a manjari flower/bud spike
with two small basal leaves. Beads is a close-up of four separated wooden beads
on a drooping cord. The conch uses the elongated shankha silhouette on its side,
with a narrow aperture and tapered end.
Botanical and museum references and drawing notes are in `reference-notes.md`.
Cow is a face-on portrait with broad ears and a wide muzzle, without a hanging
bell or chin detail. `cow-preview.png` provides an enlarged nearest-neighbour view.

Every card uses WR1's black border and 21×21 coloured inset at (2,1) inside
the 24×24 page. Backgrounds are individually chosen to contrast with the existing
drawings. Most silhouettes are simply positioned within that inset; gopi, Radha
and Krsna omit one redundant row, and conch and beads omit one column, avoiding
resampling or cutting into the frame. The source grids remain intact.
Placement centres the combined two-frame silhouette inside the coloured area,
excluding the black border. When odd/even pixel dimensions leave a one-pixel
margin difference, visible ink balance chooses the closer whole-pixel position.
Both frames use the same anchor, so tail motion never shifts the whole animal.

Six pictures animate: cow blinks, calf swishes its tail, altar lamps flicker,
peacock eye-spots catch the light, garland sways, and kirtan sways over planted
feet. The peacock's head and neck do not move. The other thirteen pictures have
identical frame pairs. Runtime uses the existing picture clock (eight updates
per frame); neither Legacy art nor animation timing is changed. Pixelorama's
preview is set to 1.5 fps, approximately the default game speed.

The game loads the horizontal runtime atlas at
`assets/sprites/krsna_words.png`. After hand-editing the project in desktop
Pixelorama, export all frames as a horizontal spritesheet at 100% scale to that
path. Keep every frame exactly 24×24 and preserve the adjacent-pair order:
cow 0, cow 1, calf 0, calf 1, and so on. The atlas is 912×24.
`krsna-words-preview.png` and `krsna-words-preview-2.png` show the two phases;
`krsna-words-animated-preview.gif` loops between them for review.

To rebuild that review GIF after exporting the two contact sheets:

```powershell
Copy-Item tools/art/pixelorama/krsna-words-preview.png build/word-card-0.png
Copy-Item tools/art/pixelorama/krsna-words-preview-2.png build/word-card-1.png
ffmpeg -y -framerate 3/2 -i 'build/word-card-%d.png' -filter_complex '[0:v]split[a][b];[a]palettegen[p];[b][p]paletteuse=dither=none' -loop 0 -final_delay 67 tools/art/pixelorama/krsna-words-animated-preview.gif
```

The pixel sketches are in `krsna_pixels.gd`, used by
`tools/build_krsna_word_art.gd` to seed the local source and atlas. These are
code-authored pixel clusters, not strokes drawn through the editor UI.
Pixelorama opens and exports the resulting `.pxo`; it is the editable source
for subsequent manual refinement. The builder is a bootstrap tool: running it
again overwrites later hand edits.
