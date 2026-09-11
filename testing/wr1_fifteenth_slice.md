# Fifteenth slice: complete song-repeat execution time

Python and Godot now match all 9,641 complete INT 63h services in the WR1.5
full-song recording, including its repeat and the following notes. Completion
time, every modeled hardware field, register writes, sequencer state, and voice
state agree. Music and voice state advance from one initial checkpoint;
hardware remains initialized independently at each service entry.

The repeat service takes **596,049 cycles / 22.075889 ms** and writes 101 OPL
registers: the final drum write followed by the 100-write reset. This interval
crosses more than one timer period. It is computed from the initialization
path and hardware state, not supplied as a measured wait.

## Recovered initialization path

The work planner now includes track completion, the CMF restart call, segment
normalization, instrument reset, clearing voice/track arrays, copying seven
CMF instruments, and decoding the stream's initial delay. Static instruction
metadata is still extracted from the supported executable and contains no
operands, executable bytes, or recorded paths.

The driver word at CS:11 controls timer ownership. It is observed as **1**
throughout this recording. In that mode, the helper at file 1f890 returns
without programming the PIT: the game owns its interrupt period. The new
fixture carries this measured mode once, and preparation rejects changes
between services. Unknown/internal timer mode is not silently treated as 1.

## Repeated memory operations

DOSBox's `dyn_string` first charges the pending instruction work, then one
cycle per memory element. Its checked-memory helper subsequently restores
`decode.cycles` to one, even when no memory fault occurs. That cycle stays
pending after REP and is charged at a later block exit.

The first repeat model missed that pending cycle, making the whole service
12 cycles short. Observation hooks around its 12 REP operations established
the local result: a count of 16 takes 18 observed cycles; counts 9, 11, and 32
take 11, 13, and 34 respectively. Every after-REP hook has one cycle pending.
The source's `dyn_check_bool_exception_al` explains the additional cycle.

The hardware work executor now separates decoded block length from pending
cycle count, since REP resets the latter without restarting the translated
block. It also follows the source's budget-exhaustion/re-entry behavior. The
12 observed repeat operations did not require re-entry; that branch has not
yet received an isolated native crossing test.

The native before/after REP states are retained as independent experiments in
the same fixture. Both Python and Godot match their complete modeled hardware
state as well as the enclosing service. No compensating per-operation offsets
or recorded future schedules are used.

## Evidence and checks

- Native evidence: `testing/output/wr1_repeat_hardware_native.json`, `.jsonl`,
  and its immutable matching `.map`.
- Fixture: `testing/fixtures/wr1_music_hardware_repeat.json.gz`, containing
  9,641 paired music services and 12 paired REP experiments.
- Observer changes: the timer-mode field and selected REP/helper boundaries;
  maintained in `tools/wr1_core_trace.cpp` and `tools/wr1_core_trace.patch`.
- Nineteen focused Python tests pass in 14.424 seconds. Godot passes 2,809,541
  cumulative checks across the short, pre-repeat, full-repeat, and REP
  recordings. Those music intervals overlap.
- Existing OPL/hardware tests still pass at 380,296 cumulative checks.
  `git diff --check` passes.

Logs are `testing/output/wr1_fifteenth_python_tests.log`,
`wr1_repeat_music_godot_tests.log`, and
`wr1_fifteenth_hardware_godot_tests.log`.

## Remaining clock integration

The surrounding game interrupt advances the speaker sequence, chains to the
BIOS on a countdown, acknowledges IRQ0, and returns to the main loop. Its
disassembly is retained at `testing/output/wr1_outer_irq_disassembly.txt`.
The BIOS callback's instruction template is in DOSBox's `callback.cpp` under
`CB_IRQ0`; its C++ timer handler and installation are in `bios.cpp`.

These surrounding operations and interrupt delivery need to be modeled before
the music-service model can replace the gameplay gate. The 122 recorded
admission residuals remain open. This result does not claim one continuous
hardware timeline from the playable-level checkpoint, complete WR1.4/WR1.6
music coverage, native PCM parity, or runtime audio integration. Remaining
gameplay routes/levels, original menus, and the ending also remain in scope.
