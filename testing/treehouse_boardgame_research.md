# Treehouse DOS 1.1 board game research

## Sources and scope

Primary sources: original `testing/output/treehouse/source/The_Treehouse_1991.zip`,
unpacked executable `output/treehouse/disassembly/unpacked.bin`, instruction
listing `output/treehouse/research-resources/overlay3-disassembly.txt`, and native
captures under `output/treehouse/research-boardgame`. The activity is **overlay3**,
entry0. All plain code offsets in this note are relative to that overlay; main
resident offsets are identified separately. Original executable DS starts at
unpacked0x321D0. Fixed board tables use segment308E, base0x308E0. Runtime DS in
these synthetic RAM-0 dumps is0x323F0; the file is not physical-address-zero RAM.

The original activity is a road-board counting/comparison game, with Money and
Chip variants. It is not a conventional six-sided-die race to a finish square.
The player drives along directed roads, receives or pays amounts, and tries to
reach a selected balance. A robot can drive the opposing car; the child still
makes the amount-comparison choices on the robot's turn.

## Native coverage and actionable artifacts

- `entry-a/state/boardgame.png`: initial options, Money / robot / .50 goal.
- `start-b/state/started.png`: board after clicking PLAY checkbox.
- `roll-a/state/rolled.png`: question-mark control after rolling.
- **`turn-b`**: complete valid turn, reward choice, and robot movement.
  The explicit route, adaptive decisions, metadata, all callback frames, named
  frames, audio, and RAM snapshots are recorded. `move-2.png` is a lucky reward
  choice; `reward-chosen.png` shows 12 cents collected and balance22 cents;
  `next-turn.png` shows robot moved and awaits a comparison choice.
- `tables.json`: original numeric tables extracted verbatim for implementation.
- `adaptive_capture_b.py`: capture orchestration, not replacement game logic.

The earlier exploratory `land-a` and `turn-a` runs do not demonstrate a completed
reward: random starts differed, and short movement waits overlapped. Use turn-b
for the verified loop. Original random layouts differ between launches; do not
claim deterministic full-frame repeatability from a shared action prefix.

## Entry and options

Interior hotspot14 is `(top181,left138,bottom200,right223)`, safe click `(180,190)`.
The activity first constructs the board and then enters modal options `0xAC5`.
Options set active count25 and rectangle pointer308E:02C4. Escape / rectangle0
exits the activity. Rectangle17, **the PLAY checkbox**, starts the game. Its
bounds are `(160,151,175,169)`; clicking the word PLAY atx184 does not start.

All rectangles in tables.json are `(top,left,bottom,right)`, with half-open bounds.

| Options rectangle | Action / bounds |
| --- | --- |
| 0 | Exit:1,304,23,320 |
| 1 | Money:25,150,32,158 |
| 2 | Chips:37,150,44,158 |
| 3 | Friend:53,150,60,158 |
| 4 | Robot:65,150,72,158 |
| 5/6/7 | Player1 goals: y81/93/105, x150..158, height7 |
| 8/9/10 | Friend goals: y120/132/144, x150..158, height7 |
| 11..16 | Printed goal values, x257..284 |
| 17 | PLAY:160,151,175,169 |
| 18 | Money/chips illustration:29,126,41,147 |
| 19/20 | Player goal illustration:85,126,101,147 /124,126,139,147 |
| 21 | Friend goal section:118,126,154,284 |
| 22/23 | Player badges:86,164,102,178 /127,162,143,181 |
| 24 | Friend/robot illustration:50,126,75,147 |

Game settings reside at the segment referenced by DS:4ADA:
state:3EE is type (0 money,1 chips); state:3F0 is opponent (1 friend,2 robot).
Six words at state:3F2 are goal/difficulty indexes: three per game type, for
player0, friend, robot. Robot goal is copied from player0 on leaving options
(`0xE6C`). Choices map to **50,100,500** cents/chips (DS:E74). Starting balances
(DS:E7A) are Money `[10,20,100]`, Chips `[15,30,150]`.

### Original resources / composition

All IDs below are MODULES.DAT unless stated. Rendering must use original assets.

| Group | Contents |
| ---: | --- |
| SHPL4000 | SHAP4001..4014: board, counters, message panel, roll faces |
| SHPL4050 | SHAP4051: options panel,266x177 |
| SHPL4100 | SCR4100 and four boy dashboard frames |
| SHPL4120 | SCR4120 and ten friend dashboard frames |
| SHPL4140 | SCR4140 and two robot dashboard frames |
| SHPL4200/4210/4220 | SHAP4201/4211/4221,320x81 dashboard tops |
| SHPL4300 | SHAP4301/4302,93x57 transfer/reveal animation art |
| SHPL4400 | SHAP4401..4450: settings, coins/chips, road icons, cars |
| SHPL20200/22200/24200 | Character groups loaded for options illustrations |

Board compositor `0x625` fills the full screen with palette group0x80 color13
(VGA branch of main0x7308). Draw4001 at `(2,83)`, opaque. Draw the current
player dashboard (4201,4211 or4221) at `(0,0)`, opaque, with its own palette.
For Money, fill DS:E96 white, draw4003 at `(137,14)` transparent and4005 at
`(221,73)` opaque. For Chips draw4002 at `(221,8)` and4004 at `(221,73)`,
transparent. Current balance is then drawn by0x19EB. The question mark is
shape4425 centered in game rectangle2; positive roll values1..5 use4008..4012.
The blank count (zero) fills its rectangle white.

Draw current player's dashboard SCR `(205+playerIdentity)*20`, i.e.4100/4120/4140,
through0x39D4. This is a one-shot original script, not a new animation.

Options0xAC5 copies the current board, draws4051 centered within320x200 using
shared original centering (origin27,12), and overlays original character art,
checkboxes, goal icons and resource strings. Text baked into4051 is not a new
font. Checkbox marks are shared TH group's shape3 colored with SHPL4050 color5;
clears use its color1, portrait fills use color7. Options routines0xEAE,0xF64,
0x107D,0x13FB redraw the affected choice only. Goal text is STRL4000 for Money
and4001 for Chips; goal picture indexes in SHPL4400 are from fixed308E:038C:
`[31,30,28,19,20,18]` for Money3 then Chips3.

## Board graph and movement

There are24 board nodes, six columns by four rows. Their 30 input rectangles
(including6 building aliases) start at308E:0174. A signed-byte adjacency table
at308E:0264 holds24 rows of4, ordered **left,up,right,down**, with -1 absent.
This is a directed graph: do not add reverse edges. Exact data is in tables.json.
The six building aliases24..29 map to nodes `[6,9,11,19,20,22]` (DS:EA6).

Initialization0x933 picks random nodes until DS:F00[node]==0. Allowed initial
nodes are7,8,9,10,13,14,15,16; both players may occupy the same node. It picks an
available direction from the adjacency row, stopping immediately for directions
other than up. DS:52C4/52C6 hold player nodes, DS:5734/5736 directions, DS:52D8
is active player. Robot games always start player0; friend games randomize who
starts. Both balances are initialized and game-over DS:5810 cleared.

Human move flow in0x430..0x5AC:

1. Roll must be positive (remaining steps DS:5276).
2. Click an adjacent node: move one edge and decrement remaining steps.
3. Otherwise depth-first-search `0x15FB(current,target,remaining,path)` accepts
   a destination reachable in **exactly** remaining steps. It iterates the
   adjacency row in left/up/right/down order, takes the first matching path,
   permits repeated nodes, and animates every edge.
4. Once steps reach zero, call landing handler0x1CCC.
5. Invalid clicks run the original hint flash, not a move.

Car drawing0x1726 selects base shape index42 withinSHPL4400; up uses43, down44,
left mirrors42 horizontally. Player1 adds3*opponentIdentity, giving friend45..47
or robot48..50. Car is centered within the node rectangle expanded horizontally
3 and vertically1. Movement0x17EE advances two pixels per3 original ticks in
the chosen direction; it updates the stored node only upon arrival. Do not
issue another native click while this animation is still running.

## Roll and turn loop

Main control2 `(50,84,67,103)` is the question/roll button. The game starts with
DS:5276=-1 and DS:57C6=1. First roll keeps player0; later rolls call0x2D87 to
switch active player, rebuild that player's board/dashboard and run its SCR.
Thus turn progression is triggered by the next question-mark click.

`0x11A4` selects a result from these original weighted arrays (DS:F18 andF1E):

| Goal/difficulty index | Roll values |
| ---: | --- |
| 0 | 1,2,3,3 |
| 1 | 1,2,3,4 |
| 2 | 1,1,2,2,3,3,4,5 |

It animates8 values, waiting6,7,8,9,10,11,12,13 ticks respectively. Final value
is the selected result. Intermediate Money faces choose1..5 avoiding immediate
repetition and the final result on the penultimate draw. Chips use the weighted
array for intermediates. The roll sound is1045. Human car blinks three times
with12-tick halves after rolling. Robot moves automatically: random valid
neighbors for all but its final step, then choose the neighbor with the lowest
node type number (23 lucky preferred,24 gain,25 chance,26 payment), retaining
first direction on ties. The robot then uses the same reward selection screen
as the human; it does not choose the amount for the child.

## Node types and learning interaction

Default24 node types are DS:EAC, exported in tables.json. Codes are shape
indexes in SHPL4400:23 lucky,24 positive,25 chance,26 payment. Every board
composition0x625 copies defaults and replaces **three distinct random nodes**
with23. This happens again when switching turns, not just once per match.
Landing on25 randomly changes it to24 or26 before resolving.

Narrative resource ID is `3987+type`: 4010 lucky,4011 gain,4013 payment. The
original string function is passed index0, selecting an original random entry.
Use the resource strings directly. Positive and lucky events offer two reward
amounts in the right panels (game rect14/15); either can be selected. Both are
added faithfully; choosing less is not rejected. Feedback says MORE/LESS money,
MORE/FEWER chips, or SAME, then reveals both numeric amounts. Money is presented
as coin graphics before selection, including `???` labels. The native turn-b
capture proves the child selects the robot's reward too.

Negative events subtract automatically with a Pay message and transfer animation.
If payment **exceeds** current balance, game ends in loss and payment is clamped
to the remaining balance (`0x2210..0x22C8`). Paying exactly the balance can leave
zero without immediately losing. Positive reward checks new balance>=goal
(`0x1F51..0x1F90`). On win, heading is `This player WON!`; on loss,
`This player LOST!` (DS:F67/F78). Game over replaces roll control withSHPL4400
index22, and clicking it invokes the original play-again/exit flow.

### Exact amount generation (0x34B5)

Let R(n) be an inclusive uniform integer0..n. Code below gives first amount A
and positive offset D; second amount is randomly A+D or A-D, changed to1 if0.
Only negative events display A alone. Follow-up in
`treehouse_board_payment_rng.md` found that the common pair-direction random
draw still occurs and Money prepares coins for the unused second amount. The
payment branch leaves D uninitialized; this can affect later random state even
though D does not affect the displayed payment.

| Mode | Difficulty | Positive A;D | Lucky A;D | Payment A |
| --- | ---: | --- | --- | --- |
| Money |0|5+R(6);1+R(1)|12+R(3);1+R(1)|-floor((5+R(8))/4)|
| Money |1|10+R(13);1+R(2)|24+R(6);1+R(4)|-floor((10+R(15))/4)|
| Money |2|47+R(78);1+R(4)|114+R(51);1+R(9)|-floor((50+R(75))/4)|
| Chips |0|4+R(4);1+R(1)|10+R(3);1+R(1)|-floor((4+R(4))/2)|
| Chips |1|8+R(9);1+R(2)|21+R(4);1+R(4)|-floor((8+R(9))/2)|
| Chips |2|37+R(58);1+R(4)|99+R(41);1+R(9)|-floor((37+R(58))/2)|

Money coin denominations are100,50,25,10,5,1 (DS:F54). To construct each
positive reward's coin representation, iterate descending denominations,
choose quotient floor(remainder/denom), and for the first3 denominations only,
randomly decrement a nonzero quotient by1 before subtracting its value and
continuing. Therefore equivalent sums can have different coin representations.
Original rendering0x2FBF and chip exchange controls need further line-by-line
mapping before full visual coverage can be claimed.

## Random source and reference limitations

Resident random routineD51:3BA6 (unpacked0x110B6) initializes its32-bit seed
DS:5290/5292 from BIOS INT1A clock ticks through0xE4A4. Each call advances
`state = (state*214013 + 2531011) mod 2^32`, then returns
`(state >>> 16) % (maximumInclusive+1)`. The unsigned-remainder helper is0xE5EA.
Deterministic comparisons must pin or record this native seed and all preceding
random calls; the current fixed-input captures alone do not pin it.

The authentic Money game loop is captured. Chip representation/exchange,
friend mode, all reward visual layouts, loss, win, and replay modal still need
native examples and renderer comparisons. The rules and tables above are
original executable derivations; no substitute minigame rules were invented.

## Exact composition follow-up

### Startup ordering and selected options

The very first entry calls0x933 (initialize starts/balances),0x625 (board), then
0xAC5 (options). It does **not** draw a pawn before initial options. After PLAY,
0x90A calls0x933 and0x625 again, then0x16D7 (pawn) and0x39D4 (dashboard SCR).
Thus the board's random icons and starting positions can change after PLAY.
The start screen requires the pawn and completed dashboard animation in addition
to the static0x625 composition. Current identity from0xA98 is0 for player0,
or configured opponent1/2 for player1; dashboard palette/shape group is
`4200+10*identity` and dashboard SCR is`4100+20*identity`.

The original options image4051 itself contains the wizard/cart, outlines,
headings, checkboxes and PLAY label. `options-source4051.png` shows this decoded
resource. The options rendering sequence0xB6A..0xBD2 is:

1. Draw4051 centered at27,12 over the already composed board, mode10.
2. Draw group20200 shape1 centered in options rectangle22 (player0 badge).
3. Update Money/Chip checkboxes; draw4400 group index16+type centered in rect18,
   clearing that illustration's rectangle with4050 palette index7.
4. Update Friend/Robot checkbox. Friend restores4051's second-goal section
   (clip rect21), redraws labels, draws group22200 shape1 in rect23; Robot clears
   rect21 with4050 color7, hiding the friend's goal section.
5. Draw selected opponent group (22200 friend or24200 robot) shape2 in rect24,
   clearing that rectangle with4050 color7.
6. Draw each visible player's three goal checkboxes (rect5..7 or8..10), then
   goal coin/chip icon in rect19 or20, using308E:038C table.
7. Draw the three amounts into rect11..13, and rect14..16 for Friend, using
   STRL4000 Money /4001 Chip. Original font isFONT1, top/left alignment,
   foregroundblack and background4050 color7. Preserve resource spaces.

`chip-a/state/chip-options.png`, `friend-options.png`, and `chip-started.png`
provide native Chip/Robot, Chip/Friend, and Chip/Friend gameplay examples. The
friend starts this captured game, demonstrating randomized first player in
Friend mode. These are additional original captures, not renderer comparisons.

### Board counter, messages, and roll faces

Original game rectangle table is the six common rectangles followed by13
variant rectangles, copied at0x933 from308E:00A4 (Chips) or308E:010C (Money).
The static zero-filled placeholders in tables.json/game_rects must be replaced
with the selected variant; do not use them directly for active gameplay.

- Exit uses shared loaded groupDS:5268 shape2 at game rect0 top-left.
- Options button usesSHPL4400 index1 centered at game rect6 top-left (source
  passes rect6.left/top directly, rather than calling centering).
- Message panelSHAP4006 is drawn at `(gameRect3.left,0)` mode10. Text isFONT1,
  black, horizontally and vertically centered in game rect4 `(5,117,26,215)`.
  Use original wrapping at98px. Goal prompt is formatted fromDS:EF0 orEDC;
  story/feedback replace that prompt through0x2D3C.
- Balance0x19EB uses digits hundreds,tens,ones: values are `floor(balance/100)`,
  `floor(balance%100/10)`, `balance%10`. Money stack sprites are4405/4406/4407;
  Chip sprites4402/4403/4404. Draw each stack at corresponding game rect7/8/9
  left,bottom-2, repeating upward every2 pixels. Digits use rect11/12/13.
  Money hides a zero dollars digit when below1 dollar; tens/ones remain shown.
  Chip higher-place zero digits are suppressed when all higher places are zero.
- Positive roll count N usesSHAP`4007+N` centered in rect2. Waiting-to-roll uses
  SHAP4425. Zero fillsrect2 white. Gameover usesSHAP4422. Hint flash alternates
  rect backgroundwhite15/red12 with12-tick intervals (`0x1391`).
- Nodes use original centering:shape`4400+nodeType` within node rect, transparent.

### Reward panels: source recipe plus native pixel checks

`0x2FBF(panel,amount,reveal,background,coinVariant,drawOr)` renders one panel.
Argument names correspond respectively to bp+10,+0E,+0C,+0A,+08,+06.

Money panel rectangles are top `(19,226,102,308)` and bottom `(109,226,194,308)`.
Fill with requested system background (normallywhite15; other choice becomes
 gray7 after selection). Coin counts atDS:5554 are two arrays of6 signed words,
indexed by denomination `[100,50,25,10,5,1]`.

Flatten coins by denomination order. For sequential coin i:

```text
cell.left = panel.left + 1 + 20*(i % 4)
cell.top  = panel.top + 17*floor(i / 4)
cell.width=20; cell.height=17
shape = 4430 + denominationIndex + 6*coinVariant
origin.x = cell.left + 10 - floor(shape.width/2)
origin.y = cell.top  + 8  - floor(shape.height/2)
```

Draw withSHPL4400 palette, transparent. The entire top coin area of native
turn-b/move-2 matches this reconstruction **pixel for pixel**. Bottom matches
apart from13 pixels belonging to the overlapping OR label; it is drawn last.
Selected coins later use lighter variants4436..4441, unselected coins remain
4430..4435 against gray background.

Footer text usesFONT1 black, centered horizontally within panel inset4px on
left/right, bottom aligned. For Money these origins simplify to
`x=267-floor(textWidth/2)`, glyph y93 top /185 bottom. Before choosing show
`???`; after choosing reveal formatted amount. Native glyph verification:
`???` width21 x257, `12 Cents` width37 x249, `11 Cents` width34 x250 all match.
`0x33EE` formats negatives with `Pay `, amounts>=100 as `$ %d.%02d`, otherwise
numeric amount plus ` Cent` or ` Cents` for Money; Chip suppresses the unit.

OR isSHAP4429 drawn opaque at `(260,101)` Money / `(263,128)` Chips, from fixed
pairs308E:0004 /0008. It overlaps the panel edge and is drawn after the panels.
Reward offers flash each panel's backgroundred12 for12ticks, restorewhite15,
and play distinct sounds10052/10051, then repeat hints after300ticks.

Chip panels are game rect14 `(98,226,196,265)` and rect15 `(98,274,196,313)`.
Chip cell i is13x13 at `(panel.left+13*(i%3),panel.top+13*floor(i/3))`.
The amount is broken into hundreds/tens/ones via0x1A4D; drawSHAP4420/4421/4422
at the cell top-left. Upper/left offer draws chip graphics; the second offer
initially hides them behind originalSHAP4414 before reveal. Chip footer uses
right alignment and two lines: left offer `%3d\r???`, right `???\r%3d`, where
known upper value is reward and known lower value is balance+reward. Revealed
format is `%3d\r%3d`; original draws a plus sign and horizontal addition rule.
Thus Chip mode teaches both comparison and addition, not just coin counting.
Chip exchange/carry animations are separate0x2392..0x2BB2 routines and have not
yet been fully rendered/compared in the rebuild.

### Chip comparison capture

`chip-turn-a` now captures an authentic Chip/Friend turn. Friend starts atnode14,
rolls2, moves15 then16, lands lucky, and is offered12 chips (left, resulting
balance27) or14 (right, resulting balance29). Before selection left shows12 plus
unknown total, right hides reward in a bag and shows total29. Selecting left
produces `You picked FEWER chips.` and balance27. Native frames are
`state/move-1.png` and `state/reward-chosen.png`. This independently corroborates
the addition/comparison layout and confirms that choosing fewer still awards
the chosen amount. Its full frame timeline also includes original carrying
animation as tens/units stacks change; exact exchange animation matching is
still unproven.

For precise base reconstruction, DS:E96 is `(64,144,75,209)` (white money digits)
and DS:E9E is `(75,226,87,299)` (chip digits). The game options icon4401 is drawn
at rect6.left/top directly. All other centered images should use the previously
recovered floor(midpoint)-floor(imageDimension/2) helper, not rounded division.
Money/footer font1 glyph verification is local to the specified regions; these
research captures alone do not establish full rebuilt-frame parity.


### RAM snapshot export and chip pixel corrections

`research-boardgame/native-states.json` exports 14 native snapshots with persistent
RAM variables, active rectangles, and selected screenshot-backed annotations.
Narrative text and selected reward are stack locals in0x1CCC, not stable DS fields:
reward pair `[BP-0x0C]`/`[BP-0x0A]`, selected index `[BP-8]`, narrative buffer
`[BP-0xBE]`. Annotated headers/reward choices in the JSON are not claimed to be
persistent raw RAM fields. Money offer values are independently recoverable from
the two six-denomination count arrays atDS:5554.

Chip counter0x1A91 clears each stack after expanding original game rect7/8/9:
left deltas[-6,-5,-5], right deltas[5,5,6], then top+1. Thus clear x ranges
[226,250),[251,274),[275,299), y[37,72).
Centered text0x178BD uses `top + ceil(height/2) - ceil(textBlockHeight/2)` before
font ascent. For currentFONT1 renderer, glyph origin simplifies to
`top + ceil(height/2) - lines*5`. Existing odd-height rectangles therefore match;
Chip digits (rectheight10) need glyph y77, not78. Horizontal positions unchanged.

SharedcheckboxgroupDS:5268 is SHPL6 loaded main0x0557..0564. Group ordinal2
is absoluteSHAP8 exit; ordinal3 is absoluteSHAP9 monochrome checkbox mark.

Native Chip reward footer glyph origins are y177 and187; text right edge is
panel.right-4. Addition rule y185 spans panel.left+2 throughpanel.left+37 inclusive
(36pixels). FONT1 plus sign visiblepixels start(panel.left+2,179); decoded glyph has blanktop1,
so the Surface.text origin must be(panel.left+2,178).

### Chip exchange is an input phase

Source0x2392 credits individual chips starting with units, then tens, then hundreds.
Each selected reward chip is removed from the offer grid and transferred to the
corresponding counter stack; balance increments by1/10/100 after each transfer.
The counter updater0x263F detects a digit rollover tozero and temporarily draws
10chips before invoking0x2A2F. This is an interactive carry phase, not an automatic
conversion. Scene is temporarily25. The full stack flashes red for6ticks, runs a
hint animation, and repeats after60ticks until the player clicks inside that
stack's original rect7+digit. Then conversion animation plays, the stack clears,
one higher-value chip transfers to the next stack, and0x263F recursively checks
for another carry. Scene restores after completion. Existing selected15+12=27
capture does not exercise carry; earlier description of that timeline as carrying
was unproven and should not be used as evidence of exchange.

Debit0x24A2 also processesunits beforetens beforehundreds. If the necessary digit
iszero,0x2732 invokes0x2854 on the next higher digit. Borrow recursively obtains a
higher chip if necessary, then similarly entersscene25 and waits for a click on
that higher stack before splitting it into10chips. Afterborrow, payment removes
one chip at a time. Strict balance<payment still determinesloss.

Exchangeanimation0x2776 usesDS:F8A eight9byte records, lengthsDS:FD2.
All frames are SHPL4400 ordinals (absoluteSHAP4400+ordinal),10ticks/frame:

| Record | Original ordinals | Purpose |
| --- | --- | --- |
|0|8,9,10,21,10,9,8|unitcarryhint|
|1|11,12,13,20,13,12,11|tencarryhint|
|2|8,9,10,21|unitcarrycommit|
|3|11,12,13,20|tencarrycommit|
|4|3,21,10,9,8,9,10,21,3|borrowtenhint|
|5|2,20,13,12,11,12,13,20,2|borrowhundredhint|
|6|3,21,10,9,8|borrowtencommit|
|7|2,20,13,12,11|borrowhundredcommit|

Forrecord<4 animationrect keeps stackleft/right but uses bottom20pixels;
record>=4 moves its top to stacktop-4 and bottom tothat+20. These frames use
0x6C2E centered-shape compositor withwhitebackground. Sound1026 precedes sequence.
Carry transfer is chipSHAP4421 forunits->tens or4420 fortens->hundreds from
(stackleft,y57) to next higher stack, movementhelper6DA9 args(0,2,8), then20ticks.
Borrow transfer uses ordinal8 for tens->units or11 forhundreds->tens from
higherstack(left,top-4) tolowerstack(left,y53), then draws10chips andwaits20ticks.


Static reward capture caution: `turn-b/next-turn` is mid delivery: top reward5+1
has arrived, bottom5+1+1+1 has not yet been drawn. Native2FBF coin variant has no
robot condition; all prechoice callers passvariant0. The rebuilt top coin panel
matches exactly. A new settledrobot capture is inprogress to avoid using that
intermediate frame as a terminalstate. Chip2392 removes selected chips individually; settled chosen Chip grid is empty.
Money20F7 instead redraws selectedpanel variant1, flies moneybag4414 from the
panelcenter to fixedpoint308E:0000 via6DA9(1,4,8), then credits the full amount
and redraws balance19EB. The light Money coin grid persists after credit. There
is no percoinMoney animation. Nextturn cannot start until the blocking transfer
returns and main1CCC sets5276=-1 at20E3.


### Final native carry and settled references

`chip-carry-a/state/carry-wait.png` is an actual scene25 carry request: player1
started thisreward with19chips, selected4 versus5, and is paused atbalance20
while3 selectedunit chips remain. The visible counter deliberately shows tens1
and units10. `carry-unit-click.png` records clickingunitstack and completing the
reward atbalance23, scene3, withchosenchipgridempty. Thefullrun includes frontend
inputroute, RAM, frame hashes, individual changedframes, and audio. ExportedRAM
and screenshotbacked annotations are appended to`native-states.json`.

`robot-settled-b/state/reward-chosen.png` waited5000callbacks afterselection:
player0balance18 from10+8, otheroffer10, scene3, remainingsteps-1. Selected8cent
coins remain light; other10cent dime remains normal ongray. This corroborates
Money'sbag transfer and distinguishes it fromChip'sindividual removal.
`robot-settled-b/state/next-turn.png` waited6000callbacks afterroll: robot's fully
delivered7/9cent offers and story`You found a winning lottery ticket!`, scene16.
Bothsettledstates are exportedto`native-states.json`.

Transfer helper main0x6DA9 takes source/destinationpoints, twoshape pointers,
erase-at-end flag, frame delay, and step interval. It walks a Manhattan/Bresenham
path: eachinternalstep advancesonlyoneaxis by1; drawsinitial, every8steps and
final. Moneycreditargs(erase1,delay4,step8), twoshapesbothbag4414, destination
(y48,x204), sourcecenterof25x24boxwithinselectedoffer. Chiptransfer uses
(erase0,delay2,step8). Originalsets2016timerandwaitsforzerobetweenrenders. Exact
wallclock-to-frontendcallbackratio depends onDOS timing and should not be inferred
from arbitrarycapturewaitcounts.

Outstanding parity gaps: original movingbag/chip rendering, deliveryhands,
exchangehint/commit animations, dashboardSCRpose progression, and complete
perphase timing needframe-by-frame runtimecomparison. The originalrules and
input blocking forcredit/debit/carry/borrow are source-recovered; these notes do
not claim those transientframes have alreadybeen matched.

End/replay correction from dedicated reward research: the game-over award control invokes the shared prize chooser directly. Selecting a prize immediately resets and starts a fresh game with existing settings; Esc from the chooser exits. There is no separate yes/no replay dialog in that path. Loss toggles active player so the opponent receives the prize. Full source details and new ordinary-input win→chooser→prize→restart captures are in `treehouse_rewards_research.md`.
