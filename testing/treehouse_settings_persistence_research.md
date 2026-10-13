# Native preferences and STATUS.DAT completion research

Primary-source research, 2026-09-27. No runtime edits. Main instruction addresses refer to `output/treehouse/research-resources/main-disassembly.txt`; overlay addresses name the overlay. The pinned original ZIP SHA-256 is `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`; unpacked image SHA-256 is `f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f`.

## Original global preferences

**F2 opens PREFERENCES.** The sole direct call to resident `1AC5` is `1995` in the shared keyboard service `18CD`. Its key flag is DS15BA, scan code3C. No separate room mouse hotspot for this panel was found in either the room hotspot dispatch or references to its entry point. Activity options icons are separate dialogs. F1 invokes context help through `5E07`. Ctrl+S toggles sound through `61BF` and shows the status message; Ctrl+V displays `Version 1.1`.

The preferences panel has exactly five rows. Shared state segment is3169; every value below is a little-endian u16. Native source toggles zero to1 and any nonzero to0.

| Row | State | STATUS file | Labels / behavior |
|---|---:|---:|---|
|0|00AA|0062|`Sound is ON/off` or `Sound is on/OFF`; calls master sound volume15 or0.|
|1|00AC|0064|`Printing is ON/off` or `Printing is on/OFF`; enables printing. **This is not speech.**|
|2|00AE|0066|Printer selection0/1; `Printer: %Fs`, or `Printer: Not Selected` when that CONFIG.DAT printer entry is unavailable.|
|3|00A8|0060|`Music Game Level: BEGINNER/advanced` or `Music Game Level: beginner/ADVANCED`; music maze initial level, independent of piano short/long mode.|
|4|00B2|006A|`Speed Optimization is ON/off` or `Speed Optimization is on/OFF`.|

The earlier rewards report's description of AA/AC as “speech/sound” is superseded by this source and capture evidence. No independent speech preference is present in this dialog.

Exact rectangles `(top,left,bottom,right)`, bottom/right exclusive, from image2E8F0:

- Panel, offset150: `(43,32,152,288)`.
- **Done**, offset158: `(136,242,148,282)`.
- Row0..4, offset160+8*i: `(61+14*i,34,75+14*i,286)`.

Renderer `5BB3` saves/restores the panel background, fills white and outlines black, uses the current saved system font handle DS57C4, centers blue `PREFERENCES` four pixels below the panel top, renders centered black rows, and a blue Done button. Use the native font already retained by bootstrap; DS57C4 is copied from the existing DS20B2 font before FONT1 is selected at1CA. Do not assume that preferences use the piano FONT2. Row feedback `1EEA` draws in the pressed color, waits12 interruptible ticks, then redraws normally. Escape follows the Done path. Clicking outside the panel does not dismiss it. Exiting calls `7CDD`, then restores the previous activity display and clears modal flag DS52E2.

Availability guard `187E` blocks F1/F2 during an existing modal (DS52E2), active music playback (stateA92), or active sound while a character is loaded. The outer key handler stops/relinquishes the active tool as needed before opening preferences and resets room ambient timing afterward.

Printer AE selects between two hardware profiles in CONFIG.DAT: routine `1CB8` checks configuration words+0A/+0C against signed−2 and chooses string-list entry1/3 accordingly. A click still toggles AE even if both profiles are unavailable. The captured original says `Printer: Not Selected` for both states. Printing AC and printer selection AE are distinct; importing AC=1 does not establish a working printer backend.

Speed optimization B2 is read by music rendering, notably overlay1 `13AB`, `2FDF`, `312B`: it affects drawing work/paths. It is not a frame-rate setting. Shared B0 has no recovered use; a superficially similar theater reference to ES:B0 at overlay4:3BEC uses segment30C8 geometry, **not** state3169.

### Ordinary-input evidence

`output/treehouse/research-settings/capture-settings.py` restored an existing unmodified native state and used only F2/mouse/Escape. `native/run.json` records the actions, state reads, and restore SHA-256. `native/state/preferences.png` captures the initial panel. `row-0.png` through `row-4.png` show each toggle. Read-only RAM observations confirm exactly AA, AC, AE, A8, B2 changing in that order; B0 stays0. Done writes a2704-byte native STATUS.DAT; the actual file is retained as `native/status-written.dat`, extracted from the emulator's filesystem delta ZIP. These are behavior observations, not a new independent pixel reconstruction.

## STATUS.DAT binary container

Writer `7CDD` and reader `7DCB` use three raw ranges:

| File range | Length | Original RAM |
|---|---:|---|
|0000..08E9|2282 /08EA|3169:0048..0931|
|08EA..08EB|2|DS556C object count|
|08EC..0A8F|420 /01A4|DS5830,21 object records ×20 bytes|

Canonical length is2704 /0A90 bytes. There is no header, signature, version, or checksum. The reader checks each read's success and requested byte count, but does **not** validate individual fields or reject trailing bytes. Therefore distinguish a structurally readable file from a state safe to use as array indexes. For the first region, `fileOffset = sharedOffset - 0x48`.

### Complete first-region map

All numbers in the two offset columns are hexadecimal. Arrays are laid out consecutively unless the row specifies interleaving. The validation column describes values produced/consumed by ordinary native UI, not checks performed by the native loader.

| Shared | File | Shape | Meaning and usable range |
|---:|---:|---|---|
|0048|0000|86×u8|Personal SONG page used flags,43 per short/long mode. Any nonzero means used; **do not restrict stored bytes to0/1**. Packaged flag0 is84.|
|009E|0056|4×u8|Page selections indexed `2*advanced+composing`: listening short, personal short, listening long, personal long. Listening0..24, personal0..42. Final24/42 are terminal pages.|
|00A2|005A|u16|Piano mode: **0=listening,1=composing**.|
|00A4|005C|u16|Advanced piano0/1; short8-note/long30-note editor.|
|00A6|005E|u16|Piano repeat0/1.|
|00A8|0060|u16|Music maze beginner0/advanced1.|
|00AA|0062|u16|Sound enabled0/1.|
|00AC|0064|u16|Printing enabled0/1.|
|00AE|0066|u16|Printer profile0/1.|
|00B0|0068|2 opaque bytes|No recovered shared-state use. Preserve.|
|00B2|006A|u16|Speed optimization0/1.|
|00B4|006C|u16|Room cloud picture index0..6; not character identity.|
|00B6|006E|u16|Nature collage day0/night1.|
|00B8|0070|u16|Nature exploration selected attribute0..6. The identification game's eighth attribute does not add an eighth persisted value here.|
|00BA|0072|i16|Nature selected animal class;−1 unselected, otherwise0..8 day/0..9 night, constrained by current filter availability.|
|00BC|0074|7×u16|Nature selected value for each of seven attributes; index into STRL5200..5206 respectively.|
|00CA|0082|2×u16|Placed-animal counts for day/night,0..40 each.|
|00CE|0086|80×u16|Placed animal indexes0..91, interleaved `2*instance+dayNight`, instance0..39.|
|016E|0126|80×4×i16|Placed animal rectangles in same interleaving; top,left,bottom,right.|
|03EE|03A6|u16|Board game0=money,1=chips.|
|03F0|03A8|u16|Board opponent1=friend,2=robot.|
|03F2|03AA|6×u16|Goal indexes0..2, indexed `3*gameType+role` with role0 human,1 friend,2 robot.|
|03FE|03B6|u16|Nature identification opponent1=friend,2=robot.|
|0400|03B8|3×u16|Identification automatic-help flags0/1 for human/friend/robot.|
|0406|03BE|u16|Theater Mix Up0/1.|
|0408|03C0|u16|Theater Props0/1.|
|040A|03C2|4×i16|Theater phrase selection by subject/action/place/time.−1 empty; ranges0..7/0..7/0..5/0..3.|
|0412|03CA|6×u16|Theater prop counts by location0..5,0..20 each.|
|041E|03D6|120×4×i16|Prop rectangles indexed `20*location+instance`.|
|07DE|0796|120×u16|Prop identities with same indexing. Encoded group/shape identifiers, not arbitrary global SHAP IDs.|
|08CE|0886|7×2×i16|Actor `(dy,dx)` translations for six locations plus blank stage.|
|08EA|08A2|4×u16|Theater sentence category order; permutation of0..3.|
|08F2|08AA|24×u16|Maze offered-song history; zero unseen/nonzero seen.|
|0922|08DA|6×u16|Maze chooser's six song indexes0..23, distinct.|
|092E|08E6|2 opaque bytes|No recovered access. Packaged value1; preserve.|
|0930|08E8|i16|Theater last sentence validation code0..6.|

This map covers all2282 bytes, including both opaque words. A separate numeric schema is at `treehouse/status-schema.json`.

Nature evidence: overlay2 `0752..07BB` increments CA+2*dayNight, writes animal ID at CE+2*(2*instance+dayNight), and rectangle at16E+8*(2*instance+dayNight); count guard069B caps40. Valid native drops are constrained to interaction rectangle `(5,131,195,315)`. Inactive records need not satisfy active-object constraints. Values at BC stop before CA: there are **seven** u16 values, not eight.

Board evidence: overlay3 options around0E6C stores robot's goal from human's when leaving options; preserve all six words in an untouched round trip instead of eagerly enforcing that UI side effect. Goal indexes map to win targets50/100/500, starting balances money10/20/100 or chips15/30/150.

Music evidence: overlay1 `07B2..07F1` synchronizes the two listening selections during page changes, while primary loader3258 reads9E for listening. Preserve all four page bytes individually on import/export. Do not coalesce them merely because native UI normally synchronizes listening pages.

Maze evidence: overlay1 `8A7B..8ADB` chooses six distinct unseen indexes from0..23, setting each history word to1. `8ADB..8BC3` marks the selected song, scans all24 history entries, and when all are seen clears48 bytes then marks the current six before replacing the chosen slot with a new unseen song. Bad imported indexes or a malformed all-seen mask can otherwise cause invalid access or endless rejection sampling. Preserve raw bytes, but build a valid runtime chooser/history together. The original's fresh-file path calls8A7B after zeroing the state.

Theater prop identities should be validated against the original prop palette/group tables used by overlay4:37F2, including the location's available prop collection. See `treehouse_theater_research.md`. Preserve z-order, inactive slots and signed actor translations. Do not force rectangles or translations to unsigned values.

### Room object block

Object count at08EA is u16, ordinary range0..21. Record i begins `08EC+20*i`:

| Relative byte | Type | Meaning |
|---:|---|---|
|0|u16|Object type; native enum0..20.|
|2|u16|Object state/quantity, semantics depend on type.|
|4|u16|Room flag0 outside/1 inside.|
|6|4×i16|Top,left,bottom,right.|
|14|u16|Old background image handle. Preserve opaque for raw round trip; never reuse as a live pointer/handle.|
|16|u32|Scheduled native tick. Preserve raw; rebase/recompute runtime scheduling on load.|

Boot normalization at `038A..053B` ensures pillow8 exists, deletes flower7 in state5 and transient bird15, takes balloon6 state modulo10 and clamps1..3, clamps flower7/pile14 to1..4, and sets other object states to1. It rebuilds runtime backgrounds/timers. Thus native loading is not a continuation of every animation or depletion timer. See `treehouse_character_research.md` and `treehouse_object_completion_research.md` for per-type behavior.

### Missing or invalid file defaults

Reader failure `7ECF` zeroes all2282 bytes, sets robot nature-help404=1, nature classBA=FFFF, all four phrase choices40A..411=FFFF, sentence order8EA=[0,1,2,3], board/nature opponents3F0/3FE=1, soundAA=1 and printingAC=1. It clears the object count and creates standard objects9/10, then initializes six maze songs through overlay1:8A7B. These are **not** the packaged file's saved settings (e.g. packaged opponents are2, cloud5, class3 and listening page20).

## Import/export contract

Recommended implementation, separate from native loader behavior:

1. Retain the entire imported STATUS byte array, including extra trailing bytes. Reject fewer than2704 bytes as truncated. Keep an immutable original or copy-on-write base.
2. Parse known values into a separate runtime model. Range-check before every resource/array index, check counts before iterating, and constrain active rectangles using the original activity's placement rules. Do not mutate raw bytes while normalizing the runtime view.
3. Report/record invalid known values; substitute missing-file defaults for unsafe preferences and omit unsafe active objects. For maze history/chooser, normalize them together so six distinct safe songs remain possible. Keep unsupported opaque data unchanged.
4. Export by copying the base array and patching only fields deliberately changed by the user/runtime. Use signed little-endian writes for sentinels/rectangles. Preserve unused slots, noncanonical nonzero song-used bytes, opaque B0/92E, old handle fields and trailing data unless explicitly regenerating a canonical native save.
5. A brand-new canonical export can begin from the source defaults or a documented seed file, but label that choice: copying the packaged file imports its previous author's preferences and content. Creating new state should follow the zero/default initialization above.

The native writer truncates/recreates its file and writes exactly2704 bytes. Retaining trailing bytes in modern round trips is a compatibility policy, not an original behavior.

## Separate files and state that is not persisted

`SONGS.DAT` stores the86 personal song records and86 title records separately; STATUS carries their used flags. See music editor research:86×65-byte SONG records at0,86×36-byte titles at15D6, and two tail bytes at21EE; total8688 bytes. A faithful interchange needs both files for music. Built-in listening songs and their instrument/tempo/sharp defaults are executable/resources, not STATUS fields. Selected instrument/tempo for a personal song lives in its SONG header, not a new global preference.

`CONFIG.DAT` is hardware setup, loaded before STATUS at main0083 (reader D51:5E2C). The supplied file is32 bytes and contains display/audio/printer setup. Missing CONFIG prints `Error reading 'CONFIG.DAT'. Please run SETUP.`; graphics selector−2 prints `Graphics Mode not selected. Please run SETUP.` and exits. It is not part of STATUS and should not be silently embedded into the game save. This report does not claim a complete SETUP/CONFIG schema; preserve that file independently if implementing full archival bundles. Preference printer AE selects its existing printer profiles.

Character choice state+A14, hungerDS5282, fatigueDS581C, poseDS5688, room/object timers, robot shelf flagsDS55F8, and telescope visit maskDS52F6 are outside all three serialized ranges. Do not infer saved character selection from cloud indexB4. Current maze node/notes/secret slot and live nature/board match state are likewise not in the preference schema above.

## Startup, return, shutdown

- Bootstrap loads CONFIG/hardware and resource archives, calls STATUS reader at02F8, clears pending events and installs shutdown callback637A at0364. Missing-file defaults do not require a new preferences dialog.
- Startup activity/room initialization resets live character and object state, then draws the outdoor treehouse. Character choice is a live selection, not restored through STATUS.
- Escape from the **interior** returns to the outdoor treehouse. This was captured directly as `native/state/room-escape.png`; do not implement that key as immediate program quit from every scene.
- In the **outdoor main loop**, Escape at06D3..06E0 calls D51:54E8 with exit code0. D51:54E8 (image129F8) calls the installed callback, performs system cleanup and DOS exit. There is no confirmation dialog in this path.
- Shutdown callback637A first calls overlay1:1E8C (stop musical/audio playback), then STATUS writer7CDD. The overlay call is `CD 3F 01 8C 1E`; it is not a song-file save call.
- Global preferences Done/Escape saves STATUS immediately at1C43; theater activity-options exit also saves at overlay4:1D8C. Leaving the theater editor itself retains shared state but does not immediately write STATUS. Other activity returns should retain shared settings for the later save.

The modern browser cannot meaningfully DOS-exit. It can expose an explicit leave-game action and save on the corresponding original transition while preserving the original interior→outdoor path. Additional modern settings such as readable text are extensions and should not consume either unknown native word.
