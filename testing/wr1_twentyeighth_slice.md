# Twenty-eighth slice: movement work before contacts

The Python and Godot movement work planners reproduce 177 independently
captured admission-to-contact intervals. Each receives the initial movement
state, live attribute columns and hardware checkpoint once. It generates the
executed instruction spans and resulting state from the original rules, then
matches the native endpoint cycle and all modeled hardware fields.

The interval begins at main 0096:0444 (file 37A4), including the update timer
reset, and ends before the contact call at 0096:0A1E (file 3D7E). It includes
previous-coordinate storage, support sampling, vertical movement, animation,
idle counters, left/right collision loops, speaker effects, the exit-position
check and bottom-of-map branch check. It does not include contacts or entities.

## Evidence and coverage

Three captures share the current observation-only core build, each with its
own preserved metadata, JSONL trace and copied immutable linker map:

| Capture prefix under testing/output | Replay | Intervals | Guest-cycle duration |
|---|---|---:|---:|
| wr1_movement_work_native | wr1_medium_drip | 65 | 102..199 |
| wr1_movement_walk_jump_native | exploration_controlled | 71 | 94..211 |
| wr1_movement_held_jump_native | wr1_jump | 41 | 94..195 |

Fixtures are `wr1_movement_work.json.gz`, `wr1_movement_walk_jump.json.gz` and
`wr1_movement_held_jump.json.gz`. `prepare_wr1_movement_work.py` validates capture
hashes, the fixed CPU configuration, main stack identity, mapped callbacks and
paired endpoints. It rejects IRQ/input preemption or unfinished intervals.
The default start call is 561 for the drip route; the two level-1 routes use
351. Comparisons occur after loading.

The drip route includes 39 neutral, 21 right, three down and two down+right
updates, including two climbing-down updates. The walk/jump route includes
28 neutral, 27 right, 12 left and four up+right updates, with seven footstep
starts and both walking-index wrap directions. The held-jump route exercises
one jump-sound start, one held-Up descent, 19 release-stop branches and 11
support-stop branches. No captured interval exercises a ceiling collision,
horizontal wall rollback, climbing up, simultaneous left+right, an enabled
exit position, a modal recap or the bottom-of-map bypass.

The native observer now records main-frame idle/walking counters, support,
saved coordinates and speaker pointer identity at movement entry and exit,
plus live attribute columns at entry. Attribute bytes are not reconstructed
from rendered pixels or assumed to match a static level file after contacts.

## Implementation

`tools/wr1_movement_work.py` and `scripts/wr1_movement_work.gd` implement the
same source-derived paths. The instruction catalogue now includes two aligned
movement ranges, excluding the idle jump table bytes, and the original left,
right and facing-dependent pose tables.

The work preserves the asymmetric collision loops: left stops after the first
rollback; right continues and reads the shifted column. Movement uses signed
16-bit arithmetic and original instruction order. Climbing, jumping, falling,
idle pose changes and horizontal movement can overwrite one another's frame.
No future observed frame or instruction path is supplied to the planner.

Speaker behavior also contributes work. Supported movement paths compare the
live far sound pointer with DS:04F6/0526, stop the speaker through IN/OUT 61,
start the jump sequence at DS:04F6 or a footstep at DS:04EA, and change the
speaker sequence index. These resulting pointers/indexes are checked against
native state. Composing with the later IRQ clock will also require carrying
the selected sound sequence data, not just its index.

Modal recap, out-of-map attribute reads, invalid animation indexes and the
bottom-of-map death bypass remain explicit unsupported boundaries. These
work planners do not yet service interrupts in the middle of movement; the
fixtures validate that none occurred in the measured short intervals.

## Validation and remaining integration

The 44-test focused regression suite passed in 87.926 seconds after adding
the first two movement fixtures (`wr1_twentyeighth_python_tests.log`). The
additional held-jump fixture then passed with all three movement tests in
0.158 seconds (`wr1_movement_work_python.log`). Godot verifies all 177 movement
intervals with 22,185 checks and zero failures (`wr1_movement_work_godot.log`).

The preceding renderer/display/idle composition remains exact for its 64
ordinary intervals. Movement is now independently exact for these 177
intervals. Connecting them still requires contact work at C1AA and entity/action
work at 50E8, including any resulting graphics, score, sound or RNG changes.
The main contact call/return are 3D7E/3D83, then the speaker idle stop check at
3D83..3D97, entity call at 3D99, and renderer call at 3D9E.

The runtime gate has not been replaced and the older 122 admission-frame
residuals remain open. There is no new framebuffer comparison in this slice.
Broader gameplay/renderer branches, original audio output, levels, characters,
difficulties, menus and ending remain necessary before claiming an exact clone.
The goal remains active.
