# WR1 HUD, books, and word/picture rendering

Static investigation of the supplied WR1.EXE, SHA256 `b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`. All addresses below are **file offsets**, except explicitly labelled DS fields. MZ image starts at file `0x2a00`; initialized DS bytes start at `0x24f50` (load-relative segment `0x2255`). Runtime DS must include the process load segment. No gameplay files were changed.

## Actionable results

* HUD text uses a BIOS/ROM **8×8 bitmap font**, not FONT.WR. Read the live far pointer `DS:43b0/43b2` to extract the emulator's actual glyph bytes.
* Score digits are black (palette index 0) on background index 3, at `x = 93 - 4*len(decimal_score)`, `y = 19`. Every glyph cell is opaque, 8×8; there is no larger clear operation in the book reward routine.
* Book `i` stamps attr `0x82+i` into the 8px collision grid at `(2*bookTileX, 2*bookTileY)`. It displays atlas tile `(304,176,16,16)`.
* Ordinary book: +5. **Final book: +500 instead of +5**, not +505. Restore the underlying saved background tile on collection.
* Word cards and pictures use the question location's top-left anchor; they are not centered over it. Pictures preserve their opaque black/white backgrounds.

## HUD font and score

Setup at `0x9b68–0x9b73` calls `d86:36` with arguments `(3,0)`. Its implementation, `0x10296`, selects font 3 and nontransparent mode. Font 3 has height 8 (`0x102de`). It obtains the font pointer with `INT 10h`, AX=1130h, BH=3 (`0x102f2–0x10305`), or uses `F000:FA6E` in the fallback branches at `0x10323–0x1032f`. The chosen pointer is stored in `DS:43b0` offset and `DS:43b2` segment. Glyph lookup is `font + unsigned_character_code*8`, not a digit-only atlas.

The GX text routine `0x103d3` copies the current font pointer/height and text colors into locals at `0x1042a–0x10463`. Width and cursor advance are always 8 per character (`0x1048e`, `0x10864`). The EGA draw callback `0x107b2` uses foreground color for glyph 1 bits and background color for glyph 0 bits (`0x107e8–0x10817`). Only transparent mode 1 skips zero bits. The packed-pixel callback makes the same rule and MSB-first horizontal bit order especially clear at `0x108b6–0x108cc`.

Color setter `c9d:345` (`0xf715`) writes `DS:4487`; background setter `c9d:2f8` (`0xf6c8`) writes `DS:4489`. These are copied into text locals `[bp-0x10]` and `[bp-0x12]`. Thus the argument 3 to `c9d:2f8` is a background color, **not the font number**; these two different calls both happen to receive 3 in setup.

Book reward HUD update at `0xaab3–0xab16`:

```python
set_page(5)
set_background_color(3)
set_foreground_color(0)
text = decimal_signed_32bit(score)  # conversion radix argument 10
draw_text(text, x=93 - 4*len(text), y=19)
```

The wrapper at `0xa333` calls the GX cursor setter and text renderer. The formula comes directly from `0xab05–0xab11`: `33 - 4*n + 60`. Therefore the painted rectangle is inclusive `[93-4*n, 19, 93+4*n-1, 26]`. It paints all pixels inside each character cell. The book routine does not first erase an independently sized score panel. Normal positive score growth makes the new centered cell rectangle cover the old one; resetting the score depends on the surrounding HUD/page reset flow.

The same score formula is used during level setup at `0x6ce9–0x6d48` and after other reward paths. The 32-bit score is `DS:0186/0188`.

Exact ROM raster recommendation: obtain the live font pointer and read at least 128×8 bytes; use `bytes[ASCII*8:ASCII*8+8]`, with bit7 at the left of each row. The binary selects the font but does not embed this BIOS font itself, so substituting a modern font would not reproduce its raster exactly. Palette colors should use the current game palette, not colors sampled from a differently loaded PCX.

## FONT.WR is the mystery-letter atlas

The resource is loaded at `0x9b85–0x9b93` into image structure `DS:9513`; `0x9b98–0x9ba7` derives a mask/image structure at `DS:ae3e`. The extracted `assets/extracted/wr1_1_png/FONT.WR.png` is 144×48 and contains 26 uppercase yellow letters, arranged in nine 16×16 columns.

The mystery-letter assembly at `0x7487–0x754f` reads a **lowercase** letter from the selected word string, subtracts ASCII `'a'` (97), and uses:

```python
glyph = ord(letter) - ord('a')
source = Rect(16*(glyph % 9), 16*(glyph // 9), 16, 16)
```

This is fixed-cell extraction, no proportional width/advance metadata. The code first overlays the derived image with operation1, then the original image with operation2 onto a saved-background staging tile (`0x74d2–0x754f`). This is the masked mystery-letter drawing path. FONT.WR is not used to draw score digits or lowercase word labels.

## Book placement and removal

`DS:0180` is the level's book count. Book tile coordinates are 16px grid arrays `DS:9844 + 2*i` (X) and `DS:99b2 + 2*i` (Y). During level setup, the original preserves source atlas X/Y from the underlying background into `DS:ab1e + 2*i` and `DS:ac4a + 2*i` (`0x6d78–0x6dc3`).

Placement at `0x6e6a–0x6ee4` writes source atlas X=304 and Y=176 into the background tables, then writes attr `0x82+i` at the doubled tile coordinate. The attr column pointer is based at `DS:9afa`; the background source-coordinate column-pointer tables are `DS:8b13` and `DS:8ccf`. The raw disk map's attrs therefore need not already contain book markers.

The shared pickup helper starts at `0xa34e`. It receives `(y,x)` in stack argument order, reads the attr, subtracts `0x7b`, and **clears that one attr byte to `0x20` immediately** (`0xa384–0xa392`). Attrs `0x7b..0x81` are the seven mystery letters. At `0xa605`, subtracting another 7 gives `book_index = attr-0x82`; indices below `DS:0180` take the book branch `0xa7c5`. Higher indices enter the separate slime-bucket branch.

Book branch `0xa7c5–0xa81f` restores the saved background source X and Y at the book's 16px tile. If a backdrop is active (`DS:af8a != 0`) it skips immediate page2 repair and proceeds to the count update. Without a backdrop, it repairs page2: copies the saved 16×16 atlas tile from page3 when saved X is nonnegative; otherwise copies the blank staging tile at page2 `(128,0)..(143,15)`. This is background restoration, not simply making a book sprite invisible. The next renderer then uses the restored background tables.

At `0xa93e` increment `DS:015c` (books collected). At 20 books, `0xa94d–0xa9d3` updates a bottom-HUD word presentation (colors11 and14 at y188); this is separate from the all-books bonus.

At `0xa9d8`, compare collected count with total book count. Equality selects `0xa9e4`: reward flag DI=0; add `DS:015a` (500) to score. The normal +5 block at `0xaa86` only runs when DI is nonzero, so the final book replaces the regular award. Ordinary reward reads `DS:0152`, initialized 5. Both branches establish a floating reward graphic for 20 render-time units at attr coordinate `(x,y-2)` (`DS:014c/014e/0150`), but full floating-graphic animation was not traced in this pass.

```python
def collect_book(x, y):
    i = attr[x][y] - 0x82
    attr[x][y] = 0x20
    background_source_x[book_x[i]][book_y[i]] = saved_source_x[i]
    background_source_y[book_x[i]][book_y[i]] = saved_source_y[i]
    books_collected += 1
    reward = 500 if books_collected == book_count else 5
    score += reward
    update_score_on_page_5()
```

The helper also handles pickup sound, immediate cached-page repair, the 20-book presentation, and reward graphics described above. This pseudocode isolates durable collision/background/score state.

## Contact scan distinction

Books are collected by the same main contact function `0xc1aa` as questions, not by the entity update at `0x50e8`. The scan is row-major over rows `max(gy-5,0)..gy`, columns `max(gx-1,0)..gx+3`, bounded below map width/height minus one. Pickup dispatch additionally requires scan X >= gx and attr > `0x7a` (`0xc52c–0xc544`, `0xc6ab–0xc6c3`).

**A pickup does not stop this scan.** After helper return, execution reaches the column increment at `0xc54c` or `0xc6cb`. Multiple pickups can be processed in one update. A qualifying question/source/target encounter instead branches to the function exit at `0xc6f3`; this can stop later pickup checks. Preserve scan ordering when combining the two interactions.

## Word and picture rendering supplement

Renderer camera offsets at `0xb368–0xb387` are `16-8*cameraX` and `32-8*cameraY`. Both the active source word (`0xb643–0xb655`) and pictures (`0xb74c–0xb75e`) add those offsets to the slot's stored pixel X/Y (`DS:9e74`/`DS:a906`). Therefore their destination top-left is the same question location anchor:

```python
dest = (slot_pixel_x + 16 - 8*camera_x,
        slot_pixel_y + 32 - 8*camera_y)
```

Pictures are loaded into page4 by `0x6254`. A second animation image named `word + '2.WR1'` is attempted at `0x62f9`; failure copies the first picture into the second image's region (`0x6302–0x6337`). Render uses the slot's animation index `DS:41b0 + 2*slot` to select one of these rows. They are 24×24 source rectangles. Final rendering uses ordinary page-to-page rectangle copy `10ed:8` at `0xb89d`, the same primitive used for unmasked background rectangle copies, **not** the derived-mask two-pass overlay used for FONT.WR. Preserve the extracted picture's white and black pixels; do not treat either as transparent. No black/white/magenta remap is present in this render path; verify global palette selection independently if an extracted PNG uses the wrong palette.

Word cards are pre-rendered into page4 at `0x633c–0x6417`, with **72×18** source rectangles from initialized DS tables `0273/0281/029d/028f`. Their atlas positions are `(168,0),(240,0),(168,18),(240,18),(168,36),(240,36),(168,54)`. Before this loop foreground=0 and text background=15 (`0x61f4–0x6200`). The rectangle/border is drawn at `0x6352–0x63c8`; text appears at card X + `32 - 4*word_length`, card Y+4, using the same BIOS font. The render clipping calculations assume nominal64×16 for the word despite the stored72×18 source bounds; reproduce the interior source dimensions first and verify edge-clipping separately.

Further decoding of rectangle function `c6e:94` (`0xf174`) confirms mode3 means outline plus fill: mode2 skips the outline (`0xf1df`), then the bit2 test controls filling after outline (`0xf299`). The card sets solid line pattern -1 and width1 (`0x6345–0x634d`; setter at `0xf625`). Its raster is a black 1px outer border around a white 72×18 rectangle, plus a black horizontal line at relative y16 and a black vertical line at relative x1 (`0x637b–0x63c8`). Thus left and bottom edges are 2px thick. Card text remains black on white, opaque.

## Other dynamic HUD fields

**Current word:** `0xc63b–0xc6a4` ultimately selects foreground15/background3 and draws at `(91-4*n,5)`, where n is word length. An initial foreground12 assignment is overwritten by15 before rendering; do not use12. Resolving a picture target (success or failure) clears the inclusive rectangle `(60,4)..(126,14)` on page5 at `0xc21d–0xc23a`. Fill state was set to solid color3 at function entry `0xc1b2–0xc1bc`; rectangle mode2 means fill only.

**Matched slots across the top:** these contain the successful word's **picture**, not its text. `0xc311–0xc363` copies the 24×24 first picture to `(144+23*old_matched_count,5)` on page5. Adjacent copies overlap one pixel. `DS:b8cd[wordIndex]` stores that display order (`0xc376`). The renderer's picture animation update recopies the selected picture frame to the same destination at `0xab71–0xac19`. When enabled (`DS:01bf != 0`), each identity's counter `DS:41a2+2*i` increments per renderer call and toggles its two-frame index `DS:41b0+2*i` after counter>7 (`0xab2d–0xab6d`). Global animation enable/startup phases should come from native state rather than assuming all frames start together.

**Mystery word along the bottom:** `0x75cf–0x75dd` sets `DS:6632 = 160 - 4*word_length`. When difficulty `DS:017e != 2`, setup draws the whole lowercase word at `(DS:6632,188)`, foreground11, font3, transparent mode1 (`0x75e0–0x762b`). Transparent means preserving the chrome background for zero glyph bits. Acquiring letters copies the word, truncates it at `DS:9491` (the acquired prefix length), and paints that prefix at the same anchor in foreground14/transparent mode1 (`0xa5c1–0xa5f0`). It restores opaque mode afterward. Reaching20 collected books also paints the whole word11 then acquired prefix14 (`0xa94d–0xa9d3`), independent of the initial difficulty2 hiding branch.

## Evidence and remaining gaps

Aligned evidence is saved under `testing/output/wr1_hud_books_*.txt`, especially `10260`, `103d3`, `10521`, `107b2`, `10889`, `6e6a`, `a34e`, `a605`, `a93e`, `aa86`, `61b0`, `7410`, and `b600`. Some broad scratch ranges begin midinstruction; use the exact named instruction offsets in this report rather than trusting their first lines. Capstone's `cwde`/`cdq` labels in these 16bit dumps mean CBW/CWD.

High-confidence results are the font source/metrics, opaque score colors/anchor, book marker arithmetic, background-state restoration, reward replacement, scan continuation, picture anchors, ordinary picture copy, card border rules, and other HUD anchors/colors. Remaining runtime checks: current BIOS font bytes/palette; cached page2 behavior on unusual backdrop changes; clipping at viewport edges; the 20-book presentation's meaning; and floating reward graphics. The parent has subsequently extracted the live font and confirmed all64pixels of the initial score glyph against the native capture. These findings do not require guessing a modern font or empirically tuning the core book/contact constants.
