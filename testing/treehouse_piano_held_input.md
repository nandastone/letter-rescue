# Held piano keys and idle-animation input

## Reproduced behavior

The original defers its piano idle animation while a note is held. The browser
ran it in parallel, consuming random choices before the original and sometimes
showing the wrong idle frame later. A second case presses a new key during an
idle animation: the original interrupts that animation and schedules its next
deadline before playing the key. The browser instead froze the animation and
resumed it after release.

The original source is overlay 1: its main-loop idle check (`00F3..0113`),
held-note handler (`19DD..1B05`), temporary-notation cleanup (`0207..0274`), and
interruptible idle sequence and next-deadline calculation (`510A..51B4`).
The idle sequence uses 17 original frames, four-tick waits, and a 10..30 second
random delay. This change does not emulate instructions or use captured timing
schedules as runtime input.

## Runtime correction

Idle animation waits until no piano key is held. Temporary notation cleanup
waits until a pending idle animation has returned, matching the original loop
order. Pressing a new key or a canvas control during idle animation ends it and
schedules the next deadline through the same helper used for normal completion.

Candidate A corrected long-held behavior but missed the new-input interruption.
Candidate B, `a89b3f65ac50ce1a548fa6618f795261e0a79507c057e3a87b4a305d9747d322`,
corrects both. It is now delivered after the full regression passed.

## Evidence

All folders below are under `testing/output/treehouse/`.

- `piano-held-native-a` / `piano-held-native-b`: repeated 13-checkpoint native
  holds/releases; all actions, states, screenshots, full WAV and callback
  timeline agree (`piano-held-repeat-a.json`).
- `piano-held-baseline-b`: old live build fails eight random-state comparisons
  and one later idle image under the corrected interval comparison.
- `piano-held-fixed-b`: candidate A matches those 13 image/state checkpoints.
- `piano-held-native-c`: adds input during active idle animation, for 17
  checkpoints. `piano-held-interruption-a` fails its two held-key checkpoints.
- `piano-held-interruption-b`: candidate B matches all 17 full RGB checkpoints
  and compared music/gameplay/random state.
- `piano-held-short-b`: all 30 existing piano-note/tempo checkpoints pass.
- `piano-held-music-b`: all 22 native authoring/playback checkpoints pass.

`verify_piano_held.py` is registered as suite 89. All 89 suites passed before delivery. The served build is `a89b3f65ac50ce1a548fa6618f795261e0a79507c057e3a87b4a305d9747d322`; previous live files are backed up in `piano-held-delivery-b` and its HTTP hash is verified.

## Input-boundary correction and limitations

The native capture's one-callback release snapshots are byte-for-byte identical
to the previous held-key images. The emulator has not yet published the input's
effect at those instants. Previously the browser verifier submitted each input
before collecting its first image, although the native interval begins at the
snapshot before input submission.

The verifier now records that actual browser boundary image too. Matches using
it are explicitly marked `matched_before_input`; they establish interval image
membership, not equal input latency. Final gameplay/music/random fields are
still compared after each action interval. No native image is supplied to the
runtime or used to replace browser pixels. The old failed reports are retained.
The unchanged old build still fails the eight random-state checks and the later
idle image, so this fixture correction does not conceal the runtime defect.

Exact redraw/input timestamps, held keyboard/touch parity and full rendered audio
remain separate requirements. The complete-clone gate remains failed.


## Fresh input and repeat verification

The extended original capture repeats exactly in `piano-held-native-c` and `piano-held-native-d`: 21 checks over every action/state, 17 screenshots, full WAV and callback timeline pass (`piano-held-repeat-b.json`). The two immediate-release boundary images are explicitly proved unchanged in `piano-held-input-boundary-a.json`.

Candidate B also passes 18 checks across fresh mouse, keyboard and real Chromium touch sessions (`piano-held-controls-b`). These navigate from character selection, hold a note for 1,800 ticks, release, wait for idle animation, interrupt it with a new note and release again. The registered held-input suite now includes these controls as well as the native replay. This verifies browser input integration; native keyboard/touch timing is not inferred. All 183 room environment states pass.
