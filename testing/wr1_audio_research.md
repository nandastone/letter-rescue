# Original gameplay audio

Original-rule play now has the three WR1 CMF songs and ten effects recovered
from the executable's PC-speaker tables. Run `just run-original`; sound is on
by default. `--mute-original-audio` disables presentation audio. Accelerated
headless checks are silent unless passed `--original-audio`.

Audio is presentation only: it does not advance the recovered gameplay clock,
consume random numbers, or supply native outcomes to the game. The 15 demos
remain the maintained gameplay regression suite.

## Recovered behavior

The supported WR1.EXE SHA256 is
`b8395fab1e0341e1398790b986c8cf8bf2393dcfdb5d492e7d7dd910d2589d0f`.
The initialized data segment begins at file offset `0x24f50`.

The music loader at file offsets `0x6182..0x61d2` selects WR1.4, WR1.5 and
WR1.6 by zero-based level index modulo three. Cached death loads skip that
loader; the clone likewise preserves the song position. A new song is selected
when progression changes the group. The recovered CMF sequencer and OPL driver
generate the register stream; the existing DOSBox DBOPL renderer synthesizes it.
Each WAV contains an initial pass followed by one repeat pass. Godot loops the
second pass using sample offsets in the manifest, with no preview silence tail.

For demo playback, the one initial checkpoint contains the native driver
counters and CMF identity. Reconstructing that state from song start validates
the track cursor, delay, active flag and running status before seeking to
`(beats * division + counter) * 12428 / 1193182` seconds. All 15 initial demo
checkpoints pass this reconstruction. No subsequent native state is fed back.

The PC-speaker IRQ handler at file offsets `0x4352..0x43f8` advances at the
same PIT cadence. Each table contains pairs of 16-bit values: a divisor word
and a duration in IRQ ticks, terminated by a zero duration. Two details matter:

- Entry zero is a delay sentinel. The IRQ increments the index before loading
  the next tone; playing entry zero would add a spurious sound.
- The EXE writes the high byte first to PIT2's low-byte latch. The effective
  divisor is byte-swapped relative to the stored 16-bit word.

| Effect | DS table offset | Example trigger, EXE file offset |
| --- | --- | --- |
| Mystery complete | `0x336` | Final mystery letter, `0xa4ed` |
| Recap transfer | `0x3e2` | Ten-IRQ wait completes, `0x5bd8` |
| Correct | `0x43a` | Letter `0xa37a`, match `0xc26e` |
| Wrong | `0x456` | Wrong match, `0xc512` |
| Slime | `0x472` | Target found, `0x521a` |
| Death | `0x492` | Death starts, `0x4d15` |
| Book | `0x4ba` | Book pickup, `0xc62f` |
| Slime miss | `0x4da` | Exhausted or missed, `0x52c9` / `0x52dc` |
| Step | `0x4ea` | Frames 3, 6, 13, 16, `0x3d3a` |
| Jump | `0x4f6` | Jump starts, `0x3960` |

The speaker is a single channel. New effects replace the previous effect;
steps and jump starts only play when idle. Support or releasing Up cancels the
jump sound; climbing stops the active sound. Death reset stops the speaker and
preserves music. Recap audio is dispatched by its existing event clock after
the first ten-IRQ wait, before the dissolve, without adding waits or events.
Slime pickups and reveal/unlock UI do not acquire invented sound triggers.
An additional table at `0x526` is referenced in stop conditions but no start
site has been identified; it is not assigned a speculative trigger.

## Reproduction and evidence

From the repository root, with the existing DOSBox source and toolchain:

```powershell
python tools/build_wr1_opl_renderer.py
python tools/build_wr1_speaker_renderer.py
python tools/build_wr1_audio_assets.py --exe testing/output/normal-play-20260909/WORD/WR1.EXE
python -m unittest testing.test_wr1_audio -v
```

Set `GODOT` to the Godot console executable for the real mixer test. That test
opens the actual game scene, checks all initial demo music checkpoints, crosses
all three loop boundaries, checks interruption and music preservation, uses
real movement controls, returns to the menu, and records the audio bus. The
Python check rejects engine errors, silent output and clipping. The generated
asset checks also validate hashes, sample bounds and all 17 distinct active
speaker pitch/duration pairs in the original 9,641-case hardware-loop fixture.
All 12 audio, OPL, recap and recap-timing tests passed after the final audio
wiring. The focused actual-game rerun of demos 11 and 5 also passed: 2,114/2,114
states and 21/21 sampled images, with no input, timing or terminal differences
and no engine warnings. Its report is
`testing/output/parity/audio-fixed-20260909/report.md`. This rerun checks that
audible presentation preserves gameplay; it does not compare PCM.

Godot uses [AudioStreamWAV](https://docs.godotengine.org/en/4.6/classes/class_audiostreamwav.html)
for PCM playback and sample-indexed loops. The test records the actual output
bus with [AudioEffectRecord](https://docs.godotengine.org/en/4.6/classes/class_audioeffectrecord.html),
without microphone capture. One saved mixer recording is
`testing/output/audio-20260909/clone-mixer.wav` (6.594 seconds, nonzero PCM).

The offline speaker renderer embeds the DOSBox Pure speaker kernel unchanged,
with clock and mixer adapters. Its source SHA256 is pinned to
`45bd8db3a4d25380417b687a11fa0c4b4d96c48be3edcfa40925335e0c362708`.
The generated manifest records the EXE, CMF, renderer and WAV hashes. No
emulator code is linked into the Godot game.

For direct native audio observation:

```powershell
python tools/build_wr1_audio_probe.py
python tools/capture_wr1_audio.py --game-dir testing/output/normal-play-20260909/WORD --replay testing/output/demo_level1_native.replay --output testing/output/audio-20260909/native-continuous.pcm
```

The probe is a separately named DLL with an observation-only tap of the stereo
buffer delivered to RetroArch. It changes no guest memory or instructions and
the builder restores the source byte-for-byte. The original reference DLL
remained SHA256
`c28f7bc568f3607c32640f5fa208d2ba1c72cb9334822b0b276487f1e6c23728`.
The probe DLL was
`c67d4b55691a70c8bb2ecaee3e4d7b977306145d9b1b3e109e4b68fdd6733f78`.

Capture runs continuously: pausing a first attempt stalled the frontend, so
that incomplete attempt is not evidence. The successful recording reached
replay frame 2200 and contains 1,507,314 stereo frames at 48 kHz (31.402375
seconds). Its PCM file, including the uint32 sample-rate header, has SHA256
`1431cbb6355a93d4bfa4fff2acaff7d219e7e6c318262da33c7ff2a9ce270341`.
Metadata and a listening WAV are beside it in the ignored output directory.

A diagnostic pitch-band comparison of native seconds 12–29 against the songs
gave mean cosine similarity 0.914 for WR1.4, versus 0.302 and 0.337 for WR1.5
and WR1.6, using one constant offset. This supports song identity and musical
content; it is **not a percentage of PCM parity**. Repeated phrases also make
the best offset unsuitable as proof of initial playback phase.

## Limits and remaining work

This implements audible original gameplay content and source-derived triggers;
it does not establish sample-exact equality with DOSBox. Music uses ideal IRQ
timing and a pre-rendered repeat pass. Synthesizer envelope/noise state across
later loops, native CPU/register-write spacing and mixer timing are not fully
preserved. Each effect starts a fresh rendered speaker state, so interruptions
and within-IRQ phase remain approximate. Source-derived mixer gains are now
1.5 for AdLib music (+3.5218 dB) and unity for the speaker, replacing the earlier
-6 dB settings. A native capture analysis independently estimated a median
music gain of 1.5206 in high-similarity windows; this is corroboration, not PCM parity.

All ten generated speaker files now preserve the DOSBox OFF-state recovery:
approximately one second of DC hold followed by a five-second ramp to zero.
Their active prefixes are unchanged. The manifest separately records logical
effect duration, so a recovery tail does not block idle-only footsteps/jumps.
The mixer test explicitly checks this boundary, replacement, volume, output
clipping, all three loops and all fifteen initial music checkpoints.
See [audio fidelity measurements](wr1_audio_fidelity_research.md).

Original pause menus keep the music playing; S provides All Sound, Music off
and All off. The attract loop restores the suspended song position. Startup
and the three-image ending use the recovered songs. The legacy simplified menu
still ends its original audio session when entered outside the original flow.
The full 15-demo baseline preceding audio matched 22,460 gameplay states
and 196 sampled images, with three documented one-frame timing discrepancies.
It is not a claim that the entire game, every rendered frame or audio is exact.

The final frontend/audio full rerun (`testing/output/parity/frontend-final-20260909/report.md`) completed all15 demos with22460 exact states and196 exact sampled images. Its only strict failures are the same three documented one-frame admission differences; it introduces no gameplay/input/terminal/image regressions.
