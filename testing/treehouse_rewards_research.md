# Treehouse rewards and persisted activity state

## Primary evidence

This report uses the pinned DOS v1.1 executable and archives in `testing/output/treehouse/source/The_Treehouse_1991.zip` (SHA256 `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`). Source addresses below are offsets in unpacked resident image unless prefixed overlay2/3/4. Relevant listings are in `output/treehouse/research-resources/`; tables and ordinary-input captures are in `output/treehouse/research-rewards/`. Main DS image base is321D0; shared state is image31690. No runtime code or captured RAM was modified.

## Shared reward chooser

ResidentAEC7 is used by nature (overlay2:2F3D) and board game (overlay3:22B). It accepts winner role and two screen rectangles; role2 is robot, all other roles use the human prize pool. Return1 means a prize was chosen; Esc/exit returns0. There is no separate chooser SCR: it is composed from original shapes, text, input rectangles and drawing primitives.

For robot, load TH SHPL960 and use exactly six fixed choices0..5, in order. For a human, fill six slots with six **distinct** random integers0..7 (inclusive random7, reject previously selected duplicates), storing those identities in DS57CC. The slot number is not necessarily the object identity. Human roles0/1 use the same prize pool.

The chooser uses small prize pictures; clicking one first presents its corresponding large picture, then animates the small picture toward its destination. Tables are DS5F6 (group selector), DS64A (small ordinal), DS69E (large ordinal), with robot index offset21. Original groups are TH870,900,930,960, loaded into DS577C..5782. Ordinals are group-relative, one-based.

| Prize identity | Group | Choice small ordinal | Presentation large ordinal |
| --- | ---: | ---: | ---: |
| Human0 | TH870 | 7 | 1 |
| Human1 | TH870 | 8 | 2 |
| Human2 | TH870 | 9 | 3 |
| Human3 | TH870 | 10 | 4 |
| Human4 | TH870 | 11 | 5 |
| Human5 | TH870 | 25 | 6 |
| Human6 | TH900 | 3 | 1 |
| Human7 | TH900 | 4 | 2 |
| Robot0..5 | TH960 | 7..12 | 1..6 |

Exact choice rectangles come from image2F0F0, as selected by resident84BB. Bounds are `(top,left,bottom,right)`, with exclusive bottom/right. Nature scene9 uses records0..5. Money uses records6..11; Chips records12..17. Full machine-readable extraction: `output/treehouse/research-rewards/tables.json`.

| Slot | Nature | Money | Chips |
| ---: | --- | --- | --- |
|0|(54,32,76,62)|(154,226,174,254)|(153,226,174,265)|
|1|(54,64,76,94)|(154,254,174,280)|(174,226,196,265)|
|2|(54,96,76,126)|(154,280,174,308)|(98,274,123,313)|
|3|(78,32,100,62)|(174,226,194,254)|(123,274,147,313)|
|4|(78,64,100,94)|(174,254,194,280)|(147,274,171,313)|
|5|(78,96,100,126)|(174,280,194,308)|(172,274,196,313)|

Each cell is cleared white15 and its small icon centered by6CEE, then drawn in mode10 (transparent). Center formula for positive screen coordinates is `floor((left+right)/2)-floor(shapeWidth/2)` and the corresponding Y formula. Hover alone does not select. The reminder8456 flashes every card in order red12, plays random sound1050..1055, waits8ticks, then redraws white; AEC7 sets timer201A=480 and repeats this sequence when it expires. A click redraws the selected card red and waits12ticks before presentation.

The caption literal at DSA96 is `Pick a Prize`. Winner portrait is groupDS52E4+2*role, relative shape2: role0 uses selected BOY/GIRL20200, role1 TH22200, role2 TH24200 in the board activity. MainAEC7 also clears both caller rectangles and restores the original board panel marking (MODULES4000 ordinal13+gameType) before showing the winner and caption.

### Selection presentation and state change

ResidentB228 onward saves the affected background. Robot selection additionally saves game rectangle10, displays the robot winner there, sets `DS55F8[slot]=1` and `DS52F6=7`. The mask7 makes telescope view3 the only unseen view on the next visit.

It starts sound10024, centers the prize's large ordinal in the presentation rectangle, waits120ticks, then restores the saved background and stops the sound. It centers the small choice shape at source and destination, plays10035, and calls original6DA9 with `(eraseAtEnd0,frameDelay3,stepInterval8)` to move it. The standard source helper uses a one-axis-per-step path and saves/restores moving sprite backgrounds. At arrival it overlays TH900 relative ordinals23,24,25 with4ticks each, sounds10034 between phases, and restores the background. Robot adds60ticks before restoring its winner picture; human calls857B(prizeIdentity,1), creating or resetting that room object. Re-selecting an owned human item resets its room placement/quantity rather than adding an arbitrary second copy (857B scans existing object type first).

Human room object initialization8637 assigns type, quantity1, roomFlag1, and the original rectangle from DS7BE+8*type; scheduling helperB8A3 is then invoked. Object identity must be preserved for original interactions.

## Robot shelf lifetime

The robot's six shelf flags at DS55F8 are sticky for the running session. **They are not part of STATUS.DAT.** Resident source references this array only at telescope2602 (read) and chooserB276 (write), and none of the three status serialization regions overlaps it. DS52F6's telescope visited mask is also outside STATUS.DAT. The earlier room follow-up's use of “persistent” meant collected state within the session and should not be read as evidence of disk persistence.

Telescope prize rendering and position tables are described in `treehouse_room_followup.md`. The six small shelf pictures are TH967..972; this is the same small art used in the robot chooser. Telescope robot uses MODULES SCR3610/SHPL3600, first pose3601; collected icons themselves do not have separate recovered scripts.

## STATUS.DAT exact layout

Writer7CDD and reader7DCB operate on three contiguous file regions. The packaged file is2704bytes; there is no length header or checksum.

| File offset | Length | Original RAM | Meaning |
| ---: | ---: | --- | --- |
|0|0x8EA(2282)|3169:0048|Shared saved activity state|
|0x8EA|2|DS556C|Movable room object count, u16|
|0x8EC|0x1A4(420)|DS5830|21 room object records,20bytes each|

Object record: u16 type, u16 quantity, u16 roomFlag, four i16 rectangle words(top,left,bottom,right), u16 background handle, u32 scheduled time. Preserve opaque bytes on round trip, including inactive records and saved transient fields. A meaningful modern serializer should not treat old memory handles as valid handles after restart.

Song used flags occupy the first86 file bytes (shared state48..9D). They are separate from SONGS.DAT. Other state includes music selections/modes, board/nature settings, theater data and unknown/reserved bytes. Retain all unknown bytes when importing/exporting native files.

Reader failure zeros the first0x8EA state bytes, sets selected phrase words toFFFF, initializes phrase order via overlay4:240D(0), enables global speech/sound fieldsAA/AC, sets board/nature opponents1, resets object count, and creates standard objects9/10. Packaged defaults differ: board opponent2(robot), among other ordinary saved preferences. Do not conflate packaged STATUS with missing-file initialization.

## Theater persistence (no named saved-story files)

Overlay4 has no file-opening/reading/writing API calls for a separate theater document and no recovered file-picker UI. It edits a single shared state inside STATUS.DAT; a fresh activity entry renders those retained values. File offset for each field below is `stateOffset−0x48`. All words are little-endian; negative sentinel is−1.

| Shared offset | Format | Meaning / packaged default |
| --- | --- | --- |
|406|i16|Mix Up enabled;0|
|408|i16|Props enabled;0|
|40A|4×i16|Selected phrase IDs in subject,action,place,time order;all−1|
|412|6×i16|Placed prop count per location;all0;capacity20 each|
|41E|120×4×i16|Prop rectangles indexed20*location+instance|
|7DE|120×i16|Original prop shape/group-relative identities, same index|
|8CE|7×2×i16|Actor translation(dy,dx) per location, including blank-stage slot;all0|
|8EA|4×i16|Sentence category order, permutation of0..3;[0,1,2,3]|
|930|i16|Last sentence validation code;0|

Choice mapping comes directly from MODULES STRL3000(subject8),3010(action8),3020(place6),3030(time4), all zero-based. Order holds category IDs, not phrase IDs. Prop arrays retain list ordering because it controls composition/hit testing. Source overlay4:2AD0 clears all7 actor offsets when changing subject. Prop rectangle insertion/deletion is in26B..4BC andC18..C9E; deletion compacts the list. Actor offset write is28B0/28D8. Order reset240D copies8bytes from one of six original permutations at DS113A; explicit argument0 selects canonical0,1,2,3, negative requests random0..5.

### When saved

- Theater options modal exit calls resident7CDD at overlay4:1D8C, including PLAY or Esc from that modal. This persists changes from previous editing plus options toggles.
- Global options exit calls7CDD at resident1C43.
- Normal program shutdown invokes callback637A, which calls7CDD (callback installed at364).
- Direct theater editor exit12C9 releases resources and returns to the room without an immediate7CDD call. Its shared state remains in memory and is saved by the above later events. Changes to phrases, props, positions or order do not each write a file.

No evidence supports separate named save slots or an explicit theater “load story” action. Modern browser persistence may save more frequently for reliability, but that would be a deliberate improvement over original write timing.


## Native comparison references and independent pixel checks

`robot-win` restores the existing fully delivered board reference, then plays through ordinary mouse choices, rolls and directed board moves until the robot wins57c against human37c. `robot-win/state/chooser.png` is the stable robot chooser. All input actions and each observed turn state are retained in run.json; no RAM values were written. Its exploratory amount-choice policy reads the coin arrays but its two Y positions both fall in the upper offer; therefore the recorded route should be described as upper-offer selections, not as proof of maximizing/minimizing amounts.

Independent original-asset checks in `check-chooser.py` give zero mismatched nontransparent pixels for the entire winner portrait and all six small prize icons:

| Asset | Origin(x,y) | Dimensions |
| --- | --- | --- |
| TH24202/SHPL24200 |257,115|21x25|
| TH967/SHPL960 |231,155|18x18|
| TH968/SHPL960 |257,155|20x19|
| TH969/SHPL960 |283,155|23x19|
| TH970/SHPL960 |231,175|19x19|
| TH971/SHPL960 |260,175|14x19|
| TH972/SHPL960 |282,180|24x8|

Original FONT1 caption has glyph origin(240,146), width54. Its black glyph mask also matches completely. Money presentation has both original offer interiors cleared white, retaining the outer board borders: rect14(19,226,102,308), rect15(109,226,194,308). Winner portrait centers in the top36pixels of rect15, and caption starts37pixels below that rectangle's top. The group4000 ordinal13 separator at(260,101) remains part of the original panel composition. This is an asset/font verification of the chooser elements, not a claimed whole-screen independent renderer comparison.

`robot-prize` restores the chooser, selects slot0 at(240,164), and captures presentation at successive50/150/350/1350callbacks plus settled state. `select-50.png` shows the large floppy-disk reward and the robot winner moved to game rectangle10(1,261,26,282). Source framing and exact intermediate timing should use its complete `frames.jsonl`, not the callback count in a label as an original tick count. It then exits the board and enters telescope through ordinary clicks. `shelf.png` proves selected flag0 produces TH967 at(103,67); all otherflags0, visitedmask changes7→15 on entry. `shelf-replay.png` records clicking the active telescope region to run SCR3610 with an owned prize.

### Actual native theater disk save

`theater-persistence` restores a previously edited sentence, opens options, clicksPLAY, exits to the room, reenters theater, and clicksPLAY again. Every capture retains choices `[0,0,1,-1]`, categoryorder `[3,1,2,0]`, optionsMixUp1/Props1 and validation5. The resulting sentence remains “Blows bubbles in the jungle the baby.”, proving it retains invalid order rather than normalizing on reentry.

DOSBox wrote an actual modified `THETREEH/STATUS.DAT` into `theater-persistence/state/reference-v1.pure.zip`. Its extracted `status-written.dat` is2704bytes, SHA256 `e75b976bb5134e596efa8223020dc0c8fa126a1f7f76cda4def71d61d82ab16e`; decoded choice/order/validation offsets match the observed state exactly. This is disk-format evidence, in addition to within-session reentry. A subsequent fresh-process capture `theater-restart` starts the original executable with this DOS-written save ZIP in its normal save directory (no RAM restoration or mutation), follows title→room→theater→PLAY through ordinary mouse input, and recovers the same choices `[0,0,1,-1]`, order `[3,1,2,0]`, validation5. `theater-restart/state/editor.png` shows the retained invalid-order sentence. This closes the native cross-launch save/read comparison.

### Human chooser and awarded room object

The nature researcher supplied its ordinary-input winning state `research-nature/quiz-win-capture/state/correct-guess.state`. New `human-prize` captures click the winner badge, open the human chooser, choose its first slot, and return to the room. Native choice identities are `[2,6,7,0,3,4]`, each distinct. First slot therefore awards object2 rather than object0. The object count changes5→6; the new record is type2,quantity1,roomFlag1,rect(148,175,174,203), and the magnifying glass is visible in `human-prize/state/room.png`.

The nature presentation panel is(6,30,116,128). Caption origin(52,43) matches the full FONT1 black mask. All small icon nontransparent pixels independently match originals: TH879@(39,58),903@(71,55),904@(104,55),877@(37,80),880@(73,83),881@(105,81). `check-chooser.py` reproduces these checks. `select-50.png` and `select-250.png` plus all changed frames capture its large-picture and transfer sequence.

## Board payment, win/loss, and restart completion

Source is overlay3 unless marked resident. These paths extend the earlier `treehouse_boardgame_research.md`; native full board route `robot-win` contains ordinary payments, a complete win, chooser entry and reward-triggered restart.

### Landing on a payment square

Landing1CCC resolves chance-node25 into24gain or26payment with a random coinflip, generates the signed amount through34B5, clears/redraws the story heading via2C90/2D3C, and displays original STRL4013 narrative for payment. It speaks sound1027 for nonpositive amount (1028 for positive). Payment bypasses the two-offer selection phase.1E38 formats the negative amount with33EE, draws the `Pay ` prefix plus its positive magnitude in upper offer rectangle14 with horizontal inset4, speaks the amount through residentD303, then calls Money21B4 or Chips24A2. Choosing a payment does not require a confirm button.

Money21B4:

1. Let payment=abs(signedAmount). Rebuild top-offer coin counts greedily using denominations `[100,50,25,10,5,1]` from DSF54. This replaces the earlier randomized denomination breakdown.
2. If balance<payment, set gameOver1, wait60ticks, and clamp payment to balance. If balance is already0, return without animation. Equality does not set gameOver.
3. Prepare the payment display through3A1B(0,0,0), subtract the entire payment in one state update, and redraw balance19EB(1,white15).
4. Wait60ticks. Load MODULES4400 ordinal14 (moneybag4414). Compute the centered25x24 top-offer position with resident6BF4. Play10035, then fly the bag **from balance point(x204,y48) to the upper offer's centered origin**, reversing credit's direction. Resident6DA9 args(eraseAtEnd1,delay4,step8); same shape for both source/destination.
5. Play1024. Temporarily clip rendering to screen bottom92, redraw upper offer with signed debit through2FBF, then restore clipping. No per-coin input or carry/borrow is needed for Money mode.

Chips24A2:

1. Clear the top-offer chip counter, clamp payment to balance and setgameOver iff balance<payment.
2. Process decimal units, then tens, then hundreds (digit indexes2,1,0). For each chip call2732 to ensure the source stack has that digit, entering the original interactive borrow flow if required.
3. Subtract1/10/100 per chip, update its stack via3810, play1025, wait20ticks. Clear the source chip strip at its stackX,y41,width13,height3. Fly the original denomination chip into the next top-offer grid cell using6DA9(erase0,delay2,step8).
4. Play1023, wait20ticks, continue until the clamped payment has been removed. Interactive borrow semantics and exact exchange sprites are already documented in `treehouse_boardgame_research.md`.

Native payment references in `robot-win`: `turn-2-move.png` finishes human18→15; `turn-11-move.png` finishes human22→21; `turn-17-roll.png` finishes robot47→46. Each complete incoming roll/move/payment animation is retained in frames.jsonl. These are evidence of ordinary automatic Money payment, not of the insufficient-balance branch. That branch is source-recovered here and has not been separately captured.

### End state and winner ownership

After any settlement,1F93 tests gameOver. Positive credit sets it when new balance>=goal. Payment sets it only on insufficient funds. The code releases the saved active-car background without restoring it, leaves the car drawn, resets the heading, then checks remaining balance:

- Nonzero: display original `This player WON!`; play1005 and11164, additionally11161 if balance exceeds goal, and speak the target. Paint balance area red12 and redraw its Money symbol/amount on red. The original roll control displays TH900 relative22 (TH922 winner ribbon) while gameOver is nonzero.
- Zero with gameOver: display `This player LOST!`, redraw zero balance, and **toggle active player**. The other player becomes prize recipient, even though the displayed heading describes the player who just lost. Zero balance without gameOver continues normally.

Settlement finally clears reminder timer201A and sets remainingSteps5276=−1. The captured robot win is57 against target50; its full win state is `robot-win/state/turn-22-choice.png`.

### Award control and replay

Clicking the award/roll hotspot2 after gameOver enters overlay3:1E0. It sets roll0, redraws the winner ribbon, restores the separate saved animation-area background5696, determines the current winner role throughA98, then calls residentAEC7 with original offer rectangles14/15. This is **direct prize choice**, not a separate “Play again?” confirmation.

If chooser returns0 (Esc/exit), the activity exits. If a prize is selected, chooser returns1 and code23D calls90A:933 initializes new nodes/directions/balances/gameOver/first-turn,625 rebuilds the board with new special squares,16D7 draws cars,39D4 starts dashboard animation,201A resets. The existing Money/Chip, opponent and goal preferences remain. The next game is ready immediately, with no second action required.

Native proof: `robot-prize/state/selected.png` shows the new game at10c after robot prize selection; the earlier chooser and won state show57c. The user's room prize/shelf ownership survives this board reset. `robot-prize/state/room.png` and `shelf.png` follow exiting that new game.


### Exact Chips chooser panel geometry

DS4A14 points at segment308E. AF67 restores MODULES4000 relative ordinal13+gameType opaque: Money at x260,y101 (308E:0004); Chips at x263,y128 (308E:0008). The board caller passes game rect14 and15. AFAC selects rect15−gameType*8 for winner/caption, meaning Money rect15 `(109,226,194,308)` and Chips rect14 `(98,226,196,265)`. Winner subrect truncates bottom to top+36; caption translates that subrect down37. Chips therefore uses winner `(98,226,134,265)` and caption `(135,226,171,265)`. Both caller rectangles are cleared: Chips other panel rect15 is `(98,274,196,313)`. Large-prize presentation uses caller rect14, which is also Chips' left panel. Type2's large original TH873 definitively identifies the human prize as a magnifying glass, correcting the earlier visual guess.


### Separator correction and nature caller cleanup

The separator coordinates above are corrected after independent native comparison. The earlier note mistakenly treated a byte displacement as a word-array index. DS4A14 is correctly308E; the exact point pairs are 308E:0000=(48,204), :0004=(101,260), :0008=(128,263), :000C=(1,304), all `(y,x)`. AF67 indexes `4 + gameType*4`, so Money4013 is `(x260,y101)` and Chips4014 is `(x263,y128)`. The `(1,304)` point is not used by this chooser.

Nature clears its winner controls in the caller before residentAEC7, overlay2:2EE1..2F3D:

1. 3E27(1) plays sound1017 and flashes the top badge/ribbon red for8ticks through28CE, then draws it white again.
2. Wait60ticks.
3. 2979 fills game rect36 `(8,137,33,162)` white15. Thus all x137..161,y8..32 are blank in the chooser, including the underlying button/ribbon area.
4. 3DC8(1,0) redraws the selected class icon in its ordinary state if `0 < DS57D8 < 99`; fills game rect38 `(6,30,116,128)` white15; skips question-decoration reconstruction.
5. Fill footer DS0DBE `(125,8,135,164)` white15.
6. Set activeplayer DS5250=winner DS57CA, resolve portrait2851, and callAEC7 with rect38 and a null second rectangle. AEC7 clears rect38 again, then builds winner portrait, caption and choices. Candidate-grid pixels remain in place.


### Win ribbon and retained car: source correction

Independent chooser comparison resolved two incorrect earlier descriptions. Overlay3:12D2 first checks DS5810. When gameOver is nonzero, it centers TH900 relative22 (TH922) in game rect2 using mode10 and the supplied background color. Chooser entry1EA calls12D2 with roll0, sound1, background15; the resulting blue/black ribbon remains at the roll control, rather than the ordinary Money dollar picture.

Settlement1FA3 calls1698(0): this releases handle568C through resident436C, **without restoring its pixels**, so the current car remains visible. The nonzero1698 branch uses82B2 to restore; that branch is not used here. Chooser1FE restores a different handle5696. It was captured at3A48 from DSE86+8*gameType: Money `(19,226,102,320)`, Chips `(98,226,194,320)`. Treat these two saved backgrounds separately.
