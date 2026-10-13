# Maze victory, activity tour and piano input

## Scope

A single original won-maze snapshot is followed by ordinary mouse inputs:
treehouse exit, piano revisit and key, room, nature, room, theater options,
room, board options, room, telescope, room, piano and maze reentry. The browser
receives the same inputs and elapsed game ticks after one initial snapshot.
There are no per-activity resets. This checks navigation and continuity;
the already-won starting snapshot does not prove a full session from launch.

References under `testing/output/treehouse/`:

- `maze-activity-tour-native-a`: uninstrumented original.
- `maze-activity-tour-audio-a`: read-only sound observation. Full WAV, callback
  timeline, images, actions and checkpoint state match the control.
- `maze-activity-tour-browser-a`: previous served build `8a107c9eb4a9`.
- `maze-activity-tour-state-d`: candidate D with board and music fields compared
  in addition to shared state and full RGB image membership.
- `maze-activity-tour-sound-d`: all 58 observed original sound sources/rates
  occur in order between inputs. One raw checkpoint timing miss remains.

## Findings and changes

### Board entry must prepare a board before opening options

Overlay 3 entry calls `0933` (player/position/balance preparation) and `0625`
(drawing and three road substitutions) before `0AC5` (options). The browser
previously waited for Play. Its initial options backdrop was wrong and its
random stream diverged before the subsequent telescope and maze visits.

`BoardGame.prepareGame` now serves entry and Play. `enter` opens options over
the prepared board; `start` also begins its introduction. Every activity entry
uses `enter`. Candidate D matches the original board image and all captured
board fields and restores the shared random stream through the later piano
visit. The random state still differs during the final maze hint.

The full D regression found a persistence defect in the new code: robot-level
normalization ran on entry. Source now preserves imported/saved levels on entry
and normalizes them only when Play starts, retaining the previous Play behavior.
Candidate E contains this correction; all 13 persistence checks and six
preferences images pass in `activity-tour-persistence-e2`. It is now delivered after the full regression passed.

### Listening keys display temporary notation

Overlay 1 `19DD..1B05` paints a quarter note at short-score index 3 with its
letter, or at advanced indices 6 and 21 without letters. Release stops sound
and restores the piano key but leaves notation visible. `0207..0274` restores
the score when timer 2018 expires (120 ticks) or a non-key control is used.

The browser now retains the audition pitch independently of the held sound,
uses its existing original glyph renderer, and restores the score on expiry
or relevant controls. It leaves the song data unchanged. Expiry waits until
the held note is released. Long held-input/idle-animation timing remains a
separate audit requirement.

### Canvas tempo clicks use original boundaries

Overlay 1 `3736..378B` compares pointer X against the four words at music
data offset `0156`: 55, 64, 73, 82. Previous nearest-marker rounding selected
the wrong tempo in part of each region. Build extraction now supplies these
boundaries to the canvas input handler.

## Focused piano evidence

`piano-note-native-b` contains 30 original checkpoints: held/released keys,
expiry, sharp/flat naming, score sizes, page changes, contents audition and
eight clicks on either side of the four tempo boundaries. The initial idle
deadline is read from the original snapshot, like the other music verifiers.

`piano-note-state-baseline-b` fails 12 notation images and five tempo-state
checks on the old live build. Some incorrect tempo selections still satisfy
image membership because the previous correct image occurred before the click;
comparing the final actual song/tempo state catches them.

`piano-note-state-fixed-d` passes all 30 RGB, active-music, history and random
state checkpoints. `verify_piano_note.py` is registered in the full regression,
bringing it to 86 suites. This is bounded evidence, not full input/timing parity.

## Delivery and remaining work

Delivered original temporary listening-key notation, original tempo hit boundaries, and board preparation before options. Board entry preserves imported player levels until Play. Both maze treehouse exits retain 14/14 matching images and their six known balloon timing mismatches.

All 86 registered suites pass on one immutable build; all 183 environment states pass. The 23 additional comparisons retain their previous outcomes. All 30 piano checkpoints match RGB and music state. The activity tour matches 22/27 images and active gameplay/random state throughout; ten room-object timing mismatches and five image mismatches remain failed. All 58 observed tour sound sources/rates match between player inputs; exact sound timing remains open.

Delivered `9a67a26e9613d5be536ba5578127717430f22ee64cbbb112d1553b211de7c65d`; see `activity-tour-delivery-e/report.json`.

The final maze mismatch in the earlier tour reports was a fixture defect: its initial snapshot restored hard mode but left the entry difficulty preference false. The corrected `maze-activity-tour-state-e2` restores that preference and compares active maze fields. Maze reentry now matches pixels and game/random state. Earlier failed reports are preserved. The tour still fails on room objects and telescope animation. Strict redraw timing and complete audio waveform requirements remain open.
