# Board-game sound and input audit

The previous turn delivered nature feedback in `a44564be50d4`. This audit
delivers board feedback in `73a6d9d9cf5c`; see the delivery evidence below.

## Captures and comparison scope

`capture_board_audio_journey.py` replays the original completion captures and
observes active digital sources at the existing safe video callback. The money
and chip recordings (`board-money-audio-native-a`, `board-chips-audio-native-a`)
both preserve their controls' full WAV, callback timeline, PNGs, actions,
decisions and ending. Controls are `board-native-completion-a` and
`board-native-chips-b` respectively.

The old browser replay settled animations then idled 420 ticks. That is too
short to compare original reminder counts. The optional `--native-waits`
replay instead reads recorded mouse-press callback ticks and checkpoint RAM
ticks, applying those waits to real canvas inputs. This is test data only;
runtime sound and animation never read reference recordings. The first version
of this harness initialized the roll reminder red; it is now explicitly loaded
as white with its original remaining timer, validating that initial fixture
condition. The failed first reports remain preserved.

`compare_board_audio_events.py` requires identical control media/state and
compares decoded sound identity, rate and order per input interval. It preserves
unmatched starts. Identical adjacent starts at a single browser scheduling
instant have zero intervening output and are reported separately; only the
last is used for matching observed native sounds. Different-source same-tick
replacement is still flagged. This does not establish complete original start
counts or full rendered waveform/timing equality.

## Demonstrated runtime differences

- The roll button and each of eight animated faces call sound **1045**:
  overlay 3 `017B–017F`, `12B7`, `1380–1384`. The clone played only one cue.
- Each road edge starts **1020 + player index**, then stops playback at arrival:
  `18E9–18F0`, `1986–198A`. Decrementing the move count calls the same sounding
  counter painter `12D2`. These movement/counter sounds were absent.
- Robot rolling pauses **60 ticks**, then waits through sound **1011** before
  moving: `02D8–02E9`. Both pause and sound were absent.
- Money credit redraws the updated balance with sound **1025**:
  `219F–21A9` calls `19EB` with its sound flag enabled. The cue was absent.
- Incoming chips and carried replacement chips use **1023**, wait 20 ticks,
  then update the stack with **1025**: `263F–2718`, called after travel, also
  from carry `2B9C`. Incoming **1023** and the carry pair were absent.
- Offer delivery clears the reminder timer at `2E16`; it immediately highlights
  and sounds both choices before starting its 300-tick wait. The clone instead
  delayed the first pair by 300 ticks.
- Exchange hint frames use interruptible waits (`2776`, `281E–282C`). A wrong
  stack click can shorten that animation without approving the trade. The
  clone ignored such input until its shape deadline; candidate C interrupts
  the hint, while retaining stack validation and the following 60-tick pause.

## Evidence so far

Money baseline with the original waits (`board-money-audio-baseline-b`) misses
100 of 236 observed sources. Candidate A (`board-money-audio-comparison-a`)
misses 14, all from the delayed first offer hints. It also flags the two
identical initial same-tick roll calls; the comparator now reports these
zero-duration restarts separately as described above.

Chip candidate A (`board-chips-audio-comparison-a`) misses 20 of 480 observed
sources: 18 initial offer hints and two repeated trade hints. All gameplay and
random states match; the known step-15 partial redraw remains 312 pixels
different. Candidate B fixes offer hints; candidate C also fixes hint input
interruption. The completed comparisons and delivery are recorded below.

Full audio sample scheduling, repeated-source completeness, exact intermediate
presentation, the known chip redraw and the separate money-loss RNG dependency
remain open. No CPU-equivalence workstream is added.

## Delivered candidate C

Delivered `73a6d9d9cf5c48401c62c3b09b869b14548c7e9f07657b16755230a86c75368e`. All 236 money and
480 chip observed original sounds occur in source/rate order with no missing
observations or flagged different-source same-tick replacements. All 25 money
images/state and all 49 chip states match; chip step-15 retains its 312-pixel
partial redraw. All original capture controls match.

Both car effects are silent on the old build and audible on candidate C. Their
first 2,000 output samples match the original with one bounded alignment each
and no gain fitting. Reports: `board-movement-output-baseline-a` and
`board-movement-output-fixed-c`. Input latency and entire waveforms remain open.

83 suites pass on identical candidate HTML: 82 from the full batch plus the boardgame rerun after correcting stale fixture state. The failed batch is preserved; this is not a second complete batch.
The fixture correction resets offerHint/nodeHint between independently loaded
snapshots. All 15 original screenshot assertions remain exact. All 183
environment states pass; all 23 extra reports retain their outcomes. Previous
live files are backed up and the served HTTP hash matches. Full parity remains
false. See `board-feedback-delivery-a/report.json`.

Post-delivery `completion-gate-bl.json` confirms the served file and all
same-build suite results, while retaining failure of full native journey,
strict timing, audio and integration completion. The overall goal stays active.
