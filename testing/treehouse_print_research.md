# Treehouse music print sheet: exact original rendering

Primary-source research, 2026-09-27. No runtime edits. All observations use the pinned original executable/assets and ordinary native input, with read-only RAM snapshots. Scratch: `testing/output/treehouse/research-print/`. This supplements `treehouse_music_completion_research.md` and corrects its classification of calls 5ACD/739E: those are **main executable** functions (`lcall 0,...`), not resident D51 functions.

## Evidence and reproduction

`research-print/render.py` independently decodes original SHAP/SHPL resources and font bytes, then applies the formulas below. Screenshot pixels are only comparison targets, never render inputs. Results compare all 64,000 RGB pixels, including the native pointer:

| Original reference | Score | Different pixels |
|---|---|---:|
|`capture-a/state/long-print.png`|30-note long Lion Theme; Bass instrument|0|
|`capture-short/state/after-20.png`|8-note short Lion Theme; Bassoon instrument|0|
|`capture-compose/state/after-20.png`|My Short Song #1, two entered notes C/E, note-letter labels; Piano instrument|0|

Each capture directory contains its exact action history, original state/RAM/PNG, callback timeline, content/core SHA-256 and restore-source digest in `run.json`. `capture.py`, `capture-short.py`, and `capture-compose.py` reproduce the ordinary-input steps. The independent images are `capture-a-long-print-independent.png`, `capture-short-after-20-independent.png`, and `capture-compose-after-20-independent.png`. Corresponding `*-diff.png` files are all black.

The printed sheet is a transient native screen. Short-sheet captures are visible approximately callbacks 12–27 after confirming Yes; simply waiting 20 frames after a ten-frame press can miss it. `capture-a/state/short-print.png` has already returned to the editor and is **not** a print-sheet reference.

## Sources and address convention

- `research-resources/overlay1-disassembly.txt`: print entry **491E–4AF1**, score **1C73**, note renderer **2A82**, accidentals **267D**, label renderer **2CD5–2D99**, score setup **2DEE**, top tab **4349–4453**.
- `research-resources/main-disassembly.txt`: colored instrument box **5ACD**, print-driver invocation **739E**.
- `disassembly/unpacked.bin`: geometry at image **2F180**, instrument tables at image **2FFE0**, builtin heading font at image **2EAC0**, DS image **321D0**.
- `extracted-v2/manifest.json`: original resource payloads from MODULES/TH.
- `research-print/tables.json`: complete 42-entry instrument palette/relative-shape table, pitch-height tables, accidentals, note letters, rest offsets, extracted from these source bytes.

Rectangles below are `[left,top,right,bottom)` unless explicitly stated. Native rectangle records store `top,left,bottom,right`. `mode=0` short, `mode=1` long.

## Whole-sheet recipe

Overlay **491E** sets shared `+A8A=1` (printing), loads MODULES SHPL **2296**, and draws MODULES SHAP **2297+mode** opaque at `(0,0)`.

| Parameter | Short | Long | Source |
|---|---:|---:|---|
|Score clip rectangle|`(60,80,264,134)`|`(6,68,317,166)`|geometry `+833`, eight bytes per mode|
|Note base X|86|28|geometry `+8`, two bytes per mode|
|Baseline Y|118|106|geometry `+14`, two bytes per mode|
|Notes per row|8|15|score geometry|
|Note spacing|22|19|score geometry|
|Rows|1|2|print call|

Let score rectangle be `(L,T,R,B)`.

1. Instrument box at `(L,T-34)`, width **29**, height **26**. Fill white. Draw its ordinary colored icon centered with transparent index 0. Center is `floor((left+right)/2)-floor(iconWidth/2)` (same for height). Draw a one-pixel black rectangle around the box.
2. Draw song picture **opaque**, at `(L+34,T-32)`. This also retains its original colors.
3. Draw title black at `(L+60,T-26)`, using builtin heading font from image `2EAC0`, length `5F7`. Text is left/top aligned and each glyph advances `width+1`, including the final glyph. Listening title comes from MODULES STRL101 item `songId+1`; composing title uses the current saved title.
4. Draw score within the exact clip rectangle. All score glyphs use their original nonzero SHAP pixels as black masks, ignoring resource palette colors.
5. Main **739E** receives the completed screen for printer handling. Overlay frees palette and restores `+A8A=0` afterward.

**There is no monochrome instrument icon selection in the visible native print sheet.** Native references establish colored instrument/song artwork, black title and score, and colored scroll/background. A physical printer backend may subsequently convert the screen; that output was not captured here.

### Instrument and song artwork selection

Main **5ACD** chooses icon palette from byte table `otherData+17E[instrument]` and relative SHAP from `otherData+1A8[instrument]`. Palette handles DS530A/530C correspond to MODULES **2050/2075**. Complete mapping is in `tables.json`:

- Instruments 0–2: palette2075 relative1–3.
- Instruments 3–24: palette2050 relative1–22.
- Instruments 25–41: palette2075 relative4–20.

Relative shape resolves as `SHPL.firstShape + relative - 1`.

Song picture code is geometry byte `+7F5 + (composing ? 0 : songId+1)`. `palette=2100+20*(code>>4)`, `shape=palette.firstShape+(code&15)-1`. Composing uses MODULES SHAP **2101**, palette **2100** (paper/pencil art).

## Exact score and notation

Overlay **1C73/2A82** uses **large notation glyphs for both print modes**, with one explicit long sharp exception below.

- Fill score rectangle white.
- For each row, staff top is `T+1+53*row`. Draw five one-pixel horizontal lines at offsets0,8,16,24,32.
- Nominal inclusive horizontal endpoints are `L+204` short and `L+311` long, but final score clipping removes the right endpoint: actual short x60…263, long x6…316.
- Left vertical join at xL, from staff top through staff top+32 inclusive.
- Clef MODULES SHAP **2301** at `(L+2,staffTop-2)`, clipped. Long top clef has two pixels removed at y67 by the clip.
- Process exactly `SONG.header[mode]` note pairs. Pair is `(pitchByte,duration)`; `notationFlag=pitchByte>>7`, `pitch=pitchByte&127`. Pitch127 is blank and is skipped completely.

For note index `i`:

```text
row = floor(i / [8,15][mode])
slotX = [86,28][mode] + [22,19][mode]*(i % [8,15][mode])
baseline = [118,106][mode] + 53*row
x = slotX + 6
y = baseline - pitchHeight[notationFlag][pitch]
```

Pitch-height table is geometry `+431`, 17 bytes per row. Printing uses rows0/1, not the small screen rows2/3. Complete extracted values are in `tables.json`.

| Detail | Exact operation |
|---|---|
|Ledger|If `pitch <= 1-notationFlag`, fill `(x-3,y+3,x+14,y+4)` black: 17 pixels|
|Head|SHAP2303 for durations0–2, SHAP2305 for durations3–7, at `(x,y)`|
|Whole note duration0|No stem|
|Up stem, pitch<12|Black rect `(x+9,y-16,x+10,y+2)`|
|Down stem, pitch>=12|Black rect `(x,y+5,x+1,y+23)`|
|Dot, durations1/3/5|SHAP2311 at `(x+11,y+(pitchHeight%8 ? 3 : 0))`|
|Up flag|SHAP2307 at `(x+10,y-15)`|
|Second up flag|SHAP2307 at `(x+10,y-9)`|
|Down flag|SHAP2309 at `(x+1,y+16)`|
|Second down flag|SHAP2309 at `(x+1,y+10)`|
|Flag count|One for durations5/6; two for7; zero otherwise|

Accidental presence is geometry `+475[pitch]`:

- Flat (`notationFlag=1`): large SHAP **2315**, at `(x-5,y-4)` in both modes.
- Short sharp (`notationFlag=0`): large SHAP **2313**, at `(x-6,y-2)`.
- **Long sharp**: small SHAP **2314**, at `(x-5,y-1)` despite its large note head. This special case is explicit in **267D** when printing, advanced mode, and notationFlag0.

### Rests

Durations8–15 draw SHAP `2312+duration` (2320–2327). No head/stem/letter label. Use slotX before the six-pixel note-head offset:

```text
x = slotX + [3,3,3,6,6,5,5,5][duration-8]
y = baseline - 37 + [8,14,14,11,11,12,12,12][duration-8]
```

### Composing note-letter labels

Overlay **2DEE** enables labels only for `composing && mode==0`. Thus short listening and all long print sheets have no note letters. Rest labels are also suppressed by **2CDE**.

The letter is geometry `+486 + 17*notationFlag + pitch`, followed by `b` or `#` when the accidental table is set. Original heading font, black, no outline. Center horizontally in rectangle `(x-3,baseline+9,x+13,baseline+17)`, top align. Total text width includes each glyph's one-pixel trailing advance; textX is `x+5-floor(totalWidth/2)`, textY `baseline+9`.

Native ordinary C/E composing capture independently matches all label pixels and the full sheet. Rest/accidental formulas above are disassembly-derived; the two filled listening captures additionally exercise the original authored song notation, without claiming exhaustive native coverage of every duration/pitch combination.

## Pointer during print

The native sheet can show the ordinary pointer or busy pointer depending on callback. The short listening and composing references use original **TH CURS1**. Long reference uses builtin cursor image **310B0**, 68 bytes. Each record begins signed `(hotspotY,hotspotX)`, then16 little-endian AND words and16 OR words. Origin is pointer position minus hotspot. Foreground is VGA yellow `(255,255,85)` and background black. This distinction explains the initial129-pixel short-frame discrepancy; selecting source CURS1 resolves it to zero.

## Top page tab: exact source recipe

Overlay **4349–4453** starts with hotspot23 record (`52F2+B8`), native rectangle `(top1,left258,bottom22,right281)`. Regular page predicate **3F7B** is true only when table-of-contents state `+9DE==0` and **3F28** says the selection is not the final sentinel page.

For regular pages:

1. Call **442C**, drawing MODULES SHAP **2265** (palette2240 relative25) opaque at **(260,8)**.
2. Select page byte `state+9E + 2*advanced + composing`, add1, format decimal via DS0C73.
3. Inset/offset the hotspot using `(left+7,top+9,right-4,bottom-3)`: final rectangle `(265,10,277,19)`.
4. Draw black text horizontally centered and top aligned using the currently selected ordinary font (4349 itself does not switch fonts).

For contents or final sentinel page:

1. Fill `(258,8,281,14)` black.
2. Mutate that rectangle's top by+1 and bottom by+8; fill `(258,9,281,22)` white.

The result is a one-pixel horizontal black top edge at y8 and a white rectangle below. Contents renderer **463D** explicitly calls4349 at **479C** after laying out its entries. No numbered-page-tab sprite is drawn for the contents or final sentinel page.

`research-print/tabs.py` independently renders and compares the changed tab rectangles. Results: zero pixel differences over `(258,8,281,22)` for all four listening contents pages and the composing contents page; zero over `(260,8,277,19)` for composing page1 and listening short/long page21. Numbered tabs use original **TH FONT1**, glyph advance equal to decoded glyph width, without an extra pixel. Center x is271; draw y10. Source-derived final sentinel behavior was not separately captured here.
