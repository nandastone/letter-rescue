# Treehouse musical maze: recovered model, rendering, and movement

Primary-source reverse engineering, 2026-09-27. This activity is entered from the piano's bucket, not the instrument-family selector. Findings derive from the pinned DOS executable, its resource archives, and ordinary mouse input to the original. No runtime files were changed.

## Deliverables and evidence

- [Numeric tables](treehouse/music-maze-tables.json): graph, scene coordinates, paths, challenge patterns/sets, actor animation tables, UI rectangles.
- [Independent comparison report](treehouse/music-maze-comparison.json): nine complete 320Ã—200 native screens reconstructed with **zero mismatched pixels**. Covers all five challenge types, zero through seven earned notes, the song chooser, and settled victory.
- Scratch root: `testing/output/treehouse/research-music-maze/`.
- `render-all.py <settled|correct-0..correct-6>` reconstructs the eight gameplay frames; `render-guess.py guess-open` reconstructs the chooser; `render-win.py win-settled` reconstructs victory. These scripts use recovered source geometry and captured model values; native PNG pixels are read only for the final comparison.
- `playthrough/` records a whole eight-note journey. `early-win/` records choosing the correct song after one note and reaching the settled victory screen. `guess-and-win/` records a wrong guess and demonstrates that further guesses are locked until earning another note; despite the directory name, that run does **not** win.
- Every capture directory has `run.json` with ordinary input actions and restore digest. No guest memory is patched. RAM reads merely observe model values and pointer position.

Pinned original ZIP SHA-256: `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`. Unpacked image SHA-256 is recorded in the numeric table. Original source and capture procedures are documented in [executable research](treehouse_executable_research.md) and [music follow-up](treehouse_music_followup.md).

Instruction offsets below mean overlay 1 in `testing/output/treehouse/research-resources/overlay1-disassembly.txt`, unless explicitly labeled resident. Data offsets refer to `testing/output/treehouse/disassembly/unpacked.bin`.

## Rules and entry

Piano hotspot 22 is `(top=141,left=11,bottom=175,right=51)`, click `(31,157)`. Entry routine is `51B6`. It loads MODULES SHPL2340 (SHAP2341..2358), the selected BOY/GIRL SHPL20000 (40 frames), and TH SHPL22000 (51 frog frames).

The player hears a target sound and chooses one of four signboards. A correct choice earns the next note of a hidden familiar song, then the player follows that sign's path to another scene. Collected notes can be replayed. After earning at least one note, the player can identify the song from six pictures. A correct early guess wins; collecting the entire introductory song automatically reveals the answer and wins.

There are nine connected ordinary scenes, plus scene 9 for introduction/victory. The maze has no destination node or separate point total: notes and song identification are its progress model.

### Main flow

Source `51B6..5928`, initialization `7062..717C`, challenge selection `5EFB..67B2`, guess selector `7C84..826C`, victory/introduction `862D..8983`.

1. Pick six distinct songs from IDs 0..23 and a secret slot 0..5. Song selection uses a history mask to avoid previously offered songs; `8A7B/8ADB` manages the history cycle.
2. Reset earned notes and correct streak. Pick node 0..8, initialize excluded/back direction to 2, generate the first challenge, draw scene, animate the player entering from the right, play the target.
3. A sign click auditions its candidate with red feedback. Correct: increment streak, change difficulty to hard at streak 2, animate reward and movement, increment earned notes, then generate the next challenge at `neighbors[node][direction]`.
4. Wrong: reset streak and difficulty to easy, mark the sign attempted, render it gray, and stay in the same scene. Repeated errors trigger three flashes of the correct sign. Source checks the previous wrong-attempt count, so the hint starts with the second error.
5. A new stage clears wrong-sign flags, wrong-attempt count, and the guess lock. The next correct direction excludes the opposite of the exit just taken.
6. A click outside controls/signs replays the target. Idle timers are 360 native ticks for target replay and 900 for sign hints.
7. Question button is available only when earned notes > 0 and no guess has been made during this stage. A wrong song guess auditions that song, removes its picture from future chooser displays, and locks guessing until the next stage. Dismissing the chooser with Escape/outside click does not use the guess.
8. When collected notes reach SONG header byte 0, reveal mode highlights the correct picture three times, plays the collected melody, then wins automatically. An early correct guess triggers celebration jumps corresponding to the uncollected notes before victory.

### Controls and rectangles

All rectangles are `(top,left,bottom,right)`, exclusive bottom/right. Table starts at image `0x2F9F0+0x470`.

| Index | Rectangle | Use |
|---|---|---|
|0|1,304,23,320|Global exit|
|1|1,280,21,302|Return while playing|
|2|0,244,84,271|Victory ladder, return to piano|
|3|119,189,135,202|Guess song / question|
|4|136,189,152,202|Replay collected notes|
|5|60,95,112,177|Six-song chooser|
|6|43,271,79,300|Victory right arrow/piano, return|
|7|95,0,131,29|Victory left arrow, new maze|
|8|37,30,112,242|Victory full score, replay|

Victory controls source `52D9..539E`: 7 starts another maze; 6 or 2 returns to piano; 8 replays the score. Escape also returns. Clicking elsewhere runs the idle response. Keyboard direction shortcuts have not been established; ordinary mouse is verified.

## Graph, positions, and path representation

Directions are `0=left,1=up,2=right,3=down`. The JSON exports the full graph rather than requiring the implementation to recreate it arithmetically:

```text
0: 2 6 1 3       3: 5 0 4 6       6: 8 3 7 0
1: 0 7 2 4       4: 3 1 5 7       7: 6 4 8 1
2: 1 8 0 5       5: 4 2 3 8       8: 7 5 6 2
```

`centers` are actor footpoints `(y,x)`; `sign_positions[node][direction]` are sign top-lefts; `sign_actor_targets` are the actor's footpoints beside signs. Do not use the center of the visible sign as the actor destination.

Each `walk_paths[node][exit]` contains up to six `(direction,distance)` segments. Raw format is packed `(s8,u16le)`, terminated by direction -1. There are **ten** nodes' paths, including the win scene. The final segment gets `offscreen_walk_extension[direction]` added. Entering reverses the segment order and substitutes opposite directions, ending in pose 3 at the node center.

Extra movement directions `4=climb up`, `5=climb down` are used by the victory ladder. They have 9-pixel steps, animation 10, and no extra offscreen extension. Ordinary directions use 2-pixel steps. Exported opposite directions are `[2,3,0,1,5,4]`; vectors `(y,x)` are `[(0,-1),(-1,0),(0,1),(1,0),(-1,0),(1,0)]`.

Node 9 paths are left `[(0,162)]`, up/ladder `[(2,40),(1,18),(2,54),(1,48),(4,45)]`, empty right path, down `[(3,50)]`. Its player footpoint is `(150,162)` and frog footpoint `(150,130)`.

## Challenge generator and sound

| Type | Meaning | Pattern data | Playback |
|---|---|---|---|
|0|Rhythm|Three duration bits|Three pitch-9 notes, each 25 or 50 ticks|
|1|Pitch pair|Two pitches|25 ticks each|
|2|Melody|Three pitches|25 ticks each|
|3|Accidental notation|Two pitches plus separate notation flags|25 ticks each|
|4|Instrument timbre|Four global instrument IDs|Audition one original instrument sample|

Easy enabled types: `[1,1,0,1,1]`; hard: `[1,0,1,1,1]`. The audio capability routine resident `62D3` also limits the supported type count to four or five. Initial selection is special: capability return 0 forces timbre; otherwise easy starts with pitch pair, hard with melody. The captured backend starts with timbre and subsequently uses notation types. Do not infer backend names from this condition alone.

For types 0..3, choose a pattern-set index without repeating within its cycle. Set element 0 is the correct candidate; place it in the chosen correct direction and randomly distribute the other three candidates. JSON includes every set row and its difficulty-dependent count. Some tables have additional rows unavailable at easy difficulty; use `challenge_set_counts`.

Easy timbre selects one random family and instrument for the answer, then instruments from three other distinct families. Hard timbre selects two distinct families and two distinct instruments from each; directions 0/2 use one family and 1/3 the other. Reject ambiguous pairs `(20,21)`, `(13,11)`, `(17,7)` in either order. Instrument families and digital sample mapping are in [music follow-up](treehouse_music_followup.md).

Original pitches are indices in the existing piano's 17-note range. Accidentals/notation flags should stay separate from pitch. For example two visually different accidental spellings can sound the same; the set tables encode the intended comparisons. Rhythm patterns enumerate all three-bit patterns except 111. Melody patterns are the six permutations of `[4,7,12]`.

## Exact settled gameplay rendering

Sources `5929`, `5A82`, `67B5`, `6AC0`; executable recipe `render-all.py`. Coordinate tuples below are `(x,y)`.

1. Opaque MODULES SHAP `2341+node`, SHPL2340 at `(0,0)`.
2. TH exit SHAP8/SHPL6 at `(304,1)`, return SHAP7/SHPL6 at `(280,1)`.
3. Opaque small score MODULES2351/2340 at `(55,107)`, roller2353 at `(60,104)`.
4. Black staff lines x65..186 inclusive, y119,125,131,137,143; left bar x65/y119..143. Clef mask2302 at `(67,118)`.
5. Play mask2336 at `(189,136)`, fill its rectangle EGA7 when no notes are earned, EGA15 otherwise. Question mask2335 at `(189,119)` when available. Click feedback uses EGA12.
6. Collected notes use the introductory prefix of the original SONG. Note i at `x=87+13*i`, `y=147-smallPitchOffset[notationFlag][pitch]`. Use the advanced piano note renderer, including stems, flags, dots and accidentals. Small score ledger condition is `pitch<=1-notationFlag`. Rests use x`82+13*i+restX`, y`119+restY`.
7. Draw each sign using the following procedure, then the character pose 3, then the normal original cursor.

For sign top-left `(x,y)`, black outer rectangle `(y,x,y+36,x+29)` plus the same rectangle translated `(1,1)` as a shadow; white inner rectangle `(y+1,x+1,y+35,x+28)`. Pole2352 at `(x+9,y+37)`. Horizontal black line x..x+28 at y+10 for up, otherwise y+25. Arrow mask `2328+direction` at `(x+10,y+2)` for up, otherwise `(x+10,y+27)`.

Candidate box origin is `(x,y+10)` for up, otherwise `(x,y)`, dimensions 29Ã—26. Timbre icons use a white box with black border and the existing instrument icon centered on `(x+14,candidateY+13)`; palette groups2050/2075 and relative indices come from family data. The group2075 palette starts with SHAP2075, not2076.

Notation boxes have a white inset, gray EGA8 five-line staff at x+2..x+26, y=`candidateY+2+5*j`, and vertical line x+2/y+2..y+22. For each note ordinal n:

```text
glyphX = x+2 +
  (3+7*n)                                      types 0,2
  (5+10*n)                                     type 1
  (7+12*n-(hasAccidental ? notationFlag : 2))   type 3
glyphY = candidateY+2+challenge_note_y[notationFlag][pitch]
glyph  = SHAP2332 + (pitch>=11 ? 2 : 0) + rhythmDurationBit
```

An accidental uses mask `2314+2*notationFlag` at `(glyphX+notationFlag-5,glyphY-notationFlag+8)`. Played/attempted sign feedback changes the box fill to red/gray while keeping its glyphs black.

Actor 0 is BOY or GIRL, sprite palette20000; actor 1 is TH frog palette22000. Pose 3 means relative frame3, hence SHAP20004 or22004. Sprite placement from footpoint `(y,x)` is `left=x-width//2,top=y-height`; saved rectangle has an extra bottom/right pixel. Width is34 for both; heights40/38 respectively. Example initial node2 pose is BOY20004 at `(143,56)`.

Cursor uses image310B0, AND rows310B4 and OR rows310D4. In these native captures its raster origin is logical pointer `(x+1,y+1)`, colors yellow EGA14 and black. Pointer pixels are included in the zero-difference comparisons.

## Song chooser: exact complete frame

Source `7C84..826C`, verified recipe `render-guess.py`:

- Opaque MODULES2355/2340 at `(95,64)`.
- MODULES2354 top bar at `(95,60)`.
- Six **opaque** song pictures at `(101+25*(slot%3),66+23*floor(slot/3))`.
- MODULES2356 handle at `(95,107)`.
- Question rectangle filled EGA12, then black2335 mask at `(189,119)`.

Each picture is20Ã—22. Its packed icon selector is byte `image2F180+7F5+songId+1`. Palette group=`2100+20*(selector>>4)`; relative one-based shape index=`selector&15`. Opaque rendering matters particularly for the girl's song icon. Already eliminated slots are skipped.

Opening/closing uses a sliding drawer: source7DFE has24 iterations, delay2 ticks; source8111 has23 reverse iterations, delay2. Bar2354 and the handle are separate from the drawer image. Sound IDs1004 open,1003 close,1005 correct guess. A wrong guess invokes the frog's disappointed response at footpoint `(135,197)`.

## Animation implementation

Resident `809E..844D` supplies actor registration, pose changes, frame stepping and draw/restore. This activity is procedural; it does not need a new SCR animation interpreter.

The exported tables `animation_first`, `animation_count`, `animation_delay`, `animation_mirror`, `animation_reverse` fully select frames. Each first/count row is three actor slots, with slots0/1 used here. Frame shape=`palette.first+first[animation][actor]+counter`; apply mirror/reverse flags. Frame counter wraps at count.

| Animation | Use | Delay ticks |
|---|---|---|
|3|Idle front pose|0|
|4,5,6,7|Left, up, right, down walk|2,3,2,3|
|8|Player response, three frames|6|
|9|Jump, eight frames|4|
|10|Climbing, two player frames|16|
|11,12|Frog pointing, three frames|8|
|13,14|Frog appearance/return, five frames, second reversed|6|
|15,16|Single frog response poses|0|

Outward movement `7AA6` follows path segments, adding the final extension, at the exported step size. Incoming `77C6` starts at the summed offscreen endpoint and traverses the reversed path. Input may accelerate or interrupt certain transitions; full interruption semantics have not been replayed frame by frame.

Reward animation `73B8`: roller2353 moves from x60 to `60+(13*noteIndex+17-1)`, y104, one tick per pixel. Note descends from y107 to its final score y, two ticks per pixel. The source waits20 ticks around the drop, then retracts the roller one tick per pixel. Draw its ledger only at final placement. Sounds: roller1002, falling1000, landing10025.

Frog voices use random DIGISND20100..20103 (source89F7). Frog appearance/return uses10033/10034. Jumps use10045/10046. The disappointed frog alternates poses15 and16 twice, with sounds10051/10052 and10-tick pauses (`83EB..84C7`).

## Victory and introduction

Native settled victory: `early-win/state/win-settled.png`, phase17, node9. It shows the identified full song, title and picture on a large two-staff score; player and frog stand below. Original background is MODULES2350/SHPL2340. Frog/player idle origins are `(113,112)` and `(145,110)`. The native introduction uses this same scene without the revealed song.

Victory is independently reconstructed with zero mismatches by `render-win.py win-settled`. Exact recipe:

1. Opaque MODULES2350/2340 at `(0,0)` and TH8/6 exit at `(304,1)`; no separate return icon.
2. Song picture at `(30,16)`, opaque, with the same packed icon mapping as the chooser.
3. Title from MODULES STRL101 decoded array index songId, TH FONT1 at `(55,25)`, black, glyph-width advances. Its layout rectangle is `(23,55,36,320)`.
4. White score rectangle `(37,30,112,242)`. Two staffs start `(30,38)` and `(30,77)`, width211 pixels; five lines separated6 pixels, left vertical bar, clefs at `(32,37)` and `(32,76)`.
5. Draw `SONG.header[1]` events,15 per row. Note head x=`52+13*(i%15)`, y=`66+39*floor(i/15)-smallPitchOffset`. Rest origin x=`47+13*(i%15)`, y=`38+39*floor(i/15)` plus rest offsets. All other note semantics match the advanced piano renderer.
6. Fill `(96,1,120,28)` white and draw MODULES2357/2340 at `(2,101)`; fill `(54,272,78,299)` white and draw MODULES2358/2340 at `(273,56)`. These are colored sprites, not monochrome masks. Existing arrows are part of the background.
7. Draw player20004 at `(145,110)`, frog22004 at `(113,112)`, then cursor.

Sources:862D, shared score1C73, button transformations8535/8583, resident rectangle-centering6CEE.

## Data offsets and observed state

All constant maze offsets below are relative to image **0x2F9F0**. `export.py` is the reproducible table extractor.

| Offset | Structure |
|---|---|
|000|2Ã—5 enabled-type bytes|
|00A|2Ã—5 challenge-set counts|
|014|6Ã—s16 movement step sizes|
|020|9Ã—4 neighbor bytes|
|044|10Ã—(s16 y,s16 x) centers|
|06C|9Ã—4Ã—(s16 y,s16 x) sign origins|
|0FC|Victory frog footpoint|
|100|9Ã—4Ã—(s16 y,s16 x) sign actor targets|
|190|10Ã—4 paths, six packed(s8 direction,u16 distance) each|
|460|Two special actor points|
|468|Song title rectangle|
|470|9 UI rectangles|
|4B8|7Ã—3 rhythm patterns|
|4CD|7Ã—4 rhythm sets|
|4E9|8Ã—2 pitch patterns|
|4F9|10Ã—4 pitch sets|
|521|6Ã—3 melody patterns|
|533|6Ã—4 melody sets|
|54B|9Ã—2 accidental pitches|
|55D|9Ã—2 accidental flags|
|56F|2Ã—8Ã—4 accidental sets|
|5AF|2Ã—17 challenge-note y offsets|
|5D1|Two sound durations,25/50|
|5D3|Mutable first-introduction flag|
|5D5|Two clip rectangles|
|5E5|6 offscreen extensions|

Resident actor constants are image2F0C0: opposite directions+0 (6s16), dimensions+C (4s16), vectors+14 (6pairs). Animation tables are image321D0: delay+542, first+554, count+588, mirror+5BC, reverse+5CE, walking IDs+C90.

Observed mutable maze state begins at image31690. In these capture RAM0 dumps, add **544** to image offsets (state at318B0, resident DS323F0). Far-pointer segment words in captured RAM use a different relocation: subtract0x1A8 paragraphs before converting to original image offsets. Do not interpret them as direct offsets into the serialized RAM dump.

| State offset | Value |
|---|---|
|000|6 eliminated-song bytes|
|026|u16 challenge type|
|0A8|u16 difficulty|
|922|6u16 candidate song IDs|
|996,99A,99E,9A2,9A6|No-repeat masks for rhythm,pitch,melody,accidentals,family|
|9AC|u16 guess lock|
|9AE|u16 secret slot|
|9BA,9C2|Actor0/1 rectangles|
|9D4|u16 current node|
|9D6|u16 excluded reverse direction|
|9E0|Two type-cycle masks|
|9E4|u16 supported type count|
|9E6|u8 earned notes|
|A10|u16 correct streak|
|A16|u16 correct direction|
|A1E|4u16 candidate patterns/instrument IDs|
|A8C|u16 wrong attempts|
|B34|u16 phase:8 playing,17 victory|

Resident DS+573A stores four wrong-sign flags; +2018/+201A are the idle timers; +2064 is pointer(y,x).

## Evidence limits and implementation order

The recovered static rendering and model are sufficient for a complete playable independent maze: implement graph/challenges, target audition, earned score, guess selection, and win/new-game/return. Then apply path/actor/reward animation tables and tick sequencing. Preserve separate modern readable labels/accessibility around the native320Ã—200 scene.

What is proven: all challenge geometries, notes0..7, exact chooser and settled victory, ordinary full progression, an early win, guess lock behavior, source-defined graph and animation tables. What still needs native comparison: every transitional animation frame, audio waveform/tick alignment, selection behavior under alternative audio backends, and all interruption paths. Do not call the ten exact screenshots a complete animation parity result.
