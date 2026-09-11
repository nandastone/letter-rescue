# WR1 word/picture matching model

2026-09-07. Static analysis of [WR1.EXE](<D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)/WORD/WR1.EXE>), SHA256 `b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`. Addresses are file offsets except those prefixed `DS:`. See [movement research](wr1_movement_research.md) for MZ/DS arithmetic and analysis limitations.

**Each of the seven locations has a different word identity and picture identity. A successful match consumes the source's word, not both locations. Previously completed word locations remain usable as pictures.** There are seven successful word-to-picture matches per level, using the same seven locations in these two distinct roles.

## Evidence files

- [Interaction function, 0xc1aa–0xc6f8](output/wr1_matching_c1aa.txt).
- [Offset initialization, 0x4ea0–0x4ee3](output/wr1_matching_4ea0.txt).
- [Active rendering, 0xb5f6–0xb8ad](output/wr1_matching_b5f6.txt).
- [Question-mark rendering, 0xb8b3–0xb9ec](output/wr1_matching_b8b3.txt).
- [Question-location discovery, 0x6bf8–0x6c59](output/wr1_matching_6bc0.txt).

## Stable slot plus two cyclic offsets

The level's raw attr values 0 through 6 are stable numeric question-location slots. Loader `0x6c18` recognizes these and caches their pixel coordinates. Do not assume a JSON list's enumeration order equals the raw attr slot; lookup the attr at each location or preserve the slot during conversion.

Two independently selected cyclic offsets map this slot to the seven loaded word/picture identities:

```python
word_index = (slot + word_offset) % 7
picture_index = (slot + picture_offset) % 7
```

`word_offset` is `DS:a984`; `picture_offset` is `DS:6634`. In normal mode, `0x4eb5–0x4ec5` picks `word_offset = rand() % 6 + 1`. `0x4ecb–0x4ee1` repeatedly picks `picture_offset = rand() % 7` until the offsets differ. The executable's demo-mode branch instead assigns word offset 3 and picture offset 2 (`0x4ea7–0x4ead`). This is a pair of rotations, not a general shuffle.

Consequently every word has exactly one matching picture at another location. The different-offset constraint guarantees no location matches itself. For source slot `s`, target slot is `(s + word_offset - picture_offset) % 7`.

The word selection uses the first formula directly at `0xc5e9–0xc5f8`. The target comparison uses the second formula at `0xc249–0xc25c`. Active picture rendering independently uses that same formula at `0xb736–0xb745`, confirming that collision matching and the displayed picture agree.

## State transitions

| Variable | Meaning and evidence |
|---|---|
| Attr 0..6 | Word still available at this slot. |
| Attr 7..13 | Source word consumed/selected; underlying stable slot remains `attr % 7`. Selection adds 7 at `0xc60c–0xc621`; failure restores modulo 7 at `0xc46a–0xc485`. |
| `DS:32d` byte | Active word mode: 1 shows selected word plus pictures; 0 shows remaining question marks. |
| `DS:32e` byte | Active word index 0..6. |
| `DS:26f/271` words | Active source grid coordinates. |
| `DS:83fa/83fc` words | Most recently touched/selected location; also used to suppress immediately reopening it. |
| `DS:32f` byte | Successful-match count, initialized to 0 at `0x4fbf`, incremented once at `0xc37a`. |
| `DS:b8cd + 2*wordIndex` | Completion-order entry, initially sentinel 9, written with the old successful-match count at `0xc376`. |
| `DS:334` word | Mistake count during gameplay. Incremented on mismatch at `0xc456`; also reused/reset by setup/load paths, so do not infer its persistence across modes from this function alone. |
| `DS:9593 + 2*wordIndex` | Set to 1 on a mistake for that word (`0xc450`). |

Core logic recovered from `0xc1aa–0xc6f8`:

```python
if not active_word:
    if attr_at_touched_location < 7 and location != last_touched:
        active_word = True
        source = location
        last_touched = location
        active_index = (attr[location] + word_offset) % 7
        attr[location] += 7
        # Show the selected word and every other location's picture.
else:
    if attr_at_touched_location < 14 and location != source:
        last_touched = location
        target_index = (attr[location] + picture_offset) % 7
        if target_index == active_index:
            score += 20
            completed_order[active_index] = matched_count
            matched_count += 1
            # Leave source attr at slot+7.
            # Do not change target attr at all.
            if matched_count >= 7:
                if mistake_count == 0:
                    score += 500
                exit_enabled = True
                completion_transition_pending = True
            if matched_count == 6:
                last_touched.x = -1
        else:
            mistakes_for_word[active_index] = 1
            mistake_count += 1
            attr[source] %= 7
            spawn_gruzzle_at(location.x, location.y + 1)
        active_word = False
        source.x = -1
```

The 20-point reward is a signed word read from `DS:156` at `0xc27a`, added to the 32-bit score `DS:186/188`. Its initialized value in this binary is 20. The zero-mistakes bonus reads `DS:15a`, initialized to 500, at `0xc392`; the controlling condition is `DS:334 == 0` at `0xc388`. Seven successful matches set `DS:18a=1` and `DS:32b=1` at `0xc429–0xc42f`. The main movement function checks the exit-ready flag against the player's exit coordinates at `0x3d46–0x3d6c`.

The mismatch spawn writes gruzzle X/Y arrays at `DS:977a` and `DS:9794`, initializes state arrays, then increments current gruzzle count at `0xc503`. If count exceeds 9, it first decrements the count at `0xc488–0xc491`, so the new spawn reuses the final array slot rather than growing indefinitely. The later collision consequence was not traced here; a wrong-picture contact followed by a reset/death is consistent with a newly spawned gruzzle, not proof of an immediate game-reset rule.

### Important source/target distinction

A location can be completed as a **word source** and still serve as a **picture target**. Active matching accepts attrs below 14, whereas starting a word accepts only attrs below 7. A success does not remove a pair. After success, question marks cover only unconsumed sources; starting the next word reveals all locations' picture roles again, including locations with already completed source words.

There is also a last-touch suppression rule. The inactive path ignores the last-touched location (`0xc5b5–0xc5c3`), including the just-used target. It is not implemented as a simple `body_exited` reset in this routine. At six successes the original explicitly clears last-touch X (`0xc435–0xc43f`), allowing the last remaining source to activate. The precise visual/contact implications of moving away and returning should be checked at runtime before simplifying this rule.

## Rendering and contact geometry

When `DS:32d != 0`, the render path loops over all seven question locations (`0xb600–0xb8a8`). The selected source is drawn as the active word using word rectangle tables based on `DS:32e` (`0xb627–0xb725`); other locations display pictures determined by `(attr + picture_offset) % 7` (`0xb728–0xb886`). It does not filter these picture locations based on whether their source word was completed.

When no word is active, the render path draws a question mark only where attr < 7 (`0xb8df`) and suppresses the most-recently touched location (`0xb8e8–0xb910`). Source attrs 7..13 are thus hidden in this mode.

The interaction function scans a rectangle of attr cells around the player, not an exact sprite `Area2D` overlap. It scans rows `max(gy-5,0)` through `gy` inclusive, and columns `max(gx-1,0)` through `gx+3`, additionally bounded to less than map dimension minus one. It stops on one relevant interaction. This enlarged sampling region explains why a question can activate while visually above/beside the character; preserve this when testing original collision parity.

## Concrete clone implications

1. Preserve the original slot ID from attr 0..6 rather than using list order implicitly.
2. Give each location separate computed word/picture indices with distinct cyclic offsets.
3. Track consumed word sources independently from picture target availability.
4. Count one success per consumed source; unlock after seven, not after removing seven pairs.
5. On failure restore only the active source's availability, return to question mode, and spawn the wrong-answer gruzzle.
6. Add 20 for a match and the conditional 500 bonus at all-seven completion.
7. Match original contact scanning and last-touch suppression after the core state machine is checked.

The formulas, state writes, success count, and reward constants are high-confidence static findings. Exact RNG synchronization, word-list selection, initial offsets of a running session, animation timing, mistake-counter lifetime across load/death paths, and downstream death behavior remain runtime or further-analysis questions. No gameplay files were changed in this research pass.
