# Berserker player art

`berserker-source.png` was created with Codex's built-in image generation,
using `assets/sprites/wr1_girl.png` and `wr1_boy.png` as character references.

Prompt: Create an EGA pixel-art sheet with the original girl (black bob, red
headband, cyan top, green dress) and boy (blond hair, cyan shirt, blue trousers),
each holding a pump shotgun in both hands. Four right-facing poses per row:
ready, running, firing recoil, pumping. Preserve recognizable characters,
chunky black outlines, consistent foot baseline, no text or separate gun prop.

Run `tools/build_berserker_assets.gd` with Godot to remove the generated neutral
background, quantize to EGA colors and pack the two transparent 28-frame atlases
in `assets/sprites/berserker_{girl,boy}.png`. Frames 0–25 map the existing engine
poses; frames 26–27 are recoil and pump, mirrored at runtime for left shots.

Sound sources: Freedoom commit `d14dbbee3b6fbfb2c11cdb65eb61216e86d4ee85`,
`sounds/dsshotgn.wav`, `sounds/dssgcock.wav`, `sounds/dsslop.wav`.
The full copyright notice and BSD conditions are shipped with all builds.
