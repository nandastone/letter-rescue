# Resource startup and deterministic cold boots

## Purpose and scope

The money-game payment dependency needs resource state generated from startup.
Later native heap snapshots remain offline comparisons. They cannot initialize
the playable game. This work implements the initial arena headers and provides
repeatable reference captures at those boundaries. It does not deliver the
payment fix or establish complete resource lifetimes.

`treehouse-demo/resource-startup.js` implements two semantic operations:

- Initialize the near heap from the executable's original stack pointer and
  runtime stack bias. Both values are extracted from the pinned executable,
  rather than copied from a RAM snapshot. Alignment and the two initial headers
  produce a zero-length free block followed by the terminator.
- Initialize the conventional resource arena from a DOS allocation result:
  a 22-byte control record, one free block and a six-byte terminator. The
  platform allocation result is still an explicit input. The model records
  this arena as open to growth; it does not pretend it is the final arena.

`resource-startup-check-b/report.json` passes all four checks: near state,
conventional arena free chain, complete control record, and invalid extents.
The two native startup fixtures have independent byte hashes. No instruction
counts or register equality are acceptance criteria.

## Capturing initialization before the first frame

`retro_load_game` runs the original initialization before returning its first
frame. Installing an observer after this call misses both arena constructors.
The adapter now has an optional `before_load` hook, called after core
initialization while its worker is stopped. Its default is a no-op.
`capture_resource_startup.py` uses it to install existing read-only observers;
no core rebuild or game patch is involved.

Earlier heap/near A and heap B captures failed because their snapshots were
absent. Their reports remain failed. Capture C reaches the intended boundaries,
but comparisons between independent cold boots exposed the clock issue below.

## Cold-boot clock correction

The old reference ZIP runs `time 12:00:00`. The pinned core's DOS Set System
Time implementation explicitly does not set nonzero times. Each new boot
therefore retains its host-derived BIOS time. In the first comparison, images,
audio and callback timing matched while eleven game-memory bytes and two BIOS
timer bytes differed. `resource-startup-control-proof-a.json` remains failed;
those differences are not masked or described as an observer pass.

`prepare_startup_reference.py` creates a separate `reference-startup-v2.zip`.
It replaces the unsupported time command with a 13-byte DOS launcher that
uses the supported BIOS Set System Time service to set CX:DX to zero, then
exits before TREEHSE.EXE starts. This is a fixed test-platform clock, not a
gameplay seed adjustment. The existing reference ZIP and its save states are
unchanged. All game-file bytes in the new ZIP match the old reference.

New reference SHA-256:
`f7b138392b28d46275e5cc26e291fbe3d18a2b26d98a3631b63c1a7eff26df91`.
Its provenance and launcher bytes are in
`testing/output/treehouse/source/reference-startup-v2.json`.
The first archive preparation reused a mutable ZIP-entry descriptor and
failed its CRC check. The partial v1 output is retained with a failure report;
capture tools use v2 only.

Heap and near captures D each match plain control D in all ordinary images,
audio, RAM, input actions and callback timeline. A later independently booted
control E repeats the result. Both reports pass all 209 checks:

- `resource-startup-control-proof-b.json`
- `resource-startup-control-proof-c.json`

The two observer event timelines also agree. Diagnostic heap snapshots remain
offline inputs to the verifier. A label identifies an observed address; the
early `game.main` address is also briefly used by the clock launcher, before
the original executable is loaded. Arena comparisons use only their paired
initialization boundaries.

## Remaining integration

The original conventional arena initially contains only five paragraphs; the
first resource allocation still requires growth. Near-heap allocation also
grows its initially empty block. Generate those growth operations and startup
resource requests before connecting this state to the existing semantic
shape/sound loaders and payment calculation. The DOS allocation result itself
must also come from the platform model rather than a captured address.

The playable build remains `d2ecc31d6a0a`, confirmed by a fresh rebuild. The
current complete money-loss replay still diverges at step-10, and all existing
strict presentation/audio failures remain open.

## Growth and the first complete allocation

`OriginalNearHeap.grow` now expands its last block using the original growth
quantum, falls back to paragraph alignment when necessary, and preserves state
when the platform cannot provide enough space. An explicit growth policy lets
ordinary `allocate` drive expansion and retry. The initial C-runtime growth
uses a 1,024-byte quantum, while the later resource phase uses 8,192 bytes;
this policy is an explicit input until the startup callers are generated.

`OriginalResourceStartup.growArena` implements conventional arena extension,
including a partial final extension and closing an exhausted arena. It
preserves existing resources and replaces the old terminator with the new
free block. `OriginalMemory` can connect this provider to `OriginalHeap`:
ordinary first-fit allocation tries packing, requests growth, then retries
the search. Cache eviction and EMS are still unsupported paths.

`resource-growth-check-b` matches all two near-growth calls and seven
conventional-growth calls in the original startup recording. Complete allocator
state, existing payload hashes, and returned conventional byte counts match.
Six focused checks cover automatic allocation retry, paragraph fallback,
failure preservation, partial growth and closed arenas. Each growth comparison
starts with its own offline fixture; it is not a continuous startup replay.

`resource-startup-allocation-a` generates the first complete 1,527-byte handle
allocation from the initial far-arena constructor. Failed-fit packing, arena
growth, coalescing, allocation and handle ownership all match. The returned
handle and complete near/far state pass four checks. The platform allocation,
its available DOS paragraphs and current near state remain explicit offline
inputs; newly allocated uninitialized payload bytes are not allocator output.
The earlier handle/raw captures filtered on 1,528 bytes and found no call.
Those failures are retained; the observed first request is 1,527 bytes.

`resource-growth-control-proof-a.json` compares both growth captures and the
complete allocation capture against the later plain cold-boot control. All
313 checks pass for ordinary images, audio, RAM, inputs, callbacks and event
timelines shared by the observers. No RAM differences are masked.

Regressions on these source versions:

- `resource-growth-heap-a`: all 52 heap states and five boundary checks pass,
  with instruction-work comparison disabled.
- `resource-growth-lifetimes-a`: 104 state checkpoints, 79 generated shapes,
  twelve scene phases, 2,399 generated sounds and four focused checks pass.
  The remaining 159 allocation requests and 43 frees are observed inputs.
- `resource-growth-board-load-a`: the complete board background load still
  matches with instruction-work modules absent.
- `resource-growth-shapes-a`: nine ownership/layout checks and all 2,337
  shape headers pass without instruction-work modules.

Growth is now connected to the resource allocator. Remaining integration is
to generate DOS allocation/availability, startup resource requests, and later
activity resource lifetimes. The playable build is unchanged; a fresh rebuild
still produces `d2ecc31d6a0a`. This is not a delivered payment fix.

## Generated DOS startup and first embedded font load

`dos-memory.js` now generates the conventional memory map from the pinned
DOSBox source constants. Process/environment allocation, ownership, resize,
coalescing and the resource arena's rejected low-memory allocation retries
produce the original arena location without reading a captured address.
`dos-resource-startup-b` passes 26 native comparisons and five focused checks.
DOS state advances continuously through seven growth calls; later resource
arena inputs in that particular verifier still come from offline fixtures.

`OriginalResourceStartup.memory` generates the initial near allocations from
the platform environment strings, the executable's stack parameters, the
32-byte CONFIG.DAT file and the VGA descriptor's 200 scanlines. It derives
the environment pointer table and the change from the initial 1,024-byte
growth quantum to the later 8,192-byte quantum. `dos-startup-allocation-b`
passes six comparisons through the first FONT 0 allocation. No native state,
addresses, available capacities or recorded allocation requests initialize
that check.

The semantic source loader now supports the original embedded-resource flag
and static catalog lock. It copies embedded bytes into independently owned
source storage and retains the normal cache/handle behavior. The font payload
comes from the pinned executable's built-in directory. `dos-startup-font-b`
passes eight native-boundary/operation checks, including the full payload hash,
and three focused cache/reload/no-instruction-observer checks. This runs
continuously from generated startup through the first font source load.

The first font verifier incorrectly kept mutable handle references while its
later focused discard check ran; `dos-startup-font-a` records that failure.
The corrected verifier copies the boundary result before subsequent checks.
No native difference is ignored. `resource-font-control-proof-a.json` passes
209 checks comparing the new observer's ordinary images, audio, RAM and
callback timeline against the plain original control and shared event labels
against the earlier initialization observer.

Current component regressions include all nine startup growth calls and six
focused checks (`dos-resource-growth-b`), the complete board background load
without work modules (`dos-resource-board-load-b`), and nine ownership/layout
checks with all 2,337 shape headers (`dos-resource-shapes-a`).

Remaining startup work begins after this first source load: font activation,
the cursor, archive catalogs and subsequent resources. Complete activity
lifetimes and the payment formula still need connection to the playable
runtime. The second font load in the capture is not covered by the first-font
comparison. Full-game parity remains false and the served build is unchanged.

## Font activation and initial cursor ownership

`font-loading.js` converts the embedded font into original VGA glyph bytes.
`OriginalMemory.detachHandle` and `attachHandle` implement the allocation
transfer used by the original: the converted block replaces the source block
under the existing cached handle, retains its ownership flags, and releases
the temporary handle. Activation preserves the original converted payload,
free-block layout, handle flags, near state and DOS allocation state.

`cursor-loading.js` allocates the 16-by-16 saved background using pixel packing
from the executable's mode descriptor. It loads the embedded cursor, generates
its image and inverted mask, promotes and locks those converted resources in
the original order, and restores the source flags. The source offset is an
outcome of these allocations; no recorded offset initializes it.

`startup-activation-d` passes all 18 boundary comparisons and three focused
checks. This is continuous generation from executable/configuration/platform
inputs through the first font activation and the first cursor activation.
Active payload hashes, complete allocator metadata, near state and DOS
ownership match at all six boundaries. Later cursor changes, catalog loading
and activity resources are not covered by this startup check.

The first verifier attempt read pixel packing from the surface descriptor
instead of the separate format descriptor; attempt C then mutated a shared
comparison object. Both failed attempts are retained with failure records.
Neither required changing expected native output. The three new captures
match the plain original boot in all 313 control checks
(`resource-activation-control-proof-b.json`).

The shape inventory and board-background load still pass on the new memory
module. The fresh build `activation-build-a` remains byte-identical to the
served `d2ecc31d6a0a`. Next: generate archive/catalog loading and subsequent
startup/activity resource requests, then use their live state for payment
preparation. Money-game and strict presentation/audio failures remain open.

## Archive opens and continuous first-catalog startup

`catalog-loading.js` parses the original directory and resource tables,
checks payload checksums, allocates directory storage, links the catalog,
and preloads entries carrying the original preload flag. Source sizes and
preload order derive from DAT bytes. `catalog-loading-b` passes all 49
comparisons for seven original opens: th, ibm_snd, midisnd, voices, digisnd,
th64 and modules. The digital-sound archive preloads SND 1008. Each of these
seven component comparisons starts from its own allocator/file-list fixture;
platform file handles, canonical filenames and volume labels remain explicit
inputs in that verifier. Attempt A retained the default DOS owner in its
fixture adapter and failed the first resize ownership check. The corrected
adapter uses the owner from the input DOS state; all native expectations are
unchanged.

The gap between cursor activation and the first catalog is a saved screen
rectangle. Its bounds `(45,60,92,154)` come from the pinned executable, and
`saved-surface.js` derives the near descriptor/row table and raw pixel storage
from those bounds and pixel packing. This joins the first th.dat open to the
existing continuously generated startup. `startup-catalog-b` passes all 28
boundary comparisons and three focused checks without captured initial state.
Attempt A's Python-to-JavaScript filename escaping caused two metadata
failures; passing the filename as structured input fixed the verifier.

The new catalog's initialized filename/volume/file-list fields and complete
directory entries are compared separately from allocator state. Uninitialized
string slack is excluded from its payload hash; active font, cursor and
preloaded resource payload hashes remain compared. Plain-original control
comparison does not exclude any RAM: `resource-catalog-control-proof-a.json`
passes all 209 ordinary-output and shared-event checks.

The next interval replaces the cursor with CURS 1, activates FONT 1 and owns
a direct resource copy before the sound archive opens. Those intervening
calls, later archive opens and activity resources still need joining into
the continuously generated sequence. No captured call sequence is installed
in the runtime. The fresh `catalog-build-a` output remains identical to
`d2ecc31d6a0a`; the playable payment discrepancy remains open.

## Continuous seven-archive startup module

`OriginalStartupResources.create` now owns the complete resource sequence
through the seventh startup archive for the pinned VGA/Sound Blaster profile.
It uses the original executable/configuration parameters and DAT contents:
initial font/cursor, saved screen rectangle, th catalog, CURS 1 and FONT 1,
the free-memory query, the direct sound-configuration copy, and the remaining
six catalogs. Archive filenames are extracted from the executable's launch
callers. Native boundaries are observer outputs only; no captured allocator
or allocation schedule initializes the module.

The first continuous comparison exposed a missing operation: resident 5C78
grows the arena to the DOS limit, exhausts eligible discardable cache entries,
and packs it before reporting available memory. `OriginalMemory.available`
now implements that maximal query. Search requests saturate at the original
20-bit limit. This API does not implement arbitrary partial cache eviction.
The failed `startup-sound-archives-a` report remains recorded, rather than
patching resource addresses to its expected values.

Source payload ownership is shared by loaders using the same memory object,
so replacing the cursor and reusing old handle slots cannot retain stale
bytes from another catalog. Discard removes resident bytes but preserves
the handle/cache entry. Direct loading can now run without instruction-work
modules; its normal accounting observer remains available for earlier tools.

`startup-sound-archives-e` passes 88 native boundary comparisons and six
focused checks. It covers all fourteen archive entry/return boundaries in one
generated sequence, plus the initial font/cursor boundaries. The extra focused
checks cover eligible cache removal, locked-resource preservation and search
size saturation. As before, catalog initialized fields/directories are
compared separately from uninitialized string slack. Raw pixel and direct-copy
payload bytes are outside this allocator comparison.

Current regression evidence:

- `startup-chain-heap-a`: 52 native heap cases and five focused checks.
- `startup-chain-lifetimes-a`: 104 checkpoints, 79 shapes, twelve scene phases,
  2,399 sound loads and four focused checks. Its initial fixture and remaining
  observed requests are still explicit; this is not whole-game generation.
- `startup-chain-shapes-a`: all 2,337 headers and nine ownership/layout checks.
- `startup-chain-board-load-a`: complete board-background resource ownership.

The fresh `startup-chain-build-a` remains byte-identical to the served game.
Next is generating the startup animation and subsequent activity lifetimes
from the returned resource state, then connecting payment preparation to its
live cursor source. Full gameplay, presentation and audio parity remain open.
