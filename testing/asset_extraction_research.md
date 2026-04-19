# Word Rescue Asset Extraction — Research Report

Date: 2026-04-19
Scope: Episode 1 shareware (`wrsw20.shr`) for the `letter-rescue` Godot clone.

---

## 1. Archive / file formats

**`wrsw20.shr` is NOT a self-extracting EXE.** Hex inspection of the first
0x100 bytes shows it begins with 32 bytes of 0x00 and contains no `MZ` /
`PK` / `-lh-` / `LZ` magic. It is a plain data file consumed by the
companion `install.exe` (which IS a real MS-DOS `MZ` binary, 142 KB) sitting
in the same directory. To "open" the shareware archive you run
`install.exe` under DOSBox; it writes out the same family of files you
already see for episodes 2 and 3 on disk:

```
wr1.exe                   (game binary)
wr1.1, wr1.2              (GX Library archives — graphics)
wr1.3                     (ASCII word lists)
wr1.4, wr1.5, wr1.6       (CMF music)
wr1.7                     (PCX — Apogee logo)
wr1.s0 ... wr1.s19        (level data, one file per level)
wr1.d0 ... wr1.d19        (recorded demo input macros, sparse)
high.wr1                  (high scores)
*.wr1                     (player saves, one per name)
```

The `.shr` container itself is not documented on ModdingWiki — there is no
"Word Rescue Archive Format" page, libgamearchive does not list `.shr`,
and Camoto does not edit it. **The supported, documented "archive" in this
ecosystem is `wr?.1` / `wr?.2` (the GX Library files), not `.shr`.** So
`.shr` is a black box that nobody has bothered to RE because the install
step only has to run once.

**Engine lineage.** Word Rescue was written by Redwood Games for Apogee. Its
direct sibling is **Math Rescue** (same engine, same file scheme, same
demo-format quirks called out on ModdingWiki). It does **not** share
engine code with Commander Keen, Cosmo, or Crystal Caves — those use
EGAGraph / ProGraphx Toolbox / their own tile formats. Practically, the
only sibling that helps is Math Rescue; its docs explicitly cross-reference
the Word Rescue level/demo formats.

Refs:
- https://moddingwiki.shikadi.net/wiki/Word_Rescue
- https://moddingwiki.shikadi.net/wiki/Category:Word_Rescue (10 pages, no archive page)
- https://moddingwiki.shikadi.net/wiki/Word_Rescue_Demo_Format

---

## 2. Asset formats

### Palette
**Your assumption is wrong, in a helpful way.** Word Rescue is not 256-color
6-bpc VGA — its tilesets are explicitly documented as **"320×200 16-colour
PCX file"** (EGA palette). The level header's `bgColour` field is a 0–15
EGA index. Sprites/UI in `wr?.1` are also 16-color.

There is **no standalone `.PAL` file**. The palette is the standard EGA
default palette, embedded per-image in each PCX header (PCX format carries
its own 16-entry RGB palette in the header). Practically: read any tileset
PCX, take its embedded palette, and you have it. The 16 RGB triplets are
6-bit-per-channel scaled to 8-bit when written by the original tools.

Backdrops resolve as `drop<N>.wr1` where N is the `backdrop` field
(e.g. `0x04` → `drop4.wr1`), stored inside `wr1.1`.

### Sprites
Stored inside `wr?.1` (GX Library). GX Library is an uncompressed
container — header `0xCA01`, 50-byte copyright string, 40-byte label,
entry count, then a flat directory of 8.3 filenames + offset + size + DOS
timestamp. **No compression** of the contained files; files are stored
contiguously but the directory order does not match physical order.
Each contained file is itself a PCX (16-color EGA). Animation frames are
just multiple PCX entries (e.g. `balloon.wr1`, `balloon2.wr1`).
Transparency: PCX has no native alpha — Word Rescue uses a designated
palette index (color-key) as transparent; the exact index is conventionally
0 for sprites in Apogee EGA games but should be **verified by inspection
once extracted**. NOT planar Mode-X — straight 4bpp PCX RLE.

### Tiles / tilemaps
- Tileset image: a PCX inside `wr?.1`, 320×200, **16×16 tiles** → 20×12 = 240 tiles per sheet (the bottom 8 pixels are unused).
- Animated background tiles: a list of `(x,y)` coords; the engine cycles through "the tile at (x,y) and the next 3 tiles to its right" in the tileset image.
- Foreground/attribute layer uses **8×8 tiles** (a separate, smaller tileset; presumably also in `wr?.1`).

### Level layouts
Each `wr?.s<N>` file is one level. **Self-contained**: the per-level word
list (the letters the player must collect) is embedded in the level file
itself as `letters[7]` — seven `WR_COORD16` (x,y) positions pointing at
spawn locations of the letter sprites. The level header also references
`tileset` and `backdrop` by index. Layout:

```
mapWidth, mapHeight, bgColour, tileset, backdrop  (UINT16LE each)
start, end                                        (WR_COORD8 player spawn / exit)
gruzzleCount + gruzzles[]      (enemies, COORD8)
dripCount    + drips[]         (origin + maxY)
slimeCount   + slimes[]        (COORD16)
bookCount    + books[]         (COORD16)
animCount    + anims[]         (COORD16, animated bg tiles)
fgCount      + fgTiles[]       (COORD16, attribute layer overlays)
letters[7]                     (the WORD to spell, as 7 sprite positions)
bgLayerData                    (RLE: count byte, value byte; expands to W×H)
attrLayerData                  (RLE: same encoding; expands to (W-1)×H×4 8×8 tiles, offset by X=1)
```

Viewport is **288×152** pixels. RLE = simple run-length pairs.

The actual *English word* itself isn't stored in the level — it's looked
up from `wr?.3` (an ASCII text file, one word per line). The level
provides only the seven letter pickup positions; the engine ties them to
the next word from `wr?.3`.

### Fonts
**Not separately documented on ModdingWiki.** No "Word Rescue Font Format"
page exists. HUD glyphs are almost certainly bitmap tiles inside `wr?.1`
(named something like `font.wr1` or sliced out of a UI sheet). This must
be confirmed by listing the contents of `wrsw20.1` after extraction.

Refs:
- https://moddingwiki.shikadi.net/wiki/Word_Rescue_Level_Format
- https://moddingwiki.shikadi.net/wiki/GX_Library
- https://moddingwiki.shikadi.net/wiki/PCX_Format

---

## 3. Existing tooling

| Tool | Word Rescue support | URL | Status |
|---|---|---|---|
| **Camoto Studio** (GUI) | Yes — listed as supported (sprites, tilesets, levels, music) | https://github.com/Malvineous/camoto-studio | Last release v1.2, **2015-02-21**. Unmaintained. Linux/autotools build, no Windows binaries. |
| **libgamearchive** + `gamearch` CLI | Yes — "Word Rescue (.1)" is a supported archive format | https://github.com/Malvineous/libgamearchive | Last release v1.2, 2015. CLI works. |
| **libgamegraphics** + `gametls` / `gameimg` CLIs | Yes — "tiles and fullscreen images" for Word Rescue | https://github.com/Malvineous/libgamegraphics | Same era / same author (Malvineous). Outputs to standardized 8-bit + RGBA palette; PNG export is straightforward. |
| **camoto-project/gamegraphicsjs** (JS rewrite) | **No** — Word Rescue not in supported list | https://github.com/camoto-project/gamegraphicsjs | Active-ish (2021), but doesn't help here. |
| ModdingWiki Word Rescue category | Documentation only | https://moddingwiki.shikadi.net/wiki/Category:Word_Rescue | 10 pages, complete enough to write a custom extractor in a day if Camoto fails. |

Nothing supports `.shr` directly. Everything assumes you've already run
`install.exe`.

---

## 4. Reverse-engineering work

**Effectively none in public.** Searches for Word Rescue decompilation,
disassembly, physics constants, RNG, or collision geometry returned zero
relevant results on GitHub or in modding forums. ModdingWiki documents
*data file* layouts but does **not** document any engine internals (no
gravity value, no walk speed, no jump arc, no RNG seed, no hit-box rules).

This is the single biggest gap for a "pixel-exact parity" goal: data
files give you correct *art and level geometry*, but matching the *feel*
of the game (jump height, fall speed, slime drip cadence, gruzzle AI)
will require either (a) frame-accurate empirical capture from DOSBox and
fitting constants, or (b) original disassembly of `wrsw20.exe` /
`wr1.exe` (a 16-bit real-mode MZ binary, ~140 KB — small enough for IDA
Free or Ghidra to handle in a weekend).

---

## 5. Estimated effort

**Asset extraction: Medium-Easy.** Camoto + the documented formats cover
~95% of what you need. The unknowns are (a) the `.shr` install step —
trivially solved by running `install.exe` in DOSBox once, and (b) the
font location — requires one directory listing of the extracted `.1`
file to confirm.

**Pixel-exact runtime parity (the bigger goal): Hard.** Not because of
assets, but because no engine RE exists. You will be reverse-engineering
physics constants from scratch. Plan for that as a separate workstream.

**Single biggest risk/unknown:** the **font sheet location and the
sprite transparency color-key index**. Both are unmentioned on
ModdingWiki and only discoverable by inspecting the actual extracted
files. Neither is hard to resolve once you have files on disk —
mentioning them so they aren't surprises.

A secondary risk: Camoto Studio is 11 years stale and Linux-only with
no binaries. You may end up using the lower-level `gamearch` /
`gametls` / `gameimg` CLIs from libgamearchive + libgamegraphics
directly, or writing a small Python extractor against the documented
formats (a weekend's work — the formats are simple).

---

## 6. Recommended extraction approach

Minimal, ordered:

1. **Install once in DOSBox** (5 min). Mount the directory containing
   `wrsw20.shr` and `install.exe`, run `install.exe`, target an empty
   directory. Out comes: `wrsw20.exe`, `wrsw20.1`, `wrsw20.2`,
   `wrsw20.3`, `wrsw20.4`–`.7`, `wrsw20.s0`–`.s19`, `wrsw20.d*`.
   (Filename prefix may be `wr1` rather than `wrsw20` after install —
   either way the layout is identical to the already-extracted
   `wr2.*` / `wr3.*` you have for the registered episodes.)

2. **List & extract `wrsw20.1`** with libgamearchive's `gamearch`:
   ```
   gamearch wrsw20.1 list
   gamearch wrsw20.1 extract <name>      # for each entry
   ```
   This gives you a directory of PCX files: tilesets, sprites, fonts, UI,
   backdrops. Same for `wrsw20.2` (the per-word picture PCXs).

3. **Convert PCX → PNG** (one-shot, any tool): ImageMagick
   `magick mogrify -format png *.pcx` works fine for 16-color EGA PCX.
   The PNG will carry the embedded EGA palette; export it once as a
   standalone `palette.gpl` / `palette.png` for Godot using ImageMagick
   or a 10-line Python script (read PCX header bytes 16–63 = 16×3 RGB).

4. **Identify the tileset(s) and font sheet** by inspection (the names
   are usually obvious — `tiles1.wr1`, `font.wr1`, `intro.wr1`, etc.).

5. **Parse `.s*` level files into JSON** with a custom ~150-line Python
   script. The level format is fully documented and trivially parseable
   (UINT16LE header, RLE-decoded tile arrays, fixed-shape entity lists,
   `letters[7]` array). Output structure suggested:
   ```json
   {
     "width": 100, "height": 12, "bg_colour": 4,
     "tileset": "tiles1.wr1", "backdrop": "drop4.wr1",
     "start": [3, 10], "end": [97, 10],
     "gruzzles": [...], "drips": [...], "slimes": [...],
     "books": [...], "anims": [...], "fg": [...],
     "letters": [[x,y],...x7],   "word": "APPLE",
     "bg_layer": [[...]], "attr_layer": [[...]]
   }
   ```
   Pair each level with the Nth line of `wrsw20.3` to recover the word.

6. **Skip `.d*` demo files and `.4`–`.6` CMF music for now** — not
   needed for pixel parity of gameplay; revisit if you want to clone
   the OPL music too (CMF is a documented Creative format, well-supported).

**Shortcut you asked about:** Camoto Studio's GUI will do steps 2–4 in
one click on Linux, with PNG export of tilesets and a level-editor view
of `.s*` files — but given the build pain on Windows and its 2015
vintage, going CLI (`gamearch` + `gametls` + ImageMagick + custom
~150-LOC Python) is probably faster and gives you a reproducible
pipeline. The whole asset-extraction phase should fit in **one
working day** once `install.exe` has run.

---

## Sources
- https://moddingwiki.shikadi.net/wiki/Word_Rescue
- https://moddingwiki.shikadi.net/wiki/Word_Rescue_Level_Format
- https://moddingwiki.shikadi.net/wiki/Word_Rescue_Demo_Format
- https://moddingwiki.shikadi.net/wiki/Word_Rescue_Saved_Game_Format
- https://moddingwiki.shikadi.net/wiki/Word_Rescue_Highscore_Format
- https://moddingwiki.shikadi.net/wiki/Category:Word_Rescue
- https://moddingwiki.shikadi.net/wiki/GX_Library
- https://moddingwiki.shikadi.net/wiki/PCX_Format
- https://github.com/Malvineous/camoto-studio
- https://github.com/Malvineous/libgamearchive
- https://github.com/Malvineous/libgamegraphics
- https://github.com/camoto-project/gamegraphicsjs
