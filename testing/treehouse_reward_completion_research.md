# Reward presentation, flight, burst, and sound completion

## Evidence and result

Research uses the original v1.1 executable/resources, ordinary mouse input, and read-only saved RAM. Source ZIP SHA256 is `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`. Addresses below refer to unpacked resident image, except explicitly named overlay addresses. Listings: [resident](output/treehouse/research-resources/main-disassembly.txt), [complete image](output/treehouse/research-resources/all-disassembly.txt), [nature overlay](output/treehouse/research-resources/overlay2-disassembly.txt).

**66 full 320×200 candidate frames exactly match ordinary native frames:** 24 robot/money poses and 42 human/nature poses. This includes each displayed flight step, large presentation, all three burst phases, and restored backdrop. Each candidate contains 64,000 independently rendered pixels. The candidate renderer uses the existing resource renderer/activity model, applies the source-derived corrections below in the research browser, and never uses screenshot pixels as a background.

- [Machine-readable poses, matching native frames/ticks, input models, sound metadata](treehouse/reward-completion-poses.json).
- [Candidate reconstruction script](output/treehouse/research-reward-completion/compare.py).
- [Ordinary native capture script](output/treehouse/research-reward-completion/capture-b.py), [input log](output/treehouse/research-reward-completion/native-b/run.json), [every video callback](output/treehouse/research-reward-completion/native-b/frames.jsonl).
- Capture directory contains `state/audio.wav` plus named PNG/RAM/state files. RAM was only read. Both branches resume earlier ordinary-input chooser saves; source hashes are in the input log.

The compared baseline HTML SHA256 was `0673ba00d6a2accea689c76c628d0c4c20942c51a85fe8d87f4d061b463ddb0f`. Runtime files were not edited by this research. Baseline corrections were applied only in the research browser. This establishes the rendering recipe and path poses; it does not claim the unmodified runtime matches.

## Confirmed implementation corrections

1. **Money presentation belongs in the lower chooser panel.** Overlay3 pushes rect14 then rect15 into AEC7; consequently AEC7's `bp+6` is rect15. B1CC copies that rectangle, not rect14. Money lower `(top,left,bottom,right)=(109,226,194,308)`, expanded saved rectangle `(105,222,198,312)`. Symmetric expansion leaves the center unchanged. Large robot floppy is TH961; flying small floppy TH967.
2. **Chips presentation is the union of its two side panels**, expanded4 on every side. B1A4 unions both. Original panels `(98,226,196,265)` and `(98,274,196,313)` produce union `(98,226,196,313)` and expanded `(94,222,200,317)`. This branch is source-derived, not among the new full-frame comparisons.
3. **Nature human destination is the exit icon rectangle**, `(1,304,23,320)`, center `(312,12)`. It is not `quiz_rectangles[9]`. B392 centers in first record of DS52F2; overlay2:27F0 sets table to301C:0580, whose first record is that exit rectangle. For TH879 magnifier the native endpoint is `(304,5)`, not `(285,1)`. The corrected complete human trajectory matches independently.
4. **Keep the cursor visible throughout the reward sequence.** Native captures retain it in large, flight, burst, and settle frames. Native money input finally settled at `(241,165)` despite a requested `(240,164)` delta; use captured coordinates for pixel comparisons. Human pointer is `(47,65)`.
5. **The first burst overlays the arrived prize.** 6DA9 argument `eraseAtEnd=0` leaves the small prize drawn. B45A draws TH923 on top, waits4 ticks, plays10034, then restores the saved arrival background before drawing TH924. TH925 also starts after restore. Replacing the prize with923 loses visible pixels; e.g. robot floppy leaves227 opaque small-prize pixels uncovered by923. The independently composed first burst matches the native whole frame.
6. **Presentation SND10024 overrides its stored rate to22050Hz** (B285 immediate5622, helper733E). Default11000 playback is an octave low and twice as long. B305 restores the stored rate after presentation; do not permanently alter the decoded resource's metadata.
7. **The reminder begins immediately.** B0EA sets201A=0, first loop calls8456, then sets480. The baseline waits480 before its first flash.

These findings supersede ambiguous `upper`/`panel` naming in earlier reward notes. Physical geometry and calling convention above are authoritative.

## Exact composition and lifetimes

Chooser entry AF3A clears `bp+A`; for board AF58 also clears `bp+6` and redraws MODULES4013/4014 marker. The chooser then draws winner portrait, caption and six white cells.

At selection:

| Activity | White fill | Presentation/saved backdrop |
| --- | --- | --- |
| Money | `bp+6`, lower panel only | Lower panel expanded4 |
| Chips | Both caller panels, separately | Their union expanded4 |
| Nature | `bp+A` shared panel | Same panel, no expansion |

Do **not** white-fill the expanded rectangle: expansion applies to background save and centering, preserving surrounding borders. B228 saves that affected backdrop; B2F4 restores it after the large display.

Robot B23E separately saves destination rect10, then draws TH24202 centered there. That portrait remains beneath the large presentation, moving prize, three bursts, and final60tick hold. B50E finally restores its previous rectangle. Nature human has no replacement destination portrait. For money robot rect10 is `(1,261,26,282)`.

Center helper6CEE computes `floor((left+right)/2)-floor(shapeWidth/2)` and likewise Y for positive screen coordinates. First nature large magnifier TH873 is centered in `(6,30,116,128)`. The saved arrival background atB426 is the union of the small destination rectangle and a25×23 rectangle centered on its center. TH923/924/925 are22×18 and use that union's center.

## Timing and input model

| Phase | Source | Native behavior |
| --- | --- | --- |
| Reminder |8456|For each slot0..5: consume random inclusive5, start1050+result, draw red, interruptible8tick wait, redraw white. After all six, set480tick reminder timer.|
| Selected |B16A|Red selected cell;12ticks via56F7, full duration.|
| Large |B281..B316|Change10024 rate, start it, draw large, interruptible120ticks via56DB, restore backdrop, wait for audio with interruption via577E, restore sample rate.|
| Flight |B3AA,6DA9|Start10035, draw step0 and every8 Manhattan units plus exact endpoint;3ticks per displayed pose.|
| Burst1 |B45A|Draw923 over small prize;4ticks, full duration.|
| Burst2 |B481|Start10034, restore destination backdrop, draw924;4ticks, full duration.|
| Burst3 |B4B9|Restore backdrop, draw925;4ticks, full duration; restore backdrop again.|
| Robot settle |B501|Interruptible60ticks, then restore robot portrait rectangle.|
| Human completion |B524|Create/reset room object using original prize identity; no extra60tick wait.|

56DB at image12BEB calls an interruptible wait: callbackDS15F0 is polled; nonzero calls13029(0), returns early. 56F7 at12C07 polls that callback but continues until timer expires. Flight7006 is a busy timer wait, with no input callback service. Therefore a blanket `dismiss()` during large/flight/burst is not equivalent: a click/key can shorten large/robot hold but does not cancel the award; the selected/flight/burst holds have their own semantics. The exact treatment of a newly held input across the following phase needs its own capture if implementing event consumption beyond this source contract.

Path source6DA9/7024:

```
dx = abs(targetX-sourceX); dy = abs(targetY-sourceY)
error = dx ? floor(dx/2) : -1
step = 0
while true:
    if atEndpoint or step % 8 == 0: draw(); waitFull(3)
    if atEndpoint: break
    if error >= 0: x += signX; error -= dy
    else:          y += signY; error += dx
    step += 1
```

The native helper supports alternating shapes; this caller passes the same shape twice. Do not interpolate diagonally or skip the endpoint hold. Money robot branch has19 flight poses,57 nominal ticks. Human nature branch has37 poses,111 nominal ticks. Manifest source ticks are sampled at video callbacks, so first/last observed ticks are not exact instruction timestamps. A duplicated frame can remain the most recent frontend image after native drawing advances.

## Digital sound duration and queue audit

All reward samples below are finite, non-looping mono PCM. Counts are decoded from original DIGISND resources. Effective Sound Blaster rate is `floor(1,000,000 / floor(1,000,000/requestedRate))`, as established from original driver21A37 and reference core in [runtime research](treehouse_runtime_completion_research.md).

| Sound | Samples | Requested / effective Hz | Natural duration |
| --- | ---: | ---: | ---: |
|10024 presentation|9440|22050 /22222|0.424804s,25.4887 game ticks|
|10035 flight|11584|11000 /11111|1.042570s,62.5554 ticks|
|10034 burst|16248|11000 /11111|1.462335s,87.7417 ticks|
|1050..1055 reminder|1125,1168,1352,1280,1184,1157|11000 /11111|0.101251–0.121681s|

There is one digital playback channel. e5e2 starts/replaces the active sample; rewards do not enqueue these sounds. A sound call must replace an earlier digital sample immediately, while independently sequenced music/MIDI channels follow their own lifetime. Reminder sounds normally end before8ticks; interrupted reminder waits can bring starts closer and replace a preceding sound. Presentation's120tick duration is not its audio duration. B300 calls577E, an interruptible audio wait, after the hold; normally the sample ended naturally long before. This corrects the earlier shorthand describing577E as a stop. If the presentation hold is interrupted very early, its following audio wait can still delay progress until the sample ends or input interrupts again.

For money robot,10034 starts after57 flight ticks+4 first-burst ticks, so it can truncate the very end of10035 (~1.56 ticks nominally). For this longer human path,10035 finishes before burst.10034 is not stopped at the third burst or award return by AEC7; it can continue into the caller until another audio action replaces/stops it. A blanket audio stop on reward completion would lose that tail.

The retained native WAV supports future waveform alignment, but this report does **not** claim a sample-exact output-waveform comparison: native mixer startup, resampling and frontend stretching require separate calibration. Rate, count, queue replacement and stop/start order are directly source-backed. The pose comparisons are complete-frame exact for the two captured prize paths, not a claim that all prize identities, chips, every input interruption or all renderer timings are now verified.
