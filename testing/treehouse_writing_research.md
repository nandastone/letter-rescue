# Treehouse writing/drawing activity research

Date: 2026-09-27. Primary sources are the pinned DOS v1.1 executable, original
resource archives, and native captures made during this investigation. All
coordinates refer to the 320 by 200 original framebuffer. This slice edits
research notes and ignored scratch only; it does not change the runtime.

## Scope correction: resident chalkboard, not a typewriter

The inspected original implements a **resident chalkboard drawing activity**
inside the main room. No separate writing/typewriter text editor has been
identified. The four main activity entries dispatch to music (room index 1),
nature (2), theater (13), and board games (14). The room's chalk tray indices
6 through 12 dispatch to resident code `0x16F9`, not an overlay.

The executable contains the explicit prompt `Erase Chalkboard?` at main image
`0x3242C`. Searches of the executable's printable strings found no writing,
typewriter, or text-editor prompt. The room input loop contains no identified
text insertion, text buffer, caret movement, selection, or wrapping behavior.
This is bounded negative evidence, not proof about every platform/release.
A proposed modern enlarged editor should therefore be a drawing canvas. A text
editor would be a new feature, not reconstruction of the identified activity.

The original initial screen is the ordinary interior. No new full-screen
background, options modal, or editor overlay is opened when taking chalk.

## Exact tools and regions

The room's rectangle table is main image `0x2E938`. Rectangles use exclusive
bottom/right, ordered `(top,left,bottom,right)`.

| Room hotspot | Tool | Bounds | VGA palette entry |
| ---: | --- | --- | ---: |
| 6 | White chalk | `(92,63,98,73)` | 5 |
| 7 | Red chalk | `(92,75,98,85)` | 62 |
| 8 | Yellow chalk | `(92,87,98,97)` | 37 |
| 9 | Violet chalk | `(92,99,98,109)` | 3 |
| 10 | Green chalk | `(92,111,98,121)` | 44 |
| 11 | Pink chalk | `(92,123,98,133)` | 11 |
| 12 | Eraser | `(92,135,98,149)` | 0 |
| 25 | Erase entire board, with confirmation | `(86,49,97,59)` | — |

The seven palette indices are bytes at main image `0x2EA85`; VGA colors are
from **TH64 SHPL 4**. The fallback EGA-color table is main image `0x2EA7E`:
`[15,1,2,12,14,6,0]`. Resident `0x31DE` chooses the appropriate color through
`0x7308` depending on display mode. VGA RGB values:

| Tool | RGB |
| --- | --- |
| White | `(255,255,255)` |
| Red | `(255,0,0)` |
| Yellow | `(247,247,32)` |
| Violet | `(101,4,255)` |
| Green | `(8,170,0)` |
| Pink | `(255,199,199)` |
| Eraser | `(0,0,0)` |

Two additional original rectangles:

- Drawing clip: main image `0x2EA30`, **`(45,60,92,154)`**, size 94 by 47.
- Tool retention region: main image `0x2EA38`, **`(40,52,97,157)`**.

Leaving the retention region returns the current tool to its tray, sets
`DS:15E8 = 0`, selects the normal arrow cursor, and resets cursor color to 14.
Selecting a tool sets `DS:15E8 = toolIndex+1`, where the eraser is index 6.
The pointer is `DS:2064` y, `DS:2066` x. The prior brush point is stored through
`DS:49E2`, segment-relative offsets `44` y and `46` x.

## Exact drawing operation

Main loop `0xD91..0xF36` checks for an active tool and changed pointer position.
With left mouse held it builds a rectangle, clips to `(45,60,92,154)`, and fills
with the chosen color. These dimensions are verified from helper `0x6BF4` and
native pixel reconstruction:

- Chalk: **2 by 2**, `[x−1,x+1) × [y−1,y+1)`.
- Eraser: **6 wide by 10 high**, `[x+1,x+7) × [y+1,y+11)`.

The bottom-right calculation uses the already-offset top-left, not the raw
pointer. Reading the constants without following this dependency incorrectly
suggests 3 by 3 chalk or a 10-wide eraser.

For colored chalk, if both prior coordinates are nonzero, the code clamps each
new pointer axis independently to the previous coordinate plus or minus 2,
then writes the clamped point back to the mouse driver (`0xE22..0xE86`). It
stamps at that clamped position. This is **not arbitrary-distance line
interpolation**. Eraser skips the two-pixel movement clamp. Native capture with
one `dx=70` mouse action while held moves the original pointer from x80 to x82,
not x115; the lost distance is not replayed in later frames.

Without left mouse held, the prior brush coordinates reset from `DS:15F8`.
The native click-at-rest capture does create the expected 2 by 2 initial stamp
through the original input loop; browser adaptation should not suppress all
click-only drawing.

After drawing, `0x6350` copies the board region into its retained image buffer
(`DS:52D2`) using resident rectangle copy `0D51:7E32`. This is bitmap state,
not a list of text characters. No sound call was identified on the drawing
path; `0x6350` is a backing-store update, not an audio routine.

## Cursor and tray rendering

Original chalk cursor is **TH CURS 3**, eraser cursor **TH CURS 4**. Both are
68-byte cursor resources with `(hotspotY,hotspotX)=(0,0)`, then sixteen AND-mask
words and sixteen foreground-mask words. Their draw origin is the pointer
itself. Chalk foreground is the chosen chalk color; eraser foreground is white
(15). Cursor bit composition follows the already-recovered original cursor
operation. The normal arrow is CURS 0, embedded in the executable, with hotspot
`(-1,-1)`; TH CURS 1 is also an arrow resource.

Taking a tool first restores the previously held tool, then alters the new
tray slot using rectangles, not a new bitmap. From its original slot rectangle:

1. Fill `(top,left,bottom−5,right)` black.
2. Fill `(top+1,left,bottom−3,right)` gray, TH64 SHPL 4 index 25
   `(105,105,105)`.

This leaves a two-pixel gray line at y93..94 where the chalk had been. Normal
chalk return fills `(top+1,left,bottom−3,right)` with that chalk's color.
Eraser return `0x2785` instead fills `(top,left,bottom−3,right)` black, then
`(top,left+1,bottom−5,right−1)` white, then
`(top+1,left+1,bottom−3,right−1)` EGA gray 7 `(170,170,170)`.

## Clear whole board

Room hotspot 25 enters `0x167B`, manages the room's active animation state,
and invokes confirmation routine `0x285F` with original string
`Erase Chalkboard?`. If accepted, it fills the drawing clip with eraser color
and updates the retained board image via `0x6350`. Do not clear the outer
chalkboard frame or tray. Confirmation is original behavior; this note has not
yet recovered that generic dialog's exact button layout.

## Native evidence and exact small-region comparison

Ignored scratch: `testing/output/treehouse/research-writing/`.

- `chalk-route.json` enters the room, selects red chalk, moves to `(80,69)`,
  clicks, and supplies one large held horizontal mouse delta.
- `chalk-capture/` retains native callback frames, PNG snapshots, states, RAM,
  content/core hashes, and original clock samples. It completed with 3,240
  callbacks and 226 unique images.
- `check-brush.py` independently composes a black background region, original
  CURS 3, and 2 by 2 red stamps. It matches each of `chalk-position`,
  `chalk-dot`, and `chalk-stroke` in all **600 compared pixels**. The compared
  region `(top65,left75,bottom85,right105)` avoids unrelated animated room
  objects; the comparison is explicitly a region check, not a whole-frame
  fidelity claim.

The parent has the already-established exact original room renderer. The new
activity only requires persistent board pixels, faithful tools/cursors/tray
changes, clipping, return-on-leave, and the native clear action. An enlarged
modern canvas can operate on the same 94 by 47 backing bitmap.

Eraser follow-up: `eraser-route.json` and `eraser-capture/` extend the same route,
select the eraser, erase the red marks, and move outside the board. Capture
completed with 3,470 callbacks and 231 unique images. `eraser-picked` has
`DS:15E8=7`; `erased` has pointer `(77,67)` and tool 7; `tool-returned` has
pointer `(168,118)` and tool zero. `check-eraser.py` independently reproduces
the erased black board and original CURS 4 with **zero differences in the
same 600-pixel region**. This confirms cursor composition and return behavior.

## Follow-up: balloons overlap the initial board

The balloons visible over the initial board are a **separate resident actor**,
not pixels belonging to the chalk bitmap. Correct scene order is background,
retained chalkboard bitmap, then room actors including the balloons. Drawing a
black board after all room actors erases the balloons incorrectly.

Room setup at `0x2074..0x2090` initializes the board backing image on first use
or restores it on later entries. The buffer handle is `DS:52D2`. Balloon type 6
is in the resident actor array, `DS:5830`, stride 20 bytes. The type is the first
word; bounds `(top,left,bottom,right)` are the four words beginning at record
byte offset 6. TH SHAP 905 / SHPL 900 is 29 by 38 and is drawn at the actor's
left/top.

Taking any chalk or eraser calls `0x8CF4(retentionRect,1)` at `0x16F9`. This
finds actor type 6 with `0x86F8`, expands the supplied rectangle by top−2 and
bottom+2, then repeatedly moves the balloon bounds **up two pixels** and
redraws through `0x8B45` until the rectangles no longer intersect. Each step
sets countdown `DS:2016=2` and waits for zero. It moves the balloons away from
the drawing area; it does not clear their bitmap as chalk marks.

For the board, the expanded avoidance region is `(38,52,99,157)`. In the native
chalk route the balloon bounds are:

| Snapshot | Balloon bounds |
| --- | --- |
| `after-click` | `(43,96,81,125)` |
| `chalk-pointer` | `(45,95,83,124)` |
| `chalk-picked` (mid-lift) | `(9,95,47,124)` |
| `chalk-position` and `chalk-stroke` | `(-1,95,37,124)` |

The final y depends on starting parity: the rule is repeated −2 until the
balloon bottom is at or above 38. Do not hardcode disappearance or y=-1.

Balloon movement `0x89BD` exits immediately while a drawing tool is held
(`DS:15E8 != 0`). Returning the tool allows the ordinary pointer-following
behavior to resume; it does **not** restore the initial balloon position.
`eraser-capture/state/tool-returned` has balloon bounds `(1,96,39,125)` after
the first resumed movement.

Resident idle movement targets `(mouseX,min(mouseY,100))` using the balloon
rectangle's center. Each axis normally moves one pixel toward the target;
the dominant-distance axis moves two. An axis with distance less than two
does not move. `0xB8A3` assigns balloon type 6 its next update at current tick
plus `0x30` (48). This behavior is resident actor logic, not an SCR pose script.
The timed two-pixel clearance movement and autonomous follow should be kept
distinct when reproducing original frame timing.
