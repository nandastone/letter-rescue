# Musical maze generation: exact random call order

Research-only, 2026-09-27. No runtime changes. Primary source: pinned DOS v1.1 archive SHA256 `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`, original overlay1 listing `testing/output/treehouse/research-resources/overlay1-disassembly.txt`, and unpacked resident image. Addresses are overlay1 offsets unless prefixed D51 or main. Shared state base is image31690; capture RAM base is318B0. Resident DS is image321D0/RAM323F0.

## Native evidence first

Scratch folder: `testing/output/treehouse/research-maze-generation/`.

`compare.py` implements the recovered rules independently. `native-generation-traces.json` compares seven consecutive ordinary native challenge transitions from `research-music-maze/playthrough`. Every comparison matches **challenge type, correct direction, all four choices, every cycle mask, and the final32-bit RNG seed**. Including the outgoing frog voice, the transitions consume10,18,8,11,9,7,13 RNG calls respectively. This covers types0,1,2,3, difficulty advancement, rejected directions, rejected distractor indices, and type-cycle rollover.

`compare-initial.py` / `native-initial-generation-trace.json`: native first-round snapshots `research-maze-completion/intro-capture/state/intro-06`→`intro-07` match seedA336FC88→EFFD4AE5 in11 calls, secret5,node2,correct1, easy timbre choices `[14,15,37,38]`.

`capture-new-round.py` restores the ordinary prior win and clicks the original new-maze button. `new-round/` contains frames, states, input log and restoration hash. `compare-new-round.py` / `native-new-round-trace.json` matches seed29C4BBE4→E6927FC5 in15 calls, song replacement, new secret/node, hard timbre choices, and incoming voice. The source-defined call sequence is replayed from observed seeds; these are not CPU breakpoint traces and no RAM is modified.

## Random primitive and cycle helper

`R(n)` is inclusive0..n, D51:3BA6. One session-wide32-bit seed at DS5290:

```text
seed = (seed * 214013 + 2531011) mod 2^32
return (seed >> 16) mod (n + 1)
```

The shared `OriginalRandom` already implements this. Eliminate Fisher–Yates and random selection from prefiltered available arrays in maze generation: both consume a different stream, and the latter has a different distribution from the original cycle helper.

**D51:4201**, called by category, notation-set and easy answer-family selection:

```text
cycle(mask, count, excludedBits):
    mask |= excludedBits
    start = R(count - 1)           // exactly ONE random call
    i = start
    while mask has bit i:
        i = (i + 1) mod count
        if i == start:
            mask = excludedBits  // cycle exhausted; preserve exclusions
    mask |= 1 << i
    return i, updated mask
```

It scans forward from a random starting index. It does not repeatedly randomize on a used entry. All maze callers pass a null reset callback.

## Persistent fields and defaults

| Shared-state offset | Meaning |
| --- | --- |
|A8|Current easy0/hard1 difficulty; same state word as the advanced preference|
|8F2|24u16 song-history flags|
|922|6u16 song IDs|
|996/998|Rhythm set cycle masks easy/hard|
|99A/99C|Pitch set cycle masks easy/hard|
|99E/9A0|Melody set cycle masks easy/hard|
|9A2/9A4|Accidental set cycle masks easy/hard|
|9A6|Easy timbre answer-family cycle mask|
|9AE|Secret slot0..5|
|9D4|Node0..8, or large scene9|
|9D6|Excluded direction for the NEXT challenge|
|9E0/9E2|Challenge-type cycle masks easy/hard|
|9E4|Subsequent-challenge type count4 or5|
|9E6|Earned notes byte|
|A10|Correct streak word|
|A16|Current correct direction|
|A1E|Four candidate IDs, direction order|

All cycle masks start zero in the unpacked executable. They survive ordinary new rounds and maze re-entry during the session. Song history/list are also serialized in STATUS.DAT at8AA/8DA. The shipped status file already contains songs `[13,20,15,1,23,5]` and history bits for exactly those six IDs. Do not randomly replace this imported initial set on first maze entry.

## Song initialization and replacement

Routine8A7B initializes six slots in ascending order. For each slot, repeatedly call `R(23)` until `songHistory[id]==0`, assign it and mark history1. This is rejection sampling, unlike the cycle helper. The routine assumes history has enough free entries; do not silently apply a1000-attempt fallback if exact stream behavior is required. The first-launch caller is main `7F54`, encoded as the overlay trap bytes `CD 3F 01 7B 8A`, reached by the missing/invalid STATUS reader branch `7ECF`. Loading a valid shipped STATUS.DAT retains its saved songs and does not run this initializer.

Routine8ADB performs one replacement:

```text
songHistory[songs[secret]] = 1
if all 24 flags are nonzero:
    clear all 24 flags
    mark all six current songs used
repeat song = R(23) until songHistory[song] == 0
songs[secret] = song
songHistory[song] = 1
```

Only the old secret's slot changes. The newly selected secret slot may be a different slot, so the next answer need not be the newly inserted song.

**When:** 8ADB is called on leaving the win phase17, including new-maze control52EC, return control5350, and global exit5294/52C4 if phase17. It occurs **before** the control flash and departure voices. Midgame exit does not replace a song. Routine7062 (new playable round) never replaces songs itself. Current `reset()` replacing a slot on every entry incorrectly consumes an unseen song after an abandoned game and moves the random calls past the departure voices.

## Round setup and difficulty

7062 performs these RNG-relevant operations in order:

1. Clear six eliminated-song bytes.
2. `secret=R(5)`; load its song.
3. Clear earned notes and correct streak.
4. `node=R(8)`.
5. Set excluded direction2.
6. Generate first challenge via5EFB(first=true).

It **does not reset difficulty**. Correct answer55AD increments streak, and exactly streak2 sets hard1. Wrong answer579E resets streak0 and difficulty0. A new round retains current difficulty. Reflect changes into the shared advanced setting if preserving native preference semantics.

Main62D3 returns0 when `DS2119 & 1` or `DS2118` is1 or6, otherwise1. **Correction:** maze entry51B6 sets supportedCount4 for return0 and5 for return1. Its arithmetic is `CMP AX,1; SBB AX,AX; NEG AX; SUB AX,5; NEG AX` (5228–5232). The earlier report inverted that result. First-challenge selection is a separate branch and deliberately does return0→type4, nonzero→easy1/hard2. Therefore the captured native configuration starts with timbre4 but subsequently cycles only types0..3. Do not infer first type from `supportedCount===5`.

| main62D3 result | Subsequent count | First easy type | First hard type |
| ---: | ---: | ---: | ---: |
|0|4|4|4|
|1|5|1|2|

All five inspected native snapshots have DS2118=3, DS2119=3, so main62D3=0 and shared9E4=4. Both initial and new-round challenges are type4. Evidence: `research-maze-generation/native-audio-category-counts.json`. For parity with this native capture configuration use count4 with first type4; a browser ability to play samples does not justify changing this source branch.

Enabled tables at maze data2F9F0:

| Mode | rhythm0 | pitch1 | melody2 | accidentals3 | timbre4 |
| --- | ---: | ---: | ---: | ---: | ---: |
|easy|1|1|0|1|1|
|hard|1|0|1|1|1|

Set counts are easy `[7,10,6,6,0]`, hard `[7,10,6,8,0]`. Preserve counts even for currently disabled types.

## Complete challenge algorithm

5EFB chooses the **direction before type**:

```text
repeat correct = R(3) until correct != excluded
excluded = oppositeDirection[correct]

if first:
    if main62D3() == 0: type = 4
    else: type = hard ? 2 : 1
    typeMask[hard] |= 1 << type
else:
    excludedTypes = bits for disabled entries i < supportedCount
    type = cycle(typeMask[hard], supportedCount, excludedTypes)

typeMask[1-hard] |= 1 << type
generate four candidates for type
guessLocked = false
clear four attempted-sign flags
```

The opposite direction is stored immediately, before candidate generation. During movement5740–5786 the caller saves the old excluded direction locally before generating a new challenge, then enters via that saved direction. Do not accidentally walk in using the newly changed excluded field.

### Types0..3: notation

1. Select `setIndex=cycle(setMask[type][hard], count[hard][type], 0)`.
2. Pick row from existing recovered set tables. Only accidental rows use a separate easy/hard bank.
3. Set `choices[correct]=row[0]`.
4. For direction0,1,2,3 in order, skipping correct: repeatedly select `j=1+R(2)` until row index j has not yet been used; mark it and assign `row[j]`.

The rejection is over row indices1..3. Do not shuffle values or pick from the remaining unused indices. Source dispatch: rhythm64DC, pitch65AD, melody640B, accidentals667E. These exact branches account for all seven native transition matches.

### Type4 easy: four distinct families, answer family has history

Source6313–6408:

```text
answerFamily = cycle(familyMask, 7, 0)
choices[correct] = members[answerFamily][R(count[answerFamily]-1)]
usedFamilies = {answerFamily}
for d = 0..3, skipping correct:
    repeat family = R(6) until family not in usedFamilies
    add family to usedFamilies
    choices[d] = members[family][R(count[family]-1)]
```

No global ambiguity rejection occurs here. The known ambiguous instruments belong to the same families, which are already distinct.

### Type4 hard: two families, pair-local rejection

Source608D–6310:

```text
familyA = R(6)
repeat familyB = R(6) until familyB != familyA
choices[0] = randomMember(familyA)
repeat choices[2] = randomMember(familyA)
    until different from choices[0] and not ambiguous with it
choices[1] = randomMember(familyB)
repeat choices[3] = randomMember(familyB)
    until different from choices[1] and not ambiguous with it
```

Call order is0,2,1,3. Only reroll the second member of the offending pair. Family choices and first pair members stay fixed. Do not update the easy family history mask. Ambiguous unordered pairs are `{20,21}`, `{13,11}`, `{17,7}`; identical instruments are also rejected. There is no cross-pair ambiguity test.

Family rows, preserving original order (`music-followup-tables.json`):

```text
0: 25,26,27,28,29,30,32
1: 35,37,34,40,39
2: 33,36,38,31,41
3: 9,16,22,23
4: 21,20,18,14,19
5: 7,10,8,17,12
6: 15,11,13,24
```

## Choreography also consumes the shared random stream

Each89F7 frog voice consumes exactly `R(3)` and plays20100+result.

- Fresh first entry:51B6 calls862D(true) **before**7062. Uninterrupted introduction uses two voices at88BB and88F4, then round setup/generation. Tutor exit uses voice7393; subsequent player entry uses voice714F.
- Re-entry after the first tutor adds voice892F before7062 because the player also leaves the large introduction scene.
- Each successful nonfinal challenge: one voice before outgoing walk, then direction/type/candidate generation. Incoming walk after an ordinary challenge has no additional random voice.
- Win→new round: replacement8ADB first, two departure voices52FA/5311, round generation7062, then entry voice714F. Captured exact call trace below.
- Win→piano: replacement8ADB first, then one voice535E before player exit.
- Wrong-answer frog animation consumes no random call; native settled→wrong snapshot retains exactly the same seed.

Native new-round trace from seed29C4BBE4:

```text
R(23)=20 rejected, R(23)=14 accepted
R(3)=1, R(3)=3               outgoing voices
R(5)=4, R(8)=1               secret and node
R(3)=2 rejected, R(3)=3      correct direction
R(6)=6, R(6)=5               hard families
R(3)=2, R(3)=0               instruments13,15 for directions0,2
R(4)=2, R(4)=1               instruments8,10 for directions1,3
R(3)=2                      incoming voice
final seed E6927FC5
```

Calls for interrupted introduction branches must be consumed only when their voice actually executes. Generating the challenge up front in `reset()` and displaying the introduction afterward cannot preserve the original shared stream.
