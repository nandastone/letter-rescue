# Resource preparation and timing reconstruction

## Implemented resource semantics

`ResourceStore.animationResources` reconstructs the original SCR constructor's
preload plan from the script itself. Main module `C449..C567` scans all nonzero
`Cx` shape ranges through the terminator. `C5AC..C62D` then loads their union in
ascending palette-relative order. This includes shapes used after the first
display, even when a caller stops after that first display.

Every browser `Animation` now prepares that complete plan before it executes.
The plan is immutable and cached by archive, script and palette. This establishes
resource order and availability; JavaScript's host execution time is **not**
used as original CPU time. Resource lifetimes, conversion costs and sub-tick
framebuffer commits remain to be reconstructed.

`verify_animation_resources.py` compares the actual constructor requests to the
read-only original trace. Both robot scripts, TH24100 and TH24103, request exactly
these 15 palette-relative shapes:

`1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16`.

Both comparisons and five focused range/order/immutability checks pass. No
native timestamps or pixels are supplied to the runtime. Evidence:
`output/treehouse/resource-preload-check-a/report.json`.

## Reference trace

`trace_nature_redraw.py --profile resources` adds constructor, resource lookup,
read, shape conversion and drawing boundaries to the original read-only probe.
The accepted trace is `output/treehouse/nature-resource-trace-b/trace.json`:
11,220 entries. Its pixels, precise clocks, PIT counters and audio are identical
to the probe-disabled control across all 3,116 callbacks. Comparison:
`output/treehouse/nature-resource-control-comparison.json`.

The earlier `nature-resource-trace-a` is diagnostic only. It watched two incorrect
return offsets and an unnecessarily frequent interpreter poll. Its timings are
not used as accepted preload evidence.

| Original operation | Turn actor | Question actor |
|---|---:|---:|
| Constructor entry, ms after input callback | 1128.2153 | 4207.7308 |
| First shape preload call | 1130.7950 | 4209.6598 |
| Last shape preload return | 1168.4046 | 4239.6188 |
| Constructor return | 1185.2732 | 4251.2255 |

Calls have different costs even with the same 15-shape plan. This rules out
assigning a single captured duration to every animation start. In addition to
shape conversion, constructor work includes resource allocation, an offscreen
surface, saved background and initial composition.

Pinned reference `src/dos/dos.cpp` also debits successful file reads using four
CPU cycles per returned byte. If `4 * bytes + 5` is not strictly below the current
budget, it sets the budget to five and adds the entire old budget to the I/O
counter. These two changes are not equivalent to a single capped subtraction.
The normal CPU core charges REP string iterations individually. These costs
must be modeled with the current CPU slice and interrupt timing; a fixed
milliseconds-per-byte rule is insufficient.

## Next work

Measure separate shape conversion and allocation blocks, derive their work from
the compressed source data and recovered code, then verify the derived clock on
both cold and repeated loads. Use that clock for ordered framebuffer operations
and the already checked `OriginalScanout` component. The live strict turn remains
614/984 callbacks with 12 missing native displays until that integration passes.

## Derived graphics work

`treehouse-demo/graphics-work.js` now derives the instruction paths for three
original graphics routines from DAT contents:

| Routine | Inputs to the model | Captured calls compared |
|---|---|---:|
| Resident DE10, four-bit VGA expansion | Width, height and decoded original indices | 30/30 exact |
| Resident DF85, LZ rows | Compressed stream and output dimensions | 6/6 exact |
| Resident E03E, LZ columns | Compressed stream and output dimensions | 24/24 exact |

Every nonzero instruction-address count is compared, including zero/nonzero
pixel branches, odd-width padding, literal/reference tokens, ring-buffer wraps
and column boundaries. The normal CPU interpreter charges one dispatch cycle
plus the additional `DoString` iterations. This produces intrinsic guest work,
not a fitted number of milliseconds. Seven focused validation checks also pass.

The first column-LZ comparison retained four failures of one instruction each.
The reference had exhausted a CPU slice during `REP STOSW`, then dispatched that
instruction again with the remaining CX. The independent `repeatString` model
now implements the pinned core's restart rule, including its do/while behavior
when no positive budget remains. Exact comparison uses explicitly identified
native residual-budget fixtures for this component. **The full runtime clock
must still calculate those budgets independently.** No fixture budgets or native
counts are embedded in the game or the model.

Accepted reports under `output/treehouse/`:

- `nibble-work-check-b/report.json`: 30 calls.
- `lzrows-work-check-b/report.json`: 6 calls.
- `lzcolumns-work-check-b/report.json`: 24 calls, including the four restarts.
- `nibble-work-control-comparison.json`, `lzrows-work-control-comparison.json`,
  and `lzcolumns-work-control-b.json`: all 3,116 callbacks, clocks, live framebuffers
  and audio bytes agree with their probe-disabled controls.

The profiling DLL records selected instruction counts and REP budgets without
changing guest memory, registers or cycle charges. `trace-core-work-a` and
`trace-core-work-b` retain their build manifests with all linked-object hashes.
The graphics work model is not bundled into the playable runtime yet, and these
checks do not increase its frame-parity counts.

## Allocation delay isolated

`nature-allocation-trace-a` separates raw allocations from the far allocator.
The turn constructor allocates two 9,612-byte surfaces. The first call spans
1168.4674..1173.5059 ms after input; the second spans
1173.5988..1182.6925 ms. Each final far-allocation call takes only 0.0084 ms.
Almost all preceding work is resident `6B06`, invoked by `65FA` before allocation.
Its source scans the heap, examines reclaimable handles, coalesces free blocks
and can request further heap management through `678B` and `7011`.

This makes heap state and resource lifetime the next required reconstruction.
Adding a constant surface-allocation delay would miss the difference between
these same-sized requests. The allocation trace passes the full 3,116-callback
probe/control comparison (`allocation-trace-control-a.json`).

## Snapshot issue closed

The ordinary `Native` adapter now finishes the pending emulated frame before
save and restore. Both capture reports and trace reports identify snapshot
protocol 2. The trace subclass inherits this shared implementation.

`verify_snapshot_boundaries.py` runs two fresh processes with the ordinary capture
DLL, then requires their complete timelines and WAV bytes to equal the established
control. All four checks pass: 3,116 callbacks per run, identical RGB/PIT clocks,
identical audio and protocol 2. Instrumented replay also preserves all 311 original
trace events exactly. Historical capture reports are unchanged.

## Heap preparation recovered

`treehouse-demo/heap.js` models the conventional-memory block chain and near
handle table used by resident `6B06`. A block has a six-byte header, an even
total size, a type, and up to seven padding bytes. Movable blocks point back to
a handle; its high bit prevents relocation. Preparation coalesces holes and
moves unlocked resources into the last suitable hole, splitting from its tail.
The raw allocation that follows uses the resulting free block.

`heap-work.js` independently follows these decisions to count original
instruction addresses and copy iterations. `heap-instructions.js` contains
instruction boundaries exported from the pinned executable by
`tools/treehouse/export_heap_instructions.py`; it contains no timing recordings.

The widened read-only probe captures all 52 preparation calls in the ordinary
nature turn/question/answer route. `heap-all-check-a/report.json` compares:

- Every before/after block address, size, type and padding field.
- All movable handle states and segment pointers, the heap search pointer, and
  payload hashes. All 49 relocations preserve their original contents.
- Every instruction-address count: 239,464 dispatches across 391 addresses,
  plus 15,164 string-copy iterations.
- Five focused checks for small remainders, tail splitting, coalescing, locked
  handles and rejection of unsupported arena-growth state.

All 52 calls and five checks pass. `heap-all-control-comparison.json` confirms
that the expanded observer leaves all 3,116 callback images, clocks, live
framebuffers and audio bytes identical to its probe-disabled control.
`trace-core-heap-b/build.json` pins the separate observer DLL and linked objects.

The initial RAM and REP residual budgets are **explicit offline component
fixtures**. They are not inputs to the browser game. The complete runtime still
needs to generate its heap state through allocations, locks, releases and cache
eviction. The instruction model explicitly rejects unreconstructed first-fit
fallback, arena-growth and overlapping/large-copy paths. Interrupt work and CPU
slice scheduling are not included in these intrinsic work counts. Therefore
this result does not establish elapsed-time parity or close TH-002.

The first two-call report (`heap-check-a`) retains its padding mismatches.
Disassembly at `6F55` showed that tail splitting replaces the entire free header
word; clearing its padding fixed the model. `heap-check-b`, `heap-work-check-a`
and the broader `heap-all-check-a` preserve the subsequent comparisons.

## Continuous memory lifetimes

`near-heap.js` reconstructs the separate near heap used for handle slots and C++
bookkeeping (resident `001C`, `003D`, `0590`). Its two-byte headers encode payload
size and the free bit. Allocation starts at a remembered cursor, coalesces free
neighbors, then wraps once. Handle creation explicitly resets the cursor to the
heap start (`6569..656C`). That reset explains the first retained pointer failure
in `near-heap-check-a`; omitting it returns a later free slot.

`memory.js` adds resource ownership: raw/handle allocations, locking, address
access, retain/discardable/resident flags, discarding, promotion and in-place
resize. Resize can absorb neighboring holes and relocate an unlocked neighbor;
on failure it restores the previous payload size. A growth operation that fills
the rounded block exactly still recalculates padding, unlike the original
same-rounded-size early return. Focused checks cover both cases.

The accepted trace `nature-lifetime-d` adds read-only observations of temporary
catalog pins, restoration of saved flags, promotion, resize and the `EC40`
resident flag. The component replay starts from **one** RAM fixture and never
replaces its simulated state at subsequent checkpoints:

| Comparison | Result |
|---|---:|
| Near allocations, with independently computed return pointers | 237/237 |
| Near frees | 206 |
| Far allocations, with independently computed return pointers | 159/159 |
| Raw frees | 43 |
| Full near/far block chains, search cursors and active/static handle state | 104/104 checkpoints |
| Focused ownership and resize checks | 4/4 |

Accepted reports: `near-heap-check-c/report.json` and
`memory-lifetime-check-f/report.json`. The latter includes every compared state.
`lifetime-control-d-comparison.json` confirms all 3,116 callback images, clocks,
live framebuffers and audio bytes are unchanged by the added probes. Earlier
failed reports are retained: they identified promotion, a static catalog handle,
in-place growth and the resident flag rather than being waived.

These remain component tests. Logical memory requests and selected source
mutation boundaries are explicit observed inputs; the initial RAM includes the
static catalog handle outside the movable heap. Resource payload writes are
outside this structural comparison. The browser must still generate the same
requests from resource loading, decompression, activity transitions and object
destruction, and derive initial memory state through startup. No native heap
fixture or event stream is bundled into the game.

Next loader boundaries: `7A66` obtains/caches resource handles; `7AEF` performs
file reads and checksum loops; `E33C` locks palette/source handles, converts a
shape and restores ownership flags; `D580/D5A7` allocate converted images and LZ
scratch storage. These operations, together with scene object lifetimes, must
drive the recovered memory model before elapsed-time/scanout integration.

## Shape requests now generated from DAT contents

`shape-loading.js` reconstructs the memory side of `E33C`, `7A66` and `D5A7`:
palette/source locks, cached compressed source handles, converted image handles,
1,024-byte LZ scratch buffers, final resize and ownership restoration. The cache
keeps compressed source resources while each call creates a separate converted
image. Discarded sources reuse their original handle slot on reload.

The verification no longer supplies memory-operation lists for selected shape
loads. It removes those native operations from the replay and invokes the loader
with original DAT bytes and the requested palette handle. An initial 30-load
comparison passed; the expanded check covers **all 79 shape loads** between the
first and last heap checkpoints: 30 from TH and 49 from MODULES, spanning 34
distinct shapes. `memory_catalog.py` initializes existing source-cache entries
from the original archive directory in the single starting RAM fixture, using
the original linked-list lookup priority and checking offsets/sizes against DAT.

`generated-all-shape-memory-c/report.json` passes all 79 generated operation
sequences and returned handles, and all 104 continuous heap checkpoints. The
generated calls include 106 handle allocations, 27 resource reads, 79 scratch
allocations/frees and 79 final resizes. Surrounding non-shape operations remain
explicit trace inputs. The same report retains four focused memory checks.

`shape-loading-layout-a/report.json` separately checks all 2,337 original shape
headers across the seven game archives against the recovered VGA storage layout.
All fit the supported 1-, 4- and 8-bit input layouts and compression methods
0..4. Seven synthetic checks cover cold/warm cache use, discarded-source reload,
independent image release, flag restoration, storage sizes and rejection of an
unknown compression method. **Header inventory coverage is not native execution
coverage for every asset.** The raw and RLE routines have no heap scratch calls;
the two LZ routines allocate the recovered 1,024-byte scratch buffer.

The playable file remains unchanged. Next are the SCR constructor/destructor
and drawing surfaces: main `C39D` allocates its near object, preloads images,
creates two work surfaces and composes the first frame. These scene-level
requests, the remaining loader work and startup state must be generated before
the full clock/presenter can use this memory model.

## Animation object and surface lifetimes generated

`animation-memory.js` now reconstructs the memory ownership portions of main
`C39D`/`BD14` and resident `7C96`. The near object occupies
`2 * (0x14E + lastShape - firstShape + 1)` bytes. For the captured SHPL range
1..29 this is 726 bytes. The VGA surface owns a near row table of two bytes per
row and a raw pixel block of width times height; the saved-background surface
owns a second pixel block. Dimensions come from the original SCR bounds:

| Script | Width Ã— height | Row table | Each pixel block |
|---|---:|---:|---:|
| TH:24100 | 178 Ã— 54 | 108 bytes | 9,612 bytes |
| TH:24103 | 94 Ã— 55 | 110 bytes | 5,170 bytes |

Destruction releases loaded image handles in palette-relative order, the work
pixels, row table, saved-background pixels and finally the near object. Each
captured object owns 15 converted images. The model derives those handles from
its own shape loads, and the second object correctly reuses the first object's
freed near address.

`generated-scene-memory-a/report.json` replaces the native memory events for
both object allocations, four pixel-buffer allocations and both complete
destructors with generated operations. All eight lifecycle phases match,
including returned object/pixel/row-table addresses. Heap preparation callbacks
compare the intermediate native before/after states while generated surface
allocation runs; no checkpoint is dropped. All 104 continuous checkpoints and
79 generated shape loads still match, with the original totals of 159 far
allocations and 43 raw frees. Four focused memory checks also pass.

`scene-memory-control-comparison.json` confirms the extra observer labels retain
all 3,116 callback frames, clocks, live framebuffers and audio bytes exactly.
The observer records only boundaries, not changed guest instructions or costs.

This component still begins with an explicit offline RAM/catalog fixture and
uses native call boundaries to compare phases. Full constructor palette setup,
composition callbacks, surrounding scene operations and startup are not yet
generated by this model. No timestamps, recorded operation lists or RAM fixtures
have been added to the playable runtime. Elapsed-time and scanout integration
remain open.

## Resource reads, file lists and DOS transfer work

`resource-work.js` now derives the intrinsic work of resident `7AEF` from the
original DAT payload and checksum. It handles the memory-backed branch,
`FFF0`-byte file chunks, checksum loops and the zero-byte early return. The
zero-byte path skips checksum validation, as the original does.

`resource-work-check-c/report.json` matches all 33 captured reads: 32,307
instruction entries and 10,021 byte-string iterations. Four focused checks cover
empty payloads, a multi-chunk payload, memory-backed copying and a bad checksum.
The captured route itself uses only successful single-chunk file reads.

Resident `794C` walks the file catalog before each read. It opens a missing file
and closes other open files that use a different volume on the same drive. The
model uses file-list state and compares volume strings byte by byte. The file
list is rooted at `SS:204C`; resource lookup priority has a separate root at
`SS:204E`. `resource-open-check-b/report.json` matches all 33 calls, totaling
20,196 instruction entries and 5,544 string iterations. All native calls here
use already-open files. Six focused synthetic checks cover the additional cold
open, volume change, drive and built-in catalog branches.

The isolated reference DLL now has a read-only observer around DOS transfer
accounting as well as the CPU observer. It records the 64-bit I/O counter without
truncation. `dos-work-check-b/report.json` compares all 66 checksum/payload read
transfers and both resulting counters exactly. Five transfers take the saturated
branch. Six focused checks cover the strict threshold, exhausted or negative
budgets, zero-byte reads and an I/O counter above 32 bits. Incoming budgets and
counters remain explicit offline fixtures for this component.

The accepted DLL is `trace-core-dos-b/dosbox_pure_trace.dll`, SHA-256
`a92c96db6fc3943b40864d040d957d96590c62683380253ac7be8744b5229123`.
Both `dos-work-control-comparison.json` and
`open-work-control-comparison.json` pass all 3,116 callback images, clocks, live
framebuffers and audio bytes against the same DLL with probes disabled. The
earlier `trace-core-dos-a` build is unused; its I/O observer field was corrected
to 64 bits before collecting accepted evidence.

All three accepted component reports identify the same `resource-work.js` hash,
`2d6fb5f64ae719299130bdc817a326d2978f4ef35233a39eb245f0311a5b7f79`.
External handle-address calls, DOS interrupt entry/return, resource lookup,
remaining constructor/drawing work and the full CPU/PIC scheduler are still
separate work. These components remain unbundled and do not change the playable
build or its strict 614/984 result. No native timing schedule or RAM fixture has
been added to the runtime.

## Lookup and cache work connected to generated memory

`OriginalResourceWork.lookup` reproduces resident `7BC9`: catalog-priority
traversal, binary type search, binary ID search and the two executable fallback
entries (`FONT:0`, `CURS:0`). Both tag-word and ID comparisons use the original
signed branches. Table order and offsets are checked against the pinned DAT
files; the offline RAM fixture supplies catalog priority.

`resource-lookup-check-b/report.json` matches all 2,496 calls, covering 49 distinct
resource keys, 812,508 instruction entries and every returned directory offset.
Seven focused checks cover catalog precedence, empty/missing tables, signed IDs
and the built-in entries. The observer was expanded to 4,096 calls and 524,288
count rows so repeated sound polling is retained rather than sampled away.

`OriginalResourceWork.cache` reproduces successful resident `7A66`/`7A30` paths.
`resource-cache-check-c/report.json` matches all 2,494 calls and 97,976
instruction entries: 2,463 resident-cache hits and 31 first loads. Its native
inputs explicitly include observed handle state. The other two reads are direct
SCR loads through resident `7688`, outside the cached loader. The verifier checks
every cached read within its own call, then checks both remaining reads inside
the direct-loader boundaries. It does not discard those reads from coverage.

The source ownership model now follows two additional branches from `7AC2` and
`7AD1`: reloading an existing handle skips the first-load directory flag actions,
and promoting a newly created resource is followed by a lock. These paths have
focused checks; all original SHAP entries in TH and MODULES use directory flag
`40`, so the captured shape route does not exercise promotion flag `80`.

`OriginalShapeLoading` now consumes the shared cache-work plan using its own
generated handle state. `generated-scene-memory-c/report.json` still matches all
79 shape loads, eight scene lifecycle phases and 104 continuous heap checkpoints.
`generated-cache-work-a/report.json` then compares all 79 generated cache inputs
and instruction paths against the separate cache observer. Every comparison
passes. The verifier first requires identical native event streams, clocks and
actions across the two observers. No per-call native cache state is supplied to
the generated memory model. `shape-loading-layout-d/report.json` retains all
2,337 header layout checks and passes nine focused checks.

Both new observer/control pairs retain all 3,116 frame callbacks, PIT clocks,
live pixels and audio bytes: `lookup-work-control-comparison.json` and
`cache-work-control-comparison.json`. Earlier failed harness runs are retained:
the first cache verifier lacked the executable's built-in cursor metadata; its
next run incorrectly attributed both direct SCR reads to the cached loader. The
first extended shape check inspected freed handles after a new allocation had
reused one; the check now observes release before subsequent allocation.

The latest five resource-work reports (`resource-lookup-check-b`,
`resource-cache-check-c`, `resource-work-check-d`, `resource-open-check-c`,
`dos-work-check-c`) all identify model SHA-256
`9cf1b2597527606bf489d922bffcf7d0eeedc5753c620aea8a718f7777b6a057`.
The connected shape model is
`90850188a1f7c33e73076a818a9c7f2d3c97791861b23f37aacf1e108377e38e`.
Remaining work includes direct SCR loading, external handle/address work,
constructor/drawing costs, startup memory state and CPU/PIC scheduling. Failed
allocation/read recovery and EMS paths remain outside these component claims.
The live build and strict 614/984 result have not changed.

## Direct script ownership and lookup address work

`OriginalDirectLoading` implements resident `7688` ownership: it allocates an
independent raw block, reads into that block when the source is not cached, or
copies the resident source's actual length when it is cached. A direct load does
not populate the shared cache. The caller retains the returned pointer and later
releases that allocation. The catalog is pinned separately while inspecting its
entry and while allocating, with its flags restored afterward.

`verify_memory_lifetimes.py --generated-scripts` now generates both SCR loads
and releases in addition to the existing object/surface/destructor phases. The
source bytes are TH:SCR24100 (516 bytes) and TH:SCR24103 (367 bytes). Both correctly
allocate at physical address 284980; the first allocation is freed before the
second reuses it. Release uses the model's saved pointer, comparing it with the
native pointer only for verification.

`generated-script-memory-b/report.json` passes 12 lifecycle phases, all 79
generated shape loads and all 104 continuous heap checkpoints. The totals remain
159 far allocations and 43 raw frees. No checkpoint within a generated script
allocation is omitted. `generated-cache-work-c/report.json` retains exact cache
state and instruction work for all 79 shape loads with this expanded model.

`direct-loading-check-b/report.json` compares the two generated direct-loader
instruction paths with the native `7688` observer: both match all 48 intrinsic
instruction entries. Seven focused checks cover independent cached copies,
release ownership, uncached reads, catalog flags and control paths for missing
resources, allocation failure and permanent read failure. The runtime ownership
model currently implements successful loads; the failure checks concern the
instruction-work model. Retryable read failures and payload writes remain
separate work. `direct-work-control-comparison.json` retains all 3,116 callback
images, clocks, live framebuffers and audio bytes with the observer enabled.

`OriginalResourceWork.handleAddress` implements resident `6628`, which obtains
an address without updating a handle's age. The lookup model now reports the
handles it visits, allowing this helper's work to be composed with each binary
search. `lookup-address-check-a/report.json` matches all 2,496 lookup calls
including their 10,018 nested address calls: 972,796 instruction entries in
total. Directory offsets still match, and eleven focused checks pass. The four
new checks cover resident, null, discarded and EMS handle-address queries.
This non-materializing helper returns zero for EMS; that does not establish
support for EMS allocation or materialization elsewhere in the memory model.
`lookup-address-control-comparison.json` confirms unchanged frames/clocks/audio.

The current shared resource-work model is SHA-256
`a08903629c756bf2e8ef1d250440b954f887a6fac880e146754dd30d51165a2d`.
Cache, file-open, payload-read, DOS transfer and shape-layout comparisons were
rerun against it (`resource-cache-check-d`, `resource-open-check-d`,
`resource-work-check-e`, `dos-work-check-d`, `shape-loading-layout-e`), all passing.
The direct-loading model is
`16851cc17c7237bad25ee0bfe016b0b1d627b0683ccc86c776d3448bb5563d77`.
Other memory helper work, constructor/drawing work, startup state, CPU/PIC
scheduling and live scanout integration remain open. The live demo remains
unchanged; these results do not establish elapsed-time parity.

## Resource-entry memory helpers and native return values

`memory-work.js` derives the work of resident `75C6` (address plus cache-age
refresh), `EC14` (payload length) and `6FA9` (block-header arithmetic).
`resource-work.js` now exposes the shared `7A30` entry query and composes these
helpers with it. The normal resident address path sets age bits `01F0` while
preserving ownership flags. This differs from `6628`, which does not change age.
Payload length subtracts the six-byte block header and its encoded padding.

The isolated observer now supports explicit disjoint code ranges, records the
source block header, and records AX/CX/DX at function return. It remains read-only.
The accepted capture uses `trace-core-entry-c` and is
`nature-entry-work-b/trace.json`. `entry-work-control-comparison.json` confirms
identical images, clocks, live pixels and audio across all 3,116 callbacks.

`entry-memory-check-b/report.json` matches all 2,496 queries and 212,313
instruction entries. It also compares every returned cached handle, payload
length and materialized pointer with native register observations. All pass.
Five focused checks cover age/ownership bits, null and discarded handles,
padding across a 16-bit length boundary, and the distinct EMS query behavior.
EMS materialization remains unsupported and is rejected explicitly.

For 81 of those queries, inputs come from the continuous memory model: 79 shape
loads and two direct script loads. The verifier compares generated handle state,
block size, padding, work and results with the native observations. It supplies
no per-call native state to the generated model. All 81 pass.
`generated-entry-memory-a/report.json` retains 12 lifecycle phases, 79 shape
loads and all 104 heap checkpoints. The remaining queries still use explicit
native input fixtures for component verification.

The first comparison exposed an invalid harness assumption, preserved in
`entry-memory-check-a`: resident sounds do not necessarily retain their packed
DAT lengths. Original `E88E` reads the compressed stream's output count;
`E935` resizes the same cache handle to that count plus ten header bytes, then
`EC40` marks it prepared with bit `2000`. The corrected verifier derives the
prepared lengths from the pinned compressed data and requires them to agree
with native returns. It does not waive the size comparisons.

| Sound | Packed DAT bytes | Prepared cache bytes |
|---|---:|---:|
| 1006 | 863 | 1,866 |
| 1011 | 3,753 | 5,126 |
| 1017 | 652 | 1,386 |
| 10048 | 2,074 | 4,942 |
| 10049 | 2,828 | 5,610 |

These account for 2,392 prepared-sound queries; the other 104 use directory
payload lengths. The native returns and the source-derived expected lengths
agree in every case. Generating sound preparation's allocation/resize lifetime
is a remaining step, along with other helper work, drawing/constructor costs,
startup state and scheduling.

Current model hashes and all passing checks are recorded in
`entry-memory-check-b/report.json`. The existing cache, lookup/address, read,
file-open, DOS transfer, shape-layout, direct-load and generated-cache comparisons
were rerun against the same source versions and pass. The live build remains
unchanged, with strict timing still 614/984 and 12 missing native displays.


## Generated sound preparation and shared resource ownership

`resource-loading.js` now owns the common source-cache lifetime used by shapes
and sounds. `sound-loading.js` reconstructs E4AA/E6E6 preparation: ready bit 2000
skips preparation, non-digital resources pass through, and compressed streams
expand to `max(decoded count, packed bytes) + 266` before shrinking to decoded
count plus ten header bytes. ED3E resizing preserves the existing handle, moves
an unlocked allocation when necessary, and respects locked allocations.
Directory bit 20 is accepted without inventing ownership behavior for it.
Resampling outside the supplied native rate bounds remains explicitly unsupported.

`generated-sound-memory-a/report.json` generates all 2,399 sound loads within
the continuous memory comparison window, together with 79 shapes and 12 scene /
script phases. All 104 checkpoints, 159 allocations and 43 raw releases match.
Only one initial RAM/catalog fixture initializes this model; checkpoints never
reset it. The two decompressions are sound 1011 (3,753 -> 5,382 -> 5,126 bytes)
and sound 1006 (863 -> 2,122 -> 1,866 bytes). Repeated prepared loads do not resize.
Other memory requests outside the generated loaders remain observed inputs.

`generated-sound-entry-check-a/report.json` matches all 2,496 native resource
queries, with 2,480 query inputs independently supplied by the continuous model.
`generated-sound-cache-check-a/report.json` matches all 2,478 generated shape /
sound cache inputs and intrinsic instruction paths. Sixteen earlier queries
precede the initial memory fixture and remain outside generated coverage.

The new labels and profiles use the existing read-only `trace-core-entry-c`
observer. `sound-memory-control-comparison.json` and
`sound-cache-control-comparison.json` each preserve all 3,116 frames, clocks,
live pixels and audio against the same DLL without probes.

`sound-loading-layout-b/report.json` validates all 283 original digital resource
storage layouts and nine focused ownership cases. These include relocation with
payload and handle preservation, locked growth failure, discarded-handle reuse,
compressed counts overriding header counts, repeated preparation, uncompressed
and non-digital resources, explicit resampling rejection and directory bit 20.
This inventory check does not claim native execution of every sound.

These components remain unbundled. PCM payload writes, remaining helper work,
startup state, drawing and constructor work, CPU/PIC scheduling and integrated
scanout remain open. The live build still matches 614/984 unshifted nature
callbacks with 12 missing native displays; no completion claim changes.


## Source-derived sound decoder and preparation work

`sound-work.js` transcribes resident E964's variable-width delta decoder and
counts its executed instructions from compressed bytes. All 273 compressed
original digital assets produce identical PCM bytes and consumed byte counts
to the independent Python decoder. The native route decompresses sounds 1011
and 1006: all 335,465 and 88,576 instruction entries respectively match. The
remaining ten digital resources are uncompressed. `sound-work-check-c/report.json`
records these results and three focused decoder checks. The count of native
calls is two; the initial expectation of three was rejected before comparison.

The same module derives intrinsic E6E6 preparation paths from the generated
memory model's decisions. `sound-preparation-work-a/report.json` matches all
2,399 loads, their returned handles and 46,011 instruction entries. The work
counts exclude separately modeled callees. No native per-call branch input
is substituted into the generated memory decisions.

`sound-decode-control-comparison.json` and
`sound-prepare-control-comparison.json` confirm unchanged pixels, live scanout,
clocks and audio across all 3,116 callbacks for these isolated profiles.

This establishes decoded source bytes and intrinsic instruction work, not
native mixer output or elapsed-time equality. PCM writes into the memory model,
copy/resize and other helper costs, resampling paths, the sound backend and full
CPU/PIC integration remain open. None of these new models is bundled into the
current playable file yet.


## Segmented copy work shared by sound preparation and heap relocation

`memory-copy-work.js` reconstructs resident 6C18. It normalizes far pointers,
chooses forward or backward traversal from overlap, and splits large transfers
at the original FFF0 / FFE0 chunk boundaries. It reports logical REP operations
separately from their CPU-slice resumptions. The former restricted heap copy
counter now delegates to this shared implementation.

`memory-copy-work-a/report.json` matches all 59 native calls, all 4,795
instruction entries, REP iteration counts and returned destination pointers.
This includes the backward overlapping move used while preparing sound 1011.
The 64 observed REP dispatch slices are explicit offline residual-budget inputs;
the model does not yet generate those budgets from a complete CPU/PIC schedule.
Five synthetic cases cover zero length, forward and backward chunk boundaries,
odd tails, adjacent non-overlap and rejection of unsupported address wrap.
Native multi-chunk execution is not claimed by these synthetic cases.

Sound preparation now derives each copy's source, destination and length from
its generated expanded allocation. Both generated triples match the original:
1011 has 3,743 compressed bytes and 1006 has 853. No per-copy native address is
fed back into the generated memory model. Other copy callers still use explicit
native arguments for this component comparison.

`generated-sound-memory-b/report.json` retains all 104 matching heap checkpoints,
2,399 sound loads, 79 shapes and 12 lifecycle phases. Its refreshed dependent
proofs are `generated-sound-entry-check-b`, `generated-sound-cache-check-b`,
`sound-preparation-work-b` and `sound-loading-layout-c`, all passing.
`heap-all-check-b/report.json` confirms the shared copy implementation preserves
all 52 heap-preparation comparisons, including their state, payload and work.
`memory-copy-control-comparison.json` confirms the capture observer preserves
all 3,116 frames, clocks, live pixels and audio.

ED3E/70E8 resize instruction work, first-fit and other helper work, generated
startup state, drawing/constructor work and complete CPU/PIC scheduling are
still required before these components can drive the live presenter. The live
build and strict timing result are unchanged.


## First-fit allocation and in-place resize instruction work

`OriginalHeapWork.firstFit` now reconstructs resident 6D47's search from the
remembered block, wrap to heap start, free-block coalescing, size comparison,
splitting and padding. It uses actual modeled heap decisions. The continuous
memory verifier can enable `--allocation-work` to derive a parallel work model
before each allocation and require identical resulting heap state.

`first-fit-work-b/report.json` compares all 159 allocations in the generated
window with native 6D47 observations. Requested lengths, returned block addresses
and all 17,883 instruction entries match. Ten earlier calls precede the initial
memory fixture. Seven focused cases cover wraparound, adjacent holes, small
remainders, minimum free headers, skipping a small hole, a word-sized length
boundary and explicit rejection of unreconstructed memory pressure.
`heap-all-check-c/report.json` retains all 52 heap-preparation comparisons on
the same updated heap-work source.

`memory-resize-work.js` derives resident 70E8's intrinsic instruction path from
block size, requested length and surrounding allocations. It preserves padding
when the rounded size is unchanged, recalculates it after growth, and splits
remainders using the original six-byte minimum. Successful growth can coalesce
holes or relocate an adjacent movable allocation. Failed relocation and arena
growth paths are explicitly unsupported in this work model.

`generated-resize-memory-a/report.json` enables both `--allocation-work` and
`--resize-work` while retaining 2,399 sound loads, 79 shapes, 12 lifecycle phases
and all 104 matching checkpoints. `resize-work-a/report.json` matches all 97
successful resize calls in this window, including addresses, lengths, returned
lengths and 4,295 instruction entries. Nine earlier calls precede the fixture.
Six focused cases cover padding, split thresholds, growth, word-sized lengths
and explicit rejection of unsupported pressure. Callee work is excluded from
this intrinsic profile and must be composed separately.

`first-fit-control-comparison.json` and
`memory-resize-control-comparison.json` each confirm identical images, clocks,
live scanout and audio across all 3,116 callbacks against the same DLL without
probes. No native per-call heap state is supplied to the generated work models;
one initial RAM/catalog fixture and surrounding non-generated logical requests
remain explicit offline inputs.

ED3E and remaining helper/wrapper costs, startup state, drawing and constructor
work, CPU/PIC scheduling and live scanout integration remain open. The playable
build is unchanged, and strict nature timing remains 614/984 with 12 missing
native display changes.


## Handle resize composition and full resource work inventory

`handle-resize-work.js` reconstructs ED3E's choice of in-place resize, locked
failure, relocation or discarded-handle reallocation. It updates a supplied
memory model and counts its intrinsic instructions; callees retain separate
costs. Five synthetic cases check those choices, old-data copy length and null
handle failure.

The native profile exposed a missing layer in the shape loader: shape conversion
also calls ED3E. `shape-loading.js` now invokes `resizeHandle` instead of bypassing
it with a direct block resize. The generated memory model consequently drives
83 ED3E calls: 79 shape conversions and four resizes in two sound preparations.
All 2,075 instruction entries, handles, requested lengths and returned statuses
match in `handle-resize-work-b/report.json`. Fifteen other native ED3E calls
remain outside generated wrapper coverage (nine outside the fixture window and
six other callers within it). The earlier four-call assumption was rejected by
the verifier, preserved as the failed `handle-resize-work-a` attempt.

`generated-handle-resize-memory-b/report.json` retains all 104 heap checkpoints,
159 allocations, 97 block resizes, 2,399 sound loads, 79 shapes and 12 lifecycle
phases. Updated entry/cache, first-fit, block-resize, copy and sound-preparation
proofs all pass against this report. `shape-loading-layout-h/report.json` keeps
all 2,337 original shape layouts and nine ownership checks passing.

The broader `resource-total` profile records every resident instruction inside
2,494 resource-cache calls. The read-only observer still preserves all 3,116
frames, clocks, live scanout and audio, as confirmed by
`resource-total-control-comparison.json`. `audit_resource_work.py` classifies all
370,350 instruction entries without unknown addresses. This is an inventory,
not a composed timing proof: membership in a modeled routine does not prove
that every call has generated inputs or that elapsed time is correct.

| Remaining group in this capture | Instruction entries |
|---|---:|
| Near-heap allocation search | 62,127 |
| Near-heap allocation wrapper | 434 |
| Handle allocation wrapper | 1,240 |
| Handle lock wrapper | 372 |
| Discardable wrapper | 270 |
| Far-allocation wrapper | 186 |
| Resident timer interrupt | 107 |

The near-heap search is the largest remaining resident resource cost. Timer
interrupts need independent scheduling; the inventory also excludes DOS/BIOS
execution outside the resident address window. `resource-work-inventory-a`
explicitly leaves `full_resource_work_parity` false. Startup state, other
resource callers, drawing/constructor work and complete CPU/PIC/scanout
integration remain open. The live playable file and its strict 614/984 result
are unchanged.


## Near allocation work and the first complete cache-hit comparison

`near-heap-work.js` reconstructs the 003D allocation wrapper and 0590 near-heap
search, including wraparound, coalescing adjacent free headers, rounded sizes,
split remainders and exact fits. It operates on modeled near-heap state rather
than a native per-call snapshot. The continuous verifier's `--near-work` option
requires its returned pointer and resulting near heap to match the ownership
model at every allocation.

`generated-near-work-memory-a/report.json` retains all previous generated
ownership and work checks plus 237 near allocations and all 104 heap checkpoints.
`near-allocation-work-a/report.json` matches those allocations against native
arguments, returned pointers, all 275,288 instruction entries and 32,870 header
reads. Seven focused cases cover wraparound, merging header bytes, odd rounding,
zero-size remainder blocks, exact fits, zero payloads, skipped small holes and
explicit rejection of unreconstructed growth. The profile's control preserves
all 3,116 frames, clocks, live scanout and audio.

`resource-cache-work.js` composes the cache-hit path with its address and payload
length helpers, counting the shared 7A30 entry body only once. Its inputs come
from the continuous memory model. Unlike the earlier isolated routine checks,
`verify_resident_cache_work.py` compares every resident instruction observed in
the full 7A66 call, without discarding addresses outside the selected routine.

The resulting `resident-cache-work-b/report.json` intentionally **fails**:
2,447 of 2,449 generated cache hits match fully. Calls 117 and 1583 have matching
cache inputs, results and resource instructions, but the native timer handler
at 6447..6487 ran inside each call. Those extra instructions remain mismatches;
the verifier only labels their cause, it does not remove them. The earlier
`resident-cache-work-a` failure is retained as well. This proves the need to
compose independent interrupt scheduling before claiming full elapsed-time
parity, even for cache hits.

`resource-work-inventory-b/report.json` updates the routine inventory to include
the new near-allocation model. Remaining unmodeled resident costs in that cache
capture are handle allocation (1,240 entries), locking (372), discardable marking
(270), the far-allocation wrapper (186) and timer interrupts (107). Classification
still does not establish complete composition, and the inventory leaves
`full_resource_work_parity` false. Cold resource paths, startup, other callers,
drawing/constructor work and full CPU/PIC scheduling remain open.

The current playable file is unchanged. Its strict nature result remains
614/984 with 12 missing native display changes.

## Timer state, allocation wrappers and complete resident resource composition

`timer-work.js` reconstructs resident IRQ0 at 6447..6487: the 32-bit game tick,
four saturating countdowns, the BIOS phase accumulator and the branch between
direct PIC acknowledgement and chaining the original BIOS handler. The new
read-only timer observer captures nine state words before and after each IRQ.
`timer-work-control-comparison.json` confirms all 3,116 frames, clocks, live
frames and audio remain identical to a no-probe run of the same new DLL.

`timer-work-check-a/report.json` matches all 1,127 IRQ calls and their 40,300
resident instruction entries, including 342 BIOS chains. Tick and BIOS phase
advance continuously from one initial state, with 19 observed game countdown
writes between interrupts. Eight focused cases cover carry, wrapping, countdown
saturation, both BIOS branches and invalid inputs. The observed BIOS step is
19,886. IRQ delivery times, BIOS execution and PIC I/O costs remain separate.

`memory-wrapper-work.js` adds handle allocation (652A/6566), far allocation
(6E8D), locking (6510) and discardable marking (659E). Combined with generated
near/far allocation and address work, `resource-allocation-work-a/report.json`
matches 29 cold source loads, all 64,772 instructions in the memory ranges and
their returned handles. Allocation state comes from the continuous ownership
model; six focused cases cover null/nonresident/resident handles and explicit
rejection of unreconstructed allocation failure.

`resource-cache-work.js` now composes cold loads as well as hits. Its cold path
combines allocation, cache, address, file-list traversal, DAT checksum/read and
discardable work. `complete-cache-work-b/report.json` matches every resident
instruction in **2,478 generated calls**, including **29 cold calls**, for
**362,222 instruction entries**. There are no address-range exclusions in this
comparison. The file list and initial file-handle states remain offline inputs.

**Interrupt placement is still an observed fixture.** Three calls (8, 117 and
1583) include timer work selected by observed IRQ boundaries. This proves the
component composition, not an independently generated execution schedule. The
report explicitly sets `full_scheduling_parity: false`. The updated strict
cache-hit check, `resident-cache-work-c/report.json`, still fails at 117 and
1583 when those fixtures are absent. Earlier failures remain preserved.

`resource-work-inventory-c/report.json` now finds a component model for every
resident code group in the 2,494-call capture. Sixteen calls outside the current
generated ownership coverage, DOS/BIOS code, startup state, drawing/constructor
work and live scheduling remain open. No live build was changed.

### Next scheduling seam in the pinned core

The pinned `include/pic.h` computes the fractional millisecond with **float**
division of `CPU_CycleMax - CPU_CycleLeft - CPU_Cycles`; `PIC_FullIndex` then
adds that float to the integer millisecond. `src/hardware/pic.cpp` services
events at their queued index, reschedules from that index during event service,
truncates the next event's cycle distance and guarantees a minimum one-cycle
slice when the truncated distance is zero. Each millisecond subtracts 1 from
queued event indices. `src/hardware/timer.cpp` computes PIT delay using float
division with `PIT_TICK_RATE = 1193182`. `core_normal.cpp` decrements the CPU
budget before dispatching each instruction. These details require explicit
rounding and ordered execution; aggregate instruction counts alone cannot
generate the three interrupt placements or the original scanout times.

## Event queue and periodic PIT phase

The isolated PIC observer records add, remove, queue-start, event-service,
slice-allocation and millisecond-shift operations. Its first fixed-buffer
capture (`nature-pic-work-a`) exceeded capacity and was rejected. The revised
probe streams bounded batches at frame callbacks and retains overflow checks;
it does not change guest memory, registers or clock budgets.

`nature-pic-work-b` records 766,599 operations in `pic.jsonl`, with one initial
queue fixture. `pic-work-control-comparison.json` passes all 3,116 frame,
clock/live-frame and audio comparisons against a no-probe run of the same DLL.
`clock-queue.js` reconstructs stable equal-time ordering, float-rounded event
indices, rescheduling from the serviced event's scheduled index, queue hashes,
millisecond shifts and CPU slice arithmetic. Its verifier drives CPU budgets
and event requests as explicit external inputs while keeping the queue
continuous; it is not a complete guest instruction executor.

`clock-queue-check-a/report.json` passes **all 766,599 operations** and seven
focused cases. The native trace includes 11,658 additions, 56 removals, 381,002
queue starts, 11,658 event services, 343,448 slice allocations and 18,777
millisecond shifts. Every before/after queue hash, queue head/count, float clock
value, service state and primitive CPU-budget result matches. There are still
343,478 external CPU-budget inputs between these operations; the report keeps
`full_cpu_scheduling_parity: false`. Selective removal is covered by a focused
case, with no occurrence in this native route.

`pit-clock.js` uses the pinned core's rounded PIT delay formula. From one initial
queue phase, `pit-clock-check-a/report.json` matches all 1,127 timer services and
reschedules across 18,777 millisecond shifts. No event resets its predicted
phase. Counter 19,886 and observer handler identity 4 are explicit component
fixtures. The resulting delay is 16.666358947753906 ms. IRQ admission and game
startup hardware programming remain separate.

The same trace exposes float-rounded video event delays of 3.17775559425354 ms
for partial display updates and 14.268064498901367 ms for frame scheduling.
The presenter's earlier double-precision intervals must be reconciled during
clock integration; component frame matches supplied with native commit-time
fixtures do not establish a generated video schedule. The live build remains
unchanged.

`timer-work-check-b/report.json` also repeats the 1,127-IRQ state/instruction
proof on the new PIC-observer capture. The next CPU step is to identify normal
core exits and callback work: many queue starts occur with a partially consumed
CPU slice, so assuming every return exhausted the slice would be incorrect.

`cpu-budget-inventory-a/report.json` inventories those 343,478 external changes:
313,073 consume part of the available slice, 30,374 end at -1 and 31 take other
numeric paths (the first examples end at -2). The inventory does not infer exit
causes from these numbers. Read-only normal-core entry/exit and callback
observations are the next step; IRQ controller admission and port I/O debits
also remain outside the verified queue component.

## Normal CPU exits and callback budget work

The new normal-loop observer records decoder and callback entry/exit boundaries,
instruction entries, string-loop iterations, I/O debit and stack-segment cycle
credits. These counters are read-only and streamed at video callbacks. The
isolated builder verifies the pinned normal core, string/prefix headers and
main-loop sources before inserting observers. `nature-cpu-work-b` contains
1,312,974 balanced boundary records. `cpu-credit-control-comparison.json`
preserves all 3,116 frames, clocks/live frames and audio against the same-DLL
control. Its PIC JSONL hash is identical to the already verified queue input.

`cpu-run-inventory-b/report.json` identifies 343,448 normal decoder runs:
313,039 return a callback, 30,405 end with negative budgets and four return zero
with a nonnegative budget. Every positive return matches the actual FE /7
callback opcode and ID. The route executes 187,382,196 instruction entries,
331,692 string iterations, 37 stack-segment credits and 14,548 I/O-debit cycles.
The total remaining-budget arithmetic matches every decoder run. The earlier
`cpu-run-inventory-a` is retained: its formula lacked the credits and differed
on 23 runs.

The callback distribution explains most partial CPU slices: 208,153 mouse
position reads and 104,076 keyboard polls. There are also 33 file seeks, 66 file
reads, 342 BIOS clock callbacks, 342 user-timer callbacks, 20 BIOS device-post
callbacks and seven mouse interrupt/return callbacks. Of the 66 file reads,
five take the already reconstructed saturated DOS transfer-budget branch.

`cpu-budget.js` implements dispatch-loop decrement, string-loop decrement,
stack-segment credit, port read/write debit and supported callback budget
changes. Seven focused cases pass. `cpu-budget-check-a/report.json` deliberately
**fails one of 656,487 comparisons**: all 313,039 callback changes and 343,447
normal runs match both CPU-cycle fields and I/O state, while one normal run has
a different division between the active slice and remaining millisecond budget.

At 113725.03200000152 ms, boundary ordinal 392199 follows `OUT 20h,AL` at physical
144219 in the sound driver. The trace and pinned PIC code point to an
acknowledgement activating the preceding timer request and transferring the
remaining 6,199 cycles into `CPU_CycleLeft`; controller-state observations are
still needed to verify that causal sequence. Native state is `cycles=-1,left=9681`, while
the CPU-only model predicts `cycles=6198,left=3482`; the totals are equal.
`PIC_Controller::activate` explicitly performs this transfer even before CPU
interrupt admission. It must be composed with the controller state, not hidden
by a total-budget-only comparison or an observed transfer flag.

Instruction paths, callback register/RAM effects, initial hardware state and
IRQ admission remain ungenerated. The budget verifier uses observed work
counts and exit modes as component inputs. This is not a live CPU executor.

### Polling code for the next execution layer

The DOS `overhead()` helper changes `reg_ip` by two rather than immediately
debiting cycles. For keyboard polling, this enters the CB_INT21 trampoline's
`push cx; mov cx,0140h; loop; pop cx; iret` delay. Its work belongs to subsequent
guest execution. Original resident 545F..546D calls 5569, then invokes DOS with
AX=0C06/DL=FF. Resident 54C5..54E5 polls mouse function 3; wait routines 5697 and
56C2 call the far function at DS:15F0 until a countdown completes. These routines
and the pinned callback trampolines are the next sources for generated polling
work. No instruction count or callback timestamp from the trace may become
runtime playback data. The live build and strict 614/984 result are unchanged.

## Interrupt controller and composed CPU budgets

`interrupt-controller.js` models the pinned dual PIC controller: request/mask/
in-service registers, priority and cascading, EOI, initialization, interrupt
admission and CPU-budget transfer. The new read-only observer records every
controller operation and its CPU context. `irq-work-control-comparison.json`
passes all 3,116 callbacks, clocks, live frames and audio. The CPU and event-queue
streams are byte-identical to the previously accepted capture.

`irq-controller-check-a/report.json` matches all 3,575 operations, including
1,156 deliveries: 1,127 timer, 26 sound and three mouse interrupts. Controller
state is continuous from one initial fixture. Only external CPU budgets, flags
and operation requests are supplied between operations.

This confirms the previously inferred sound-driver EOI sequence. At operation
950, IRQ0 is pending while IRQ7 is in service. Writing 20h to port 20h clears
IRQ7, admits the pending request to the CPU-check stage and transfers the
remaining 6,199 cycles into `CPU_CycleLeft`. The following failed dispatch check
leaves `cycles=-1,left=9681`. Actual CPU interrupt entry occurs later when IF
allows it.

`cpu-irq-check-a/report.json` composes those controller operations with CPU work
segments. All 343,448 normal runs and 313,039 callbacks now match all budget
fields: **656,487/656,487**. It also checks all 3,575 controller operations, 1,257
of them within CPU runs. The single budget transfer is generated by controller
state; no recorded transfer flag or per-operation controller reset is used.
The earlier CPU-only failure is retained as diagnostic evidence.

Instruction/string/stack-credit/I/O counts, controller requests and flags still
come from offline observations. The next execution layer must generate those
paths and requests. This component result does not change the live build or
establish integrated timing fidelity.

## Generated input polling and callback trampolines

`polling-work.js` reconstructs resident 58E2 as an ordered instruction generator,
with explicit DOS keyboard and mouse callback yields. It includes the 320-LOOP
DOS delay, mouse-button edge detection, the 96-entry key scan and key latches.
Cursor-movement, joystick and Control-key exit paths fail explicitly until
reconstructed. Generated paths retain original instruction addresses for work
accounting; native timestamps are not execution inputs.

The polling observer streams completed calls and selected-instruction counts,
input memory before/after, mouse callback results and an ordered instruction
hash. `nature-poll-work-b` contains 104,075 complete calls and one explicitly
excluded final partial call. `poll-order-control-comparison.json` passes all
3,116 callbacks, clocks, live frames and audio; its CPU, queue and controller
streams are byte-identical to the accepted IRQ capture. The failed first probe
build is retained; the accepted probe is `trace-core-poll-c`.

`polling-work-check-c/report.json` matches every selected instruction count and
ordered path hash for all 104,075 complete calls: 136,233,469 instruction entries,
104,075 keyboard callbacks and 208,149 mouse callbacks. All return values and
input-state memory match. One initial input-state fixture is carried through the
entire capture without resetting mouse edges or key latches. Only four distinct
input/result combinations occur, allowing the verifier to memoize generated
paths while still comparing every native call. Eight focused branch checks also
pass; native evidence on this route covers the actual mouse journey.

Mouse callback results remain offline inputs. IRQ execution outside the selected
polling code, caller work between polls and CPU scheduling are not included in
this path proof. For example, the first idle calls execute 1,309 instructions
each, with 85 instructions between them; those caller paths must be recovered
before continuously scheduling the polling generator. The live build is still
unchanged and does not consume these verification fixtures.

## Poll callers and the remaining animation busy loop

`trace-core-poll-e` extends the read-only polling observer with CPU context,
caller stack/global fields and work between polls. Each gap retains an ordered
prefix of at most 256 instructions plus an ordered hash; gaps above 1,024
instructions also retain a complete sparse instruction histogram. These are
offline observations. `poll-gaps-control-comparison.json` again preserves all
3,116 frames, clocks, live frames and audio. CPU/PIC/controller streams remain
byte-identical to the accepted IRQ capture. `polling-work-check-d` repeats the
104,075-call continuous input-state and ordered-path proof on this capture.

The three observed callers are main 18CD (return 1A68, 34,186 polls), resident
5697 (return 569E, 56,060 polls), and resident 577E (return 5787, 13,829 polls).
`wait-work.js` provides ordered timer/sound wait generators, timer-setting
wrappers and the three-channel sound-status lookup. Timer and sound state are
read through the shared caller interface. The non-aborting timer wait preserves
the last input result in AX on expiry; its caller does not use that result to
abort the wait. `nature-idle-work.js` derives the shared input wrapper and nature
idle branch from game state, including the completion-mask comparison.

`poll-callers-check-b/report.json` compares all **101,652** eligible uninterrupted
continuations: 56,039 timer, 11,448 sound-ID-zero, and 34,165 nature idle paths.
All 3,754,218 generated instruction entries match in order and hash. Ten focused
branch checks also pass. Selection uses original arguments and global state,
not the observed path length/hash. IRQ observations identify interrupted gaps.
The report leaves 2,423 gaps explicitly uncomposed: one initial context, 40 IRQ
intervals, 15 caller transitions, six expiry transitions and 2,361 specific-sound
resource lookups. The latter should compose with the existing sound/resource
work, not acquire a hard-coded 623-instruction cost.

The gap inventory reveals the main remaining execution hotspot. Between poll
31,250's return and poll 31,251's entry, the original executes 44,279,929 guest
instructions over about 4.441 seconds. This interval encloses the question SCR
24100 constructor and animation. Its main BDA0 interpreter enters 626,497 times
and fetches 626,544 opcodes, repeatedly checking display deadlines between real
updates. The next work is to generate this interpreter/wrapper execution against
the shared clock, then join rendering and resource operations at their actual
call sites. Those loop frequencies are evidence of the missing execution layer,
not runtime constants or recorded schedules.

The live SHA and strict 614/984 comparison remain unchanged. Caller path proofs
do not close timing integration, audio, RNG or broader activity coverage.


## Interpreter and animation wrapper instruction generators

`script-work.js` reconstructs main BDA0 interpreter work with named callees for
rendering, bounds, audio and callbacks. `script-work-check-b` matches all 626,498
calls (28,822,581 intrinsic instruction entries and ordered path hashes).
It compares all 726 instance bytes for 626,451 calls; 47 rendering/bounds calls
initially compare only interpreter-owned PC/scratch/delay fields. No expected
callee memory is injected. Initial code/state and actual timer operand reads
remain offline inputs. Unsupported direct-slot opcode F0 is explicit.

`script-wrapper-work.js` reconstructs the loop at main 485D and callback helper
4E9E from caller arguments. `script-wrapper-check-a` matches 626,403 uninterrupted
continuations (14,706,534 ordered instructions). Independent IRQ delivery counters
identify 93 interrupted gaps; one initial gap and one activity-overlay call are
uncomposed. Eight focused exit/intro/callback checks also pass. The observer
coalesces only identical states, work and ordered gaps, so observed repetition
counts are comparison weights rather than runtime scheduling parameters.

The accepted `nature-script-wrapper-a` capture passes its same-DLL control and
has byte-identical CPU, PIC and IRQ streams to the previous accepted IRQ capture.
Frame-update/scene/slot composition is the next layer. The first drawing capture
revealed the always-enabled caption branch and its clipping intersection; the
initial `script-drawing-check-a` failure is retained pending that composition.
These are unbundled components; strict live parity remains 614/984.


## Composed frame update, scene and slot bounds

`animation-work.js` now supplies main C78A frame updates, C9ED scene composition,
CBD2 slot drawing dispatch, and CC1E dirty bounds. It reproduces display/timer
stamps, dirty rectangle clearing/union/intersection, delayed frame movement,
wrap/ping-pong direction, 16.16 velocity/acceleration, background restore and
caption clipping dispatch. Actual resident graphics execution is an explicit
callee, not assumed to consume no time in the future scheduler. Nonzero room
object/cursor/activity composition flags remain explicit unsupported branches.

`script-drawing-check-b` composes these generators with BDA0 and matches every
one of 626,498 calls: all 726 instance bytes, return/context/display globals,
28,822,581 interpreter instructions and 27,029 drawing instructions, with both
ordered hashes exact. The previous 47 partial-memory comparisons are now full
comparisons. Ten focused state/branch checks pass, including reverse wrap,
ping-pong reversal, delayed counter comparison and fixed-point carry. All shape
headers and timer operands are declared input fixtures; expected after-memory
is never substituted for generated state. This does not verify pixel copies.

The initial drawing failure (`script-drawing-check-a`) exposed the caption branch.
A new observer records its rectangle/id as operands, and the model derives the
intersection result. `nature-script-drawing-b` passes its same-DLL control with
identical frames, clocks and audio; its CPU/PIC/IRQ stream digests remain identical
to `nature-irq-work-a`. `script-wrapper-check-b` also repeats the prior wrapper
result on this capture. Build `trace-core-script-e` is the accepted observer for
these comparisons. The live playable file remains unchanged.

### Next execution integration

Resident calls remaining beneath the animation layer include clip push/pop
(7DB6/7E1C), offset/intersection/union/empty rectangles (8242/83B4/84FA/7EE6), near
copy/fill (096E/099A), surface transfers (7E32), shape drawing (8272), shape-header
lookup (6628), and main 64A4 caption drawing. REP work must split at generated CPU
budgets; recorded dispatch counts cannot determine runtime progress. The wrapper
also needs its activity overlay and IRQ guest work. A continuous execution-clock
comparison should start from one declared initial state and generate subsequent
loop counts, timer reads, callbacks and budgets before promotion to the demo.


## VGA surface copies and generated CPU/queue execution

`surface-copy-work.js` reconstructs resident 9A68 (the VGA backend selected by
DS:207E for 7E32). It clips source and destination bounds, applies active destination
clipping, reverses overlapping traversal, performs indexed pixel writes and yields
REP work for the CPU executor. A shared destination buffer exposes intermediate
writes to scanout. Original mode 4 follows the same fast-copy path as mode 0;
other bitwise modes follow the original XOR/AND/OR operations. Twenty focused
checks cover clipping, overlap, modes and visibility of partial writes.

The first observer attempt detected nested copies during cursor preparation.
`blit_probe.h` now has a bounded stack and attributes intrinsic instructions to
each invocation separately. Pixel snapshots begin after cursor preparation and
end before cursor restoration; those helpers are not silently treated as free.
`nature-blit-clock-a`, built with `trace-core-blit-c`, passes its same-DLL control
(frames, clocks, audio) and retains all 39,543 resource instruction events exactly
from `nature-irq-work-a`. `surface-copy-check-c` matches all 123 calls, 59,167
intrinsic instructions, 3,305 REP dispatches and 136,442 pixel writes. Two calls
are clipped empty. No expected output pixels generate the writes.

`work-runner.js` executes instruction generators against `OriginalCpuBudget`,
preserving the pending instruction across exhaustion and publishing partial REP
writes before queue service. `copy-execution-check-a` derives 2,799 budgets for
109 loops from one starting budget each. Twelve longer copies originally needed
queue refills; those are now composed in `execution-clock.js`.

`OriginalExecutionClock` couples generated work with `OriginalClockQueue` and
explicit hardware/interrupt composition points. `OriginalVgaEventWork` generates
the pinned M_VGA/PART latch, vertical, interrupt-marker and four-part draw events.
`copy-clock-check-a` matches all 121 nonempty copy loops and all 3,305 REP budgets:
cycles, remaining budget, exact float milliseconds, tick count and VGA part state.
The execution produces 12 refills, nine millisecond transitions and three hardware
events (one panning latch, one draw part and one vertical start), without supplying
any future native budget or event schedule. Queue entry fixtures are reconstructed
only from reference mutations before each loop's first REP. Five runner checks
cover suspension/resumption, zero-count REP, string underflow and guest returns.

This is execution within copy loops, not whole-game clock parity. Each loop starts
from a declared initial CPU/queue/VGA state. Cursor helpers, sprite drawing (VGA
A112 selected by DS:2086), other resident graphics operations, IRQ guest execution
and continuous animation/startup integration remain open. The live build is still
unchanged and strict timing remains 614/984. The next graphics layer should use
the same generated work runner rather than recorded per-row cycle budgets.


## Indexed sprites, masks and cursor ownership

`trace-core-sprite-b` / `nature-sprite-work-b` passes its same-DLL control and
preserves all 39,543 resource-route instruction observations. `sprite-work-check-b`
accepts all 123 draws: 81 indexed sprites and 42 colourised masks (including the
cursor planes). Generated outputs match 235,982 intrinsic instructions and 26,429
pixel writes. All 122 nonempty drawing loops match 2,697 CPU/queue/VGA samples and
49 independently generated refills. Ninety-one focused checks cover modes, colour
masking, clipping, odd/even widths, source padding and partial shared writes.
One clipped-empty call has no inner clock interval. No IRQ-containing calls occur
in this component route. Cursor helpers were excluded from that inner-loop proof.

`cursor-work.js` reconstructs resident 8955 prepare, 857A hide and 8822 restore.
`trace-core-cursor-a` observes nested helper calls without guest writes;
`cursor-control-comparison-a.json` confirms equal clocks, frames and audio.
`cursor-work-check-a` accepts all 849 helpers (415 prepare, 420 restore, 14 hide),
9,400 ordered intrinsic instructions and all 42 observed words at entry/return.
Nested execution includes 56 copies/masks, 59,668 intrinsic graphics instructions
and 14,336 writes. Child state is generated, never injected from observed results.
Sixteen focused checks cover negative/positive nesting, deferred movement and
strict rectangle overlap. At this stage graphics buffers and REP splits remain
per-draw fixtures, and handle-address work is omitted from the intrinsic proof.

`graphics-work.js` now composes these helpers with shared indexed surfaces,
resident handle queries, dispatch wrappers and the common work runner. Its
complete-root CPU/queue/pixel comparison is the next verification stage. These
modules remain unbundled until continuous animation integration is verified.


Complete cursor-root composition now passes `cursor-clock-check-b`: all 672 roots,
849 nested helpers, 56 graphics calls, 69,572 instructions and 10,976 string
iterations. All 2,650 CPU/queue/VGA clock samples and 168 source/destination pixel
comparisons match. Eleven refills generate two start latches and two panning
latches. There are no IRQ-containing roots on this route, so no roots were skipped.
Each root starts with one CPU/queue/cursor fixture and, when drawing occurs, one
screen/backup pixel pair. Subsequent nested calls share both buffers and clock;
reference later pixels, clocks and REP splits are comparisons only. Shape bytes,
resident handle words and row tables are explicit inputs. `graphics-work.js`
includes resident dispatch wrappers and 6628 handle-query instruction execution.
The same-DLL control is `cursor-clock-control-comparison-a.json`; all 39,543
resource-route events also equal the independent IRQ capture. Whole-animation
execution, startup, IRQ guest code and live scanout are still separate work.


`rect-fill-work.js` now implements resident A034 clipping and copy/AND/OR/XOR
fills, inverted ink, odd widths and budget-split REP STOSW. `work-runner.js`
executes both REP MOVSW and STOSW; `graphics-work.js` exposes fills on the same
indexed destination and cursor state. `trace-core-fill-a` / `nature-fill-work-a`
passes `fill-control-comparison-a.json` (same frames, clocks, audio). The resource
instruction route still matches the independent IRQ capture.

`fill-work-check-a` accepts all 174 captured sprite/mask/fill calls, 249,138
intrinsic instructions and 65,950 writes. This adds 51 fills, 13,156 instructions
and 39,521 writes to the earlier sprite proof. All 172 uninterrupted nonempty
loops match 4,926 CPU/queue/VGA samples with 51 refills. One IRQ-containing fill
is excluded from the clock comparison (its intrinsic work/pixels still compare),
and one fully clipped sprite has no draw loop. All 129 focused checks pass,
including eight fill modes, odd/even widths, clipping and immediate shared writes.
`cursor-clock-check-b` remains accepted after the runner gained REP STOSW support.

Next composition work is the resident animation support layer: clip push/pop
(7DB6 and its counterpart), clear wrapper 7F08, rectangle offset 8242,
intersection 83B4, empty 7EE6, union, and near copy/fill (099A for fill).
Main shape-header calls already map to generated 6628 work; slot draws dispatch
through 8272 to A112. Main C7FB/CA2F display/background calls use generated 7E32
surface copies. Once these wrappers are composed, full frames can use one clock
and shared pixels, followed by IRQ guest execution and continuous startup/scene
integration. All current modules remain unbundled; the live build is unchanged.


## Geometry helpers and complete animation frames

`geometry-work.js` reconstructs resident offset 8242, intersection 83B4, empty
7EE6, union 84FA, local point 81F0, clip save/restore 7DB6/7E1C, clear wrapper
7F08, near copy 096E and near fill 099A. Clipping retains an explicit saved
rectangle stack, signed word comparisons and zeroing on empty intersection.
Near transfers retain alignment, overlap, word/byte REP and immediate partial
writes. `work-runner.js` now executes REP byte transfers as well as words.

`trace-core-geometry-a` / `nature-geometry-work-a` passes its same-DLL control.
`geometry-work-check-c` accepts all 822 calls, 22,265 intrinsic instructions and
outputs, plus 117 focused checks. Complete helper execution matches 1,729
CPU/queue/VGA samples across 770 calls, including six refills. The clock scope
excludes 51 clear wrappers pending pixel-callee composition and one helper with
an IRQ; their intrinsic outputs/work still compare. The 29 clip pushes compose
their point/intersection callees without resetting the clock. Models are loaded
from captured source bytes, and reports hash those exact evaluated bytes.

`animation-graphics-work.js` joins main frame/scene work, geometry, cursor,
shape queries, copies and sprites on mutable indexed memory. All headers, pixel
surfaces and shape data come from the current memory store. The caption action
initially named palette handle DS:5270 and shape ordinal 10. That interpretation
was later corrected by actual resource-call arguments: shape ordinal 3, mode 10.
See the complete caption execution evidence below; the original analysis is
preserved in frame-caption-inventory-a.json.
Complete instruction comparison also exposed reversed intersection operands at
main CB7B; both it and the similarly arranged CC94 call now follow the native
argument order. Symmetric rectangle results had concealed that path difference.

`trace-core-frame-a` / `nature-frame-work-c` captures complete C78A calls, initial
and final 0xB0000-byte memory images, all guest instruction addresses and clock
samples. Initial capture attempts `nature-frame-work-a/b` failed because their
file/folder names collided with ordinary screenshots/frames.jsonl; both attempts
are preserved, and the observer now uses frame-work/ and frame-work.jsonl.
`frame-control-comparison-a.json` proves equal ordinary clocks, frames and audio;
all 39,543 resource-route observations match the independent IRQ trace.

`frame-work-check-d` accepts 18 of 25 complete frames. From one initial guest
memory/CPU/queue fixture per frame, the model generates exactly 102,585 ordered
instructions, 25,049 string iterations, 1,874 clock samples, 18 refills, two VGA
vertical events and three draw-part events. Operations include 158 cursor calls,
34 copies and 16 sprites. All 716,800 checked bytes per frame match final memory:
all captured RAM except a declared 4 KiB region below the guest stack pointer.
The independent renderer holds locals as values, so incidental stack bytes are
not reconstructed. No later expected memory, instruction path or timing sample
is fed into execution. This is complete eligible-frame execution, not continuous
animation or live scanout parity. `frame-work-check-a` preserves the earlier
operand-order failure. `script-drawing-check-d` still matches all 626,498
interpreter calls and all 726 instance bytes after the descriptor corrections.

Seven frames (0, 1, 5, 6, 7, 11, 16) are explicitly excluded because main 64A4
loads/converts/draws/frees a caption shape. `frame-caption-inventory-a.json`
initially inferred palette handle 26284, shape ordinal 10 and resource 5410.
That inference was wrong: inventory-b and complete execution below establish
shape 3, resource 5403, draw mode 10 for all seven.
E33C temporarily clears the heap callback at [203A]->12/14, locks palette/source,
looks up cached source data, converts through D580/DA63/D5A7 (E03E plus DE10),
allocates/resizes converted storage, restores flags/callback, draws via 8272,
and releases through 64CE/756E. Each frame allocates one converted handle and
uses two near allocations (handle cell and decode scratch); it does not call
heap preparation 6B06 on this route. The source is cached, but conversion and
allocation still occur. These operations must be scheduled from their inputs,
not replaced with the observed caption instruction counts. No frame on this
route needed IRQ exclusion, but IRQ execution remains required for continuous
animation and other routes. Live build SHA and strict 614/984 result are unchanged.

## Complete caption execution and narrower memory exclusions

`resident-resource-work.js` now executes the cached resource directory search,
handle flag queries/locks, catalog pinning, lengths and E33C lifecycle directly
on the shared guest memory. The first prefix comparison exposed reversed shape
and drawing-mode operands: main 64A4 receives shape **3**, mode **10**, palette
handle 26284, whose resource base is 5401. Native `resource.handle` independently
observes SHAP **5403**. `frame-caption-inventory-b.json` corrects the preserved
inventory-a analysis. `frame-caption-prefix-check-a` preserves the resulting
binary-search path failure; the corrected prefix passes.

The `trace-core-frame-c` observer records the actual minimum stack pointer per
frame and at each conversion boundary. The former fixed 4 KiB exclusion included
some main globals, so it was too broad to establish their memory parity.
`frame-caption-prefix-check-c` repeats all 18 complete frames and seven caption
prefixes with the measured exclusion, successfully checking 18,019,236 bytes.
The legacy verifier fallback was narrowed to a declared 1 KiB. New accepted
evidence uses measured bounds, not that fallback.

`nature-frame-stages-a` and its same-DLL control have identical clocks, live
frames and audio (`frame-stages-control-comparison-a.json`). All 39,543 generic
resource events also equal the independent IRQ route. Five additional read-only
snapshots per caption observe prepared conversion, allocation, column decode,
nibble expansion and pre-free memory. Snapshots and instruction paths remain
offline comparisons only.

`resident-near-work.js` implements ordered 003D/0590/001C allocation, splitting,
coalescing, search wrapping and freeing on the same RAM. `resident-heap-work.js`
adds 652A handle allocation, 6E8D/6D47 conventional first fit, 6FD8 coalescing,
unlock, equal-size resize and 64CE/756E freeing. Arena growth, EMS and
size-changing resize remain explicit unsupported paths. Every actual caption
allocation/resize/free in this route now executes through the shared model.

`shape-codec-work.js` supplies E03E column LZ with a cleared 1 KiB circular
dictionary, overlapping references, literal bytes, column traversal and partial
REP writes. DE10 expands packed nibbles backwards in place, keeping transparent
zero and the palette offset. `shape-codec-work-check-b` accepts all seven native
decoder/expansion paths, all decoded non-stack memory and all 2,240 expanded
pixels. Twenty-eight focused checks cover dictionary wrapping, overlapping and
clipped tokens, tiny instruction slices, zero rows, odd/even widths and writes
confined to the expansion extent.

`shape-conversion-work.js` joins D580/DA63 palette preparation, D5A7 sizing/chunks,
D06F/D366 stride, 10A8 multiplication, D2CD codec dispatch, E256 pointer
normalization and D162 palette selection to those memory and pixel operations.
`frame-caption-allocation-check-a` first proved the extended prefix through the
allocation boundary. The full composition then passed `frame-caption-complete-
check-b`: **25/25 complete C78A calls**, **234,629 ordered instructions**,
**68,216 string iterations**, **2,852 exact clock samples**, and **46 refills**.
The same execution generates eight VGA draw-part events, four vertical events,
and one each of handlers 1, 2 and 6. It executes 242 cursor operations, 48 copies
and 30 sprites without per-callee clock resets or expected-memory injection.

Final memory matches across **18,014,924 checked bytes**, with 25,470 changed
bytes. All **35 intermediate snapshots** also match across **25,204,802 checked
bytes**, excluding only each boundary's observed active stack. The final path
hash, every ordered address, each sampled budget/remaining budget/time/VGA state
and a balanced clip stack are checked. `script-drawing-check-e` independently
repeats all 626,498 interpreter/state calls after the caption operand correction.

This closes the captured frame/caption composition gap. Each frame still begins
from its own explicit initial fixture. The next acceptance step is uninterrupted
interpreter/caller execution with guest IRQs, then continuous scene/startup and
live scanout. Other codecs, cold loads and resize paths must be added when those
supported routes reach them. These components remain unbundled, and the live
strict result remains 614/984 with 12 missing displays.

## Complete IRQ0 and chained BIOS execution

`timer_execution_probe.h` adds a read-only complete resident 6447..6487 observer.
It includes the intervening chained BIOS/user-timer stubs, records every guest
instruction's budget/remaining budget/I/O debit/time/IF and VGA state, and saves
before/after 0xB0000-byte RAM with measured stack depth. The fixed BIOS stubs are
captured as identity evidence; the independent model follows their researched
operations rather than executing recorded code or instruction paths.

`trace-core-timer-execution-a` / `nature-timer-execution-a` passes
`timer-execution-control-comparison-a.json`: all ordinary callback clocks, live
frames and audio equal its same-DLL uninstrumented control. All 39,543 generic
resource-route events equal the independent IRQ capture. The observer captures
1,127 complete timer calls, with no partial final call or nested interrupt.

`resident-timer-work.js` performs timer increments, saturating countdowns and
BIOS phase arithmetic on shared RAM. Chained BIOS work follows the pinned
`CB_IRQ0` and `CB_IRET` stubs, including STI/CLI, INT 1C, callback boundaries,
BIOS tick/day rollover, VGA-machine motor timeout and motor-bit clearing. Port
writes and IF changes are explicit actions; the execution host composes the
existing CPU I/O debit, PIC controller and queue rather than charging a fixed
IRQ duration. Hardware delivery and entry/return stack mechanics remain separate.

`timer-execution-check-b` accepts **all 1,127 calls**, **45,430 instructions** and
their per-instruction budgets/times/I/O/IF/VGA values, **1,127 PIC EOI writes**,
**342 BIOS chains**, **684 BIOS callbacks**, and **seven generated refills**.
Two refills service VGA latch events (handlers 2 and 1). All **812,436,874**
non-stack RAM bytes compare, including 4,929 changed bytes. Each call starts
from one initial memory/CPU/queue/controller fixture, with no subsequent resets
or expected-memory injection. The controller initial state is the corresponding
native IRQ0 admission's after-state; later EOI before/after state is comparison
evidence only.

The first verifier attempt (`timer-execution-check-a`) rejected the IRQ stream's
timestamp ordering before executing the model. Three exhausted-instruction
boundaries move PIC time backwards by about 0.0001 ms at a tick rollover. The
corrected verifier preserves controller operation order and pairs the 1,127
IRQ0 admissions with the 1,127 timer entries instead of sorting by time.

`timer-execution-edge-check-a` passes 14 cases: tick low-word carry/full wrap,
BIOS phase carry/high-word ADC wrap, midnight byte wrap, motor timeout/stop,
port/callback/IF behavior and write extent, each under full and three-instruction
slices. The earlier independent timer state/count model agrees on resident work.

Next interrupt work: the 26 sound IRQ7 deliveries target CS:IP 1E5F:4D3C
(physical 2332C on this route), whose handler finishes at 4D76 IRET. It reads
DSP status, either programs the next DMA block via 4D77/4C85/4B40 or stops via
4DDC and INT 15 AX=91F0, then acknowledges the PIC. The vector is installed only
while playing; the first timer fixture still points IRQ7 at the idle IRET stub.
The three mouse IRQ12 deliveries target physical F13E0. Their guest/callback
execution and hardware admission must join the same scheduler before continuous
interpreter/caller and live-build integration. The served build is unchanged.

## Complete sound and mouse guest interrupt execution

The isolated `--device-execution` observer captures IRQ7/IRQ12 from their current
IVT entry through the outer pre-IRET boundary. It records all instruction clocks,
registers/code identity, measured stack depth and before/after RAM. Appended,
read-only sound/mouse exporters provide initial DSP/DMA and mouse event state.
The ordinary pinned checkout is unchanged. `device-execution-control-comparison-b`
and `-c` each pass all 3,116 callback clocks/frames/audio; their resource event
streams also equal the independently accepted IRQ capture.

`sound-interrupt-work.js` composes driver 4D3C, block/DMA setup, DSP polling,
stop/vector restoration, the INT15 hook, resident C559 completion/loop handling,
C66F/E54C notification/unlock and dispatcher command 7 restart. Ports, IF changes,
host callbacks and MOV/POP SS budget credits are explicit actions. Hardware
polling derives from the initial DSP busy counter; observed loop counts are only
comparison data. `sound-execution-check-d` passes all 26 calls: 5,670 ordered
instructions and exact per-instruction CPU/I/O/time/IF/VGA values, 396 port
operations, 93 controller operations, 20 callbacks and 34 stack credits. All
18,741,372 non-stack RAM bytes match (179 changed). Two refills include a PIT
edge while IF is clear; the queued timer is admitted only after sound IRET.

The first sound attempt exposed an initial-queue fixture bug at a millisecond
rollover: exhausted-instruction time from the preceding tick was slightly later
than the following IRQ entry. `initial_queues(..., tick_order=True)` now orders
that boundary by integer tick before fractional time. Subsequent attempts added
the generated PIT edge, IF-disabled controller check and DSP command-completion
IRQ deactivation. Historical failed reports remain intact. Operations at the
final pre-IRET timestamp are excluded because an immediate post-IRET admission
belongs to the next execution boundary.

`mouse-interrupt-work.js` composes the pinned BIOS IRQ12/user-return stubs with
resident 88CA movement handling and the existing shared-memory graphics adapter.
The initial event queue/subscription selects whether to call the guest; no
recorded path is used to choose it. `mouse-execution-check-a` passes all three
calls: 4,547 instructions, 784 string iterations, six PIC outputs, seven host
callbacks, one stack credit and 2,162,492 non-stack RAM bytes (452 changed).
The movement path uses 14 cursor helpers, two copies and two mask sprites. Two
refills service VGA latch/panning events during cursor drawing.

`device-execution-edge-check-a` passes 36 focused checks, each with full and
three-instruction slices: partial/cross/full DMA pages, busy polling, whole/range
loops, disabled loops, positive stop/negative tail behavior, mouse reentrancy,
same-position/button events, hidden/deferred movement and nested drawing.
Only those branch checks stub their already separately verified callees.

These proofs cover guest bodies from one initial state per IRQ. Sound command
bytes and DSP polling/ack state are checked; complete DMA/DSP event scheduling,
PCM generation, hardware entry/return stack/register mechanics, nested IRQs and
continuous interpreter/startup execution still require composition. They do not
close live scanout or full-game parity. The served build remains unchanged.

## Hardware interrupt entry and return

The isolated `--interrupt-entry` probe is appended to pinned `cpu.cpp`, observing
real-mode IRQ0/7/12 entry immediately after the existing `FillFlags()` and the
matching outer IRET. It does not call flag materialization itself or alter CPU
budgets. The first build lacked `pic.h`; that compiler failure is preserved in
`trace-core-interrupt-entry-a`. The corrected `-b` build produces
`nature-interrupt-entry-a`, whose same-DLL control matches all 3,116 callback
clocks, frames and audio. Its generic event stream equals the accepted IRQ route.

`interrupt-entry.js` independently performs 16-bit FLAGS/CS/IP pushes, IF/TF
clearing, vector loading, stack-mask arithmetic and IRET restoration, including
the pinned CPU's AC/ID flag mask behavior. `interrupt-entry-check-a` passes all
**2,312 boundaries** (1,156 entries/returns), with exact complete register/flag/
segment/CPU/time state and stack words. A patterned memory arena also verifies
write extent. Twenty-one focused cases cover odd/wrapping stack offsets, a
nonzero high ESP word, preserved flag bits and extended flag clearing on IRET.
Admission identities and times are independently paired with the IRQ stream.

This closes boundary mechanics as a component. Guest generators still need to
propagate caller register and lazy arithmetic flag values continuously; entry
fixtures cannot substitute for those values during live execution.

## Runtime sound-device port state

`sound-device-work.js` now owns DSP readiness/acknowledgement, command parsing,
DMA address/count byte registers, masks, page/mode and old-format single-cycle
eight-bit PCM setup. Mixer fill/frequency, PIC IRQ changes and DMA event changes
are explicit effects for the shared execution host. It rejects uncomposed active
DMA catch-up/ownership paths instead of silently treating them as no work.

`trace-core-device-execution-d` expands the 32-word hardware snapshot to include
speaker/type/stereo/rate/minimum state and corrects command position to the actual
`dsp.in.pos` used by the parser. Earlier captures recorded `cmd_in_pos`; all
observed before/after commands were idle, so both were zero at those boundaries.
The new same-DLL control again matches clocks, frames and audio.

`sound-device-execution-check-b` passes all 26 IRQ7 calls with the runtime device
module: 5,670 instructions, 396 ports, 93 PIC operations, **832 hardware state
comparisons**, and **12 DMA-end event removals** with exact queue state/time.
The generated effects include 38 IRQ deactivations, 24 inactive/masked mixer
fills and 12 frequency assignments. All previous non-stack RAM checks remain.
`sound-device-edge-check-a` adds 20 checks for busy-counter transitions/wrap,
reset status, one-time acknowledgement, DMA byte/page/mode writes, DSP rates,
short/silent transfer scheduling and SB16 speaker behavior.

Active PCM consumption, mixer scheduling, full continuous device state and live
integration remain open. No fixture path, clock or after-state is runtime input.


## Continuous animation and prepared sound starts

`OriginalAnimationLoopWork` now composes the 4855..48C0 caller with the script
interpreter, wrapper, frame renderer and resident sound API on shared mutable
RAM. Script reads use the current far code pointer, including backwards/16-bit
wrap; display count, drawing globals, sound enable and cue are live views.
Timer reads and interpreter repetitions are generated rather than supplied per
call. The execution harness also derives the frontend I/O accounting reset from
completed VGA scanout followed by the next exhausted-tick boundary (GFX_Events /
GFX_AdvanceFrame); that reset does not refund CPU cycles.

`animation-loop-check-d` passes the complete short span: 20,226 instructions,
22 sparse samples, 12,045 string iterations, four refills, complete path hash,
and 720,078 non-stack RAM bytes (1,140 changed). The long span now executes
57,550 interpreter repetitions and 30 generated IRQ0 calls. Its first mismatch
is instruction 4,872,192, after 4,761 matching sparse address/clock/IF samples.
The independent native IRQ trace identifies IRQ7 at 113725.0 ms immediately
before that sample. Active audio DMA/mixer consumption is not composed, so the
missing interrupt remains a real failure; no expected IRQ timestamp is injected.
Only the complete short span has a full path/hash/final-RAM proof.

The new `resident-sound-work.js` implements cached preparation, pointer-specific
status and stop selection, digital start and E5E2's public wrapper. It composes
the existing resource and sound driver generators, with pause (D0), dispatcher
commands 3/5, callback unlocking, vector replacement and caller IF preservation.
Known non-auto-init DSP transfers can replace a paused transfer. DSP auto-init
ownership is captured separately from the DMA controller's auto-init bit.
Unprepared digital decoding/resampling, cold resources, active music/speaker
stops and music/speaker starts remain explicit unsupported paths.

`sound-start-check-c` passes both native prepared SND 10048 calls (idle start and
replacement): 2,205 ordered instructions, 71 port operations, five PIC operations,
three exact DMA-event removals, one stack-segment credit, 66 hardware fields and
1,441,616 checked non-stack RAM bytes (17 changed). The targeted observer matches
all 3,116 same-DLL control callbacks in clocks, frames and audio. The first
unfiltered observer attempt exceeded its 32,768-instruction capacity on another
sound call; it is preserved as a failed diagnostic. The new RESOURCE_ID filter
makes this proof explicitly about 10048, not all sound preparation.

Forty focused resident-sound branch/flag checks pass under budgets 3 and 10,000.
Thirty device checks cover previous cases plus pause, replacement and explicit
unknown-auto-init rejection. The 26 IRQ7 cases retain their previous full pass in
`sound-device-execution-check-c`; the later flag-read placement refinement is
covered by `sound-start-check-c` and the focused flag tests. Complete frame
regression `frame-caption-complete-check-c` still passes all 25 frames after the
shared-state adapter change.

The live build remains unchanged: strict 614/984 callbacks, 12 missing displays.
These results remain offline component evidence. DMA sample consumption, mixer
phase/output, caller register/lazy-flag propagation, cold resource/startup paths
and live integration remain required before completion.


## Continuous animation and prepared sound starts

The new `animation-loop-work.js` joins the 4855..48C0 caller, script interpreter,
wrapper, renderer and resident sound API on one mutable RAM state. Script bytes
follow the current far pointer (including backwards/16-bit wrap); drawing globals,
display count, sound enable and cue remain live. Interpreter repetitions and timer
reads are generated. The execution harness derives frontend I/O accounting resets
from completed VGA scanout followed by the next exhausted-tick boundary, following
GFX_Events / GFX_AdvanceFrame. Resets do not refund CPU cycles.

`animation-loop-check-d` passes the complete short span: 20,226 instructions,
22 sparse samples, 12,045 string iterations, four refills, complete path hash,
and 720,078 non-stack RAM bytes (1,140 changed). The long span now generates
57,550 interpreter repetitions and 30 IRQ0 calls. It fails at instruction
4,872,192 after 4,761 matching sparse address/clock/IF samples. The independent
native IRQ trace places IRQ7 at 113725.0 ms just before that sample. Active
DMA/mixer consumption remains uncomposed, so the missing interrupt is retained
as a real failure. No expected IRQ timestamp is injected. Only the complete
short span has full path/hash/final-RAM proof.

`resident-sound-work.js` implements cached preparation, pointer-specific status
and stop selection, digital start and public E5E2. It composes the resource and
sound-driver generators. Driver additions cover pause (D0), dispatcher commands
3/5, completion unlocking, vector replacement and caller IF preservation. DSP
auto-init ownership is captured separately from the DMA controller auto-init bit.
Unprepared digital decode/resampling, cold resources, active music/speaker stops
and music/speaker starts remain explicit unsupported paths.

`sound-start-check-c` passes both prepared SND 10048 calls: 2,205 instructions,
71 port operations, five PIC operations, three exact DMA-event removals, one
stack-segment credit, 66 hardware fields and 1,441,616 non-stack RAM bytes
(17 changed). Same-DLL controls match all 3,116 callbacks in clocks, frames and
audio. The first unfiltered sound-start capture exceeded its instruction capacity
on another sound; it remains a failed diagnostic. The RESOURCE_ID filter makes
the accepted fixture explicitly about 10048, not all sound preparation.

Forty resident sound/flag branch checks and thirty DSP/DMA edge checks pass.
`sound-device-execution-check-c` retains all 26 native IRQ7 passes. The final
flag-read placement refinement is covered by the sound-start and branch proofs.
`frame-caption-complete-check-c` retains all 25 full frame passes after changing
the shared-state adapter. The live build is unchanged: strict 614/984 callbacks,
12 missing displays. DMA consumption, mixer phase/output, caller registers/lazy
flags, remaining resources/startup and live integration remain open.


Final reruns for this increment: `sound-start-check-d` passes both starts;
`sound-device-execution-check-e` passes all 26 sound IRQs; and
`animation-loop-check-f` retains the complete short-loop pass and the same first
missing-DMA mismatch in the long loop. These reports identify the final model
hashes. `sound-device-edge-check-c` passes 31 checks, including establishing
non-auto-init ownership when a single-cycle command is processed. Shared script
word operands now wrap the effective offset once before reading the two physically
adjacent bytes, matching the reference CPU's word load at offset FFFF.
`script-shared-code-check-a` passes five backwards-branch/word-boundary cases.
Completion gate `completion-gate-ad.json` remains false; no integrated/full-game
parity claim or live-build promotion is made.


## DMA sample output and generated mixer cadence

`audio_dma_probe.h` captures GenerateDMASound entry/exit, 1,024 source bytes,
processed PCM, 32 DSP/DMA fields, eight transfer fields, 16 mixer-channel fields
and the actual signed-32-bit contribution to the native stereo mixer buffer.
The isolated mixer exporter reads state/work without mutation. The first build
failed for a missing cpu.h declaration; `trace-core-audio-dma-b` fixed that.
Its traced/untraced control matches all 3,116 callbacks in clocks, frames and audio.

`audio-dma-check-b` passes all **6,011** observed calls: **62,809 PCM bytes**,
**290,096 stereo mixer frames**, **192,352 hardware**, **48,088 transfer** and
**96,176 channel-state comparisons**. All 26 terminal counts, event removals and
IRQ7 completion times match. Each call starts from its own initial fixture; this
report does not establish continuous cadence. The observed route has no fade-in
calls. Twenty-six separate source-derived edge checks cover interpolation, signed
samples, volume, silence, fade, DMA wrapping, terminal/queued transfers, phase,
frontend buffer consumption and fractional tick arithmetic.

Runtime `sound-dma-work.js` now consumes shared guest PCM using the DMA address,
page/count and DSP ownership state, handles terminal masking, optional startup
fade, and emits IRQ/event effects. `mixer-channel-work.js` reproduces the integer
sample phase, interpolation and volume contribution, with silence decay and
request sizing. `mixer-clock-work.js` composes millisecond mixing, fractional
FillUp and ordinary unthrottled frontend audio consumption (min_needed=0).
Unsupported formats/modes remain explicit errors.

`trace-core-animation-loop-c` adds initial DMA/channel/mixer/frontend state to
the continuous-loop fixture. The frontend is rebuilt from the pinned source plus
the existing deterministic capture patch, now factored as `instrument_frontend`;
the builder verifies that it matches the prepared checkout before adding read-only
state access. The frame-count pointer only observes the static handoff counter.
Its same-DLL control again matches clocks, frames and audio.

`animation-loop-check-i` generates **1,633 DMA calls / 18,209 PCM bytes**, **99 IRQ0**
and **six IRQ7** admissions from the initial state, shared RAM, millisecond mixer
cadence and generated VGA frame handoffs. All **105 vector/timestamp admissions**
match the independent native IRQ trace; expected times are comparison data only.
The short loop retains its complete 20,226-instruction/hash/non-stack-RAM pass.
The long loop reaches **16,360,637 instructions**, **193,269 interpreter calls**
and **15,988 matching sparse clock/address/IF samples**, then stops explicitly at
`activity-overlay` after main 4EC8. It remains a failing incomplete span: only
full completion can establish its full path hash and final memory parity.

The next callee is main **4E15**, the previously documented question-icon removal
hook: saved backdrop manipulation via main 70B6 / resident 841E, encoded overlay2
**198A(attribute,1,0)**, then backdrop update and DS5296 suppression. That callback,
remaining resource/overlay paths, complete interrupt/caller state, final host audio
clipping/resampling and live integration remain open. Live strict parity remains
614/984 with 12 missing displays. No prerecorded path/IRQ/sample schedule is used
by the runtime models. Completion remains unproven.

`audio-dma-check-c` additionally verifies all 26 generated DMA-end event-removal
timestamps against the independently captured PIC queue, retaining every PCM,
output and state comparison. The final completion gate is `completion-gate-af`.
