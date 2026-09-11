# Original runtime tracing is available

2026-09-07. Tested locally with RetroArch 1.22.2 (69a4f0e), DOSBox Pure
1.0-preview5 and the WR1.EXE hash recorded in the movement research.

We now have enough tools and measurements to begin bringing the clone's movement
and camera into agreement with the original. Full-game parity still requires
matching starting state, defining completed logical-update boundaries, and
connecting these state samples to the capture pipeline.

## Working interface

RetroArch supports UDP memory reads, pause/frame advance and replay metadata.
These were tested on the installed version, rather than inferred from current
documentation alone. [Official interface documentation](https://docs.libretro.com/development/retroarch/network-control-interface/).

DOSBox Pure exposes a rearranged address space: conventional game memory is first,
OS memory begins at exposed address 0x100000, and expanded memory at 0x200000.
Exposed addresses are therefore not raw DOS physical addresses. The source routine
is DBP_ReportCoreMemoryMaps. [Core source](https://github.com/schellingb/dosbox-pure/blob/main/dosbox_pure_libretro.cpp).

The installed build successfully returned a 512 KiB memory dump. Three 32-byte
code signatures from executable offsets 0x3c14, 0x37c5 and 0xac27 independently
located the same exposed load base, 0x220. The exposed DS base was consequently
0x22770. These are session observations, not hardcoded universal addresses.

[wr1_trace.py](../tools/wr1_trace.py) rediscovers the load address, checks the
executable hash, requires a paused core, reads named fields and writes JSON. It
does not write game memory. The optional --advance flag advances the frontend
between samples. The tool records the active replay's frame counter where available
and checks single-frame progression when advancing that replay.

Captured fields: directional held states, player render/world/grid coordinates,
jump phase, sprite frame, camera coordinates, timer counter and threshold, facing,
score, RNG state, and word/picture offsets. Main-function local animation counters
on the DOS stack are not yet captured.

## Measurements and validation

- Initial live snapshot: render position (144,112), world position (176,176), grid
  (19,18), camera (4,8), jump phase 4, sprite 10, timer 6, threshold 8, score 15,
  RNG 1178738697, word offset 5 and picture offset 0.
- An exploratory 100-frame trace showed 8-pixel horizontal steps, usually five or
  six frontend advances apart. This supports the approximately 12 Hz update rate
  inferred from the timer setup; elapsed host time while paused is not game time.
- The first prototype read separated memory regions once each. Some rows mixed
  position and phase changes across an update. The reusable tool therefore requires
  two identical consecutive reads of all sampled regions, with bounded retries.
- Twelve paused/advanced samples passed the stability check. A further 48 samples
  all stabilized in two reads and showed eight leftward steps of exactly 8 pixels.
  Their sprite sequence was 13,14,14,15,16,17,17,18, independently agreeing with the
  disassembled walking table. World X moved from 296 to 232, with world Y fixed at 208.
- A further six samples recorded replay frames 678 through 683 and passed the
  exactly-one-frame progression check.

Evidence under ignored testing/output: original_memory_probe.bin,
original_memory_mapping.json, original_memory_trace.json,
original_stable_trace.json, original_stable_movement_trace.json,
original_numbered_trace.json. The first trace is exploratory; use the stable-reader
outputs for state comparisons. The temporary probe session was separate from the
two normal game sessions and was closed after verification.

Two identical reads are a practical coherence check, not an atomic emulator
snapshot guarantee. A stable frontend-frame boundary can still be inside a DOS
logical update. Inputs may also change between logical updates. The eventual
comparator must identify completed updates, not call every observed phase/position
change a new gameplay tick. A small core hook or debugger remains an option if
frame-level sampling cannot unambiguously identify those boundaries.

## Reproduce

Start a task-owned RetroArch instance with both tools/retroarch.cfg and the optional
[trace overlay](../tools/retroarch_trace.cfg), separating appendconfig paths with
the supported pipe character. Use the same core, content and native replay. The
overlay enables commands on port 55445 without saving global config changes.

With RetroArch and Python on PATH, pause/advance once and read samples:

```powershell
retroarch --command "FRAMEADVANCE;127.0.0.1;55445"
python tools/wr1_trace.py --exe "D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)/WORD/WR1.EXE" --output testing/output/wr1_trace.json --samples 48 --advance
```

The probe used testing/output/exploration_controlled.replay. That exploratory
replay supports forward playback; do not assume its generated backreferences
support seeking. Capturing a known starting state and fixing the production replay
reader remain part of building a repeatable comparison harness.

## Further disassembly and implementation priority

[Animation and RNG research](wr1_animation_research.md) now adds exact animation
transitions, original sprite rectangles, RNG recurrence and seed sites. It corrects
the old sprite metadata assumption: 26 records of 22 bytes per character, with frame 0
loaded from STATIC.WR rather than CHARS. The original RNG is a 32-bit linear
congruential generator; its live state is readable, making startup synchronization
and later divergence investigation feasible.

No further broad decompilation is a prerequisite for the first walking/jumping
slice. Implement recovered movement, camera and animation; compare numeric state
before pixels. Extend targeted research where that comparison finds unexplained
differences. Enemy/slime rules, interaction timing and death/restart transitions
are the most useful remaining behavioral targets.
