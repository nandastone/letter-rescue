# Contextual F1 help and keyboard status messages

Primary-source reconstruction, 2026-09-27. No runtime changes. Main addresses refer to the pinned unpacked executable and `output/treehouse/research-resources/main-disassembly.txt`; resident-library image addresses are explicitly prefixed “image”. Source ZIP/image hashes are those in `treehouse_settings_persistence_research.md`.

## Deliverables and demonstrated parity

- `treehouse/help-text.json`: **all26 original TXT4 help resources**, independently decoded, with source resource paths, context IDs, raw decoded bytes, title and body strings.
- `treehouse/help-layout.json`: all26 contexts' exact panel geometry, title/body positions, prewrapped body lines, and comparison results.
- `output/treehouse/research-help/decode-help.py`: decoder directly translated from native image1BB2E.
- `output/treehouse/research-help/render-help.py`: independent renderer from original fonts, text and source geometry.
- `research-help/native/` and `research-help/extra/`: ordinary-input native captures, state snapshots and logs identifying their unmodified restore states.
- `research-help/comparison.json`: **12 complete help-panel regions and two status-message regions match with zero differing pixels**, including native cursor where overlapping. These cover outdoor welcome, room, listening/composing music, Animal Album, theater editor/options, board options/active game, nature quiz, and musical maze. Board options has two captured instances.

The attempted `board-trays` F1 press did not open help while the native tray/sound sequence was in progress (modal flag stayed0). It is recorded as `help_not_opened`, not counted as a rendering comparison. The supplied text/geometry for context16 is source-derived but not independently captured in this pass. Full room backgrounds were not reconstructed here; each comparison covers its entire declared modal/message rectangle.

## TXT4 format: these are the help resources

TH contains26 `TXT4` resources in the1100..1129 range, excluding unused IDs1104,1105,1112,1114. They each decode to two strings, title then body. Native helper6393 requests tag54585434 (“TXT4”), passes the loaded resource through decompressor D51:E2A4/image1B7B4, then indexes the resulting counted NUL-separated string list. Calls use1 for title and2 for body. There are **no help page images, page arrows, or multiple-page state** in5E07; the complete selected body is displayed in one modal.

Decoder at image1BB2E:

```text
outputLength = u16le(payload[0:2])
bitstream = payload[2:]
extendedWidth = (bitstream[0] >> 6) + 5
bitPosition = 2
repeat until outputLength bytes emitted:
    v = readBitsMSB(4)
    n = 4
    if v == 0:
        n = extendedWidth
        v = readBitsMSB(n)
    emit v if n == 8 else alphabet[v]
```

Alphabet is the128-byte table at **main DS247A / image3464A**. It begins NUL,space,a,e,t,o,n,i,s,r,d,l,h,u,g,f. The extracted alphabet and exact offset are documented by the decoder. The output starts with byte2 (string count), then title NUL body. Resource1129's declared decoded length ends at the final `Lance` without a terminal NUL; retain that final string rather than dropping it. All other help resources have the expected terminal NUL.

This identifies the26 previously unresolved TXT4 resources described in the early resource report. `help-text.json` preserves exact punctuation, double spaces, and CR characters; do not normalize them before native wrapping.

## Context selection

Resident5CA3 uses live activity phase at shared state+B34 (runtime fixture RAM318B0+B34). It does **not** use the saved global preferences directly except for theater switches, music composing, and per-player nature help.

| Live phase | Context | Meaning |
|---:|---:|---|
|0|0 listening /15 composing|MUSICAL KEYS; sharedA2 selects composing.|
|1|1|ANIMAL ALBUM.|
|2|2/20/21/22|TREEHOUSE THEATER editor; see switches below.|
|3|3 or23|ROAD RALLY active game; DS5810 nonzero selects prize/winner help23.|
|4,5|18 or19|Outdoor/room: DS5692==0 means welcome18, nonzero means treehouse19.|
|6|6|THE ORCHESTRA family selector.|
|7|7|ORCHESTRA SECTION.|
|8|8|MUSICAL MAZE active game.|
|9|9/26/27/28|GUESS MY ANIMAL; see priority below.|
|10|10|ROAD RALLY options.|
|11|11|GUESS MY ANIMAL options.|
|13|13|TREEHOUSE THEATER options.|
|16|16|ROAD RALLY money tray choice.|
|17|17|MUSICAL MAZE LOBBY/victory.|
|24|24|ROAD RALLY chip tray choice.|
|25|25|ROAD RALLY making change.|
|12,14,15,18..23, >25|18 or19|Fallback welcome/treehouse according to character-loaded state.|

TXT4 resource ID is `1100+context`. The exact26-entry jump table is image5DC7; it distinguishes activity phase from help context (context15 composing is not activity phase15).

Theater phase2 mapping: shared406 Mix Up and408 Props both zero→2; both nonzero→20; Props only→21; Mix Up only→22. The different texts retain the base theater instructions and append the applicable controls.

Nature phase9 priority (`5D29..5D72`):

1. DS55EA nonzero (end/reveal/prize state)→28.
2. Else DS529E nonzero (roll/clue request state)→26.
3. Else call overlay2:2851 for role: DS5250==0→human0, otherwise shared3FE opponent1/2. If saved help flag shared400+2*role is nonzero→27; otherwise→9. Context9 includes manual thumbs-up/down elimination;27 omits it.

### Hidden dedication

Inside5E07, held **Ctrl+Alt** and pointer both coordinates<2 override the computed context to29. Ctrl bitmapDS159B, AltDS15B6; X=DS2066,Y=DS2064. Thus Ctrl+Alt+F1 at the top-left corner opens TXT41129, titled `DEDICATED TO JANESE SWANSON`. The full body is included in the decoded data. This path is source-established, not native-captured here.

## Entry, blocking, and closing

F1 is scan code3B, flagDS15B9. Shared key service18CD tests guard187E before5E07:

- Existing modal DS52E2 prevents entry.
- Music playback flag sharedA92 prevents entry.
- Active sound plus a loaded character also prevents entry.

Before opening, it flushes the pending input state, performs resource/sound preparation, and puts down an active drawing tool (DS15E8) through2785; the native cursor is restored to the standard pointer. On return, B95C resets room ambient deadlines. This shares the preferences guard and avoids nested F1/F2 modals. See source18DB..1941 and187E..18CC.

Help sets DS52E2=1 only after drawing. Its loop calls2F86 for limited shared service and18CD for input. On any nonzero input, it checks **whether the current pointer is inside the entire help panel**, not whether the pointer hits Done and not whether the event is Escape. If outside, it continues waiting. If inside, it closes. This native peculiarity is verified by ordinary room captures:

- F1 opens help with cursor inside.
- Move to(10,10); Escape leaves help open (`room-escape-outside.png`, modal1).
- Click(10,10); help remains open (`room-click-outside.png`, modal1).
- Move to(160,100); Escape closes help (`room-escape-inside.png`, modal0).

Consequently an inside click on text closes help; an outside click does not. The mouse must be inside even for Escape. Closing clears modal flag, draws Done pressed, waits **20 interruptible native ticks**, restores the saved backdrop, then calls overlay1:518B with argument10, setting the orchestra idle deadline DS56C4/56C6 to current tick+600. The source has no page-changing controls, no help scroll, and no help narration call.

## Exact dynamic layout

Fonts: heading/Done use embedded **FONT0** (existing `heading_font`); body uses external **TH FONT1** (existing body font). FONT0 has character gap1 and9-pixel ascent+descent; FONT1 has character gap0 and the same7+2+1 line metrics. FONT1 glyph payloads are compressed SHAP records: use the established shape decoder, not FONT0's direct bitmap layout.

The native code intentionally uses different widths for measurement and display:

1. Count lines of the body at width **256**, using native break helper D51:8492/image159A2 and FONT1 widths. `height = measuredLineCount*10 +48` (source5E45..5EA0, helper7822).
2. `top=100-floor(height/2)`, `bottom=100+floor(height/2)`. Panel is `(top,32,bottom,288)`.
3. Fill white, black1-pixel inside frame.
4. FONT0 heading: centered horizontally in `(top+4,32,bottom-4,288)`, top aligned at glyphY=`top+4`, blue.
5. FONT1 body: inset rectangle **`(top+4,50,bottom-4,270)`**, width220. Rewrap at220; left align atX50 and center all rendered lines vertically in this rectangle. For N rendered lines, text block height is`10*N−1`, so glyphY=`top+4+ceil((bottom-top−8)/2)−ceil((10*N−1)/2)`. Draw subsequent lines10 pixels apart.
6. Done logical rectangle `(bottom−16,242,bottom−4,282)`. Use the exact preferences button construction: two black shadow rectangles, two blue face rectangles, and FONT0 `Done` centered in the logical rectangle shifted down1 pixel. See preferences rendering report for that helper's recipe.
7. Draw normal native cursor.

Measured and displayed line counts differ in real screens: composing13/14, Animal Album13/14, board options11/12, musical maze9/11. **Do not size the panel from the final displayed line count.** `help-layout.json` supplies the correct wrapped lines and resulting coordinates for every original help body, so integration can directly consume the native layout without duplicating a fragile text wrapper.

### Native wrapping rules

Use summed glyph advances; FONT1 already includes its spacing in width and header gap0. Scan characters until the accumulated advance exceeds available width. Record break opportunities after space/hyphen and immediately before a following space. Carriage return ends the line and is consumed; consecutive CRs create blank lines. On overflow use the last recorded break, or the consumed character count if no break exists. Return all remaining characters if they fit.

Rendering left-aligned continuation lines skips one leading space unless the preceding source character was CR. If the preceding source character was a period and the next character is another space, skip the second leading space too. This matters for the native double spaces after sentences; omitting the rule caused a single displaced line in several screens. Source image159A2..15A07 and178E0..1790F. Preserve the untrimmed source positions while applying this display-only skip.

### Palette

Ordinary room/music/nature/board uses EGA black0 `(0,0,0)`, white15 `(255,255,255)`, blue9 `(85,85,255)`, pressed red12 `(255,85,85)`.

Theater phases2/13 use the existing palette remapper7308 through58EE/5934/597A. In the captured theater palette, blue is **MODULES SHPL3000 color12 `(32,24,255)`**, white is color1, and pressed red is the mapped theater color10. The same geometry/text matches exactly once this remapping is used. Avoid fixed EGA RGB in theater help/preferences.

## Ctrl+V and Ctrl+S status overlays

Shared key handler19E9..1A60:

- Ctrl+V (scan2F, DS15AD) clears its key flag and Ctrl flag, then calls78B8 with literal DS0276 **`Version 1.1`**, duration180 ticks.
- Ctrl+S (scan1F, DS159D) clears its key flag and Ctrl flag, toggles sound via61BF, then displays literal DS0042 **`Sound is Off`** or DS004F **`Sound is On`**, duration180 ticks.

These key paths do not call the F1/F2 guard187E. They are processed wherever the shared input service18CD runs, including during its modal loop; there is no independent persistent speech preference. Ctrl+S modifies stateAA and calls sound volume15/0; it does not itself immediately write STATUS.

Renderer78B8 saves the original backdrop in DS04FC rectangle **`(176,108,192,212)`**, invokes76E5, waits, then restores it.76E5 fills white, draws a red1-pixel inside frame, selects FONT0, temporarily sets font descent to **0**, and centers black text. Restore descent2 after rendering. Exact version/status glyphY=180; centeredX=`160−floor(sum(glyph.width+1)/2)`, including final gap. This independently matches all1,664 pixels in both captured `version.png` and `sound-off.png` regions.

D51:5C0F/image1311F implements the wait: timerDS2016=180, services input until it expires or any input is returned, clears the timer, returns the input event and restores the previous input mode. Thus the message is blocking within the current input handler but dismissible early; the triggering key flags have already been cleared. Native `version-closed.png` / `sound-closed.png` show the background restored after200 additional capture frames. No Done button or modal help flag is used for this small message.

## Implementation scope

Use all26 resource texts and context selection above, including state-dependent help. Native text remains available for pixel mode; modern readable text can be a separately rendered presentation of the same content. Preserve original pointer-dependent close semantics in native mode if strict input parity is required. The hidden dedication, all theater switch combinations, and the noncaptured board/quiz subphases have source-backed data, but this report's pixel-parity claim applies only to the explicitly listed successful captures.
