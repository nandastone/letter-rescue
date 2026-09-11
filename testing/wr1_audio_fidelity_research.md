# Audio fidelity: native mixer gain and speaker release

Research dated 2026-09-09. This compares the existing generated audio with the
pinned DOSBox Pure source and the successful continuous native recording. It
does not claim sample-exact audio parity. No original executable, emulator
source, reference DLL, runtime script or shipped asset was changed by this
investigation.

## Concrete corrections

### Recover the mixer gains

The offline OPL adapter writes DBOPL samples directly, without DOSBox mixer
scaling. DOSBox's `Adlib::Module` installs the FM channel and explicitly calls
`mixerChan->SetScale(1.5f)`. The PC-speaker channel has the ordinary default
scale of 1.0. Mixer channel volume and master volume initialize to 1.0; the
Sound Blaster mixer resets FM and master to 31, whose `calc_vol(31)` is 1.0.
The reference configuration therefore calls for these runtime gains:

```gdscript
music.volume_db = linear_to_db(1.5) # 3.521825 dB
speaker.volume_db = 0.0
```

Sources: [adlib.cpp](output/dosbox-pure-trace/src/hardware/adlib.cpp), lines
822–825; [mixer.cpp](output/dosbox-pure-trace/src/hardware/mixer.cpp),
`MIXER_AddChannel`, `UpdateVolume`, and `MIXER_Init`; [sblaster.cpp](output/dosbox-pure-trace/src/hardware/sblaster.cpp),
`calc_vol`, `CTMIXER_UpdateVolumes`, and `CTMIXER_Reset`;
[offline OPL adapter](../tools/wr1_opl_render.cpp), `generate`.

The previous -6 dB setting on both players attenuates the speaker by about
half and the music by about a third relative to those native defaults. It
also makes effects 1.5 times as prominent relative to music. These are emulator
reference gains, not a universal loudness calibration for every physical
Sound Blaster card. DOSBox's own comment explicitly notes card variation.

Existing assets have a maximum music peak of 15,254 and maximum speaker peak
of 5,000. The conservative sum bound after these gains is
`1.5 * 15254 + 5000 = 27881`, below signed 16-bit clipping at 32,767. This bound
assumes the current single song and single speaker streams and a unity master
bus. It does not assume their peaks occur together.

As a separate check, compare the native recording's seconds 12–29 with WR1.4
at the previously measured fixed offset of 0.9386667 seconds. For 250 ms
windows, compute Hann-windowed Fourier magnitudes, aggregate power into 40 Hz
bands excluding DC, and retain windows with magnitude cosine similarity above
0.97. The 47 qualifying windows have median estimated native/raw-asset gain
**1.5206**, with interquartile range **1.4242–1.6151**. This supports 1.5 rather
than 0.5; it is not an exact amplitude calibration because timing, phase,
register-write spacing, and possible speaker contribution remain uncontrolled.
The native left and right channels are identical in this recording.

Source data: [native capture metadata](output/audio-20260909/native-continuous.json),
[native WAV](output/audio-20260909/native-continuous.wav),
[measurements](output/audio-20260909/fidelity-analysis.json). The native PCM
hash, including its uint32 rate header, remains
`1431cbb6355a93d4bfa4fff2acaff7d219e7e6c318262da33c7ff2a9ce270341`.

### Preserve the speaker's release tail without delaying gameplay sounds

All ten original generated effect files end at sample **-5000**, because the
builder stops rendering about 2 ms after the final port-off event. Stream
completion then jumps to zero. This extra 5,000-unit discontinuity is absent
from an uninterrupted native speaker release.

The native `PCSPEAKER_SetType(0)` queues `-SPKR_VOLUME`, which is -5000, rather
than zero. `PCSPEAKER_CallBack` keeps the channel running while OFF. Once
`last_ticks + 1000 < PIC_Ticks`, it changes `volwant` toward zero by **one unit
per callback**; the regular mixer callback is installed as a millisecond tick
handler. Thus an isolated effect has about one second at -5000 followed by
about five seconds of gradual DC recovery. Once `volwant` is zero the next
turnoff check disables the channel. This is largely DC, not another six
seconds of pitched sound.

Sources: [pcspeaker.cpp](output/dosbox-pure-trace/src/hardware/pcspeaker.cpp),
`SPKR_VOLUME`, `PCSPEAKER_SetType`, and the tail of `PCSPEAKER_CallBack`
(lines 313–328); [mixer.cpp](output/dosbox-pure-trace/src/hardware/mixer.cpp),
`MIXER_Mix`, `MixerChannel::Mix`, and `TIMER_AddTickHandler(MIXER_Mix)`.

Rendering the same events through the unchanged standalone kernel with a
longer output duration verified all ten effects:

- Their entire existing PCM prefixes remain byte-identical.
- Each ends at zero.
- The last nonzero sample is 6000.078–6000.929 ms after its off event.
- Beyond the first 2 ms following off, adjacent samples differ by at most one
  integer unit, instead of a final jump of 5000.

Examples: step is logically off at 20.831692 ms and its last nonzero sample
is at 6020.979167 ms. Death is off at 3551.803497 ms and reaches its last
nonzero sample at 9551.979167 ms. Results are in
[tail report](output/audio-20260909/tail-analysis/report.json). With the
adapter's one-millisecond callbacks, `ceil(off_ms) + 6005` total milliseconds
leaves several zero samples after release. The maximum observed tail is
under 6001 ms. This bound is for that callback schedule, not every possible
host mixer configuration.

Recommended builder change, after accumulating the table durations:

```python
logical_duration_samples = round(ticks * IRQ * RATE)
total_ms = math.ceil(ticks * IRQ * 1000) + 6005
```

Include `logical_duration_samples` in each effect's manifest entry. Let the
speaker stream continue through its PCM release while its logical busy state
ends at that sample count. Idle-only footsteps and jumps must test the logical
busy state; `speaker.playing` would now incorrectly suppress them for another
six seconds. A newly admitted effect should replace the old release stream,
since native hardware still has only one speaker.

This metadata separates native sequence completion (`speaker_index = -1` at
the terminating IRQ) from emulator PCM release. It also avoids retaining the
previous approximate extra 2 ms as part of logical busy time. The source IRQ
behavior is already recovered in [wr1_irq_work.py](../tools/wr1_irq_work.py)
and the original audio notes.

There is still a limit: replacing a clip resets its recorded initial
oscillator/DC state. Native interruptions preserve the running speaker state,
and the new first entry is admitted at an IRQ boundary. Extending the file
does not make replacement or early cancellation phase-exact. Do not overlap
two tails, invent a six-second logical lock, or claim a generic short fade is
the recovered native behavior. Exact continuity needs a persistent speaker
synthesizer or a state-aware transition renderer.

## Music loop boundary findings

The present WAVs have no appended preview-silence tail. Their stored loop
endpoints produce jumps of 2761, -47 and -3585 for tracks 4, 5 and 6. Each is
exactly the same jump as that file's natural first-to-second-pass boundary.
Their largest ordinary adjacent-sample steps are 9408, 12598 and 9432,
respectively. There is no measured evidence here for adding an arbitrary
crossfade to hide a special loop-end click.

This endpoint check does not prove later synth-state parity. First and second
passes are not identical waveforms: equal-position sample RMS differences are
532.45, 565.37 and 637.76. A repeated second-pass WAV freezes later noise,
envelope and oscillator histories at that pass. Native synth state continues
through the actual register restart. A useful next fidelity experiment is
rendering at least three complete passes from the same initialization and
comparing the third pass with the reused second. Full PCM equality also needs
native register-write times and mixer state; gameplay frame equality alone
does not supply them.

Sources: [asset builder](../tools/build_wr1_audio_assets.py), `music_events`;
[manifest](../assets/audio/original/playback/manifest.json);
[DBOPL source](output/dosbox-pure-trace/src/hardware/dbopl.cpp), `Handler::Generate`
and `Chip`; the measurements linked above.

## Reproduce

```powershell
python tools/analyze_wr1_audio_fidelity.py --speaker-tail
```

The analysis script uses the existing local NumPy installation and the built
offline speaker renderer. It reads existing assets and native capture, writes
only under `testing/output/audio-20260909`, and launches no DOSBox, RetroArch
or game session. It leaves original inputs unchanged. If the shipped assets
are subsequently regenerated with full tails, the script measures the new
files and still confirms their shared prefixes against the unchanged kernel.

The two immediate corrections are therefore source-derived mixer gains and
speaker release plus separate logical busy duration. Native PCM phase,
mid-effect cancellation and interruption, repeated music synth state, and
host mixer scheduling remain explicitly unverified.


## Implementation follow-through

The runtime now applies both recovered gains. The asset builder appends the
full OFF-state tail to each effect and records `logical_duration_samples`;
idle-only sounds consult that logical bound rather than WAV playback duration.
The real mixer test verifies the tail does not block new footsteps and checks
replacement, level/death music continuity, loops, volume and clipping. These
corrections leave the existing gameplay clock/IRQ models unchanged. Music/PCM
phase and persistent synth state across interrupted effects remain limitations.
