# WR1 player animation and RNG research

2026-09-07. Static analysis of [WR1.EXE](<D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)/WORD/WR1.EXE>), SHA256 `b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`. Code addresses below are file offsets. `DS:` addresses use the data-segment convention established in [movement research](wr1_movement_research.md).

This pass recovers the animation rules needed for an ordinary walk/jump comparison, the exact original sprite rectangles, and the RNG state recurrence. It does not change the clone.

## Primary evidence

- [Animation branches, data tables, and decoded idle jump table](output/wr1_animation_evidence.txt), reproduced by [this script](output/wr1_animation_disasm.py).
- [Sprite metadata and loader instructions](output/wr1_sprite_metadata.txt), plus [machine-readable source rectangles for both characters](output/wr1_player_sprite_rects.json).
- [RNG recurrence, seed calls, multiplication helper, and DOS time/date helpers](output/wr1_rng_evidence.txt).
- [Movement disassembly](output/wr1_movement_evidence.txt) supplies the surrounding vertical-position updates.

The animation evidence also includes the RNG entry points; the separate RNG evidence supplies the multiplication and seeding helpers. Branch-table bytes at `0x3ba1–0x3bd4` are decoded as 26 little-endian near addresses, not x86 instructions.

## Animation state and initialization

| Storage | Meaning |
|---|---|
| `DS:1c3` word | Current sprite frame 0..25. |
| `DS:1c1` word | Jump phase used by movement and rising/falling frame selection. |
| `DS:9e82` word | Facing: 0 right, 1 left. |
| Main function `[BP-8]` | Idle update counter. |
| Main function `[BP-0xa]` | Right walking sequence index. |
| Main function `[BP-0xc]` | Left walking sequence index. |

At main-function entry `0x3484–0x3493`, both walking indices are -1, facing is 0, and idle counter is 3. Separately, level/game setup at `0x4e7d–0x4e83` assigns frame 0 and facing 1. Thus function-entry facing 0 is not sufficient to establish the first playable frame's facing. No per-update RNG is involved in player animation selection.

Frame 9 is unconditionally changed to frame 0 at the start of the movement update (`0x37b3–0x37ba`), before the later animation rules can overwrite it again. No corresponding unconditional frame-19 reset exists there.

## Walking

The data at `DS:1cd` and `DS:1e1` is:

```python
left_walk  = [13, 14, 14, 15, 16, 17, 17, 18]
right_walk = [ 3,  4,  4,  5,  6,  7,  7,  8]
```

Left handling at `0x3c59–0x3c8d` sets facing=1, sets right index=-1, increments left index, and wraps values above 7 to 0. Right handling at `0x3cd5–0x3d09` symmetrically sets facing=0, resets left index, and advances the right index. Both reset the idle counter to zero (`0x3c1e`, `0x3cd0`).

The selected walking frame is written only if **player render Y equals its saved pre-movement Y** and the current frame is **not 9** (`0x3c74–0x3c82`, `0x3cf0–0x3cfe`). This compares Y before camera scrolling; it is not a grounded-state check. A blocked upward move can also leave Y unchanged.

The indices advance even when a wall prevents horizontal movement or when vertical movement suppresses the visible walking frame. This matters after a jump: the walking cycle has continued invisibly while airborne. Left and right are handled sequentially, so pressing both also affects both indices; do not reduce this to one normalized horizontal axis.

At the default approximately 12 Hz gameplay rate, the eight-index cycle is approximately 0.6666 seconds. Frames 4/7 or 14/17 each occupy two update slots; the others occupy one. This is not an independent animation timer.

## Jumping, falling, and climbing

The facing-dependent table is eight words at `DS:1f5`:

| Facing | Start jump | Rising | Return/landing pose | Falling |
|---|---:|---:|---:|---:|
| Right (0) | 9 | 10 | 9 | 25 |
| Left (1) | 19 | 20 | 19 | 24 |

The row base is `DS:1f5 + facing*8`. The four entries are read at offsets +0, +2, +4, +6.

- Holding Up with support sets the start-jump frame and phase=0 (`0x38d5–0x38f3`).
- Holding Up without support selects the rising frame when phase<9, otherwise the falling frame (`0x38fb–0x3933`). The descending held-Up branch writes the falling frame again at `0x39d1–0x39e7`.
- Without Up, the unsupported/down-through branch selects the falling frame unless the climb-down pattern applies (`0x3a26–0x3aa3`).
- Climbing alternates frames 22 and 23 on each qualifying update: if current frame is 22 choose 23, otherwise choose 22. Up-climbing does so at `0x38ac–0x38bb`; down-climbing at `0x3a76–0x3a85`. Exact attr patterns are in the movement report.

All vertical frame choices use facing **before** this update's horizontal handling changes it. Therefore a left/right reversal during a jump can change position direction immediately while the airborne sprite still reflects the previous facing for one update. A faithful implementation must preserve this ordering.

For an unobstructed held jump with no other interactions, the frame pattern is start once, rising for the remaining rising updates, then falling. Ceiling collisions, simultaneous direction input, or releasing Up can alter this because later branches can overwrite the earlier choice.

## Idle and landing transitions

The idle block (`0x3b03–0x3c14`) runs only when none of Up/Down/Left/Right is held. It increments the idle counter once. Down alone skips this block but does not itself reset the idle counter; Up and horizontal handling do reset it elsewhere.

The following pseudocode decodes the branch table and preserves the original ordering. `support` means the pre-vertical-movement support sample from the movement block.

```python
if not (up or down or left or right):
    idle_ticks += 1
    if idle_ticks > 17:
        if frame < 2:
            idle_ticks = 0
            frame ^= 1
        elif frame < 22:
            frame = 0
            idle_ticks = 0
        elif frame in (24, 25):
            frame = facing_table[facing][2]  # 9 or 19
            # No idle counter reset in this branch.
        # Otherwise (22/23), retain frame and counter.
    else:
        if frame in (0, 1, 11, 21, 22, 23):
            pass
        elif frame in (10, 25):
            if support:
                frame = 9
        elif frame in (20, 24):
            if support:
                frame = 19
        else:
            if left_walk_index > -1:
                left_walk_index = 0
                right_walk_index = -1
                frame = 12
            else:
                right_walk_index = 0
                frame = 2
```

The jump table has exactly these cases: no-op `{0,1,11,21,22,23}`; support-to-9 `{10,25}`; support-to-19 `{20,24}`; default for other values. Out-of-range frame values above 25 also use the default branch. The actual instructions use signed word counters; the pseudocode assumes ordinary valid gameplay states without counter overflow.

Consequences for a short comparison:

- Releasing a walk gives facing-specific stopped frame 2/12 on the next eligible idle update, not immediately generic frame 0.
- The stopped branch resets the walking index to 0. Resuming the same direction increments it to 1 before rendering, so it can resume at frame 4/14 rather than frame 3/13.
- After 18 idle updates following a movement reset (nominally 1.5 seconds), a stopped/moving frame in 2..21 returns to frame 0. Subsequently frames 0 and 1 alternate every 18 eligible idle updates. The initial main idle counter=3 changes the first delay if no intervening reset occurs.
- Landing without direction input converts falling frame 25 to 9, or 24 to 19, when support is sampled. Frame 9's special start-of-next-update reset creates an asymmetry with frame 19. Do not replace these transitions with a single generic landing animation.

Other gameplay paths can overwrite the frame after this block: the action handler assigns frame 21 at `0x5133` and frame 11 for the alternate facing at `0x519e`; reset/death-related paths assign 0 at `0x58e7` and `0x5960`. These actions and exceptional animation sequences have not been fully reconstructed here.

## Exact sprite rectangles: correction to earlier report

The earlier `wr1_exe_research.md` described 28 records of 20 bytes and suggested the lower CHARS rows might be unused. **The actual character tables contain 26 records of 22 bytes.** The loader proves this independently: gender stride `0x23c`=572 at `0x9270`, record stride `0x16`=22 at `0x927e`, and loop bound `0x1a`=26 at `0x9292`.

Metadata base is `DS:884 + gender*572`. Each record is:

```text
u16 image_offset, image_segment
u16 derived_buffer_offset, derived_buffer_segment
u16 width, height
u16 source_x1, source_y1, source_x2, source_y2
u16 source_graphics_page
```

The helper at `0xa2d0–0xa332` uses dimensions at record +8/+10 and passes the source rectangle plus page at +12..+20 into the blitter. All player records describe 24x32 pixels. Sprite buffers advance 128 bytes per frame; those strides are buffer structures, not raw RGBA pixel storage.

Source page 2 contains `CHARS.WR`, loaded at `0x91aa–0x91b6`; page 5 contains `STATIC.WR`, loaded at `0x9bb0–0x9bbc`. The complete [JSON mapping](output/wr1_player_sprite_rects.json) lists every frame with source asset and rectangle. It is extracted directly from the binary metadata, not reconstructed from a guessed regular atlas layout.

- **Frame 0** comes from STATIC.WR: boy `(232,40,24,32)`, girl `(256,40,24,32)`.
- Frames **1..23** come from CHARS.WR. For boy, let `n=frame-1`: `x=(n%13)*24`, `y=(n//13)*32`. Girl uses the same X and Y+64. Thus the lower two CHARS rows are ordinary girl animations.
- **Boy frame 24** is CHARS `(288,32,24,32)`; **boy frame 25** is `(288,96,24,32)`.
- **Girl frame 24** is CHARS `(240,96,24,32)`; **girl frame 25** is `(264,96,24,32)`.

The special falling rectangles mean even correctly extracting the regular 24x32 grid can select the wrong final frames. Frame 0's separate STATIC source explains why a correct standing capture does not establish that the moving sprites are mapped correctly.

## RNG: exact recurrence and practical watchpoints

The RNG state is a 32-bit little-endian value at `DS:6378` (low word) and `DS:637a` (high word). Its initialized executable value is 1. It is within initialized DS data, unlike the higher BSS addresses.

Seed function `2155:000f` maps to file `0x23f5f`. It reads one 16-bit argument, writes that to the low word, and clears the high word (`0x23f62–0x23f6b`). Random function `2155:0020` maps to `0x23f70`:

```python
def seed(value):
    state = value & 0xffff

def rand():
    state = (state * 0x015A4E35 + 1) & 0xffffffff
    return (state >> 16) & 0x7fff
```

The multiply uses DX:AX for old state and CX:BX=`0x015a:0x4e35`; helper `0000:0408` at file `0x2e08` implements the low 32 bits of that multiplication using 16-bit partial products. The increment and return mask are explicit at `0x23f82–0x23f92`.

Normal seed calls at `0x97c7` and `0x9b32` take the AX result of `21c6:0046` with a null pointer argument. That routine at `0x246a6` reads DOS date/time via helpers issuing INT21 AH=2A and AH=2C (`0x23b36`, `0x23b4c`), then converts the result to a timestamp. Only the low 16 bits are passed to the seed routine. The complete timestamp conversion/epoch handling is not needed for state capture and was not decoded here.

Demo-related branches explicitly seed 200 at `0x34ad`, `0x36e4`, `0x3714`, and `0x50ff`; the last is at entity-update entry when demo mode is active. Therefore reproducing demo behavior is not just seeding 200 once and then letting the generator run forever.

Direct random-call sites found in gameplay/setup code:

| File sites | Confirmed use or scope |
|---|---|
| `0x4eb5`, `0x4ecb` | Word offset and picture offset selection; see matching report. |
| `0x6692`, `0xc4ca` | Loaded gruzzle and wrong-answer-spawn gruzzle variant, modulo 4. |
| `0x722a` | Word-list selection offset (`rand()%9+1`). |
| `0x5094`, `0x552a`, `0x553d`, `0x56c3`, `0x572c` | Entity initialization/update paths; detailed semantic conditions not fully mapped. |
| `0x5c79`, `0x5c86`, `0x7321`, `0x8877` | Other transition/setup paths; treat as additional state consumers until their conditions are traced. |

Capturing `DS:6378..637b` at the comparison start is more useful than guessing a seed from wall-clock time. For a first walking/jumping comparison, player movement/animation does not need RNG; initialize the same map, player/camera state, and sprite state. For longer full-game parity, capture or reproduce RNG state **and the call sequence**, because enemy/update/interaction paths consume the same generator.

## What is now ready, and what still needs measurement

The ordinary player step, frame choices, exact source rectangles, camera block, and nominal gameplay clock are specific enough to implement a faithful first walk/jump slice. More broad decompilation is not a prerequisite for that slice. Runtime traces should settle the first comparison boundary, initialization values, update/IRQ relation under the selected emulator, and whether other entities or interactions interrupt the chosen path.

Useful trace fields now include player frame `DS:1c3`, jump phase `DS:1c1`, facing `DS:9e82`, current render/grid/camera positions, speed threshold `DS:8e8f`, and RNG state `DS:6378`. The three local animation counters require the live main-function stack frame; they cannot be read at fixed DS offsets. Exceptional action/death frames, complete restart initialization, all RNG-consuming branches, palette changes, and the graphics-buffer implementation remain separate bounded follow-ups.
