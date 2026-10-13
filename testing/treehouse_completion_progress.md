# Completion work: verified playable update

The playable build includes all original activities and the source-backed
completion work below. **Exhaustive full-clone parity is not established.**
The verification counts describe the captured scenarios, not every possible play
sequence, timing alignment, or audio waveform.

Live file: `output/treehouse/playable/index.html`.
SHA-256: `27689144aa93085bc22f6e2b282b0563f08960659bfeb2b489bf307ac1804413`.
Source: pinned DOS 1.1 ZIP
`53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`.

## Payment random sequence and complete board journeys

Restored the random choice consumed by original payments. All 49 regression
suites and 183 environment states pass on the delivered build. A fresh money
loss now has explicit prize/restart/reload coverage. The full native chip game
matches all 49 state/random checkpoints through its 35/58 ending; 48 of 49
images match. One partially cleared trade highlight is still missing. A full
native money-loss capture exposes a later unused coin-preparation random-state
quirk that remains open. Both failed comparisons are retained in completion
verification; no checkpoints were removed. See `treehouse_board_payment_rng.md`
and `treehouse_board_chip_journey.md`.

## Digital sound level correction

Removed the extra 0.4 gain on digital sound. The rendered browser Bass A attack
now measures 99.9898% of the native reference level (previously 39.9959%), with
correlation 0.999972. All 47 regression suites and 183 environment reference
states pass on the delivered build. Exact waveform and strict presentation
timing parity remain open. See `treehouse_audio_output_fix.md` and
`output/treehouse/audio-output-delivery-a/report.json`.

## Maze exit and persistence correction

Readable victory controls now share the native canvas action handler, preserving
song interruption, control flash and the climb-out animation. Every exit saves
the finalized song list/history immediately. Five ordinary-input exit/reload
routes pass 41 checks. All 46 regression suites and 183 environment reference
states pass on the delivered build. Strict nature timing remains unresolved.
See `treehouse_maze_exit_fix.md` and `output/treehouse/maze-exit-delivery-a/report.json`.

## Added and corrected

- Character needs, feeding, naps, alternate poses, original authored reactions,
  room object dragging, falls, hatching and departures.
- Bird, worm, squirrel, nest and spider events; spoken calendar/time/status;
  automatic room events and cloud movement.
- Human and robot prize selection, presentation, transfers, persistent room
  objects and the robot's session-only telescope shelf.
- Maze introduction, frog guidance, footsteps, note drops, sliding chooser,
  wrong guesses, victory, replay, tutorial interruption and song history.
- Song contents, title entry, held-note writing/glissando, palette/note audition,
  both terminal pages, erase-all, print sheets and original songbook interchange.
- Nature question/guess/turn animations, selective question removal, hidden
  animals, second reveal, post-win inspection and candidate elimination colors.
- Original F2 preferences with readable controls. Sound, printing and maze level
  settings are connected to play. Printer and speed preference words are retained
  for DOS compatibility; browser printing uses the native score preview.
- STATUS.DAT import/export and browser persistence of preferences, collage,
  theater arrangements, board settings, maze history and room objects. SONGS.DAT
  remains a separate file, as in the original. Imported unknown bytes, inactive
  slots, old handles and trailing bytes survive untouched round trips.
- Shared original LCG, Sound Blaster rate rounding, a single digital channel,
  finite auditions, forced piano/editor note release and whole-sample effect loops.

## Latest completion pass

- All original contextual help layouts, dedication, sound/version overlays, native
  keyboard pointer controls, and signed/offscreen room-object save coordinates.
- Native chalk erase dialog with blank calendar unroll/reroll and balloon avoidance.
  Nature single/both-scene confirmations, per-animal bursts, preserved facts and printing.
- Board debit hands/paid chips, zero-balance losses, offer feedback, win presentation,
  target flashes, arrival pauses, interruptible reminders and speech.
- Exact native seeded landing amount/message generation, without spurious Chip coin RNG.
- Native maze category/history/distractor RNG, independent replay/hint timers,
  victory prompts, retained won-song display, frog ascent and departure timing.
- Original reward poses, two actual flight paths, delayed speech and interruption rules.

- Basket clipping and held-pointer worm pickup; chute transfers and outdoor discard paths.
- Native nature reminder cycles, question reveal cues, robot thinking sound and seeded deal.
- Whole-buffer sound loops with original owner stops for calendar, roller, food, departures,
  nature turns and telescope replay; instrument effect suppression during auditions.
- Save/import cancellation of unfinished collage erasure and current balloon position.

## Exterior, navigation and final interaction pass

- All eight title credit panels; returning to the yard preserves the chosen friend.
  Saved outdoor objects stay hidden and inactive on the fresh character chooser.
- Cloud, sun, pond cycle, birdhouse, window conversations and squirrel hollow,
  including three nut flights, both squirrels and the sign's original voice.
- Naps continue while visiting the yard/hollow; natural waking restores the indoor
  pillow. Yard events continue during sleep, while indoor events remain indoors.
- Original ring/bubble room transfers, theater curtain backing and foreground
  objects, plus both telescope approach poses and return walks.
- Robot telescope shelf automatically celebrates earned prizes and replays with
  all four original cues; empty shelves retain their silent first pose.
- Owner-specific sound completion: retain final frames during finite sound waits,
  consume a skip click, and preserve original immediate-stop exceptions.
- Nature definitions before the first roll and panel dismissal; pitched candidate
  removal/restoration, newly eliminated candidates only, die lead-in and invalid
  input guidance. Turn entry uses the original silent first pose. The complete
  robot question/answer/elimination sequence matches original frames in order.
- Fresh and reloaded desktop/touch journeys through visible controls. Reading
  text size now survives reload alongside saved creations.

## Verification on this exact build

All 37 regression suites pass: **764 behavioral checks, 288 exact complete frames, and 42
exact regions**, with no browser exceptions. They include 30 generated nature
games, 60 board games (484 turns), and 40 maze games.

Separate sequence checks retain 73/73 entrance frame membership matches and
38/38 ordered theater display changes and 18/18 ordered basket/bird states. The 22 selected complete board stages
also match in original order across Money, Chips and robot victory. The room environment check matches all
183 sampled states (spider 162, nest 15, chirp 6) against complete native RGB
frames. Its cursor visibility alternatives are explicit in the report.

Additional complete RGB sequence comparisons match **540/540** distinct display
states in original order: room transfers330, yard/hollow78, telescope walks43,
robot shelf50, and full robot nature turn39. These counts are separate from the
complete-frame snapshots above; they are not claims of callback timing equality.

The nature boundary test advances the real question generator to original
display counts 10, 11 and 12 and compares complete frames. All 24 positions of
the maze drawer match completely. Six preferences panel states match their
entire 256Ãƒâ€”109 region. Three print sheets match all 64,000 pixels.

A single original board callback containing a partially redrawn counter is
explicitly excluded from completed-frame acceptance. Its adjacent completed
stages match. No screenshot pixels are used by the game renderer.

Evidence: [completion_verification.json](treehouse/completion_verification.json).
Run `tools/treehouse/verify_all.py` and `verify_environment.py` against a saved
candidate; each needs a new output path. The suite runner checks that the build
hash remains unchanged throughout verification.

Fixtures now explicitly establish the telescope visit mask for its shelf
reference and reset theater storage for fresh-session invalid-sentence cases.
Runtime rendering never consumes captured screenshots. Selected reference
models are read from original RAM; generated gameplay is checked separately.

## Strict timing pass

Faithful reproduction comes first, including redraw delays and intermediate
displays; improvements follow afterward. This supersedes the earlier preference
for faster complete redraws.

The nature turn now preserves fractional sound completion, matching all six
native 31-tick elimination gaps. Its missing eight-tick end-of-turn die flash is
restored from the original cleanup/reminder calls. Telescope sequence matching
is restricted to each actual native input window.

The separate strict check **fails**: 614/984 unshifted callback comparisons match,
and 12 native display changes remain unrepresented. Passing regression suites
does not waive those failures. Original progressive redraws and sub-tick
presentation alignment remain open. Details and red-to-green evidence are in
[timing fidelity](treehouse_timing_fidelity.md).

A subsequent isolated presenter check reproduces all 306 native callbacks during
the question animation, including four mixed old/new displays. It uses generated
browser pixels with native commit-time fixtures. This component is not yet wired
into the live app and does not change its strict result or verification counts.
Read-only tracing also established repeatable snapshot boundaries and verified
identical pixels, clocks and audio with probes enabled and disabled. See
[redraw reconstruction](treehouse_redraw_reconstruction.md).

The next verified increment prepares each animation's complete shape list in
the original order before execution. Both captured constructors match all 30
native load requests; five additional resource-plan checks pass. The original
36 suites and the new resource suite were run against the same immutable
candidate, then that file was promoted and its HTTP-served hash checked.
This does not change the strict 614/984 result. Resource conversion time and
progressive drawing remain open. See [resource timing](treehouse_resource_timing.md).

Snapshot protocol 2 now applies to the shared capture adapter. Two fresh ordinary
captures agree exactly with the established 3,116-callback reference and audio.
The persistent [issue ledger](treehouse/remaining-work.md) records this issue as
closed and the remaining six as active/open. `completion_status.py` fails until
the integrated fidelity work and its evidence are complete.

## Limits of the fidelity claim

The resource work components now reproduce 60 graphics routine calls and all 52
heap-preparation calls in the captured nature sequence. The latter includes 49
resource moves with exact resulting blocks, handles, content hashes and
instruction counts. These components use explicit offline initial-state and
CPU-budget fixtures; they are not integrated into the game yet. No live-build
parity count has changed. The next step is to generate heap state from resource
allocation/release lifetimes before connecting work to the presentation clock.

- Broader ordinary-input sequence coverage beyond the recorded fixtures, including
  additional object flights, maze branches and board transitions.
- Complete global random-call ordering, sound backend timing and native
  waveform comparison. Browser audio gain/resampling are not claimed identical.
- Exhaustive path coverage across long sessions and all supported input sequences.
  Fresh/reloaded desktop and touch journeys are covered by the current suite.

Exact static states and frame membership do not establish timing equality.
The earlier room delivery report retains its previous build and scope.


## Latest resource work checkpoint

The continuous offline model now generates shape, script and sound ownership:
79 shapes, 12 lifecycle phases and 2,399 sound loads agree at all 104 memory
checkpoints. Generated resource inputs match 2,480 entry queries and 2,478 cache
paths. Sound decoding matches all 273 compressed asset outputs; preparation and
copy instruction paths have separate native comparisons. The shared copy model
also preserves all 52 heap-preparation comparisons. Detailed scope and report
names are in [resource timing](treehouse_resource_timing.md).

The composed resident resource model now matches 2,478 generated calls,
including 29 cold loads, across 362,222 instruction entries. The timer model
matches 1,127 IRQs with continuous game-tick/BIOS-phase state. Three resource
calls still use observed interrupt placement in the composition check; the
comparison without those fixtures deliberately remains failing.

These are unbundled components. Other resource callers, drawing/constructor
work, startup state and CPU/PIC scheduling prevent a claim of live timing
parity. The playable SHA and 614/984 strict result remain unchanged.

The new clock queue component matches 766,599 native queue operations from one
initial queue state. Periodic PIT phase matches 1,127 timer events without phase
resets. CPU budgets and event requests still come from an offline trace; guest
execution and interrupt admission must generate them before live timing can
be claimed. These checks do not close TH-002 or TH-003.

CPU budget accounting now covers 343,448 observed normal-core runs and 313,039
callbacks. Continuous PIC state now explains the acknowledgement transfer and
matches all 3,575 controller operations and 1,156 deliveries. The composed
comparison passes all 656,487 CPU/callback budgets. Observed work counts and
requests are still component inputs to this comparison.

The input polling generator separately matches 104,075 completed native polls:
136,233,469 instruction entries, every ordered path hash, return value and input
state. Mouse edges and key latches remain continuous from one initial fixture.
The original DOS keyboard delay and mouse callback trampolines are included.
Mouse callback results, caller work between polls, interrupt execution and live
clock integration remain separate. These unbundled checks do not change the
playable build's strict 614/984 result.

Generated timer/sound wait and nature idle caller paths now match 101,652 native
continuations and 3,754,218 ordered instruction entries. The verifier explicitly
leaves resource lookups, interrupts and caller transitions uncomposed. New gap
observations locate 44,279,929 instructions in the question animation interval,
mostly repeated interpreter deadline checks. Reconstructing that execution loop
against the shared clock is the next integration step; observed loop counts
will not be used as runtime schedules.


The SCR interpreter now matches all 626,498 observed calls and 28,822,581 ordered
intrinsic instructions. Its wrapper matches 626,403 uninterrupted continuations
and 14,706,534 instructions. The drawing layer is being composed to replace the
47 partial instance-memory comparisons. IRQ execution, resident graphics and
shared-clock integration remain open; no component loop counts become runtime
schedules and the live build remains unchanged.


Frame/scene/slot bounds composition now eliminates all partial animation-instance
comparisons: 626,498 calls match all 726 bytes, plus 27,029 ordered drawing
instructions. Caption intersection follows captured input rectangles rather than
expected branch outcomes. Ten focused movement/bounds checks pass. Actual pixel
copy callees and continuous scheduling remain open, so this does not change the
strict integrated result or close TH-002/TH-003.


VGA surface-copy output now matches 123 native calls and 136,442 pixel writes.
The shared work runner/CPU/PIC queue/VGA event clock independently reproduces all
3,305 REP budgets and timestamps for 121 nonempty copy loops, including 12 CPU
refills. Partial writes are visible before completion. Each comparison still
starts from one native initial state; cursor/sprite work and full-game integration
remain open. The live build and its strict 614/984 result are unchanged.


Indexed and colourised-mask sprites match 123 native calls, 235,982 intrinsic
instructions and 26,429 writes. Their 122 nonempty draw loops match all 2,697
CPU/queue/VGA samples, including 49 refills. Cursor helpers now match all 849
calls, all 42 observed state words and 9,400 intrinsic instructions; composition
includes 56 nested graphics calls and 14,336 pixel writes. These are component
proofs with declared initial fixtures. Complete cursor roots sharing pixels and
CPU time are under verification; live strict parity remains unchanged.


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


Resident geometry/clipping/short-memory helpers now match 822 calls and 22,265
ordered instructions; 770 calls also match 1,729 generated clock samples.
Complete frame composition advances to 18/25 native C78A calls: all 102,585
instruction addresses, 25,049 string iterations, 1,874 clock samples and captured
non-stack memory match from one initial fixture per frame. Intersection operand
order was corrected where equal rectangle results had hidden different native
branches. The 626,498-call interpreter/state proof remains accepted.

The seven remaining frame calls were initially misidentified as SHAP 5410
(corrected below to SHAP 5403), performing a cached source
lookup followed by conversion, allocation, draw and free each time. Their call
inventory is recorded; that resource path is the next composition step. Full
frame coverage, continuous animation, IRQ execution, startup and live scanout
remain open. Nothing from these reference captures becomes runtime frame or
instruction playback. The live build and strict 614/984 result are unchanged.

All **25/25 C78A frame calls now pass**, including the seven caption lifecycles.
The caption is SHAP **5403**, shape ordinal **3**, draw mode **10**; the former
5410 identification reversed shape/mode operands and is explicitly corrected in
`frame-caption-inventory-b.json`. The new resource, near/far heap, palette,
column-LZ and nibble-expansion generators share memory and the execution clock.

`frame-caption-complete-check-b` verifies 234,629 ordered instructions, 68,216
string iterations, 2,852 clock samples, 46 refills and all captured final RAM
outside the measured active stack. It also checks 35 intermediate memory stages.
The measured exclusions supersede the earlier 4 KiB mask that overlapped globals.
All seven decoder/expansion calls and 28 focused edge checks pass separately;
the 626,498-call interpreter/state check also passes after the argument fix.

The ledger now names the next TH-002 items explicitly: guest interrupts,
continuous interpreter/caller execution, remaining reached resource/codec paths,
and continuous startup/transitions. Component full-frame coverage is established
for this captured route; integrated live timing and full-game coverage are still
open. The served game remains unchanged at strict 614/984 callbacks.

Complete timer IRQ0 execution now passes all **1,127** observed calls, including
**342** chained BIOS calls. `timer-execution-check-b` compares **45,430** ordered
instructions and every instruction's clock/budget/I/O/IF/VGA state, **1,127** PIC
acknowledgements, **684** callbacks and **seven** refills. All **812,436,874**
captured memory bytes outside measured active stacks match. Fourteen focused
timer/BIOS rollover, timeout and tiny-budget checks also pass.

The new observer's same-DLL control is identical in clocks, frames and audio.
This establishes timer guest execution from each IRQ's initial fixture. Hardware
admission/stack mechanics, sound and mouse IRQs and continuous caller execution
remain required; the broader interrupt ledger item stays in progress. The live
build is unchanged, and this component result does not satisfy live parity.

Sound and mouse guest interrupt execution now pass against complete native calls.
`sound-execution-check-d` covers all **26 IRQ7 calls**, **5,670 instructions**,
**396 port operations**, **93 PIC operations**, 20 BIOS callbacks, 34 stack-segment
credits and **18,741,372** checked non-stack RAM bytes. The paths include ordinary
completion/unlocking, crossing a DMA page boundary and restarting looped audio.

`mouse-execution-check-a` covers all **three IRQ12 calls**, **4,547 instructions**,
784 string iterations, six PIC outputs and **2,162,492** checked non-stack bytes.
The movement callback composes 14 cursor helpers, two background copies and two
mask sprites, with two VGA latch events occurring during its execution. The
mouse input queue and DSP busy counter are initial state, not replayed paths.

Both new observer controls match all 3,116 callbacks in clocks, frames and audio.
Thirty-six focused sound/mouse branch checks pass under normal and tiny budgets.
The broader interrupt item remains open: entry/return stack mechanics, continuous
device scheduling and DMA/PCM behavior must join these guest paths. The live
strict result is still 614/984; the verified components remain unbundled.

Hardware entry/return now passes **2,312 native boundaries**: 1,156 entries and
their 1,156 outer IRETs (1,127 timer, 26 sound and three mouse interrupts). Every
captured register, stack word, flag, segment base and CPU/time value matches.
Twenty-one stack-wrap/high-ESP/flag edge checks pass. This proves the boundary
mechanics; continuous caller register and lazy-flag propagation still needs to
be joined to the generated instruction stream.

The new runtime `sound-device-work.js` replaces verifier-only DSP polling and
command parsing. `sound-device-execution-check-b` retains all 26 full IRQ7 passes
and checks **832 hardware fields**, **12 DMA-end event removals** and the generated
device effects. Twenty focused DSP/DMA checks pass. The observed mixer-fill
effects occur in inactive/masked modes; active sample consumption, mixer timing
and PCM output remain required. The live file and completion gate remain unchanged.


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


## Player-facing audit and delivered input fix (2026-09-28)

Following user feedback, work now prioritizes the integrated game's observable
behavior. `treehouse/player-fidelity-matrix.md` lists 17 finite journey groups
and distinguishes focused checks from complete ordinary-input native/browser
comparisons. Complete game wins and prize delivery are the next coverage work.

The served build now ends animal, sentence-token and music-editor drags on focus
loss, clears held arrow keys when the page is hidden, and cancels pending piano
presses awaiting audio unlock. The baseline reproduced six failures; all nine
lifecycle checks pass after the shared input cleanup fix. The new suite is part
of the standard regression command. All **38 suites pass**, and all **183 room
environment states** still match. Candidate and HTTP-served hashes agree.

Evidence: `output/treehouse/input-lifecycle-baseline-c/report.json`,
`output/treehouse/player-input-regression-a/report.json`,
`output/treehouse/player-input-environment-a/report.json`, and
`output/treehouse/player-input-delivery-a/report.json`.

Strict timing was rerun on this exact build and remains **614/984**, with
**12 unrepresented native displays** (`player-input-strict-a/report.json`).
This release fixes input reliability; it does not establish full clone parity.
The current completion gate is `completion-gate-ag.json`, which correctly fails.


## Delivered complete-game control fixes (2026-09-28)

Complete nature-game journeys exposed two player-facing defects: no readable
next-turn button after a robot answer, and the win routine overwriting the prize
buttons with the previous activity panel. Both are fixed in the served build.
Activity panels yield control to the shared prize chooser until transfer ends.

The new `verify_winning_journeys.py` covers four fresh mouse/touch games, both
characters, friend/robot opponents and assisted/manual play. It asks questions,
makes and recovers from wrong guesses, reaches human/robot wins, reveals both
animals, collects prizes, starts the next game and visits the room/robot shelf.
Human prizes persist on reload; robot prizes retain their session-only lifetime.
All **42 checks pass twice with identical actions**, using a fixed initial date
and game-clock stepping. No gameplay state is installed by the journey runner.

All **39 regression suites** and **183 room environment states** pass on the
current build. The aggregate `winning-regression-final-a/report.json` preserves
38 passing suite results and incorporates the corrected new journey harness's
final pass; earlier failed harness reports remain available. Candidate and
HTTP-served hashes agree (`winning-delivery-a/report.json`).

Strict timing remains **614/984**, with **12 missing native display changes**,
on this same build (`winning-strict-a/report.json`). The next player-facing work
is full maze and board-game winning journeys, followed by the remaining paired
native comparisons. Full completion is unproven; gate `completion-gate-ah.json`
remains failed.


## Full maze and board journeys verified (2026-09-28)

The unchanged live build now passes **41 suites together** in
`full-journeys-regression-a/report.json`. Twelve complete maze rounds cover
all five challenge types, all nine locations, wrong signs and song guesses,
recovery, early identification, all-note wins, replay and restart. Twelve board
games cover money/chips, both opponents, every goal, illegal roads, carry/borrow
and wrong-stack rejection, wins and a chip-payment loss, prizes, new game and
reload. No gameplay state is installed; the tests read answers to select visible
controls and accelerate the animation clock. Both new suites repeat their prior
passing actions, checks and outcomes exactly. HTTP-served SHA still matches.

No game-source change was needed by this batch. Earlier failed coverage and
harness reports are preserved. Environment and strict timing evidence remain
valid for the same unchanged build; strict timing is still 614/984 with 12
missing displays. Full native parity remains unproved. The updated completion
gate is `completion-gate-ai.json` and still correctly fails.

Next work: uninterrupted cross-activity creation/prize/save/revisit journey,
ordinary money-payment loss coverage, then paired native journeys and fixes for
observable differences. CPU instruction equivalence does not define completion.


## Continuous sessions and original maze playthrough (2026-09-28)

Two ordinary-control desktop/touch sessions pass 38 checks twice with identical
actions and checkpoints. Both songbooks, theater sentence, day/night collages
and an earned prize survive maze/nature wins, board/telescope/yard visits,
revisits and full reload. Evidence: `session-journey-repeat-a/report.json`.

A continuous maze comparison loads one original starting snapshot, then uses
only the original mouse choices through a wrong sign and eight correct signs.
All ten stable RGB checkpoints and all compared state/RNG fields match, as does
the historical in-progress song highlight. The original's completed victory was
captured without memory edits; two captures match all 3,000 callbacks, clocks
and audio. Evidence: `maze-native-journey-c/report.json` and
`maze-victory-tail-repeat.json`. This is checkpoint and sequence evidence, not
native timing/audio equality or a fresh-boot/cross-activity RNG proof.

No game-source change was needed. The verification record aggregates 43 passing
suites on the same served build (`session-native-regression-a/report.json`).
Existing environment/strict evidence remains tied to that unchanged SHA. Gate
`completion-gate-aj.json` remains failed for the documented fidelity work.
Next: paired native activity/transition journeys and observable differences;
ordinary money-payment loss is still missing from browser journey coverage.


## Delivered board-game continuity corrections (2026-09-28)

The robot now follows the original four-direction retry rule, preserving the
random sequence consumed by later amounts and layouts. Ordinary money credits
also reset the move counter to the original completed-turn value. A full native
money/robot game exposed the first defect after 18 matching checkpoints; the
corrected game matches all 25 images and checked state/RNG values through its
56-to-39 win. The minimized turn now offers the original 8/9 cents.
See `treehouse_board_continuity_fix.md` for cause and preserved failing evidence.

All **45 regression suites** rerun together and pass on the delivered build,
as do **183 environment states**. Evidence: `board-turn-regression-b/report.json`,
`board-turn-environment-b/report.json`, `board-native-completion-check-b/report.json`
and `board-turn-delivery-a/report.json`. The candidate and served hashes agree.
Strict timing remains **614/984**, with **12 missing native displays**
(`board-turn-strict-b/report.json`). Gate `completion-gate-ak.json` remains failed.

Next: other paired native activity/transition routes and cross-activity random
continuity; an ordinary money-payment loss remains uncovered. Ordered checkpoint
matches do not establish exact native timestamps or audio-waveform equality.

## Delivered nature prize continuity (2026-09-28)

The current served build is `0d57eba7c465c0101d717f057f4ff4179e6e5566f9759ffd7a6236b087e9b515`.
After revealing the other animal, the prize chooser now preserves that player's
displayed cards. Collecting a room object also schedules the original ambient
event, correcting the shared random draw and the next game's hand. All thirteen
native checkpoints through the new game and return to nature match in full RGB
and active gameplay/random state. See `treehouse_nature_prize_continuity.md`.

All **50 regression suites** pass together, including thirteen complete board
games with an explicit payment-loss route, and **183 environment states** pass.
Evidence: `nature-prize-regression-b/report.json`,
`nature-prize-environment-a/report.json`, `nature-prize-delivery-a/report.json`.
The earlier board aggregate coverage failure is preserved; it relied on a loss
happening among general routes, which the corrected startup random sequence
no longer produced. The added route requires a loss rather than removing that
coverage requirement.

The complete native nature journey still fails at room return: balloon/clock
pixels and random state differ. Full chip-game and money-loss comparisons retain
their previously documented failures on this same build. Strict nature timing
also remains 614/984 callbacks with 12 missing displays. These failures remain
explicit in completion verification and gate `completion-gate-ao.json`.

Next: resolve the room-return behavior through its observable transition and
environment operations, then remaining paired activity/sound journeys. Continue
to use low-level research only to explain demonstrated game discrepancies.

## Delivered room-return continuity (2026-09-28)

The current served build is `d367f5d54d5cd4e057b7512f72eaa2022c4d9eb4da4eee2d996eae186b9e377e`.
Room long-event scheduling now also refreshes the ambient deadline and indoor
nut timer, matching the original BB48 operation. Ordinary balloon movement uses
the original strict deadline and vertical tie rule. The separate chalk lift
keeps its existing two-tick cadence.

The full animal game, prize, new deal and room return now matches all **14 native
RGB checkpoints** and **16 gameplay/progression checks** from one initial
snapshot. No checkpoint state or random resets are used. Correcting the fixture
clock from saved BIOS time also removed a clock-image comparison error. Exact
room-event and presentation timestamps remain unproven; the matching room image
occurs earlier in the generated interval. See `treehouse_room_return_continuity.md`.

All **51 suites** and **183 environment states** pass on the delivered build.
Five guessing-game journeys now explicitly require human and robot prize paths;
question choice keeps a wrong candidate available instead of assuming that the
first question cannot uniquely identify the answer. Evidence:
`room-return-regression-b/report.json`, `room-return-environment-b/report.json`,
`room-return-delivery-a/report.json`.

The full chip/money-loss native comparisons and strict timing check were rerun:
their documented failures remain. Completion gate `completion-gate-ap.json`
continues to fail. Next broad comparison: complete theater sentence correction,
stage playback and return, followed by day/night nature editing and remaining
music/sound journeys. Existing strict timing work remains recorded separately.

## Delivered theater wrapping and decoration persistence (2026-09-28)

Current served build: `3d7c96f509e1e3ea11df0710e8a2abbf9ddacc5f8de7fae8c2075b43371fe2d3`.
Theater wrapping now searches before the fitted character count, matching the
original sentence layout. Newly dragged decorations start at integer pixel
coordinates, retaining their exact positions through save and reload.

All **53 regression suites** and **183 environment image states** pass. The
complete original theater journey repeats identically across two native captures;
all **29 browser image checkpoints** and theater state/geometry comparisons now
match. Room-return random state still differs. See `treehouse_theater_journey.md`.

Evidence: `theater-wrap-regression-b`, `theater-wrap-environment-b`,
`theater-native-check-d`, and `theater-wrap-delivery-a`. The served file matches
the verified candidate. Full chip and money-loss comparisons were rerun on this
same build and retain their documented failures; strict nature timing also
retains 12 missing displays. Complete theater comparison is now explicitly
required by the completion verification, so its remaining failure cannot be
hidden by the passing focused suites.

Next: complete day/night nature editing and remaining music/sound journeys.
Continue investigating original code only for demonstrated gameplay defects;
instruction-level equivalence is not a game-completion metric.

## Delivered day/night nature editing (2026-09-28)

Current served build: `e9af2b698fce8aec436c97f7052384f3aeb0f8d8ab8bf7059de2b8364f2d812c`.
Moving an existing animal now dismisses its fact panel and reschedules its idle
animation after a retained drop. Nature confirmations no longer schedule a room
event, and switching day/night initializes the restored animals' timers.
Dragging an existing animal outside also plays the original removal sound.

Two original editing captures repeat identically in state, all 21 PNGs, the
4,500-callback timeline and audio. The final browser candidate matches every
editing image checkpoint and checked filter/collage/random state. Eleven fresh
ordinary-control creation, move, erase, decline and reload checks pass; the
removal sound dispatch check passes. See `treehouse_nature_editing_journey.md`.

All **56 regression suites** and **183 environment image states** pass on the
served build. Evidence: `nature-edit-regression-b`, `nature-edit-environment-b`,
and `nature-edit-delivery-a`; candidate and served hashes match. The complete
native editing journey is now part of required completion verification.

Known money-loss, chip partial-redraw, theater room-return RNG and strict timing
failures were rerun and remain explicit. Full audio waveforms and exact native
presentation timing are not established by these passing image/state/dispatch
checks. Next: ordinary music creation/interchange and full playback journeys.


## Music journeys verified (2026-09-29)

The served runtime remains e9af2b698fce. Thirty ordinary browser checks pass
for both songbooks, all five speeds, repeat/stop, copying, saving and reopening.
All 22 paired original image/active-state checkpoints match. Both checks pass
twice; the original captures also repeat in images, state, timeline and audio.
See `treehouse_music_journey.md`.

The verification report now contains 58 passing suites on the same build:
56 from the previous integrated batch and two separately repeated music suites.
This is additional coverage, not a new runtime delivery or a full 58-suite rerun.
Full clone parity remains false; existing strict failures are retained.

Next: verify listening settings across song and score-mode changes, then address
observable transition/board/audio discrepancies. Instruction equivalence is not
a completion metric. The remaining-work ledger keeps these scopes explicit.


## Listening preferences delivered (2026-09-29)

Served build: `fb6652aa720a42d1873d6dcb545e061b6a7496020e3950ac92d06b6bc4c39f09`.

Each original song now retains separate speed, instrument and notation for
short and long scores. Composition and room visits preserve these session
preferences. Restart loads the saved song page with its original default
instrument. Music page refreshes also retain the idle-eye deadline, with the
original strict deadline comparison. See `treehouse_music_preferences.md`.

The paired original journey repeats exactly and all eleven browser image/state/
random checkpoints match. Eleven ordinary-control checks include mode/song
changes, composition, room return and full reload. The earlier candidate passed
59/60 suites, exposing the reload instrument bug; the final candidate passes
all **60 suites together**, plus **183 environment image states**.

Evidence: `music-preferences-regression-b`, `music-preferences-environment-b`,
and `music-preferences-delivery-a`. The served file hash matches the candidate;
the previous live build and completion report are backed up. Known money-loss,
chip partial redraw, theater return and strict timing failures were rerun on
this build and remain open. Full clone parity is false. Next: theater-to-room
continuity through an ordinary return journey.


## Room return and reminders delivered (2026-09-29)

Served build: `a59674954b51d942f4afd9ce65d0ff68caa643c293db1a4b558e9f0e3da4ebfc`.

Character actions now perform the original post-action ambient reset. Activity
return effects finish before overdue reminders, and urgent needs receive the
original minimum 600-tick grace period after return. A single original return
click reproduces the old mismatch; its repeated captures agree in state,
images, timeline and audio. See `treehouse_theater_return_fix.md`.

All **62 suites** ran together and pass, including the full **29-checkpoint
native theater journey** with room-return RNG and the fresh ordinary reminder
checks. All **183 environment image states** pass. The served HTML hash matches
the tested candidate and the prior live build/report are backed up in
`theater-return-delivery-a`.

Money-loss and chip partial-redraw comparisons were rerun and retain their
known failures. Strict nature timing remains 614/984 callbacks with twelve
missing displays. Full clone parity remains false. Next: audible instrument
release/stop and playback comparisons, retaining all broader fidelity issues.


## Sustained audio rate delivered (2026-09-29)

Served build: `1dde9b9a90a5dcf09649a52e549fd71ced7775158e1de7ecc9fb6217a780f2f3`.

The production audio graph now applies the pinned reference mixer's 14-bit
fractional rate quantization after hardware rate rounding. Twelve repeated
native note captures expose the old phase drift and the corrected graph passes
56 bounded sustain/metadata assertions. See `treehouse_audio_sustain_fix.md`.

A broader ordinary-input capture covers all 42 instrument/family choices with
126 notes. All rates, sample counts and loop metadata agree. Median correlation
for later waveform windows improves from 0.91173 to 0.99976. Three Balloon
windows remain below 0.99; full interpolation, stop decay and scheduling parity
remain open. The measurements do not establish subjective audibility or exact
complete waveforms.

All **63 suites** ran together and pass, plus **183 environment image states**.
The served hash matches the candidate; prior build/report are preserved in
`audio-rate-delivery-a`. The full theater journey remains passing. Board-loss,
chip partial redraw and strict nature timing failures were rerun and retained.
Full clone parity remains false. Next: the complete theater notebook journey.


## Theater notebook coverage completed (2026-09-29)

All 14 paired notebook drag/drop, correction, performance, removal and restoration
checkpoints match on unchanged build `1dde9b9a90a5`. Both original captures and
both browser replays repeat successfully. No runtime fix was needed. See
`treehouse_theater_notebook_journey.md`. The bundle now has 64 passing suites
(previous 63-suite batch plus this separately repeated check), retaining all
known strict failures. Next: the money-loss discrepancy, then remaining ordinary
room/yard journeys. CPU-equivalence work is not the completion metric.


## Actual payment coin preparation delivered (2026-09-29)

Served build: `c6795ecc633cb3b6240498f9fa5ca177abcb44157b86f2c722eab62114c8b475`.

Money payments now perform the original preparation of their actual coin amount
before the greedy payment display replaces it. The isolated 26-cent payment
previously failed random-state comparison; it now matches both full images and
all gameplay/random fields. The full loss journey improves from first divergence
at step-07 to matching through step-09. Step-10 unused second-amount preparation
remains open. See `treehouse_board_payment_rng.md`.

All **65 suites ran together and passed**, including the new theater notebook
and large-payment comparisons. All **183 environment image states** pass.
Delivery hash matches the served file; previous live artifacts are backed up.
Strict nature timing remains 614/984 with twelve missing displays; chip state
continuity still passes with one partial redraw mismatch. Full parity is false.
The 12-note audio sustain comparison was rerun; the broader 126-note diagnostic
remains historical evidence rather than being relabeled for this new build.

Next: complete ordinary room/yard interaction and interruption journeys. Keep
the scratch-state discrepancy explicit without escalating to CPU equivalence.


## Yard interactions delivered (2026-09-29)

Served build: `c279d12d4977f7fae371f59a243f7619db4b9db8ae2954445560a2f7826a2337`.

Hollow toss/squirrel/sign completions preserve the original random state; pond
animations retain their final frog sprite. All 23 yard/hollow checkpoints match
full RGB/gameplay/object/RNG state, including interruption, nut limit and revisit.
The full 24-checkpoint journey generates every reference image and matches RNG,
but its final room balloon is one movement step ahead; this failure is retained.
See `treehouse_yard_journey.md`.

Verification: 65/66 suites passed in `yard-regression-a`. The old exterior
sequence mixed two independent reference captures; its corrected fixture passes
twice on the same HTML. Aggregate `yard-regression-b` reports 66 passing suites
without claiming a new batch run. All 183 environment states pass; all prior
strict board/nature failures were rerun. `yard-delivery-a` backs up the prior
live build and verification. Full clone parity remains false.

Next: continuous ordinary room calendar/clock/environment/chalk interactions.


## Calendar controls and narration delivered (2026-09-29)

Served build: `36849cc7af8817419e27f0dff11af1848b4da01ba6e565401e25166f44c450e9`.

Canvas calendar hit behavior now matches the original; date browsing speaks
before opening, and opening/closing restores the original scheduling side
effects and cloud countdown. All ten paired calendar checkpoints match full
images and gameplay/random state. See `treehouse_calendar_journey.md`.

All **67 suites ran together and passed**, plus **183 environment image states**.
Prior live artifacts are backed up in `calendar-delivery-a`, and the served hash
matches the candidate. Full room controls still fail from clock completion;
short clock and chalk reproductions are retained. Native board-loss, chip
redraw, yard balloon and strict nature failures remain explicit. Full clone
parity is false. Next: clock completion, chalk input and narration interruptions.

## Room navigation, clock and chalk fixes delivered (2026-09-29)

Served build: `d5e06ec0ed5824040393a01f97a2d2f4b8dd2f766974273e3057f2841e50c8eb`.

Choosing another friend during calendar narration no longer clears selection
while navigation is blocked. Eight failing baseline assertions are corrected;
80 checks now exercise five controls in narration and rolling phases on desktop
and touch. Clock speech completion and chalk return now reset ambient scheduling
as the original does. The returned chalk cursor retains its tool color until
the next movement. Both isolated original comparisons pass full images/state.

All **70 suites ran together and passed**, plus **183 environment image states**.
The uninterrupted desktop/touch creation/game/prize/reload session also passes
within that batch. Delivery backup and matching HTTP hash are recorded in
`room-controls-delivery-a/report.json`.

The complete room journey now passes the first eleven checkpoints, then fails
at spider completion. `room-spider-baseline-a` reproduces that failure in a short
replay. Full board-loss, chip redraw, yard balloon and strict nature comparisons
were rerun on the delivered hash and remain failed. Audio full-waveform parity
remains unproven. See `treehouse_room_controls_followup.md`.

The user's concern about CPU-level detail is reflected explicitly in the ledger:
instructions/registers/heap/interrupt equivalence are diagnostic research, not
additional deliverables. Observable fidelity requirements remain intact. Next:
spider/environment completion and remaining room interaction integration.

## Complete room control journey delivered (2026-09-29)

Served build: `61f8e694fe1b772846ec0cf6d9c4bd9844960b7ec175f226543f98d2dab31cfc`.

Room animations no longer wait for a popped balloon to clear their area. Spider,
nest and chirping completion now schedule ambient behavior once; the automatic
event selector no longer schedules prematurely as well. The full original room
journey passes all **24 complete RGB and gameplay/random/object checkpoints**.
The existing nature/prize/room-return journey also passes after the duplicate
reset was removed.

Both desktop/boy and touch/girl complete **22 feeding/sleep/wake checks** through
visible controls and production time advancement. They cover refusal, feeding,
yard travel while asleep, natural wake, activity interruption and room return.
Actions and checkpoints repeat identically on the delivered build.

Verification: batch b passed 71/72 suites; a yard test assumed the previous
premature scheduling. Its corrected behavior assertion and all existing images
pass twice on the same HTML. Aggregate c records **72 passing suites**, with
provenance rather than a new-batch claim. All **183 environment states** pass.
`room-environment-delivery-a` retains previous live files and matching served
hash evidence. See `treehouse_room_environment_completion.md`.

Known board-loss, chip partial redraw, yard-return balloon and strict nature
failures were rerun and retained. Exact room timing and full audio parity remain
open. Next: remaining object-drag/revisit and cross-activity control coverage,
then noticeable board/audio differences. No CPU-equivalence work is needed for
this next step.

## Object dragging and drawing revisits verified (2026-09-29)

The served HTML remains `61f8e694fe1b772846ec0cf6d9c4bd9844960b7ec175f226543f98d2dab31cfc`.
No game-source fix was required. `room-drag-journey-a` and
`room-drag-journey-repeat-a` pass all **30 checks** with identical reports.

The new registered suite uses actual mouse and touch events on the game canvas,
plus visible buttons. It pops the balloon, drags a pillow to the friend, drops
fruit and a nut through the trapdoor, visits their yard objects and reloads
them. It draws on the original canvas, visits music/nature/theater, compares
every retained drawing pixel, declines and confirms erase, and undoes the clear.
Only the production clock is accelerated; no gameplay state is installed.

`room-drag-coverage-a` backs up the prior verification and records **73 passing
suites in aggregate** on the unchanged HTML: the previous 72 plus this new suite
run twice. It is not a new 73-suite batch. Strict original timing/audio and the
known board/yard discrepancies remain failed or unproven.

An asynchronous scope question asks whether intermediate DOS redraws and tiny
waveform differences should continue blocking release, following the user's
concern about excessive detail. Until answered, the original strict acceptance
remains in force; no failures have been waived.


## Prize object rendering and placement fixed (2026-09-29)

Delivered `43a8cda7163cc8b06b0f8ab1c5621e3183ab10629de502c82c07a5c5e94bb9dd`.
The balloon now moves clear of released objects, held prizes render above the
friend, and the handed caterpillar remains visible. Placement and departure
reset the ambient/object timers at the appropriate events.

The repeated original airplane and caterpillar captures match all nine complete
RGB/state checkpoints in the browser. Held object storage is compared through
the browser drag origin; displayed geometry is reported and verified by full
images. Rerunning this comparator against the previous live build retains the
visible failures. See `treehouse_prize_object_journeys.md`.

The complete 73-suite regression batch passes, plus two separately run new prize
suites on the same HTML (75 aggregate). All 183 environment states pass. The
local delivery backs up prior HTML/build metadata/verification and confirms the
HTTP-served SHA in `object-clearance-delivery-a/report.json`.

Full native money-loss, chip and yard failures and strict nature timing were
rerun on this build and remain open. The completion goal is active; no fidelity
acceptance has been waived. CPU equivalence is diagnostic only. The previous
status-only goal turn was no progress; this turn changes the runtime and delivers
verified player-visible fixes.


## Egg input and idle-room handoff delivered (2026-09-29)

Delivered `e8ad0a585e548bbe58f827039242a74e81f29283e277436945f7285d5a64f55b`.
This goal turn is progress: runtime input and scheduling corrections were
implemented, compared with repeated original journeys, regression-checked and
served. No CPU-equivalence work was added.

The egg now distinguishes release and a held press before hatching; pointer
movement does not drag it. Bird flight completion performs its own ambient
reset, and due balloon/cloud updates run between object animation and the next
ambient event. All 75 registered suites pass in one complete immutable-build
batch, including the previous plane/caterpillar and full room journeys. All
183 environment states pass. Local delivery backups and HTTP hash verification
are in `egg-input-delivery-a/report.json`.

Both new original journeys repeat: 163 short-press and 133 held-motion PNG/WAV
files, input actions and timeline hashes match. The full held-motion journey
passes all four RGB/state checkpoints. The short-press journey matches all seven
RGB images but **fails its final balloon state**: the hatch/flight finishes a
few ticks early and a later movement occurs before the original's. The failure
is retained in the current verification bundle. No checkpoint was excluded and
no fixture-specific delay was added. Other click-only object gestures are a new
explicit open ledger item. See `treehouse_egg_input_journey.md`.

Full money-loss, chip, yard and strict nature comparisons were rerun on this
same HTML and remain failed. Full audio parity is unproven. The goal remains
active; this is not a complete-clone claim.


## Object press and consumption fixes delivered (2026-09-29)

Delivered `d7a51afab75241553a1094e409c740e96321350f9ad3ce06b172a4596502498c`.
Nut piles and dropped food now respond to clicks, click-only objects preserve
original short/held press behavior, and duplicate pointer capture-loss no longer
cancels released actions. Basket/worm handoff and object timer ownership are
corrected. The previous status-only goal turn was no progress; this turn
completes repeat evidence, promotes these runtime changes and updates the ledger.

All 16 original capture pairs repeat in actions, checkpoints, timeline and
PNG/WAV hashes. Fourteen browser journeys pass completely. Of 72 checkpoints,
71 match full RGB membership and 71 match compared state. Short nuts retain one
intermediate position difference; held open-basket retains a 49-pixel worm image
difference. Raw storage order of non-overlapping objects is diagnostic, while
full images, object geometry/state and subsequent interactions remain checked.

The 76-suite batch initially passed 75 suites. The exterior fixture assumed
all random ambient choices start activity; its corrected coverage includes the
original no-op choice and passes twice on identical HTML with unchanged image
assertions. Delivery records 76 passing suites in explicit aggregate, including
234 mouse/touch press checks, plus 183 environment states. It does not claim a
second complete batch. Backups and HTTP hash proof are in
`object-press-delivery-a/report.json`.

All known money-loss, chip, yard, egg and strict timing failures remain in the
current verification bundle. Full audio parity remains unproven. Next priority
is the money-game loss sequence and player-facing progression. CPU equivalence
is not a separate workstream. See `treehouse_object_press_journeys.md`.


## Money loss ending and mystery payments delivered (2026-09-29)

Delivered `63151140a6de463d86a3603f9de4b70210861e176f0abf50a9dde4c6a8e816b2`.
This turn is progress: two runtime corrections were implemented, checked against
original input and delivered. Unaffordable money payments keep the requested
amount in their label while taking only available coins. Mystery-node payments
now prepare both original coin arrays, restoring their random-call side effects.

The focused final payment/ending matches both complete RGB checkpoints and
compared gameplay/random state. The previous live build still fails the same
comparator with a seed mismatch and 219 differing pixels. Original logical
player means prize recipient after a loss; the verifier reports it separately
from the retained losing dashboard, which remains checked by full RGB.

All 77 registered suites pass in one full immutable-build batch, and all 183
environment states pass. The read-only native probe and uninstrumented control
agree on inputs, callback timeline and all 163 ordinary PNG/WAV files. The 23
additional comparison reports have no execution errors and retain all known
failures. Delivery backs up the previous live files and verifies the HTTP hash.
See `treehouse_board_loss_ending.md` and
`output/treehouse/board-mystery-payment-delivery-a/report.json`.

The complete original money-loss journey still diverges at step-10. Its direct
payment uses an uninitialized delta inherited from cursor resource allocation;
this changes the following roll and prize layout. The dependency is now
identified and retained explicitly, without a fixture constant or CPU-emulation
workstream. Chip partial redraw, yard/egg balloon timing, nut phase, held-worm
image, strict nature presentation and full audio parity also remain open.

## Production audio mixer delivered (2026-09-29)

Delivered `b0b73bf1f6f0cd7720d9f7b28cedaafa364cb543f117038cc557c14254deb4de`.
The preceding user-status turn was no progress: it explained priorities but
changed no implementation. This turn completed candidate validation and
delivered the pending sound and input corrections. CPU equivalence remains
diagnostic only; the work changed the actual playable audio renderer.

The worklet consumes original decoded PCM with the pinned reference's linear
interpolation and decay toward silence. All 336 measured waveform windows
across 126 note cases and 42 instruments are sample-exact, using one attack
alignment per note. The Balloon differences are resolved. Three stop phases
follow the observed four-unit decay law. These results do not prove complete
unaligned audio or native event timing.

The full candidate-C regression caught delayed first-input processing during
worklet module loading. Candidate D loads independently of input, retains
queued commands and preserves cancellation before readiness. Its 18 real-output
checks cover file/HTTP origins, note replacement, old-key release, mute and
focus loss. The failed C batch and earlier fixture failures are preserved.

All 80 registered suites pass in one complete immutable-build batch. All 183
environment states pass. The 23 additional comparisons completed without
execution errors and retain their prior pass/fail outcomes. Full money loss,
chip partial clearing, yard/egg balloon timing, nut phase, held-worm pixels and
strict nature presentation remain failed. Previous live files are backed up
in `audio-mixer-delivery-a`; the served HTTP hash matches the candidate.
See `treehouse_audio_mixer.md` for evidence and scope.

The next priority is integrated player journeys and speech/effect continuity.
Full audio scheduling and waveform parity remain open. This is a delivered
increment, not a complete-clone claim.


## Theater sound and selection sequences delivered (2026-09-29)

Delivered `c6f3a650aaaadfff02e787cf202a959ff6e25f8568c1a5da561fffd6f9437c55`. The previous goal turn delivered
the audio mixer and was progress. This turn found and restored 33 missing
original cues during a complete theater journey: option/category/prop clicks,
new-token travel, curtain transitions and narration order. All 73 observed
original sound sources now occur in order. Read-only native observation leaves
all 29 saved images, the entire WAV, callback timeline, actions and states
identical to the uninstrumented control.

All 81 suites pass in one immutable-build batch, plus 183 environment states.
All 29 theater and 14 notebook endpoint image/state checks pass. Return to the
room closes the curtains and defers reminders throughout its transition.
Desktop/touch whole sessions and drawing revisits pass. Historical wait
fixtures now advance the restored presentations; failed batches are retained.
The separate interval display audit matches 309/580 original images
(baseline 201/580); full intermediate presentation remains incomplete.

All 23 additional comparisons completed without execution errors. Existing
money-loss, chip partial redraw, yard/egg timing, nut phase, held-worm pixels
and strict nature failures remain in the same-build verification bundle.
Full sound timing and waveform parity remain open. Previous live files are
backed up; served HTTP hash verified. See `treehouse_theater_sound_journey.md`.


## Nature editing feedback delivered (2026-09-29)

The previous status-only turn was no progress. This turn reproduced and fixed
15 missing nature editing cues, then delivered `a44564be50d4bbc7c18bae9195eedb77f9d2f56db08b50645ad7e1af722d7342`.
All 17 editing and 57 quiz observed original sound sources match in order and
rate. Native controls retain identical recorded WAV, video timeline, images,
actions and checkpoints. All 21 editing and 14 quiz/prize/room image/state
checkpoints pass. The defect was absent sound callbacks in editing handlers.

All 82 registered suites pass in one complete batch, plus 183 environment
states. The 23 additional comparisons retain their known pass/fail outcomes
without execution errors. Earlier live files are backed up and the HTTP hash
verified. Full event timing, rendered whole-waveform parity and all existing
strict/native failures remain open. See `treehouse_nature_sound_journey.md`.


## Board action sounds and trade input delivered (2026-09-29)

The previous turn delivered nature feedback and was progress. This turn
restored board roll, driving, robot thinking, balance and chip sounds, corrected
immediate offer hints, and made wrong-stack input interrupt trade hints.
Delivered `73a6d9d9cf5c48401c62c3b09b869b14548c7e9f07657b16755230a86c75368e`. All 236 money and 480 chip observed original
source/rate events match. All 25 money images/state and all 49 chip states
match; 48/49 chip images match, retaining the 312-pixel partial redraw. Actual
car sound output passes for both players.

83 suites pass on identical candidate HTML: 82 from the full batch plus the boardgame rerun after correcting stale fixture state. The failed batch is preserved; this is not a second complete batch.
All 183 environment states pass and all 23 extras retain known outcomes.
Previous live files are backed up and served hash verified. Full audio
waveforms, event timing and all prior strict/native gaps remain open.
See `treehouse_board_sound_journeys.md`.


## Maze automatic-hint input delivered (2026-09-29)

Delivered `032490fa50b5a1e7141a3910f30d3e6a934fecfb91776c76ffc534bc0d0e3e8b`. Fixes lost canvas presses during automatic maze auditions. Eleven native RGB/state checkpoints match through victory. All 184 observed original sound sources/rates match between inputs. Thirteen unmatched browser starts and early victory-song timing remain recorded; full audio/timing parity is not established.

All 84 suites pass in one immutable-build batch, including a paired original-scheduled maze journey and fresh desktop/touch hint input. All 183 environment states pass; 23 additional reports retain their prior outcomes. Known strict/native failures remain. Previous live files are backed up and the served HTTP hash matches. See `treehouse_maze_sound_journey.md`.


## Piano and maze transfer delivered (2026-09-29)

Delivered `57b4673bf421a0deaf06ba9a624607e650edd38576f1abba84ee71947c923917`. Restores original smoke and child bucket transitions at both piano/maze boundaries. All 62 transfer compositions match original images in order in each full/skip route. Full entry improves from 21/46 to 45/46 RGB checkpoints; stable tutorial/return/reentry state matches. All 18 full-route and 13 skipped-route observed sound sources/rates match between inputs. Actual smoke output is verified; full timing remains open.

85 suites pass on identical candidate HTML: 84 from the full batch plus the journey rerun after waiting for the restored return animation. The failed batch is preserved; this is not a second complete batch. Original transfer frame order and entrance/exit/skip journeys pass. All 183 environment states pass; 23 additional reports retain prior outcomes. Full entrance reports retain their cursor and intermediate RNG timing failures alongside all previous strict/native failures. Previous live files are backed up and the served HTTP hash matches. See `treehouse_maze_entry_transfer.md`.


## Maze treehouse exit delivered (2026-09-29)

Delivered `8a107c9eb4a91d13b19b36312d0fae0932eb965d011477836abffd7e5aec067b`. The original top-right maze exit now returns to the treehouse using the music activity return transition. The adjacent control still returns to the piano. Both desktop and touch victory exits finalize and persist the replacement song/history. Play and victory native sound observations match all three sources/rates between inputs; exact cue timing and full waveform parity remain open.

All 85 registered suites pass in one immutable-build batch, including 53 ordinary maze exit/save/reload checks. All 183 environment states pass. The 23 additional comparisons retain prior outcomes. Both new maze exit replays match all 14 RGB images and preserve destination, random state and song history; six balloon-state timing mismatches per route remain explicit failures. Previous live files are backed up and the served HTTP hash matches. See `treehouse_maze_global_exit.md`.


## Board entry and piano corrections delivered (2026-09-29)

Delivered `9a67a26e9613d5be536ba5578127717430f22ee64cbbb112d1553b211de7c65d`. Delivered original temporary listening-key notation, original tempo hit boundaries, and board preparation before options. Board entry preserves imported player levels until Play. Both maze treehouse exits retain 14/14 matching images and their six known balloon timing mismatches.

All 86 registered suites pass on one immutable build; all 183 environment states pass. The 23 additional comparisons retain their previous outcomes. All 30 piano checkpoints match RGB and music state. The activity tour matches 22/27 images and active gameplay/random state throughout; ten room-object timing mismatches and five image mismatches remain failed. All 58 observed tour sound sources/rates match between player inputs; exact sound timing remains open. Previous live files are backed up; served HTTP hash matches. See `treehouse_activity_tour.md`.


## Maze difficulty persistence delivered (2026-09-29)

Current served build: `2d29766c93dda302b3e0c0d618a36f40eec6f91a92bbfbf2655a77206093869b`. Difficulty now survives ordinary piano exits and maze reentry in both directions. All 87 regression suites pass on the delivered build, including 12 new desktop/touch difficulty checks. All 183 environment states pass. The paired activity tour retains the same five image and ten room-object mismatches, with final maze reentry matching. All 58 observed tour sounds match sources/rates between inputs. Strict timing remains failed. Other supplemental comparisons retain their previous-build hashes and are explicitly historical, not newly verified. See `treehouse_maze_difficulty.md`.


## Theater caption sequencing delivered (2026-09-29)

Delivered `fe0819316c49aeff41b013108debd70cf1ec7659e4ef49894edcb7d4698b8434`. The sentence now stays unchanged until both tokens finish moving. All 88 regression suites and 183 environment states pass on this build. The caption fix restores 35 complete shuffle frames and four manual-drag frames without losing prior native image matches. Theater now matches 348/580 intermediate images, all 29 endpoints/gameplay states and all 73 observed sound sources/rates. The remaining 232 images and strict nature 614/984 callbacks remain explicit failures. Other supplemental evidence retains previous-build hashes and is not claimed as freshly verified. See `treehouse_theater_shuffle_caption.md`.


## Held piano input delivered (2026-09-29)

Delivered `a89b3f65ac50ce1a548fa6618f795261e0a79507c057e3a87b4a305d9747d322`. All 89 regression suites and 183 environment states pass on this build. Held piano notes and idle interruption match 17 native full-image/music/random-state checkpoints; 18 fresh mouse/keyboard/touch checks pass. The 30 short-note and 22 native authoring/playback checkpoints pass. Identified before-input frame matches prove interval membership, not equal input latency. Theater remains at 348/580 intermediate images; strict nature remains at 614/984 callbacks with 12 missing displays. Historical supplemental evidence retains its original hashes; full fidelity is not established. See `treehouse_piano_held_input.md`.


## Telescope centering delivered (2026-09-29)

Delivered `377179be2807525d7c010e2da7e8b517d073be2f930b69d59cb9ff2836850df1`. All 92 regression suites and 183 environment states pass. All four final telescope views match original RGB images and all 16 mouse/touch replay-versus-exit checks pass; the complete activity tour improves from 22/27 to 23/27 matching images, with four room-return images and ten object-state mismatches retained. The strengthened money-loss suite covers 16 games in four mouse/touch friend/robot sessions. Strict nature remains 614/984 callbacks with 12 missing displays, and theater remains 348/580 intermediate images. Historical supplemental comparisons retain their original build hashes; full fidelity is not established. See `testing/treehouse_telescope_centering.md`.


## Theater room input delivered (2026-09-29)

Delivered `d2ecc31d6a0a8f254c519335ffa16739c566806f915fe75f5685203274f06d13`. All 93 regression suites and 183 environment states pass. Sixteen fresh mouse/touch theater entrance edge checks now match the original; the previous build failed all eight outside clicks. The complete activity tour remains 23/27 matching images with ten balloon-state mismatches. Strict nature remains 614/984 callbacks with 12 missing displays, and theater remains 348/580 intermediate images. Historical supplemental comparisons retain their original build hashes; full fidelity is not established. See `testing/treehouse_theater_room_input.md`.


## Payment resource dependency (2026-09-29)

All nine native loss-game payments now have a verified operation-level formula using the current embedded CURS 0 resource offset: 36 amount/coin/random checks pass. Its handle and payload persist while offset changes from 10 to 14 during the step-21 board redraw. SHAP 4001 allocation triggers forward resource packing. The new allocator pack method matches both native packing operations, all 122 moves and returned available sizes; all 52 existing preparation states and five boundary checks pass. Resource-lifetime integration into the playable game remains required. The current full loss replay still fails at step-10 and later rolls; no recorded offsets, fixed delta or seed reset is used. Served build remains `d2ecc31d6a0a`. Rebuilding confirms the same HTML hash; this is component progress, not a delivered payment fix. See `testing/treehouse_payment_resource_dependency.md`.


## Payment resource integration (2026-09-29)

The complete converted board-background handle allocation now follows packing-before-eviction ordering and matches native allocator state, including cursor relocation. The complete SHAP 4001 load matches using semantic resource decisions with instruction-work modules absent. Both cache/layout modes pass nine checks and all 2337 shape headers; the continuous resource regression retains 104 matching checkpoints, 79 generated shapes, 12 scene phases and 2399 generated sounds. All 248 observer/control checks pass. These are component comparisons from offline initial fixtures; generated startup and whole-scene resource lifetimes remain required. The full money-loss game still diverges at step-10; no playable fix, recorded offset schedule or seed reset is delivered. Served build remains `d2ecc31d6a0a`, verified by a fresh rebuild and HTTP hash. See `testing/treehouse_payment_resource_dependency.md`.


## Resource startup and reference clock (2026-09-29)

Initial near-heap headers now derive from pinned executable stack parameters; conventional resource-arena headers derive from an explicit DOS allocation result. All four startup model checks pass. New observers run before the first game frame. Separate startup reference fixes the previously unsupported time-to-noon command using a BIOS clock launcher before the unchanged game. Two original observer captures match two plain cold boots in all 209 checks, including RAM, images, audio and callback timing. Previous unpinned-clock control failure remains recorded. Arena growth, generated DOS allocation and complete startup/resource lifetimes are still required; the money-game divergence and playable build remain unchanged. Served build remains `d2ecc31d6a0a`, verified by fresh rebuild and HTTP hash. See `testing/treehouse_resource_startup.md`.


## Resource growth and startup allocation (2026-09-29)

Semantic near-heap and conventional resource-arena growth now match all nine original startup growth calls and six focused checks. Ordinary allocation drives growth and retries; the first complete 1527-byte handle allocation matches generated initial far-arena state, returned handle and full near/far metadata. All 313 observer/control checks pass. Existing 52 heap cases, 104 continuous resource checkpoints, 79 generated shapes, 12 scene phases, 2399 generated sounds and the board background load retain their passes. Each native growth check starts from an offline fixture; DOS allocation/availability, startup resource requests and complete activity lifetimes still need generation. The playable file and full money-game failure remain unchanged. Served build remains `d2ecc31d6a0a`, verified by fresh rebuild and HTTP hash. See `testing/treehouse_resource_startup.md`.


## Source-generated startup and embedded font (2026-09-29)

Startup now generates the pinned DOS process map, resource arena and near allocations from executable/configuration bytes and platform source constants. The first embedded FONT 0 source load matches exact payload and complete allocator ownership without captured starting state. DOS startup passes 26 comparisons plus five focused checks; first allocation passes six, font loading passes eight plus three focused checks, and observer/control output passes 209. Later font activation, cursor/catalog resources and complete activity lifetimes remain required. The money-game divergence is not fixed and the playable build is unchanged. See `testing/treehouse_resource_startup.md` and `testing/output/treehouse/dos-resource-evidence-a/report.json`.


## Generated font and cursor activation (2026-09-29)

Generated startup now includes VGA font conversion, transfer into the cached font handle, cursor background allocation, embedded cursor loading, image/mask conversion and promotion. All 18 native boundary comparisons and three focused checks pass; all 313 plain-original control checks pass. The continuous resource regression retains 104 checkpoints, 79 shapes, 12 scene phases and 2399 sounds. Archive/catalog loading and later activity resource lifetimes remain required. No playable payment fix is claimed. See `testing/treehouse_resource_startup.md` and `testing/output/treehouse/activation-evidence-a/report.json`.


## Generated archive loading (2026-09-29)

Archive directory allocation, linking and flagged preload now pass 49 comparisons across seven original opens. A source-defined saved rectangle joins the first th.dat open to continuously generated startup; all 28 boundary and three focused checks pass. New capture/control comparison passes 209 checks without masking RAM. Later cursor/font replacement, direct resource copies, remaining catalog opens and activity lifetimes still need continuous integration. The playable build and money-game divergence are unchanged. See `testing/treehouse_resource_startup.md` and `testing/output/treehouse/catalog-evidence-a/report.json`.


## Continuous seven-archive startup (2026-09-29)

The reusable OriginalStartupResources module now generates the pinned VGA/Sound Blaster resource sequence through all seven startup archives, including cursor/font replacement, the maximal free-memory query and direct sound-configuration copy. All 88 native boundary comparisons and six focused checks pass. Heap, shape, board-background and continuous resource regressions pass. Startup animation and later activity lifetimes still need generation before the direct-payment formula can use the live cursor source. The playable build and money-game failure are unchanged. See `testing/treehouse_resource_startup.md` and `testing/output/treehouse/startup-chain-evidence-a/report.json`.


## Maze dispatch timing audit (2026-09-29)

The unchanged playable build passes two new complete original-scheduled maze journeys (11 RGB/state checkpoints each) and fresh mouse/touch hint input. New origin-anchored timing audit distinguishes 176 unique source matches from eight ambiguous repeated auditions. Victory-song onsets remain 23 ticks early (one observation 24); deficits increase around chooser opening, collected-song cleanup and final scene construction. No fixed delay or runtime correction was added. See testing/treehouse_maze_dispatch_timing.md.


## Cold sound preparation checkpoint (2026-09-29)

Semantic sound preparation now writes decoded PCM and updates the original header in the shared resource cache. 341 checks pass across 19 native load boundaries, all 273 compressed assets, control output and focused cases; the hash-matched previous model fails both cold drawer payloads. Startup passes 98 native/six focused checks and the continuous regression retains 104 checkpoints, 79 shapes, 12 scene phases and 2399 sounds. Original drawer loads account for 63.9529/89.9895 ms in the last-note route. Those measurements are comparison evidence only. The playable build is unchanged and the early victory song remains open. See testing/treehouse_maze_cold_sound_loading.md.


## Maze drawer sound preparation delivered (2026-09-29)

Delivered `09b8bf3819b343109cf09fd6b2848a87b91bbfefe35454294551e602e344724f`. All 94 regression suites and 183 environment states pass. Maze drawer first-use preparation now consumes intrinsic decoder work from original compressed assets; 36 fresh mouse/touch checks pass, with 18 failures on the prior build. The original-scheduled maze retains all 11 RGB/state checkpoints and 184 observed sources/rates. The ending song improves from 23 to 13 ticks early; exact timing remains failed. Original cache eviction, other load costs and scene drawing remain unintegrated. The activity tour remains 23/27 images with ten balloon-state differences. Strict nature remains 614/984 callbacks with 12 missing displays; theater remains 348/580 intermediate images. Historical supplemental reports retain their original hashes. Full fidelity is not established. See `testing/treehouse_maze_decoder_delivery.md`.


## Theater curtains and previews delivered (2026-09-29)

Delivered `50db501cceb7b595f169978c2660d91e6346540992d7f20d2d85bb5d2e462542`. All 95 regression suites and 183 environment states pass. Theater small previews now hide the cursor; curtains preserve the prior stage/options, cover the rail, use the busy cursor and restore the director background. All 57 fresh mouse/touch checks pass; the previous build fails 32. Exact native theater image membership improves from 348/580 to 385/580, restoring 37 complete images without losing a previous match. All 29 endpoint/gameplay checkpoints and 73 observed sound sources/rates pass. The remaining 195 theater images and exact timing remain open. Strict nature remains 614/984 callbacks with 12 missing displays; the cross-activity tour retains 23/27 images and ten balloon-state differences. Money-loss RNG, resource lifetimes and whole-session audio/timing remain unresolved; full fidelity is not established. See `testing/treehouse_theater_curtain_preview.md`.


## Script-driven animation resource preparation (2026-09-29)

Complete animation preparation now generates object, ordered shape, surface and backup ownership from original SCR/SHAP resources. Six native constructors pass 24 comparisons and 80 shape loads, with no instruction-work dependency or observed allocation requests driving construction. The original-output control passes 209 checks; the existing resource regression retains 104 checkpoints, 79 shapes, 12 scene phases and 2399 sound loads. Each new constructor comparison begins from an offline initial fixture. Palette/direct-script ownership and continuous startup/activity integration remain required. The playable build is unchanged and the money-loss divergence is not fixed. See `testing/treehouse_animation_resource_lifetimes.md`.


## Continuous title resource setup (2026-09-29)

Startup now generates resource ownership continuously through the first title-animation constructor from executable/platform/archive inputs. All 24 native boundary comparisons and four cache-release/reload/reuse checks pass. Palette loading, persistent shape caching and cached-source backlink cleanup are implemented. Original-output controls pass 209 checks; previous startup, six animation constructors, continuous resource regression and board-background checks retain their passes. No native initial RAM or allocation schedule drives the joined startup. Playback/disposal and later activity lifetimes remain required. The playable build and money-loss divergence are unchanged. See `testing/treehouse_animation_resource_lifetimes.md`.


## Complete title resource lifetimes (2026-09-29)

Generated startup now continues through all three title animation resource lifetimes, cursor restoration, the playback-status query source load, script/image/surface disposal, and final title/music resource release. All 54 native comparisons and four cache checks pass from executable/platform/archive inputs. Earlier startup retains 98 comparisons and six focused checks. This verifies ownership at semantic script/sound completion, not rendering or audio timing; title interruption coverage, later startup/activity lifetimes and live integration remain required. The playable build is unchanged and the money-loss divergence remains open. See `testing/treehouse_animation_resource_lifetimes.md`.


## Resource startup reaches character selection (2026-09-29)

Generated resource startup now reaches initial character selection, including six interface palettes, the backdrop and decorations, both child palettes, three preview lifetimes, saved rectangles, music ownership and cleanup. All 144 comparisons at 24 native boundaries and four cache checks pass continuously from executable/platform/archive inputs. The unchanged-original control passes 209 checks; earlier startup retains 98 comparisons and six focused checks. This proves bounded resource ownership, not pixel/audio timing or live integration. Actual character selection, transitions and activity lifetimes remain required before the money-game formula can use the generated cursor location. The playable build and full money-loss discrepancy remain unchanged. See `testing/treehouse_animation_resource_lifetimes.md`.


## Earned magnifying-glass return delivered (2026-09-29)

Delivered `b5744fce90a3433acad289ecebe0498dccfd854dbbe794a53ab11f82e9462352`. All 96 regression suites and 183 environment states pass. An earned magnifying glass now returns through original floor placement after the child uses it, preserving its position through room visits/reload and its placement random draw. Ten fresh mouse/boy and touch/girl checks pass; the previous build fails six. The uninterrupted quiz/prize/use/revisit comparison preserves all 22 random checkpoints (previously 18), while full state improves from 14/22 to 16/22. Images remain 16/22; balloon timing and click/overlap rendering differences remain explicit failures. Strict nature remains 614/984 callbacks with 12 missing displays; theater remains 385/580 intermediate images. Money-loss RNG, other resource lifetimes and whole-session audio/timing remain unresolved. Unrefreshed supplemental reports retain their prior build hashes; full fidelity is not established. See `testing/treehouse_earned_prize_return.md`.


## Robot reward route and warning completion delivered (2026-09-29)

Delivered `9b6d63debe08a863c5a6ba57bbe99342cc2c96dfc44668cdf175f32249990d3e`. 97 regression suites and 183 environment states pass on one immutable build: the full batch passed 96 suites, and the exterior suite passed after replacing two immediate-increment assertions with original warning-completion ordering. The failed batch is preserved. Hunger/fatigue increments, urgent retry deadlines and the other need grace period now follow warning completion. All 576 branch checks pass (164 failures on the prior build). A complete original robot quiz/prize/shelf/theater journey matches 33/35 images and all 35 random states; three room endpoints retain balloon-state differences, and full state remains 32/35. The prior hunger mismatch is fixed. Strict nature remains 614/984 callbacks with 12 missing displays and theater remains 385/580 intermediate images. Money-loss RNG, balloon clearance/return timing, full audio timing and other required integration remain open. Unrefreshed supplemental evidence retains historical build hashes; full fidelity is not established. See `testing/treehouse_robot_prize_and_need_warnings.md`.


## Character balloon clearance delivered (2026-09-29)

Delivered `efc57996b72588e9144516acede437714c79840d1e67b71080dad3968d645bfc`. All 98 regression suites pass in one immutable-build batch; all 183 environment states pass. Character actions now clear overlapping balloons before constructing and starting their original scripts. All 84 focused checks pass; the previous build fails 30. The focused native warning improves from 2/5 to 5/5 complete images, with 3/5 checkpoint states matching. Two timing-state differences remain. The uninterrupted robot prize route retains 33/35 images, 32/35 states and all 35 random states; the earned human prize route retains 16/22 images/states and all 22 random states. Strict nature remains 614/984 callbacks with 12 missing displays, and theater remains 385/580 intermediate images. Money-loss RNG, room-return timing and full audio/presentation timing remain open. Supplemental reports not rerun retain their historical hashes; full fidelity is not established. See `testing/treehouse_character_balloon_clearance.md`.


## Character-selection resource ownership (2026-09-29)

Resource ownership now continues through actual boy/girl selection, both departure scripts, the chosen climb, and cleanup of four saved backgrounds and two palettes. Each variant passes 192 native comparisons and six focused checks from generated startup; plain-original control comparisons pass 423 and 407 checks. The verifier supplies the default cloud and two observed visible credit-change events before selection; their timer schedule and live renderer hooks remain unintegrated. No captured allocation requests, resource addresses or initial heap RAM drive the model. Native comparisons A/baseline failures are preserved. The playable build is byte-identical and the money-loss divergence remains unresolved.


## Basket handoff and stationary placement delivered (2026-09-29)

Delivered `27689144aa93085bc22f6e2b282b0563f08960659bfeb2b489bf307ac1804413`. All 100 regression suites pass in one immutable-build batch; all 183 environment states pass. Basket-to-worm handoff preserves the original initial drawing delay, and long stationary holds now place draggable objects instead of clicking them. All 14 native basket checkpoint images and gameplay/object/random states match across three gestures. All 50 mouse/touch threshold checks pass; the prior build fails 20. The new original long-hold capture repeats across 141 checks. Strict nature remains 614/984 callbacks with 12 missing displays, and theater remains 385/580 intermediate images. Money-loss RNG, room-return timing, full audio/presentation timing and remaining complete journeys stay open. Supplemental reports not rerun retain their historical hashes; full fidelity is not established. See `testing/treehouse_basket_handoff.md`.


## Initial room resource ownership (2026-09-29)

Generated startup now reaches initial room ownership for both children. Corrected foreground saved-background selection and the cloud lifetime across calendar overlay drawing. Boy: 246 native comparisons plus six focused checks; girl: 204 plus six. Observer controls pass 423 checks. Semantic idle events/new-game defaults remain harness inputs; activity lifetimes and live timer/render integration remain required. The playable file is unchanged and the full money-loss divergence remains unresolved. See `testing/treehouse_room_resource_lifetimes.md`.


## Board-transition resource preparation (2026-09-29)

Generated startup now matches the ordinary board-transition entry and opening-ring constructor. All 264 native comparisons and six focused checks pass. Device rate limits are derived from the original Sound Blaster backend; the constructor now includes caller-owned initial child composition. The six earlier constructor cases retain 24 comparisons and 80 shape loads. Ordinary controls pass 439 checks. Playback/cleanup, room teardown, board lifetimes, live event integration and complete payment replay remain required. Playable bytes and the money-loss failure are unchanged. See `testing/treehouse_board_transition_resources.md`.


## Outgoing board transition and room release (2026-10-05)

Generated startup now matches the complete outgoing board-transition resource lifecycle and room release: 294 native comparisons and ten focused checks pass. The shared SCR interpreter drives the ring and bubble, including both authored sounds and the child-removal callback. Added PSL sound preloading, child-backing replacement, board-inlet ownership, sound replacement, animation cleanup and room teardown. Original observer controls pass 439 checks. This is default central-room resource ownership at semantic completion, not pixel/audio/timing parity. Board initialization, live event integration and the complete payment replay remain required. The playable file and money-loss discrepancy are unchanged. See `testing/treehouse_board_transition_resources.md`.


## Board initialization resources (2026-10-05)

Generated resource memory now reaches the initial Money/robot options screen: 366 native comparisons and twelve focused checks pass, including the complete initial board draw and options resource lifecycle. The existing BoardGame algorithm reproduces nodes, directions, balances, board types and final RNG state from one native board-entry seed; that seed remains a stated semantic input, so upstream RNG/clock integration is not established. Girl startup/room regression retains 204 comparisons and six focused checks. Both new capture-control reports pass 439 checks. Temporary filled-label surfaces were the final options mismatch. Archive/payload transport is compacted without changing the first 360 comparison results. Playable bytes are unchanged; board gameplay resource lifetimes, live integration and full money-loss replay remain open. See `testing/treehouse_board_initialization_resources.md`.


## Godot runtime correction and first port checkpoint — 2026-10-05

The user clarified the expected architecture after noticing Treehouse used JavaScript rather than the established Godot approach. Godot is now the delivery target (including browser delivery via Web export); the earlier JS build remains the reference during migration. TH-008 through TH-017 explicitly track the required port and TH-007 depends on them.

Implemented shared asset extraction, an independent Godot project, GDScript indexed renderer/text/cursor, complete SCR interpreter, rotating selection credits, both entrance sequences and initial room composition. Godot startup evidence B passes nine checks, two full native frames (128,000 pixels total), and 356 bounded JS interpreter comparisons containing 11,512 events; all scripts terminate. Native timing and activity callbacks are outside the interpreter cross-check. Preliminary PCM playback is not verified audio parity. The real Godot Web export passes three Edge boot/input/room-region/Escape checks with no browser errors; export hashes and full screenshots are retained in godot-web-a.

The shared extraction refactor rebuilds the JS artifact unchanged at 27689144aa93085bc22f6e2b282b0563f08960659bfeb2b489bf307ac1804413. The live browser reference was not replaced. Next port room/yard/character state and transitions, then full music activity; the Godot room is currently an initial-state view. Existing strict timing/audio, RNG integration and complete-journey failures remain open. Reports: testing/output/treehouse/godot-startup-b/report.json and testing/output/treehouse/godot-web-a/report.json.


## Godot room interaction checkpoint — 2026-10-05

Ported calendar sheet/browsing and date/time speech fragments, cloud movement, spider/nest/chirp, original chalk brush/eraser/cursor/confirmation, pointer-key cadence and focus cleanup. Balloon following, clearance and short-click color/pop now work. The 24-checkpoint room-native-journey-c route passes every full RGB image (1,536,000 pixels total) and the explicitly compared calendar/cloud/chalk/balloon fields after one initial room/time fixture. Image membership within each input interval is tested; strict presentation times, resident RNG and general object/need state are outside this proof. Historical failed Godot calendar/chalk reports are retained.

Evidence: godot-room-journey-d/report.json; godot-room-startup-c/report.json (nine checks, two native images, 356 scripts/11,512 events); godot-room-input-a.json (twelve input checks); godot-room-web-a/report.json (six actual Edge interaction checks, no errors). Export: testing/output/treehouse/godot-room-web-build-a, package SHA-256 126f3c092efe169541b96dcbe6db84ba6fd558aa53e2e467e6feae6c119ec123. The existing port 8767 JS demo remains untouched.

TH-009 and TH-015 are in progress, not closed. Next: resident character/object actions and held-object placement, yard/hollow and original navigation/transitions, then complete music. Escape currently returns to selection and still needs the retained-character yard flow. Preliminary Godot audio uses original sample/rate data but mixer/waveform parity remains open.


## Godot resident and yard checkpoint — 2026-10-05

Added the shared original RNG stream, resident poses/action queue and callback object ownership, need warnings, yard/hollow hotspots, pond/window/squirrel animations, interruptible sign and original integer nut flight. Escape returns to the retained-character yard; the ladder returns indoors. General object drag/place, offers, sleep/wake and automatic ambient tasks remain incomplete.

Godot action regression C matches all 158 available character/pose/action cases against JS in final image, pose, objects, completion tick and RNG. It uses explicit isolated fixtures and disables device playback while retaining sample-derived deadlines; no audio parity claim. Accelerated A/B audio-backend shutdown warnings are retained; C cleanly isolates device output. Native yard journey C has 24/24 exact full-frame image matches and 23/24 checked states. Its final balloon bounds mismatch is unchanged from yard-native-check-c: expected [64,133,102,162], actual [65,135,103,164]. It remains a failure. Native room regression B passes 24/24 images and checked states; startup D passes nine checks/two native images/all 356 scripts; twelve focused inputs remain passing.

Actual Edge export check B passes nine interactions through the room, yard, hollow, nut throw and ladder return, with no browser errors. Immutable export: testing/output/treehouse/godot-yard-web-build-b; PCK SHA-256 3b83f548ef6df6db4efa148b44e39373d4650aebdc3dd16b6cf236f3d90b737b. Separate local Godot preview: http://127.0.0.1:8768/; delivery-a checks served files against export hashes. Original JS port 8767 is unchanged. All broad migration/fidelity issues remain open.


## Godot objects, care and ambient events — 2026-10-05

Ported held-object thresholds, surface placement/falls, all direct object click/offer handlers, fruit/pillow care, naps and natural waking, basket/worm/bird handoffs, nut bags/piles, food consumption and automatic room/yard events. Connected calendar, clock speech, environment and window completion timers. Pending object callbacks are released when the Godot scene exits.

Evidence: godot-objects-component-c passes 86 isolated JS comparisons with 3,425 sampled resident frames, sound events, completion/state/RNG. godot-objects-care-b.json passes 18 mouse/touch care checks from selection with ordinary updates and advancing civil clock, without need/pose/object fixtures. Twelve focused input checks, 158 action cases, nine startup checks, two native startup images and all 356 SCR comparisons remain passing. Three godot-objects-basket*-final-a routes match all fourteen native images and full checked object/gameplay/RNG states.

Broader strict failures stay open: godot-objects-room-e matches 24/24 images, 19/24 full states; remaining RNG divergence starts after declining erase. godot-objects-yard-final-a matches 24/24 images, 23/24 full states, with the known return-balloon geometry failure; its RNG matches throughout. godot-objects-egg-final-a matches 3/4 images and 4/4 full states; final frame remains unmatched. Native image membership is bounded, not exact display-time or audio-output proof. Historical failures remain intact.

Immutable export godot-objects-web-build-b has PCK SHA-256 ae99622847dcea0bf31f778db534e56a928004ef106319796c1430b7ac0219d3. Eleven real Edge checks pass, including held pillow drag/fall and nut bag. All nine files served at http://127.0.0.1:8768/ match the export (godot-objects-delivery-a.json). The server is direct Python PID 30000 with redirected logs; orphaned older 8768 Python servers were stopped after their detached pipes caused closed HTTP connections. Existing browser tabs were not refreshed. Port 8767 reference is untouched.

Next: original room-to-activity transitions/rewards, then the complete Godot music activity. All required migration and fidelity issues remain open.


## Godot music listening and room transfers — 2026-10-05

Ported original room/music teleport and return, waking a sleeping child before departure, listening books, both score sizes, all 17 piano keys, held note movement/focus cleanup, pitched original PCM with effective rates/loop bounds, song playback/tempo/repeat, contents/page navigation, idle animation, all seven families and 42 instrument selections/facts/auditions. The generic ring/bubble renderer supports all four variants; only music is integrated into playable activity navigation. Added safe empty-clip handling for foreground objects.

Evidence: godot-music-component-e passes 151 full-image and complete song-event/end-tick cases versus the JS reference, plus four complete native menu/music images (long score allows 17 authored idle-eye frames, not timing equality). godot-music-transitions-c matches all 330 changed full RGB frames in original order across eight isolated transition sequences from explicit initial native fixtures. godot-music-input-a.json passes 47 production control checks; godot-music-care-b.json passes 22 mouse/touch checks including interrupted-nap music entry. godot-music-objects-a retains 86 operation cases. godot-music-startup-b retains nine checks, two native images and 356 SCR comparisons.

The native room replay retains 24/24 images and 19/24 full states; yard retains 24/24 images and 23/24 states. Remaining erase-dialog RNG and yard-return balloon differences are unchanged. The earlier egg final-image failure stays open. Real device output waveform/mixer parity, exact presentation timestamps and complete integrated activity journeys are unproven.

Immutable export godot-music-web-build-a, PCK SHA-256 783e07f7bf51274309d30cdb684d50671c08a0381c055fd7d852f5528894c5a0, passes sixteen actual Edge checks (godot-music-web-b) including piano entry, physical key down/up, families and return. All nine served files match (godot-music-delivery-a.json). The preview at http://127.0.0.1:8768/ is direct Python PID 14668 with redirected logs. Existing tabs were not refreshed. JS reference port 8767 is unchanged.

Next: complete composition/personal songbooks, note/rest editing, title input, copy/random/erase dialogs, persistence/printing, then musical maze. These controls are still incomplete in the Godot preview. Required fidelity and migration items remain open; this checkpoint is not full-game completion.


## Godot personal songbooks and print sheets — 2026-10-05

Ported both personal songbooks (42 editable songs each), original note/rest palette, insertion marker and note dragging, erasing, title editing, contents, copy/random/erase confirmations, and original print-sheet preview. Native SONGS.DAT serialization preserves all 86 records, CP437 titles and trailing bytes; desktop saves use user://SONGS.DAT and Godot Web persists the same file through IndexedDB. Invalid imports are rejected before changing either book.

Evidence: godot-editor-native-c passes all 22 full native images and active song/title/marker/selection/RNG states through one continuous input journey. godot-editor-component-c passes 223 complete image/sequence cases across both sizes, all note/rest durations and spellings, drag colors, seven contents pages, title carets and confirmation phases; three original print sheets also match in full. godot-editor-controls-b passes 32 production-control/binary-save checks. godot-editor-listening-a retains 151 listening cases and four native frames. godot-editor-care-a retains 22 mouse/touch care checks.

Actual Edge export check godot-editor-web-a passes 23 checks with no console errors, including physical-key composition, title entry, switching books, print preview and restoring the authored notes/title after an actual browser reload. Immutable export: testing/output/treehouse/godot-editor-web-build-a; PCK SHA-256 b0118b8db2bdab0c2dcb3d7ff73b3b69aec683d334ecc28acbba4181efb5785b. The Godot preview at http://127.0.0.1:8768/ serves all nine matching files (godot-editor-delivery-a.json), direct Python PID 36552. Existing tabs were not refreshed; the JS reference on 8767 remains unchanged.

Historical failed runs are retained: native-a exposed JSON float lookup mismatches in CP437 and pitch tables, fixed by integer normalization; component-a/b failed in the new JS comparison harness (constant reassignment and wrong renderer name), corrected without changing the reference game; controls-a incorrectly expected a Unicode music symbol absent from the recovered CP437 mapping, corrected to supported extended characters. Native-c and component-c use the production source delivered above.

Next: musical maze and its integration/rewards. User-facing file import/export and physical print/download delivery are still required; the current print button only previews the original sheet. Strict presentation timing/audio and prior room erase RNG, yard-return balloon and egg-route final-image failures remain open. No migration issue is closed by this checkpoint.

Startup regression godot-editor-startup-a also passes nine checks, two full native images and all 356 SCR comparisons. Completion remains unproven; completion-gate-db retains every open migration/fidelity requirement.


## Godot musical maze — 2026-10-05

Ported overlay 1's challenge generation, all five sound/sign types and nine scenes, both characters and frog animations, note roller/falling rewards, walks, adaptive difficulty, reminders, song drawer, incorrect and correct guesses, victory, full-song replay, next round and exits. Music/maze smoke and bucket transfers now use the original shapes and character scripts. Maze notation uses instrument 9; instrument-identification samples play finitely. First-use drawer decoding waits derive from the recovered sound work, with warm reuse. Audio note completion preserves a newer sound's channel ownership.

Evidence: godot-maze-native-b passes 20 checks: eight seeded native generation comparisons, ten continuous full-image/state/RNG checkpoints through a wrong sign and eight correct signs, the in-progress victory highlight, and completed victory. godot-maze-component-a passes 244 full image fixtures across scenes, sign types, both characters, actor/frog frames, drawers, note drops, highlights and endings. godot-maze-controls-d passes 66 fresh mouse/boy and touch/girl checks including full/skipped tutorial, two errors, wrong guess, correct early guess, automatic-audition input, cold/warm sound loading, replay, new round, reentry and global exit. These checks read answers to select inputs and do not install maze progress/difficulty states.

Godot-maze-entry-full-d and godot-maze-entry-skip-c remain FAILED overall. Both pass all 54 changed transfer frames in native order and every stable entry/return checkpoint. The full route matches 45/46 checkpoint images and 44/46 checked states; intro-05 and intro-25 differ in when RNG is consumed, and intro-15 has a 129-pixel frog-pointer timing difference. The skipped route matches 19/19 images and 18/19 states, with intro-05 RNG timing remaining. Paired native sound observation/control timelines and WAVs agree; all 18 full-route and 13 skipped-route observed sound sources/effective rates occur in Godot order between player inputs. Unmatched Godot starts remain in the reports. This is not exact event-timing, stop ownership or audio waveform proof.

The existing composing native journey retains all 22 checkpoints (godot-maze-editor-a). Editor rendering now passes 225 cases (godot-maze-editor-component-a), including added original music-eraser cursor checks; its cursor uses CURS2 with recovered color and hotspot ordering. Startup retains nine checks, two native images and all 356 SCR comparisons (godot-maze-startup-a).

The actual Edge export passes 29 checks (godot-maze-web-b), including saved composition after reload, maze transfer/tutorial skip, a sign interaction and retained-score return. Immutable export: testing/output/treehouse/godot-maze-web-build-a; PCK SHA-256 c214b7474cfb5337a0485b71ba928d31224fbe2616957d114b73d403a6a1a6e0. Nine served file hashes match in godot-maze-delivery-a.json. Preview http://127.0.0.1:8768/ uses direct Python PID 6916 with redirected logs. Existing tabs and the JS reference at 8767 were not refreshed.

Earlier failed reports are retained. Controls-a/b clicked outside the girl's original selection hotspot; the harness now uses the same x=145 hotspot as the existing care checks. Web-a sent Escape before the reverse bucket animation finished; web-b waits for the original portrait to return. Entry transfer count checks now compare changed-frame counts (54) rather than the older collector's 62 entries containing checkpoint-boundary duplicates, and use each route's own native hashes/order. No gameplay timing was changed to fit these harness errors.

Next major port: sentence theater, followed by nature and board games. Maze preference/history persistence, help/settings, file interchange, physical printing and integrated rewards remain open, along with the explicit tutorial, room erase RNG, yard balloon, egg-route image and strict audio/presentation failures. No broad migration issue is closed.


## Godot sentence theater — 2026-10-05

Ported the sentence theater to Godot: all actor/action/place/time choices, original speech and animation, grammar feedback/correction, Mix Up tokens and shuffle, draggable scenery decorations, per-place actor positions, options, curtain choreography and original room entry/return. Plays save through user://theater.json and persist in the Web export after reload. Shared STATUS.DAT interchange, rewards, help and printing remain separate unfinished integration work.

Evidence: godot-theater-c passes 1,390 whole-frame/component/continuous progression checks, including ten independent native still images. godot-theater-room-c passes all 29 full native checkpoint images and checked scene/selection/order/options/props/actor-position/RNG fields through one original room snapshot and the complete recorded pointer journey back to the room. godot-theater-controls-c passes 52 fresh mouse/boy and touch/girl checks for entry, choices, valid/invalid performance, correction, shuffle, drag, persistence rejection and return/reentry. Two identical overlapping decorations now retain distinct identity when dragged; controls-b demonstrates the old failure and controls-c its correction.

Godot-theater-audio-a matches all 73 observed original PCM sources/effective rates in order within input intervals. The native observer/control pictures, frame timeline, audio recording and inputs agree. The editor click finishes before its curtain cue. Additional Godot starts remain explicit. Neither this nor the image-membership replay proves exact native presentation timestamps, sound-stop timing, mixer or output waveform parity.

Immutable Web export: testing/output/treehouse/godot-theater-web-build-b. PCK SHA-256 83a0efb401efd7f35fde92c5f9d90a6cde16c42e3f58def4cca45a4da1ac65f0. Godot-theater-web-c passes ten actual Edge checks, including original stage/sentence regions, animated performance, persisted play after reload and room return; no console errors. All nine files served at http://127.0.0.1:8768/ match (godot-theater-delivery-a.json). Direct Python server PID 7748 replaces the prior owned maze preview server. Existing browser tabs were not refreshed. The old 8767 reference server closes HTTP connections; no action was taken on it, and its source/artifact files were not edited.

Regressions: godot-theater-startup-b retains nine checks, two full native startup images and all 356 SCR comparisons; godot-theater-maze-controls-a retains 66 maze controls. Earlier failed harness runs are preserved: theater-a used a nonexistent random.state instead of reset/seed; room-a initialized the yet-unentered theater as editor rather than its default options screen; web-a compared the empty-stage region over the native snapshot's pointer. Those harness defects were corrected without changing production behavior to fit fixtures.

Next: Godot nature exploration/collages/guessing, then board games. The theater remains in progress until shared rewards/help/printing/persistence and strict timing/audio are integrated. Prior maze tutorial, erase-dialog RNG, yard balloon and egg-image failures remain open. No migration/fidelity issue is closed by this checkpoint.


## Godot nature, prizes and telescope - 2026-10-05

Nature now runs in GDScript: animal filters/facts, day/night collages, drag/blink,
erase confirmation, scene-print preview and persistent saves; human/robot animal
guessing, definitions/help, wrong guesses, victory, both animal reveals and
shared prize choice/delivery. Telescope approach/return, all four views,
nonrepeating view selection, original per-view replay/exit bounds, speech-tail
interruption and robot prize shelf are also connected. The shelf remains
session-only, as in the original; original STATUS.DAT interchange is unfinished.

Evidence: godot-nature-b passes 2,559 rendering/behavior cases;
godot-nature-edit-b passes 21 complete native collage checkpoints;
godot-nature-quiz-a passes ten complete native quiz checkpoints through both
reveals; godot-nature-controls-c passes 56 fresh mouse/boy and touch/girl checks,
including human prize delivery, persistence and room return. Godot-telescope-a
passes 72 controls and nine complete native images (all four views for both
children, plus the populated robot shelf). These are bounded comparisons,
not proof of strict native timing or output waveform equality.

The complete native robot route godot-robot-prize-a matches 33/35 full images
and 32/35 complete checkpoints; all RNG, quiz, shelf and visited-mask fields
match. Three room-return object states and two images still fail. The human
prize route godot-nature-full-a matches all 14 checkpoint images but fails final
balloon geometry and object storage order. Both remain explicit known failures;
no broad migration or fidelity issue is closed. The theater regression retains
29/29 native checkpoints (godot-nature-theater-b); startup retains two full
native images and all 356 SCR comparisons (godot-nature-startup-b).

The immutable export testing/output/treehouse/godot-nature-web-build-b is served
at http://127.0.0.1:8768/ by direct Python PID 40560. PCK SHA-256:
d94108f1154de9074d0ad08351a3c5a36faeb13a5fe38b09d34429061a4939fb.
Godot-nature-web-d passes 21 actual Edge checks with no console errors, including
collage save/reload, quiz interaction and telescope entry/replay/return.
Godot-nature-delivery-a.json verifies all nine served files. Existing tabs were
not refreshed and the old JavaScript reference files were not changed.

Earlier browser failures are preserved: web-a compared the native ready-screen
cursor against a cursor moved elsewhere; web-c attempted the telescope before
the room-return animation released input. The verifier now reproduces the
native ready pointer and waits for the original visible cursor before the next
room click. No runtime behavior was changed to fit these harness defects.

Next: Money and Chip board games, then shared help/settings/STATUS.DAT,
file interchange and actual printing. Nature printing currently previews the
original sheet only. Prior maze tutorial timing/RNG, room erase RNG, yard balloon,
egg-route image, and strict audio/presentation failures remain open.


## Godot Money and Chip games - 2026-10-05

Implemented boardgame.gd, board_motion.gd and board_renderer.gd. Both games
are connected through original room transition variant 3 and share prizes with
nature. Includes options, six retained goal settings, human/robot turns,
original random-call order, directed paths, rolling/blinking cars, mystery-node
resolution, offer comparison, payment hands, coin/chip transfers, interactive
carrying/borrowing, spoken numbers, win/loss endings and fresh games after prizes.
Mode/opponent/goals persist through user://board.json; STATUS.DAT integration
remains required. Robot prizes reach the telescope shelf; human prizes reach
the retained room.

Evidence:

- godot-board-b: 4,794 complete RGB, gameplay/RNG and sound-dispatch comparisons
  against the preserved JS implementation, including options for both children,
  four continuous games, payments (including zero balance), credit and exchanges.
  This is port consistency, not original waveform/presentation proof.
- godot-board-money-a: all 25 native images and state/RNG checkpoints through a
  complete winning Money game, using one initial snapshot and recorded clicks.
- godot-board-chips-a remains FAILED: all 49 native states/RNG match and the
  ending is reached; 48/49 images match. Step-15 retains the same 312-pixel
  exchange-highlight discrepancy present in the existing JS comparison.
- godot-board-loss-a remains FAILED: 12/33 images, 11/33 complete states; first
  RNG mismatch step-10, later routes diverge and the recorded losing ending is
  not reached. Direct-payment random/resource dependency remains required work.
- godot-board-controls-c: 39 fresh mouse/boy and touch/girl checks through legal
  games, exchanges, endings, prizes, return, settings reload and invalid-save
  rejection. No gameplay progress or balances are injected.
- godot-board-web-b: 20 actual Edge checks, both game modes, original options,
  dice/car pixels, legal road movement, saved Chip mode after reload and return.
- Regressions: theater 29 native checkpoints; nature 56 controls; telescope 72
  controls and nine native images; startup two full images and all 356 SCRs.

The native board replays settle each action and observe 420 ticks, matching the
existing verifier. They establish checkpoint membership and state continuity,
not equality at original input/display timestamps. Strict timing remains open.

Immutable export: testing/output/treehouse/godot-board-web-build-a.
PCK SHA-256: 4e55b389ab507d4a6fe613d66445ffb01fc82466e5ee7c299f8e6845033109f7.
All nine files served at http://127.0.0.1:8768/ match in
godot-board-delivery-a.json. Direct Python server PID 30000 replaces the owned
nature server. Existing tabs were not refreshed; JS reference files are unchanged.

Earlier failed checks are preserved: component-a identified a retained payment
visibility flag and zero-sign transfer mismatch; component-b corrects them and
exercises payments through the actual landing sequence. Controls-b found JSON
numeric-type validation rejecting valid saved goals; controls-c accepts integral
JSON numbers and rejects invalid goals. Web-a's verifier placed its cursor so
part of the cursor was clipped at the screen edge; web-b uses an interior point.

Next: shared settings/help and original STATUS.DAT integration, file interchange
and actual printing/downloads. Native board loss/Chip highlight, nature/robot
room returns, maze tutorial, erase RNG, yard balloon, egg final image and strict
audio/presentation failures remain explicitly open. No migration issue is closed.

## Godot shared preferences and contextual help delivered - 2026-10-05

All 26 original help texts and context selection now run in Godot, including
Ctrl+Alt+F1 dedication, theater notebook tabs, pointer-dependent help dismissal,
20-tick close feedback and room/music ambient resets. F2 implements the five
original preference switches, FONT0 geometry, red 12-tick row feedback and
validated local reloads. Sound and printing switches gate actual audio and
print prompts; maze difficulty follows the chosen level. Ctrl+S and Ctrl+V
show the original interruptible 180-tick status messages, including over a
preferences/help panel. Modal mouse/touch/keyboard input is isolated from the
underlying activity, with the standard original cursor.

Evidence under testing/output/treehouse:
- godot-preferences-e/report.json: 62 controls/context/persistence checks;
  all 20 native regions including cursor match (12 help, six settings, two status).
- godot-preferences-web-d/report.json: 17 actual Edge checks on immutable build B,
  including all five switches, reload, status overlays, room and notebook help.
- godot-preferences-startup-a/report.json: two whole native images, nine startup
  checks and all 356 bounded SCR script comparisons pass.
- godot-preferences-theater-a/report.json: all 29 native journey checkpoints pass.
- godot-preferences-money-a/report.json: all 25 Money winning checkpoints pass.
- godot-preferences-board-a.json: all 39 board gameplay/control checks pass.
- godot-preferences-delivery-a.json: all nine served files match; PID 29852
  serves http://127.0.0.1:8768/ from godot-preferences-web-build-b.
  PCK SHA-256: 9fc31eb4ce1750239f4c7e001df287121f6d8cb1297ea402d2d3c0d6346e0a40.

Browser failures A/B are retained: A used the wrong theater PLAY rectangle;
A/B pressed F1 during the original final 60-tick entry pause. C waits for that
pause and passes on build A; D passes on build B with the ambient reset fix.
The modal comparison covers full declared regions, not their room backdrops.
Other help contexts have source/context coverage, not new native screenshots.
An audio teardown warning in controls B-D was traced to the isolated voice
fixture; E clears its stream/cache before engine shutdown and has no leak warning.

Preferences JSON is interim persistence: original STATUS.DAT integration,
user-facing STATUS.DAT/SONGS.DAT interchange, real print/download delivery and
title boot remain required. No migration issue is closed. Earlier strict
fidelity failures are unchanged. The legacy completion gate is still JS-oriented
and must be migrated to current Godot artifacts before final acceptance.

## Godot original save files and interchange delivered - 2026-10-05

Added STATUS.DAT codec/runtime integration for all recovered fields: preferences,
score modes/pages/used flags, nature filters and both collages, board goals,
theater words/order/props/actor offsets, maze history/chooser and room objects.
Original bytes are retained, including inactive records, opaque words/handles,
noncanonical flags and trailing data. Normalized/skipped records retain their
source slots for later edits; structural changes materialize a consistent active
list. Native transient bird/spent flower removal, pillow creation and object
state normalization are applied to the runtime without changing an untouched
export. Unsafe maze histories/choosers cannot enter endless rejection sampling.

STATUS imports restart at character selection and reset session-only activities,
prizes and timers. SONGS remains separate and is retained across STATUS imports.
Shared saves accompany activity/preferences/song saves and periodic browser
persistence. Existing JSON profiles migrate into a seeded STATUS export. Bad
uploads leave the game unchanged; truncated local saves are preserved before
recovery, and read failures disable automatic replacement. Regression fixtures
now explicitly disable user-profile persistence before constructing their scene.

F9 opens file controls; browser imports use native HTML buttons/file pickers
through JavaScriptBridge, with GDScript serialization and downloads. Both original
filenames are supplied. Desktop native FileDialog support is implemented but
interactive desktop checking remains pending. Gameplay pauses while these file
controls are open. There are no new controls over the original game screen when
F9 is closed.

Passing evidence under testing/output/treehouse:
- godot-status-k/report.json: 81 format/model/control checks, including all known
  rich-model fields, three original files, exact round trips, filtered record
  edits, noncanonical flags, invalid imports, fresh-runtime reload and F9 controls.
- godot-status-web-e/report.json: 22 actual Edge checks for complete STATUS/SONGS
  byte interchange, CP437 titles, cancellation, rejected input, repeated imports,
  automatic persistence/reload and preservation through preferences.
- godot-status-preferences-web-b/report.json: 17 browser help/preferences checks.
- godot-status-preferences-a/report.json: 62 controls and all 20 native modal regions.
- godot-status-editor-a.json / godot-status-nature-a.json: 32 / 56 controls.
- godot-status-money-a/report.json / godot-status-theater-a/report.json: all
  25 / 29 original full-image/gameplay checkpoints remain matched.
- godot-status-startup-a/report.json: two full native images, nine startup checks
  and all 356 bounded SCR comparisons pass.
- godot-status-delivery-a.json: all nine served files match the immutable export.

Build: godot-status-web-build-c. PCK SHA-256:
54f3c174ef3a07f172b7cce424710fb6a812d30474aab1402e34811cd829151c.
Preview http://127.0.0.1:8768/ now uses direct Python server PID 32844.
Existing user tabs were not refreshed and the JavaScript reference is unchanged.

Earlier attempts remain on disk. Status A had a zero-size synthetic pile record;
B's expected difference incorrectly assumed only one byte of an invalid u16 could
change. F/G compared integer loaded coordinates to floating resource coordinates;
normalizing the assertion fixed it without changing the already-correct bytes.
Web A/C exposed unreliable repeated file-picker opening from deferred Godot GUI
signals; B happened to pass. The final browser controls invoke the picker from a
native DOM click. D passes the full sequence; E additionally passes cancellation
and three repeated import/download cycles. Desktop uses the Godot native dialog.

Next: printing/download output and title/startup, including native missing-file
initialization. The current first-profile migration is documented as a seeded
export, not proof of the DOS missing-STATUS path. Original load-time RNG/timing,
interactive desktop dialogs and all previously tracked strict failures remain
unverified/open. The completion gate still targets the historical JS artifact
and must migrate to the Godot export before final acceptance. No issue is closed.


## Godot print output checkpoint — 2026-10-05

Godot print previews now provide F9 Save picture and Print picture controls. PNG export preserves all 320x200 pixels; browser printing uses the same bytes with original aspect, pixelated scaling and utility UI omitted. Desktop saves PNG through its file dialog and can open a standalone HTML print page. 47 production controls, 52 real Edge checks and 225 editor/rendering cases pass, including three full native score sheets. Repeated PNG downloads are byte-identical. Save interchange retains 22 browser checks; help/preferences 17; editor/nature controls 32/56; startup two native frames and 356 bounded SCR comparisons. All nine served files match immutable godot-print-web-build-a, PCK 9e474ebdc752c6a5c0c2639f8b0cbb7697e4b07093fe8a421c2038be70e3a6c3. Headless Edge emits beforeprint but leaves requests pending without afterprint; the verifier uses fresh documents, and interactive dialog completion/physical paper output remain unverified. The original configured printer backend is unavailable, so DOS physical-output/duration parity is not claimed. Title boot, native missing-STATUS defaults, interactive desktop dialogs and all earlier strict gameplay/timing/audio failures remain open.

The output utility is separate from the original artwork: confirm its printer
prompt, press F9, then Save picture or Print picture. Escape closes the utility
and another Escape dismisses the original preview. Nature exports the complete
320×200 screen, matching the original print rectangle, including facts and UI.
The pointer is omitted from the image sent to output.

Evidence: `godot-print-controls-b/report.json`, `godot-print-web-c/report.json`, `godot-print-native-a/report.json`, `godot-print-status-web-a/report.json`, `godot-print-preferences-web-a/report.json`, `godot-print-editor-a.json`, `godot-print-nature-a.json`, `godot-print-startup-a/report.json`, `godot-print-delivery-a.json`.

Earlier attempts remain preserved. Control A called the resident busy property
as a function in its test; B fixes that assertion and passes. Web A compared
animal fact text from independently timed runs and attempted multiple pending
headless print requests. A standalone page reproduces the missing afterprint
event even with a trusted click and a 2.5-second interval. Web B checks every
download pixel against two pointer-separated observations of its actual frozen
preview, and checks score pixels against independent renderer output. Its two
exit assertions ran before the engine processed queued keys. Web C waits for
those input frames and passes all 52 checks. Runtime code was unchanged between
Web A/B/C. No output screenshots are runtime inputs. Print-media screenshots were
visually inspected; these are not physical-printer or PDF pagination evidence.

Preview http://127.0.0.1:8768/ serves the immutable build through direct Python
PID 3028. User tabs were not refreshed. No issue is closed.

Next: Implement original title/startup paths and native missing-STATUS defaults. Verify interactive desktop file dialogs and browser printer-dialog completion. PNG/download/browser print dispatch are delivered, with physical output unverified. Keep board loss/Chip highlight, nature/robot room returns, maze tutorial, erase-dialog RNG, yard balloon, egg-route image and strict audio/presentation failures open. Migrate the completion gate to current Godot artifacts before final acceptance.


## Godot fresh-profile defaults — 2026-10-05

New Godot profiles now use the original missing-STATUS defaults: empty activity state and usage flags, first listening pages, original preferences/opponents/goals/sentinels, three normalized room objects and six distinct RNG-generated maze songs. Fresh startup no longer constructs and schedules temporary packaged-profile room objects before loading defaults. Existing STATUS bytes still restore and prior Godot profiles migrate. Two independent unchanged-DOS cold boots with only STATUS removed reproduce saved data and selected complete images (7 checks). A seed-controlled isolated Godot comparison passes 21 checks, including all 2282 settings/activity bytes, every active object field and the complete preferences panel. Real Edge passes 11 first-profile/reload/native-import checks. Existing save suite retains 81 checks, browser interchange 22, printing 52 (using a packaged-profile import through ordinary controls), and startup two native frames/356 bounded SCR comparisons. Nine served hashes match immutable godot-fresh-web-build-a, PCK 79219c560f8e7aa935ff9c517eebe6efbd41086d7d29ab1a2c08dcf53075c72b. Native session deadlines, inactive object records and complete cold-boot RNG/timing are outside this proof. Title boot/music and the missing-STATUS path with a lone existing SONGS file remain open; that file currently selects legacy migration to preserve older Godot creations. All earlier strict gameplay/audio/presentation failures remain open.

Evidence: `fresh-startup-native-c/run.json`, `fresh-startup-repeat-a.json`, `godot-fresh-startup-c/report.json`, `godot-fresh-web-a/report.json`, `godot-fresh-status-a/report.json`, `godot-fresh-status-web-a/report.json`, `godot-fresh-print-web-a/report.json`, `godot-fresh-startup-regression-a/report.json`, `godot-fresh-delivery-a.json`.

Native captures C/D remove only STATUS.DAT from the fixed-clock source archive;
all remaining game bytes are unchanged. F2/Escape makes DOS write its own file.
The whole first saved region matches in the seeded Godot component check. Native
object handles/deadlines and unused records are recorded separately and are not
claimed as equivalent. Browser checks compare every deterministic saved field,
then separately validate six distinct random choices and their exact history.
No capture supplies runtime state.

Historical failed attempts remain: native A/B required snapshot protocol 1 in
the new test, while the adapter uses protocol 2; C/D use the correct protocol.
Godot A initialized fresh state after a packaged-fixture startup, consuming extra
ambient random calls. B/C use the same empty resident construction as production
fresh startup, before default initialization. The actual Web export separately
verifies that production path. A fresh-data copy is retained before migration
tests alter the test host settings at shutdown.

The title research identifies TH palette60 with shapes61/62, palette70/SCR70
repeated at three executable-derived origins, and sound20200 before cue checks
for a/b/c/e and a two-pixel wipe. The current asset exporter omits MIDISND and
Godot only has the independent digital sample channel. Implement source-driven
sequence decoding and the music channel before claiming title timing parity;
do not replay captured audio or encode fixture timestamps.

Preview http://127.0.0.1:8768/ now uses direct Python PID29752. Existing tabs
were not refreshed. No issue is closed. The historical JS completion gate
remains failed and must migrate to Godot before final acceptance.

Next: Implement the original title sequence and its separate music channel from source data: overlay 5:0206, TH palettes 60/70, SCR70 at three source origins, MIDISND sound20200 and music cue waits before the wipe. Integrate title interruption, startup RNG and fresh/packaged/SONGS-only profiles. Fresh-profile defaults without older saves are now delivered and verified. Keep all earlier strict gameplay/audio/presentation failures, interactive desktop dialogs, printer completion and Godot completion-gate migration open.


## Godot title-logo checkpoint — 2026-10-05

Godot now boots through the original 64-color Broderbund logo, three SCR70
sparkles positioned by bottom/center, cue-e two-pixel presents reveal, separate
FM playback, final wait and keyboard/mouse/touch skip. MIDI and patches are
read from the pinned source; independent melodic driver rules generate OPL
writes for a standalone pinned DBOPL synthesizer. Captures are verification
fixtures, never runtime inputs. Godot builds verify the generated WAV manifest.

Evidence:

- `title-native-proof-a/report.json`: 119 checks. All 1,124 title FM writes,
  order and timer-interrupt positions match; all channel events, six cues,
  tempo steps and the active 128-patch bank match. Eight MIDI resources round
  trip byte exactly, with additional parser controls.
- `godot-title-d/godot.json`: nine startup/input checks. Its 82 distinct complete
  title frames match native boot frames in order.
- `title-midi-native-b` / `title-midi-control-a`: identical full callback
  timeline, native audio and selection RAM with/without read-only observers.
- `godot-title-web-a`: ten Edge export checks, 24 sampled title frames, automatic
  selection, three skip inputs and playable room entrance.
- `godot-title-fresh-web-a`: eleven fresh profile/reload/native-import checks.
- `godot-title-regression-a`: two native full frames, nine startup checks and
  356 bounded SCR regressions pass. Activity fixtures explicitly skip the logo;
  browser activity tests do so through ordinary Escape input.
- `godot-title-delivery-a.json`: all nine served files match the immutable
  `godot-title-web-build-a` export. PCK SHA-256:
  `f8d183ce85db39bd87c96bda6848073338b585b9c5bd0288c7fe284cc0e8f6bc`.

The original tempo handler reads its last two tempo bytes as a little-endian
word. That behavior, fixed-point division and fractional carry reproduce cue
IRQs 0, 205, 307, 512, 1036, 1532 without captured timestamps. Independent synth
builds B/C generate the same WAV SHA-256:
`bd48c58e46e1dc6a68c46f02d7bd834c8e28019303bfb467987ad8ea098d1ee7`.

Still open: the original pre-selection preview animation and looping music;
other FM tracks, pitch bend and rhythm patches; native mixer/output-waveform
parity and browser audio activation; partial redraws and unshifted presentation
timing; full startup RNG/profile integration, including SONGS-only saves; all
prior strict gameplay failures and Godot completion-gate migration. Writes
within an interrupt currently share a PCM sample boundary. No issue closes.
Live preview: http://127.0.0.1:8768/ (PID 37572).

Retained failed development runs: synth A lacked assembler PATH; title A called
a nonexistent animation cleanup method; B selected 16-color resources; C used
top-left instead of source bottom/center sparkle placement. D fixes those and
passes all complete-frame checks. Completion gate DK remains failed as expected.


## Godot selection-music checkpoint — 2026-10-05

Selection music MIDISND20000 now plays in Godot and loops its authored duration.
It continues during all three child entrance scripts and stops on room arrival,
following the original A83 cleanup. Digital effects have a separate player.
Sound-off silences the selection player without rewinding it; sound-on restores
output. This is functionally verified, not yet native mute/register equivalence.

The melodic FM model now includes source pitch-bend range handling, signed
semitone/fraction representation and table interpolation. Reset preserves the
original rotating allocation cursor. Complete title source events derive the
initial selection cursor; no observed register schedule is playback input.

Evidence:

- `selection-music-proof-b`: 33 checks. All 47,366 original selection register
  writes, values, order and timer-interrupt ordinals match; all 13,042 channel
  events match, including 776 bends; EOT is IRQ 36,432. The next loop's first
  2,972 writes also match. Source edge values and paired observer/control full
  timeline/audio/RAM equality pass.
- `godot-selection-controls-b`: ten controls covering title transition, PCM,
  loop extent, mute/unmute, digital/FM independence, child entrance and cleanup.
  Initial selection matches all 64,000 native pixels (first matching callback
  594). Both imported WAV streams match every generated PCM byte.
- `godot-selection-audio-web-a`: an actual Edge build runs through 155+ seconds
  without seeking or speeding up. Passive destination analysis verifies audible
  selection music after ordinary keyboard input, exact silence while muted,
  resumed output and audible playback after one full 151.782-second PCM loop.
- `selection-title-proof-b`: all 119 prior title checks still pass, including
  82 ordered complete native frames and 1,124 title register writes/IRQs.
- `godot-selection-title-web-a`: ten Web title/skip/room checks pass.
- `godot-selection-fresh-web-a`: eleven fresh-save/reload/import checks pass.
- `godot-selection-regression-a`: nine startup checks, two full native images
  and all 356 bounded SCR comparisons pass.
- `godot-selection-delivery-a`: nine served files match immutable export
  `godot-selection-web-build-a`. PCK SHA-256:
  `318ba0882ccfa630ff41db8eeed5a6e21209644df18cc14300e1871c2a04dc82`.
  Live preview remains http://127.0.0.1:8768/ (PID 13096).

Correction to the previous ledger: there is no separate visible pre-selection
preview animation to add. Main ACE..D0E draws the three first poses into a saved
screen and copies the finished selection screen. The existing Godot first poses
match that native screen. Timing of the native off-screen work remains open.

Godot defaults WAV imports to lossy compression. The new controls caught that;
both title and selection now explicitly import uncompressed, and asset generation
preserves this setting. Selection synth WAV SHA-256:
`8ff6e146e8b897c2180ff1fa258095ec4693da65517b6dbd1d867577db9764a2`.

Limits remain explicit: register/IRQ matching does not prove native wall-clock
audio timing or actual waveform equality. The native first selection playback
spans about 155.65 seconds between start/reset, while the source timer-based PCM
spans about 151.78 seconds; foreground/driver timing still needs integration.
Current PCM starts from a fresh synthesizer and repeats its first rendition;
retained oscillator/envelope state across interrupted logos and loop/track
boundaries is not reconstructed. Other FM tracks, rhythm patches, title audio
activation and focus handling remain open, alongside all prior strict gameplay
failures, printer checks, startup profiles/RNG and Godot completion-gate migration.
No issue closes.

Retained development evidence: the first 11,000-frame native/control captures
ended before the track completed; the 12,000-frame B pair covers the repeat.
Selection synth A had a shadowed output filename (its WAV bytes match B); the
unintended installed files were removed after hash verification. Controls A
caught compressed-import loop sizing; controls B verifies lossless imports.


## Godot activity music checkpoint — 2026-10-05

Godot now dispatches all remaining authored FM tracks (Home 20001 and frog 20100..20103) alongside the independent digital voice. Home sign and sleeping-child hotspot wait through source EOT and support interruption; incoming maze movement stops all channels at original overlay 1:7A93 while outgoing movement preserves accompaniment across the next entrance. All five imports retain exact generated PCM. Paired ordinary DOS maze capture/control timelines, audio and final RAM match; eight playback prefixes cover all four frog tracks with exact MIDI values/order/timer ordinals (66 combined native/component checks). Godot passes 48 activity audio controls, 66 maze controls, seven actual browser Home audio checks, ten title Web checks and startup/two full native frames/356 SCR checks. Full maze entry remains 45/46 images and 44/46 states with exactly the prior intro-05/15/25 failures. Nine served hashes match godot-activity-web-build-a at port 8768, PCK 87d6940b170922e351a246b0c1d9d437339041a43ba004dc7f36a4f177befd62. No full waveform, retained chip state or wall-clock equivalence claim; no issue closes.

Source correction: the frog accompaniment IDs are MIDISND, not DIGISND. The
original 89F7 selects 20100..20103; incoming walk 7A93 force-stops all channels,
while outgoing 7AA6 has no equivalent stop. Home calls at main 15B9 and 3E51
wait through completion/input and then stop all. Nonlooping WAVs include a
release tail, which is excluded from the gameplay EOT deadline.

Evidence:

- `activity-music-proof-a/report.json`
- `godot-activity-controls-a.json`
- `godot-activity-maze-controls-a.json`
- `godot-activity-audio-web-a/report.json`
- `godot-activity-title-web-a/report.json`
- `godot-activity-startup-a/report.json`
- `godot-activity-delivery-a.json`
- `godot-activity-maze-entry-b/report.json`: still FAILED overall; the same
  intro-05 RNG, intro-15 129 pixels and intro-25 RNG differences remain. All
  54 changed transfer frames match native order; digital source checks pass.
- `maze-midi-native-a` / `maze-midi-control-a`: ordinary full tutorial, piano
  return, reentry/interruption and final piano. Identical callbacks, WAV and
  final RAM; no guest patches. MIDI observation does not prove PCM waveform.

Native MIDI proof covers prefixes of the four frog tracks, not complete loops.
Home native waveform is still unverified. Fresh-chip PCM generation and first
loop repetition do not retain source oscillator/envelope state. Original mixer,
wall-clock pacing, mute registers and title focus/activation remain open.

Retained development failures: import A caught mixed GDScript indentation,
fixed before export; maze-entry A referenced a nonexistent fixture directory,
corrected in B. No acceptance thresholds were relaxed. Digital-only maze
verification now leaves FM starts explicitly unmatched rather than indexing
them as PCM samples.

Preview: http://127.0.0.1:8768/, server PID 38324, immutable build
`godot-activity-web-build-a`. Next: address the outstanding gameplay journey
failures, then integrate the remaining audio/presentation proof and Godot gate.


## Godot maze loading and cursor correction — 2026-10-05

Fixed missing cold instrument preparation in the Godot maze and its original busy cursor (overlay 1:97C9; audition 3BEF). The shared decoder-work/cache model now delays first playback, ignores input while loading and avoids repeating cached work. A seven-check regression fails three assertions before the fix and passes after. Full entry now matches all 46 checkpoint images (previously 45); 44/46 states still pass, with intro-05/25 early RNG timing remaining. Skipped tutorial retains all 19 images and 18/19 states. Native maze generation/victory passes 20 checks, static rendering 244, full controls 66, activity audio 48, startup nine controls/two full native images/356 SCR comparisons. Browser maze route passes 22 checks after importing the original packaged STATUS through ordinary UI; fresh-profile route separately passes 11. Native frog music starts remain early: first 3793 vs 3808, later 5160 vs 5191 and 5458 vs 5489 (later starts improved by 22 ticks). No timing equivalence claimed. Chip replay revalidated 49/49 states and 48/49 images; the remaining 312 pixels are the known partial clear. Money direct-payment resource-lifetime dependency remains open. Delivered immutable godot-maze-loading-web-build-a, nine served hashes verified, PCK d8c3ce7494850fbbf9ed66ab4533de4b491ba7982b19a3ad79c2da8c429e59d2.

Diagnosis correction: intro-15's 129 pixels were the mouse cursor, not the frog.
Original native image shows CURS1 while an instrument loads; the clone showed
CURS0. Native 3BEF calls 3DCC/97C9 before audition; 97D8 selects cursor1, 9842
loads the sample and 986C restores cursor0. The production queue now prepares
the instrument before starting its samples and exposes that loading phase to
the cursor renderer. Existing source-derived decode work is used; no recorded
per-track delays or checkpoint-specific RNG changes were added.

Evidence:

- `godot-maze-loading-green-a.json`
- `godot-maze-loading-controls-a.json`
- `godot-maze-loading-native-a/report.json`
- `godot-maze-loading-component-a/report.json`
- `godot-maze-loading-web-b/report.json`
- `godot-maze-loading-fresh-web-a/report.json`
- `godot-maze-loading-startup-a/report.json`
- `godot-maze-loading-audio-controls-a.json`
- `godot-maze-loading-delivery-a.json`
- `godot-maze-diagnosis-baseline-a`: repeatable original three failures.
- `godot-maze-loading-red-a.json`: three failing loading/input assertions.
- `godot-maze-loading-full-a/report.json`: still FAILED for intro-05/25 RNG;
  all 46 images and all 54 changed transfer frames now match.
- `godot-maze-loading-skip-a/report.json`: still FAILED for intro-05 RNG.
- `godot-chip-highlight-red-a/report.json`: still FAILED for partial clearing,
  312 pixels at step-15; all 49 state checkpoints and ending remain correct.

Browser attempt A used a fresh profile against the older packaged-song
expectation, failing three music score/portrait checks. Attempt B explicitly
imports the pinned original STATUS.DAT through F9/Load game and passes all 22
unchanged assertions. This test helper now accepts an optional status fixture
and records its hash. Fresh behavior is checked separately by the 11-check
fresh-profile browser suite. Both initial states remain covered.

No issue closes. Do not describe the remaining two RNG discrepancies as wrong
random sequences: the frog starts occur early, with the same selected tracks.
Do not hide the board failures: Money needs its generated resource-lifetime
dependency for the unused second coin preparation; Chip needs faithful partial
presentation. Source audit rejects fixed cursor offsets and injected seeds.

Preview: http://127.0.0.1:8768/, PID 40516, `godot-maze-loading-web-build-a`.
Next: continue unresolved gameplay/resource dependencies and migrate the
completion gate to the current Godot build without weakening acceptance.


## Godot completion gate migration — 2026-10-05

Migrated the default completion gate to Godot schema 2. All 59 ledger acceptance statements are indexed verbatim, with explicit review/evidence state; 15 required Web regression categories and 14 ordinary native journey categories cannot be dropped. The gate validates every exported file (including nested assets), current source inventory, result/verifier hashes, unchanged run bindings, complete ordinary native journeys, strict unshifted/unexcluded presentation, actual waveform/event timing, desktop evidence and all served hashes. Headless component checks cannot stand in for Web integration. The legacy JavaScript index is archived unchanged and requires explicit --html opt-in. 38 synthetic positive/rejection cases pass; fresh-profile browser 11 checks and maze browser 22 checks pass under new source/build-bound evidence envelopes. The native headless maze replay remains FAILED for two early RNG checkpoints and is explicitly component evidence. Fresh attested export is byte-identical to the existing served maze-loading build, PCK d8c3ce7494850fbbf9ed66ab4533de4b491ba7982b19a3ad79c2da8c429e59d2; nine HTTP hashes match. Completion gate dp correctly fails: known gameplay/timing/audio failures and missing integrated evidence remain. No issue closes.

New tools: `godot_completion.py`, `build_godot_release.py`,
`run_godot_evidence.py`, `verify_godot_completion_gate.py`.
`completion_status.py` now defaults to Godot; the old gate remains available
only for explicitly requested historical JS evidence. The original index is
preserved byte-for-byte as `completion_verification.legacy-js.json`.

Evidence:

- `godot-gate-build-a/build.json`: source inventories unchanged across export;
  whole-export fingerprint
  `8678ebaa63e6d4537b2c73dd6afc7b87e3daefc9607449608ee1b51150ee8c32`.
- `godot-gate-tests-d/report.json`: 38 gate-mechanics cases; synthetic fixtures
  establish validator behavior, not game fidelity. Earlier A/B/C retained.
- `godot-gate-tests-envelope-d/evidence.json`: exact gate/verifier files bound
  to the source/export, covers TH-007 acceptance 1 only.
- `godot-gate-fresh-envelope-a` / `godot-gate-maze-envelope-a`: actual exported
  browser checks, 11 and 22 checks respectively. Bounded coverage remains stated.
- `godot-gate-native-maze-envelope-a`: expected failure, two RNG differences;
  its headless comparison cannot claim actual Web native-journey coverage.
- `godot-gate-delivery-a.json`: all nine served files match the attested export.
- `completion-gate-dp.json`: FAILED as required. Three retained reference
  requirements and the gate-mechanics requirement are reviewed; other pending
  rows are unproven integration claims, not a count of unimplemented features.

The gate preserves all strict requirements and known failures. Hashes validate
identity, not semantic sufficiency: the final completion audit must still
inspect whether each report really proves the associated acceptance text.
Do not bulk-mark the pending rows reviewed from passing component results.
No runtime behavior changed in this checkpoint; the existing preview remains
http://127.0.0.1:8768/, PID 40516, byte-identical to the new attested export.

Next: return to unresolved gameplay/resource and timing causes. Complete
ordinary-input export journeys and native audio/presentation evidence are still
required; gate migration itself does not establish completion.

## Godot room activity completion fixes - 2026-10-05

Two reproducible failures are resolved in the Godot runtime:

- The held egg journey's final frame was 791 pixels different while its object
  and RNG state matched. The cloud was one pixel behind: room updates ran before
  resident task completion, and a following activity could make the resident
  busy again before the next tick. The resident idle boundary now services the
  same due-gated cloud update as the room loop, before choosing another action.
  This matches the recovered room loop and preserved reference implementation.
- Chalk erase confirmation omitted the original main 16F2 call to BC43 after
  either answer. BC43 schedules the next ambient action using one random(10)
  draw. Both decline completion and actual accepted board-clear completion now
  schedule that action. Existing calendar-close initialization remains intact.

Red evidence: `godot-egg-diagnosis-a` (3/4 full images, 4/4 states) and
`godot-erase-diagnosis-a` (24/24 images, 19/24 states). No recorded delays, seeds,
frame substitutions or fixture coordinates were added to the runtime.

Green, bound to `godot-room-idle-build-a/build.json`:

- `godot-room-idle-egg-b`: all four native checkpoint images/states.
- `godot-room-idle-room-b`: all 24 native checkpoint images/states.
- Both replays additionally compare cloudX where the original report provides
  it. They start from one native fixture and replay ordinary recorded inputs;
  image membership within an input interval is not strict presentation timing.
- `godot-room-idle-input-a.json`: 12 input checks.
- `godot-room-idle-care-a.json`: 22 ordinary mouse/touch care checks.
- `godot-room-idle-web-b`: 22 actual Edge export checks with the original
  packaged profile imported through the file chooser.
- `godot-room-idle-fresh-b`: 11 actual Edge fresh-profile/reload/import checks.
- `godot-room-idle-gate-a`: 38 synthetic validator checks, not game fidelity.
- `godot-room-idle-delivery-a.json`: all nine served export hashes match.

Live preview: http://127.0.0.1:8768/, server PID 2324. Export PCK:
`3e52eceab04c8f40b09693a4229c1cf399c7abb418fe4ee6b5503cb8f8f2c400`.
The former `music_erase_rng` failure was room chalk, not the songbook editor.
These two failures moved to resolved history; the broader TH-009 remains open.
The separate short-egg balloon timing limitation is not claimed resolved.
`completion-gate-dq.json` still fails for seven known journey discrepancies and
required native presentation/audio and integrated browser/desktop evidence.
No issue or goal was marked complete. Next: room-return balloon causes and
resource-dependent Money payment preparation, alongside remaining integration.

## Missing STATUS with retained SONGS - 2026-10-05

The original fresh-start capture (`fresh-startup-native-c`) removes only
`TheTreeh/status.dat`; it explicitly retains `TheTreeh/songs.dat`, SHA-256
`b4a1aa95cf0fef83076b303ce8c3ceb9676fbcf05a715e45a0f83e9d33c3643b`.
The Godot migration predicate incorrectly treated that original DOS song file
as evidence of an earlier Godot profile and substituted bundled-profile state.
Only the four earlier JSON saves now select legacy migration. SONGS alone
receives original missing-STATUS settings without modifying its song payload.
The native personal-page loader 7AFB reads SONGS independently of usage flags;
retaining the separate records with initially clear STATUS flags is intentional.

Regression evidence under `testing/output/treehouse/`:

- `godot-songs-only-red-a/godot.json`: four new component assertions fail.
- `godot-songs-only-web-red-b`: the previous delivered export fails three of
  13 checks (settings, usage flags and one room object), with no browser errors.
  Earlier red A also recorded a fixture-page favicon 404; B removes that
  fixture artifact by serving a dedicated blank storage page.
- `godot-songs-only-fresh-b`: 26 component/native-default checks, including
  retained song bytes, full 2282-byte saved region with fixed seed, JSON legacy
  migration and STATUS reload. The initial fixture seed is explicit.
- `godot-songs-only-cold-web-b`: 13 actual Edge startup/reload checks. Ordinary
  file import prepares the song file; while Godot is unloaded, a disposable
  IndexedDB profile has STATUS/legacy JSON removed. This is a documented
  storage fixture, not an ordinary-input native gameplay journey. All later
  reads and reloads use the unmodified exported game and F9 controls. Song
  bytes, deterministic defaults, object fields and chooser invariants pass.
- `godot-songs-only-fresh-web-b`: existing 11 fresh-profile checks pass.
- `godot-songs-only-status-b`: existing 81 save-format checks pass.
- `godot-songs-only-status-web-b`: existing browser file interchange passes.

The current yard and nature replays (`godot-yard-return-current-a`,
`godot-nature-return-current-a`) reconfirm the one-step final balloon geometry
failure, with all 24 and 14 checkpoint images respectively present. This is
consistent with previously measured early room rebuilding, not evidence for
changing balloon movement cadence or inserting a captured fixed delay.
These timing failures remain open.

Delivery: `godot-songs-only-build-a/web`, PCK
`c4403fe860cdbde2d9039a920e0e9fd29370158a1a9fa4fb159291f7d185fd50`,
served at http://127.0.0.1:8768/ by verified server PID 8096. All nine served
files match the manifest. Browser interchange and room/music/maze route each
pass 22 checks. `completion-gate-dr.json` verifies current source/export identity
and delivery but remains failed for outstanding requirements and seven known
journey discrepancies. TH-014 and the goal remain in progress.

## Real browser title/focus checks and held-note fix - 2026-10-05

A held piano note continued sounding after switching tabs. The runtime handled
`NOTIFICATION_APPLICATION_FOCUS_OUT` but omitted
`NOTIFICATION_WM_WINDOW_FOCUS_OUT`. Both now invoke the same existing input
release/save path. This is browser input ownership, not a change to original
music rules or timing. Godot's [4.6.1 Web display implementation](https://github.com/godotengine/godot/blob/4.6.1-stable/platform/web/display_server_web.cpp#L1171)
registers window-focus notifications; its window-blur callback also clears the
engine's pressed events. The game has its own held-note state to clear.

Evidence under `testing/output/treehouse/`:

- `godot-title-focus-a` exposed harness assumptions (single-page context and
  autoplay expectation). B/C/D did not establish actual tab blur: Playwright
  focus emulation must be disabled after navigation/renderer replacement.
  These failed reports remain intact and do not prove a runtime focus bug.
- `godot-title-focus-e` uses real headed Edge tabs, confirms document focus
  false while away, true on return and actual blur/focus events. The old export
  fails only held-note silence; post-return output peak remains about 0.34.
- `godot-window-focus-red-a.json`: production selection/music/key-down/window
  notification regression fails held-note cleanup before the source fix.
- `godot-window-focus-input-a.json`: all 49 production input checks pass after
  the fix, including both application and window focus loss.
- `godot-window-focus-title-a`: all 25 actual-browser checks pass. Ordinary
  title completion, keyboard/mouse/touch interruption, activation audio,
  title focus return, room/piano entry, held-note release and replay work.
  The same post-focus destination analyser now reads zero; replay is audible,
  and ordinary release returns to zero. No synthetic blur event is dispatched.
- Existing browser checks pass: status 22, fresh profile 11, retained-SONGS
  cold-start fixture 13, room/music/maze 22. Total browser checks: 93.
- `godot-window-focus-gate-a`: 38 validator checks, not game fidelity.

Autoplay was running on this host despite the requested launch policy. That
observation is retained; a denied/suspended autoplay context is not claimed
verified. OS minimization, mobile suspension, exact native title presentation
and waveform/event timing remain open. The analyser proves audible output and
silence, not DOS waveform equivalence. Title screenshots sample the recovered
frames sparsely, not every native video presentation.

Immutable delivery: `godot-window-focus-build-a/web`, PCK
`fc357753f3d1718d3d604faa705b0a37d54f0b4161df139e0f9fc4ac5e00ae3d`.
All nine HTTP files match the bound manifest, served at
http://127.0.0.1:8768/ by PID 29248. `completion-gate-ds.json` remains failed for
seven known journey discrepancies and missing full fidelity/integration
proofs. TH-015 and the overall goal remain in progress.

## Godot display scanout delivered — 2026-10-05

The Godot runtime now commits its independently rendered framebuffer to a
four-band VGA presenter. Periods come from the pinned reference implementation:
800 dots per line at 25.175 MHz, 400 visible physical lines, four 50-row logical
bands. The previous mode-3 vertical period survives the reference's timing-change
threshold. Delays use float32 precision, matching PIC_AddEvent. Runtime drawing
does not read native images or recorded timestamps.

Each logical update produces a framebuffer commit, including updates batched
within one host callback. The presenter owns snapshots, reads bands in order,
and sends completed displays to the same texture used by the browser. Original
drawing/loading work and absolute native video phase remain unimplemented;
this change alone does not establish strict timing fidelity.

Evidence under `testing/output/treehouse/`:

- `godot-scanout-native-b`: all 306 native question-animation callbacks match;
  whole-frame sampling matches 291. This component test explicitly supplies
  native clock fixtures and existing independently generated JS-reference
  source images. It proves the Godot presenter, not Godot gameplay timing.
- `godot-scanout-presenter-c.json`: six snapshot/ownership/boundary checks.
- `godot-scanout-batching-a.json`: five production `_process` checks; all 280
  title presentation hashes and timestamps agree between small host callbacks
  and one-second batches (15 distinct images).
- `godot-chip-scanout-observe-a`: all 49 gameplay/RNG checkpoints and 48 images.
  The 312-pixel step-15 failure remains. Four diagnostic old/new band composites
  each match that image exactly; they are not actual game presentations.
  See `godot-chip-scanout-phase-a.json` and the Chip journey document. Do not
  insert an artificial clear stage or fit a phase offset to make the test pass.
- Input component 49 and completion-validator 38 checks pass.
- Browser title/focus 25, status interchange 22, fresh profile 11 and retained
  SONGS cold startup 13 checks pass. Room/music/maze run B passes all 22 checks.
  Run A, alongside the title browser run, failed at the squirrel throw and
  later navigation. The unchanged candidate passes alone and the old export
  passes the concurrent control. The cause is unproven; this is retained as
  an additional intermittent Web integration failure, not closed by the retry.

Delivery: `godot-scanout-build-a/web`, build fingerprint
`570e7c2ffe7e2242043022a996d255e112df4461dbd10977acd3c44aa15466cc`,
PCK `53ba992ba07f24c0501af82f80d363bd580fc3e305fc187844580e8e33dae675`.
All nine served files match at http://127.0.0.1:8768/ (PID 12088).
`completion-gate-dt.json` confirms build/source/delivery identity but fails
completion, retaining seven native journey discrepancies plus the intermittent
browser route. No acceptance requirement or issue was newly marked complete.

## Resume and browser-wait correction — 2026-10-13

The test batch interrupted by the requested pause finished successfully. Its
source, export, verifier and result hashes remain valid. The full exported
room/music/maze route passes all 22 checks (`godot-scanout-maze-c`); title/focus
passes 25 (`godot-scanout-title-b`).

The squirrel failure was reduced to the first eleven browser assertions. Eight
concurrent runs across the old and new exports passed without forced stalls.
A controlled 900 ms browser main-thread stall during the nut flight then
reproduced both failed assertions on **both** exports: landing was not yet
visible, and the next exit click arrived while the flight owned input.
Evidence: `godot-hollow-stall-red-a/{scanout,window-focus}`.

The functional verifier now waits for the exact native landing region before
continuing, then waits for the yard and room regions. It retains bounded
timeouts and reports actual sample counts/waits. Both controlled cases pass;
landing took 2.27 and 1.72 seconds, exceeding the former fixed 1.2-second wait.
The unchanged current export also passes the bound eleven-check stalled route
(`godot-hollow-stall-bound-a`) and the full normal route alongside title checks.
No runtime source, native checkpoint window or native timing assertion changed.

This resolves the reproduced functional-verifier fault. The original
spontaneous run had no frame-gap logging, so its precise scheduling cause is
an inference, not a recorded fact. Its failed artifacts remain intact. Seven
native gameplay/timing discrepancies and the broader integration requirements
remain open. The preview was restored from the same immutable scanout export
at http://127.0.0.1:8768/; all nine HTTP hashes match (PID 33980).

### Additional activity coverage on the same export

Five previously unbound browser categories now have current evidence under
`testing/output/treehouse/`:

- `godot-resume-oct13-board-b`: 21 checks covering both modes, options, dice,
  original car sprites, legal movement, mode persistence and room return.
- `godot-resume-oct13-theater-a`: ten entry/edit/performance/reload/return checks.
- `godot-resume-oct13-nature-c`: 23 collage, animal facts, day/night, reload,
  quiz-dealing/question and telescope/replay/return checks.
- `godot-resume-oct13-preferences-a`: 17 help/preferences checks.
- `godot-resume-oct13-print-a`: 52 preview, PNG download and print-layout checks.

Board A and nature A expected settings from the original packaged profile,
although their actual browser contexts had fresh profiles. The native fresh
save and Godot's persistence loader specify friend opponents, no selected
animal category and help off. Board B explicitly selects the robot through the
original checkbox. Nature C selects the insect class and robot through ordinary
input before retaining the original pixel assertions. Nature B remains failed:
its readiness check could see the old room cursor before nature appeared, and
its extra help toggle disagreed with the reference. C observes the nature
controls first and preserves help off. The game source was not changed.

These 123 passing checks are bounded Web integration evidence, not complete
native journeys or timing/waveform proof. Print checks retain their limitations:
no physical paper comparison and no claim of completed interactive printer
dialogs. The current completion index binds all five results to the unchanged
scanout source/export. No issue or acceptance row was marked complete.

### Money loss replay refreshed

The unchanged current Godot build still matches 12 of 33 images and 11 of 33
complete states on the native losing Money route. At step-10 the image matches,
but RNG is 2527103840 instead of 2204794019; later turns diverge and the losing
ending is not reached. The resource-dependent second coin preparation remains
open. Reports: `godot-resume-oct13-money-loss-a/report.json` and its bound
`godot-resume-oct13-money-loss-a-envelope/evidence.json`.

## Godot allocation and ownership port — 2026-10-13

The recovered allocation semantics now have GDScript implementations in
`resource_heap.gd`, `resource_near_heap.gd`, and `resource_memory.gd`. They
implement first/last-fit allocation, forward packing, handle relocation, near
allocation with explicit growth limits, locking, promotion, resize, discard,
raw/handle ownership transfers and catalog backlink cleanup. No CPU instruction
accounting or captured address schedule was added.

- `godot-resource-heap-b/report.json`: 402 passing checks. All 52 original
  preparation operations and both cursor-moving packing operations match,
  preserving payload hashes, block geometry, handles and search cursors. The
  operations make 171 moves in total. A continuous near-heap replay matches
  all 104 checkpoints and 237 allocation returns through 206 frees. Six focused
  checks cover padding, locking and bounded growth.
- `godot-resource-memory-c/report.json`: 668 passing checks. From one initial
  fixture, all 104 complete near/far structures and active/static handles match
  through 159 far allocations and 43 raw frees. Return-pointer assertions and
  eight focused ownership/resize checks also pass.

The fixtures are hash-checked original RAM and observed semantic operation
requests, used only by offline test drivers. This establishes the port of these
components; generated live resource requests and a complete payment replay
remain required. The game does not call these modules yet. The preview remains
`godot-scanout-build-a`; the current source inventory has advanced beyond that
export, so its browser evidence must not be described as testing these changes.

Retained attempts: `godot-resource-heap-red-a` used the wrong reference filename;
`godot-resource-heap-red-b` reports the missing Godot modules before implementation.
The first ownership run matched every memory state but its final empty-stack
assertion failed: the native window ends after preparation, inside one raw
allocation. The corrected assertion requires exactly that pending raw allocation;
its subsequent far allocation and return are present just beyond the observed
window. `godot-resource-memory-a/report.json` preserves the failed assertion.

Next: port generated startup/catalog loading into these Godot components, then
generate board redraw ownership and connect the live payment dependency. The
seven native fidelity discrepancies and all strict timing/audio requirements
remain open.

## Generated Godot startup resources — 2026-10-13

The allocation port now has a generated starting state. New Godot modules model
DOS conventional allocations and growth, startup near allocations, cached source
resources, archive directories, font/cursor conversion, saved surfaces, direct
raw copies, and digital-sound preparation. `resource_startup_assets.gd` composes
these through all seven startup archives and the retained initial sound.

`resource_startup_inputs.py` extracts the inputs from the pinned original EXE and
DAT bytes plus the documented DOS/Sound Blaster launch profile. The normal
`build_godot.py` now includes this compact base64 transport in
`original.json.resource_ownership`. No captured RAM, allocator addresses, call
stream, CPU instruction counts or native elapsed times enter this generation.

Evidence under `testing/output/treehouse/`:

- `godot-resource-startup-e/report.json`: all 108 checks pass using the normal
  generated asset bundle. This includes 98 native boundary-field comparisons
  (complete arena/near/DOS state, active payload hashes, files and catalog entries),
  five boundary-count checks and five focused cache/conversion checks. Native
  boundaries are comparison outputs only.
- `godot-resource-startup-d/report.json`: all 108 checks pass with direct source
  extraction; the normal bundle exercises the same production `from_data` entry.
- `godot-resource-memory-d/report.json`: all 668 continuous ownership checks
  still pass after the startup integration within the resource modules.
- `godot-resource-startup-assets-a.log`: normal resource generation succeeds,
  retaining all 2,337 shapes and 356 scripts. Asset bundle SHA-256:
  `57a482dfbd65ef1f52a51a4c80ab1a83ea2411e19c72c5f66e8d06b441474f2b`.

Early attempts A/B retain Godot identifier collisions (`Font` and global
`convert`) and their compile failures. They were renamed; no native mismatch
was waived. Attempt B's specific failed Godot child was stopped after its
compilation errors; the successful later runs exited normally.

This resource startup is still separate from the playable event loop. Title,
selection, room and board lifetime hooks remain required before its cursor
address can drive payment preparation. The preview still serves the previous
scanout export, and completion correctly fails because source has advanced as
well as because gameplay/timing/audio work remains open. Next is porting
palette, shape and animation ownership through the existing native title
boundaries, then continuing to board gameplay.

## Godot scene ownership through board options — 2026-10-13

Added GDScript palette/shape/animation ownership and lifecycle modules for the
title, child selection, initial room, board transition and initial board/options
construction. The normal source extractor now includes the original EXE palette
masks, rectangles, SCR code and child archives used by these modules. Palette
byte updates explicitly preserve Godot PackedByteArray copy-on-write semantics.

The sequence generates requests from these source structures and current game
fields. It releases saved character backgrounds, animation objects, temporary
screens, sound locks and source-cache links at the corresponding semantic
boundaries. Board transition display/sound/callback events come from the actual
Godot SCR interpreter: the ring completes 18 displays; the bubble completes 13
displays, sounds 10034/10035 and callback [0,0]. Initial board layout is produced
by the actual Godot BoardGame rules.

Evidence under `testing/output/treehouse/`:

- `godot-resource-board-c/report.json`: **377 checks pass**, including all 366
  native allocator/DOS/catalog/source-payload comparisons through initial Money
  options, and 11 gameplay/interpreter/ownership checks. Uses the normal asset
  bundle for both resource metadata and board tables.
- `godot-resource-room-girl-b/report.json`: **209 checks pass**, including all
  204 native comparisons through girl selection and room construction, and
  five ownership/cache checks, also using the normal asset bundle.
- `godot-resource-startup-f/report.json`: all **108 startup checks** remain
  passing after the shape/catalog integration.
- `godot-resource-scene-assets-a.log`: normal asset generation succeeds with
  all 2,337 shapes and 356 scripts. Current asset SHA-256 is
  `a83014cbf1c508a975dfaed72b5451fab8ebf561b9b519ba9e51d14f8cbd1fb1`.

Earlier passing title/room/transfer checkpoints remain as
`godot-resource-title-boy-a`, `godot-resource-room-boy-a`,
`godot-resource-transfer-a`, `godot-resource-board-a/b` and
`godot-resource-room-girl-a`. They cover intermediate versions or direct
extraction; the current reports above bind the final source and normal assets.

Limits: these are headless resource ownership comparisons at semantic completion,
not live browser gameplay or elapsed-time proof. The route supplies cloud 5,
two visible credit changes, noon, the five source-defined room objects, and one
native RNG seed at board entry. Those are explicit test inputs; they must not
become runtime fixture schedules or seeds. Converted shape/surface pixels remain
the graphics decoder's responsibility and are outside these resource comparisons.
The modules are not yet hooked into the playable event loop. The preview remains
the prior scanout build; full completion and its source/export check still fail.

Next is generating board start, turn, sound and redraw resource events after
options dismissal, then connecting the live lifecycle and deriving the payment's
cursor-dependent second amount. The full losing Money replay, seven native
discrepancies, timing and waveform work remain open.


## 2026-10-13 — Godot board options to first-turn readiness

The source-generated Godot resource chain now continues through Play: the click
sound, preference dismissal, fresh board draw, pawn saved background, dashboard
animation and three opening prompt flashes. Board start uses the production
BoardGame preparation and continues its RNG without reseeding. Dashboard sound
comes from the production SCR interpreter. Click completion is an explicit
caller event, as are animation completion and each prompt draw; this component
comparison does not claim an elapsed-time implementation.

Evidence under `testing/output/treehouse/`:

- `godot-resource-play-c/report.json`: **415 checks pass**, including 402 native
  allocator/DOS/catalog/modeled-payload comparisons and 13 focused, interpreter
  and gameplay checks. Uses the normal generated asset bundle.
- `godot-resource-startup-g/report.json`: **108 startup checks pass** with that
  same bundle.
- `resource-board-play-controls-a.json`: **468 checks pass** comparing the Play,
  restart, redraw and dashboard observers against the plain control. Ordinary
  PNG/WAV/RAM files, callback timelines and input/source metadata agree.
- `resource-board-play-a`, `resource-board-restart-a`, `resource-board-redraw-a`,
  `resource-board-dashboard-a`: new paired original snapshots, obtained by
  restoring the existing fixed-clock options state and clicking Play normally.
- `godot-resource-play-a/report.json`: preserved failing first candidate. Its
  three failures were the click sound's lock bit, which the original releases
  during the button flash. The corrected model exposes sound completion to its
  caller. `godot-resource-play-b/report.json` preserves the intermediate pass.
- `godot-resource-play-assets-a.log`: normal asset generation retains all 2,337
  shapes and 356 scripts. Asset SHA-256:
  `032f0d9a81ac39c473dc5bc35d9c17f1ce9184270a8fb51c4997513f12bb78a8`.

Limits: one board-entry seed and room/credit/sound completion semantic inputs
remain explicit fixture inputs. Converted surface pixels, live lifecycle,
absolute frame timing and audio waveform parity are not proved by these checks.
No native discrepancy or issue was closed. The preview still serves the prior
scanout export. Next: roll/movement/landing/payment lifetimes, live integration,
then the full losing Money replay and a fresh playable export.


## 2026-10-13 — First roll, restored button flash and refreshed preview

The Godot board now reproduces the original question-mark button flash before
rolling: red for 12 ticks, white for 12 ticks, then eight faces at their authored
6-through-13-tick intervals, followed by three 12-tick pawn blink pairs. The
new production events drive the resource model's prompt surfaces and saved
pawn image. Starting from the existing generated startup/board chain and its
one entry seed, the roll result and final RNG agree without reseeding.

`godot-resource-roll-c/report.json` passes **443 checks**: 426 native resource
boundary comparisons and 17 gameplay/interpreter/focused checks. The first roll
matches native relative PIT ticks for every prompt draw and all nine sound
dispatches, completing at tick 172. This is logical-event evidence; absolute
scanout timing and audio waveform parity remain open. The original observers
match their ordinary control in **230 checks**. An initial candidate's closure
ownership leak is preserved in `godot-resource-roll-a`; weak ownership fixed it,
and attempts B/C terminate cleanly.

The new `godot-roll-build-a` Web export passes **21 browser checks** across
Money and Chips: options, roll, legal movement, persisted mode and room return.
The resource test and Web test have build-bound evidence envelopes. All nine
served files match the immutable export at http://127.0.0.1:8768/ (PID 6764).
PCK SHA-256: `b1f96ec656ea3d6dc6832210ae31d3f6879250be1ea08feeb0294cb2ac1927fd`.

`godot-roll-money-loss-a/report.json` retains exactly the previous checkpoint
pixel counts and state differences: 12/33 images, 11/33 states, first RNG
mismatch at step-10, losing ending not reached. No issue was closed. Resource
lifecycle integration, movement/landing/payment lifetimes and seven native
failures remain open. Prior suite results need refreshing on this export.

Automatic approval review rejected the bulk completion-index replacement
without a detailed reason. The existing index was preserved; the new export,
hashed evidence and remaining work are recorded in
`testing/treehouse/roll-build-progress.json`. The remaining-work ledger points
to that record. No acceptance was promoted or historical evidence discarded.
