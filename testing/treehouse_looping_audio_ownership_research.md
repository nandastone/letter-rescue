# Ownership and stopping of whole-sample looping effects

This follow-up is required before enabling `loop_end==0` globally in OriginalAudio. Source is the pinned original executable/resources; no runtime edits. [Extraction script](output/treehouse/research-loop-owners.py) and [full script audio inventory plus code contexts](output/treehouse/research-loop-owners/owners.json) retain reproducible evidence. Addresses are resident image or explicitly named overlay offsets.

## SCR sound commands and sentinels

Across all original archives,261 scripts contain1423 audio instructions: **every one is opcode3**. No original script contains opcode4 or5, or opcode3 operands0 or65535. There is no hidden stop marker in the authored SCR sound stream to implement.

- Opcode3 handlerBEFA waits for the preceding display deadline, checksDS5822, and if enabled callsD51:E5E2(soundID). It yields after advancing3bytes. This loads/starts the sound, replacing the prior digital channel where applicable.
- D51:E5E2 is image1BAF2→1B9BA(resource lookup/decode)→1B9F0(start). A missing resource gives handle0 and returns without starting anything. **Do not interpret opcode3(0) or(65535) as stop-all.** They are not present in these assets in any case.
- Hypothetical opcode4 handlerBF47 callsD51:E566: stop matching soundID;0 is explicitly stop-all. Nonzero missing ID is a no-op. Source1BA76.
- Opcode5 handlerBF5D waits onD51:E5A2 matching soundID;0 asks whether any sound is active. Source1BAB2→19A15.

The existing renderer's no-op for absent opcode3 resources is appropriate; replacing it with sentinel-stop semantics would invent behavior.

## Important correction: 577E is a wait

`D51:577E` is image12C8E: **wait until soundID is inactive, allowing input interruption**. It does not itself stop playback. With argument0 it waits for any sound. D51:C461/image19971 is forced stop; D51:E566/image1BA76 is stop by ID. Earlier reward prose called its B300 call a stop: that was imprecise. Reward B300 waits after the120tick presentation; normally10024 has finished much earlier. If the presentation is interrupted early, the following audio wait can still matter.

## Concrete owner table

All13 effects below loop their whole decoded buffer when started with looping allowed. Bounds0/0 mean `[0,count)`. A subsequent digital start replaces the current digital channel. Match explicit stop type: some source sites stop only a matching sound, others stop all channels.

| Sound | Starts / owner | Exact stop or replacement | Browser integration |
| ---: | --- | --- | --- |
|1002|Musical maze roller: overlay1:74EF/74F3 start and768F/7693 start|Forced-all7567 after outward roller loop and before20tick wait; forced-all7707 after inward loop|Stop at each roller arrival. Do not let sound persist through the20tick pause or after the return.|
|1013|Room hotspot145C→7072(1013)|Next room nonzero input calls forced-all11AF **before** hit dispatch; room exitAC3 also stops|A room input boundary owns this intentionally sustained effect. Do not assign its full4.4237s buffer as a duration.|
|1015|Resident5233 starts before TH980 wrapper;5338 starts same path withDS5A1C=1|5338 branch's980 return force-stops through4A82.5233 branch exempts base980, carries into followingTH1100+variant; their first10034/10032/10035 replaces it|Keep effect across the first980 stage where source does. Full visual variants and explicit state flag determine stop.|
|1018|Room object1 departure A14C|After A8FE flight and85E7 object removal, forced-allA169|Stop after departure completes.|
|1022|Room object5 departure A810|After A8FE flight and85E7 removal, forced-allA82D|Stop after departure completes.|
|1036|Room object0 departure A202|After A8FE flight,90D3 redraw and85E7 removal, forced-allA237|Stop after departure completes.|
|10000|TH1001 SCR offset49; TH1080 offset24|TH1001 offset183 starts10009, later207 starts12029. TH1080 offset443 starts10003, later572 starts10002|Normal replacement already bounds the loop. Also appears in instrument SCRs; see suppression below.|
|10001|TH820 offset48; MODULES4120 offset53|TH820 offset232 starts10030; MODULES4120 offset132 starts10030|Normal replacement. Some music SCR occurrences are suppressed by caller.|
|10014|TH1004 offset88|Offset152 starts10011|Normal replacement.|
|10017|Food consumption BBCB|480tick timer; interruptible wait5697 atBBD8; forced-allBBE1, then object cleanup|Stop when consumption wait completes or is interrupted.|
|10031|Calendar closing3464; opening3585; also TH820 offset256|Calendar forced-all34E7 and35E7 immediately after its final2tick slide step. TH820 replay setsDS5A1C=1 at2735, then wrapper force-stops at4A82 on completion|Calendar arrival needs explicit stop. Stop the telescope replay sound when the authored animation completes.|
|10043|GIRL20523 offset54 only|Offset153 starts10025|Normal replacement. BOY20523 uses different finite sounds.|
|10048|Nature question/guess perform: overlay2:30EB,327A,36F7; also script starts|All three setDS57C0=1 (309A,3274,36F1); commonwrapper4A82 force-stops at completion. Additional stop-by-ID10048 follows at3128,32B6,3734.|After `perform` completes, implement the original forced stop for this wrapper mode. The explicit ID stop alone also prevents a remaining10048 loop, but would not replicate stopping a replacement sound.|

Correction to preliminary chat shorthand: the first roller start is overlay1:74F3 (instruction at74EF loads1002); the forced stops are7567/7707. Numeric source listings are authoritative.

## Authored SCR replacement inventory

These offsets are resource byte offsets reported by the decoder, not executable addresses. On a normal authored sequence, every later digital start replaces the earlier one; there is no PCM queue.

```
TH1001:   +49 10000 -> +183 10009 -> +207 12029
TH1004:   +24 10004 -> +88 10014 -> +152 10011
TH1080:   +24 10000 -> +443 10003 -> +572 10002
TH820:    +34 10030 -> +48 10001 -> +232 10030 -> +256 10031
MODULES4120: +29 10030 -> +53 10001 -> +132 10030
GIRL20523: +54 10043 -> +153 10025
```

Nature BOY/GIRL20100..20109, TH22100..22109 and TH24100..24109 begin10048, then replace it with10049,10030 or the robot's10050/10023 variation. They are additionally bounded by caller stop logic above. See inventory for every resource's exact offsets.

## Shared animation-wrapper policy

Resident415F forwards to419D. Audio enable is argument`bp+A`, copied toDS5822 at4332. **The interpreter and the caller wrapper have different jobs.** Do not add unconditional stop-all to generic `Animation.done`.

Cleanup4A56..4AB2 after its completed/early-exit render loop:

1. If sound20000 is playing, skip audio cleanup.
2. Else if DS5A1C orDS57C0 is nonzero, force-stop all immediately at4A82.
3. Else if script **base** is980 or70, skip audio cleanup.
4. Otherwise call577E(0), waiting for sound completion or input, then force-stop all at4AAD.

For base70 input cancellation during the render loop,489D force-stops immediately before cleanup. Other render-loop cancellation behavior is caller-specific; the interpreter alone does not turn any click into cancellation.

A looping final sound in case4 would leave the wrapper waiting for input after the last picture; telescope TH820 is not such a case, since its actual caller2735 selects case2. A finite final sound can continue for its natural remainder. This explains why resource length alone cannot determine animation ownership. A browser activity that allows navigation away should dispose/stop the corresponding owner in that navigation path; ordinary `setScene` already releases all audio, but embedded animations need their own equivalent lifecycle.

Room loop11AF is a separate global boundary: every accepted nonzero room input stops all before trying object or hotspot handlers. This is a source-backed place to stop1013 and any older ambient sound, not a policy inferred from the sample's length.

## Music suppression and theater caveat

TH11100..14001 include many opcode3 starts for10000/10001. They are instrument illustration animations. Overlay1:3B92 invokes419D with **soundEnabled0**, suppressing their opcode3 path viaDS5822. It instead installs callback4454, which starts the selected VOICES instrument at pitch9. Keep those script sounds suppressed in the browser; enabling them globally would replace the intended instrument sample with unrelated effects.

Do not classify thoseTH11000-series scripts as theater actors. Theater actors are MODULES3200-series. Also, overlay4:33EC setsDS5A1C only when **digital sound is unavailable** (the branch at33E2 skips it for our SB backend). It is not evidence for blanket forced stop at the end of every digital theater animation. No audited loop-end0 effect occurs in thoseMODULES3200-series actor scripts.

## Safe implementation sequence

Add owner stop operations first: roller arrivals, calendar endpoints, nature perform return, object departure completion, food wait end/interruption, accepted room input. Preserve SCR replacement and sound-enable gates. Then enable whole-buffer loops in the sample backend. Keep matching-ID stop available for source sites that need it, and distinguish source finite playback requests from resource loop flags. The two-phase approach prevents newly looping effects from escaping their native owners.

## Ordinary native telescope replay confirmation

[Capture script](output/treehouse/research-loop-owners/capture-telescope.py) restores the original alien-view save, clicks its center once, releases, and advances600callbacks with no further input. [Driver trace](output/treehouse/research-loop-owners/telescope/driver.json) and the accompanying native WAV, every-frame timeline, pressed/settled PNG/RAM/save files are retained. No RAM writes were made.

| Sampled tick | Active decoded sound/header | DS5A1C |
| ---: | --- | ---: |
|6587|None, before replay|0|
|6621|10030 finite, count1142|1|
|6628|10001, flags129/count5500/loop0..0|1|
|6761|10030 replaces10001|1|
|6775|10031, flags129/count2176/loop0..0|1|
|6789|None, replay completed automatically|0|

This independently confirms the native whole-buffer loop, replacement, and **automatic forced stop on TH820 completion**. Its final10031 does not require another user click to stop. The active interval spans the end of its first2176sample buffer, corroborating that0-end does not mean one-shot. The wrapper flag chooses the immediate-stop path.

The other owner entries are code/resource audits, not new native captures for every effect; bounded piano captures remain in the companion [audio note report](treehouse_audio_note_completion_research.md). Existing native visual/activity captures and sound streams can be reused to validate each owner once implemented.
