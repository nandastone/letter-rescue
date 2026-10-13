# Bounded native piano audio comparison

## Findings ready to implement

1. **The original piano and editor stop notes immediately.** These UI paths call the driver's forced-stop entry, not graceful release. The current `OriginalAudio.release()` implementation is a plausible transcription of an available driver facility, but `noteUp` and editor preview expiry/release should call `stop` instead. This is audible: a short Bass key tap currently continues through the attack and tail for roughly0.8875s rather than stopping with the input.
2. **Loop-end0 means full-sample looping.** `OriginalAudio.start()` currently requires `loop_end>loop_start`, excluding13 original looping DIGISND resources whose loop bounds are0,0. Use `effectiveEnd=loop_end || decodedSampleLength`, then validate it against loop_start. This issue affects actual original resources, not just hypothetical malformed headers.
3. **The reference DOSBox capture has approximately unity digital gain, while the browser deliberately uses0.4.** Do not describe current browser audio as waveform-identical. Treat user volume separately from a reference rendering gain. The captured attack supports corrected hardware rate11111Hz;11000Hz is measurably worse.
4. **A native forced stop still has a short core-generated DC decay.** It is not the instrument's release tail. A sample-exact DOSBox backend would reproduce that stateful decay and14-bit linear resampling. Ordinary Web Audio buffer stopping/resampling differs even after note semantics are corrected.

No runtime files were edited. Parent was sent findings before this report so it could implement independently; descriptions of `OriginalAudio` refer to the state inspected at the start of this research.

## Reproducible evidence

The capture restores the already recorded ordinary-input piano save (Bass, VOICES12011), waits20 frontend frames, presses **N** (pitch9/A), and releases after12 or90 frames. A third branch replaces N with **M** (pitch11/B) after12frames. No DOS RAM writes, patched game instructions, debugger-injected calls or generated source waveforms are used as native evidence.

- [Capture script](output/treehouse/research-audio-note-capture.py).
- [Pinned core/content/save hashes, options, keyboard events and per-frame driver state](output/treehouse/research-audio-note-c/driver.json).
- [Waveform analysis code](output/treehouse/research-audio-note-analyze.py).
- [Numeric waveform results](output/treehouse/research-audio-note-c/analysis.json).
- Native stereo WAVs: [short](output/treehouse/research-audio-note-c/short.wav), [long](output/treehouse/research-audio-note-c/long.wav), [replacement](output/treehouse/research-audio-note-c/replace.wav).
- `research-audio-note-c/state/` retains full native recording, held/released frames, read-only RAM snapshots and emulator saves. Use the `-c` run; earlier scratch runs were superseded due to incomplete metadata.

The reference core reports48,000Hz stereo signed16 PCM and70.0863037109375 frontend fps. Config is SB16, `A220 I7 D1 H5`, fixed10000cycles, normal CPU core, no force60fps. Native device flagsDS2118/2119 are3/3; digital driver pointer is1E5F:4334. Those are capture-backend facts, not assertions about every original DOS sound card or browser device.

RAM source header while sounding is `[flags129,rate11000,codec8,count9861,loopStart6032,loopEnd7641]`, matching independently decoded VOICES12011. Its decoded PCM SHA256 is `71717a161651024c8546cc6be721e080dbe9ada13dcbd2c386afde827595fc0b`. Do not interpret headers at an inactive stale source pointer: that storage can already have been freed/reused.

## Forced release: native state and executable

| Branch | Last input event frontend run | Observed start/stop ticks | DS211E graceful-release flag |
| --- | ---: | --- | --- |
|12frame N tap|keyup1831|active at3043, inactive at3054|Always0|
|90frame N hold|keyup2121|active at3043, inactive at3120|Always0|
|N→M replacement|N up/M down2333; M up2345|A at3043; same sample changes requested rate to12346 at3053; inactive3063|Always0|

Keyboard delivery is processed during the following emulation runs. These are sampled counter values, not sub-frame interrupt timestamps. Both short and long captures become inactive two frontend callbacks after the keyup request; neither waits for Bass loop completion nor requests its2220sample release tail.

Primary code:

- [Overlay1](output/treehouse/research-resources/overlay1-disassembly.txt) `4F75→1E8C` is the music note-stop wrapper. `1E8C→1FCA` performs other music cleanup, then `1E9E` calls `D51:C461` with null pointer.
- `D51:C461` is resident image19971, which calls19BAD (forced digital stop),19BDC and19C0B. By comparison, graceful release19917 setsDS211E=1; none of these piano/editor paths calls it.
- Editor held-score note loop1B0B waits for input release or leaving its note rectangle, then1B51 calls1E8C.
- Timed preview311F and duration-palette audition6D6B also call1E8C after their timer/input wait. Ordinary song note completionBE1 uses the same stop wrapper.
- Note start20C5 updates header rate, then2169 first callsD51:C461 before starting its new sound. A new key therefore replaces the previous note; it does not layer with an old release tail.

For the Bass resource at corrected11111Hz, natural attack to7641 is0.687697s; loop1609samples is0.144811s; tail2220samples is0.199802s. Calling graceful release during the attack gives total9861/11111≈0.887499s. That explains the incorrect lingering short note in the inspected browser code. Keep the graceful facility available if another source-backed caller requires it; change these caller semantics.

## Attack waveform fit: pinned rate and gain

Analysis uses original decoded unsigned8 PCM, maps `(byte−128)*256` to signed16 scale, and linearly interpolates at the reference mixer's14fractionbit step. It aligns a4800output-sample (100ms) attack window by **normalized** correlation, permitting up to2000samples of callback/mixer latency; a free amplitude scale is then fitted by least squares. This is a bounded fit, not a claim that the full output pipeline is bit-identical.

Both native N branches give the same aligned waveform results:

| Requested model rate | Mixer-quantized effective rate | Correlation | Fitted gain | Residual RMS, signed16 units |
| ---: | ---: | ---: | ---: | ---: |
|11000|10998.046875|0.963063|0.853229|1227.36|
|11111|11109.375|**0.999952**|**0.999916**|**51.23**|

Hardware rate rounding from the original SB driver21A37 gives11111Hz for requested11000. The reference mixer then computes `floor(11111*16384/48000)=3792`, yielding its quantized interpolation step11109.375Hz. Browser `AudioBufferSourceNode.playbackRate` reproduces the hardware nominal rate but uses its browser's own resampler, not this integer phase accumulator.

The best aligned model origin is1047 output samples after short keydown request,1059 after long request; this difference is frontend/mixer buffering. Do not bake those offsets into gameplay audio scheduling. The first restored short branch also contains residual output before keydown, so the report's first-nonzero field is not an attack onset estimate; use the fitted alignment or the cleaner long branch.

Both channels are identical for these mono notes. Full captured short/replacement branches peak20438; long peaks32768 in absolute signed16 magnitude. These peaks depend on duration and signal phase, so they are not a gain estimate by themselves.

Gain corroboration: [mixer.cpp](output/treehouse/capture-core/src/hardware/mixer.cpp) lines120..126 initialize channel scale1 and volume(1,1); lines803..804 initialize master1. [sblaster.cpp](output/treehouse/capture-core/src/hardware/sblaster.cpp) CTMIXER_Reset1236..1246 sets master/DAC31, and calc_vol returns1 at31. The waveform fit independently supports that unity reference path. `OriginalAudio`'s `.4` is about−7.96dB relative to it. That may remain an intentional comfortable default, but pin/normalize it for reference waveform work. Browser/OS speaker volume and analog hardware response are outside this capture.

## Stop decay and replacement

All three native recordings end with **exact−4 signed16 units per output sample**: the last500 differences are all−4, and the last values are84,80,…,8,4,0. This directly confirms `MixerChannel::AddSilence` at mixer.cpp212..251. It steps the prior output sample toward zero by4 per48kHz sample, preserving sign, rather than reading the Bass release tail.

Last nonzero output is31.229ms after the short keyup request,46.208ms after long keyup,75.271ms after final replacement-branch keyup. These spans include input delivery, buffered output, and amplitude-dependent decay; they are not constants to attach to all notes. A reference implementation needs the actual last mixer sample and phase. Abrupt Web Audio stop is closer to the original **game's forced-stop intent** than graceful resource-tail playback, but still lacks this DOSBox-specific smoothing.

Replacement branch confirms the same active decoded sample pointer while its header switches11000→12346. That is source reuse, not evidence of two playing voices. The driver stops before reusing it; Web Audio buffers can remain immutable while each source gets a different rate.

## Loop-end0 audit

Original source19C84..19C9F uses full count when loopEnd0. Interrupt19ABD..19AD5 again substitutes full count, then loops from loopStart. `OriginalAudio.start()` must therefore interpret0 as the sample end when the loop flag is enabled.

| DIGISND ID | Decoded sample count | Loop start/end |
| ---: | ---: | --- |
|1002|2144|0/0|
|1013|49152|0/0|
|1015|12768|0/0|
|1018|13856|0/0|
|1022|6284|0/0|
|1036|7700|0/0|
|10000|15332|0/0|
|10001|5500|0/0|
|10014|6122|0/0|
|10017|11148|0/0|
|10031|2176|0/0|
|10043|4368|0/0|
|10048|4932|0/0|

All have requested11000Hz and loop flag set. Resource headers and decoded counts are in [extracted manifest](output/treehouse/extracted-v2/manifest.json) and original sample files. No VOICES instrument resource has this particular0-end case. A caller explicitly requesting finite playback should still suppress looping. A graceful release for a0-end loop stops at its next full-buffer boundary without a tail; forced stop remains immediate.

## Scope

This closes the concrete piano/editor release error and establishes the loop-end0 omission. Hardware rounding and one-channel replacement already implemented in `OriginalAudio` agree with the audited path. It does not establish sample-exact browser output, full long-note loop-boundary alignment, every DMA64KB split, other sound-card backends, browser output latency, or analog filters. Those remain distinct from the proven game-level input semantics.
