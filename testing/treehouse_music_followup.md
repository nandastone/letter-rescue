# Treehouse music follow-up: instrument families and composition

Primary-source reverse engineering, 2026-09-27. All image offsets below refer to the unpacked pinned DOS executable documented in [the executable research](treehouse_executable_research.md); instruction addresses refer to overlay 1 in `testing/output/treehouse/research-resources/overlay1-disassembly.txt`. No secondary web descriptions informed these findings.

Machine-readable recovered tables: [music-followup-tables.json](treehouse/music-followup-tables.json). Extraction recipe: `testing/output/treehouse/research-music-followup/export.py`.

## Native evidence and entry paths

Ordinary input captures restore the previously recorded native `demo-piano/state/piano.state`. No guest RAM is modified. Reusable capture helper is `research-music-followup/capture.py`; every evidence directory has `run.json` with exact ordinary mouse inputs, original state digest, content digest and capture-core digest.

| Piano control | Native point | Original hotspot / rectangle | Result |
|---|---|---|---|
| Rainbow | (25,124) | 4 / (115,12,136,39) | Instrument-family selector |
| Green book/pencil | (275,169) | 2 / (161,264,178,305) | Listening/composing toggle |
| One/two staffs | (274,149) | 9 / (140,265,157,304) | Introductory/advanced toggle |
| Bucket | (31,157) | 22 / (141,11,175,51) | Separate musical maze game |
| Instrument label | (39,99) | 1 / (95,13,106,70) | Next individual instrument |
| Copy song | (275,124) | 13 / (113,262,136,286) | Yes/No copy into personal song book |

All rectangles are (top,left,bottom,right), exclusive bottom/right. Piano hotspot table is image `0x2F180+0x44`, stride 8. Captures: `ensemble/state/click-0.png` = family menu; `click-1.png` = Animals; `click-2.png` = Lamb. `menus/state/click-1.png` = advanced Lion Theme; `click-2.png` = blank My Long Song #1. `categories/state/click-0.png` = copy dialog. `selector/state/click-0.png` and `click-1.png` show the musical maze and its movement.

## Family selector

Source: `8BF0..9075`, data segment image `0x2FFE0`.

1. Draw MODULES SHAP2271 with SHPL2270 at (0,0), opaque.
2. Draw TH SHAP8 exit at (304,1), TH SHAP7 return at (280,1), using the shared UI palette. Both use TH SHPL6, confirmed by full-frame reconstruction.
3. Seven labels come from MODULES STRL100, IDs 0..6 in zero-based extracted arrays. Category rectangles are `menu_rectangles[2+i]` in the exported table. The original draws the built-in heading font (`heading_font`, executable0x2EAC0) with an eight-neighbor black outline and gray foreground (EGA7), with extra1pixel advance per glyph, centered at `x=(left+right)//2-width//2`, `y=(top+bottom)//2-(height+1)//2`. Root background already has some box/sector decoration; source explicitly fills first three category rectangles with the family's palette color and rounded corners via resident6B21. The helper first draws the same rounded fill translated by(1,1) in black, producing a one-pixel right/bottom shadow, then the colored foreground.
4. Current selected instrument animation sits at bottom-left. Wrapper `3B92(instrument,-1,199)` supplies x=-1 sentinel and bottom y199. Its screen origin is(1,199-height), where height is script.bounds.bottom-script.bounds.top. For Bass this is(1,114), yielding body11101@(8,137) and head11105@(14,114). Both menu root and Animals page reproduce these exactly.
5. Clicking a category highlights its text and brightens its palette color by8 (6-bit RGB, clamped63), waits24 native ticks, opens category page.

| Category ID | Label | Member IDs (portrait order) | Portrait palette/group |
|---|---|---|---|
|0|Animals|25,26,27,28,29,30,32|2400|
|1|Home Made|35,37,34,40,39|2410|
|2|Mixed Bag|33,36,38,31,41|2420|
|3|Percussion|9,16,22,23|2430|
|4|Brass|21,20,18,14,19|2440|
|5|Woodwinds|7,10,8,17,12|2450|
|6|Strings|15,11,13,24|2460|

The table proves categories are mixed instrument choices, not separate animal/home-made world scenes. The bucket game is a distinct additional activity.

### Category page

Independent static reconstructions `research-music-followup/menu-render.py` (root) and `category-render.py` (Animals page) each match all64,000pixels, including the original mouse cursor.

Source `9076..987F`; table offsets relative image0x2FFE0:

- +0x50: eight UI rectangles (`instrument_rectangles`).
- +0x90: seven category palette indices in SHPL2270, `[12,13,14,8,10,6,4]`.
- +0x97: EGA fallback indices.
- +0x9E: seven member counts `[7,5,5,4,5,5,4]`.
- +0xA5: seven groups of seven member bytes.
- +0xD6: 42 signed16 portrait x positions.
- +0x12A: 42 signed16 portrait y positions.

Draw SHAP2272/SHPL2270 opaque at (0,0). Each portrait uses SHAP(group+1+memberOrdinal), SHPLgroup, at `(portrait_x[instrumentID], portrait_y[instrumentID])`. Input extends each portrait's decoded bounds by6 in all directions. Draw UI exit and piano-return controls, and SHAP2273 at(259,3). Header rectangle(4,106,21,208) is family palette color; text uses the built-in heading font (`heading_font`, executable0x2EAC0), black outline, EGA7 center. Draw waveform MODULES SHAP(2001+instrumentID) / SHPL2000 at(63,144), inside mainDS:CA6 rectangle(144,63,192,183), except Sousaphone21 uses Tuba20 waveform. Inspecting an instrument updates name/fact/icon/waveform and animates the individual singer/musician.

The name is STRL100[instrumentID]. Facts are STRL[instrumentID]. Native initial fact is randomly chosen, then subsequent fact clicks advance. Title rect(103,227,115,305); facts rect(126,193,194,306); fact icon rect(97,194,123,223); waveform interaction rect(125,63,195,183). Fact icons use member bytes at data+17E to select MODULES2050 or2075 palette, and data+1A8 as a1-based relative shape index. Use palette.first+index-1; group2075 starts at SHAP2075, not2076. Fill white, frame black, center original icon. Animals icon is2075@(203,102). The title uses heading_font with+1advance and lineheight10; Animals origin(246,104). Paragraph wraps FONT1 at113pixels, preserves doubled spaces, uses10pixel lines vertically centered in68pixels. The five-line Animals first fact starts(193,135), then y+=10. `9698` resets the information alternate mode, chooses random fact, draws name/fact/icon/waveform. `98B7`/`98F6` advance information/facts and remain to be traced precisely.

Clicking family header selects instrument ID0..6; combined sample VOICES12000+ID and animation TH10000. Clicking portrait selects that individual instrument, updates SONG byte3, and auditions it. Clicking the already selected portrait repeats its sample and cycles the fact. Clicking the animated instrument at bottom left repeats its audition.

### Combined playback backend distinction

Digital backend uses original combined sample12000..12006. MIDI backend builds one simultaneous channel per family member (`1EA9..1FC7`), each with member-specific program and octave adjustment, and stops all channels together (`1FCA..2034`). Do not implement the digital combined sample as one arbitrarily selected family member. The clone currently uses original digital samples, so all seven combined samples are sufficient for its existing audio backend.

## Composition state and notation

Source `D21..D72` toggles composing flag, source `E6F..EC0` toggles advanced flag. Both stop playback, repaint controls, reload selected song. These flags are independent: four states (short listening, long listening, short composing, long composing). Native My Long Song #1 starts blank with Piano9, tempo3, selected quarter note duration4.

Original state is in the segment reached by mainDS:4A22 (do not assume this equals the constant geometry segment): +A2 composing flag, +A4 advanced flag, +9E four selected song indices keyed by `2*advanced+composing`. Runtime selection index is in the segment reached via4A3C at+A12. Printer enlargement uses a separate +A8A flag; normal screen rendering keeps it0.

Constant geometry lives at image0x2F180. The export preserves these tables rather than inferring shape placements from screenshots:

| Offset | Data |
|---|---|
|+16B|u16 notes per row:8 intro,15 advanced|
|+16F|9 introductory marker rectangles; first is aggregate|
|+1B7|31 advanced marker rectangles; first is aggregate|
|+2B3|8 introductory note rectangles|
|+2F3|30 advanced note rectangles, two rows|
|+431|four17-byte pitch height tables: normal sharp/flat then small sharp/flat|
|+4A8|5 introductory duration hit rectangles|
|+4D0|16 advanced duration hit rectangles|
|+550|32s16 palette-glyph x offsets,16slots per mode|
|+590|32s16 palette-glyph y offsets|
|+5D0|u16 duration palette counts5,16|
|+5D4|16 duration codes per mode; intro0,2,3,4,6; advanced0..15|
|+634..646|paired normal/small stem and flag constants|
|+64A|u16 capacities8,30|

### Advanced score geometry

Routine3478 redraws staff segments;37FE draws joined five-line staffs. In advanced mode: staff lines y28,34,40,46,52 and y67,73,79,85,91; left x88; width210 (verify inclusive endpoint through the native comparator). Vertical joins atx88. Clef is the small mask SHAP2302. Native complete reference is `menus/state/click-1.png`. Independent reconstruction `research-music-followup/advanced-score.py` matches every one of the15,900pixels in(88,27)-(300,102), including staff endpoints x298 and small clefs at(90,27),(90,66).

Routine2A82 places notes: x=110+13*(index%15), y=56+39*floor(index/15)-pitch_y_offsets[2+notationFlag][pitch]. Source uses head horizontal shift5 on top of note hit-cell left105. Small heads are SHAP2304 hollow/2306 filled; accidentals2314 sharp/2316 flat, small flags2308/2310, small dot2312. The small ledger line is `[x-2,y+2,x+7,y+3)`.

Small upward stem: x+4, y-10 through y (height11). Small downward stem: x,y+4 through y+14 (height11). Upward flag2308 at(x+5,y-9), second at(x+5,y-6); downward flag2310 at(x+1,y+10), second at(x+1,y+7). Duration1,3,5 has dot2312 at(x+6,y+(pitchHeightOffset%6?3:0)), confirmed from385F and2C84 and the complete score comparison. Ledger condition at2CB3 is pitch<=1-notationFlag (sharp mode0 includes C and C-sharp; flat mode1 includes C only). Rests retain the original rest glyph shapes2320..2327 and use recovered offsets (export has separate printer/layout variants; normal screen variant0).

Source33D5: advanced markers use2319 for row0,2318 for row1, at markerRect.left+4, markerRect.top. Markers sit between staffs at y62; direction indicates which staff receives the next key input. Intro uses2317 at left+6,top+4. Selected marker green(EGA2), playback red(EGA12), removal white(EGA15).

### Duration palette

Routine217E first fills (111,129,140,231) white. It loops5 or16slots. For sloti, draw at `(rect.left+xOffset[16*advanced+i],rect.top+yOffset[16*advanced+i])`. It passes original duration code, upward stem, dot-height argument1, no accidental or ledger. Selected duration is dark red EGA4, others black. The glyph routine chooses small geometry when advanced and not printer mode. Intro duration choices correspond whole/half/dotted-quarter/quarter/eighth; advanced includes all8notes and8rests.

Keyboard entry in composing mode writes a note into the selected position, uses selected duration and notation flag, repaints it, and advances selection. Earlier research covers original physical keys. Source loops around18A1..1B0B and1C73 need further tracing for insertion/drag behavior. Duration selection preserves the chosen note/rest code modulo8 for subsequent keyboard notes (0033A..00354). Original short/long song capacity is8/30; personal song count and serialization format still need full tracing.

## Additional missing activity: musical maze

The piano bucket launches overlay1:51B6, loading MODULES group2340 (`0x924`), TH22000 and boy20000. State is a node graph in image0x2F9F0; current node +9D4, four exits per node at+20 (u8 neighbors), positions at+6C (four `(y,x)` pairs per node), paths/animation targets+100. Native starts with frog near paths, homemade instruments as obstacles, and a score. This needs its own research and implementation; it is not already covered by the piano or family selector.

## Verification limits

Captures above are trustworthy original ordinary-input evidence. The complete advanced Lion Theme score region is independently exact (15,900pixels). Family root and Animals category page also match full64,000pixel native frames independently. Other categories, fact variants, audition transitions, composition edits, rest variants, and the newly identified musical maze still require additional comparisons. The findings are implementable source evidence, not a declaration of complete parity.
