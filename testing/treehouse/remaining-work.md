# Remaining Treehouse work

The active objective is a faithful independent reconstruction, then improvements.
The issue ledger is [`remaining-work.json`](remaining-work.json). Work continues
through it without asking the user to authorize each component.

## Latest Godot checkpoint — 2026-10-13

All main activities are playable in Godot. The current preview is
http://127.0.0.1:8768/ (`godot-scanout-build-a`). Its new VGA display presenter
passes 306 native callback comparisons with explicit clock fixtures and
preserves 280 title displays across host callback batching. Complete native
gameplay timing is still unproven. The Chip replay still matches 49 gameplay
states and 48 of 49 images; the remaining mixed-band image needs correct timing.

The browser suites have passing runs for startup/focus, save interchange,
fresh and retained-song startup, and room/music/maze navigation. Five further
categories now pass 123 checks on this same export: board games, theater,
nature/telescope, help/preferences and print output. The checks recreate older
reference settings through ordinary UI where fresh defaults differ.

The squirrel test's fixed wait was replaced with a wait for the exact landing
image after a controlled browser stall reproduced the failure on both exports.
Runtime timing was unchanged. Seven native journey discrepancies remain open,
along with complete native presentation/audio and other integration proofs.
The latest full gate remains failed. Earlier sections below are historical
checkpoints; the JSON index identifies current bound evidence.

## Godot delivery correction â€” 2026-10-05

The required runtime is **Godot**, matching the Word Rescue and Math Rescue
projects. Browser delivery means a Godot Web export. The JavaScript build is
preserved as a reference during the port. It is not the final runtime.

The initial project is in `treehouse-godot/`. Its two checked full frames match
the DOS reference, both character entrances work, and all 356 SCR scripts match
11,512 bounded interpreter events in the JS reference. An exported Godot game
also passes a real Edge input/entrance smoke check. These were foundation checks. The later room checkpoint below adds calendar,
clock, environment and chalk interactions; activities remain unported.

| Issue | Required migration |
|---|---|
| TH-008 | Godot graphics, SCR interpreter, startup, RNG |
| TH-009 | Room, yard, hollow, character, objects, transitions, rewards |
| TH-010 | Instruments, songs, songbooks, musical maze |
| TH-011 | Sentence theater |
| TH-012 | Nature browser, collage and guessing game |
| TH-013 | Money and Chip board games |
| TH-014 | Saves, help, preferences, printing |
| TH-015 | Input, rendering and strict timing verification in Godot |
| TH-016 | Godot audio integration and native comparisons |
| TH-017 | Verified Godot desktop and Web delivery |

TH-007 depends on these items. Historical browser evidence remains useful but
cannot establish completion of the Godot runtime. Next: room state, interactions
and activity transitions, then the complete music activity.

## Existing fidelity work

| Issue | Work | Acceptance focus |
|---|---|---|
| TH-001 | Deterministic reference snapshots | Repeated pixels, PIT clocks and audio |
| TH-002 | Resource and drawing time | Costs and intermediate states derived from original operations |
| TH-003 | Runtime scanout integration | All 984 unshifted nature callbacks; no regression |
| TH-004 | Shared random call order | Ordinary journeys across activities |
| TH-005 | Audio output | Native event timing, mixer and waveform comparisons |
| TH-006 | Remaining path coverage | Finite activity/transition/interruption/save matrix |
| TH-007 | Verified delivery | One immutable build and matching served file |

Current statuses and hashed evidence are maintained in the JSON ledger. Run:

```powershell
python tools/treehouse/completion_status.py
```

Exit code 1 means required work remains. Gameplay regressions, isolated timing
fixtures and frame membership cannot satisfy strict integrated completion.

## Current working sequence

### Held piano input correction delivered, 2026-09-29

Candidate `a89b3f65ac50` defers idle animation while notes are held and interrupts it on new input. All 17 native held-key/interruption image and gameplay/random checkpoints pass, as do 30 short-note and 22 authoring/playback checkpoints. All 89 suites and 183 environment states pass. Previous held-piano milestone: `a89b3f65ac50`. Strict fidelity failures remain open. See [held input evidence](../treehouse_piano_held_input.md).


### Theater caption correction delivered, 2026-09-29

Candidate `fe0819316c49` keeps the old sentence visible until both word tokens finish swapping. It restores 39 complete original images across shuffle and manual dragging, without losing any previously matching original image. All 88 regression suites and 183 environment checks pass. Previous theater caption milestone: `fe0819316c49`. The 232 intermediate theater images and strict timing failures remain open. See [caption evidence](../treehouse_theater_shuffle_caption.md).


### Maze adaptive difficulty delivered, 2026-09-29

Previous maze difficulty milestone: `2d29766c93dd`. Difficulty now survives exits and reentry in both directions. All 87 regression suites pass on the delivered build, including 12 new desktop/touch difficulty checks. All 183 environment states pass. The paired activity tour retains the same five image and ten room-object mismatches, with final maze reentry matching. All 58 observed tour sounds match sources/rates between inputs. Strict timing remains failed. Other supplemental comparisons retain their previous-build hashes and are explicitly historical, not newly verified. See [maze difficulty evidence](../treehouse_maze_difficulty.md).

### Activity-tour fixes delivered, 2026-09-29

Previous board/piano milestone: `9a67a26e9613`. Delivered original temporary listening-key notation, original tempo hit boundaries, and board preparation before options. Board entry preserves imported player levels until Play. Both maze treehouse exits retain 14/14 matching images and their six known balloon timing mismatches.

All 86 registered suites pass on one immutable build; all 183 environment states pass. The 23 additional comparisons retain their previous outcomes. All 30 piano checkpoints match RGB and music state. The activity tour matches 22/27 images and active gameplay/random state throughout; ten room-object timing mismatches and five image mismatches remain failed. All 58 observed tour sound sources/rates match between player inputs; exact sound timing remains open. See [activity-tour evidence](../treehouse_activity_tour.md).

### Maze global exit correction delivered, 2026-09-29

Following the user's renewed concern about CPU-level detail, prioritise concrete
navigation, progression, persistence and visible/audible defects. Retain strict
timing failures as evidence; do not pursue instruction equality as a deliverable.

Candidate `8a107c9eb4a9` corrects the maze's top-right treehouse exit, which
previously went to the piano. It now returns through the parent music activity's
room transition. All 14 native screen checkpoints match. The strict navigation
report still fails on object-state timing at six checkpoints; this is not full
parity. Seven ordinary mouse/touch winning exit/reload journeys pass 53 checks;
the previous live build fails both newly covered treehouse exits.

Evidence: `maze-navigation-fixed-a/report.json`,
`maze-navigation-exit-a/report.json`, and
`maze-navigation-exit-baseline-a/report.json` under `testing/output/treehouse/`.
All 85 registered suites pass in one immutable-build batch, including 53 ordinary maze exit/save/reload checks. All 183 environment states pass. The 23 additional comparisons retain prior outcomes. Both new maze exit replays match all 14 RGB images and preserve destination, random state and song history; six balloon-state timing mismatches per route remain explicit failures.

Previous maze navigation milestone: `8a107c9eb4a9`. Continue the finite player journey
matrix; existing full-fidelity requirements remain open. See
[maze exit evidence](../treehouse_maze_global_exit.md).

### Delivered piano/maze transfer, 2026-09-29

Previous piano/maze transfer milestone: `57b4673bf421`. Original smoke and child bucket
animations now connect piano and maze. Both full/skip routes match all 62
transfer frames and stable tutorial/return/reentry states. All 85 suites and
183 environment states pass. Full entrance cursor/timing and previous fidelity
gaps remain open. See [transfer evidence](../treehouse_maze_entry_transfer.md).

### Delivered maze hint input, 2026-09-29

Previous maze input milestone: `032490fa50b5`. Correct sign clicks during automatic
hints now advance the game. Eleven native image/state checkpoints through
victory and eight fresh desktop/touch input checks pass. All 184 observed
original sound sources/rates occur between the matching inputs; full timing
and waveform parity remain open. All 84 suites and 183 environment states pass.
See [maze evidence](../treehouse_maze_sound_journey.md).

### Delivered board feedback, 2026-09-29

Previous board milestone: `73a6d9d9cf5c`. Restored ordinary board action sounds
and immediate offer hints; wrong-stack input now interrupts trade hints. All
236 money and 480 chip observed sources/rates match. There are 83 passing
same-build suites, including one corrected fixture rerun, and 183 passing
environment states. Known strict/native failures remain. See
[board sound evidence](../treehouse_board_sound_journeys.md).

### Delivered nature feedback, 2026-09-29

Previous nature milestone: `a44564be50d4`. Restores 15 missing nature editing
cues. All 82 suites and 183 environment states pass. Original observed
source/rate order matches for 17 editing and 57 quiz cues. Full sound timing,
waveforms and known strict/native failures remain open. See
[nature sound evidence](../treehouse_nature_sound_journey.md).

### Delivered theater sequences, 2026-09-29

Previous theater milestone: `c6f3a650aaaa`. All 81 suites and 183 environment
states pass. Theater option/category/prop feedback, token travel, curtains and
phrase ordering now include all 73 observed original sound sources;33 missing
cues restored. Complete waveform/timing and intermediate visual fidelity remain
open. See [theater evidence](../treehouse_theater_sound_journey.md).

### Delivered audio and input update, 2026-09-29

Previous audio milestone: `b0b73bf1f6f0`. All 80 registered suites pass in one
complete batch, together with all 183 environment states. The audio worklet
matches all 336 measured instrument windows and the original stop-decay law.
Module loading no longer delays the first input; cancellation, replacement,
mute and focus-loss behavior pass on file and HTTP origins.

Whole-game speech/effects, sound event timing and unaligned waveforms remain
open. So do the known money-loss, partial-redraw and animation differences.
The next work remains complete ordinary player journeys and demonstrated
visible/audible defects. Instruction-level equality is not a deliverable.
See [audio evidence](../treehouse_audio_mixer.md) and the JSON ledger for
bounded closures and retained failures.

### Priority correction following user feedback, 2026-09-28

The user raised concern that instruction-level replication is consuming work
without improving the playable game. The next pass must audit the integrated
game by activity and list concrete visible, audible, input or progression
differences. Prioritize fixes that reach the playable build. Use CPU-level
research only when a demonstrated player-facing discrepancy requires it.
Keep the existing strict reports as historical diagnostics; do not describe
their callback match ratio as a percentage of game completion. The fidelity
goal remains original graphics, behavior, animation and sound, with readable
text improvements following the faithful baseline. No full-parity claim is made.

The latest isolated compaction check passes 5,057 instructions and all non-stack
RAM (`compaction-check-a/report.json`), with an unchanged-output native control
(`activity-backdrop-control-comparison-b.json`). This is saved research evidence;
the complete backdrop callback remains uncomposed and the served build unchanged.

The sequence below records the prior CPU-focused approach, which is superseded
as the immediate priority by the integrated activity audit above.

1. Close the shared snapshot race with ordinary and instrumented replay evidence.
2. Recover the original animation preload plan and shape conversion costs.
3. Reconstruct ordered drawing, then attach the independently derived clock to
   the four-part presenter. Preserve all strict mismatches until resolved.
4. Audit shared RNG/audio and extend the same method across the coverage matrix.
5. Promote verified increments to the demo; close the final issue only when all
   completion checks pass.


### Current graphics integration checkpoint

- Indexed sprites, masks and rectangle fills: native pixel/work comparisons pass.
- Complete cursor sequences: shared buffers and CPU/queue comparisons pass.
- Resident clipping/rectangle helpers: all 822 calls match.
- Complete animation frames: all 25/25 match instructions, clocks and non-stack RAM.
- All seven SHAP 5403 caption lifecycles now run, including allocation/decode/free.
- All 35 intermediate conversion memory snapshots match.
- Timer IRQ0: all 1,127 complete calls match, including 342 BIOS chains.
- Sound IRQ7: all 26 guest calls match instructions, clocks, port commands and non-stack RAM.
- Mouse IRQ12: all three calls match, including the composed cursor redraw.
- Thirty-six focused device branch checks pass.
- Hardware entry/return: all 2,312 boundaries and 21 wrap/flag edge checks match.
- Runtime DSP/DMA ports: all 26 sound calls match 32 hardware fields; 20 focused checks pass.
- One continuous short animation span matches all 20,226 instructions and non-stack RAM.
- Both prepared SND 10048 starts match all 2,205 instructions, 71 ports and device/RAM state.
- Forty resident sound/flag branch checks and thirty-one DSP/DMA checks pass.
- DMA/PCM: all 6,011 native calls and 290,096 mixer output frames match.
- Long animation: 15,988 sparse samples and 105 exact IRQ admissions match before the activity callback.
- CPU callback research is retained for diagnostics. Next: complete ordinary-input winning journeys and prize delivery from `player-fidelity-matrix.md`.
- Remaining product requirements: original visible scene/startup sequences,
  intermediate displays, animation and sound timing, gameplay continuity and
  full-path coverage. Continuous CPU/interrupt/device emulation is a possible
  diagnostic technique, not a required architecture or separate deliverable.

The live strict result remains 614/984 callbacks with 12 missing displays.
Component passes do not close the integration issues.

### Implementation boundary reaffirmed, 2026-09-29

Following the user's repeated concern about excessive CPU-level work, completion
is judged by the browser game's rendering, input, gameplay, sound and timing.
Existing strict presentation failures remain open. Matching internal CPU
instructions, registers, heap layout or interrupt execution is not an additional
acceptance requirement. Preserve that research, and consult it only to explain
a reproduced difference in the game. Do not extend it as a workstream of its own.


### Current delivery and next work, 2026-09-29

Build `d7a51afab752` is served locally. Missing pile/food click interactions,
press cancellation and timer ownership are corrected. There are 76 passing
regression suites in explicit aggregate and 14/16 passing new native click
journeys. The two failed journeys and previous strict failures remain required
work. Next address the money-game loss sequence and ordinary-control progression;
consult internal execution research only when it explains a reproduced game
problem. See `../treehouse_object_press_journeys.md` for evidence and limits.


### Money loss ending delivered, 2026-09-29

Build `63151140a6de` is served with a full passing 77-suite batch. The unaffordable
payment label and mystery-node payment coin preparation are corrected. The
isolated original loss ending matches. The full loss sequence remains failed
at direct-payment preparation; its cursor resource-allocation dependency is
recorded in TH-004. No captured delta or seed is installed in the runtime.
Next prioritize remaining sound/playback and observable presentation gaps while
retaining every strict failure. See `../treehouse_board_loss_ending.md`.


## Money loss input coverage (2026-09-29)

The unchanged served build `a89b3f65ac50` passes four friend/robot mouse/touch payment-loss sessions twice: 101 checks, sixteen completed games, matching actions/state/final images. All intervening prizes and restarts are checked; final room return and reload pass. The existing thirteen board journeys also pass all 126 checks. This is supplemental browser coverage, not a new 89-suite batch or native fidelity proof. The direct-payment RNG discrepancy remains open. See `testing/treehouse_board_loss_input_matrix.md`.


## Telescope centering delivered (2026-09-29)

Delivered `377179be2807525d7c010e2da7e8b517d073be2f930b69d59cb9ff2836850df1`. All 92 regression suites and 183 environment states pass. All four final telescope views match original RGB images and all 16 mouse/touch replay-versus-exit checks pass; the complete activity tour improves from 22/27 to 23/27 matching images, with four room-return images and ten object-state mismatches retained. The strengthened money-loss suite covers 16 games in four mouse/touch friend/robot sessions. Strict nature remains 614/984 callbacks with 12 missing displays, and theater remains 348/580 intermediate images. Historical supplemental comparisons retain their original build hashes; full fidelity is not established. See `testing/treehouse_telescope_centering.md`.


## Balloon return scheduling isolated (2026-09-29)

On unchanged build `377179be2807`, paired observation shows the first post-return balloon movement 34 ticks early, with its reset deadline established 31 ticks early. Both versions then move every 49 ticks. Native observation/control files and timelines agree in 359 checks; browser image/state acceptance results are unchanged. No delay constant or movement-rate change was added. Room rebuild/return timing remains open. See `testing/treehouse_balloon_return_schedule.md`.


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


## Godot room interaction checkpoint â€” 2026-10-05

Ported calendar sheet/browsing and date/time speech fragments, cloud movement, spider/nest/chirp, original chalk brush/eraser/cursor/confirmation, pointer-key cadence and focus cleanup. Balloon following, clearance and short-click color/pop now work. The 24-checkpoint room-native-journey-c route passes every full RGB image (1,536,000 pixels total) and the explicitly compared calendar/cloud/chalk/balloon fields after one initial room/time fixture. Image membership within each input interval is tested; strict presentation times, resident RNG and general object/need state are outside this proof. Historical failed Godot calendar/chalk reports are retained.

Evidence: godot-room-journey-d/report.json; godot-room-startup-c/report.json (nine checks, two native images, 356 scripts/11,512 events); godot-room-input-a.json (twelve input checks); godot-room-web-a/report.json (six actual Edge interaction checks, no errors). Export: testing/output/treehouse/godot-room-web-build-a, package SHA-256 126f3c092efe169541b96dcbe6db84ba6fd558aa53e2e467e6feae6c119ec123. The existing port 8767 JS demo remains untouched.

TH-009 and TH-015 are in progress, not closed. Next: resident character/object actions and held-object placement, yard/hollow and original navigation/transitions, then complete music. Escape currently returns to selection and still needs the retained-character yard flow. Preliminary Godot audio uses original sample/rate data but mixer/waveform parity remains open.


## Godot resident and yard checkpoint â€” 2026-10-05

Added the shared original RNG stream, resident poses/action queue and callback object ownership, need warnings, yard/hollow hotspots, pond/window/squirrel animations, interruptible sign and original integer nut flight. Escape returns to the retained-character yard; the ladder returns indoors. General object drag/place, offers, sleep/wake and automatic ambient tasks remain incomplete.

Godot action regression C matches all 158 available character/pose/action cases against JS in final image, pose, objects, completion tick and RNG. It uses explicit isolated fixtures and disables device playback while retaining sample-derived deadlines; no audio parity claim. Accelerated A/B audio-backend shutdown warnings are retained; C cleanly isolates device output. Native yard journey C has 24/24 exact full-frame image matches and 23/24 checked states. Its final balloon bounds mismatch is unchanged from yard-native-check-c: expected [64,133,102,162], actual [65,135,103,164]. It remains a failure. Native room regression B passes 24/24 images and checked states; startup D passes nine checks/two native images/all 356 scripts; twelve focused inputs remain passing.

Actual Edge export check B passes nine interactions through the room, yard, hollow, nut throw and ladder return, with no browser errors. Immutable export: testing/output/treehouse/godot-yard-web-build-b; PCK SHA-256 3b83f548ef6df6db4efa148b44e39373d4650aebdc3dd16b6cf236f3d90b737b. Separate local Godot preview: http://127.0.0.1:8768/; delivery-a checks served files against export hashes. Original JS port 8767 is unchanged. All broad migration/fidelity issues remain open.


## Godot objects, care and ambient events â€” 2026-10-05

Ported held-object thresholds, surface placement/falls, all direct object click/offer handlers, fruit/pillow care, naps and natural waking, basket/worm/bird handoffs, nut bags/piles, food consumption and automatic room/yard events. Connected calendar, clock speech, environment and window completion timers. Pending object callbacks are released when the Godot scene exits.

Evidence: godot-objects-component-c passes 86 isolated JS comparisons with 3,425 sampled resident frames, sound events, completion/state/RNG. godot-objects-care-b.json passes 18 mouse/touch care checks from selection with ordinary updates and advancing civil clock, without need/pose/object fixtures. Twelve focused input checks, 158 action cases, nine startup checks, two native startup images and all 356 SCR comparisons remain passing. Three godot-objects-basket*-final-a routes match all fourteen native images and full checked object/gameplay/RNG states.

Broader strict failures stay open: godot-objects-room-e matches 24/24 images, 19/24 full states; remaining RNG divergence starts after declining erase. godot-objects-yard-final-a matches 24/24 images, 23/24 full states, with the known return-balloon geometry failure; its RNG matches throughout. godot-objects-egg-final-a matches 3/4 images and 4/4 full states; final frame remains unmatched. Native image membership is bounded, not exact display-time or audio-output proof. Historical failures remain intact.

Immutable export godot-objects-web-build-b has PCK SHA-256 ae99622847dcea0bf31f778db534e56a928004ef106319796c1430b7ac0219d3. Eleven real Edge checks pass, including held pillow drag/fall and nut bag. All nine files served at http://127.0.0.1:8768/ match the export (godot-objects-delivery-a.json). The server is direct Python PID 30000 with redirected logs; orphaned older 8768 Python servers were stopped after their detached pipes caused closed HTTP connections. Existing browser tabs were not refreshed. Port 8767 reference is untouched.

Next: original room-to-activity transitions/rewards, then the complete Godot music activity. All required migration and fidelity issues remain open.


## Godot music listening and room transfers â€” 2026-10-05

Ported original room/music teleport and return, waking a sleeping child before departure, listening books, both score sizes, all 17 piano keys, held note movement/focus cleanup, pitched original PCM with effective rates/loop bounds, song playback/tempo/repeat, contents/page navigation, idle animation, all seven families and 42 instrument selections/facts/auditions. The generic ring/bubble renderer supports all four variants; only music is integrated into playable activity navigation. Added safe empty-clip handling for foreground objects.

Evidence: godot-music-component-e passes 151 full-image and complete song-event/end-tick cases versus the JS reference, plus four complete native menu/music images (long score allows 17 authored idle-eye frames, not timing equality). godot-music-transitions-c matches all 330 changed full RGB frames in original order across eight isolated transition sequences from explicit initial native fixtures. godot-music-input-a.json passes 47 production control checks; godot-music-care-b.json passes 22 mouse/touch checks including interrupted-nap music entry. godot-music-objects-a retains 86 operation cases. godot-music-startup-b retains nine checks, two native images and 356 SCR comparisons.

The native room replay retains 24/24 images and 19/24 full states; yard retains 24/24 images and 23/24 states. Remaining erase-dialog RNG and yard-return balloon differences are unchanged. The earlier egg final-image failure stays open. Real device output waveform/mixer parity, exact presentation timestamps and complete integrated activity journeys are unproven.

Immutable export godot-music-web-build-a, PCK SHA-256 783e07f7bf51274309d30cdb684d50671c08a0381c055fd7d852f5528894c5a0, passes sixteen actual Edge checks (godot-music-web-b) including piano entry, physical key down/up, families and return. All nine served files match (godot-music-delivery-a.json). The preview at http://127.0.0.1:8768/ is direct Python PID 14668 with redirected logs. Existing tabs were not refreshed. JS reference port 8767 is unchanged.

Next: complete composition/personal songbooks, note/rest editing, title input, copy/random/erase dialogs, persistence/printing, then musical maze. These controls are still incomplete in the Godot preview. Required fidelity and migration items remain open; this checkpoint is not full-game completion.


## Godot personal songbooks and print sheets â€” 2026-10-05

Ported both personal songbooks (42 editable songs each), original note/rest palette, insertion marker and note dragging, erasing, title editing, contents, copy/random/erase confirmations, and original print-sheet preview. Native SONGS.DAT serialization preserves all 86 records, CP437 titles and trailing bytes; desktop saves use user://SONGS.DAT and Godot Web persists the same file through IndexedDB. Invalid imports are rejected before changing either book.

Evidence: godot-editor-native-c passes all 22 full native images and active song/title/marker/selection/RNG states through one continuous input journey. godot-editor-component-c passes 223 complete image/sequence cases across both sizes, all note/rest durations and spellings, drag colors, seven contents pages, title carets and confirmation phases; three original print sheets also match in full. godot-editor-controls-b passes 32 production-control/binary-save checks. godot-editor-listening-a retains 151 listening cases and four native frames. godot-editor-care-a retains 22 mouse/touch care checks.

Actual Edge export check godot-editor-web-a passes 23 checks with no console errors, including physical-key composition, title entry, switching books, print preview and restoring the authored notes/title after an actual browser reload. Immutable export: testing/output/treehouse/godot-editor-web-build-a; PCK SHA-256 b0118b8db2bdab0c2dcb3d7ff73b3b69aec683d334ecc28acbba4181efb5785b. The Godot preview at http://127.0.0.1:8768/ serves all nine matching files (godot-editor-delivery-a.json), direct Python PID 36552. Existing tabs were not refreshed; the JS reference on 8767 remains unchanged.

Historical failed runs are retained: native-a exposed JSON float lookup mismatches in CP437 and pitch tables, fixed by integer normalization; component-a/b failed in the new JS comparison harness (constant reassignment and wrong renderer name), corrected without changing the reference game; controls-a incorrectly expected a Unicode music symbol absent from the recovered CP437 mapping, corrected to supported extended characters. Native-c and component-c use the production source delivered above.

Next: musical maze and its integration/rewards. User-facing file import/export and physical print/download delivery are still required; the current print button only previews the original sheet. Strict presentation timing/audio and prior room erase RNG, yard-return balloon and egg-route final-image failures remain open. No migration issue is closed by this checkpoint.

Startup regression godot-editor-startup-a also passes nine checks, two full native images and all 356 SCR comparisons. Completion remains unproven; completion-gate-db retains every open migration/fidelity requirement.


## Godot musical maze â€” 2026-10-05

Ported overlay 1's challenge generation, all five sound/sign types and nine scenes, both characters and frog animations, note roller/falling rewards, walks, adaptive difficulty, reminders, song drawer, incorrect and correct guesses, victory, full-song replay, next round and exits. Music/maze smoke and bucket transfers now use the original shapes and character scripts. Maze notation uses instrument 9; instrument-identification samples play finitely. First-use drawer decoding waits derive from the recovered sound work, with warm reuse. Audio note completion preserves a newer sound's channel ownership.

Evidence: godot-maze-native-b passes 20 checks: eight seeded native generation comparisons, ten continuous full-image/state/RNG checkpoints through a wrong sign and eight correct signs, the in-progress victory highlight, and completed victory. godot-maze-component-a passes 244 full image fixtures across scenes, sign types, both characters, actor/frog frames, drawers, note drops, highlights and endings. godot-maze-controls-d passes 66 fresh mouse/boy and touch/girl checks including full/skipped tutorial, two errors, wrong guess, correct early guess, automatic-audition input, cold/warm sound loading, replay, new round, reentry and global exit. These checks read answers to select inputs and do not install maze progress/difficulty states.

Godot-maze-entry-full-d and godot-maze-entry-skip-c remain FAILED overall. Both pass all 54 changed transfer frames in native order and every stable entry/return checkpoint. The full route matches 45/46 checkpoint images and 44/46 checked states; intro-05 and intro-25 differ in when RNG is consumed, and intro-15 has a 129-pixel frog-pointer timing difference. The skipped route matches 19/19 images and 18/19 states, with intro-05 RNG timing remaining. Paired native sound observation/control timelines and WAVs agree; all 18 full-route and 13 skipped-route observed sound sources/effective rates occur in Godot order between player inputs. Unmatched Godot starts remain in the reports. This is not exact event-timing, stop ownership or audio waveform proof.

The existing composing native journey retains all 22 checkpoints (godot-maze-editor-a). Editor rendering now passes 225 cases (godot-maze-editor-component-a), including added original music-eraser cursor checks; its cursor uses CURS2 with recovered color and hotspot ordering. Startup retains nine checks, two native images and all 356 SCR comparisons (godot-maze-startup-a).

The actual Edge export passes 29 checks (godot-maze-web-b), including saved composition after reload, maze transfer/tutorial skip, a sign interaction and retained-score return. Immutable export: testing/output/treehouse/godot-maze-web-build-a; PCK SHA-256 c214b7474cfb5337a0485b71ba928d31224fbe2616957d114b73d403a6a1a6e0. Nine served file hashes match in godot-maze-delivery-a.json. Preview http://127.0.0.1:8768/ uses direct Python PID 6916 with redirected logs. Existing tabs and the JS reference at 8767 were not refreshed.

Earlier failed reports are retained. Controls-a/b clicked outside the girl's original selection hotspot; the harness now uses the same x=145 hotspot as the existing care checks. Web-a sent Escape before the reverse bucket animation finished; web-b waits for the original portrait to return. Entry transfer count checks now compare changed-frame counts (54) rather than the older collector's 62 entries containing checkpoint-boundary duplicates, and use each route's own native hashes/order. No gameplay timing was changed to fit these harness errors.

Next major port: sentence theater, followed by nature and board games. Maze preference/history persistence, help/settings, file interchange, physical printing and integrated rewards remain open, along with the explicit tutorial, room erase RNG, yard balloon, egg-route image and strict audio/presentation failures. No broad migration issue is closed.


## Godot sentence theater â€” 2026-10-05

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


## Godot print output checkpoint â€” 2026-10-05

Godot print previews now provide F9 Save picture and Print picture controls. PNG export preserves all 320x200 pixels; browser printing uses the same bytes with original aspect, pixelated scaling and utility UI omitted. Desktop saves PNG through its file dialog and can open a standalone HTML print page. 47 production controls, 52 real Edge checks and 225 editor/rendering cases pass, including three full native score sheets. Repeated PNG downloads are byte-identical. Save interchange retains 22 browser checks; help/preferences 17; editor/nature controls 32/56; startup two native frames and 356 bounded SCR comparisons. All nine served files match immutable godot-print-web-build-a, PCK 9e474ebdc752c6a5c0c2639f8b0cbb7697e4b07093fe8a421c2038be70e3a6c3. Headless Edge emits beforeprint but leaves requests pending without afterprint; the verifier uses fresh documents, and interactive dialog completion/physical paper output remain unverified. The original configured printer backend is unavailable, so DOS physical-output/duration parity is not claimed. Title boot, native missing-STATUS defaults, interactive desktop dialogs and all earlier strict gameplay/timing/audio failures remain open.

The output utility is separate from the original artwork: confirm its printer
prompt, press F9, then Save picture or Print picture. Escape closes the utility
and another Escape dismisses the original preview. Nature exports the complete
320Ã—200 screen, matching the original print rectangle, including facts and UI.
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


## Godot fresh-profile defaults â€” 2026-10-05

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

The Godot game now boots through the Broderbund logo, its three SCR70 sparkles,
the cue-e two-pixel “presents” reveal, separate FM playback, final wait and
keyboard/mouse/touch skip. Both original 64-color logo shapes are used. The
source wrapper places sparkles by bottom/center; the independent renderer now
uses that geometry. New asset generation reads original MIDI and patches,
implements the original melodic FM rules, and uses a standalone pinned DBOPL
synthesizer. Native audio recordings and register captures are never runtime
inputs. The generated WAV is checked against its provenance before Godot builds.

Evidence:

- `title-native-proof-a/report.json`: 119 checks pass. All 1,124 title FM writes,
  their order and timer-interrupt positions match the original; all MIDI channel
  events, six cues, tempo steps and the active 128-patch bank match. All eight
  MIDI resources round-trip byte exactly. Parser edge controls pass.
- `godot-title-d/godot.json`: nine startup/input checks. Every one of its 82
  distinct complete title frames matches a native boot frame in order.
- `title-midi-native-b` and `title-midi-control-a`: identical complete callback
  timeline, native audio and selection RAM with and without read-only observers.
- `godot-title-web-a`: ten actual Edge export checks, 24 sampled title frames,
  automatic selection, all three skip inputs and playable room entrance.
- `godot-title-fresh-web-a`: eleven fresh profile/reload/native-import checks.
- `godot-title-regression-a`: two native full frames, nine startup checks and
  356 bounded SCR regressions remain passing. Activity tests explicitly skip
  the title at their fixture seam; browser activity tests use ordinary Escape.
- `godot-title-delivery-a.json`: nine served files match the immutable export.
  Build `godot-title-web-build-a`; PCK
  `f8d183ce85db39bd87c96bda6848073338b585b9c5bd0288c7fe284cc0e8f6bc`.

The original tempo handler reads its last two tempo bytes as a little-endian
word. Preserving that behavior, its fixed-point division and fractional timer
carry reproduces all six cue IRQs (0, 205, 307, 512, 1036, 1532), rather than
using standard MIDI timing or captured wall-clock timestamps. Title synth B/C
produce the same WAV SHA-256
`bd48c58e46e1dc6a68c46f02d7bd834c8e28019303bfb467987ad8ea098d1ee7`.

Limits: pre-selection preview animation and looping selection music are still
missing. Other FM tracks, pitch bend and rhythm patches need implementation.
Register writes inside an interrupt currently share a sample boundary; native
mixer/output-waveform parity and browser audio activation remain unverified.
Ordered full-frame matches do not prove partial redraws or unshifted timing.
Full startup RNG/profile integration and all earlier strict failures remain
open. No issue closes. The live preview is http://127.0.0.1:8768/ (PID 37572).

Failed development runs are retained: synth A lacked the compiler assembler
PATH; Godot title A called a nonexistent animation cleanup method; B used the
16-color resource override; C placed sparkles at top-left instead of the source
wrapper's bottom/center. D corrects these and passes the complete-frame checks.


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

### Godot resource ownership checkpoint — 2026-10-13

Godot now implements the conventional allocator, near allocator and resource handle ownership directly in GDScript. Native component checks pass: 402 allocator checks (52 preparation calls, two cursor-moving packing operations, 104 near checkpoints, 237 returned pointers and six boundaries) and 668 continuous ownership checks (104 complete near/far checkpoints, 159 far allocations, 43 raw frees and ownership/resize boundaries). Offline initial RAM and request streams are diagnostic fixtures only. Generated startup/catalog/scene lifetimes and live board integration remain required; Money loss is unchanged. These modules are not yet called by the playable game.

The source inventory now includes these unintegrated modules; the preview still serves `godot-scanout-build-a`. See the payment resource dependency notes for evidence and retained failed attempts.

### Generated Godot startup resource state — 2026-10-13

Godot now generates startup resource ownership from pinned executable/platform/archive inputs: DOS allocation and arena growth, source cache, converted fonts/cursors, saved surface, all seven startup catalogs, direct configuration copy and retained SND 0. All 98 native boundary-field comparisons, five boundary-count checks and five focused checks pass (108 total), including when loading the normal generated original.json bundle. The 668 continuous memory ownership regression checks still pass. Resource modules are not yet connected to live title/selection/room/board events; the Money loss and all seven native discrepancies remain open. Preview is the prior scanout export; source inventory is ahead of it.

### Godot scene resource chain — 2026-10-13

Godot resource ownership now continues from generated startup through all three title animations, selection previews/departures/climb, initial room construction, outgoing ring/bubble transfer and initial Money/robot board options. Normal built-asset comparisons pass 377 checks for the boy-to-board route (366 native boundary/state/payload comparisons plus 11 checks), 209 for girl-to-room (204 native comparisons plus five checks), and 108 startup regression checks. Transfer resource events are driven by the production Godot SCR interpreter; initial board state uses production BoardGame with one explicitly supplied native entry seed. Room time/cloud/objects and two visible credit changes remain explicit semantic fixture inputs. These resource modules are not connected to the live game event loop. Board start/turn/redraw lifetimes and payment integration remain open; no Money fix or native timing/audio parity is claimed. Preview remains the prior scanout export.
