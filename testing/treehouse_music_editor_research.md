# Treehouse DOS 1.1: music composition editor

## Evidence and address conventions

Primary evidence is the executable and data in pinned `The_Treehouse_1991.zip` (SHA256 `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`). Instruction addresses below refer to `output/treehouse/research-resources/overlay1-disassembly.txt` unless marked resident. Original data image is `output/treehouse/disassembly/unpacked.bin`; music geometry starts at image0x2F180 and main DS at0x321D0. This supplements [the earlier music findings](treehouse_music_followup.md) and its [exported tables](treehouse/music-followup-tables.json).

Native evidence under `output/treehouse/research-music-editor/`:

- `edit-capture`: short/long blank books, keyboard notes, vertical pitch drag, palette-rest drag, mode persistence.
- `actions-capture`: marker drag, replacement, sharp/flat default, per-note eraser, erase/random dialogs and outcomes.
- `copy-capture`: copy dialog and copied Lion Theme.
- `last-page-capture`: pages40,41,42 and the terminal The End page.

Sibling `capture-edit.py`, `capture-actions.py`, `capture-copy.py`, `capture-last.py` reproduce these by boot, restoration of an ordinary-input captured state, and only ordinary mouse events. Every run retains a full callback timeline and named PNG/state/RAM snapshots. `run.json` records exact input actions, source-state digest, original hashes, observed65-byte SONG, title, marker, and actual pointer coordinates. No native game RAM was changed.

The observational decoder in the first edit helper was corrected after capture by reading the retained RAM; native frames were not changed. The restored core's segmented pointers carry a consistent image relocation displacement. Decoder derives that displacement from geometry pointer DS:4A54 versus known image0x2F180, then applies it to the state/song pointer. This avoids mistaking stale segment addresses for current song data. Existing capture files still reproduce all actual inputs.

## Books, state and storage

### Four independent selections

Composing and advanced flags are independent. State segment is reached through DS:4A22; its selected song bytes at+9E are indexed `2*advanced+composing`. +A2 is composing; +A4 is advanced. Introductory capacity is8, advanced30. Per-mode chosen duration starts4 (quarter note), stored at geometry+64E/650. The cursor/marker is state+A12.

There are25 listening page records and43 personal page records per mode (table geometry+65C). The last page is special in both books: listening index24, personal index42. Thus there are24 ordinary listening songs and42 normal writable personal pages per mode. Source3F28 tests `selectedIndex == count−1`;3F7B disallows editor operations there.

The terminal page is **The End**, not a random-song page. Native `last-page-capture/state/last-page.png` shows the original The End artwork; drawing428E uses MODULES2207 at(98,27). Source3E47 clears title/icon/staff/page label. It loads the terminal record's own instrument and song and starts playing on entry; keyboard input auditions without recording. Captured record instrument28 is Duck. The title buffer can still contain the previous page's name although it is not displayed.

### SONGS.DAT layout

Resident7948 saves current personal page;7AFB loads it. The filename is literal mainDS:508 `SONGS.DAT`. Switching page, listening/composing, short/long, or leaving saves through4304→resident7948. There is no per-song Save dialog in this path.

The file is8688bytes:

| File offset | Data |
| --- | --- |
| 0x0000 | 86 records of65bytes, indexed `43*advanced+personalIndex` |
| 0x15D6 | 86 titles of36bytes each, same index, CP437 null-terminated |
| 0x21EE | Two trailing bytes |

The native save writes the65-byte current record at65*index, title36bytes at0x15D6+36*index, then two bytes at0x21EE. In current captures those bytes are2400: source7948 writes the local count from its preceding successful36-byte title write. Preserve them when round-tripping a native file rather than assigning them musical meaning. The exported native file is retained inside each capture's `state/reference-v1.pure.zip` as `THETREEH/SONGS.DAT`.

SONG record:

| Byte | Meaning |
| ---: | --- |
| 0 | Short-mode used span |
| 1 | Long-mode used span |
| 2 | Tempo index0..4 |
| 3 | Instrument ID0..41 |
| 4 | Default notation0 sharp /1 flat for newly entered notes |
| 5+2*i | Pitch low7bits0..16; bit7 per-note notation; exact127 means empty |
| 6+2*i | Duration0..15 |

Both record lengths and all30slots exist even for a short book. Read **only header[advanced]** for the current span. Native initialization clears only the active length and pitch bytes, preserving irrelevant other-mode length and duration bytes. Evidence: blank short header `[0,12,3,9,0]`; blank long `[8,0,3,9,0]`. All pitches are127. It is safe for new independent blank records to initialize ignored bytes deterministically, but a format round-trip should preserve imported bytes.

Default fresh blank parameters are tempo3, instrument9 Piano, notation0. Source3FB2 sets these only when called with resetDefaults=true; ordinary Erase calls it with false.

Default title `My Short Song #N` or `My Long Song #N` comes from418C, with1-based visible page N. Title editing is enabled in composing mode by clicking title rect6 `(13,113,26,258)` (also icon rect10); C0F calls the resident text editor with maximum35characters. A custom title counts as a used page even when no notes remain (4127).

## Note entry replaces, never inserts

Keyboard entry18A1..19DA writes directly into current marker slot, storing `pitch | (header[4]<<7)` and selected duration modulo8. It increases active length to `max(oldLength,index+1)`. There is no movement of later entries.

On key release,1B54..1B9E advances only if marker<capacity−1. Helper4AF2 clamps advancement to capacity−1. It does not wrap. Repeated keys after reaching the final slot overwrite that slot.

Loading a page3258 resets marker0, scans its8/30slots, and selects the first exact empty pitch127. If none are empty, marker remains0. This scan is not restricted to stored used span. `actions-capture` confirms dragging marker back to0 and entering D replaces C while span remains2 and second E remains intact.

Physical piano/mouse pitch entry remains the same as listening mode; it records only on regular composing pages when table-of-contents is closed.

## Duration, rest and accidental input

### Clicking duration palette

Source2BD..647 uses existing recovered palette rectangles/offsets.

- Selecting any code0..15 stores `code % 8` as the keyboard-note duration.
- A short click released inside the selected palette rectangle auditions pitch9 with that duration for codes0..7.
- A rest click released inside the palette does not audition and does not enter a rest.
- Changing duration alone does not change any existing score note.
- Rest insertion requires dragging the rest glyph to a score cell. Modern separate buttons can add a convenience action, but must not be described as the original click behavior.

### Dragging a palette glyph

Native source36F..63B calls resident67F2 immediately, without the theater's15-tick hold. Its movement threshold is more than2pixels in either axis. Virtual drag box is24wide×26high. If slot glyph origin is `(durationRect.left+xOffset,durationRect.top+yOffset)`, initial box origin is `(glyphX−8,glyphY−stemHeight)` where stemHeight=[16,10] for intro/advanced.

Preserve the pointer's original offset to this box. Resident full-screen clamp uses2pixel margins. At drop, note anchor is `(boxX+8,boxY+stemHeight)`. Test **this anchor**, not pointer coordinates, against note-cell rectangles. If inside a cell:

1. Compute row offset0 or39 for advanced row1.
2. `heightIndex=clamp(baseY+rowOffset−anchorY,0,maxHeight)`, baseY78/56, maxHeight36/27.
3. Pitch is `verticalPitchMap[advanced][heightIndex]`; maps are37bytes each at geometry+3E7.
4. For rest code8..15 force pitch5 (notation bit still from current header).
5. Replace the destination entry, extend active span if needed, advance marker to min(capacity−1,destination+1).
6. Audition entered note only for code<8.

Normal vertical map0: `[0,1,1,2,2,3,3,4,4,4,5,5,5,6,6,7,7,7,8,8,9,9,10,10,11,11,11,12,12,12,13,13,14,14,15,15,16]`.
Advanced first28 meaningful values: `[0,1,2,2,3,3,4,4,5,5,6,6,7,7,8,9,9,10,11,11,12,12,13,13,14,14,15,16]`.

`edit-capture/state/rest-entry.png` shows original long book with C-quarter then quarter-rest (raw `[5,12]`). Entering E afterward writes a quarter note at next position: rest selection had set keyboard duration4.

### Sharp/flat control

CB1..D1E toggles headerbyte4 and redraws only the control via3A65. It does not rewrite existing note bytes or rerender their notation. New notes get their own high bit from the new default. Existing per-note bit remains when changing pitch by drag. Listening mode additionally remembers this default per song/mode in its parameter table.

`actions-capture/state/toggle-flat.png` preserves both old notes; `new-flat-note.png` has first D raw[2,4], second D-flat raw[129,4].

## Selection marker and existing-note drag

### Marker drag

Native selection is by dragging the **existing green marker**, not by clicking any score cell. Source64A..72D tests only the current marker rectangle, clears the old green marker white, and invokes resident drag with callback3627.

The callback selects the column from pointer X versus marker rectangles' right edges, capped at last column. In advanced mode the pointer Y chooses upper/lower row using current marker cell bottom−5 (the midpoint boundary between staffs). It selects indexcolumn orcolumn+15 and changes marker orientation (2319 upper,2318 lower). Intro marker is2317. On release it redraws green. Geometry is constrained by aggregate marker rectangle (first record in recovered marker array).

`actions-capture/state/marker-to-first.png` changes marker2→0 without altering song notes. Entering a key then replaces slot0. Empty score-cell clicks do nothing.

### Existing note pitch drag

Source817..BEA scans note-cell rectangles when composing. It ignores empty pitch127 and rests duration>=8. On note press, audition its pitch/instrument and draw selected note in dark red. Horizontal pointer motion has no effect on its slot.

3554 finds the first heightIndex whose verticalPitchMap equals the starting pitch. While held, update `heightIndex=clamp(heightIndex−newPointerY+previousPointerY,0,maxHeight)`. When mapped pitch changes, repaint and audition, and48D9 replaces just the low7pitch bits in this same slot. Original notation high bit and duration remain. On release restore black note. There is no hold threshold and no note movement between slots.

`edit-capture/state/pitch-drag.png` changes second note E4 to A9 while keeping its duration4, its index1, and marker3 unchanged.

## Erasing and random generation

### Eraser tool

Rect24 is `(105,77,112,117)`. Handler1450 chooses **CURS2** and sets DS:55E0. Leaving aggregate score rect25 `(26,77,112,300)` automatically restores CURS0 and ordinary tool; eraser does not stay selected when leaving the score. Pressing a score cell in eraser mode sets its pitch127, preserves duration, and does not shift later cells. It scans backward trimming only trailing empty cells from active span. Interior holes remain. Marker does not move. Source878..96A.

`actions-capture/state/erase-first.png`: length2, first pitch127, second pitch129 unchanged, marker2. `eraser-left-score.png` records auto-return after moving outside score.

### Whole-song erase

Composer toolbar at(235,113) is SHAP2253. Ordinary click asks “Erase the whole song?”; a blank unchanged page instead says “Nothing to erase!”. Yes clears all30pitch bytes127 and current length0, retains tempo/instrument/default notation and duration bytes, resets marker0 and default title, saves. SourceF33..104F and3FB2.

Ctrl+click (`resident5C52` reads BIOS keyboard flags0040:0017 and tests bit2) asks “Erase ALL songs?” and reinitializes both books through resident7F65. Do not wire that branch to ordinary click.

### Create a random song

Composer toolbar at(262,113) is SHAP2255. It asks “Create new song?”. Yes forces default notation1 (flat) if currently0, keeps current tempo/instrument/title/marker, and fills all8/30cells:

- Each pitch chosen from `[0,2,5,7,9,12,14]`, uniform original randomInclusive(6).
- Each duration chosen from `[2,3,3,4,4,4,4,4,4,6,6,6,6]`, uniform randomInclusive(12).
- Last note duration is forced0 (whole), but the duration random draw still occurs.
- Every stored pitch has notation high bit128.
- Each note appears with an interruptible6-tick wait; set active span=capacity at end and used flag1.

Source1052..1230; tables geometry+80F and+816. `actions-capture/state/random-song.png` is one ordinary native result, not a requirement to hardcode that random melody.

## Exact composing controls and labels

Palette MODULES2240, opaque shape draws:

| Position | Listening | Composing |
| --- | ---: | ---: |
| (235,113) |2263|2253 Erase|
| (262,113) |2257 Copy|2255 Create random song|
| (289,113) |2259 Print|2259 Print|
| (264,161) |2245|2246|
| (265,140) |2247 short /2248 long|same|
| (98,117) |2251 sharp /2252 flat|same|

Source38D3 and3A65; three composing toolbar assets at235/262/289 match every native asset pixel in `blank-long.png`. Press animation uses next shape (erase2254,random2256,copy2258,print2260); these are not the idle images.

Personal title icon uses song index−1→table entry0: shape2101/palette2100 at(88,6), recovered via4DF2 and geometry+7F5. Title FONT1 is rendered in rect6 `(13,113,26,258)` on white. Page number is1-based index, drawn by4349 in its tab. Composing green marker appears only on regular score pages. Default blank short image is `edit-capture/state/blank-short.png`, long is `blank-long.png`.

Short composing letter labels (2CDE..2D99) appear only for notes, not rests: heading/small FONT handle57C4, centered in rect `(baseY+9,headX−3,baseY+17,headX+13)`, intro baseY78 gives glyph regiony87..94. Label centerX=headX+5. ASCII pitch tables at geometry+486 are sharp `CCDDEFFGGAABCCDDE` and flat `CDDEEFGGAABBCDDEE`,17chars each. Append `#` or `b` if the original accidental table geometry+475 is nonzero. Advanced composer suppresses labels.

## Copying a listening song

Source1233..1345 scans the current mode's43used flags for the first0. No free slot: show “Your song book is full!”. Otherwise ask “Copy song to your book?”. No returns unchanged. Yes:

- Set composing1 and choose that free index.
- Preserve the current65-byte SONG (including both lengths).
- Set used flag1 and title `My ` plus original listening title.
- Redraw composing controls/title/page/score/marker and save to SONGS.DAT.

The observed native `copy-capture/state/copied-lion.png` is `My Lion Theme`, header `[8,30,3,11,1]`, personal index1 (visible page2), same original pitches/durations. This is a clone of current song parameters, not a fresh blank record. The packaged STATUS.DAT has a nonzero first used flag, so this capture selected the second page; see the flags section below. The last special page exists physically but its used flag is preset1, leaving ordinary copy destinations0..41.

## Shared Yes/No dialog rendering

The copy/erase/create dialogs use resident285F and TH group80. They are built from primitives and original artwork, not a single background image. For music screen (resident scene0):

- Black panel `(top16,left5,bottom81,right79)`; white interior `(17,6,80,78)`.
- TH81@(25,8) for boy decoration (girl uses82 at25,1), TH83@(1,33), TH84@(79,33), TH85@(29,81), all SHPL80 transparent.
- Yes face86/87 at(7,40), No face88/89/90 at(43,40), drawn opaque. Resident tables determine their blink order; every12original ticks.
- Green Yes rounded fill `(69,11,78,37)`, red No `(69,47,78,73)`, with black shadows translated(+1,+1). Rounded fill omits four extreme corner pixels (two inset strips), as resident6B21. Colors EGA2 `(0,170,0)` and EGA4 `(170,0,0)`.
- FONT1 black Yes@(16,70), No@(55,70).
- Exact copy message glyph origins: “Copy song to”@(13,19), “your book?”@(17,29). These foreground pixels were independently reconstructed and matched the original.
- Copy native current captured face phase87/89 matches every nontransparent asset pixel. Frame phase matters for a full dialog comparison.
- Clicking the broad left face/button rectangle accepts; right declines. Underlying scene is saved and restored on closure. Music title/score remain visible to the right.

Source2E7B composes the outer decoration;285F composes panel,text/buttons,cycles faces,and restores background. `copy-capture/state/copy-dialog.png`, `actions-capture/state/erase-dialog.png`, and `random-dialog.png` are native dialog references.

## Verification scope

All listed native snapshots and state transitions came from ordinary input. Specific toolbar and dialog artwork positions and copy text foreground were independently checked against native pixels. No claim of a complete whole-screen independent music editor comparison is made by this research alone. Native random seed/call synchronization, generated-song timing, full title-entry keyboard behavior remain separate precision checks.


## Used flags and exact file preservation

Used flags live at shared state+0x48, one byte per physical personal record (86total). They are **not in SONGS.DAT**. Resident7CDD writes STATUS.DAT (literal mainDS:512): first0x8EA bytes from state+48, then2bytes from DS:556C, then0x1A4bytes from DS:5830. Resident7DCB reads the same regions. Thus the first86bytes of STATUS.DAT contain the song-used flags, alongside a much larger status record for other activities.

Original packaged STATUS.DAT is2704bytes. Its song flags0..85 are all0 except flag0=84, flag42=1, flag85=1. Flag0's nonzero value is stale relative to its empty default-title SONG but is still treated as occupied by copy. This explains the native copy going to visible page2. Do not infer that any nonzero flag must equal1, and do not overwrite unrelated STATUS bytes when importing/exporting song state.

Recalculation4127 returns used1 if active SONG length is nonzero, otherwise compares the title with its exact default `My Short/Long Song #N`: a renamed empty song is occupied; an empty default-title song is free. Tempo/instrument changes alone are not part of this test. Note entry, drag entry, random generation and copying explicitly mark used1. Per-note deletion and title edit recompute through4127. Whole-song erase resets flag0 and default title. Terminal flags42/85 are preset1. Without STATUS.DAT, a modern importer can infer normal flags from active length/title and reserve terminal pages, but that is a reconstruction and not byte-identical status preservation.

SONGS.DAT record/title offsets and sizes are directly established by resident7948 (write) and7AFB (read). Keep imported raw65-byte records and all36 title bytes, including bytes after the firstNUL, for a lossless round-trip. The original packaged file already contains the blank records with nonzero irrelevant length/duration bytes and both terminal Duck records: terminal headers `[8,8,4,28,0]`. Its final2bytes are2400. Rebuilding all empty records from zeros cannot produce the same original file, even though the current rendering would be equivalent.

## The End rendering regions

Source42B6 clears three original UI rectangles to EGA15 white:

- rect10 `(6,88,26,110)` title icon;
- rect6 `(13,113,26,258)` title;
- rect27 `(27,88,102,300)` score.

Then428E draws MODULES2207/SHPL2200 at(98,27). Header number helper4349's special branch transforms tab rect23 `(1,258,22,281)` by top+7,bottom−8, giving `(8,258,14,281)`, and fills black. Its second transform is **not an inset**: it changes top+1,bottom+8, leaving x unchanged, then fills white `(9,258,22,281)`. The remaining black line is therefore y8, x258..280. This makes an empty tab instead of a numeric page. The rest of the instrument controls remains drawn; the native terminal page selects Duck from its stored record.


## Visual precision follow-up: dialogs, cursors, eraser, repeat

### Dialog lifecycle and exact text

Resident285F first invokes overlay1:231D(1) through the overlay trap at28A2 (`CD 3F 01 1D 23`). This calls509F(1,0) to stop the musician animation and restores saved musician background handle DS5294 through resident82B2. **Remove the musician before saving/drawing the dialog**; the transparent head, fingers and feet are drawn on that restored scene. Merely drawing panel2E7B over the idle musician leaves hundreds of wrong pixels above and below the panel. On dismissal, resident2E68 invokes overlay1:3B92 to redraw the current instrument at(40,92).

Full face-image comparisons against the native erase/random captures select SHAP87 at(7,40) and SHAP89 at(43,40), both with zero different pixels over their entire asset rectangles. The original face sequences at image2E8F0+188 are `[0,1]` for Yes and `[0,1,2,1]` for No: add86/88 respectively; counter advances every12ticks. Dialog starts counter0 with its timer reset, so the first update is immediate.

Verified black FONT1 text origins (x,y), using the full glyph masks:

| Dialog | First line | Origin | Second line | Origin |
| --- | --- | --- | --- | --- |
| Copy | Copy song to | 13,19 | your book? | 17,29 |
| Erase | Erase the | 20,19 | whole song? | 14,29 |
| Random | Create new | 15,19 | song? | 29,29 |

### Cursor resource, color and timing

The builtin ordinary cursor is the68-byte record at unpacked image310B0; hotspot words areFFFF,FFFF. Original TH archive has CURS1..4 only; requested CURS0 resolves to this builtin. Eraser uses original TH CURS2 unchanged, through overlay1:1450 and residentD51:8806. Resident15B89..15B95 proves the first signed word is **hotspot Y**, the second **hotspot X**. For CURS2 these are(3,8), so screen origin is(pointerX−8,pointerY−3). AND/OR masks are sixteen little-endian words each; do not interpret them as big-endian.

Eraser input invokes resident7308 with(12,12,128). VGA mode5 returns `(paletteLookup(128)<<4)+12`, observed DS2060=124. Native eraser-tool foreground is exactly(243,24,0), matching music palette12; all27 cursor foreground pixels and28 black pixels match the CURS2 mask. This is not the yellow standard cursor.

On leaving the score, source installs CURS0 **before** setting DS2060=14. The installation immediately redraws the ordinary cursor using its previous red color, then the color variable changes without a redraw. Accordingly the native eraser-left-score snapshot has DS2060=14 but its displayed ordinary cursor remains red: all54 foreground pixels are(243,24,0), all41 black pixels match; pointer(150,126), origin(151,127). The next cursor redraw should use global palette14 (standard EGA yellow), not music palette14. This frame-sensitive stale displayed color explains the remaining54-pixel mismatch; treating the new DS variable as an immediate redraw is inaccurate.

### Eraser tray and repeat playback

The saved background tray rectangle used by DS581E is original image2F180+104: `(top105,left77,bottom112,right117)`. Entering eraser restores that saved region. Leaving redraws group52C8 relative SHAP8 at(x77,y105), as3B60 reads original geometry offsetsC0/C2. Do not erase a wider tray area.

Shared state+A6 is repeat playback. At end-of-song overlay1:3231, nonzero jumps back to2F52 to restart; zero clears active playback state+A92. Its UI uses shape2243/2244. This is independent of song composition mode and note duration.

Reproduction: scratch `research-music-editor/refine.py` directly decodes pinned source resources, checks the native FONT/face/cursor masks, and prints the source rectangle bytes. The earlier exploratory big-endian cursor diagnostic in that script intentionally demonstrates a mismatch; the final little-endian section contains the correct match.

An additional ordinary-input check restored the eraser-left-score save and moved the pointer one pixel right. `cursor-return-capture/state/after-motion.png` has pointer(151,126), and all54 builtin cursor foreground pixels are standard yellow `(255,255,85)`. Thus the stale-red-to-yellow transition is directly observed, not only inferred. The immediate one-frame `before-motion` restored screenshot has a transient palette restoration mismatch and is not a valid visual reference; use the original actions-capture image for the pre-motion frame.
