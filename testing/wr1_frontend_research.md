# Original front end, startup and ending â€” 2026-09-09

Source: `testing/output/normal-play-20260909/WORD/WR1.EXE`, SHA256
`b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`.
This investigation reads the original bytes and disassembles with Capstone in
16-bit mode. No original file was modified or guest state injected. Addresses
below are executable **file offsets**. Initialized DS begins at file `0x24f50`;
far code addresses map to `0x2a00 + segment*16 + offset`.

The companion [`data/wr1/frontend.json`](../data/wr1/frontend.json) contains the
original strings, positions, menu actions, page tables, asset sequences and
profile formats. It is extracted from initialized data and instruction operands,
not from screenshots. Native captures remain necessary to verify palettes,
illustrations, GX rectangle details and complete presentation timing.

## Main menu

Function `0x7670`, selection in `DS:2500`. Thirteen far string pointers at
`DS:24c8`, text at `(86,40+10*i)`. Cursor is the `*` string at `DS:3d77`, drawn
at `(74,40+10*i)` in color 4. Up/Down (`0xc8`, `0xd0` in this input interface)
wrap between 0 and 12. Enter executes current selection. Both cases of each
letter shortcut immediately select and execute the corresponding action.

| Index | Label | Key | Handler |
|---|---|---|---|
|0|Play game / Back to game|P, B, Escape|`0x78fa`|
|1|Instructions|I|`0x7912`|
|2|Difficulty|D|`0x7bd4`|
|3|Keyboard Redefine|K|`0x7d5b`|
|4|Joystick|J|`0x7d63`|
|5|Story|S|`0x7e18`|
|6|Ordering|O|`0x7ece`|
|7|Call our BBS|C|`0x7e56`|
|8|About the game|A|`0x8145`|
|9|High score|H|`0x8252`|
|10|New player|N|`0x825a`|
|11|Run demo|R|`0x828f`|
|12|Quit|Q|`0x8346`|

Menu background helper `0x88e3` fills the page with EGA index 11 and blits
buffer 7 (MENU.WR), inclusive source rectangle `(0,0)..(197,175)`, to `(60,10)`.
It selects text background index 15 and foreground 0. Text goes through
`0xa333` (`set text position`, then GX string draw), the same 8-pixel glyph
path as the verified level-title card. It does not blit FONT.WR glyph sprites.
The background atlas may have padded blank rows/columns beyond decoded PCX
content; do not infer source crop size solely from PNG dimensions.

Play changes the first label to `Back to game`. New Player resets it to
`Play game` after the name/character flow. Calling menu with argument 1 forces
an initial lowercase `o`, opening Ordering immediately (`0x76f6..0x7701`).

## Selectors, controls and help

Difficulty (`0x7bd4..0x7d58`) uses `(86,64/76/88)`, cursor x74, E/M/H shortcuts.
Up/Down clamp to 0..2. Escape restores prior difficulty, then still calls
`0x8841`. On Medium this consumes another random draw even when cancelling.
The difficulty heading is a saved MENU.WR rectangle `(26,94)..(171,119)`,
captured at `0x9f39..0x9f56`; redefine uses `(26,127)..(171,152)`, captured at
`0x9f5b..0x9f78`. Both are applied via GX saved-rectangle call `0x14e6:4` with
screen region `(80,10)..(227,36)`.

Redefine (`0x857f..0x86a3`) asks Right, Left, Up, Down, Slime, in that order.
Prompts are red (index 4), at x72 and y48/64/80/96/112; captured key-name text
is at x224. Helper `0x8531` accepts make scancodes below `0x59`, except `0x2a`
(Left Shift); it does not reject duplicates or reserved gameplay keys.
Names come from the far-pointer table `DS:2502`. New bindings write immediately
to DS:1b6,1b7,1b4,1b5,1b8. `Save this? (Y/N)` at `(80,136)` changes DS:1b9,
the custom-control activation and persistence flag. The ISR at0xc758 checks it before matching any custom scan bytes: N therefore disables custom mappings and uses defaults, even though the newly captured bytes remain in memory.

Joystick (`0x7d63..0x7e15`) asks `Use a Joystick? (Y/N)` at `(68,68)`.
Y (case-insensitive) sets DS:178=1, shows `Center Joystick and press 'J'`
at `(46,68)`, then **any key** proceeds to read axes 0 and 1 as center values
(DS:9776 and DS:978e). Any non-Y response disables joystick. This is native
hardware calibration, not evidence for modern gamepad deadzone thresholds.

Instructions: 5 pages of 16 strings at DS:1328, x16,y16+10*i.
Ordering: 10 pages at DS:10a8, same positioning.
About: 2 pages at DS:1468, x12,y16+12*i.
BBS: 14 strings at DS:14ec, x16,y16+12*i.
A blank string still occupies its row. All strings and spacing are in JSON.
Pages use background 11 and an inclusive framed area `(4,4)..(315,195)`,
text foreground 1/background 15. Continue prompt is red, `(48,180)`.
Any key advances; Escape leaves the page sequence. Instructions and About
also draw original sprites; those blits are at `0x7999..0x7b94` and
`0x81a2..0x8206`. Ordering illustrates pages at `0x7f5c..0x812c`.
The text tables alone do not recreate those illustrations.

Sound selector `0x8995` uses cursor x104,y82+12*i and three choices:
All Sound, Music off, All off. Numeric keys 1/2/3 choose immediately;
Up/Down clamp. Original settings are DS:f24=2/1/0 when AdLib is present.
The source Escape branch restores DS:f24 temporarily but the common exit
then writes the currently highlighted row again; do not assume rollback.

HELP.WR is loaded into buffer6 at `0x9d92..0x9da4`; KEY.WR goes into buffer5
at the metadata coordinates DS:31b/329 (`0x9d6a..0x9d80`). They include gameplay
help overlays, not a new replacement font. `0x87ad` blits HELP source
`(0,0)..(167,175)` to `(72,16)` and waits for fresh input. `0x87f7` blits source
`(192,0)..(319,191)` to `(192,0)`. The sound popup is assembled from HELP regions
`(192,0)..(319,40)` and `(192,152)..(319,191)` at `0x9de6..0x9e27`, with its
original sound-choice text written into that saved image.

## Startup and story

The initialization path at `0x99b1` sets graphics mode, initializes image
palette data from WR1.7, then progresses startup screens while loading assets.
`0xa16f..0xa2cf` is the startup screen state machine. Four images:

| Stage | Image | Position | Display page | Time until next stage |
|---|---|---|---|---|
|0|WR1.20|(60,30)|0|strictly greater than 7 DOS seconds|
|1|WR1.21|(0,0)|1|strictly greater than 12 seconds|
|2|WR1.22|(32,12)|0|strictly greater than 8 seconds|
|3|WR1.23|(60,30)|0|strictly greater than 0 seconds|

Times are integer DOS wall-clock seconds; input can advance early, and loading
work overlaps the sequence. Stage0 is forced by setting baseline time 21 seconds
in the past (`0x99d5..0x99e7`). Stage1 overlays V2.0 `(270,174)`, APOGEE `(94,172)`
in index14 and SHAREWARE `(16,8)` in index12. Thus blindly adding nominal waits
serially after loading would reproduce neither original ordering nor timing.

Name entry `0x8ba8` initially loads WR1.24 on page1. Depending on load stage and
whether this is initial startup, it waits until total elapsed time18seconds or
input before flipping to this card. Input is `(48,126)`, maximum8characters.
It accepts printableASCII, changes spaces to underscores, title-cases letters
(first uppercase/rest lowercase), supports cursor motion and editing. Empty
input repeats. A sole Q (case-insensitive) quits. Name is stored at DS:850a.

No matching save overlays WR1.25 at `(16,44)` and selects girl by default.
Left picks girl1, Right boy0; Enter accepts. Girl rectangle is
`(41,88)..(74,129)`, boy `(123,88)..(156,129)`. Selected outline index14,
unselected index4, GX outline styling `(0xffff,3)`. These are rectangles,
not cursor arrows. A restored profile overlays WR1.26 in the same position,
with score centered at x103,y98 and level number centered at x103,y132.

Story handler `0xa07a` displays WR1.30..WR1.34 full-screen in order. Menu Story
starts its local index0. Key input advances; Escape marks sequence skipped.
Its initial stage also starts automatically after elapsed time exceeds6seconds;
later normal story pages await input. This same routine is interleaved with
initial startup loading; it is not the level-completion ending.

## Saves and scores

Profile writer body `0x49ff..0x4bdf`; reader `0x8d60..0x8ec8`:
`<name>.wr1` is the current episode save. Reader tries `.wr1`, `.wr2`, `.wr3`
so a returning name from another episode can preserve identity/options while
resetting episode-specific progress.

Packed variable-length fields, all integers little-endian:

1. u16 zero-based level; u16 gender; u32 word-list cursor; u32 score.
2. Seven NUL-terminated current word strings.
3. u16 difficulty; u16 save-custom-keys flag.
4. If flag nonzero: five raw scancode bytes, Right/Left/Up/Down/Slime.
5. u16 joystick-enabled flag.

There is no live actor/velocity/RNG/collected-item snapshot. Resuming reconstructs
a level from saved words and cumulative progress. Original read requests up to
81bytes, but the writer writes only its packed used length.

High score file `high.wr1` reader `0x929d..0x93c2`, updater `0x93c3..0x9644`:
ten records of NUL name (max8chars) followed immediately by 32bit score. Maximum
length130bytes; no fixed13byte padding per record. Names stored at DS:a92a,
scores DS:b891. Updater finds existing names case-insensitively and retains the
higher score; otherwise replaces bottom slot when eligible. Descending bubble
sort swaps only strictly greater scores, preserving tie order. Highscore display
`0x86a4` shows positive entries only, names x68, scores right-aligned at248,
y44+10*i. Title `High Scores` is `(106,28)`; panel `(60,20)..(254,160)`,
foreground15/background9, surrounding page11.

## Episode ending

At `0x3f9e`, incrementing level index to15 in a normal game takes the original
ending. Native demos bypass it. If music exists, `(level_index+1)%3` selects
WR1.5. The sequence is:

1. WR1.10 displayed on page0; WR1.11 preloaded on page1; wait key.
2. Display WR1.11; preload WR1.12 on page0; wait key.
3. Display WR1.12; reset levelindex0; advance word-list via `0x7170`;
   update highscores via `0x93c3`; set score0; wait key.
4. Call menu with argument1, opening Ordering automatically; return to play flow.

Evidence spans `0x3fb6..0x4098`. The embedded 80-column DOS text thanks/order
screen elsewhere in DS is a separate process-exit presentation, not these three
EGA episode-ending images.

Run-demo menu iterates map indices from DS:a0:
4,1,10,12,14,15,2,5,8,11,9,3,6,13,7 (one-based here). It begins from the table
slot indexed by current zero-based level, wraps after15, and interleaves the
WR1.21 title and story routine between demos (`0x828f..0x8343`).

## Boundaries of this evidence

Menu decisions, source text tables and positions, profile layouts and image
ordering above are decoded from original instructions. No native comparison
of all these screens has yet been performed as part of this research subtask.
The current JSON explicitly leaves page illustration draws incomplete. Pixel
parity requires retained native screenshots and original palette selection;
startup cycle-exact delays and DOS joystick hardware behavior are not claimed.

## Completed page-illustration extraction

The `illustrations` dictionary in frontend.json now covers every Instructions,
Ordering, About and BBS page, including explicit empty pages. This supersedes the
initial text-only limitation above. Each command contains its source file offset,
source rectangle or sprite-table record, destination, and opaque versus masked
compositing. Instructions dispatch table is file0x7999 (four illustrated pages;
page4 has none). Ordering dispatch table is0x7f5c (eleven entries, but the loop
only reaches indices0..9). About only illustrates page1.

Player illustrations use frames11 and21 of the **selected gender**, not a fixed
boy/girl. Sprite source metadata is22bytes per record; the body/AND-mask pair must
retain the original destination AND mask then OR body operation. Existing
verified extracted sprite assets may implement these operations with alpha.
Opaque atlas/page copies must not be chroma-keyed.

Instruction page0 uses the currently loaded word panel for slot0 and pictures
for slots0/1 (native buffer4). Its question icon is STATIC.WR(208,40)..(231,63).
Page1 copies the book tile from current BACKn.WR(304,176)..(319,191); page3 copies
the letter tile at(288,176)..(303,191). These depend on the loaded level context.
Page3 also explicitly copies native buffer2(0,0)..(15,15) to(156,120).
Follow-up native capture corrected the initial assumption that CHARS.WR remained
there: `0x730a..0x75ad` repopulates this buffer with mystery-letter tiles. The
first tile is the first current mystery letter, composited on the level's
background color. For the retained native session that is C from `cup`.

The common white panel primitive is inclusive(4,4)..(315,195), style3,
foreground/border1, fillpattern0/color15. Native screenshots still need to
validate the chosen decoded image palettes and all GX rendering edge details.

## Why original demo-start controls can suddenly miss

A concrete source-dependent speed difference was found in DOSBox Pure:

- `dosbox_pure_libretro.cpp:2716..2724` searches the entire content path for a
  release year such as `(1992)` or `/1992/` when content metadata has no year.
- `DBP_CyclesForYear`, near line626, maps year1992 to exactly **27000** cycles.
- `DBP_SetRealModeCycles`, line642, applies that value for real-mode AUTO CPU
  speed when a content year is known.
- `src/cpu/cpu.cpp:2805` instead uses **3000** when AUTO has no such year.

The earlier Downloads path includes `Word Rescue (1992)(Apogee Software Ltd)`;
the task copy `testing/output/normal-play-20260909/WORD` has no matching year.
This can make identical loading work take nine times the emulated elapsed time,
so fixed-frame name/menu controls reach different screens. This is a source-based
causal explanation, not a measurement of the currently failing process's
CPU_CycleMax. Test with a separate, immutable-input copy under a `/1992/WORD`
path and AUTO before changing recorded controls or gameplay timing assumptions.

For isolated per-run RetroArch core options, local source
`testing/output/retroarch_69a4f0e_runloop.c:1147..1233` searches game/folder,
then per-core, then global options. At1535..1539 the caller passes
`!settings->bools.global_core_options` to this per-core selection. Therefore an
appended task-owned config should set all three:

```
game_specific_options = "false"
global_core_options = "true"
core_options_path = "D:/absolute/task/output/run.opt"
```

Without the first two, merely setting core_options_path can still load the
user's existing per-core file. The existing user DOSBox-pure.opt was read only;
it currently specifies cyclesauto, no maximum, scale1.0. No user config changed.

Do not rely on `dosbox_pure_cycles="27000"` as an options value: the core's
published enum contains26800, not27000, although its low-level parser accepts
integers. RetroArch can reject out-of-enum values. The filename-year AUTO path
is the original source mechanism producing the observed27000-cycle setting.


## Final coordinate and gameplay-popup checks

PCX load argument order differs from the text wrapper. At0x131f1 the loader
forwards BP+10 then BP+8. EGA width clipping0x121a2 usesBP+10 as x; height
clipping0x121ed usesBP+8 as y. Therefore new/resumed player overlays are
**(16,44)**, and startup20/23 are(60,30), startup22(32,12). Earlier reverse
assignment was incorrect; JSON and the tables above have been corrected.
Rectangle and glyph coordinates retain their existing order.

W word list is built at0x6c5b..0x6cdb into the right part of HELP buffer6.
For i=0..6: current picture frame0 at(287,7+26*i),24x24, and its word panel
at(200,10+26*i),72x18. Word panels originate in buffer4 and use blackborder,
whitefill, BIOS textcenterlocalx32,y4, plus extra bottomliney16 and leftlinex1
(0x633e..0x641c). Display0x87f7 copies(192,0)..(319,191) to(192,0), stops
PCspeaker, waits for any fresh key and pauses gameplay while visible.

Speed controls are raw scan0x0d/0x4e(Equal/keypadPlus) and0x0c/0x4a(Minus/
keypadMinus). Faster decrements the IRQ wait thresholdDS8e8f only whenpositive;
slower increments the unsigned16-bit threshold without an explicitmaximum.
Initial threshold8; each make event changes once, keyboardautorepeat can repeat.
Demos ignore these flags. Evidence keyboarddispatch0xc7e2 andhandlers0xc89d/
0xc8ad, mainloop0x35ab..0x35f4. This controls admitted gameplay frequency,
not jump acceleration or render scaling.

Q confirmation0x70bf..0x716f draws inclusivepanel(60,58)..(256,84), blackborder,
cyanindex11fill, blacktext. Lines: `Press 'Q' to quit` at(88,62),
`'ESC' to return to game` at(64,72). It clears initiatingQ, then freshQconfirms,
Escape cancels; otherkeysdo notdismiss. It waitsforreleasebefore returning.

GX rectangle helper0xf174 handles style3 as outlineplusfill; style2 fills only.
For usual1pxline, horizontal boundaries include bothcorners, verticalboundaries
omitsharedcorners, then interior is inset1pixel and filled. Border color is
currentforeground, fillcolor is separately selected. Wider lines center around
the nominalboundary: halfwidth extends outward, then interiorinset grows.
Characterselector temporarily chooses3px lines at0x9004;0x9146 restores1px
before return, so subsequent menu/help panels normallyhave1pxborders.


## Implemented frontend and measured coverage

The Godot frontend now includes all thirteen menu actions, original startup
and player cards, five story pages, three ending pages, help/words/sound/quit
popups, controls, native profile/high-score files and the repeating attract loop.
Gameplay remains suspended in the same scene while menus or demos run.

`testing/test_wr1_frontend.py` compares retained immutable DOSBox PNGs with
source-driven rendering. The manifest in `testing/fixtures/wr1_frontend/`
records image, acquisition and replay hashes. Full-page checks currently cover
46 screens, except sound/quit/words which compare their complete popup rectangles
against a live native game background. Functional coverage includes name editing,
profile binary round trips, other-episode option import, difficulty, sound,
remapping, joystick menu flow, pause/resume and the ending's return to level1.
A graphical run verifies the actual viewport presents the menu, in addition
to testing the image-generation routines.

Native captures corrected these concrete details:

- PCX x60 loads at x56 because the EGA loader addresses byte columns. General
  rectangle blits, such as MENU.WR at x60, retain exact pixel positioning.
- The old extracted PCX palette expands 85/170 to87/171 in some files. Runtime
  normalizes those colors; yellow entry6 becomes brown, except WR1.21 which
  reassigns it to bright red. Native comparisons verify those remaps.
- Native name cursor is a10x9 hollow outline. Character selection uses3px
  outlines centered on the specified rectangles.
- Sound title is(138,70); choice strings start atx114. Cursor remainsx104.
- Joystick question is a red-outlined cyan panel(36,58)..(283,84) on gray7,
  with red text, rather than a normal menu panel.
- Remapped key names come from89 original far pointers atDS:2502 (`Rt`,
  `Lft`, `Up`, `Dn`, `Spc`, etc.), preserving the red prompt color.
- The BIOS font extraction originally retained only128 characters. The local
  DOSBox `int10_font_08` table supplies the remaining128, after validating the
  first1024 bytes against the measured native font. Its extended pound glyph
  now matches the UK Ordering page; metadata records both source hashes.

Runtime demos live under `data/wr1/demos/`, generated by
`tools/build_wr1_attract_assets.py`. They contain only decoded WR1.D controls
and one initial level/entity/music/video checkpoint. No expected completed
states, future timestamps or images are packaged. The original fixture files
remain the independent regression references. The attract test exercises a
natural demo11 ending, the7-second title and5x10-second story interlude,
all fifteen demo starts, and restoration of the identical paused scene/state.
Its graphical variant checks the restored viewport pixels too, and also starts
from the initial menu with no live game and cancels during a title interlude.

Loading delays are deliberately outside parity. The startup presentation uses
nominal source waits and an Apogee initialization card; it does not emulate
concurrent DOS loading. Modern gamepad calibration/deadzones are an adaptation
and have no physical-controller verification. Names use a safe DOS-compatible
alphanumeric/underscore subset of native printable ASCII. Before initial play,
instruction illustrations use the available word set; a live game supplies its
actual mystery letter/background. Menu-history-dependent pre-game random draws
and extreme zero-delay speed remain outside the measured demo coverage.
The three ending assets and their gameplay transition are source-derived and
integration-tested, but have no independently captured native ending sequence.

Reproduce supplemental checks with GODOT set:

```
python -m unittest testing.test_wr1_frontend testing.test_wr1_attract testing.test_wr1_audio testing.test_input_replay
python tools/build_wr1_attract_assets.py
python tools/extract_wr1_frontend_assets.py --game-dir testing/output/frontend-20260909/1992/WORD
python tools/extract_wr1_font.py --exe testing/output/normal-play-20260909/WORD/WR1.EXE --bios-source testing/output/dosbox-pure-trace/src/ints/int10_memory.cpp
```

The earlier `screens-fixed`, `screens-mapped`, `screens-native`, `menu-native`
and `main-native` acquisitions in the task output directory used a no-year
path and therefore the slower AUTO CPU default. They are debugging artifacts,
not evidence for the retained menu comparisons. The later `/1992/WORD`
acquisitions reached the intended screens with the established startup inputs.


## Final keyboard dispatch and profile checks

Source `0xc762..0xc7c8` checks custom Up, Down, Right, Left, Slime in that order;
each match jumps to the IRQ epilogue. Unmatched scans continue into the default
dispatch table. Therefore custom S/W suppress Sound/Words shortcuts, duplicate
bindings have first-match priority, and unshadowed defaults stay available.
The runtime now follows this ordering; real InputEvent tests cover all three.

The table at `0xc7e2` has a surprising mismatch with HELP.WR: Ctrl scan29 and
Up scan72 both target `0xc8d6`, writing DS:190 (Up). Alt scan56 and Space scan57
both target `0xc8bd`, writing DS:19e (Slime request). The observation-only
`modifiers-native.json` acquisition confirms it: held Ctrl at frames820/850
sets Up=1 and raises worldY from208 to184/144; held Alt at1130/1180 keeps Up=0,
worldY208, and reaches the slime pose11. That capture and its source/core hashes
are retained in `testing/fixtures/wr1_frontend_controls.json`. Runtime follows
the executable; the inaccurate original help artwork remains unchanged.

The last screen fixtures add sparse native high-score rows and the post-New
Player menu. Native selection remains at row10 after changing player. Loading
an existing player from the live menu returns directly to that menu (the
startup resume card remains part of initial presentation). Functional tests
load a saved level5 profile with score12345 and verify that tearing down the
previous game cannot overwrite it.

The frontend capture builder supports polled gamepad/analog mappings, including
J/I/K/L on the Generic Keyboard's right stick. Raw N/Y BSV callback events in
one exploratory recording did not reach the guest with the null host input
driver; those events are not treated as evidence of successful guest input.
The retained screenshots show the states actually reached. Calibration's Y
branch has functional Godot coverage, not native hardware parity.

F1 through F10 also invoke native gameplay help (dispatch table0xc7e2), unless
a custom action shadows that scan. The clone preserves those aliases.


## Completed frontend/audio regression, 2026-09-09

The final full sequential run is
`testing/output/parity/frontend-final-20260909/report.md` (JSON alongside it).
All15 demos completed:22460/22460 gameplay states, all consumed controls,
all15 terminal states/timings, and196/196 sampled viewport images match.
There are no missing updates or execution/evidence errors. The strict command
exits1 for the unchanged timing residuals: demo6 tick1474 (9242/9241), demo13
tick662 (4497/4496) and tick956 (6214/6213), native/clone counters respectively.
No offsets or residual allowlists were applied.

The separate frontend suite has46 exact native screen/popup comparisons and
checks actual viewport composition. Integration tests cover the real final-level
exit handler, all three ending pages, restarting level1, loading another saved
player, remapping priority/default fallbacks, and isolated save destinations.
Attract tests cover natural completion, interludes, all fifteen starts, visible
restoration with and without a suspended game, and cancellation before deferred
launch. Mixer, replay roundtrip, OPL, recap and seeded-startup checks also pass.
The detailed limits above still apply; this is not whole-game or PCM perfection.
