# The Treehouse — Godot port

The target runtime is Godot 4.6, following the Word Rescue and Math Rescue
reconstructions. Desktop and browser builds execute GDScript. The earlier
`treehouse-demo` JavaScript game remains a development reference during migration.

## Run

From the repository root:

```powershell
./treehouse-godot/play.ps1
```

This extracts the pinned original resources, imports the project and launches
Godot. Set `GODOT` to select an engine executable. `-ImportOnly` stops after
import; `-BuildWeb` exports to `treehouse-godot/build/web/`. Serve that directory
with an HTTP server to play the Godot browser build. The original reference
browser server at port 8767 is not replaced by these commands.

## Implemented so far

- Independent indexed graphics, palette recoloring, clipped drawing, bitmap text
  and original cursor.
- Sixteen-slot SCR interpreter, fixed-point movement, shape cycling, animation
  display events, sound requests and callback signals.
- Character selection, original entrance sequences for both children, rotating
  credits, and initial room composition with the current date and clock.
- Mouse/touch selection, Enter/Space activation and Escape back to selection.
- Original digital samples plus source-generated title, selection, Home and four
  frog FM tracks; independent channels, original loop flags and activity stops.
  Native waveform and wall-clock audio parity remain unfinished.
- Calendar sheet, day browsing, original date/time speech fragments, moving
  clouds, spider, nest and chirp sequences.
- Original chalk brush, eraser, cursor, tray and erase confirmation; mouse/touch
  strokes, original keyboard-pointer cadence and focus-loss release.
- Balloon following, chalk/environment clearance and short-click color/pop cycle.
- Persistent character poses, queued actions, SCR callbacks and need warnings.
- Retained-character room/yard return, yard cloud/sun/birdhouse/pond/window,
  squirrel hollow, three nut throws, squirrel animations and interruptible sign.
- Held-object dragging, surface placement/falls, fruit and pillow offers,
  sleep/wake, basket/worm/bird handoffs, nut bags/piles, prize-object interactions,
  food consumption and automatic room/yard events.
- Original room/music teleport and return, including waking a sleeping child.
- Listening books, both score sizes, all 17 piano keys, pitched original samples,
  song playback/repeat/tempo, page/contents navigation and idle animation.
- All seven instrument families, 42 instrument selections, facts and auditions.
- Nature filters, animal facts, day/night collages, blinking animals, dragging,
  erase confirmation and persistent collage saves.
- Animal guessing against another child or the robot, question definitions,
  help, wrong guesses, victory, revealing both animals and shared prize delivery.
- All four telescope views, original approach/return, replay boundaries and the
  robot's earned-prize shelf.
- Money and Chip board games, original options/goals, human/robot turns, road
  movement, payments, carrying/borrowing, spoken feedback, endings and prizes.
- F1 contextual help, all 26 original help texts, theater notebook help, F2
  preferences, Ctrl+S sound and Ctrl+V version messages. Settings survive reload.
- Shared STATUS.DAT persistence and F9 file controls for importing/exporting
  STATUS.DAT and both personal songbooks in the original SONGS.DAT format.

The personal songbooks now support composing, note/rest editing, titles, copy,
random songs, erasing, print-sheet preview and persistent SONGS.DAT saves.
The title logo and looping selection music now use source-generated FM audio.
Integrated startup timing, other FM tracks, physical printer verification,
audio mixer parity and strict presentation timing still require work.
Escape now returns from the room or hollow to the retained-character yard.
Click the ladder to return indoors. The current port starts at the original logo, then reaches character selection.
All main activities are now playable in Godot; the remaining integration and
strict fidelity work is tracked in the ledger.

## Evidence

### Selection-music checkpoint

The live preview includes looping selection music with the original pitch bends,
separate digital effects, sound-off/on controls, and music through the child
entrance. All 47,366 native register writes and timer ordinals match; 776 pitch
bends and the start of the following loop are included. The complete initial
selection screen matches the original. Its first poses are composed off-screen
in DOS; there is no additional preview animation missing.

An actual Edge session runs beyond a full music loop and verifies audible output,
mute silence and restored sound. Title and selection WAV imports preserve their
generated PCM bytes without lossy compression. Actual DOS waveform and elapsed
audio timing still differ or remain unverified; other FM tracks, full-title
browser activation and existing gameplay fidelity failures remain open.

Export: `godot-selection-web-build-a`, PCK SHA-256
`318ba0882ccfa630ff41db8eeed5a6e21209644df18cc14300e1871c2a04dc82`.
Reports: `selection-music-proof-b`, `godot-selection-audio-web-a`, and the ledger.

### Title-logo checkpoint

The preview at <http://127.0.0.1:8768/> now starts with the original animated
logo, generated FM music and presents reveal. Press a key, click or touch to
skip. All 82 distinct complete title frames match native boot frames in order;
all 1,124 title FM writes and timer-interrupt positions match. Ten real Edge
title/input checks and eleven fresh-save checks pass. Pre-selection animation
and music, unshifted display timing and output-waveform parity remain open.
See `title-native-proof-a`, `godot-title-web-a` and the remaining-work ledger.

Regenerate music with `tools/treehouse/render_title_music.py --install`; its
compiler/output arguments and attribution are documented in
`tools/treehouse/opl_standalone/README.md`. Godot builds verify the WAV manifest.

### Fresh-profile checkpoint

The preview at <http://127.0.0.1:8768/> now initializes a new profile from the
original missing-STATUS defaults: first listening page, empty animal scenes and
theater, human opponents, lowest board goals, and the original three room
objects after normalization. Six distinct maze songs are generated from the
session RNG. Existing STATUS files still restore; older Godot profiles migrate.

Two independent DOS cold boots with STATUS removed produce identical saved
data and selected images. In an isolated seed-controlled Godot comparison,
all 2,282 saved settings/activity bytes, active object fields and the complete
preferences panel match. There are 21 passing component/native checks and 11
real Edge first-profile/reload/native-import checks. The existing save suite
retains 81 checks, browser file interchange 22, and printing 52; the print route
explicitly imports the packaged profile through the normal file controls.

The comparison does not assert equality for live object deadlines, unused
object records, or complete cold-boot RNG/timing. The later title-logo checkpoint adds the logo and separate music; full
pre-selection startup integration remains open. A lone existing SONGS.DAT is
currently treated as a legacy profile to preserve earlier Godot creations;
the native missing-STATUS path with that separate file needs further integration.

Immutable export: `testing/output/treehouse/godot-fresh-web-build-a/`.
PCK SHA-256: `79219c560f8e7aa935ff9c517eebe6efbd41086d7d29ab1a2c08dcf53075c72b`.
Evidence: `fresh-startup-native-c/run.json`, `fresh-startup-repeat-a.json`,
`godot-fresh-startup-c/report.json`, `godot-fresh-web-a/report.json`, and
`godot-fresh-delivery-a.json` under `testing/output/treehouse/`.
All nine served file hashes match; the game remains incomplete.

### Print-output checkpoint

Play at <http://127.0.0.1:8768/>. Click the original printer in music or nature,
confirm Yes, then press **F9** while the picture is displayed. **Save picture**
downloads the complete original 320×200 image as `TREEHOUSE.PNG`. **Print picture**
opens browser printing with the same image; utility controls are omitted from
the printed page. Escape returns to the preview, then Escape again returns to
the activity. Outside a print preview, F9 retains the game/songbook file controls.
Desktop provides PNG saving and a standalone browser page for printing.

Passing: 47 production control/PNG checks; 52 real Edge output checks, including
all downloaded pixels, repeated downloads, print CSS and a real print event for
each of four previews; 225 editor/rendering cases including three complete DOS
print sheets. Save-file interchange retains 22 browser checks, preferences/help
17, editor/nature controls 32/56, and startup two native frames plus 356 SCR
comparisons. Printed media screenshots have been visually inspected.

Headless Edge leaves its print request pending without an `afterprint` event;
the test uses a fresh document for each print request. Interactive printer-dialog
completion, desktop native dialogs and physical paper output remain unverified.
The pinned DOS installation has no configured printer backend, so this does not
claim equality with a DOS printer's physical output or its printing duration.

Immutable export: `testing/output/treehouse/godot-print-web-build-a/`.
PCK SHA-256: `9e474ebdc752c6a5c0c2639f8b0cbb7697e4b07093fe8a421c2038be70e3a6c3`.
Evidence: `godot-print-controls-b/report.json`, `godot-print-web-c/report.json`,
`godot-print-native-a/report.json`, and `godot-print-delivery-a.json` under
`testing/output/treehouse/`. All nine served file hashes match this build.

### Current save-file checkpoint

Play at <http://127.0.0.1:8768/>. **Press F9** to load or save game files.
Keep both `STATUS.DAT` (settings and saved scenes) and `SONGS.DAT` (songbooks).
Importing STATUS returns to character selection, as on original startup;
matches, animation timers, the chosen child and the robot's prizes are session
state. Files and settings also save locally and survive browser reload.

The loader preserves unknown words, inactive records, noncanonical usage flags,
old handles and trailing bytes. Unsafe values are normalized for play while
the original bytes remain untouched until corresponding saved values change.
Room-object normalization and skipped animal/prop records retain their original
file slots for subsequent edits. Truncated imports leave the current game intact.

Passing: 81 format/model/control checks, including the packaged save and two
files written by DOS; 22 actual Edge picker/download/reload checks, including
repeated imports, cancellation and complete byte comparisons of both formats;
17 browser help/preferences checks. The complete Money/theater journeys retain
25/29 native matches. Editor and nature controls retain 32/56 passing checks.
The desktop file dialog is implemented but has not received an interactive check.

Existing Godot JSON profiles migrate into STATUS over the pinned file's opaque
bytes. That migration remains a seeded export. New profiles now use the original
missing-file defaults described above. Title boot, full startup integration and
strict presentation/audio fidelity remain unfinished.

Immutable export: `testing/output/treehouse/godot-status-web-build-c/`.
PCK SHA-256: `54f3c174ef3a07f172b7cce424710fb6a812d30474aab1402e34811cd829151c`.
Evidence: `godot-status-k/report.json`, `godot-status-web-e/report.json` and
`godot-status-delivery-a.json` under `testing/output/treehouse/`.

The browser file picker uses native HTML controls and Godot's
[JavaScriptBridge](https://docs.godotengine.org/en/4.5/classes/class_javascriptbridge.html).
Serialization and gameplay remain in GDScript.

### Preferences and help checkpoint

Play at <http://127.0.0.1:8768/>. Press F1 for contextual help, F2 for settings,
Ctrl+S to toggle sound, or Ctrl+V for the original version message. Help retains
the original pointer-dependent close behavior: the pointer must be inside the
panel even when pressing Escape. Settings include sound, printing, printer
profile, maze difficulty and the original speed-optimization flag. Printer
profiles remain unavailable, as in the supplied configuration; physical
printing is still pending.

All 20 captured original modal regions match, including their cursors: 12 help
panels, six preferences states and two status messages. There are 62 passing
control/context/persistence checks and 17 actual Edge checks, including reload
and theater notebook help. The native Money winning route retains 25 matches;
the theater journey retains 29. These are bounded checks, not full-game parity.

Immutable export: `testing/output/treehouse/godot-preferences-web-build-b/`.
PCK SHA-256: `9fc31eb4ce1750239f4c7e001df287121f6d8cb1297ea402d2d3c0d6346e0a40`.
All nine served file hashes match in `godot-preferences-delivery-a.json`.
STATUS.DAT and file interchange were added in the subsequent checkpoint above.

### Current board-game checkpoint

Play at <http://127.0.0.1:8768/>. Click the board on the room floor. Choose
Money or Chip Game and PLAY. Roll with the question mark, follow the road
arrows, choose an offer and click the highlighted stack to exchange chips.
Game mode, opponent and goals survive browser reload.

Passing: 4,794 port rendering/state/sound-dispatch comparisons, 39 production
controls through games/endings/prizes, and 20 actual Edge checks. The complete
winning Money replay matches all 25 native images/states. The Chip replay
matches all 49 states but retains one highlight-image mismatch. The losing
Money replay still diverges after a payment and does not reach its recorded
ending. These failures and strict timing/audio work remain open.

Immutable export: `testing/output/treehouse/godot-board-web-build-a/`.
PCK SHA-256: `4e55b389ab507d4a6fe613d66445ffb01fc82466e5ee7c299f8e6845033109f7`.
Next: shared settings/help, original STATUS.DAT integration, file interchange
and actual printing/downloads.

### Nature and telescope checkpoint

Play at <http://127.0.0.1:8768/>. Click the animal picture in the room for
filters, facts, day/night collages and the animal guessing game. Drag animals
onto the scene; scenes survive reload. The telescope opens four original views
and shows the robot's earned prizes. Click inside a finished view to replay;
click outside it to return to the room.

Passing: 2,559 nature rendering/behavior cases, 21 native collage checkpoints,
ten native quiz checkpoints, 56 nature controls, 72 telescope controls and nine
complete original telescope/shelf images. The exported build passes 21 actual
Edge checks including save/reload and telescope interaction. The longer robot
prize route still fails three room-return states and two images; strict timing,
audio waveform parity and shared save/help/printing integration remain open.

Immutable export: `testing/output/treehouse/godot-nature-web-build-b/`.
PCK SHA-256: `d94108f1154de9074d0ad08351a3c5a36faeb13a5fe38b09d34429061a4939fb`.
Next major port: the Money and Chip board games.

### Current sentence-theater checkpoint

Play at <http://127.0.0.1:8768/>. Click the small curtains in the main room,
then PLAY. Choose words from the notebook and click the director to perform.
Options enable Mix Up word tokens and draggable decorations. Your play saves
and survives browser reload. The upper-right trophy returns to the room.

The complete recorded room/theater/return journey passes all 29 native image
and checked gameplay/RNG checkpoints. Also passing: 1,390 rendering/progression
cases, 52 mouse/touch checks, 73 observed original sound sources/rates, and ten
actual Edge checks including save/reload. These do not prove exact native
frame timestamps or audio waveform parity.

Immutable export: `testing/output/treehouse/godot-theater-web-build-b/`.
PCK SHA-256: `83a0efb401efd7f35fde92c5f9d90a6cde16c42e3f58def4cca45a4da1ac65f0`.
Next: nature and board games. Shared rewards, help, original save-file
interchange, printing and strict fidelity work remain unfinished.

### Current musical-maze checkpoint

Play at <http://127.0.0.1:8768/>. Enter the piano room, then click the bucket at
lower left. Listen and choose a matching sign to earn notes, or open the song
picture drawer to guess. Clicking during the first tutorial skips it. The upper
back arrow returns to your retained piano score; the trophy exits to the room.

The maze includes all five challenge types and nine scenes, wrong-answer hints,
adaptive difficulty, guesses, victory, replay and new rounds. Both children work
with mouse and touch. Immutable export: `testing/output/treehouse/godot-maze-web-build-a/`,
PCK SHA-256 `c214b7474cfb5337a0485b71ba928d31224fbe2616957d114b73d403a6a1a6e0`.

- `godot-maze-native-b`: 20 native generation/continuous victory checks.
- `godot-maze-component-a`: 244 complete rendering comparisons.
- `godot-maze-controls-d.json`: 66 fresh mouse/touch control checks.
- `godot-maze-web-b`: 29 actual Edge checks, including composing/save/reload,
  maze entry, sign interaction and retained-score return.
- `godot-maze-entry-full-d` / `godot-maze-entry-skip-c`: all 54 changed transfer
  frames in native order, stable endpoints and observed sound sources/rates pass.
  Overall reports remain failed for intermediate tutorial timing/RNG mismatches.

Sentence theater is available in the newer checkpoint above. Maze persistence/preferences, other activities,
file interchange, actual printing, rewards and strict audio/presentation checks
are still required.

### Earlier personal-songbook checkpoint

Play at <http://127.0.0.1:8768/>. Enter the piano room and click the lower-right
book/pencil button to compose. Play notes with the piano keys, drag notes/rests
onto the score, drag the green insertion marker or an existing note, and click
the title to name your song. The score-size button switches between independent
short and long books. Songs save automatically. The printer button currently
opens the recovered print-sheet preview; click or press Escape to return.

Immutable export: `testing/output/treehouse/godot-editor-web-build-a/`, PCK SHA-256
`b0118b8db2bdab0c2dcb3d7ff73b3b69aec683d334ecc28acbba4181efb5785b`.
Nine served file hashes match. Evidence:

- `godot-editor-native-c`: 22 continuous native image and active-state checks.
- `godot-editor-component-c`: 223 editor/print image and sequence cases, including
  three full original print sheets.
- `godot-editor-controls-b.json`: 32 controls and binary save/load checks.
- `godot-editor-listening-a`: 151 retained listening cases.
- `godot-editor-web-a`: 23 actual Edge checks, including saved notes and title
  surviving browser reload.

The next activity is musical maze. Original-file import/export controls and
actual print/download delivery remain unfinished. The checks above do not prove
strict presentation timing or audio waveform equality.

### Earlier music listening checkpoint

The Godot Web preview at <http://127.0.0.1:8768/> now includes music. Click the
piano on the room floor. Play with the onscreen keys or
`Z S X D C V G B H N J M , L . ; /`. The instrument button opens family browsing;
Escape returns through the original ring/bubble sequence.

Immutable export: `testing/output/treehouse/godot-music-web-build-a/`, PCK SHA-256
`783e07f7bf51274309d30cdb684d50671c08a0381c055fd7d852f5528894c5a0`.
All nine served files match (`godot-music-delivery-a.json`).

- `godot-music-component-e/report.json`: 151 complete image/song-dispatch cases
  against JS, plus four full native music/menu images. The native long-score
  check allows the 17 authored idle-eye frames; it does not prove timing.
- `godot-music-transitions-c/report.json`: all 330 changed full frames match the
  original in order across eight ring/bubble sequences. Each sequence has an
  initial native room fixture. Only music is connected to an activity so far.
- `godot-music-input-a.json`: 47 production-control checks through room entry,
  music, every keyboard key, touch movement, focus cleanup and return.
- `godot-music-care-b.json`: 22 mouse/touch checks, including interrupted naps
  that restore the pillow before music entry.
- `godot-music-web-b/report.json`: 16 actual Edge checks through room/yard,
  music entry, physical piano input, family browsing and room return.

The object suite retains all 86 cases; startup retains its nine checks, two
native images and all 356 SCR comparisons. Native room and yard checks retain
24/24 images each but remain failed: room 19/24 full states (erase-dialog RNG),
yard 23/24 (return balloon). Sound dispatch uses recovered samples and effective
rates, but actual output waveform/mixer parity remains unproven. Composition,
copy/erase/random-song controls, printing and maze are not yet implemented.

### Current object and care checkpoint

Play the Godot Web export at <http://127.0.0.1:8768/>. The immutable build is
`testing/output/treehouse/godot-objects-web-build-b/`, package SHA-256
`ae99622847dcea0bf31f778db534e56a928004ef106319796c1430b7ac0219d3`.
`godot-objects-web-b/report.json` passes eleven actual Edge checks, including
pillow dragging/falling and taking a nut from the bag. `godot-objects-delivery-a.json`
checks all nine served files against that export.

`godot-objects-component-c/report.json` passes 86 isolated object cases against
the JavaScript reference: 3,425 sampled resident frames, sound events, completion
ticks, poses, needs, objects and RNG. These fixtures do not prove native timing.
`godot-objects-care-b.json` passes eighteen mouse/touch control-handler checks
through feeding, pillow refusal, nap, yard/room visits and natural waking, with
an advancing clock and no installed need/pose/object state. Twelve input checks,
158 action cases, startup checks and all 356 SCR comparisons remain passing.

The three `godot-objects-basket*-final-a` reports match all fourteen native full
images and gameplay/object/RNG states. The broader comparisons remain **failed**:

- `godot-objects-room-e/report.json`: 24/24 images, 19/24 full states. RNG first
  diverges after declining the chalk erase dialog.
- `godot-objects-yard-final-a/report.json`: 24/24 images, 23/24 full states.
  Final return balloon geometry remains different; RNG now matches throughout.
- `godot-objects-egg-final-a/report.json`: 3/4 images, 4/4 full states. The final
  scene image remains unmatched despite matching object/RNG state.

Native replays start from one snapshot and compare image membership within each
input interval. They do not establish exact presentation timestamps or device
audio parity. Failed intermediate reports are preserved.

### Current character and yard checkpoint

The immutable Godot Web build is in
`testing/output/treehouse/godot-yard-web-build-b/`, package SHA-256
`3b83f548ef6df6db4efa148b44e39373d4650aebdc3dd16b6cf236f3d90b737b`.
`godot-yard-web-b/report.json` passes nine actual Edge checks through room,
calendar, drawing, yard, hollow, a nut throw and ladder return.

`godot-resident-actions-c/report.json` passes 158 available character/pose/action
cases against the JavaScript reconstruction: final full image, pose, objects,
completion tick and RNG state. These isolated cases supply a pose, seed and
empty object list. Device output is disabled in this accelerated comparison;
sample durations still drive deadlines. This does not prove native audio output.

`godot-yard-journey-c/report.json` matches all 24 original yard/hollow full images
and 23/24 checked states. **The final room-return balloon state still fails**:
expected `[64,133,102,162]`, actual `[65,135,103,164]`. The same mismatch exists
in the JS reference. It remains open; no captured delay was added to hide it.
The replay supplies one initial snapshot and checks image membership within
input intervals, not exact display times or complete RNG/object state.

`godot-yard-room-regression-b/report.json` retains all 24 room-route checks.
`godot-yard-startup-d/report.json` retains nine startup checks, two native images
and 356 SCR traces. `godot-yard-input-a.json` retains twelve input checks.

Repeat the action check with `tools/treehouse/verify_godot_resident.py` and the
yard replay with `verify_godot_room.py --reference
testing/output/treehouse/yard-native-journey-b --stop room-return`; both also
require `--godot <engine> --output <new-folder>`.

### Current room checkpoint

`testing/output/treehouse/godot-room-journey-d/report.json` passes all 24 full
320x200 native images in the recorded calendar/clock/environment/chalk route.
It also compares calendar date/open state, cloud, chalk tool and balloon
presence/state/geometry. The replay supplies one initial room/time fixture and
then ordinary pointer events. It checks image membership within input intervals,
not exact presentation timestamps or the unported resident RNG/needs/objects.

`testing/output/treehouse/godot-room-input-a.json` passes twelve focused touch,
keyboard, focus-loss and eraser checks. `godot-room-startup-c/report.json` retains
the two exact startup frames, nine checks and all 356 SCR comparisons.
`godot-room-web-a/report.json` passes six actual Edge interaction checks with no
browser errors. Its immutable Web files are in
`testing/output/treehouse/godot-room-web-build-a/` (package SHA-256
`126f3c092efe169541b96dcbe6db84ba6fd558aa53e2e467e6feae6c119ec123`).

Run `tools/treehouse/verify_godot_room.py --godot <engine> --output <new-folder>
--stop calendar-final-closed` to repeat the full room route. For exported builds,
`verify_godot_web.py` accepts `--web <export-directory>`.

### Initial foundation checkpoint

`testing/output/treehouse/godot-startup-b/report.json` records:

- Nine capture/input/entrance checks.
- Selection and initial boy-room frames matching pinned DOS captures at all
  64,000 pixels each. The room test supplies the reference date/time.
- All 356 recovered scripts match 11,512 interpreter events in the JavaScript
  reference. Every script terminates within the 10,000-tick bound. This comparison
  supplies no activity callback behavior and does not prove native timing.

`testing/output/treehouse/godot-web-a/report.json` records an actual Godot Web
export running in Edge, mouse selection through the entrance, and Escape back
to selection with no browser errors. Its image assertion covers a stated static
room region; complete screenshots and hashes of all exported files are retained.

`tools/treehouse/verify_godot_startup.py --godot <engine> --output <new-folder>`
and `tools/treehouse/verify_godot_web.py --output <new-folder>` reproduce these
checks. Always use a fresh output directory to preserve earlier evidence.

The shared extractor still rebuilds the JavaScript reference byte-for-byte at
SHA-256 `27689144aa93085bc22f6e2b282b0563f08960659bfeb2b489bf307ac1804413`.
Godot stores the original CP437 table as Unicode integers because Godot strings
reject its NUL entry; no source resource bytes are changed.

Remaining work is tracked in `testing/treehouse/remaining-work.json`, including
TH-008 through TH-017 for the Godot migration. Prior strict fidelity failures
remain open and must be checked against the integrated Godot build.

`python tools/treehouse/completion_status.py` now checks this Godot project and
its attested Web export by default. It reports all 59 ledger acceptance rows;
pending verification does not mean that a feature is absent. The historical
JavaScript results are archived separately and cannot satisfy Godot completion.
See `tools/treehouse/README.md` for build/evidence capture commands.
