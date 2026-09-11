# Ninth pass: compare from the first displayed level frame

Follow-up: [the tenth pass](wr1_tenth_slice.md) adds medium/hard hazards,
pit rescue, the boy character, 446 matching states and 18 new exact images.

Loading duration is excluded from gameplay parity. The level-two replay now
starts at one visually verified, playable checkpoint and runs without any
later synchronization or native state injection.

## Boundary and independent replay

The original finishes loading before its returned video shows gameplay.
Native counter **6378** still shows the loading title; counter **6379** is the
first complete level image. Counter 6380 shows the same image. This distinction
was verified with actual 320x200 screenshots, not inferred from ready flags.

`tools/prepare_wr1_level_start.py` validates the complete instruction trace and
paired frontend samples, then prepares an explicitly selected post-load slice.
It copies only the initial player/camera state, main-loop locals, actors/RNG,
pictures, puzzle rotations, word cursor, score and entrance countdown into the
replay. The checkpoint presenter does not advance the camera or animations.
The native initial image is `testing/fixtures/wr1_level2_start.png`.

The frontend and IRQ phases are calibrated from idle counters **6372..6419**,
after the original loader has reset its timer. The few observations before
the first visible frame constrain its initial phase; no loader duration is
modeled. The first movement input is counter **6420**, after calibration.
There are no moving-state observations or per-update timing schedules in the
runtime replay metadata. All later native states live only in the test fixture.

The slice runs from source frame 6379 through 6801: 423 frontend frames,
approximately six seconds. Its **72 completed gameplay updates** (native
818..889) have identical state, held inputs and admission frames. This includes
**65 updates after calibration**, walking both directions, two jumps, horizontal
and vertical camera movement, actor updates and collecting two books. Score
advances from 740 to 750. The initial state is checked separately as tick zero.

The prepared checkpoint currently requires an untouched puzzle, no active
effects or drips, and offscreen actors. It is a deliberately narrow fresh-level
test setup, not an arbitrary saved-game loader. Other initial scenes need their
presentation state accounted for before using this tool.

## A real rendering defect found and fixed

The initial image and early moving images matched exactly. At counter 6800,
the clone retained its pink entrance doorway while the original showed the
house beneath it: **1,238 differing pixels**, confined to the 32x40 entrance.

Disassembly resolves the cause:

- `WR1.EXE 0x4e77` initializes `DS:c3dd` to 60 on fresh and cached resets.
- `0xb4b1..0xb4cc` decrements it once per renderer invocation, including when
  offscreen. After decrement, values at most 10 draw only on render page one.
  A call beginning with zero does not draw the entrance.
- `0x6540..0x654d` places this graphic at the start grid minus `(1,4)`.

The entrance now follows that countdown and page blink in original-rules mode.
The observational core and UDP reader expose `entrance_timer`; the initial
level-two checkpoint measures 59, and all 72 later countdown states match.
No timed delay, movement trigger or screenshot-specific condition was added.

## Replay input remains authoritative across focus changes

While running captures in other windows, the older recap screenshot test could
lose held controls and take a different route. An isolated replay matched.
`testing/release_wr1_replay_input.gd` reproduces the underlying failure by
clearing live input between replay delivery and a player update. Before the
fix, the altered route eventually missed required native updates.

`InputReplay` now keeps the recorded held-action state. Original-rule movement
reads that state during a replay and live input during normal play. The forced
release test now retains exact native input/state/timing. A separate negative
test removes the recorded jumps and confirms the comparator detects the
resulting differences; the checkpoint cannot conceal later divergence.

## Visual scope and validation

The actual GPU renderer is tested against a pre-input checkpoint image and
fixed native-counter / clone-source-frame pairs. Gameplay pairs use native
counter N and clone input frame N-1; images are not shifted to find matches.
The maintained image manifest records each PNG hash and native trace provenance.

Native video delivery can lag an instruction-completed update at its boundary.
For example, screenshots taken on the entrance update's completion counter
still show the preceding render while the clone has already drawn the new one.
The blink verification samples two counters after completion, before the next
admission. These sparse image checks do not claim every intervening video frame
or native rendering latency is reproduced. Gameplay update timing is checked
separately for every update.

Run the engine checks with `GODOT` set:

```text
python -m unittest discover -s testing -p test_wr1_level_start.py -v
```

Recreate the primary fixture from the retained native evidence:

```text
python tools/prepare_wr1_level_start.py --capture testing/output/wr1_level2_final_native.json --trace testing/output/wr1_level2_final_native.jsonl --replay testing/output/wr1_level2_motion_replay.json --output testing/fixtures/wr1_level2_motion_replay.json --fixture testing/fixtures/wr1_level2_motion_boundaries.json --start-counter 6379 --calibration-end 6420
```

The raw BSV replay, captures and traces remain under ignored `testing/output`;
the portable input, expected-state and image fixtures are under
`testing/fixtures`. The existing full-route recap and exit tests continue to
exercise transitions independently of this post-load slice.

Final validation: **52 Python tests and all twelve Godot suites pass**.
The expanded pixel test covers **12 complete 320x200 images with zero differing
pixels**: the pre-input checkpoint, five gameplay samples, and six entrance
blink/disappearance samples. All 72 native updates also match the new entrance
countdown field. `git diff --check` passes.

The next coverage gaps remain moving hazards on medium/hard difficulty and
boy/ending behavior. Loading-time parity is not a requirement.
