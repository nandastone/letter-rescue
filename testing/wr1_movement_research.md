# WR1.EXE movement and timing research

2026-09-07. Static analysis of the original executable; no gameplay code or running game session changed.

The original uses **8-pixel movement steps on an approximately 12 Hz gameplay clock**, at the default speed setting. Its jump is a counter-controlled rise and fall, with 8-pixel vertical steps and up to nine rising updates. This is substantially different from the clone's continuous gravity model. These findings come from the executable's instructions, not from fitting screenshots.

## Evidence and address conventions

Primary source: [WR1.EXE](<D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)/WORD/WR1.EXE>), 176,958 bytes, SHA256 `b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`.

[Selected disassembly with instruction bytes](output/wr1_movement_evidence.txt) and its [reproducer](output/wr1_movement_evidence.py) support the file offsets below. [Keyboard interrupt disassembly](output/wr1_disasm_c700.txt) supports the key mappings. Broad exploratory disassembly files in `testing/output` include data decoded as instructions; the selected movement evidence avoids the known jump tables. Capstone's 16-bit `0x98`/`0x99` instructions are CBW/CWD, despite its displayed CWDE/CDQ spellings; the selected evidence corrects these labels.

All `0x...` code addresses here are **file offsets**, unless explicitly `DS:` or `segment:offset`.

- MZ header size is `0x2a0` paragraphs = `0x2a00` bytes. The relocation table has 2,625 entries and begins at file `0x22`.
- For a stored, unrelocated far pointer, `file = 0x2a00 + segment*16 + offset`. The main gameplay function at `0x347c` is `0096:011c`; its code segment begins at file `0x3360`. Near branches in the evidence are printed as equivalent synthetic file addresses.
- Startup at file `0x2a00` loads the relocatable value `0x2255`, then assigns DS at `0x2a14`. The initialized data image therefore begins at file `0x24f50`. The immediate at `0x2a01` is present in the MZ relocation table.
- The IRQ handler similarly loads DS using the relocated immediate at `0x434e`. A runtime debugger must add the process's MZ load segment to `0x2255`; using runtime DS=`0x2255` without this adjustment would address the wrong memory.
- DS offsets above the initialized-data end refer to BSS/runtime storage, not to bytes that can simply be read from the executable at `0x24f50 + offset`.

## Gameplay clock

| Instruction evidence | Meaning |
|---|---|
| `0x3402: mov word ptr [0x8e8f],8` | Default speed threshold is eight timer interrupts. |
| `0x9883: mov ax,0x308c; push ax`; far call at `0x9887` to `0172:015b` | Timer initialization receives divisor 12,428. This far call maps to file `0x427b`; its segment word is relocated. |
| `0x427e–0x4282` | Stores the first argument into `DS:c40f`. |
| `0x42ac–0x42b8` | Installs vector 8 at `0172:0224`, mapping to file `0x4344`. |
| `0x42bf–0x42c4` | Passes the stored divisor to timer-programming routine `0x42f9`. |
| `0x4301–0x4311` | Writes command `0x34` to port `0x43`, then low/high divisor bytes to channel-0 port `0x40`. |
| `0x4352` | IRQ8 increments `DS:f2e`. |
| `0x371b–0x3724` | Main loop waits until unsigned `DS:f2e >= DS:8e8f`. |
| `0x379f–0x37a4` | Clears the timer counter before this update's movement. |

Using the IBM PIT input frequency of 1,193,182 Hz from [DOSBox-X's timer implementation header](https://dosbox-x.com/doxygen/html/timer_8h_source.html), the nominal rates inferred from this binary are:

```text
IRQ frequency      = 1193182 / 12428 = 96.0075635661 Hz
default update rate = IRQ / 8       = 12.0009454458 Hz
default step time   = 8 / IRQ       = 83.326768255 ms
unblocked walking  = 8 px * updates = 96.0075635661 px/s
```

These are nominal simulation limits, not proof that every displayed frame or actual emulator run has this exact cadence. The main loop resets the counter to zero rather than subtracting eight: it does not catch up by running multiple movement updates after a long frame. Modal interactions, slow emulation, and rendering costs can change observed cadence. A 70 Hz capture is sampling this approximately 12 Hz gameplay clock.

The keyboard table maps scan code 13 (`=`/`+`) to handler `0xc89d`, setting `DS:1b2`; the main loop then decreases the threshold when positive (`0x35b9–0x35c4`). Scan code 12 (`-`) maps to `0xc8ad`, setting `DS:1b0`; the main loop increases the threshold (`0x35e1`). Thus speed keys can change the gameplay rate. Do not compare captures without controlling this setting. Threshold zero removes this timer gate; it does not define an infinite fixed rate.

## Variables and coordinates

| DS offset | Supported interpretation |
|---|---|
| `662e`, `6630` | Mutable player screen/render coordinates X and bottom Y. Copied to old-coordinate storage at `0x37a7–0x37b0`, moved during gameplay, and rendered at `0xb9f3–0xb9fa` with top-left `(X,Y-32)`. These are not merely initial positions. |
| `9790`, `97a8` | Previous update's render X/Y. |
| `83f6`, `83f8` | Player grid X/Y in the 8-pixel attribute grid, abbreviated `gx,gy` below. |
| `8480`, `8482` | Camera X/Y in 8-pixel units. |
| `1c1` | Jump phase/elapsed-update counter, capped at 16. |
| `1c3` | Player sprite-frame index. Render uses `frame*128` at `0xba01–0xba0b`. |
| `9e82` | Facing index: left sets 1; right sets 0. |
| `190`, `192`, `194`, `196` | Up, down, left, right held states respectively. Keyboard interrupt writes 1 on make and 0 on break. |
| `9afa` | Far-pointer array for attribute columns. **Corrects `9cfa` in the earlier report.** |
| `9778`, `9792` | Attribute dimensions, each twice the level header's background dimensions. |

The coordinate conversion at `0x50bf–0x50e0` is:

```text
gx = trunc_toward_zero((X - 16) / 8) + cameraX - 1
gy = trunc_toward_zero((Y - 31) / 8) + cameraY
```

The original attr map is already an **8x8-pixel grid**. The loader doubles the header dimensions at `0x64e1–0x64f8`, then writes each RLE-decoded attr byte to `A[i % width][i // width]` at `0x6a4b–0x6a6f`. This is column-pointer storage for a row-major stream. It does not derive collision from rendered 16x16 background tiles.

At level load the render coordinates are `(startX-cameraX)*8+16`, `(startY-cameraY)*8+40` (`0x65ca–0x65f6`). This loading convention and the runtime grid conversion must both be preserved when choosing a clone coordinate origin.

Keyboard mapping is explicit: scan codes 72/80/75/77 dispatch to `0xc8d6/0xc8cd/0xc8df/0xc8e7` and write the four directional states. Space (scan code 57) dispatches to `0xc8bd` and sets the separate action `DS:19e`. **Up is the jump/climb action; Space is not the up/jump state in this executable.** User-defined keys can also map through `DS:1b4..1b8` (`0xc762–0xc7c8`).

## Movement order and collision

The main update handles vertical motion first, increments the jump counter, updates idle animation, processes left, then independently processes right. It next checks exit/bottom conditions, calls interaction processing at `0x3d7e` (target `0xc1aa`), entity/action processing at `0x3d99` (target `0x50e8`), and rendering at `0x3d9e` (target `0xab25`). Simultaneous left and right are therefore sequential attempts with collision checks; they are not collapsed to a normalized axis.

Define `A[x][y]` as the raw attribute byte. `0x73` is solid. `0x74` provides support, permits downward traversal, and participates in climb detection; describing it as only a one-way platform omits behavior.

### Horizontal motion

```python
# 0x3c14–0x3c59: left
if left:
    X -= 8
    gx -= 1
    for row in range(gy - 4, gy):
        if A[gx][row] == 0x73:
            gx += 1
            X += 8
            break
    facing = 1
    # Advance left walk animation even if the move was blocked.

# 0x3c90–0x3cd5: right
if right:
    X += 8
    gx += 1
    for row in range(gy - 4, gy):
        if A[gx + 2][row] == 0x73:
            gx -= 1
            X -= 8
            # Original has NO break here: subsequent rows re-read gx+2.
    facing = 0
    # Advance right walk animation even if the move was blocked.
```

This inspects four 8-pixel rows along a leading edge of a three-column footprint. No acceleration, friction, fractional position, swept collision, or diagonal normalization appears in this movement block. The missing break in the right loop is visible in the branch from `0x3cbe` through `0x3cc9`; preserve it for exact emulation until a runtime test establishes its practical effect. It can matter if multiple sampled solid cells still exist after the first undo.

Walking animation uses eight-entry sequences: left `13,14,14,15,16,17,17,18` from `DS:1cd`, right `3,4,4,5,6,7,7,8` from `DS:1e1`. Each direction has a local index initialized to -1 and reset to -1 by the opposite direction. It updates the sprite only when render Y equals its pre-update value, and current frame is not 9 (`0x3c5f–0x3c8d`, `0x3cdb–0x3d09`). These are original sprite indices, not necessarily clone atlas indices.

### Vertical movement: executable-equivalent core

This pseudocode excludes sound and sprite-selection side effects, but retains the movement/control order in `0x37c5–0x3b03`:

```python
support = A[gx + 1][gy]
if support not in (0x73, 0x74):
    support = 0

if up:
    climbing_up = (
        (support == 0x74 and A[gx + 1][gy - 2] == 0x74)
        or (A[gx + 1][gy - 1] == 0x74
            and A[gx + 1][gy - 3] == 0x74)
    )
    if climbing_up:
        frame = 23 if frame == 22 else 22
        phase = 0
    elif support != 0:
        phase = 0
        # Also chooses jump-start frame from the facing table.
    else:
        # Choose rising/falling sprite according to phase < 9.
        pass

    if phase < 9:
        Y -= 8
        gy -= 1
        for col in range(gx, gx + 3):
            if A[col][gy - 4] == 0x73:
                Y += 8
                phase = 16
                gy += 1
                break
    else:
        Y += 8
        gy += 1
        # Choose falling sprite.

else:
    descend = (support == 0 or (down and support == 0x74))
    if descend:
        climbing_down = (
            (support == 0x74 or A[gx + 1][gy + 1] == 0x74)
            and (A[gx + 1][gy - 1] == 0x74
                 or A[gx + 1][gy - 2] == 0x74)
        )
        if climbing_down:
            frame = 23 if frame == 22 else 22
        else:
            # Choose falling sprite.
            pass
        # Corner adjustment before descending; note sequential gx writes.
        if A[gx][gy - 1] == 0x73:
            gx += 1
            X += 8
        if A[gx + 2][gy - 1] == 0x73:
            gx -= 1
            X -= 8
        Y += 8
        gy += 1

phase = min(phase + 1, 16)
```

The supporting cell is a **single center-column sample**, whereas ceiling checks sample three columns and side checks sample four rows. Landing/support is decided at the beginning of an update; this code has no general bottom sweep of the entire player rectangle. Sideways adjustments while falling happen only in the no-up branch (`0x3aa6–0x3ae8`). They do not appear in the held-up falling branch.

Movement implications, inferred from the above instructions and requiring runtime checks for exact observed trajectories:

- On normal solid ground, holding Up resets phase to 0 and gives nine rising steps (`phase` 0 through 8): **72 pixels maximum rise** without overhead collision or climbable tiles. The first falling step is the tenth movement update. Full rise occupies nine update opportunities, nominally about 0.75 seconds, with real first-input alignment affecting stopwatch measurements.
- Continued Up while landing starts the next jump on the next support-bearing update: **automatic repeat jumping** is present.
- Releasing Up causes immediate descending on the next unsupported update; there is no remaining upward velocity.
- Releasing Up **does not set phase to the falling half**. Phase still increments each update. Re-pressing Up while phase is below 9 can resume rising in the air. This is not a fresh full jump: it uses the remaining phase window.
- Walking off after standing long enough to saturate phase cannot start a fresh airborne jump; a supported Up update or climb pattern is what resets phase. Do not add an independent coyote timer on top of this.
- `0x74` climb patterns reset phase every rising update, allowing ascent beyond 72 pixels; jump height measured while touching climbable geometry is not a valid ordinary-jump measurement.
- Up takes precedence over Down because the down logic is only reached when Up is clear.

## Limits and useful next checks

High confidence: byte-level movement constants, ordering, tested cells, counter conditions, PIT divisor, default gate, loader attr dimensions, register/address arithmetic. These were independently checked against instruction bytes and MZ relocation sites. No debugger attached and no runtime memory trace was captured in this research pass.

Still to verify before claiming whole-game parity: camera thresholds/scroll order, temporary modal behavior when touching question blocks or letters, initialization across level transitions, how much rendering costs at selected DOSBox cycles, palette/sprite correspondence, and exceptional collision configurations. These can alter what a screenshot implies even when the movement block is understood correctly.

Recommended next implementation seam: a pure integer movement function accepting raw attr grid, held directional state, `gx/gy`, phase, and facing/animation counters, called on the original clock. Keep camera projection separate. Begin with unobstructed walking and ordinary jump/release/repress sequences, then verify the asymmetrical right wall loop and `0x74` climbing. Leave the existing pixel-perfect starting-frame placement untouched until coordinate conversion is tested against the same level origin.
