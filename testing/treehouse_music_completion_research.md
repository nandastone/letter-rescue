# Treehouse music completion: contents, titles, printing, and input

Primary-source follow-up, 2026-09-27. Supplements [music editor research](treehouse_music_editor_research.md). No runtime files changed. Sources are the pinned original executable/resources and ordinary-input native captures; the original ZIP SHA-256 is `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`.

Actionable extracted data and comparison results: [music-completion-tables.json](treehouse/music-completion-tables.json). Scratch and capture root: `testing/output/treehouse/research-music-completion/`.

Instruction addresses below are overlay1 unless marked resident. Resident library `D51:xxxx` has linear image address `0xD510+xxxx`; its instructions are available in `research-resources/all-disassembly.txt`. Shared music state starts at image31690; geometry at2F180; resident DS at321D0. This capture environment adds544 to those image offsets when reading RAM0.

## Ordinary-input evidence

| Directory | Useful named captures |
|---|---|
|`main-capture/state`|`listening-toc1`..`listening-toc4`, `toc-row`, `composer-toc1`, `title-open`, `print-click`|
|`title-erase-capture/state`|`title-a`, `title-escape`, `composer-toc-renamed`, `erase-all-dialog`, `erase-all-confirmed`, `other-book-cleared`, `listening-end`, `listening-end-audition`|
|`print-capture/state`|`print-question`, `print-yes`, `print-after-wait`|
|`release-capture/state`|`c-held`, `e-held`, `released`, `toc-key-held`, `toc-key-released`|

Every directory retains `run.json`, full `frames.jsonl`, unique callback frames, and named PNG/state/RAM files. Scripts boot then restore an existing ordinary-input native state; they never change guest memory.

Two capture caveats matter:

- In `main-capture`, the exploratory Escape after the print question returns out of the activity. Later snapshots in that run (`erase-all-*`, `erase-other-book`) are **not valid editor evidence**. The dedicated `title-erase-capture` replaces them.
- The text editor does not keep an up-to-date NUL after every typed character. Its live length is a local variable. A raw RAM string such as `ay Long Song #1` in the run report displays only `a` while editing. Named Enter captures sometimes show the field reopened under this keyboard harness; use the later mouse-committed title/contents captures for accepted-title evidence. The source editor's Enter branch is unambiguous, but an end-to-end Enter-only capture remains a harness-sensitive check.

## Table of contents: model and navigation

Sources `073E..0805`, `14F8..1743`, `463D..48D8`.

- Open with hotspot15 `(26,305,35,318)`, click `(311,30)`. State+9DE is the one-based contents page; zero means regular score view.
- Six songs per page, **column-major in two columns of three**. Listening has4 pages for24 songs; composing has7 pages for42 ordinary personal songs. The special terminal record is never listed. Source page count is `(bookRecordCount+4)//6`, with book counts25/43.
- `songIndex=(contentsPage-1)*6+slot`. A row click selects it, saves the previous personal page where relevant, closes contents through the normal page loader, and updates the listening index in both short and long modes. Personal selections remain separate by mode.
- Clicking the current page tab hotspot23 `(1,258,22,281)` closes contents without changing song selection (`4844`).
- Page-turn hotspot21 `(9,284,26,303)` splits diagonally: forward if `pointerX-left > pointerY-top`, backward otherwise. While contents is open, forward after the last contents page enters song0. Backward from contents page1 clamps at1. Backward from ordinary song0 opens the **last** contents page. Other normal page turns change the song by1, clamped at the terminal record.
- Direct side page-number tabs still jump to their advertised song pages. Table-of-contents state is cleared by the page loader.
- Piano keys continue to audition while contents is open, but do not write notes or advance the composition marker. Verified by `release-capture/toc-key-*`.

### Exact contents rendering

Source `463D`. `render-toc.py listening-toc1`..`listening-toc4` independently reconstruct the full score area plus heading. Each compares17,785 pixels with **zero differences**; four pages total71,140 exact pixels. This is a region comparison, not a full piano-frame claim.

1. Clear score `(27,88,102,300)` white, title icon `(6,88,26,110)` white, and title rectangle `(13,113,26,258)` white.
2. Use these six row rectangles, stored at image2F180+124:

| Slot | Rectangle `(top,left,bottom,right)` |
|---|---|
|0|27,88,47,193|
|1|50,88,70,193|
|2|73,88,93,193|
|3|27,194,47,299|
|4|50,194,70,299|
|5|73,194,93,299|

3. Opaque song picture at `(left,top)`. Listening uses the existing packed selector at geometry+7F5+songId+1; group=`2100+20*(selector>>4)`, one-based relative shape=`selector&15`. Composing always uses personal icon2101/palette2100.
4. FONT1 title black at x=`left+24`. Wrap by words to81 pixels using actual glyph-width advances. Ten-pixel line spacing. Text block top=`(top+bottom-(10*lineCount-1))//2`. Listening titles are MODULES STRL101 decoded array[songId]; composing titles are read from native SONGS.DAT through resident7C20.
5. Heading `Table of Contents` comes from STRL101 one-based26. Use the builtin heading font image2EAC0, glyph-width+1 advances, black, no outline. Exact origin `(137,13)`.
6. Roman page labels are `i,ii,iii,iv,v,vi,vii`; mainDS+B12/B14/B17/B1B/B1E/B20/B23. FONT1 bottom-right in the score area: y93, x=`300-measuredWidth`. The top page tab is updated by4349 to contents artwork.

## Listening terminal page differs from personal terminal

The listening terminal is **SONG24**, directly from MODULES. Captured header is `[8,8,4,27,0]`, so it uses **Dog instrument27**, tempo4. The personal terminal record uses **Duck28**, as established by the earlier editor research. Do not make both books share the same terminal SONG.

Native path: choose listening side tab24 at `(311,90)`, then forward page corner `(300,14)`. Capture `title-erase-capture/state/listening-end.png` shows the dog and The End artwork. It automatically plays on entering. A subsequent piano-key audition leaves the SONG and marker unchanged.

Rendering remains the existing terminal recipe: white title/icon/score regions, MODULES2207/SHPL2200 at `(98,27)`, special empty page tab, instrument controls retained. Print/editor commands fail the regular-page predicate3F7B and do not operate on terminal pages.

## Ctrl + erase all

Source `0F33..0FB3`, resident7F65..809D. This is a separate branch from ordinary whole-song erase.

1. On the erase toolbar press, test Ctrl using library5C52 (BIOS0040:0017 bit2).
2. Ask `Erase ALL songs?` using the standard animated Yes/No dialog. Exact native text wraps `Erase ALL` / `songs?`; the screenshot is `title-erase-capture/state/erase-all-dialog.png`.
3. No returns unchanged. Yes first saves/closes the current page, then initializes all43 physical records in each of the two personal books through the existing blank/default initializer with resetDefaults=true, saving each record.
4. Both personal selected indices reset0. Restore the original short/long and listening/composing mode. Reset marker0 and load the selected first page.

Defaults are tempo3, Piano9, sharp default0, default `My Short Song #1` / `My Long Song #1` titles. Source retains the special terminal initialization. This erases both ordinary personal books, not the fixed listening resources or unrelated activity state.

Native confirmation: previously renamed long title `luna song` becomes `My Long Song #1`, long active length0; switching short yields `My Short Song #1`, short active length0. Captured headers `[8,0,3,9,0]` and `[0,12,3,9,0]` retain irrelevant other-mode length bytes. Do not treat those irrelevant bytes as remaining song content.

## Native title editor

Entry `0C0F`; libraryD51:3DE8 = image112F8..115BA. Title rect6 is `(13,113,26,258)`; maximum35 characters.

The original is a simple **replacement field**, not a cursor-moving text editor:

- Copy the old title to a local backup, clear the displayed field and set edit length0. It starts blank regardless of the previous title.
- ASCII32..126 appends to the end. No insertion point, selection range, arrow movement, Home/End editing, or Unicode path exists in this routine.
- Both Backspace8 and Delete5300 remove the final entered character if edit length>0.
- In addition to max35 characters, accept a new glyph only when `currentX+glyphWidth+underscoreWidth < rect.right`. Thus wide text can reach its limit before35 characters.
- Escape restores the original title, redraws it, moves the append position to its end, and **stays in edit mode**. It does not close the editor.
- Enter13 or pointer-button event1/2 accepts. Empty replacement restores/retains the original title. On acceptance, write NUL at edit length. The calling handler recomputes the used flag through4127.
- The editor temporarily writes into the shared buffer without maintaining a NUL after each append; render only the active length, not the whole leftover buffer.

Rendering: FONT1 at x113, vertically centered by shared115BD (native visible text top15). White fill within the title rectangle, black text. Blue EGA9 outline around the title rectangle expanded2 pixels horizontally: x111..259, y13..25. Blinking underscore uses FONT1 `_` at current append x; alternate foreground/background every6 native ticks. On exit erase outline in white and restore normal title display. Capture `title-open` shows blank field/underscore; `title-a` shows `a`; `title-escape` restores original title with caret at its end. `composer-toc-renamed` proves mouse acceptance and saved-title use in contents.

For a modern implementation, a conventional editable field can be offered as an explicit usability improvement. Native mode should retain the replacement/restore semantics above if exact behavior is desired.

## Printing

Entry toolbar hotspot14 `(113,289,136,308)`; click `(296,124)`. Source0EC3 requires regular page3F7B and shared state+AC nonzero (configured printing availability). It highlights SHAP2260 and asks `Print song?` through the ordinary dialog. This works for an empty regular composition too.

Yes invokes491E..4AF1:

1. Stop musician/clear the piano activity buffers.
2. Set state+A8A=1 (print geometry mode).
3. Load MODULES SHPL2296 and draw relative1/2, i.e. **SHAP2297 short,2298 long**, at `(0,0)`, opaque.
4. Draw the instrument's black print icon using resident5ACD. Its origin is `(printRect.left, printRect.top-34)`; shared state print mode uses a monochrome fill path.
5. Draw the song picture at `(printRect.left+34,printRect.top-32)`, using personal2101 or the listening song's own icon.
6. Draw title with builtin heading font, black, in the print rectangle translated `(x+60,y-26)`. Use personal title or STRL101 listening title.
7. Draw score through1C73 using print-mode geometry and then pass the screen surface to resident739E printer-driver dispatch.
8. Free print resources, clear+A8A, and reconstruct the piano. Native `print-after-wait.png` shows the restored composition.

Geometry at music+833:

| Mode | Print rectangle | Note baseline | Note x parameter |
|---|---|---:|---:|
|Short|80,60,134,264|118|86|
|Long|68,6,166,317|106|28|

The print score uses eight-pixel staff spacing (versus six in normal advanced display). Long staffs start y69 and122; x6..316 inclusive. The print glyph branch uses the large clef/note shapes, even for the long book. Long title origin is `(66,42)`, personal icon `(40,36)`, instrument icon `(6,34)`. Native `print-capture/state/print-yes.png` is an ordinary-input blank long sheet with title `luna song`. It is captured20 callbacks after confirmation; waiting600 callbacks returns to the piano.

Resident739E selects a configured driver description, builds `PDRIVERS\\%Fs`, loads it, and passes the surface through the native printer API. Driver callbacks report offline/out-of-paper/timeout/I/O/write/not-ready errors with Retry prompts, or allow Cancel Print. No successful physical paper output was observed. For a browser implementation the recovered sheet can be rendered to a print canvas/PDF, then passed to the browser print system; do not claim a native DOS printer backend from that adaptation.

## Confirmation face animation and input

Resident285F, specifically2D63..2E30. Existing dialog geometry/lifecycle in the editor research remains correct, including **removing the musician before saving/drawing the panel** and redrawing the instrument after closure.

- Counter starts0, timer starts0, so phase0 is drawn immediately.
- At each timer expiration, Yes=`[86,87][counter&1]`, No=`[88,89,90,89][counter&3]`; then timer=12 and counter++.
- Both faces are opaque, at `(7,40)` and `(43,40)`, SHPL80. They share one phase counter; independent/random blinking is incorrect.
- A notification with no Yes choice draws a stationary face and skips the pair animation loop.
- Yes hit rectangle includes the face and button, `(40,7,80,41)`. Any other dismissal returns false; do not restrict acceptance to only the green label's small rectangle.
- Dialog background restoration removes the entire panel/artwork; it does not redraw the whole piano from scratch.

The prior static erase/random/copy frames happen to capture Yes87/No89. They are phase observations, not fixed images to use throughout the dialog.

## Audition and release semantics

Source `011B..01B5`, `17FB..1BC1`, resident65E4.

Physical keyboard mapping in ascending pitch order is:

```text
Z S X D C V G B H N J M , L . ; /
```

The 17 BIOS scancodes are exported in the numeric table. Key events move the original pointer to the center of the corresponding piano key, then enter the same press/audition handler as mouse input. Black-key hit order is a separate table at music+660; do not use sequential white rectangles over the black keys.

For mouse entry on a writable score page:

1. Press writes/replaces the current marker slot immediately, extends active span, draws held-key feedback and auditions the selected instrument.
2. While held, remain on that key while the pointer remains within its rectangle. Releasing **or leaving that key rectangle** ends its audition, restores its key image, and advances marker once (clamped at last slot).
3. If still held after leaving, re-enter the key-detection loop. Moving through another key therefore records another note and begins another audition without a fresh button press: native mouse glissando.
4. Native evidence: `c-held` has length1/marker0; drag while held to E produces length2/marker1; release produces marker2. These are C0 and E4 quarter notes, no insertion or duration change.

Listening mode, contents, and terminal pages audition without writing or moving the marker. Duration palette selection remains the earlier documented behavior: ordinary note click auditions; rest click only selects its duration; rest insertion requires a drag. Release calls1E8C to stop the active note/music state, regardless of natural sample completion. The digital instrument sample may loop while the press remains held according to its original sample flags.

The physical-key capture confirms entry at the mapped pitch, but the harness's key callback/scancode timing does not establish precise held duration: `physical-held` already has an advanced marker. Mouse press/drag/release timing above is directly observed; physical key-up parity needs a focused keyboard callback check before making a frame-accurate claim.

## Implementation checklist supported by this research

Contents view can now use exact rows/text/roman labels, all four listening pages, and seven personal pages. Use distinct terminal records. Wire Ctrl+erase to the two-book reset only. Implement title replacement as a modal state with the original width bound, and printable sheet state with dedicated assets. Drive confirmation faces with one12-tick counter. Complete mouse audition/glissando by treating key-boundary departure like release before entering the next key.

Precision still open: full independent print-sheet comparison, title acceptance without the harness's Enter re-entry, physical keyboard key-up timing, and actual printer-driver output. The contents region comparison and native state transitions are verified within the scope explicitly stated above.
