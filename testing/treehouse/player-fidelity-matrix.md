# Integrated player-facing fidelity audit

## Scope and priorities

The goal remains a faithful independent reconstruction of the original game.
This matrix makes the next work observable in the playable build: complete
activities, correct graphics and animation, input, sound, and saved creations.
Instruction counts are diagnostic evidence when needed to explain a mismatch.
They are not a measure of game completion.

The 2026-09-28 desktop/touch journey rerun passed 38 checks on build
`e8d83608950c33ee60689df4f7efea33a02f7c7708c9c09ddfe1217b71af0024`.
Evidence: `testing/output/treehouse/player-audit-journeys-a/report.json`.
That journey performs a sentence and a song, visits each principal activity,
and reloads a collage and sentence. It starts the guessing game, board game,
and maze; it does **not** establish their complete ordinary-input win paths.

## Finite journey matrix

Each row needs both ordinary-input browser execution and pinned-original
comparison for its stated scope. Existing focused suites are evidence leads,
not automatic completion of a row: many arrange internal state to cover a
particular branch. Every row is currently partial or awaiting a complete
paired journey. Preserve existing exact-image and strict timing failures.

| ID | Journey / variants | Related existing suites | Remaining whole-journey evidence |
|---|---|---|---|
| J01 | Boy and girl entrance; return to yard and reenter | entrance, exterior, journeys | Paired uninterrupted input/animation/sound sequence for both characters |
| J02 | Pond, sun, cloud, birdhouse, friend call; three nuts and squirrel sign | exterior, exterior_sequence, journeys | 23 paired yard/hollow image/state/RNG checkpoints match, including fourth-nut rejection, sign interruption, all pond cycles and revisit. Full 24-checkpoint room return has matching RGB image membership/RNG but final balloon one step ahead; full sound/timing remain |
| J03 | Room clock, calendar browse/today, nest, spider, cloud and chalk erase/decline | room, room_sequence, environment, chalkboard, global_controls, room_navigation, room_clock, chalk_native_stroke, room_native_journey, room_drag_journey | All 24 continuous original checkpoints match full RGB membership and gameplay/random/object state. 80 narration/rolling navigation checks pass. Mouse/touch drawing survives music/nature/theater revisits pixel for pixel; actual erase decline/confirm and undo pass. Exact presentation/audio timing remains |
| J04 | Drag room objects, offer food/pillow, sleeping friend and wake/navigation | character, objects, room_sequence, room_care_journey, room_drag_journey | 22 ordinary feeding/sleep/wake checks pass for desktop/boy and touch/girl. Actual mouse/touch pillow, fruit and nut drags, trapdoor transforms and yard-object reload also pass in the repeated 30-check drag/drawing journey. Five native airplane and four caterpillar drag/offer/landing/departure checkpoints now match full RGB and compared state. Delivered egg follow-up also matches all seven short-press images and four held-motion RGB/state checkpoints, but final short-press balloon state is one step ahead. Click-only press coverage is implemented; all three basket-to-worm gestures now match 14 native checkpoints. One nut-flight position discrepancy and full paired sleep/wake timing/audio remain |
| J05 | Each activity entrance/return and all four telescope views | room_transitions, telescope_journey, shelf_sequence | Ordinary journey after earned robot prize, with interruption |
| J06 | Original songs, all five speeds, repeat, instrument selection and auditions | demo, music_followup, music_completion, audio_ownership, music_journey, music_native_journey, audio_instruments, audio_stop, audio_mixer_lifecycle | Both authored books finish at all five speeds; repeat/stop pass. All 22 paired music checkpoints match. Eleven native and eleven ordinary-control listening preference checks pass, including restart. All 336 measured windows across 42 choices/126 notes now match sample-exactly after one attack alignment per note, including Balloon. Native stop-decay law and 18 real-output input/lifecycle checks pass. Full unaligned sound and native event timing remain open |
| J07 | Short/long songbooks: create, move, erase, copy, name, save/reload, SONGS.DAT round trip | music_editor, music_completion, persistence, music_journey, music_native_journey | Thirty ordinary-input authoring/playback/interchange checks pass; both books survive full reload and SONGS.DAT round trip byte for byte |
| J08 | Musical maze: wrong choice, recover, collect notes, wrong song, win and restart | music_maze, maze_generation, journeys | Browser: twelve rounds/all types/scenes; native continuous snapshot-to-victory state/RNG and ten RGB checkpoints match; fresh entry and full timing/audio remain |
| J09 | Theater: valid/invalid sentence, shuffled tokens, notebook token, actor/props, weather and replay | theater, theater_playback, journeys, theater_wrap, theater_prop_save | Native complete correction/props/weather/room-return journey matches all 29 images and state/RNG; return reminder order and grace time pass; all 14 notebook-token image/state/RNG checkpoints also pass; full sound/timing remain |
| J10 | Nature day/night collage: filter, facts, drag, remove, erase/decline and reload | nature, global_controls, persistence, journeys, nature_editing_native, nature_editing_save | Delivered e9af2b698fce matches all 21 native image/state/RNG checkpoints and 11 ordinary-control edit/reload checks; removal sound dispatch fixed; full idle/timing/audio remain open |
| J11 | Animal guessing: human/friend and human/robot, helped/unhelped, wrong/correct guess, win/restart | nature_completion, nature_guidance, nature_sequence, timing | Complete input-driven game for both opponents; retain known redraw/timing differences |
| J12 | Money board: each goal, friend/robot, wrong road, rewards, end and restart | boardgame, board_completion, board_sequence | Browser: both opponents/all goals, prizes and money-payment loss/reload pass; native money/robot win matches 25 checkpoints; full native loss matches through step-09 after actual payment preparation fix; direct-payment unused second-amount RNG diverges at step-10; isolated native loss ending now matches after correcting mystery-payment coin preparation and the unaffordable payment label; partial-counter timing remains |
| J13 | Chip board: each goal, carries/borrows, friend/robot, end and restart | boardgame, board_completion, board_sequence | Browser: both opponents/all goals, carry/borrow and win/loss covered; full native friend game matches all 49 state/RNG checkpoints and 48/49 images, with partial trade-flash clearing still missing |
| J14 | Human/robot prizes, collection, room delivery, shelf and later revisit | rewards, reward_completion, shelf_sequence | End-to-end prize earned through gameplay and retained through reload |
| J15 | F1/F2, confirmations, sound toggle, version panel, print consent and STATUS.DAT interchange | help, global_controls, persistence | Apply through actual controls across activities and compare saved data |
| J16 | Desktop keyboard/mouse and touch interruptions: focus loss, hidden page, held notes and drags | journeys, input_lifecycle | Browser lifecycle checks plus full combined long-session pass |
| J17 | One uninterrupted session visiting games, earning prizes, saving and returning | journeys, persistence | Two full browser sessions pass and repeat identically; native cross-activity RNG/sound comparison remains |

## Concrete findings and next work

- **INPUT-01:** Focus loss leaves nature/theater/music-editor drags active,
  hidden-page arrow keys remain held, and pending piano audio unlock can start
  a note after cancellation. Six failures reproduced in
  `input-lifecycle-baseline-c/report.json`; candidate correction passes all nine
  checks in `input-lifecycle-check-a/report.json`. Delivered in build `a522379ee14863aec9b2829fe2ffa2cc5a6424087e16058d5a3611497f0670c5`
  after all 38 regression suites and the environment checks passed. Delivery
  evidence: `player-input-delivery-a/report.json`.
- **VISUAL-01:** The existing nature comparison omits 12 original display
  changes and has timing differences. See `treehouse_timing_fidelity.md` for
  the specific intermediate draws. Keep this open; no frame shifting or
  relaxed comparison has been introduced.
- **AUDIO-01:** Actual browser rendering exposed an extra 0.4 gain. Delivered
  unity gain now measures 99.9898% of native Bass A attack level, correlation
  0.999972. Resampling, stop decay, other sounds and whole-game sound timing
  remain open. See `../treehouse_audio_output_fix.md`.
- **COVERAGE-01:** Complete ordinary-input winning journeys (J08, J11â€“J14) and
  cross-activity continuity (J17) are the next audit priority after INPUT-01.
  Existing passing component tests cannot substitute for these journeys.

No full-game fidelity or completion claim is made by this matrix.

### Current prize/room checkpoint (2026-09-28)

On served build `0d57eba7c465`, J11/J14 now have thirteen matching continuous
native checkpoints through a friend/manual quiz, wrong guess, win, second reveal,
prize, next deal and return to nature. The chooser background and next hand were
corrected. All 50 browser suites pass, including thirteen complete board journeys
with an explicit money loss. Full original room-return comparison remains open:
717 differing pixels and a three-draw random-stream difference. This preserves
the remaining J05/J14/J17 integration requirement. See
`../treehouse_nature_prize_continuity.md`; full timing/audio parity remains open.

### Room-return follow-up (2026-09-28)

Served build `d367f5d54d5c` extends the paired J11/J14 journey through room return:
all fourteen native RGB checkpoints and active gameplay/random state match.
The room long-timer scheduling side effects and balloon cadence/tie rule are
corrected; the verifier initializes its clock from saved BIOS time. These are
image-membership results, with exact transition/ambient timestamps still open.
All 51 suites pass, including five browser animal-game journeys with explicit
human and robot prize requirements. See `../treehouse_room_return_continuity.md`.
The next broad paired activity target is J09 theater, then J10 day/night editing.

### Theater follow-up (2026-09-28)

Served build `3d7c96f509e1` corrects sentence wrapping and fractional decoration
coordinates. All 29 paired native theater images and active theater state match;
an ordinary-input reload also preserves the whole saved theater state. J17 still
has a theater-to-room RNG discrepancy despite the correct room image. Full audio
and presentation timing remain open. All 53 registered suites pass. See
`../treehouse_theater_journey.md`; J10 day/night editing is the next broad flow.


## Guessing-game winning journeys (2026-09-28)

`verify_winning_journeys.py` now runs four fresh browser journeys through visible
buttons and selectors, from character selection to saved prize inventory:

- Desktop / boy / friend / manual crossing out.
- Desktop / boy / robot / help enabled.
- Touch / girl / friend / help enabled.
- Touch / girl / robot / manual crossing out.

Each asks a question, makes a wrong guess, resumes play, reaches a human or robot
win, waits through its animation, reveals the other animal, chooses a prize,
waits for its transfer, checks the next game, returns to the room and reloads. Robot winners also visit
the telescope shelf; human prizes persist across reload while robot prizes
follow the original session-only lifetime.
The test reads the current answers to choose inputs and accelerates the clock;
it never installs internal gameplay state. This establishes browser integration
for the winning portions of J11/J14 in these four scenarios. Paired native
journeys and exhaustive paths remain open. The initial calendar and BIOS-seed
clock is fixed at 2026-09-28 10:00 Brisbane for repeatability.

Two reproduced application bugs blocked these journeys:

- **GAME-01:** After a robot question, the readable panel omitted the next-turn
  die button. Its visibility now follows the completed-turn state, matching the
  still-available original canvas die action.
- **GAME-02:** The win routine's final change notification replaced the prize
  buttons with the guessing-game controls. Activity panel updates now defer
  while the shared prize chooser owns the controls, in both nature and board
  games. The prize's normal completion restores the next game's panel.

Baseline: `winning-journeys-a/report.json` (all four journeys fail).
Final candidate: `winning-journeys-fixed-c/report.json` and
`winning-journeys-fixed-repeat-a/report.json` (four journeys, 42 checks pass
twice with identical actions and outcomes). Baseline with the same fixed clock:
`winning-journeys-baseline-fixed-a/report.json`.
The new suite is included in `verify_all.py`; integrated regression and delivery
are recorded in the completion report. Existing native image/timing checks are
retained, and this browser test does not claim native timing parity.

Delivered GAME-01/GAME-02 in build `c594f3e829394d46df313d17d70cebc6064b6994be7886a17edc76d18ef23827`; all 39 suite results and
183 environment states pass. Evidence: `winning-delivery-a/report.json`.


## Complete maze and board journeys (2026-09-28)

The current served build (`c594f3e82939`) completes twelve musical-maze rounds
through visible controls in two uninterrupted desktop/touch activity sessions.
The routes cover all five challenge types and all nine scenes, two wrong signs,
wrong-song recovery, early song identification, collecting every note, full-song
replay, restarting and returning to the piano. All 50 checks pass in
`maze-journeys-b/report.json`. The first coverage attempt passed its journeys but
missed the easy pitch challenge; its failed coverage report is retained.

Twelve ordinary-control board journeys cover money/chips, friend/robot and all
three goals. All 116 checks pass in `board-journeys-c/report.json`, including
illegal-road rejection without spending moves, carry and borrow, rejection of
the wrong chip stack, complete endings, human/robot prizes, transfer, new game,
room return and reload. One chip game ends by exhausting a player's balance;
the remaining routes end at a goal. An ordinary money-payment loss is still
uncovered. The earlier coverage run reached only winning endings and its failed
coverage report is retained, along with an initial harness setup failure.

These tests read the current answers to choose inputs, fix the initial date and
advance animation time. They never install gameplay state. They establish full
browser activity integration for these routes, not native pixel/audio/timing
parity. No game-source change was required by this batch. Next: an uninterrupted
cross-activity session retaining creations and prizes, then paired native
journeys to isolate remaining observable fidelity differences.


## Uninterrupted sessions and native maze comparison (2026-09-28)

`session-journey-a` and `session-journey-repeat-a` each pass all 38 checks with
identical actions and checkpoints. Both desktop/boy and touch/girl sessions
create three notes and a rest in each songbook, play a composition, win the maze,
perform a sentence, create day and night collages, win the animal game and earn
a room prize, visit board/telescope/yard, revisit the creations and reload. Both
songbooks reload byte for byte; sentence, collages and prize survive. These
ordinary-control sessions initialize only the clock; no gameplay state is set.

`maze-native-journey-c` establishes a stronger native comparison for one maze
route: load one original initial snapshot, then feed the original canvas inputs
without resetting state/seed between turns. A wrong sign and eight correct signs
reach victory. All ten RGB checkpoints and all compared state/RNG values match.
The historical `correct-7` capture is still playing note 9, so it is checked
against a generated playback frame. A new ordinary original-game continuation
(`maze-victory-tail-b`) establishes the completed screen. Its repeat agrees at
all 3,000 callbacks, clocks and audio (`maze-victory-tail-repeat.json`).
The first comparator run's initial frog visibility setup error and mistaken
settled-endpoint assumption remain recorded in `maze-native-journey-a`.

The suite registry now includes both checks. `session-native-regression-a` is a
transparent aggregate of the previous 41 passes and these two new passes on the
same unchanged HTML. No game-source fix was required. This closes the browser
continuity evidence gap for these routes; fresh-start native continuity, full
animation timing and audible output equality remain open.


## Board continuity defects delivered (2026-09-28)

The complete original money/robot capture `board-native-completion-a` reaches
56 cents versus 39 after 24 ordinary mouse inputs. The browser initially matched
18 checkpoints, then diverged when a robot road choice skipped eight rejected
directions in the shared random sequence. `boardgame.js` now draws all four
directions and retries missing roads, as the original does. `board-motion.js`
also clears remaining moves after ordinary money credit. Both have preserved
failing evidence and a minimized reproduction; see `treehouse_board_continuity_fix.md`.

All 25 original RGB/state/RNG checkpoints now match continuously through victory
(`board-native-completion-check-b/report.json`), including the previously wrong
8/9-cent offer. The short seven-checkpoint turn also matches its hint and delivery
frames. All 45 suites reran together and pass on delivered build `014d9c299a2b`;
183 environment states pass, and HTTP/candidate hashes agree. Strict timing remains
614/984 with 12 missing displays. No timing, waveform or exhaustive-route claim
is inferred from these ordered checkpoint comparisons.

## Maze victory exit audit

Readable victory replay/restart/return controls now use the canvas action path.
Return during playback interrupts first; the following activation plays the
original departure. Global Back saves finalized song history before leaving.
All five desktop/touch exit and immediate-reload routes pass 41 checks; the full
46-suite run passes on build `805cd0adac74`. This extends J08 and J15 input/save
coverage; exact presentation timing remains open. See `../treehouse_maze_exit_fix.md`.

## Payment and chip-game follow-up

Build `4144de5beb39` corrects the unconditional payment pair-direction random
draw. All 49 regression suites pass. See `../treehouse_board_payment_rng.md`
for full money-loss evidence and its remaining unused-coin RNG discrepancy,
and `../treehouse_board_chip_journey.md` for the full chip game's matching
state sequence and one preserved partial-redraw failure. These additional
failed journeys are explicit inputs to the completion gate.

### Nature editing follow-up (2026-09-28)

Served build `e9af2b698fce` passes the complete 21-checkpoint day/night editing
comparison, ordinary-control save/reload, and original removal-sound dispatch.
All 56 suites pass together. Fact-panel behavior, confirmation side effects and
restored animal timers are corrected. See `../treehouse_nature_editing_journey.md`.
J10 full idle/timing/audio evidence remains open; J06/J07 complete music playback
and songbook creation/interchange are the next broad flows.


### Listening settings delivered (2026-09-29)

Build `fb6652aa720a` restores original per-song/per-score-mode speed, instrument
and notation, retains the idle deadline across music control refreshes, and
loads the correct instrument for a saved page after restart. All 60 suites ran
together and passed; 183 environment image states pass. See
`../treehouse_music_preferences.md`. Full native transition, board, timing and
audio gaps remain explicit in the completion report.


### Theater return continuity delivered (2026-09-29)

Build `a59674954b51` passes the full 29-checkpoint native theater journey,
including final room random state. The fresh ordinary return test checks
reminder ordering, the 600-tick grace period and post-action ambient scheduling.
All 62 registered suites pass together. See `../treehouse_theater_return_fix.md`.
Full sound/presentation timing and the remaining board comparisons stay open.


## Prize object follow-up (2026-09-29)

Served build `43a8cda7163c` restores the balloon moving clear of a dropped
object, correct held-object and caterpillar-in-hand layering, and drop/departure
timer ownership. Five airplane and four caterpillar checkpoints match full RGB
image membership and compared gameplay/object/random state. The native captures
repeat identically. The verifier compares a held object's stored origin with
`drag.rect`; the displayed rectangle is reported separately and still checked
by the entire original image. The previous build still fails the corrected
verifier at the same visible defects.

All 73 existing suites pass in one batch. The two new prize suites pass
separately on identical HTML, giving 75 passing suites in aggregate; all 183
environment states also pass. The served hash is verified. Known strict nature
timing, money-loss, chip partial-clear and yard-return balloon failures were
rerun and retained. This is a delivered player-visible correction, not complete
intermediate-frame or full-audio parity. See `../treehouse_prize_object_journeys.md`.


## Egg input candidate (2026-09-29)

Candidate `e8ad0a585e54` restores the egg's press/hold distinction, the separate
bird-flight ambient reset, and balloon/cloud service between object animations
and the next ambient activity. The full short-press journey remains failed at
its final balloon state despite matching all seven checkpoint images. The
held-motion journey passes all four images and compared state. Both original
input captures repeat. All 75 registered suites and 183 environment states now pass; the candidate
is delivered with a verified HTTP hash. The full short-press egg comparison
is retained as a failed native journey in `completion_verification.json`. See `../treehouse_egg_input_journey.md`.


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
is not a separate workstream. See `../treehouse_object_press_journeys.md`.


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
See `../treehouse_board_loss_ending.md` and
`../output/treehouse/board-mystery-payment-delivery-a/report.json`.

The complete original money-loss journey still diverges at step-10. Its direct
payment uses an uninitialized delta inherited from cursor resource allocation;
this changes the following roll and prize layout. The dependency is now
identified and retained explicitly, without a fixture constant or CPU-emulation
workstream. Chip partial redraw, yard/egg balloon timing, nut phase, held-worm
image, strict nature presentation and full audio parity also remain open.


### Theater sound/presentation delivery (2026-09-29)

Build `c6f3a650aaaa` restores 33 missing cues; all 73 observed original
sound sources occur in order. All 29 theater and 14 notebook endpoint images
and compared states still match. Curtain/token sequences, narration ordering
and safe room-return handoff are delivered. Full81-suite batch and 183
environment states pass. The independent intermediate-display audit matches
309/580 original interval-local images; remaining displays, exact
timestamps, repeated-source event completeness and full audio waveform remain
open. See `../treehouse_theater_sound_journey.md`.


### Nature sound feedback delivered (2026-09-29)

Build `a44564be50d4` restores 15 missing J10 editing cues. The J10
editing and J11/J14 guessing/prize/room journeys contain all 17 and 57
observed original sound sources respectively, at original rates and order.
All 21 editing and 14 quiz image/state checkpoints pass. Full sound timing,
repeated-source event completeness and rendered waveforms remain open.
All 82 integrated suites pass. See `../treehouse_nature_sound_journey.md`.


### Board sound and input delivery (2026-09-29)

Build `73a6d9d9cf5c` restores J12/J13 roll, movement, robot, balance and
chip feedback plus immediate offer hints. Wrong-stack presses interrupt the
trade hint without approving a trade. All 236 money and 480 chip observed
source/rate events match. Money: 25/25 RGB/state. Chips: 49/49 state, 48/49 RGB;
the 312-pixel partial redraw remains. There are 83 passing same-build suites
with one documented fixture rerun, plus 183 environment states. Full sound and
intermediate timing remain open. See `../treehouse_board_sound_journeys.md`.


## Maze automatic-hint input delivered (2026-09-29)

Delivered `032490fa50b5a1e7141a3910f30d3e6a934fecfb91776c76ffc534bc0d0e3e8b`. Fixes lost canvas presses during automatic maze auditions. Eleven native RGB/state checkpoints match through victory. All 184 observed original sound sources/rates match between inputs. Thirteen unmatched browser starts and early victory-song timing remain recorded; full audio/timing parity is not established.

All 84 suites pass in one immutable-build batch, including a paired original-scheduled maze journey and fresh desktop/touch hint input. All 183 environment states pass; 23 additional reports retain their prior outcomes. Known strict/native failures remain. Previous live files are backed up and the served HTTP hash matches. See `../treehouse_maze_sound_journey.md`.


## Piano and maze transfer delivered (2026-09-29)

Delivered `57b4673bf421a0deaf06ba9a624607e650edd38576f1abba84ee71947c923917`. Restores original smoke and child bucket transitions at both piano/maze boundaries. All 62 transfer compositions match original images in order in each full/skip route. Full entry improves from 21/46 to 45/46 RGB checkpoints; stable tutorial/return/reentry state matches. All 18 full-route and 13 skipped-route observed sound sources/rates match between inputs. Actual smoke output is verified; full timing remains open.

85 suites pass on identical candidate HTML: 84 from the full batch plus the journey rerun after waiting for the restored return animation. The failed batch is preserved; this is not a second complete batch. Original transfer frame order and entrance/exit/skip journeys pass. All 183 environment states pass; 23 additional reports retain prior outcomes. Full entrance reports retain their cursor and intermediate RNG timing failures alongside all previous strict/native failures. Previous live files are backed up and the served HTTP hash matches. See `../treehouse_maze_entry_transfer.md`.


## Maze treehouse exit delivered (2026-09-29)

Delivered `8a107c9eb4a91d13b19b36312d0fae0932eb965d011477836abffd7e5aec067b`. The original top-right maze exit now returns to the treehouse using the music activity return transition. The adjacent control still returns to the piano. Both desktop and touch victory exits finalize and persist the replacement song/history. Play and victory native sound observations match all three sources/rates between inputs; exact cue timing and full waveform parity remain open.

All 85 registered suites pass in one immutable-build batch, including 53 ordinary maze exit/save/reload checks. All 183 environment states pass. The 23 additional comparisons retain prior outcomes. Both new maze exit replays match all 14 RGB images and preserve destination, random state and song history; six balloon-state timing mismatches per route remain explicit failures. Previous live files are backed up and the served HTTP hash matches. See `../treehouse_maze_global_exit.md`.


## Board entry and piano corrections delivered (2026-09-29)

Delivered `9a67a26e9613d5be536ba5578127717430f22ee64cbbb112d1553b211de7c65d`. Delivered original temporary listening-key notation, original tempo hit boundaries, and board preparation before options. Board entry preserves imported player levels until Play. Both maze treehouse exits retain 14/14 matching images and their six known balloon timing mismatches.

All 86 registered suites pass on one immutable build; all 183 environment states pass. The 23 additional comparisons retain their previous outcomes. All 30 piano checkpoints match RGB and music state. The activity tour matches 22/27 images and active gameplay/random state throughout; ten room-object timing mismatches and five image mismatches remain failed. All 58 observed tour sound sources/rates match between player inputs; exact sound timing remains open. Previous live files are backed up; served HTTP hash matches. See `../treehouse_activity_tour.md`.


## Maze difficulty persistence delivered (2026-09-29)

Current served build: `2d29766c93dda302b3e0c0d618a36f40eec6f91a92bbfbf2655a77206093869b`. Difficulty now survives ordinary piano exits and maze reentry in both directions. All 87 regression suites pass on the delivered build, including 12 new desktop/touch difficulty checks. All 183 environment states pass. The paired activity tour retains the same five image and ten room-object mismatches, with final maze reentry matching. All 58 observed tour sounds match sources/rates between inputs. Strict timing remains failed. Other supplemental comparisons retain their previous-build hashes and are explicitly historical, not newly verified. See `treehouse_maze_difficulty.md`.


## Theater caption sequencing delivered (2026-09-29)

Delivered `fe0819316c49aeff41b013108debd70cf1ec7659e4ef49894edcb7d4698b8434`. The sentence now stays unchanged until both tokens finish moving. All 88 regression suites and 183 environment states pass on this build. The caption fix restores 35 complete shuffle frames and four manual-drag frames without losing prior native image matches. Theater now matches 348/580 intermediate images, all 29 endpoints/gameplay states and all 73 observed sound sources/rates. The remaining 232 images and strict nature 614/984 callbacks remain explicit failures. Other supplemental evidence retains previous-build hashes and is not claimed as freshly verified. See `treehouse_theater_shuffle_caption.md`.


## Held piano input delivered (2026-09-29)

Delivered `a89b3f65ac50ce1a548fa6618f795261e0a79507c057e3a87b4a305d9747d322`. All 89 regression suites and 183 environment states pass on this build. Held piano notes and idle interruption match 17 native full-image/music/random-state checkpoints; 18 fresh mouse/keyboard/touch checks pass. The 30 short-note and 22 native authoring/playback checkpoints pass. Identified before-input frame matches prove interval membership, not equal input latency. Theater remains at 348/580 intermediate images; strict nature remains at 614/984 callbacks with 12 missing displays. Historical supplemental evidence retains its original hashes; full fidelity is not established. See `treehouse_piano_held_input.md`.


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


## Earned magnifying-glass return delivered (2026-09-29)

Delivered `b5744fce90a3433acad289ecebe0498dccfd854dbbe794a53ab11f82e9462352`. All 96 regression suites and 183 environment states pass. An earned magnifying glass now returns through original floor placement after the child uses it, preserving its position through room visits/reload and its placement random draw. Ten fresh mouse/boy and touch/girl checks pass; the previous build fails six. The uninterrupted quiz/prize/use/revisit comparison preserves all 22 random checkpoints (previously 18), while full state improves from 14/22 to 16/22. Images remain 16/22; balloon timing and click/overlap rendering differences remain explicit failures. Strict nature remains 614/984 callbacks with 12 missing displays; theater remains 385/580 intermediate images. Money-loss RNG, other resource lifetimes and whole-session audio/timing remain unresolved. Unrefreshed supplemental reports retain their prior build hashes; full fidelity is not established. See `testing/treehouse_earned_prize_return.md`.


## Robot reward route and warning completion delivered (2026-09-29)

Delivered `9b6d63debe08a863c5a6ba57bbe99342cc2c96dfc44668cdf175f32249990d3e`. 97 regression suites and 183 environment states pass on one immutable build: the full batch passed 96 suites, and the exterior suite passed after replacing two immediate-increment assertions with original warning-completion ordering. The failed batch is preserved. Hunger/fatigue increments, urgent retry deadlines and the other need grace period now follow warning completion. All 576 branch checks pass (164 failures on the prior build). A complete original robot quiz/prize/shelf/theater journey matches 33/35 images and all 35 random states; three room endpoints retain balloon-state differences, and full state remains 32/35. The prior hunger mismatch is fixed. Strict nature remains 614/984 callbacks with 12 missing displays and theater remains 385/580 intermediate images. Money-loss RNG, balloon clearance/return timing, full audio timing and other required integration remain open. Unrefreshed supplemental evidence retains historical build hashes; full fidelity is not established. See `testing/treehouse_robot_prize_and_need_warnings.md`.


## Character balloon clearance delivered (2026-09-29)

Delivered `efc57996b72588e9144516acede437714c79840d1e67b71080dad3968d645bfc`. All 98 regression suites pass in one immutable-build batch; all 183 environment states pass. Character actions now clear overlapping balloons before constructing and starting their original scripts. All 84 focused checks pass; the previous build fails 30. The focused native warning improves from 2/5 to 5/5 complete images, with 3/5 checkpoint states matching. Two timing-state differences remain. The uninterrupted robot prize route retains 33/35 images, 32/35 states and all 35 random states; the earned human prize route retains 16/22 images/states and all 22 random states. Strict nature remains 614/984 callbacks with 12 missing displays, and theater remains 385/580 intermediate images. Money-loss RNG, room-return timing and full audio/presentation timing remain open. Supplemental reports not rerun retain their historical hashes; full fidelity is not established. See `testing/treehouse_character_balloon_clearance.md`.


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
