# Pixel-exact native preferences rendering

Primary-source follow-up, 2026-09-27. Complements `treehouse_settings_persistence_research.md`. No runtime changes.

## Result

The independent renderer `output/treehouse/research-settings/render-panel.py` matches **27,904 of27,904 pixels** in the original preferences panel `(x32,y43,width256,height109)` for each of six captures: initial preferences, Sound toggled, Printing toggled, Printer toggled, Music Game Level toggled, Speed Optimization toggled. The original cursor is reconstructed from executable masks and read-only pointer coordinates; it is included in these comparisons. The renderer does not copy native screenshot pixels into its output. Reference images are loaded only for comparison.

Evidence: `output/treehouse/research-settings/panel-comparison.json`; reconstructed crops are `preferences-panel-reconstructed.png` and `row-0-panel-reconstructed.png` through `row-4-panel-reconstructed.png`. Original captures and ordinary input log remain under `research-settings/native/`. The comparison covers the complete panel, including frame, button shadow, text and cursor; it does not claim to reconstruct the room behind the modal.

## Font identity: existing heading_font is correct

The global preferences font is **FONT0**, embedded in the executable at image offset **0x2EAC0**, length **0x5F7**. This is exactly the asset currently exported as `ORIGINAL.heading_font`, including lowercase glyphs. It is not the external TH FONT1 used for body text elsewhere.

Primary evidence:

1. The executable's internal resource directory at `0x3166A` contains little-endian tag words spelling `TNOF` (FONT), resource ID0, far payload pointer `2EAC:0000`, and size05F7.
2. Graphics bootstrap at image `15575..1557A` calls FONT loader1563A with CX=0 after the preceding `rep movsw` exhausted CX, then stores the returned handle in DS20B2.
3. Main `01C4..01C7` copies DS20B2 into DS57C4. Only afterward, `01CA..01D3`, the application loads external FONT1 and changes DS20B2.
4. Preferences heading renderer5BB3, row renderer1CB8 and Done renderer5893 explicitly select DS57C4.
5. The six independent pixel comparisons establish the font's identity and rendering metrics in the ordinary native VGA room palette.

Font header at2EAC0:

| Byte | Value | Meaning |
|---:|---:|---|
|0|27|First character|
|1|126|Last character|
|2..3|7|Ascent|
|4..5|2|Descent|
|6..7|1|Interline spacing|
|8..9|1|Intercharacter spacing|
|10..209|100×u16|Offsets from font start to glyph records|

Glyph record: u16 height, u16 width, u16 byte stride, then `height*stride` bytes of row-major monochrome data, MSB first. Space has height0,width2,stride0 and still advances3 pixels. Lowercase descenders can be9 pixels high; do not align each string using its first glyph's bitmap height.

String width is **sum(glyph.width +1)**, including the final character's trailing gap. This is confirmed by native width routine image17962..179A2. Do not subtract that last gap.

For one centered line in rectangle `(top,left,bottom,right)`:

```text
advance = sum(glyph.width + 1)
rasterX = left + floor((right-left)/2) - floor(advance/2)
rasterY = top + ceil((bottom-top)/2) - ceil((7+2)/2)
        = top + ceil(height/2) - 5
```

`rasterY` is the top of the glyph bitmap, **not the baseline**. Draw glyph masks at that shared Y; descenders are included in their bitmap rows. Native alignment arithmetic is image1789C..178CF and17919..1793A. Top-aligned heading uses its rectangle top directly. Font ascent/descent/interline metrics govern vertical centering, not the visible capital glyph's7-pixel height.

## Exact panel recipe

Coordinates below use exclusive bottom/right. Draw in this order:

1. Black rectangle `(43,32,152,288)`.
2. White rectangle `(44,33,151,287)`.
3. Blue9 `PREFERENCES`, centered horizontally in `(47,32,148,288)` and **top aligned**, glyph raster Y47.
4. Five centered black labels in `(61+14*i,34,75+14*i,286)`, i0..4. Glyph raster Y is63,77,91,105,119.
5. Black Done shadow as the union of `(138,243,148,283)` and `(137,244,149,282)`.
6. Blue9 Done face as the union of `(137,242,147,282)` and `(136,243,148,281)`.
7. Black `Done`, centered in **`(137,242,149,282)`**, raster Y138. This text rectangle is the logical button rectangle shifted down one pixel; do not vertically center in the face's7/10-pixel subrectangles.
8. Original cursor when it overlaps the panel.

Original logical Done hit rectangle remains `(136,242,148,282)`. The shadow extends right to282 and bottom to148 inclusive. The button has clipped one-pixel corners, not a conventional stroked rectangle. Source5893 passes shadow color0 and the chosen face color into6B21; that helper combines a vertical inset1 rectangle and a horizontal inset1 rectangle, draws the pair shifted `(1,1)` as shadow, then draws the unshifted pair as face.

Palette in the verified native room capture:

| Index | RGB | Use |
|---:|---|---|
|0|0,0,0|Text, panel frame, Done shadow|
|9|85,85,255|Heading, ordinary Done face|
|12|255,85,85|Pressed row background / pressed Done face|
|14|255,255,85|Cursor yellow|
|15|255,255,255|Panel and ordinary row background|

Shared color helpers58EE/5934/597A return15/12/9 outside activity phases2/13. For phases2/13 they use7308 to map those desired colors into that activity palette. The six pixel comparisons above use interior phase5. Use the native palette mapping helpers if retaining indexed activity palettes, rather than assuming color index9 always has the same physical RGB in every context.

## Exact label strings

Use the selected state word's zero/nonzero branch:

| Row | Off/on forms |
|---:|---|
|0|`Sound is on/OFF` / `Sound is ON/off`|
|1|`Printing is on/OFF` / `Printing is ON/off`|
|2|`Printer: Not Selected` when selected profile unavailable; otherwise `Printer: ` followed by the original selected printer profile name|
|3|`Music Game Level: BEGINNER/advanced` / `Music Game Level: beginner/ADVANCED`|
|4|`Speed Optimization is on/OFF` / `Speed Optimization is ON/off`|

Case is meaningful: selected state is uppercase. No colon follows Sound or Printing. Source literals are DS028E,0295,029C,02AE,02C0,02CD,02DD,02EA,0300,0316; heading DS03C9 and Done DS03C4.

Source1EEA redraws a changed row using pressed red12, waits12 interruptible native ticks, then redraws it white15. This feedback fills its entire row rectangle and renders the newly changed label in black. Done/Escape draws the button in pressed color12 before returning. The supplied comparisons are settled states; no pressed-state capture was added in this follow-up.

## Integration instructions

- Reuse `ORIGINAL.heading_font`; an additional font asset is unnecessary.
- Keep ordinary body text helpers separate if their vertical centering uses7-pixel bitmap height. Preferences needs the font's9-pixel ascent+descent line box.
- Include the trailing character gap in measured width, even for `Done`.
- Follow the explicit union-of-rectangles button recipe and shifted text rectangle.
- Numeric geometry/font metadata and proof counts are recorded in `treehouse/preferences-rendering.json`.

Primary artifact hashes are those in the persistence report. These findings derive from executable code/resource bytes plus ordinary native input captures, with no guest memory modifications.
