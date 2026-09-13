# Hand-edited boy shotgun artwork — all 26 poses

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
