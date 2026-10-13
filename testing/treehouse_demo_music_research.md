# Treehouse DOS music activity: executable and live-memory findings

Date: 2026-09-27. Target is the pinned DOS v1.1 binary documented in
[the executable research](treehouse_executable_research.md). This investigation
uses original executable/resource bytes and the native piano capture at
`testing/output/treehouse/demo-piano/state/piano.png`, with its corresponding
RAM. No external descriptions are needed for the facts below.

Maintained decoder: `tools/treehouse/sound.py`. Generated table export:
`testing/output/treehouse/research-music/music.json`. Generated sample evidence:
`testing/output/treehouse/research-music/sounds.json` and individual WAV files.

## Digital sound decoded and independently compared

All **283 digital resources** in VOICES (41) and DIGISND (242) decode. The
original Bass sample, VOICES SND12011, produces **9,861 unsigned PCM bytes**;
every byte equals the original game's decoded buffer in the native piano RAM.
This confirms sample decoding for that independent reference. It does not
establish final mixed output, resampling, note timing, or looping equivalence.

The resident loader at unpacked image0x1BBF6 tests the digital flag and codec;
0x1BD9E reads the compressed stream's embedded count. It calls decoder0x1BE74
at0x1BE22, then updates the header to codec8 and the decoded count. Header:

| Offset | Field |
|---|---|
|0|kind:1 digital, high bit80 loop flag|
|1|u16 LE sample rate|
|3|codec:8 raw unsigned8 PCM,255 compressed|
|4|u16 LE declared sample count|
|6|u16 LE loop start|
|8|u16 LE loop end|
|10|raw PCM, or compressed stream|

For codec255 the stream starts with u16 output count, one initial sample byte,
then MSB-first bits. The decoder starts in control mode. A three-bit control
0..6 selects delta width2..8. Control7 emits the previous sample plus128,
wrapping modulo256. In delta mode, the midpoint code `1 << (width-1)` returns
to control mode without output. Other codes are signed two's-complement deltas
of that width; add the delta to the previous sample modulo256 and emit it.
Stop exactly at the embedded output count.

The original corpus has210 resources with no full trailing byte and73 with
one. The decoder retains that byte as metadata. DIGISND10123's header declares
8,768 samples but its stream declares9,600; the original loader uses9,600.
`decode_sound_with_info` retains both values and exposes `count_matches`.

The native memory-handle lookup at image0x13B38 is significant: a handle's
first word contains flags as well as its pointer nibble. Resolve the buffer as
`segment*16 + (first_word & 15) + 6`, then translate guest physical address to
the captured memory region. Treating the first word as an ordinary full offset
produces a wrong buffer. In the piano capture, DS:5274 points through handle66D2
to buffer at RAM0 offset9B168; its10-byte header precedes the compared PCM.

## Instrument and pitch mapping

MODULES STRL100 lists42 instrument/category labels in original order. Original
overlay1 routine97C9 loads sample ID12000+instrumentIndex. Index21 (Sousaphone)
uses sample12020 (Tuba). Indices0..6 are mixed categories; MIDI playback can
combine instruments for these, so treating them as individual sampled
instruments does not reproduce that backend's orchestration.

Animation group selection is10000+100*instrumentIndex, except indices0..6 use
group10000. Overlay1 routines3B92 and97C9 establish this formula. The original
native piano opens Lion Theme (SONG20) with instrument11, Bass. Raw SONG20 has
instrument0, but the original overrides it from its per-mode defaults table.

Overlay1 function20C5 sets a digital sample's rate from main DS:C00 indexed by
chromatic pitch0..16. Exact rates:

```text
6540 6930 7341 7778 8240 8731 9250 9800 10383
11000 11655 12346 13081 13859 14683 15556 16481
```

Thus pitch9 is the sample's nominal11,000Hz A note. The fallback pitch-frequency
table at DS:C22 is `[262,277,294,311,330,350,370,392,415,440,466,494,523,554,587,622,659]`.
For direct sample playback, use the first table, not these rounded frequencies.
SND resources may request looping and supply loop boundaries; retain them when
building browser audio buffers.

## SONG encoding and timing

Each resource is exactly5+2*header[1] bytes. Header byte0 is the introductory
mode's note count; byte1 is the advanced mode's note count. Byte2 is tempo0..4;
byte3 is instrument; byte4 is the notation option. Original overlay1 function
3258 overwrites bytes2..4 for built-in songs from three25-entry-per-mode tables.

Each pair is `(pitch_and_flag, duration_code)`. Mask pitch with127. Value127
is skipped with no timer wait (overlay1:2F94). The high bit is passed to the
notation renderer separately and does not alter playback pitch. Pitches0..16
are chromatic semitones from C to the next octave's E. Codes0..7 sound notes;
8..15 use the same durations with no new note start (rests).

At overlay1:2FAF..2FCF, countdown ticks are:

```text
tempoFactor[header[2]] * durationFactor[durationCode]
tempoFactor = [12,10,8,6,4]
durationFactor = [16,12,8,6,4,3,2,1,16,12,8,6,4,3,2,1]
```

The original approximately60Hz PIT counter drives the countdown, not video
frames. Overlay1:30F9 waits for DS:2016 to reach0. The MIDI path's note-stop and
repeated-note handling still need independent output comparison.

The original unrelocated executable data segment for the music tables begins
at image2F180. Keyboard rectangles are+671 (17*8 bytes), pressed shape indexes
+6F9 (17*u16), keyboard characters+71B (17*u16), associated hotspot indexes+73D
(17*u16), tempo factors reversed at+166..16A, duration factors+823..832.
Song defaults are+75F (tempo),+791 (instrument),+7C3 (notation), each50bytes
(25 songs per mode). These table bytes match the native RAM exactly.

## Exact piano input geometry

All rectangles are `(top,left,bottom,right)`, with exclusive bottom/right.
Black keys overlap white rectangles and should be hit-tested first. Original
keyboard order by chromatic pitch is `Z S X D C V G B H N J M , L . ; /`.

|Pitch|Rectangle|Pressed MODULES SHAP|
|---:|---|---:|
|0|(144,86,188,103)|2202|
|1|(145,99,167,108)|2206|
|2|(144,103,188,120)|2204|
|3|(145,116,167,125)|2206|
|4|(144,120,188,137)|2205|
|5|(144,137,188,154)|2203|
|6|(145,150,167,159)|2206|
|7|(144,154,188,171)|2204|
|8|(145,167,167,176)|2206|
|9|(144,171,188,188)|2204|
|10|(145,184,167,193)|2206|
|11|(144,188,188,205)|2205|
|12|(144,205,188,222)|2203|
|13|(145,218,167,227)|2206|
|14|(144,222,188,239)|2204|
|15|(145,235,167,244)|2206|
|16|(144,239,188,256)|2205|

Overlay1:1C10 selects SHPL2200, the table's relative shape index, and the
rectangle's left/top as the draw origin. It saves the underlying rectangle
before drawing; native release restores that backing image. Rendering helper
652C may perform additional masking; exact key-down pixels should still be
compared to a native held-key capture.

## Initial Bass and score composition

The Bass illustration uses TH SHPL11100: SHAP11101 at(x7,y30) and SHAP11105
at(x13,y7), source index0 transparent. Independent comparison against the
native piano image matches all2,921 nonzero body pixels and all977 nonzero head
pixels. These positions follow SCR11100's initial slots plus the instrument
anchor(x40,y92) passed by overlay1:2510 to3B92.

The normal introductory score rectangle is(top27,left88,bottom102,right300).
Five staff lines span x88..293 at y41,49,57,65,73. Treble clef MODULES SHAP2301
is a monochrome mask drawn black at(x90,y39). All239 mask pixels match the
native image. Notes0..7 have head origin `x=120+22*index`,
`y=78-normal_y_offsets[notationFlag][pitch]`; the two17-byte offset tables are
exported in `music.json.notation` directly from image2F180+431. First two
SONG20 heads, MODULES SHAP2305 at(120,78) and(142,62), each match all54 mask
pixels in the native frame.

The actual note renderer is overlay1:267D, with position calculation at2A82
and stems/flags at28E3. Durations0..2 use hollow head2303;3..7 use filled2305.
Duration0 is stemless;1..6 have stems;5..6 have one flag and7 has two flags.
Durations1,3,5 have dot glyph2311. Rests8..15 use shape `2300+duration+12`.
Ledger lines, accidentals, stems, and flags require the source's coordinate
adjustments; substituting a text-font music character loses the original
pixels. All music glyphs are in MODULES SHPL2300; the original rendering helper
64EB treats their one-bit masks as a requested solid color.

### Complete normal-size note geometry

The following derives from overlay1:267D,28E3,385F and uses the head origin
`(x,y)` computed above. Rectangle notation here is `[left,top,right,bottom)`.
All glyphs are MODULES masks rendered in the requested color.

- For durations1..7, pitch<12 has stem rectangle `[x+9,y-16,x+10,y+2)`;
  pitches12..16 have stem rectangle `[x,y+5,x+1,y+23)`.
- Durations5/6 have one flag and7 has two. An upward stem uses SHAP2307 at
  `(x+10,y-15)`, with its second flag at `(x+10,y-10)`. A downward stem uses
  SHAP2309 at `(x+1,y+16)`, with its second flag at `(x+1,y+11)`.
- Durations1,3,5 draw dot2311 at `(x+11,y+dot_shift)`, where `dot_shift` is3
  when the selected pitch-height offset modulo8 is nonzero, otherwise0.
- When `pitch <= notationFlag`, draw the low ledger line rectangle
  `[x-3,y+3,x+14,y+4)`.
- The17-byte accidental table at music segment+475 identifies black pitches.
  For these, notationFlag1 draws flat2315 at `(x-5,y-4)`; flag0 draws sharp2313
  at `(x-6,y-2)`. This establishes the flag's flat/sharp spelling role.
- Rest durations8..15 use shape2320..2327. Their origin is
  `x=114+22*index+[1,1,1,4,4,3,3,3][duration-8]`,
  `y=41+[6,10,10,7,7,8,8,8][duration-8]`.
- Pitch127 entries are not drawn or played. Duration17 belongs to these
  placeholders and must not index the16-entry duration table.

The introductory mode selection/playback marker is SHAP2317 drawn at
`(120+22*index,33)`. Overlay1:33D5 receives its color: playback12, selection2,
and removal15. Index rectangles are `(top29,left114+22*i,bottom39,right136+22*i)`;
the note editing regions below are `(38,114+22*i,94,136+22*i)`.

### Initial UI overlays verified against the native piano screen

MODULES SHPL2240 supplies the following opaque sprites. Each row marked exact
matches every pixel within its rectangle, not merely the nonzero mask.

|SHAP|X|Y|Result|
|---:|---:|---:|---|
|2245|264|161|697/697 exact|
|2247|265|140|663/663 exact|
|2243|54|159|522/522 exact|
|2259|289|113|437/437 exact|
|2241|56|138|450/450 exact|
|2249|12|115|567/567 exact|
|2252|98|117|459/459 exact|
|2262|73|127|60/60 exact; tempo pointer|
|2261|44|115|tempo track; pointer overlays it|
|2264|258|1|song-number card top; other card/text overlap|
|2265|260|8|song-number card; original number text overlays it|

The Lion Theme picture is MODULES SHAP2128 with SHPL2120 at(88,6), all440 pixels
exact. Song picture codes at music segment+7F5 are indexed by songID+1:
`group=2100+20*((code&0xF7)>>4)`, `shape=group+(code&15)`. The renderer4DF2 uses
three loaded groups2100,2120,2140. Code0 is the blank entry, so it does not
refer to a valid shape in the usual1-based group.

Original instrument text comes from MODULES STRL100 at rectangle
`(top95,left13,bottom106,right70)`, selected string instrumentIndex+1 in the
original1-based string API. Song-title text comes from STRL101 in rectangle
`(13,113,26,258)`. Original text rasterization and alignment remain the font
researcher's responsibility; these are the exact rectangles passed to the
text routines at overlay1:2510 and2576.

### Null SCR callbacks

Main interpreter0xBFE5 handles10..13. It checks the selected callback far
pointer at `state+0x60+4*(opcode&3)`. A null pointer skips the call. Both paths
advance the script pointer by3 at0xC01F and continue interpreting immediately
via0xC363. A null callback therefore is a valid no-op, with no yield or wait.
A configured callback receives the animation-state pointer and the instruction's
u16 operand. Its own side effects must be recovered when that callback is used.

The instrument audition wrapper3B92 does install callback0: overlay1:4454.
That callback calls20C5 with the current SONG instrument, force-sample flag1,
and pitch9. It therefore triggers the instrument's nominal A sample at
11,000Hz when the audition script reaches10. Treating it as null would omit
that original audition sound. It should not be indiscriminately attached to
keyboard-note animation, where it would insert an unrelated A note.

### Independent complete score and label comparison

The disposable `testing/output/treehouse/research-music/score_probe.py` composes
the introductory Lion Theme score from original masks plus the geometry above.
It produces **zero mismatches across all15,900 pixels** of the rectangle
`[88,27,300,102)` against the native piano image. The staff additionally has a
vertical line at x88 from y41 through73 inclusive, joining its five lines.
This comparison covers the initial score, not every notation branch or song.

FONT1 glyphs are9 pixels high and advance by their decoded width. Searching
the native image for the complete string masks gives these unique positions,
each with every ink pixel matching:

|Text|Glyph origin X|Glyph origin Y|Matching ink pixels|
|---|---:|---:|---:|
|Bass|31|96|52|
|Lion Theme|113|15|103|
|21|267|10|22|
|1|311|39|8|
|6|309|51|15|
|12|308|63|22|
|18|308|75|25|
|24|306|87|28|

Origins refer to the entire decoded9-row glyph bitmap, including blank rows,
not its visible ink bounding box. The instrument label's21-pixel advance is
centered in x13..70; the title is left-aligned at113. The last five entries are
the original song-selection strip labels on the right.

### Disabled editor region and remaining initial controls

Overlay1:217E prepares the duration-editor rectangle at52F2+18. The simple
listening mode branch22F8 fills its interior `(top111,left129,bottom140,right231)`
with the base background purple, RGB(186,85,199), MODULES SHPL2200 index3.
The source calls color selector7308 with mode-dependent parameters before
the rectangle fill. Preserve the surrounding original frame; its interior
fill is `[129,111,231,140)`, not a larger rectangle covering the flat/sharp
control or the editor border.

Overlay1:38D3's mode0 branch draws MODULES SHAP2263 at(235,113), then SHAP2257
at(262,113), both with SHPL2240. Each24x23 sprite matches all552 pixels of the
native screen. SHAP2263 is the disabled control face; drawing the nearby white
control face or moving2257 three pixels to the right creates visible errors.

The tempo pointer SHAP2262's X values are exactly `[46,55,64,73,82][tempo]`,
Y127. These come from music data segment+154 via overlay1:3AA7, and form nine
pixel increments. A ten-pixel increment formula can accidentally match the
default tempo3 while drawing the other four positions incorrectly.

Native piano pointer coordinates, read from main DS:2064/2066 in the capture,
are `(y185,x49)`. This is the physical input pointer location, not necessarily
the top-left of its cursor mask; retain the cursor's hotspot adjustment.
