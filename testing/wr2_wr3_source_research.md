# Word Rescue 2 and 3: source feasibility

2026-09-23. Read-only investigation of the original files, existing import code,
and the developer's official product page. No game code changed. No applicable
`AGENTS.md` was found in the worktree or its ancestor directories.

## Finding

The original sources needed for both ports are already present locally. The
registered episodes appear to use the same basic engine and asset formats as
WR1. Reusing the recovered engine is strongly supported by the executable and
asset comparisons below. This does **not** establish instruction, timing, or
pixel parity for either new episode; each needs its own reference runs.

For these particular local binaries the target is **20 levels in WR2 and 20 in
WR3**, not 15 each. This is supported by executable bounds as well as files and
titles, and is an important input to any implementation estimate.

## Original artifacts and executable evidence

Primary source directory:
[original installed files](<D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)>).
WR1 is in its `WORD` subdirectory; WR2 and WR3 are directly in that directory.

| Artifact | Size | SHA-256 |
|---|---:|---|
| [WR1.EXE](<D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)/WORD/WR1.EXE>) | 176,958 | `b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f` |
| [wr2.exe](<D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)/wr2.exe>) | 176,940 | `6bd51a4c199bee7ebe18f8b6da040a9a1e4dd10ffcc9ed2e8367d28187329ab1` |
| [wr3.exe](<D:/Downloads/Word Rescue (1992)(Apogee Software Ltd)/wr3.exe>) | 177,054 | `551b40a25931b392980d49e2f61367536b614e42b1362aedd3693d16b973b236` |

All three are MZ executables with image offset `0x2a00`. Their data segments
begin at different file offsets: WR1 `0x24f50`, WR2 `0x24eb0`, WR3 `0x24ef0`.
Existing WR1-only address tables and executable-hash guards cannot be applied
unchanged.

Capstone 16-bit disassembly of the three original binaries provides a useful
bounded comparison:

- The player movement interval `0x37a7..0x3d7e` contains 468 instructions in all
  three binaries, with the same instruction addresses and mnemonics.
- Replacing direct memory-address operands with a placeholder leaves 13 operand
  differences for each registered episode against WR1. Eleven are immediate
  values that move by `+0x36` in WR2 or `+0x32` in WR3, consistent with moved data
  tables; two are a far-call target and a jump target. This strongly suggests
  reusable movement logic. The called routines and all other engine routines
  were not exhaustively compared, so this is evidence of common implementation,
  not proof of identical gameplay or clock behavior.
- At file `0x36a9`, the level-number bound is `cmp si,0x0f` in WR1 and
  `cmp si,0x14` in WR2/WR3. At `0x3fa2`, the post-increment level-end comparison
  is `cmp word ptr [0x20b],0x0f` in WR1, `cmp word ptr [0x241],0x14` in WR2,
  and `cmp word ptr [0x23d],0x14` in WR3. Both registered executables also contain
  a full sequence of named cards through `Level 20`. These independently support
  twenty playable levels, rather than five unused maps.

Examples from the original embedded title strings: WR2 begins with “You enter
the Cave” and ends at “Flash Flood”; WR3 begins with “The Haunted House” and ends
at “Another Cavern”. Sources: the executable links above.

## What can be imported

The following results came from reading the original `wrN.1`, `wrN.2`, `wrN.3`,
`wrN.4..6`, `wrN.S*`, and `wrN.D*` files in the source directory, using the GX
directory layout implemented by [extract_gx_library.py](../tools/extract_gx_library.py)
and the decoder in [convert_levels.py](../tools/convert_levels.py).

| Content | WR1 | WR2 | WR3 |
|---|---:|---:|---:|
| Level files | 15 (`S0..S14`) | 20 (`S0..S19`) | 20 (`S0..S19`) |
| Graphics archive entries (`.1`) | 30 | 30 | 34 |
| Word-picture archive entries (`.2`, including animation frames) | 108 | 154 | 147 |
| Word-stream tokens / distinct words (`.3`) | 95 / 86 | 125 / 119 | 131 / 124 |
| Word lengths | 3–7 | 3–7 | 2–7 |
| Recorded demo files | 15 | 6 | 6 |

All forty WR2/WR3 maps decoded without an exception through the existing
`parse_level` function. This is a format compatibility check, not a successful
playthrough. Maps use the same seven indexed word slots, solid/platform values
`0x73`/`0x74`, coordinate scheme, and familiar entity arrays. WR3 requires tileset
4, which WR1 maps never use. There are additional raw attribute values that were
not interpreted in this investigation.

The parser reports one duplicate word slot in WR2 `S1` and `S2` (duplicate slot
0), and WR3 `S0` (duplicate slot 3). In every case the extra is precisely the
bottom-right final attribute cell, not an additional slot index. Investigate
the original loader's handling of that edge/padding before treating these as
eight blocks or changing the seven-word rule.

Byte comparison of same-named entries in each `.1` archive shows:

- All episodes share identical `CHARS.WR`, `BENNY1.WR`, `BENNY2.WR`, and
  `SLIME.WR` assets. Most same-named environment/UI files are also identical.
- Of fifteen names shared with WR1, WR2 has thirteen identical files;
  `STATIC.WR` and `BACK2.WR` differ. It also supplies `DROP2.WR` and episode
  frontend pages.
- WR3 has fourteen of those fifteen identical files; `STATIC.WR` differs.
  It additionally supplies `BACK4.WR`, `DROP2.WR`, `FSTORY1.WR` through
  `FSTORY3.WR`, and episode frontend pages.
- Word-picture names use `.WR2` and `.WR3` suffixes and are distinct episode
  catalogs. They need importing with their animation frames and word streams;
  renaming a WR1 picture directory is insufficient.
- WR2 music `.4` equals WR1 `.5`, and WR2 `.6` equals WR1 `.4`. Further native
  investigation found that local WR2 `.5` is **not a valid CMF**: its first word
  is `0x0052`, while the original loader requires `0x5443` at executable
  `0x4198`; failure disables music at `0x41f0`. The original source ZIP contains
  identical bytes. This artifact cannot be described as a recovered track.
  WR3 `.4/.5/.6` equal WR1 `.6/.4/.5`, respectively. Music slot order matters
  even when the underlying track is shared.

The existing converter recognizes WR1/WR2/WR3 filenames, but loops over only
15 levels and writes generic `level_01.json` names. Use separate episode output
roots and the actual level count. [extract_wr1_rules.py](../tools/extract_wr1_rules.py)
also fixes WR1's hash, fifteen levels, data offsets, and output directory;
[extract_wr1_level_titles.py](../tools/extract_wr1_level_titles.py) fixes WR1's
hash, pointer-table address, and fifteen titles. These need episode-aware
configuration before importing.

## External corroboration and limits

The original developer describes Word Rescue as a trilogy with word-picture
matching, platform traversal, Gruzzles, and environments including caves and
haunted houses. Its page advertises **45 trilogy levels** and **300 word-picture
pairs**, plus a separate Word Rescue Plus containing 45 new levels. That is
useful product-level context but does not match the exact local registered
binaries' twenty-level bounds. The release/version provenance behind that
discrepancy was not established. Do not silently truncate the local sources to
fit the website's count. [Redwood Games, Word Rescue](https://redwoodgames.com/word.php).

No DOSBox playback of WR2/WR3 was performed in this investigation. Exact enemy,
contact, word selection, frontend, ending, audio, and CPU/video timing equivalence
remains unverified. The practical next step is an episode-aware data import plus
representative original/port comparisons, extending the existing engine where
observed differences require it. Recovering both games from scratch is not
supported by the evidence as necessary.
