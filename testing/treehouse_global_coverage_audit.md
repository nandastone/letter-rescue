# Global controls and remaining user-facing coverage

Research-only audit, 2026-09-27. No runtime edits. Scope: original global input, activity control paths, persistence, and visible workflows versus `treehouse-demo/app.js`, `preferences.js`, `save.js`, and activity classes. This is a bounded missing-feature audit, not an assertion of exhaustive animation/audio parity. Implementation proceeded concurrently; findings below record the gaps identified and the original contract for the fixes.

## Sources and evidence

- Pinned unpacked executable: `testing/output/treehouse/disassembly/unpacked.bin`; main DS image `321D0`, shared state `31690`.
- Main and overlay2 listings: `testing/output/treehouse/research-resources/{main,overlay2}-disassembly.txt`.
- `D51:offset` means unpacked image `D510+offset`; unqualified main offsets are direct image addresses.
- Ordinary native input captures: `testing/output/treehouse/research-global-coverage/`. Each capture directory has action history, core/content/restore SHA-256 values, RAM, states and PNGs. No RAM was patched. Viewport observed in native RAM is `(top0,left0,bottom200,right320)`.
- Prior source investigations: `treehouse_settings_persistence_research.md`, `treehouse_writing_research.md`, `treehouse_nature_research.md`, `treehouse_music_editor_research.md`.

## 1. Keyboard-only pointer operation was absent

At audit start, `app.js` keydown supplied activity-specific shortcuts, such as Space playing music or rolling a die, and arrow keys driving the car. It did not provide the shared native pointer route. Therefore keyboard users could not reach arbitrary native canvas controls in nature, theater, room, maze, rewards or settings.

### Original movement, D51:57D3–58E1

The shared event service D51:58E2 calls this function before checking mouse/new key edges. It reads held scan flags at DS157E+scan:

| Axis | Positive | Negative | Simultaneous-key precedence |
|---|---|---|---|
| X | Right scan4D | Left scan4B | Right wins |
| Y | Down scan50 **or keypad5 scan4C** | Up scan48 | Down/keypad5 wins |

Both axes can move in the same service call. Step size is one pixel per active axis. Clamp X to0..319 and Y to0..199. BIOS0040:0017 bits0/1 select the Shift state. Original table at image30DD0+155 is four signed words `[1,1,3,1]`: steps `[1,1]`, delays `[3,1]` for normal/Shift. The routine moves the pointer, then waits this many native ticks. Holding Space without Shift adds five ticks: ordinary3, Shift1, Space+ordinary8. It does not rely on operating-system key repeat.

### Fresh events, D51:58E2–5993

The table at image30DD0+95 contains Escape, Enter, Space and piano characters `S D G H J L ; Z X C V B N M , . /`. It scans key codes0..95 and uses shared+A2A to emit once per fresh press. A held key must be released before its next activation edge. Mouse service D51:5BB0 emits for a fresh edge of either left or right button.

Enter/Space return nonzero events to each activity's ordinary pointer hit-testing; they are not universally “Play”, “Yes” or “Roll”. The shared confirmation loop main2D6E also activates according to pointer position. A modern shortcut may coexist, but it should not remove the original pointer workflow. Held Space is additionally consulted by movement/held-input services; dispatching an instantaneous synthetic click alone does not establish full keyboard dragging parity.

## 2. Nature clear controls lacked confirmation and clear-both

At audit start `Nature.clear()` immediately removed only the active scene. `app.js` did not pass Ctrl to `nature.click`, so the native clear-both path was unreachable. The parent began implementing this during the audit.

### Exact behavior

- **Overlay2:029D–0326, Ctrl+clear:** D51:5C52 checks BIOS Ctrl bit4. If either day/night count is nonzero, ask **“Send daytime AND nighttime animals home?”** (DS0CEA). Yes sets both counts to zero and restores the saved environment backdrop DS57C8 directly. It does **not** play the per-animal burst. If both were empty, show **“No animals to send home!”** (DS0D13), an acknowledgment dialog.
- **Overlay2:0329–0495, ordinary clear:** If the active scene is nonempty, ask **“Send all animals home?”** (DS0D2C). Yes processes animals from last index to first. Decrement active count before each animation. Center a1×1 rectangle on the animal bounds, expand it by12 horizontally and11 vertically, union this with the animal bounds for restoration. Draw TH900 relative23, wait4ticks, sound10034, draw relative24, wait4, relative25, wait4, then restore. Continue to the next animal. The inactive scene is untouched.
- **Overlay2:0498:** An empty active scene gives the same acknowledgment text at DS0D43.
- Neither path changes selected animal, its visible fact, filter or day/night selection. The post-Yes native frame `native-clear-result/state/both-yes.png` retains the Ant fact and header.

### Exact nature dialog recipe

This is main285F, scene1 branch28C6, **not** the decorated music dialog. Rectangle notation below is top,left,bottom,right exclusive.

- Base `(98,6,166,124)`. Fill white; its black boundary is already present in the nature text panel. No TH81–85 head/hands/feet decorations.
- Message rectangle `(99,7,125,123)`, FONT1 black, centered both axes. Single-line messages start at glyph y107. Ctrl text wraps as `Send daytime AND` / `nighttime animals home?`, glyph y102/112.
- Yes hit rectangle `(126,16,166,50)`; No `(126,80,166,114)`. Their width is34, wider than the colored buttons. Main2D84 tests Yes first. Any other activation returns false; an activation outside the base panel also waits for release.
- Yes face86/87 at x16,y126, No face88/89/90 at x80,y126, TH palette80, opaque. Phase sequences `[0,1]` and `[0,1,2,1]`; advance every12 native ticks. The timer begins at0, so initial update is immediate.
- Rounded colored button rectangles `(155,20,164,46)` Yes / `(155,84,164,110)` No, green EGA2 and red EGA4, black shadow translated+1,+1. FONT1 label centered at y156. Rounded rectangle excludes four extreme corners.
- Acknowledgment-only dialog: one **static TH86** face at x48,y126, red OK button `(155,52,164,78)`. Main2D3A/2DC6 skip the cycling branch when yes/no argument is0. Ordinary activation dismisses it; it is not necessary to click precisely on OK.
- Save underlying panel, render dialog, restore it when closed. Native references: `native/state/{empty-clear,single-clear,print-question}.png`, `native-ctrl/state/both-clear.png`.

`native/state/both-clear.png` is an intentionally retained unsuccessful short-Ctrl capture: Ctrl was released before the game sampled it, so it shows ordinary-clear text. Use the `native-ctrl` reference, whose action holds Ctrl before, during and after the mouse press.

## 3. Nature print control was a message-only stub

At audit start the print hotspot only announced “Use your browser's Print command…”. It neither confirmed nor invoked printing.

Original **overlay2:0276–0295** asks **“Print this Scene?”** (DS0CD8) through the same nature dialog. After Yes restores the dialog, it passes DS15F8 to main739E. This is the entire320×200 screen, including the visible UI and selected fact, **not** just the right-hand environment rectangle and not a separately laid out page. Native viewport values were observed directly in capture RAM. The original print preference and configured printer govern native dispatch. A browser print adapter can use this exact framebuffer with the pointer/dialog removed; original DOS printer-driver emulation is outside this audit's user-facing scope.

## 4. Valid offscreen room objects were rejected on restore

At audit start `save.js:loadObjects` rejected every record whose top/left was negative or bottom/right exceeded200/320. The native signed coordinate format permits legitimate offscreen object bounds.

Concrete ordinary native case: taking chalk calls main16F9→8CF4, which moves balloon type6 upward in two-pixel steps until it clears the expanded board rectangle `(38,52,99,157)`. Native `research-writing/chalk-capture/state/chalk-position` and `chalk-stroke` contain balloon bounds **(-1,95,37,124)**. Releasing chalk resumes motion rather than resetting the position. Main038A–053B normalizes object state on load while retaining the rectangle; the STATUS record stores signed bounds.

The demo's old validation dropped this otherwise valid type6 and then set `balloon.hidden=true`. A save taken while drawing could therefore permanently lose the balloon on reload. Accept the native signed position range needed for valid object motion, while retaining positive-size/type/count validation. Do not require the whole object to fit in the screen. This is source/native-position evidence plus a direct control-flow consequence of the validator; a browser save/reload reproduction was not run by this research agent.

## 5. Smaller visible differences

- **Nature fact selection:** `selectAnimal` always reset `factIndex=0`. Original overlay2:1DED–1E01 requests STRL5100+animal with string index0, the resource helper's random-entry convention. Thus repeated native selections can show different facts. The demo's readable Next Fact exposes all text, so this is selection behavior, not inaccessible content. See prior nature report1D3E/1E0E.
- **Chalk erase confirmation:** main167B→285F provides the original question dialog. `app.js` used browser `window.confirm("Erase Chalkboard?")`, while the readable Clear Chalkboard control directly cleared. The functional erase path exists; native presentation/consistent confirmation remained absent at audit start.
- Dialog keyboard shortcuts Y/Enter→Yes are modern additions. Exact original behavior uses the current pointer for any event; retain a way to perform this native route.

## Checked and not reported as missing

F1 contextual help, F2 preferences, Ctrl+S sound, Ctrl+V version, dedication help, music title input, songbook and STATUS import/export, activity option controls, and pagehide save exist. The native global preferences contain sound rather than a separate speech-enable preference; no unsupported missing “speech switch” is inferred. Browser read-aloud is a modern facility already present.

DOS printer selection and speed-optimization backend behavior are outside this missing-workflow audit. The debug-only Alt+S/Alt+M paths at main18CD are gated by DS55EC/command-line `debug`, so they are not ordinary user-facing omissions.

No additional completely absent activity was found in this bounded pass. This conclusion does not certify every activity transition, random stream, renderer or cancellation path; existing focused audit reports remain the evidence for those details.

## Follow-up: original chalk confirmation and nature erase frames

### Chalk lifecycle and exact room dialog

Native ordinary-input reference: `research-global-coverage/chalk-question/state/chalk-question.png`, restored from the existing writing route's `eraser-capture/state/tool-returned.state`, then clicking room hotspot25 at(54,90). Scene id5 was read from native RAM. `capture-chalk.py` records the complete route.

Main **167B–16F6** does more than open a question:

1. If the calendar is already open (DS5262), close it through341E.
2. Call8CF4 with avoidance rectangle DS021E and direction0 to move the balloon away from the calendar region.
3. Call **3515(0)** to unroll a **blank** calendar shade. Main328A fills white above the moving lower edge, draws TH1201/SHPL1200 transparently at `(162,height)`, and skips date text. Heights38,48,58,68,78,88,98, each2 native ticks; sound10031. The settled white rectangle is TLBR `(28,162,98,283)`; roller asset is121×12 at `(162,98)`, with transparent pixels retaining underlying room artwork.
4. Main285F shows the question with yes/no1 and music-special0.
5. After either answer, close the calendar through341E: heights88,78,68,58,48,38,28, each2ticks, restoring the captured room background.
6. On Yes, run the chalkboard balloon-avoidance call, fill only the drawing clip with the eraser color, and update retained board via6350. Finally resume room scheduling throughBC43.

The **scene5** branch of285F at28F1 gives a flat white base TLBR `(29,168,87,278)`. There are no outer music decorations and no new border.

| Part | Original geometry |
|---|---|
| Message rectangle | `(30,169,46,277)` |
| Text | `Erase Chalkboard?`, FONT1 black centered at x223; glyph top33 |
| Yes face | TH86/87, palette80, opaque, x178,y47 |
| No face | TH88/89/90, palette80, opaque, x234,y47 |
| Yes hit rectangle | `(47,178,87,212)` |
| No hit rectangle | `(47,234,87,268)` |
| Yes rounded button | `(76,182,85,208)`, EGA2 green |
| No rounded button | `(76,238,85,264)`, EGA4 red |
| Button shadows | Black translated+1,+1 |
| Label glyph top | 77 |

The same12-tick face sequences apply. This capture matches faces87/89. `compare-art.py` builds the panel from original resources and text glyphs: **zero different pixels** across every pixel of the white panel x162..282,y28..97, plus every nontransparent roller-art pixel. It deliberately does not claim independently reconstructing the room pixels visible through the roller. Output: `chalk-panel-independent.png`, `chalk-panel-diff.png`, `art-comparison.json`.

### Nature single-clear transient evidence

`capture-burst.py` restores the ordinary single-clear question, moves to the Yes face, and records every callback around acceptance. Full original frames are under `research-global-coverage/nature-burst/state/`.

The placed Ant rectangle is TLBR `(94,215,104,227)`, center `(221,99)`. All three TH923/924/925 burst resources are22×18 and draw centered at **(210,90)** with SHPL900. They do not use the expanded restoration rectangle's top-left as sprite origin.

| Native frame | Asset | Nontransparent pixels | Different original-art pixels |
|---|---|---:|---:|
| after-01 (also02..04) | TH923 |94|0|
| after-06 (also07..09) | TH924 |75|0|
| after-10 (also11..14) | TH925 |25|0|
| after-50 | Settled scene |—|—|

Source uses4 native ticks for each phase, not4 video callbacks. `after-05` contains an intervening presentation and is not the representative second frame.

**The first burst overlays the still-visible animal.** Overlay2:0427 calls main6C2E directly after decrementing the logical count; it has not restored that animal's background yet. Six Ant pixels remain visible outside TH923's foreground in this capture. The next two stages call overlay2:0EC0 at0451/0470, which restore/rebuild the region before drawing TH924/925. Their native region differences are exactly the burst's foreground, with no Ant pixels. Rendering from the shortened object list therefore needs to retain the removed object behind the first burst only. The fact panel and Ant header persist throughout and in the settled frame.
