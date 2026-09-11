# Why the hard-impact images and update timing differ

The remaining differences have two distinct causes. The clone's completed
gameplay states match, but it admits some updates before the original CPU has
finished its interrupt handler, and it presents whole scene changes immediately
instead of reproducing the original video-page latch and scanout.

## Update admission: the timer changes before the interrupt returns

The hard-impact trace confirms the earlier medium-mode finding independently:

| Native event | Emulated time (ms) |
| --- | ---: |
| IRQ observation before timer increment, timer 7 | 13102.454000006 |
| Before music-driver call, timer already 8 | 13102.454222232 |
| Frontend handoff 915, timer still 8, IRQ not finished | 13103.000074029 |
| Return from music driver | 13103.114333332 |
| IRQ return observation | 13103.115666667 |
| Main update admission | 13103.115962960 |

The driver call costs approximately **0.660111 ms**. It crosses the frontend
handoff. The original main loop cannot run until the IRQ returns. The clone's
elapsed-time threshold has no CPU-busy interval, so its update 61 starts at
counter 914 rather than 915. All 45 admission mismatches in this route are one
counter early. This is active gameplay CPU service time, not loading duration.

## Presentation: page selection is not immediate output

Impact update 65 itself is admitted at the **same counter 938** in both games.
It therefore isolates presentation differences from the earlier admission miss.
The native renderer runs from 13435.861741 to 13438.928815 ms, taking about
3.067 ms. It then selects page 0, finishing at 13438.940778 ms.

DOSBox Pure's `VGA_DisplayStartLatch` copies the selected address at vertical
retrace. `VGA_VerticalTimer` then selects that latched address for the next
scanout. This capture uses `VGA_DrawPart` with **four 50-row chunks**. RetroArch's
callback receives the completed buffer chosen before the next emulation worker
is started. Reading the current game `display_page` therefore does not identify
the image already returned to the frontend.

The clone's `_original_physics` immediately calls `render_step` and
`_present_original`. Rescue similarly calls `_present_rescue` as soon as its
abstract IRQ wait expires. Those calls have no original drawing-work duration,
page-latch stage, or partial scanout. The actual game can consequently be in the
correct logical state while the displayed image is ahead of the native output.

## Frame 940: exact proof of a mixed image

The previously unexplained image is not a missing sprite or an unmatched whole
animation frame. It contains parts of two different renders of page 0.

Timing below is derived from the native graphics boundaries and recorded VGA
geometry; computed scanout event times have normal floating-point scheduling
precision limits.

| Event | Emulated time (ms) |
| --- | ---: |
| Page 0 display-start latch | 13445.341104 |
| Scanout of page 0 starts | 13446.516815 |
| Rows 0–49 sampled | 13449.694571 |
| First rescue scene plus Benny completed on page 1 | 13450.087926 |
| Rows 50–99 sampled from page 0 | 13452.872326 |
| Rows 100–149 sampled from page 0 | 13456.050082 |
| Second rescue scene redraw on page 0 starts | 13456.597444 |
| Second rescue scene redraw on page 0 finishes | 13459.171741 |
| Rows 150–199 sampled from the rewritten page 0 | 13459.227838 |
| Second Benny blit on page 0 finishes | 13460.486185 |

The first three chunks retain the impact scene. The last chunk sees the later
rescue scene, including advanced enemy animation. Benny's separate drawing does
not appear in this output. The clone only offers whole rendered scenes at its
frame boundary, so no adjacent whole-frame comparison could match this image.

Pixel-level experiment using unchanged, actual-game screenshots:

- Native counter 940 versus clone source frame 937: **374 different pixels**.
- Native counter 940 versus clone source frame 938: **833 different pixels**.
- Rows 0–149 from clone 937 plus rows 150–199 from clone 938:
  **zero different pixels out of 64,000**.

This reconstruction is diagnostic evidence only. It does not modify fixtures,
input, game code, or the strict comparison, and does not count as a parity pass.
Five other outstanding images already have exact matches at earlier clone
frames; frame 940 now has this separate scanout explanation.

## Reproduce the investigation

```powershell
python tools/diagnose_wr1_impact_timing.py --trace testing/output/wr1_hard_drip_impact_complete_native.jsonl --native testing/fixtures/wr1_hard_drip_impact_counter_000940.png --clone-before testing/output/parity/hard-drip-impact-final/hard_drip_impact/pixels/source_000937.png --clone-after testing/output/parity/hard-drip-impact-final/hard_drip_impact/pixels/source_000938.png --output testing/output/hard_impact_timing_diagnosis_repeat
```

The tool requires a fresh output directory. It stores hashes, compact native
boundary observations, calculated chunk times, and the reconstructed image.
The verified run is in `testing/output/hard_impact_timing_diagnosis/`.

## Implication for the next fix

Separate logical updates from presentation. CPU/IRQ availability determines
when an update may start; completed drawing operations change the two video
pages; VGA latching and scanout determine the returned image. A fixed frame
offset cannot reproduce a frame containing parts of two renders. The existing
gameplay rules should remain independently tested while this presentation
scheduling is implemented. No gameplay timing or rendering behavior was changed
during this investigation.
