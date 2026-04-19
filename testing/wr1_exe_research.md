# WR1.EXE Engine Internals — Research Report

Date: 2026-04-19
Target: `D:\Downloads\Word Rescue (1992)(Apogee Software Ltd)\WORD\WR1.EXE`
176,958 bytes. MZ image, Borland Turbo-C 1988. Data segment at file offset
`0x24f50` (load segment `0x2255`); image data starts at `0x2a00`. `strings`
confirm third-party libs: **Genus Microprogramming GX Kernel/Graphics/Text
2.0 + PCX Toolkit 5.00** (Christopher A. Howard) and **WORX TOOLKIT 2.01(M)
1993 Mystic Software**.

Methodology: capstone (`CS_MODE_16`) on raw file bytes; code segments map
1:1 with file offsets. All addresses are **file offsets** unless marked
`DS+…` (data-segment offset) or `seg:ofs` (far pointer).

---

## 1. Tile-index → atlas-cell lookup for BACK3

**CONFIRMED. There is no static remap table.** The engine uses a fixed
mod-20/div-20 formula, identical to your current Godot code. Your observed
91.88% boost comes from **runtime BG-buffer overwrites at level-load**, not
from a persistent lookup.

### 1a. BG-layer algorithm

Level-loader inner loop at `0x6907`. For each RLE-decoded BG byte `al`:

```
ax = al (zero-extended)         ; tile index 0..255
bx = 20
(ax, dx) = idiv(ax, bx)         ; 0x6956 idiv bx (bx=0x14)
src_x_px  = dx << 4              ; 0x695c shl cl,4
src_y_px  = ax << 4              ; 0x6982 shl cl,4
bg_x_table[col][row] = src_x_px ; 0x6971 mov es:[bx], dx
bg_y_table[col][row] = src_y_px ; 0x6997 mov es:[bx], ax
```

So **col_px = (idx % 20) × 16, row_px = (idx / 20) × 16** — identical to
your code. Sentinel tile `0xff` stores `0xffe0/0xffe0` (transparent).

`bg_x_table` row-pointer array: logical `DS-0x74ed`. `bg_y_table`:
`DS-0x7331`. Both are BSS (GX-Kernel malloc'd at startup).

### 1b. Runtime overwrites (the "remap")

Immediately after BG/ATTR decode, the loader overwrites selected
`(bg_x, bg_y)` cells with sprite pixel coords drawn from the **same**
`back?.wr` tileset:

| Code site | Entity | `bg_x` write | `bg_y` write | Back3 tile |
|---|---|---|---|---|
| `0x6e6a–0x6eaf` | Books (count `[DS+0x180]`) | `0x0130` (304) | `0x00b0` (176) | col 19, row 11 (idx 239) |
| `0x6eea–0x6f2f` | Letters (count 7) | `0x0120` (288) | `0x00b0` (176) | col 18, row 11 (idx 238) |

Letter writes also set the attr byte to `0x82 + letter_slot` (`0x6f3a:
add al, 0x82`) — that's why attr has values 0x82..0x88.

Gruzzles, slime buckets, drips, and question blocks do **not** overwrite
the BG tables; they are sprite-drawn every frame on top of the buffered
map. I did not find BG-table writes tied to those entity lists in the
loader.

**Practical fix:** after RLE-decoding your BG layer, walk `books[]` and
`letters[]` and replace each cell with tile indices 239 and 238
respectively. This should recover most of the remaining ~8%.

---

## 2. Animated-tile behavior

**Partially confirmed.** The level-header `animations` list is stored with
**tile-grid units, not pixels**. At `0x6895–0x68ba` the loader stores:

- `anim_x[i]` at `DS-0x528a` (u16, column in level tile units)
- `anim_y[i]` at `DS-0x5140` (u16, row in level tile units)

Max 100 entries (`cmp si, 0x64`).

### Render path (`0xbc63–0xbd6f`)

```
for i in 0..animCount:
    col = anim_x[i]; row = anim_y[i]
    src_x = bg_x_table[col][row]
    src_y = bg_y_table[col][row]
    lcall 0x10ed:0x0008 with rect (src_x, src_y, src_x+0x0f, src_y+0x0f)
         and dst (col*16+0x10-cam_x, row*16+0x20-cam_y)
```

**Caveat.** The render loop as disassembled *redraws the base tile* with
no frame counter. I scanned every `les bx,[bx-0x74ed]`/`[bx-0x7331]` site
(`0x6971, 0x6997, 0x6e8a, 0x6eaf, 0xa63f, 0xa66c, 0xa7ef, 0xa80a`); only
level-load and pickup-removal write these tables — **no animation cycling
rewrites**.

**Unknown:** whether the 4-frame cycle happens inside `lcall 0x10ed:0x0008`
(GX clipped blit at file offset `0x138d8`) via one of the 8 args
(3rd-from-last arg is `3` in this call-site; GX reads `es:di + 0x16/0x17/
0x18` around `0x13939–0x13946`). Without runtime trace I can't confirm.
Level 1 has `animCount == 0`, so this does not affect your current score;
impact only appears on levels with animated tiles.

**Recommended implementation:** treat `animations` as `List[(col_tile,
row_tile)]` in **level tile units** (not pixels), and cycle through the 4
consecutive tile indices (the level cell's original index + 0, +1, +2, +3)
at some fixed rate. The ModdingWiki constraint "tiles must be in the same
row of the tileset" is consistent with this since you'd just bump
`src_x += 16` per frame.

---

## 3. Attribute-layer foreground rendering

**CONFIRMED. No foreground tileset; the attr layer is collision + marker
only.** Exhaustive scan of every `cmp byte ptr es:[bx], imm` against attr
values `0x70–0x8f` found only these three:

| Compare | Sites | Meaning |
|---|---|---|
| `== 0x73` | `0x37d8, 0x398f, 0x3ab7, 0x3ad9, 0x565f, 0x5708` | solid wall |
| `== 0x74` | `0x37ec, 0x3874, 0x388c, 0x38a6, 0x3a56, 0x3a70, 0x56bd` | one-way platform |
| `< 7` | `0x6c18, 0xb8df` | question-block letter slot (0..6) |

No other attr value (`0x20`, `0xfd`, `0x82..0x88`) is ever inspected.
`0x82..0x88` are written by letter-overwrite code (§1b) as pickup markers;
they are not rendered.

Asset-string scan confirms: the only image files the binary references are
`back%d.wr`, `drop%d.wr`, `chars.wr`, `benny1.wr`, `benny2.wr`, `slime.wr`,
`font.wr`, `static.wr`, `key.wr`, `help.wr`, `menu.wr`, `wr1.%d` (cutscene
PCXs). **No `fore*.wr`, `attr*.wr`, or `mask*.wr` exists.**

### Where do textured ground stones come from?

From the BG layer alone. BACK3.WR is 320×200 = 20×12 tiles. Texture
detail lives there. If your render looks less textured than DOSBox,
check:

1. Book/letter overwrites (§1b) — you may be missing visually-distinctive
   overlays at those positions.
2. `bgColour` (`[DS+0x9af8]`, 0..15): at `0x6f86` if `< 0x10` a call to
   `lcall 0x1469:0x0004` passes `(bgColour, 2)` — likely a backdrop-tint
   or border-fill step, not FG tiles. Worth testing by toggling off in
   your renderer to see if it hides detail you're matching incorrectly.

---

## 4. Player character selection & rendering

### 4a. Selection: binary boy/girl flag

**CONFIRMED.** Selection is a u16 `gender` at **`DS+0x18e`**, matching the
save-file's offset-2 word (wiki: 0=male, 1=female). Character-select
function starts near `0x8fe8`:

1. Loads `chars.wr`; initial `[DS+0x18e] = 1` (default girl) at
   `0x8ffe: c7 06 8e 01 01 00`.
2. Polls scan-code via `lcall 0x1a3:0x036a`:
   - `0xCD` (→): `[0x18e] = 0` (boy), `0x9082`.
   - `0xCB` (←): `[0x18e] = 1` (girl), `0x908e`.
   - `0x0D` (Enter): exit.
   - `0x51` (Q): quit handler.
3. Redraws two cursors at `(0x7b − gender*0x52, 0x58)` and
   `(0x9c − gender*0x52, 0x81)` (two indicators moving together, 82 px
   apart).

Only one variable. **Default is gender=1 (girl).**

### 4b. CHARS.WR four rows

Sprites are 24×32 (from sprite-metadata tables at `DS+0x884` for gender 0
and `DS+0xac0` for gender 1, 28 × 20-byte records each). Metadata I
confirmed references y=40 (row 1 of menu-screen sprite; the menu cutout is
NOT aligned with CHARS.WR's rows).

In CHARS.WR itself: rows 0–1 are the two menu-render characters' standing
poses. Rows 2–3 likely hold alternate-state animation frames (duck, hurt,
climb). **I did not locate sprite-metadata records referencing y ≥ 64** in
the first 28 records of each table. If the bottom rows are used, it's via
a code path I didn't map (slime hit? celebration?).

Your reference recording's "brown-haired green-dress" girl is **almost
certainly the same `gender=1` sprite** with an **EGA palette remap** applied
by the backdrop/tileset PCX load. GX's PCX loader rewrites EGA palette
registers (`out 0x03c0`) from each PCX's embedded palette. Compare the
palette embedded in `BACK3.WR` (or the relevant `DROP*.WR`) with your
extracted `CHARS.WR` palette — if they diverge, the level is recoloring the
character via shared palette index reassignment.

### 4c. Player origin

**CONFIRMED.** Player sprite top-left is drawn at `(start.x_px,
start.y_px − 32)` (code at `0xb9f3–0xb9fa`):

```
di = [DS+0x662e]            ; start X pixels
ax = [DS+0x6630] + 0xffe0   ; start Y pixels − 32
lcall 0x13ae:0x0002 ...(di, ax)...
```

For a 24×32 sprite with top-left at `(x, y−32)`, the sprite's bottom-center
is `(x+12, y)`. Level-header conversion (`0x65ca`):
`start.x_world_px = (start_tile_x − cam_tile_x)*8 + 16`,
`start.y_world_px = (start_tile_y − cam_tile_y)*8 + 40`.
Start coords are in **8×8 tile units**, not 16×16. Viewport offset
`(+16, +40)` px into the playfield.

Your `(+0, +24)` hack is close to 32 but off by 8 (likely Godot's default
centered anchor vs top-left). Correct: **top-left at `(start.x_px,
start.y_px − 32)`** or centered-anchor at `(start.x_px + 12, start.y_px −
16)`.

---

## 5. Start / exit door rendering

**Inconclusive.** I found **no dedicated door-sprite blit at the
player-start position**. The wiki's phrasing about "bottom-middle of where
the door image is drawn" is about the **exit** door, not entry. The start
position is where the *player sprite* is placed.

Likely explanations for what you're observing, in order of plausibility:

1. **Door art is part of the BG tileset.** Level designers place
   door-frame 16×16 tiles at and around player-start positions. Check
   BACK3.WR for door-looking tiles (likely in the first few rows — row
   0 or 1) and inspect `level_01.json` BG bytes at
   `(player_start_x, player_start_y)` and neighbors. This is the most
   likely answer.
2. **Exit door only** is sprite-drawn (using exit coords). The exit
   field is read later in the level header (past where I traced). If it's
   a sprite, it comes from `STATIC.WR` which is loaded once at startup
   (refs at `0x9bb0` and `0x9fca`).
3. **STATIC.WR contains a door/frame graphic** overlaid on the player
   spawn via some code I didn't map.

**I did not find** a "draw door sprite at every player_start" call. The
only player-start sprite blit I located is the player character itself
(§4c). If the DOSBox reference shows a door at spawn, it is probably (1).

---

## Appendix A: Key DS offsets (base = file `0x24f50`)

| Offset | Meaning |
|---|---|
| `+0x0a2` | u16[14] level sequence `3,0,9,11,13,14,1,4,7,10,8,2,5,12,6` |
| `+0x0be` | Level-name string-pointer table (30 far ptrs, `Level N`/name pairs) |
| `+0x150` | Score table u16[6]: `0, 5, 10, 20, 100, 500` |
| `+0x18e` | **`gender`** (0=boy, 1=girl; default 1) |
| `+0x20b` | Current level number |
| `+0x20f` | Tileset index (→ `back%d.wr`) |
| `+0x180/0x182` | bookCount / letterCount |
| `+0x235/0x237` | gruzzleCount |
| `+0x528a / +0x5140` | `anim_x[] / anim_y[]` (tile-grid units) |
| `+0x662e / +0x6630` | player start X / Y (pixels, pre-converted) |
| `+0x664a` | player sprite-frame image buffer (BSS, 128 B/frame) |
| `+0x8480/0x8482` | camera tile X/Y |
| `+0x884 / +0xac0` | Menu char sprite metadata, gender 0 / 1 (20-byte records) |
| `+0x8b13 / +0x8ccf / +0x9cfa` | `bg_x / bg_y / attr` row-pointer arrays (BSS) |
| `+0x9778 / +0x9792` | mapWidth<<1 / mapHeight<<1 (internal 8×8 grid) |
| `+0x9af8` | bgColour EGA index |
| `+0xa928` | animCount |
| `+0xaf8a` | backdrop index (→ `drop%d.wr`) |

## Appendix B: function entry points

| Offset | Role |
|---|---|
| `0x6433` | Level-file open (`"wr1.s" + itoa(level)`) |
| `0x6ad1` | Tileset open (`"back" + itoa(tileset) + ".wr"`) |
| `0x6b69` | Backdrop open (`"drop" + itoa(backdrop) + ".wr"`) |
| `0x68e4–0x6ac5` | BG RLE decode → pre-computed `(col*16,row*16)` buffers |
| `0x6a38–0x6a85` | ATTR RLE decode (raw bytes) |
| `0x6e6a–0x6f63` | Book + letter BG-layer overwrites |
| `0x8fe8`+ | Character-select (gender) |
| `0x91a0` | chars.wr menu sprite render (gender-dependent) |
| `0xa399–0xa60c` | Mystery-word letter rendering |
| `0xb8d0–0xb9e3` | Question-block rendering (attr < 7) |
| `0xb9f3`+ | Player sprite blit at `(start.x, start.y−32)` |
| `0xbc63–0xbd6f` | Animated-tile render |
| GX Graphics API | `0x1078:0x000a` load_image, `0x1280:0x0004` blit_region, `0x10ed:0x0008` clipped_blit (file `0x138d8`), `0x13ae:0x0002` sprite_to_buffer |
| RTL | `0x1f55:0x0003` fread, `0x1f85:0x008a` sprintf_d, `0x1faa:0x000d` strcpy, `0x1fa1:0x000e` strcat, `0x1eb1:0x003d` open, `0x2155:0x0020` random, `0x1a3:0x036a` read_scancode |

---

## Confidence summary

| Q | Status | Confidence |
|---|---|---|
| 1. BG tile → atlas | Algorithm + overwrite mechanism fully traced | High |
| 2. Animations | Coords are tile units; frame-cycling partially unresolved | Medium |
| 3. Attr layer ≠ FG render | No FG tileset, only 3 attr-value compares exist | High |
| 4a. Gender = binary flag, default girl | `[DS+0x18e]`, handler fully traced | High |
| 4b. CHARS.WR 4-row purpose | Rows 0–1 used by menu; rows 2–3 unexplained | Medium |
| 4c. Player origin = top-left at `(start.x, start.y−32)` | Fully traced | High |
| 5. Start-door sprite | Not found; likely BG-tile art | Low |

## Recommendations

1. Apply §1b overwrites (book→idx 239, letter→idx 238) in your level
   loader before rendering BG — should close most of the ~8% gap.
2. Verify `animCount>0` levels in smoke test; if affected, implement the
   4-frame cycle from §2 using **tile-grid coords** (not pixel coords).
3. Fix player placement to top-left at `(start.x_px, start.y_px − 32)`.
4. Default `gender = 1` (girl) if simulating a fresh save; the reference
   recording's "brown-haired" appearance is probably EGA-palette remap
   from the backdrop PCX, not a different character.
5. For the start-door, inspect `BACK3.WR` for door-frame 16×16 tiles and
   check the BG bytes at level_01's `player_start` tile and neighbors.
