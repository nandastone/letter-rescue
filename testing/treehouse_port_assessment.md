# The Treehouse: faithful reconstruction assessment

For completed binary recovery and replay results, see the
[first-stage report](treehouse_first_stage.md). This file preserves the initial
source reconnaissance and subsequent findings; its early uncertainties should
be read alongside the later inspection results.

Date: 2026-09-25. Initial scope: bounded source reconnaissance and reconstruction
plan. The follow-up below adds public preservation metadata and read-only
inspection of the DOS archive obtained by the parent task. This research changed
no game implementation and ran no tests.

## Target and evidence boundary

The intended target is a complete reconstruction of one original release:
original assets, palettes, object placement, animations, audio, activity rules,
input behavior, and timing, with every captured native frame compared. Readable
text and optional input/rendering improvements follow an original presentation
mode that remains usable as the regression baseline.

The DOS release and later Windows/Macintosh editions must not be treated as one
binary or resource format. Choose the specific edition/build before using an
engine name or available decoder as architectural evidence. The Windows evidence
below does not establish that the DOS edition uses Mohawk. The Macintosh edition
was not independently characterized in this investigation.

## Concrete public source findings

- **ScummVM recognizes a Windows edition but does not implement its game.** Its
  current Mohawk [detection table](https://github.com/scummvm/scummvm/blob/master/engines/mohawk/detection_tables.h#L1324-L1337)
  has `treehouse`, `MAINROOM.MHK`, detection digest
  `12f51894d7f838af639ea9bf1bc8f45b`, Windows platform, and explicit
  `ADGF_UNSUPPORTED` / `GAME_NOT_IMPLEMENTED` flags. This is a detector entry,
  not a runnable Treehouse reconstruction. The value is ScummVM detection
  metadata; do not assume it is a complete-file provenance hash.
- **Generic Mohawk archive parsing is publicly implemented.** ScummVM's
  [resource.cpp](https://github.com/scummvm/scummvm/blob/master/engines/mohawk/resource.cpp)
  describes the `MHWK`/`RSRC` headers and parses resource types, IDs, names,
  offsets, and file sizes. It also handles older Living Books formats. These are
  useful candidate readers after the actual target files have been inspected;
  they do not establish Treehouse activity logic or DOS compatibility.
- **A standalone archive extractor exists.** ScummVM Tools'
  [extract_mohawk.cpp](https://github.com/scummvm/scummvm-tools/blob/master/engines/mohawk/extract_mohawk.cpp)
  can enumerate/export resource streams, preserving type/ID and archive metadata
  in names. Decoder success on Treehouse files has not been checked. Archive
  extraction and reconstruction of game behavior are separate tasks.
- **No original source release or Treehouse-specific DOS decompilation/format
  specification was found in this bounded search.** Searches included the title
  with Broderbund, source code, GitHub, decompilation, reverse engineering, and
  file format. This is a search result, not proof no such source exists. The
  sources above belong to ScummVM, not Broderbund's original game source.

## Original materials needed next

For the chosen build, obtain the original executable and complete companion
data, including overlays, drivers, configuration, and any external audio. Keep
the original directory layout or disk images; record filenames, sizes and
SHA-256 hashes. Record edition, language, media/version markings, and selected
graphics/audio settings. For a classic Mac build, preserve resource forks and
original media metadata. `MAINROOM.MHK` is only a known Windows detection file,
not a sufficient list of required game data.

The first binary investigation should identify executable architecture, resource
headers and compression, text/glyph storage, palette and drawing code, timers,
mouse/keyboard polling, and randomness. Disassembly/decompiler output needs to
be reconciled with observed execution; it does not automatically recover names,
original source structure, or a complete behavioral specification.

## Reconstruction and comparison plan

1. Establish a reproducible original run from a known startup state and pinned
   emulator settings. Record deterministic mouse coordinates, button edges,
   keyboard events, and event timing. Include idle time, animation interruptions,
   repeated clicks, transitions, exits, and every activity's branches.
2. Extract assets with recorded source offsets/resource IDs and palette data;
   document every recovered structure and unresolved field. Recover behavior
   through disassembly plus runtime traces, building one complete activity at a
   time until the full game is covered.
3. Implement the original logical coordinates, draw ordering, pixel operations,
   animation sequences and update scheduling. Keep the original text renderer
   available for comparisons. Preserve audio event order/timing as a separate
   recorded trace where useful.
4. Compare every native presentation frame in each recorded scenario, plus
   important internal state and timing. Define frame boundaries from the
   original video output/presentation behavior, not host/Godot refresh frames.
   Report missing/extra frames, changed pixels, first divergent state, and
   palette/cursor treatment explicitly. A screenshot match alone cannot prove
   game-rule or timing equivalence, and scenario coverage is not proof of every
   possible execution.
5. Add readable text through a separate presentation choice and narrowly scoped
   input/rendering improvements. Preserve original mode so new changes can
   continue to run against the complete baseline.

## Relationship to the existing parity work

The parent investigation identified useful methodology in
[the WR1 parity workflow](wr1_parity_workflow.md), but its current coverage
compares every gameplay update with **196 sampled gameplay images** and **46
frontend screens**. The requested Treehouse goal requires broader frame capture.
The existing capture tool pins a Word Rescue executable hash and game-specific
trace hooks; its offsets, state readers, and recordings cannot be transferred to
Treehouse. Reuse comparison utilities and evidence conventions where practical,
then build Treehouse-specific capture/state instrumentation after inspecting the
chosen executable.

## DOS follow-up: media, filenames, and build identification

The public metadata and the now-local executable provide more specific evidence
than the general 1991 title date. The local archive is at
`testing/output/treehouse/source/The_Treehouse_1991.zip`; it was downloaded by
the parent task. The research agent read its directory and executable strings
without executing the program.

### Preserved builds and public metadata

- Internet Archive's [2014 DOS item metadata](https://archive.org/metadata/msdos_The_Treehouse_1991)
  specifies `TheTreeh/treehse.exe` as the emulator start path and a ZIP named
  `The_Treehouse_1991.zip`, 2,494,156 bytes, SHA-1
  `9b1f060e072865657ac6949203b4b2b891639b1e`. The parent reports that the local
  archive matches this hash. This is a preserved installed package, not evidence
  that its contents are an untouched 1991 first release.
- Internet Archive's [2019 DOS item metadata](https://archive.org/metadata/msdos_Treehouse_The_1991)
  instead starts `TheTreeh/IAFIX.BAT` and lists `Treehouse_The_1991.zip`, 2,501,633
  bytes, SHA-1 `4f0d34437fc6c1d40e27f4886f133ab8f13541d9`. Its wrapper and content
  have not been inspected here. Do not silently interchange these packages.
- A preservationist's [v1.1 disk listing](https://forum.winworldpc.com/discussion/8311/ibm-pc-tandy-1000-game-installation-file-listing-screenshot/p211)
  records three 1.2 MB disks labeled `TREEHSE 1.1`, dated February 1992. Disk 1
  has `TREEHS1` (1,158,952), `SETUP.EXE` (35,837), `SETUP.CFG` (725),
  `PRINTER.LST` (5,617), and `CONEDIT.COM` (10,996); disk 2 has `TREEHS2`
  (1,213,952); disk 3 has `TREEHS3` (784,146). These are firsthand published
  media observations, not a verified match of the local package to those disks.
  The accompanying report lists an 8088 or later CPU and EGA/Tandy/MCGA/VGA.
- The Good Old Days' [preservation metadata](https://archive.org/metadata/000572-TheTreehouse)
  identifies a separate English **v1.2**, dated 1993, on two 1.44 MB raw disk
  images. The contributor explicitly marks it **Unverified**. Published image
  SHA-1 values are `df295752d9d4b065eaca54b940f9ef5c2704ee48` (`disk1.img`) and
  `4a664f96f2876e3f9f7de5733ed3738edd8ca382` (`disk2.img`). This is a possible
  comparison source, not the currently inspected build.

### Read-only observations of the local package

The executable's printable strings contain `Version 1.1`, a 640K memory
requirement, Microsoft Run-Time Library copyright 1990, and ImageBuilder
SmartDrivers copyright 1990. The version string is stronger evidence of this
build than the archive's 1991 catalog year; corroborate its runtime presentation
before calling the target fully pinned. Runtime-library text alone does not
establish a compiler version, and the SmartDrivers text does not identify the
game’s resource format.

The locally computed SHA-256 of the uncompressed `TREEHSE.EXE` is
`16c5623174f0e97ee928790fd6d3e638d5724f3fb2a7794c7d3a48274f1d82d9`.

Key package members and uncompressed lengths:

| File | Bytes | Observation |
| --- | ---: | --- |
| `TREEHSE.EXE` | 273,408 | Main executable; contains the version and memory strings above |
| `MODULES.DAT` | 474,679 | Referenced by executable; content semantics not yet established |
| `TH.DAT` | 400,066 | Referenced by executable |
| `TH64.DAT` | 54,087 | Referenced by executable; suffix does not by itself identify a graphics mode |
| `BOY.DAT` / `GIRL.DAT` | 113,612 / 115,694 | Both filenames occur in executable |
| `DIGISND.DAT` | 1,113,437 | Name suggests sound; decoder/format unverified |
| `VOICES.DAT` | 412,330 | Name suggests voices; decoder/format unverified |
| `MIDISND.DAT` / `MT32SND.DAT` / `IBM_SND.DAT` | 54,519 / 26,503 / 20,587 | Names suggest sound backends; formats unverified |
| `CONFIG.DAT` | 32 | Executable requests running SETUP if reading this fails |
| `SETUP.EXE` / `SETUP.CFG` / `SETUP.DAT` | 35,837 / 725 / 28 | Keep alongside target installation |
| `SONGS.DAT` / `STATUS.DAT` | 8,688 / 2,704 | Preserve original bytes until mutable-file roles are established |

The package also has printer drivers under `PDRIVERS`, `PRINTER.LST`,
`CONEDIT.COM`, a PIF, and a zero-byte `.ba1` entry. There are no `.MHK` members.
That does not alone identify the DAT formats, but the Windows Mohawk lead must
not substitute for inspecting these actual DOS files.

### Manual and related source leads

The preservation page links a file named
[`The-Treehouse_Manual_DOS_EN.pdf`](https://d2.xp.myabandonware.com/f/lkbj/The-Treehouse_Manual_DOS_EN.pdf).
An HTTP HEAD request returned 200, `application/pdf`, 147,071 bytes. Its contents
were subsequently inspected during the input investigation: it contains one
scanned instrument-identification chart, not the complete manual. It provides
no startup or input-selection instructions. See
[the input research](treehouse_input_research.md).

A related Playroom resource-viewer lead points to
`https://github.com/PeterSwinkels/Playroom-PES-Viewer`, but that repository returned
404 during this investigation. No available code or shared Treehouse format was
established from it. There is still no verified original Treehouse source-code
release or documented DOS DAT schema in this bounded search. Binary inspection
of this identified v1.1 package is the next source of concrete structural facts.
