# Treehouse shared clock, randomness, scripts, and digital audio

Primary-source follow-up, 2026-09-27. No runtime files were changed. Addresses below
are linear offsets in the pinned unpacked DOS executable unless written as a
segment:offset. This closes several implementable timing details; it does not
claim final audio waveform parity or complete emulation of every supported card.

## Sources and reproducibility

- Original archive: `output/treehouse/source/The_Treehouse_1991.zip`, SHA256
  `53ecb856cb6c49f28064ce22b9723eed9a8d19db139ae1bead9786f37a7eb78c`.
- Executable image: `output/treehouse/disassembly/unpacked.bin`, SHA256
  `f2776b04a307996d1a7b4230d49b552b67ad787675b766a7b4c8577ad417973f`.
- [Complete disassembly](output/treehouse/research-resources/all-disassembly.txt).
  Its linear disassembly occasionally starts a function two bytes late after an
  alignment byte. Verify instructions from the entry address when necessary.
- [Native piano memory](output/treehouse/demo-piano/state/piano.ram-0), main DS
  at RAM0 offset `0x323F0`; original DS image offset `0x321D0`.
- Pinned capture core DLL SHA256
  `51b29480c3f55ac7840a2009b87a6693693d7f3472718cf9b8e88f0f0ff19bd9`.
  Its checked-in-to-scratch source is under `output/treehouse/capture-core/`.
  Emulator mixer findings below describe this reference implementation, not
  analog circuitry in an original Sound Blaster.
- Existing [sample decoding research](treehouse_demo_music_research.md),
  [room research](treehouse_room_followup.md), and
  [maze choreography research](treehouse_maze_completion_research.md).

## 1. One shared random stream

Routine `D51:3BA6` / image `0x110B6..0x11116` implements:

```js
// maxInclusive is the original positive signed16 argument.
if (!initialized) {
  seed = biosTicksSinceMidnight >>> 0;
  initialized = true;
}
seed = (Math.imul(seed, 214013) + 2531011) >>> 0;
return (seed >>> 16) % (maxInclusive + 1);
```

The first call invokes BIOS INT1A/AH=0 through `0xE4A4..0xE4D1`, storing DX
as seed low word at DS5290 and CX as high word at DS5292. The initialized flag
is word0 of segment DS4AEC, originally segment30DC/image30DC0, initially0.
Do not seed from the game's approximately60Hz counter: BIOS time is a distinct
counter maintained through the interrupt chain. No other seed writes occur in
the resident/library image. Re-entering an activity does not reseed.

The multiplication helper `0xE5B8` keeps the low32bits. Unsigned-remainder
helper `0xE5EA` confirms that the high16bits are not masked with32767.
The bound is **inclusive**, and `random(0)` still consumes one LCG step. The
denominator is computed by16-bit increment then signed extension; use the
formula above for gameplay's normal0..32766 bounds, rather than inventing
semantics for unsupported negative/overflowing inputs.

For deterministic comparison, save both seed and initialized flag, and log
`{tick,callSite,bound,seedBefore,seedAfter,result}`. Preserve invisible calls:
room actor scheduling at `0xBB48` consumes `random(60)` to schedule an event at
`now+(120+result)*60`, and selection/entry routines can consume randomness before
the first visible activity frame. Separate PRNGs for each activity cannot align
with the native shared stream. Ordinary-input captures are the evidence source;
setting the seed is a diagnostic control, not a replacement for those captures.

## 2. Exact game timer and waits

Startup `0x11E..0x122` passes60 to `D51:62EA` / image137FA. The timer installer
`0x13816` converts frequency to PIT divisor using the literal1193181 stored at
DS2036. The chosen divisor is `floor(1193181/60)=19886=0x4DAE`. It installs INT8
and programs PIT channel0, mode3, through ports43h/40h (`0x1387D..0x138A2`).
Native piano RAM independently contains DS2014=60 and DS202E=0x4DAE.

The reference core defines PIT input frequency1193182 in
[timer.h:27](output/treehouse/capture-core/include/timer.h#L27), hence the
reference counter rate is `1193182/19886 = 60.00110630594388 Hz` and one game
tick is `19886/1193182` seconds. Retain integer tick state and fractional time
accumulation; do not increment once per video callback or assume a70Hz callback
is a game tick. Normal gameplay60Hz is an excellent approximation, but a precise
long-run reference should use the divisor ratio.

INT8 handler `0x13957..0x13997`:

1. Increment unsigned32 DS201E/2020 with low-word carry.
2. In order DS201C,201A,2018,2016, decrement each nonzero16-bit countdown by1.
   These are shared timers0..3, not owned per scene or animation.
3. Add DS2030 to the fractional BIOS-chain accumulatorDS2034. Carry plus
   DS2032 determines whether to invoke previous INT8; otherwise acknowledge PIC.

Thus timers keep running during modals, sound playback, and CPU-side script
execution. Drawing only happens when the relevant foreground loop services it.
The tick comparisons in the SCR interpreter compare unsigned high/low words
directly; they are not modular wrap-safe deadline comparisons.

|Library routine|Linear entry|Semantics|
|---|---:|---|
|D51:5697|12BA7|Call far input callbackDS15F0 repeatedly; input result aborts wait, invokes13029(0), returns1. Otherwise wait for selected timer0..3 to reach0, return0.|
|D51:56C2|12BD2|Call input callback repeatedly but ignore its result; wait for selected countdown0.|
|D51:56DB|12BEB|Set selected countdown to ticks, then use interruptible12BA7.|
|D51:56F7|12C07|Set selected countdown, then use non-aborting12BD2.|
|D51:5713|12C23|Set selected countdown, busy-wait without the input callback.|

DS15F0 is mutable. Call sites CD6E/CEAF/CED9/D01A/D042/D14F switch between
input callbacksresident0:89BD andD51:58E2; a universal browser “any input skips every
delay” rule would be wrong. Even non-aborting waits can service input. Preserve
the caller's chosen wait flavor and shared countdown aliasing.

## 3. Room clouds: gate, clipping, wrap, and cadence

Resident idle service `0xD16..0xD8C` updates clouds only when both
DS5262(calendar open)==0 and DS201A(timer2)==0. On that service call:

```text
x += 1
if x > 283:
    cloudIndex = (cloudIndex + 1) % 7
    x = 163 - width(cloudIndex)
redraw cloud window
timer2 = 300
```

`x` is wordA18 in segmentDS49E0; cloudIndex is wordB4 in segmentDS49DC.
Automatic changes are sequential, with no PRNG call. Cadence is one pixel per
300ticks (about5seconds), not a continuous fractional drift. There is no
catch-up loop: after a modal has kept foreground service away, one step is
performed when service resumes, and a new300tick timer begins.

The reset helper is `0x633B..0x634F`. Room entry `0xB95C→0x633B`, and room
redraw `0x2298→0x633B`, establish300ticks. Early writes10800 at5B9/966/4CB9 do
exist, but are not sufficient to infer a three-minute normal cloud onset;
follow subsequent room setup, which overwrites that shared timer.

`0x24C2` has two placements: argument1 centers the current image atx223,
`x=223-floor(width/2)`; argument0 puts it just outside the left boundary,
`x=163-width`. Initial/manual selection uses centered placement. Cloud click
handler13E1 changes index modulo7 only with calendar closed, centers, redraws,
and plays1044. That handler itself does not reset timer2.

Renderer22E1 uses cloud shapeTH171+index with palette170, top
`55-floor(height/2)`, clipped to `[left163,top30,right283,bottom80)`. It restores
the window background, draws the cloud, then redraws the calendar edge mark.
Opening the calendar suppresses movement but does not freeze timer2; if it
expires while open, closing permits one immediate movement at next idle service.

## 4. SCR timing and interruption

Interpreter `0xBDA0` executes immediate opcodes repeatedly within one invocation
until a yielding opcode or completion. A sprite transform is not itself a frame.
The slot renderer runs on display opcode1, and frame countDS5586 increments only
there (`0xBE36`). Native wrapper `0x4855` repeatedly pumps the interpreter.

Relevant SCR-instance layout:

|Offset|Field|
|---:|---|
|4E/50|current script far pointer|
|52/54|shared opcode scratch: display-repeat counter or delay deadline|
|56|backing-image/dirty preparation flag|
|58|instance display counter|
|5A|current display delay, u16 ticks|
|5C/5E|last actual display tick, u32|
|60..6F|four far callback pointers|
|70..77|four loop counters|
|78 onward|16 actor slots, stride22hex|

|Opcode|Size|Exact timing/action|
|---:|---:|---|
|00|1|Return complete only when `now >= lastDisplayTick + displayDelay`; otherwise yield.|
|01|5|If old display deadline is due, render, stamp lastDisplayTick=now, increment display counters. If repeat counter was0, load repeat count from+1 and the new delay from+3. Decrement repeat counter; advance5 only when it becomes0. Always yield after this attempt.|
|02|3|First visit: scratchDeadline=now+signed16 operand; if lastDisplayTick!=0, add the same amount to lastDisplayTick. Yield. Later visit: when deadline due, clear scratch and advance3; still yield.|
|03|3|Wait for last display deadline, then play sound operand only if DS5822!=0; advance3 and yield.|
|04|3|Stop sound by ID throughD51:E566, advance3 and yield.|
|05|3|Poll sound-ID playing stateD51:E5A2; advance3 only once inactive; yield. ID0 can mean any active sound.|
|06|2|Load cue thresholdbyte into scratch if0. Advance once DS211B==0 or DS211B>=threshold, clear scratch; otherwise wait.|
|07|1|Prepare actor backing regions throughC9ED, set flag56=1, advance1, yield.|
|10..13|3|Call callback[opcode&3](operand,instance), advance3, continue immediate execution.|
|14..17|5|Loop counter slotopcode&3. If0, load operand+1 and jump to `pc+3+signed16(+3)`. Otherwise decrement; jump while nonzero, or advance5 when exhausted. Continue immediate execution.|

Source jump tableC376 supplies handlersBDCE,BE03,BE79,BEFA,BF47,BF5D,BF7B,BFBD.
The central timing detail is that a display stamps the **actual** current tick.
It does not repeatedly advance an ideal deadline to catch up missed displays.
The next display therefore occurs after its full delay even when rendering ran
late. Opcode1 checks the previous delay before loading its own new delay.
Zero repeat counts underflow; do not silently normalize malformed resources.

ConstructionC39D zero-fills the instance, andC776 clears sharedDS5586. The
wrapper's first-frame mode exits exactly whenDS5586==1 (`4868..487B`), before
the remainder of the script. A complete replay follows its full script and end
delay. Generic SCR interpretation itself does not poll mouse/key cancellation.
The wrapper has a special interruptible base70 path (`487E..48A2`), otherwise
it services activity callbacks4E9E unlessDS5296 is set. Treat cancellation and
first-frame mode as caller policy, not a universal property of every script.

## 5. Digital playback is one shared channel

Native piano RAM reports sound-device selection3 atDS2118 and flags3 atDS2119.
Its digital driver is logical1CB7:4334 / image20EA4, the Sound Blaster DSP/DMA
driver; relocated capture pointer is1E5F:4334. The other active driver is MIDI
1CB7:2B4E. The digital sample channel and music/MIDI channel are independent.

General dispatch1998A selects digital for headerbit0, MIDI forbit1, otherwise
the PC-speaker format. Digital start19C46 explicitly stops the previous digital
sample through19BAD, then replaces DS2120/2122 with the new source pointer.
Consequently simultaneous effects/voice/instrument starts steal this single
digital channel. There is no game-side multivoice PCM summation in this path.
Do not let Web Audio sample nodes accumulate just because older samples have
not reached their natural end. MIDI/FM voices can still sound concurrently.

### Hardware rate rounding

Driver21A37..21A54 computes unsigned `q=floor(1000000/requestedRate)` and sends
DSP command40h followed by `(-q)&255`. Core
[sblaster.cpp:959](output/treehouse/capture-core/src/hardware/sblaster.cpp#L959)
sets `actualRate=floor(1000000/(256-timeConstant))`.
For the17 supported music pitches, q<256 so denominator=q:

|Pitch|Requested Hz|q|Reference Hz|
|---:|---:|---:|---:|
|0|6540|152|6578|
|1|6930|144|6944|
|2|7341|136|7352|
|3|7778|128|7812|
|4|8240|121|8264|
|5|8731|114|8771|
|6|9250|108|9259|
|7|9800|102|9803|
|8|10383|96|10416|
|9|11000|90|11111|
|10|11655|85|11764|
|11|12346|80|12500|
|12|13081|76|13157|
|13|13859|72|13888|
|14|14683|68|14705|
|15|15556|64|15625|
|16|16481|60|16666|

A raw11kHz effect also follows this driver rounding. Use effective rate to
compute source sample position and duration, retaining the requested rate as
resource metadata. Command14h plays unsigned8bit mono DMA;218E7 splits
transfers at physical64KB boundaries and sends byte count−1. This can introduce
IRQ/reprogramming boundary timing that a contiguous browser buffer omits.

### Attack, loop, release tail

Header layout remains as established in the sample research: flagsbyte0,
rateu16+1, codecu8+3, countu16+4, loopStartu16+6, loopEndu16+8, PCM+10.
Digital start19C84 chooses initial count=loopEnd when looping is enabled,
loopEnd!=0, and asynchronous driver capabilityDS212C!=0; otherwise fullcount.
Completion interrupt19A69 implements:

1. Loopflag set, no release requested: replay `[loopStart,loopEnd)`; when
   loopEnd==0, use full sample count as the end.
2. Graceful release requested via19917 (DS211E=1), loopEnd!=0 and tail nonempty:
   play `[loopEnd,count)` once, negate release flag, then finish.
3. Otherwise finish immediately at this buffer boundary, clear activeDS211C,
   and invoke completion callback.

Thus release is a source-tail transition at the next DMA completion, not a
generic gain ramp. Forced stop19971/19BAD immediately calls driver stopcommand3,
clears active state, and invokes completion with a stopped reason. ID-based
stopD51:E566 resolves through1BA76 to this forced path. Preserve the distinction
between graceful release, forced stop, and sample replacement.

## 6. Reference-core resampling and final mixing

The emulator adds processing after the original game's driver. Primary source:
[mixer.cpp](output/treehouse/capture-core/src/hardware/mixer.cpp) and
[sblaster.cpp](output/treehouse/capture-core/src/hardware/sblaster.cpp).

- Mixer conversion for unsigned8bit: `(byte-128)*256`, giving signed16-scale
  source samples. Mono is copied into left/right.
- `SetFreq` at190 uses14fractionbits:
  `freqAdd=floor((actualRate*16384)/outputRate)`.
- `AddSamples` at257 keeps persistent prev/next samples and phase. Consume source
  samples while phase>=16384; for unequal rates, output
  `prev + (((next-prev)*(phase&16383)) >> 14)`, then phase+=freqAdd. The signed
  shift matters for negative differences. Equal rates use prev without lerp.
- Per-channel gains are signed integer `trunc(8192*scale*channelGain*masterGain)`
  (`UpdateVolume`, line163). Channels sum into the shared work buffer; the output
  conversion shifts by13 and clips to signed16 (`MIXER_CallBack`). Gain must be
  taken from the chosen reference-core configuration, not inferred from resource
  amplitude or an arbitrary browser0.35 multiplier.
- `AddSilence` at212 applies a linear integer decay of4 signed16 units per
  output sample from the previous sample toward0; it then resets source phase.
  This is emulator output smoothing, distinct from original sample release tails.
- Core SB initialization sets `dma.fade=16` (`sblaster.cpp:811`). `GenerateFade`
  around422 modifies the initial samples with `fac=13-fade`, clamping negative
  factors to0 and scaling byfac/13. This is a core startup artifact, not an
  original-game envelope on every note.
- `DBP_MIXER` can additionally stretch buffered output with linear interpolation
  (`mixer.cpp` around987..1023). So host callback PCM is not always identical to
  a fixed-rate direct rendering of the DMA stream.
- Core defaults48kHz (`dosbox_pure_libretro.cpp:53`), but device configuration and
  reported `av_info.timing.sample_rate` are authoritative. The capture harness
  writes the reported sample rate, not a hardcoded44.1kHz.

## Implementation order and remaining evidence

The bounded changes directly supported here are: shared initialized LCG;
integer PIT-derived ticks/shared countdowns; cloud300tick gated stepping;
SCR actual-display deadlines and caller-specific cancellation; shared digital
channel replacement; hardware-rate rounding; and loop/release-tail semantics.
Those can be implemented independently of reproducing the entire emulator.

For an exact audio claim, still capture and align ordinary native note-on,
note-off, loop boundary, sample replacement, and mixed MIDI+digital output. Log
native driver state and active sample boundaries alongside callback PCM, and pin
core gain/output rate/time-stretch configuration. This research established
source formulas and corroborating existing RAM, not a waveform comparison.
Analog hardware filters and all alternate card backends remain outside this
Sound Blaster reference result. Long-run PRNG alignment likewise requires the
full call trace; substituting a plausible seed does not establish it.
