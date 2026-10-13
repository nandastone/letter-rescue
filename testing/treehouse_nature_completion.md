# Nature quiz: turn, guess, and win completion research

Primary-source follow-up,2026-09-27. Read alongside `treehouse_nature_research.md` and `treehouse_nature_followup.md`. Main addresses refer to `disassembly/unpacked.bin`; overlay addresses refer to overlay2 body, documented in `research-resources/overlay2-disassembly.txt`. DS imagebase is321D0.

## New original references

`output/treehouse/research-nature-completion/capture-a` restores existing ordinary-play native states, then supplies mouse input only. `run.json` includes restoration hashes, actions, and read-only final state. No native RAM mutation.

| Capture | Ordinary route | Observed final original state |
| --- | --- | --- |
|wrong-guess|Restore human guess-mode, click card after actualsecret|player0,win0,guessing0,answered1,remaining255|
|second-animal|Restore correct-guess win, click other shrub|player1,win1,guessing0,answered1|
|single-secret-auto-win|Restore human turn, manually cross out seven non-secret candidates, wait|player0,win2,guessing0,answered1,remaining16|

The wrong guess keeps the failed card available when Help is off. The third capture confirms automatic guessing for a human whose remaining mask equals the secretbit. It performs guess-entry animation and then correct-guess/celebration/retreat; it is not an immediate win on the last checkbox click.

`research-nature-completion/render-second.py` independently reconstructs the second-animal settled screen from original assets, data, bitmap font, and cursor: **0 different pixels out of64,000**. `second-animal-reconstructed.png` and `second-animal-diff.png` retain the result. This extends the earlier full-frame win reference to both shrubs revealed and the other player's cards/attributes displayed.

## Essential foreground composition hooks

### Stage divider during turn/ask/guess-entry/retreat

DS57C0 is set around these character SCR sequences:

- Turn entry overlay287E..28C2.
- Ask overlay3274..32BB.
- Enter guess overlay309A..312D.
- Retreat overlay36F1..3739.

Main animation rendererC9ED first restores the retained backdrop, draws all16 SCR sprite channels, then applies foreground hooks. When DS57C0 is true and translated dirty rectangle intersects DS0D96 `(41,166,81,174)`, CB4A..CBAA draws **modulesSHAP5403/pal5400 at(x166,y41)** after the sprite channels. The drawing uses sprite-index-zero transparency and coordinates relative to the animationbuffer's origin. It is a foreground divider/rope, not baked behind the moving actor. DS5270 is the5400palettehandle loaded by overlay0006B..00078.

The wrapper also clears DS0D6E `(42,134,80,167)` white before playback while DS57C0 istrue (`4825..4838`). This clears the previous actor's standing area. Preserve the original clear rectangle; do not clear an entire half of the scene.

### Standing actor while winner's shrub flattens

Win routine overlay39E4 sets DS52CA=1 immediately before running modulesSCR5600+player and resets it afterward. MainCBAD invokes overlay2:3C09 from the animation renderer after ordinary sprite composition. The encoded original call bytes atCBB9 begin `CD3F04093C`, confirming targetoverlay2:3C09.

3C09 redraws the waiting actor over the shrub animation:

| Role / character | Archive + palette | Relative SHAP | Screenx,y |
| --- | --- | ---: | --- |
|Human boy|BOY,pal20100|1|(238,115)|
|Human girl|GIRL,pal20100|1|(238,112)|
|Friend|TH,pal22100|1|(231,139)|
|Robot|TH,pal24100|2|(229,137)|

Coordinates come from DS0D76+8*(role+3*isHumanGirl), and then subtract the animationbuffer origin before drawing. The role helper2851 returns0forplayer0, otherwise configuredopponent1or2. The callback does not draw the player's usual top-left turn pose.

## Script and background lifetime sequence

Every role has group20100+2000*role. HumanusesselectedBOY/GIRL; friend/robotuseTH. Script number isgroup+index; the wrapper does not ignore the index.

### Enter turn

1. Roll handler clears footer and selection as necessary, switchesplayer (`2F8F..2F98`), setsanswered0.
2. DS57C0=true, runSCRgroup+0, thenfalse.
3. Restore learned attributes from that player's askedmask (`394A`) and draw candidates (`1E82`).
4. Clear eight question flags, generate three distinct attributes using sharedrandom-maskhelper; each selectedquestion waits30ticks BEFORE its draw (`2FD5..303B`).
5. Draw enabledguesscontrol; setidletimer300.
6. Automatic branch only while answered==0 and(role==robot OR remainingMask==1<<secretIndex). Wait60ticks. Robot additionallyplayssound1011. Ifalreadyguessing, selectsecret; ifsingle-secretbutnotguessing, enterguess; otherwise choose randomavailableattribute byrejection fromrandom0..7.

After a normal robot answer, answered==1 prevents this auto branch. The next turn requires the die input. A timed autoroll is not the original rule.

### Question

1. Hide guess button, clear inspected definition/animal ifneeded.
2. Setquestioncallbackthreshold DS0DC6 fromattr×role table in earlierfollowup; DS57C0=true; start sound10048; runSCRgroup+attribute.
3. Main4E9E counts displayupdates using DS5586. At threshold it calls4E15->overlay198A(attribute,enabled1,showIcon0), stores the changed question decoration into the retained backdrop, and prevents repeat throughDS5296. This is the question decoration removal hook described in earlierfollowup.
4. Stopsound10048, DS57C0=false, threshold−1; setaskedbit; drawlearnedanswerrow and footeranswer.
5. Wait36ticks. WithHelp, remove mismatches in ascendingcardindex,18ticks aftereachchange.
6. Wait60ticks;cleanup3ADB hides stillenabledquestiondecorations, clearsstandingactorrect andguessrect, restoresdie, setsanswered1/guessing0.

### Guess entry

Overlay3054 permits entry only whenanswered0andguessing0. Clicking guess again while alreadyguessing invokes idle guidance; there is no toggle-back action in this handler.

1. Clear currentinspection ifneeded, highlightguesscontrol, hidequestiondecorations.
2. Save originalbackground DS5742 from the role-specific waitingactorrectangle:

   boy `(115,238,147,261)`; girl `(112,238,147,261)`; friend `(139,231,166,259)`; robot `(137,229,170,256)`.
3. DS57C0=true; sound10048; runSCRgroup+8; stop10048; DS57C0=false.
4. Setguessing1,idletimer0. Auto actors return through the mainloop and incur ANOTHER60tick automatic delay before choosing the card.

### Wrong guess

Overlay3683 runsSCRgroup+11 using the SAME savedbackgroundhandleDS5742. IfHelpenabled, clears thatcandidatebit andredraws itscrossout. WithHelpoff no maskchange.

Then DS57C0=true,sound10048;runSCRgroup+9 usingDS5742;stop10048;DS57C0=false;releaseDS5742. Wait60ticks;cleanup3ADB setsanswered1/guessing0. The wrong branch does not reveal the secret or erase all learnedanswers.

### Correct guess

1. SavewinnerplayerDS57CA beforecalling39E4; role resolvedthere.
2. Playsound1005. DS52CA=true;runSCR5600+player;DS52CA=false. The actorforegroundhook above keeps the waitingactorvisible during this.
3. 3E6E(secretIndex) clearscurrentinspection, writesanimalnamefooter and ALL eightattributeanswers. This does NOT set the player's askedmask to255; it draws them as a special reveal display and setsDS57D8=99.
4. In a temporarybuffer coveringDS5742's savedrect, RESTORE the pre-guess background, drawthesecretlargeanimal at topofitsrevealrect and horizontallycentered, then RECAPTURE that region into a NEWDS5742. This retainedbackground now includes anyportionofthesecretanimal that overlaps thewaitingactorrectangle.
5. RunSCRgroup+10 withupdatedDS5742; setwinphaseDS55EA=2; clearqueuedinput.
6. CommonretreatSCRgroup+9 withDS57C0=trueandupdatedDS5742; releasebackground. Clearstandingarea,restorepalette,drawribbon in diebutton,wait60ticks,cleanup3ADB.

This retainedbackground lifecycle explains the original missing pixels in the final upper flattenedshrub around `(238,115,261,147)`: the pre-guess backdrop is intentionally restored there before the animal is drawn. Drawinganintactflattenedshrub followed bytheanimalcannotmatch that area.

## Post-win inspection and reward

DS55EA=2 means oneanimalrevealed;1means bothrevealed. This state is separate from currentplayerDS5250 and winnerDS57CA.

When the other shrub isclicked (`2D05..2D95`):

1. Switch currentplayer toother.
2. Ifwinphase2,runthatplayer'sSCR5600+player,drawsecretinformation,andsetwinphase1.
3. Redraw currentplayer'scandidatecards andsecretinformation. This changes the visible cards/attributes to the inspectedplayer, while preservingwinner.

The second-shrubreveal does not setDS52CA, does not play the winnercelebration, and does not require another guess. Subsequentclicks onrevealedshrubs toggleinspectplayer and refreshfacts. Clicking currentrevealedshrub restoressecretinfo if aninspection replaced it.

Pressing the die/ribbon afterwin (`2F17..2F8C`) first restorescurrentplayer=winnerDS57CA, resolveswinnerrole, then calls sharedrewardchooserAEC7 withthequizinspectionrectangle and defaultscreen-originarguments. The reward belongs to the winner even after inspecting the otheranimal. The chooser result determines return/rebuild behavior. Sharedchooser details and human/robotreferences are being handled by the rewardresearch agent.

## Useful implementation boundaries

- Keep `winner`, `inspectedPlayer`, `winPhase`, `guessing`, and `answered` distinct. Collapsing them into one `won` flag loses post-win behavior.
- Retain the guessbackground across entry, failure/celebration, and retreat; replace it at the correct-revealpoint.
- Foregrounddivider andwinnerwaitingactor are displaycompositionhooks. Questiondecoration removal is a display-countthresholdhook. Character objectopcode10 callbacks are a different mechanism.
- New settled references andsecond-revealpixelcomparison are complete. Fullordered temporal comparisons still need animation/audio synchronization against callbacktimelines; the new capture directories retain everycallback for that work.
