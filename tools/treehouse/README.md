# Treehouse DOS reconstruction tools

The target is the complete original game, followed by readable text and other
optional improvements. These tools implement resource recovery and a repeatable
original-game reference. An independent **[playable browser demo](../../treehouse-demo/README.md)**
now rebuilds character selection, the interior, music, and telescope views.
The complete game and full frame-by-frame parity remain unfinished.

The pinned executable identifies itself as **Version 1.1**. It comes from the
[Internet Archive DOS package](https://archive.org/details/msdos_The_Treehouse_1991).
Its ZIP SHA-1 is `9b1f060e072865657ac6949203b4b2b891639b1e`; executable SHA-256 is
`16c5623174f0e97ee928790fd6d3e638d5724f3fb2a7794c7d3a48274f1d82d9`.
The archive's catalog year is not an exact executable version identifier.

Python 3 and Pillow are required. Original files, decoded assets, emulator
sources/binaries, and recordings stay in ignored `testing/output/treehouse/`.
Tools refuse to overwrite evidence directories. Run commands from the repository
root, using new output names for another run.

## Recover resources and executable structure

```powershell
python tools/treehouse/resources.py testing/output/treehouse/source/The_Treehouse_1991.zip testing/output/treehouse/extracted --extract
python tools/treehouse/images.py testing/output/treehouse/extracted/manifest.json testing/output/treehouse/images
python tools/treehouse/executable.py testing/output/treehouse/source/The_Treehouse_1991.zip testing/output/treehouse/executable
```

`resources.py` inventories every file, records hashes and source offsets,
validates all resource bounds/checksums, and extracts payloads unchanged. All ten
DAT containers parse: **3,806 resources**. String previews retain exact bytes;
CP437 is provisional. One STRL resource declares 25 strings but contains 24;
the manifest records that discrepancy without discarding it.

`images.py` decodes all **2,337 SHAP images**, checks exact compressed-input
consumption and decoded lengths, and writes raw palette indices. These grayscale
index PNGs are data, not correctly colored artwork. To render a specific image
with an explicit original palette:

```powershell
python tools/treehouse/images.py testing/output/treehouse/extracted/manifest.json testing/output/treehouse/background --archive th64.dat --shape 1 --palette 0
```

The original has overlapping palette groups. Do not choose a permanent palette
solely from image ID. The TH64 background using replicated 6-bit RGB channels
matches all unobstructed title pixels to the right of x=170 in the native capture.
The title's other sprites and text are separate drawing operations.

`executable.py` accepts only the researched executable, statically expands its
main image to **226,208 bytes**, catalogs **1,386 relocations and five overlays**,
and disassembles the framing of **356 SCR scripts and 195 PSL sound lists**.
Unpacking executes no game instructions. Unknown opcode semantics remain raw
operands; a successful parse is not a behavioral equivalence claim.

## Build the reference capture core

The ordinary DOSBox Pure frontend starts its worker before delivering video and
polls input while that worker can still advance. This caused real mismatches in
repeated entry routes. A small source patch holds the worker during input polling
and audio/video callbacks, and disables frame skipping. The original executable,
CPU implementation, timer implementation, and artwork are unmodified.

Use an independent upstream checkout pinned to the researched revision:

```powershell
git clone https://github.com/schellingb/dosbox-pure.git testing/output/treehouse/capture-core
git -C testing/output/treehouse/capture-core checkout db325ff427e3d0df2e6c38bc75b00b6771e03b38
python tools/treehouse/instrument_core.py testing/output/treehouse/capture-core
```

From that checkout, with a MinGW-w64 compiler and GNU make on PATH:

```powershell
make -j8 CXX=g++ "LDFLAGS=-shared -static-libgcc -static-libstdc++ -Wl,--gc-sections"
```

The capture runner defaults to the resulting Windows DLL. `--core` or
`DOSBOX_CORE` can select another path. It requires the capture boundary marker;
`--allow-unsynchronized-core` is only for investigating a stock core's behavior.
Keyboard events are queued until the synchronized input poll. Mouse deltas are
delivered on the first run of an action; buttons remain held for its duration.
Input polled for callback N is consumed by the next emulated frame. Keep fixed
CPU cycles, native frame rate, and the supplied virtual mouse configuration.

## Record and compare the original

```powershell
python tools/treehouse/prepare.py testing/output/treehouse/source/The_Treehouse_1991.zip testing/output/treehouse/source/reference.zip
python tools/treehouse/capture.py testing/output/treehouse/source/reference.zip testing/output/treehouse/run-a --actions testing/treehouse/routes/enter-treehouse.json
python tools/treehouse/capture.py testing/output/treehouse/source/reference.zip testing/output/treehouse/run-b --actions testing/treehouse/routes/enter-treehouse.json
python tools/treehouse/compare.py testing/output/treehouse/run-a testing/output/treehouse/run-b testing/output/treehouse/comparison.json
```

Preparation adds only a recorded DOSBox configuration: fixed 10,000 cycles,
normal CPU core, and DOS date/time January 1, 1992 at noon. It preserves original
member bytes and pins ZIP metadata. `--program setup.exe` launches original setup
for investigation instead.

Every video callback has a JSONL entry, including duplicate images; unique RGB
images are stored losslessly by hash. The runner records the original PIT counter
while the worker is held inside the video callback, source/core/tool hashes,
input actions, core settings, audio, and named snapshots. The main image is found
using three independent original strings rather than a fixed host pointer.
Named save-state/RAM dumps happen after `retro_run` and are diagnostic snapshots;
the callback's PIT sample is the frame timing evidence. Snapshot protocol 2
finishes the pending emulated frame before saving or restoring. The public
AV-info call holds the pinned core's worker during this boundary operation.
Earlier evidence retains its original protocol and is not silently relabeled.

The entry route waits at the exterior, selects the boy at logical `(96,145)`,
and reaches the interior. The tree itself requires Ctrl before a character has
been chosen; Enter/Space do not provide a universal Continue action.

Comparison verifies actual PNG content against recorded hashes and rejects
incomplete/missing evidence. It checks every callback's dimensions, pixels,
run number, and PIT sample, along with exact audio and matching inputs/settings.
There are no frame shifts, similarity thresholds, or mismatch allowances.

Passing two original runs proves reference repeatability. The browser demo now
has a rebuilt renderer/interpreter; full clone parity still requires broader
behavioral reconstruction and comparisons against these references.
The current route does not cover all activities or every possible execution.
See [first-stage results](../../testing/treehouse_first_stage.md).

## Read-only timing probes

`build_trace_core.py --checkout <pinned-core> --compiler <g++.exe> --output <new-directory>`
builds a separate instruction-probe DLL using the existing core objects. It does
not overwrite the ordinary reference core. `trace_nature_redraw.py --core <probe-dll>
--output <new-directory>` restores the original nature input route at a fixed
worker boundary and records selected drawing calls plus VGA timing. Run another
capture with `--no-probe` and compare with `verify_trace_capture.py reference
candidate new-report.json` before trusting the trace.

`verify_scanout.py` verifies the independent JS presenter using generated browser
pixels and native commit-time fixtures. It is a component test, not an end-to-end
gameplay timing claim. Full findings, scope and reproducible evidence are in
[redraw reconstruction](../../testing/treehouse_redraw_reconstruction.md).

Use `--profile resources` with `trace_nature_redraw.py` to observe SCR construction,
preloads, resource reads, shape conversion and drawing. The accepted resource
trace and source-backed preload implementation are documented in
[resource timing](../../testing/treehouse_resource_timing.md).

`verify_snapshot_boundaries.py --output <new-directory>` checks two ordinary
capture processes against the established reference, including every callback
and all audio bytes. `verify_animation_resources.py --html <candidate.html>
--output <new-directory>` verifies the independent runtime's preload order.
The latter is included in the gameplay suite; it does not establish CPU timing.

The work-probe DLL additionally supports `trace_nature_redraw.py --profile resources
--work nibbles`, `--work lzrows`, and `--work lzcolumns`. Each captures instruction
counts inside one recovered graphics routine; the later probe also records REP
slice budgets. `verify_graphics_work.py --trace <trace.json> --output <new-directory>`
compares these to the independent JS model using the pinned DAT resources.
Residual CPU budgets are explicit component fixtures, not a runtime schedule.

`completion_status.py` evaluates the persistent issue ledger and the current
integrated-build evidence. It exits with code 1 while any required issue,
strict-timing failure, missing evidence or build-hash mismatch remains.
The default now validates the Godot schema-2 index in
`testing/treehouse/completion_verification.json`: every ledger acceptance row,
all export files (including nested files), runtime source, evidence and verifier
hashes, ordinary native journeys, unshifted timing, actual audio, desktop and
HTTP delivery. The archived `completion_verification.legacy-js.json` can only
be evaluated with explicit `--verification` and `--html` arguments.

`build_godot_release.py --godot <engine> --output <new-folder>` exports `web/`
and writes `build.json`, with matching source inventories before and after.
`run_godot_evidence.py --build <build.json> --output <new-envelope-folder>
--result <new-result.json> --scope <scope> --verifier <tool-or-test-file>
-- <verifier-command>` executes a fresh check and binds its report to that
unchanged source/export. Repeat `--verifier` for supporting test scripts.
Headless comparisons use `component`; only checks exercising the actual export
can use `web`, `native_journey`, `strict_timing` or `native_audio`. Complete
native journeys must explicitly report ordinary inputs and completion.

The evidence index keeps pending requirements separate from bounded passing
tests. A `reviewed` requirement must cite proof of that exact acceptance text;
hash validation alone cannot assess semantic coverage. The final human-readable
completion audit must still inspect those claims. Gate mechanics are checked
with `verify_godot_completion_gate.py --output <new-folder>`; its synthetic
fixtures are not game fidelity evidence.

## Parser checks

```powershell
python -m unittest discover -s tools/treehouse -p test_formats.py -v
```

Ten independent fixture tests cover container bounds/checksums, all five image
compression modes, overlapping LZ copies, packed pixels, palette conversion,
malformed script framing, executable version rejection, and incomplete captures.

Research: [resources](../../testing/treehouse_resource_research.md),
[graphics](../../testing/treehouse_graphics_research.md),
[executable](../../testing/treehouse_executable_research.md),
[animation](../../testing/treehouse_animation_research.md),
[capture scheduling](../../testing/treehouse_capture_research.md).


`verify_godot_songs_only_web.py --web EXPORT --output NEW_OUTPUT` checks a
missing-STATUS cold start with the original SONGS file retained. It prepares a
disposable browser storage fixture while the engine is unloaded, then compares
ordinary F9 downloads and reloads with native fresh defaults. Its report records
the storage setup and exact export inventory; it does not claim an ordinary-input
native gameplay journey or exact cold-start timing.


Title/focus browser checks now require real observed blur/focus and destination
audio observation. On Windows run `verify_godot_title_web.py --headed --web
EXPORT --frames TITLE_FRAMES --output NEW_OUTPUT`. Playwright focus emulation is
disabled after navigation. A headless browser that keeps all tabs focused fails
explicitly instead of claiming tab-switch coverage. The WebAudio analyser only
observes output; it does not alter audio scheduling or game state.
