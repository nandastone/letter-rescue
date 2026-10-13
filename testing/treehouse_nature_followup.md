# Nature quiz follow-up: panels and turn sequencing

Primary sources: pinned DOS v1.1 executable and resource archives. All overlay addresses below are offsets within overlay2's body (`testing/output/treehouse/research-resources/overlay2-disassembly.txt`). Resident addresses are offsets within the unpacked main image. The sources are local original binaries, not secondary descriptions.

## Five additional exact full-screen references

Ordinary mouse input restored an existing ordinary-play save state, then selected three definitions and two candidate cards. No RAM was modified. Capture driver: `output/treehouse/research-nature/capture-followup.py`. Inputs, restore hash, source/core hashes and clock-indexed frames: `output/treehouse/research-nature-followup/capture-a/run.json` and `frames.jsonl`.

Independent renderer: `output/treehouse/research-nature-followup/render.py`. Every pixel is composed from original decoded resources and source-derived drawing operations. RAM supplies only ordinary game state and pointer position. Full 320x200 RGB comparisons:

| State | Different pixels |
| --- | ---: |
| definition-backbone | 0 |
| definition-legs | 0 |
| definition-active | 0 |
| inspect-first (Flea) | 0 |
| inspect-second (Spider) | 0 |

This establishes these static panels. It does not establish complete animation timing parity.

## Definition panel recipe

Source: overlay `0x3142..0x31FE`, clearing helper `0x3DC8`, tab helper `0x10F3`, resident rectangle helper `0x11644` and text routines.

1. Clear quiz rectangle38 `(top6,left30,bottom116,right128)` white. Restore any previously selected left attribute tab to UI palette5650 color2.
2. Repaint selected left tab with UI palette5650 color8 background and its normal SHAP5651+attribute. (No grayscale/monochrome icon conversion.)
3. STRL5300[attribute], original FONT1 black, horizontally centered at x79, top y6.
4. STRL5310[attribute], FONT1 black, left x30, top y17, wrap width98, line spacing10. Preserve source double spaces. The available drawing rectangle is `(17,30,116,128)`.
5. Right scene, character, candidates and enabled question decorations remain as before. No footer text is introduced by choosing a definition.

If the same left icon is selected twice, `0x314B..3154` returns without repainting. Selecting a different one clears the old panel first. When an answer is later requested, the temporary panel is cleared and previously learned secret answers are restored.

## Candidate inspection recipe

Source `0x343C..0x3615`, helper `0x1C01`, original resident font initialization main `0x1C4..1D3`.

The current demo's animal-name footer and giant centered image do not match this original panel. Normal candidate selection instead:

1. Clears quiz rectangle38 white; removes any selected definition-tab highlight.
2. Displays animal class (STRL5208+active_time[category]) centered x79, y7, using **resident heading_font plus one pixel extra character spacing**. Its total width includes the extra pixel for each character, including the final character. This is the pre-resource-load default font saved at DS:57C4. Existing build extraction of heading_font from main0x2EAC0 provides it.
3. Displays animal name STRL5000[id], FONT1 centered x79,y21.
4. Draws the animal's large shape centered in `(30,30,77,128)` with its original palette and index0 transparency. Center x79; center y53; subtract floor(shape dimension/2). This rectangle is derived from rect38 by top+24 and bottom-39 at `0x34CF..34EF`.
5. Enumerates the currently available question flags in attribute order0..7 (`DS:52A2`). Displays the selected animal's corresponding STRL5200+attribute[value] at x79 centered and y77,91,105. These are **available questions**, not the selected definition and not the secret's learned-answer mask.
6. Does not draw a footer name. It preserves an existing footer answer unless that footer belongs to the special complete-reveal state99.

Rows are derived by taking the corresponding left icon rectangle, moving it23pixels right and extending83pixels right: `(top5+14*row,left30,bottom18+14*row,right128)`. FONT1 rendering centers vertically with its9pixel metric, producing y7+14*row. Class uses the resident9pixel line metric too despite its7pixel glyph height.

`DS:57D8`: 0=normal learned answers;1..8=definition; -1=candidate inspection;99=all-attributes reveal. Clearing a temporary panel can restore the learned secret answers via `0x394A`.

## Input/rule corrections

- Manual cross-out is permitted only after dealing, for a human role, and **only when Help is off**. Overlay `0x3795..37D0` rejects it otherwise. Current demo's `crossOut()` should also check `help[role]`.
- Automated action is not exclusive to the robot. At `0x2AF5..2B45`, `singleSecret = remainingMask == (1 << secretIndex)`; an unanswered turn automatically acts whenever role is robot **or** singleSecret is true. A human whose manual elimination leaves precisely the true animal is therefore guided automatically into guess/reveal. A single incorrect remaining card does not trigger it.
- An ended robot turn does **not** automatically roll the die into a human turn. Source `0x3ADB..3B55` clears question decorations/character/guess button, restores the die, then `0x391D` sets phase1 and guessMode0. It returns to the mouse/keyboard input loop. Current demo's150tick robot handoff is an added behavior.
- Robot questions use rejection sampling: random integer0..7, repeat until its available-question flag is set (`0x2B9D..2BBC`). Choosing uniformly from the three flags has equivalent probability but different PRNG calls, so it cannot yield seed parity.
- Robot guess mode always selects the known secret index (`0x2B72..2B87`). The original's remaining-mask equality test guarantees this happens only when deduced, absent state corruption.

## Script IDs: important correction

Main wrapper `0x415F` forwards to `0x419D`; `0x41E6..41EC` resolves SCR as **base ID plus index**. The argument following base is not a relocation or animation mode.

Let group=20100+2000*role, role0=chosen BOY/GIRL archive, role1=friend TH archive, role2=robot TH archive; all use palette group.

| Action | Actual SCR | Source |
| --- | --- | --- |
| Enter turn | group+0 | `0x287E..28C2` |
| Ask attribute0..7 | group+attribute | `0x3257..32BB` |
| Enter guess mode | group+8 | `0x30E3..3133` |
| Wrong guess | group+11 | `0x3683..36B6` |
| Correct guess celebration | group+10 | `0x3A96..3AC1` |
| Retreat after either guess | group+9 | `0x36F1..3739` |
| Flatten/reveal secret shrub | **5600+player** | `0x3A04..3A1E` |

Using SCR20100 for celebration or relocating SCR5600 for both players gives incorrect frames. TH lacks SCR24111 because the original robot never guesses incorrectly.

Guess setup captures an existing background handle before script+8 (`0x30E3`). That backdrop is reused/restored for guess resolution and retreat, as described in the earlier nature research document. The currently visible all-screen retained presentation cannot be reproduced by merely rendering the final sprite of each sequence.

## Original turn wait intervals

All values below are native60Hz game ticks, using resident wait helper0D51:56DB (main0x12BEB). A complete state machine must additionally await original SCR completion and original audio behavior; these waits are not replacements for script durations.

| Point | Wait | Source |
| --- | ---: | --- |
| Before enabling each of three selected questions | 30 ticks each | `0x301C..303B` |
| Before any automatic robot/single-secret action | 60 ticks | `0x2B45..2B4D` |
| Robot action cue | sound1011 | `0x2B5F..2B63` |
| After question animation and answer/footer draw | 36 ticks | `0x3339..3346` |
| After each mismatching candidate is removed with Help | 18 ticks each, ascending card index | `0x33F5..3424` |
| After help elimination / before normal answered state | 60 ticks | `0x3427..3436` |
| After guess retreat / before normal answered state | 60 ticks | `0x3780..378F` |

Turn sequence: switchplayer -> play group+0 -> restore learned-answer rows -> show current candidates -> generate/show three questions with30tick gaps -> enable guess -> if robot/singleSecret,60tick delay -> cue -> ask/guess branch. Guess entry and actual guess are separate auto-loop actions, each incurring the60tick delay.

On asking, source writes DS:0DC6 from the eight-by-three table at DS:0DC8 indexed attribute*3+role while running the question script, then resets it to-1 (`0x325F..32C1`). This is callback state for original question decorations; source mapping needs the callback's consumer before temporal parity can be claimed.

## Idle guidance

300ticks of idle invokes source `0x3C9F`. In question mode it flashes each available question off18ticks,on6ticks, then guess highlight24ticks. In guess mode it iterates each remaining card: plays a random sound1050..1055, highlights candidate6ticks, restores. In answered mode it flashes the die8ticks, optionally sound1017 on an invalid input. These cues reset the idle timer300ticks. Source `0x3C9F..3DC5`, `0x3E27..3E6B`.

## Remaining work from this research

The formulas above and five static frames are ready to integrate. For complete native sequencing, implement SCR base+index dispatch and the wait schedule, identify the DS:0DC6 callback consumer, then compare normal robot, human single-secret, wrong guess, win, and post-win second-animal reveal callback sequences. No assertion of full quiz pixel/timing equivalence is made here.

## Resolved question callback

The question callback consumer is main `0x4E9E`. It compares `DS:5586` against DS:0DC6. DS:5586 is the count of SCR display updates: reset at main `0xC776`, incremented on each opcode01 display update at `0xBE36`. Once equal, main `0x4E15` calls overlay2 `0x198A(attribute,1,0)` through an encoded overlay call. This redraws the selected question's enabled background **without its attribute icon**. The redraw is baked into the saved animation backdrop, and DS:5296 prevents a repeated callback. This is not a sound callback.

Native frame-update thresholds by attribute, columns human/friend/robot, from main image`0x321D0+0x0DC8`:

```
Backbone        17 17 17
Temperature     11 11 12
Wings           10  9 11
Legs             9  9 10
Skin            13 11 12
Breathing       13 13 14
Food            11 11 12
Active time     11  9 12
```

Rendering operation: inside the selected question rectangle, if its background ID table entry is nonzero, fill white and draw SHAP5600+backgroundID; otherwise restore the original scene background. Do not draw SHAP5651+attribute. Other enabled question illustrations stay intact until turn cleanup. The original wrapper updates the animation's saved background after this operation (`0x4E61..4E90`).

This resolves the consumer named in the earlier remaining-work section; ordered native comparisons for the newly integrated animation phases remain necessary.
