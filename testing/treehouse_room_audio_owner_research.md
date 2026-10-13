# Room animation audio tails: caller-owned completion policy

Primary-source audit,2026-09-27. No runtime edits. Source: `testing/output/treehouse/research-resources/main-disassembly.txt` and resident helper definitions in `all-disassembly.txt`, from pinned unpacked executable SHA256 `f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f`.

## Normal419D wrapper contract

After SCR completion, but **before restoring animation background/freeing surfaces/showing the cursor**,419D executes4A56..4AB2:

1. If sound20000 is playing, skip audio cleanup entirely.
2. Otherwise, if DS5A1C orDS57C0 is nonzero, force-stop all sound immediately (`C461` at4A82).
3. Otherwise, bases980 and70 skip completion cleanup.
4. All other bases: call577E(0), wait until the current shared sound is inactive or input interrupts; then force-stop all throughC461 at4AAD.

577E is a wait, not a request for graceful release. It polls sound-ID0 (=current/any sound) and calls the current DS15F0 callback while active. The default callback isD51:58E2/image12DF2: checks mouse/joystick/key state. Nonzero callback result makes577E reset input tracking through13029(0), return1, and wrapper force-stop. See12C8E..12CB6,12DF2..12EA3,13029..1305C.

The body of ordinary SCRs is not cancelled by that input. Generic wrapper4855..48BD only gives base70 its direct input-cancellation check; the listed room callers do not select first-frame mode. Cursor remains hidden throughout SCR plus any final audio wait. Background restoration and caller state mutations must wait too. A faithful JavaScript owner should retain the final displayed frame and busy state during the tail and consume a tail-interrupt click rather than pass it through to the next hotspot.

Do not attach this policy to every `Animation.done`: it belongs to each native419D owner and has the exceptions above. Browser backend/mute behavior also matters: the native waits **actual active sound**, so if native sound is disabled or a play request fails there is no fictitious sample-length delay.

## Runtime owners to update

|Owner/native caller|SCR group|Sound enabled|Completion policy|
|---|---|---:|---|
|RoomCharacter ordinary actions392B..39A6|BOY/GIRL20500+resolved action|1|Normal finite/current-sound wait, then stop; only afterward clear active, scheduleBC43, dispatch next action/callback|
|Telescope approach19 andreturn28 via392B|20519/20619/20719 and20528|1|Same normal wait; approach’s explicit60-tick pause comes **after** it; return resumes room idle **after** it|
|Spider604F..607E|TH1080|1|Normal wait, then stop; afterwardBC43. Retain environment’s final display through tail|
|Outer nest4CCC..4D53|TH1250|1|Normal wait, then stop; afterward clearDS5520,free backing andBC43|
|Exterior cycling gag608C..60C1|TH1000+DS5570, cycles0..2|1|Normal wait, then stop; afterward increment cycle modulo3 andBC43|
|Exterior gag60E0..610F|TH1060|1|Normal wait, then stop; afterwardBC43|
|Exterior nut pile611D..61B1|TH1402|1|Normal wait, then stop; afterwardBB48|
|Floor nut event8742..880B|TH1403|1|Normal wait, then stop; callback4ED3 still executes within SCR|
|Exterior food removalBBAD..BC19|TH1300|1|**Force-stop at SCR end**, DS5A1C=1 atBBEF. Clear flag, free backing/remove object. No normal tail wait|
|Exterior window sequence4C0F..4CA1|BOY/GIRL20400,20400+variant,20401|Only middle variant1; opening/closing0|All individual419D calls use normal completion policy; only the middle normally creates sample audio. Preserve ordered open→status→close ownership|

Window4C0F first runs a first-frame-only20400 call to acquire backing, then full20400, middle variant,20401. First-frame call has sound disabled as well. Existing runtime windowScene full opening/middle/closing sequence must not accidentally enable opening or closing script sounds; source passes0,1,0. The wrappers still wait any pre-existing active shared sample unless sound20000 exception applies. This matters if audio can survive into the sequence.

## Nearby owners that must stay distinct

Inner nest chirp3C12 uses direct sound1041 and alternates original nest sprites while sound plays, bounded180ticks. It is not the419D environment wrapper and should retain its specific loop/timeout rule.

Inside foodBBAD starts looping10017, waits up to480ticks using5697 (input-interruptible), forcibly stops, removes food. Its exterior counterpartTH1300 uses the forced-at-SCR-end branch above. Ordinary projectile/departure routines have their explicit stop calls; see `treehouse_looping_audio_ownership_research.md`.

Room activity teleport1015 is also exceptional: outgoing980 skips cleanup so1015 continues until110x replaces it; returning980 setsDS5A1C and stops at ring completion. That is documented in `treehouse_activity_transition_research.md`.

## Native observation relevant to telescope

New `research-telescope-navigation/` records the sound-active flag, frame counter and native frames through pose0 andpose1 approaches and both20528 returns. The balloon does not resume idle until the wrapper has completed. This captures the visible return ownership boundary, though no additional waveform fit was performed for this owner audit. Driver/audio gain and resampling analysis remain in `treehouse_audio_note_completion_research.md`.

## Additional audit: title, telescope view, hollow and sun

This section audits their current JavaScript owners as read2026-09-27, before parent integration of these findings. Resource facts below are from original SCR/SND payloads through `disassemble_script` and `decode_sound_with_info`, using extracted-v2 manifest paths.

### Title greeting and entrance8000..8003

All native calls use **sound flag0**:

- Initial setup00BEF..00C0B boy8000,00C23..00C3F girl8001,00C4F..00C6B boy8000 again all select first-frame mode1 and sound0.
- User-selected greeting00805..0083A, other greeting00851..00899, selected entry8002/8003 at008CE..00902 select full playback and sound0.
- Every8000..8003 resource has **zero sound opcodes**. Their authored display sums are105,105,308,238ticks respectively.

These wrappers still follow the general wait/stop cleanup for any previously active shared sound, including the sound20000 bypass. They do not create an inherent tail of their own. Current app sequence (selected greeting→other greeting→selected entrance) is correct. Explicit sound suppression would match source intent, but current enabled callback cannot produce audible difference from these silent resources. There is no reason to fabricate a fixed title audio-tail delay.

### Telescope ordinary views800/820/840

The single native path2735..2765 is used both immediately on arrival (26B6 jumps26F6) and on an in-picture replay. It setsDS5A1C=1, uses sound1 and restore-background1, waits for the SCR to finish, then force-stops all audio through4A82. It does **not** wait for the final finite cue. These facts apply equally to800,820,840.

|SCR|All sound cues by resource byte offset|Final cue loops?|
|---:|---|---|
|800|+39:10006, +208:10005, +277:10007|No;10007 has8824samples at11000Hz|
|820|+34:10030, +48:10001, +232:10030, +256:10031|**Yes**,10031 whole-buffer loop2176samples,11000Hz;10001 also loops but is replaced|
|840|+29:10040, +178:10042, +287:10041|No;10041 has14432samples at11000Hz|

Current `app.js` stop-all at nonrobot telescopeSCRdone matches forced audio termination. It must also retain pointer/input blocking during the synchronous body: native does not run18CD to accept replay/exit until419D returns. Runtime’s telescope hit handler currently accepts both replay and exit while the animation runs. An ordinary click is not a whole-SCR skip in this path. Restoring the final animation background before accepting input remains a separate rendering responsibility.

### Robot shelf MODULES3610

Native first draws background and owned prizes. If any of the sixDS55F8 bytes is nonzero it sets localbp-4=1 (25FF..2637). It then runs3610 first-frame mode1, positioned at centerx206,bottom140, **sound0** (2647..2673), using a saved backing pointer.

After the display setup it jumps26F6. If any prize exists, it immediately executes full3610 at2708..272F, **sound1**, first-frame0. Subsequent in-picture clicks repeat the same full-play call. With no prizes it remains at the first frame and does not full-play on arrival or click. Full replay uses ordinary wait-for-final-sound then forced-stop cleanup; there is noDS5A1C flag in this branch.

3610 authored duration200ticks. It has four audio instructions, all10024 atbyte offsets39,133,227,321.10024 is **finite**,9440samples at11000Hz. This playback uses its normal resource rate, unlike the reward-flight caller’s explicit22050 request.

Concrete current runtime gaps in `startTelescopeAnimation`:

1. Full playback is conditioned on `replay && shelf.some(Boolean)`, so initial arrival with prizes incorrectly stays still. Original condition is any-owned-prize for both arrival and replay.
2. MODULES3610 is constructed without `onSound`; all four10024 cues are missing.
3. The normal audio tail and its input-interrupt/stop ownership must be added to the shelf owner. Preserve body input blocking and consume a tail interruption instead of firing another replay or navigating away with the same event.

### Hollow squirrel1400/1401

Native3E1F starts1019 directly, **before**415F. Upper/lower choice selects variant1/0 through3E33..3E3B. The wrapper has restore-background1 and **sound0** (`3E40..3E48`), because1400 and1401 themselves contain no audio opcodes. They have authored display sums66 and99ticks.1019 is finite,19377samples at11000Hz, roughly105ticks at the native requested11000→hardware11111 rate. Normal419D completion waits for any remainder, then force-stops, restores backing and accepts the next input. No forced flags are set.

This exposes a concrete defect in the newly added runtime per-animation sound deadline: `hollowClick` calls`this.sound(1019)` then`playAmbient(...)`, whose initial`ambientAnimation.soundDue=this.tick` forgets that externally started sound. AtSCRdone it now forcibly cuts1019 short. Pass the externally started deadline into the owner (or query the active shared audio state), so the owner can hold the final frame until1019 completes or a tail-interrupt input arrives. This is especially visible for1400’s66tick animation.

### Exterior sun1301

Native009EE..00A14 requires a selected character, invokes loaded group1300 withvariant1, restore-background1,sound1, no first-frame mode and no forced-stop flag. It then schedulesBC43. SCR1301 has one sound cue10016 atbyte44, finite9088samples at11000Hz; authored duration128ticks. Normal419D wait/stop applies, though the sole cue normally ends before the whole script. The parent’s general ambient finite-tail owner fix already covers this caller correctly. Do not confuse sun1301 with food1300’s forcedDS5A1C policy.

### Ordinary native shelf capture confirming first arrival and replay

`testing/output/treehouse/research-shelf-play/` now provides the complete reference sequence, generated by `research-shelf-play-capture.py` without RAM modification. It restores the ordinary `research-reward-completion/native-b/state/robot-400.state`, whose robot shelf has `[1,0,0,0,0,0]` and visitmask7, exits the board normally, clicks the telescope, waits for initial playback, then clicks within the shelf to replay. No source state was patched to manufacture an owned prize.

|Snapshot/event|Run|Original tick|Meaning|
|---|---:|---:|---|
|state/before-telescope|2764|129697|PNG/RAM/state after pointer movement, immediately before normal telescope click|
|First-frame robot setup observed|3069|129959|DS5822=0, no active sound|
|Full initial3610 setup observed|3072|129961|DS5822=1; existing pose3 remains|
|Initial10024 first observed|3081|129969|Digital header `(1,11000,8,9440,0,0)`|
|Initial full playback settled|3309|130164|Display counter25; audio inactive|
|state/before-replay|3799|130583|PNG/RAM/state after pointer move to(160,100), immediately before replay click|
|Replay10024 first observed|3811|130594|Same finite header; noDS5A1C flag|
|Replay settled|4039|130789|Display counter25; audio inactive|

The full resource has25displayed frames whose authored delays total200ticks; it is not200distinct frames. `frames.jsonl` provides ordered lossless frame paths. Compare the replay in runs3800..4040; source-backed placement is palette3600,origin(181,93): raw3610bounds `(175,283,222,333)` are50×47, wrapper centerx206,bottom140 subtracts halfwidth/height. Initial full playback despite no replay click and the sound-enable0→1 switch are directly confirmed by the driver trace. The trace’s unchanged header between repeated10024starts is expected: later cue starts replace the same finite sample on the single channel. The SCR supplies all four cue offsets; a mere header-change log cannot count identical replacements.

Settled references are state/arrived.png andstate/replayed.png; all snapshots retain `.ram-0`, companion low-RAM dump and `.state`. Complete input events and origin SHA256 are in driver.json. Audio is native48kHz stereo WAV; playback-resource request11000Hz is established by the active driver header.

For composition initialization from RAM, DS base is0x323F0 in these dumps. Prize bytesDS55F8 are at0x379E8..0x379ED; visitmaskDS52F6 is word0x376E6. Native pointer `(y,x)` is two signed16words atDS2064/dump0x34454. Arrival’s actual pointer is `(123,199)`, despite requested targety122 rounding during the DOS mouse conversion; replay’s is `(100,160)`. Recommended full-play comparison ranges are3072..3310 and3802..4040. Run3070 is the preliminary silent firstframe setup; replay’s first full-play display is3802.
