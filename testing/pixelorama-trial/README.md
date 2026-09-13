# Editable Pixelorama sprite projects

Keep the editable projects and their PNG exports in version control:

- `wr1_girl.png.pxo` — editable Pixelorama 1.2.2 project; open this to continue
  drawing. Preserves the animation frames and layer structure.
- `wr1_girl_trial.png` — transparent PNG spritesheet exported from that project.
- `wr1_boy.png.pxo` — clean editable male project with all 26 original frames.
- `wr1_boy_sheet.png` — clean transparent male sheet, 624×32; decoded ARGB pixels
  match `assets/sprites/wr1_boy.png` exactly, including frame order and alpha.

These are source projects for further editing, not finished shotgun artwork.
The female trial contains 27 frames of 24×32 pixels: original frame 1, a test duplicate, then
original frames 2–26. The duplicate has three cyan test pixels at (0,0), (1,0),
and (2,0). All 26 original frames are pixel-identical to
`assets/sprites/wr1_girl.png`, including alpha.

The male project contains only the original 26 frames of 24×32, with no test
duplicate or test pixels. It was imported, saved, and exported through the
Pixelorama desktop UI without image generation or scripted image modification.

## Continue editing

1. Open the desired `.pxo` project in Pixelorama (do not reimport the exported PNG).
2. Save a new project for production artwork before replacing the test duplicate
   or adding ready/recoil/pump poses. Keep the original game sprite unchanged.
3. Save the `.pxo` project as well as any exported PNG after editing.
4. Use **File → Export as → Spritesheet**, one row, all frames, forward order,
   100% scale, no padding. The female trial exports at 648×32; the clean male
   project exports at 624×32.
5. Explicitly choose an export path in the current checkout. The editor may
   remember an absolute path from the checkout where the project was saved;
   avoid the quick overwrite command until the destination has been checked.

The portable editor executable is installed outside the repository and is not
part of the source assets. The `.pxo` and PNG are the portable project files.
