# Twentieth slice: masked-sprite work and live image headers

All 198 measured masked-sprite draws now match completion time and modeled
hardware state in Python and Godot. The planner reads the image header,
destination coordinates and device state; it does not use recorded durations
or pixel-byte values to choose the instruction path.

Together with the previous aligned-copy work, both primitives responsible for
about 90% of the measured renderer interval now have verified work models for
this route. The renderer control flow and its calls have not yet been generated
continuously from live gameplay state.

## Recovered drawing work

The source paths are file `164E2..165EA` for setup and `167F6..16995` for the EGA
implementation. The planner includes the original image-origin lookup,
graphics device and BIOS mode checks, coordinate-to-VRAM helper, bounds and
alignment calculations, per-row/per-plane loops, and EGA register IO costs.

The image-origin helper at `18C5A` receives source X/Y zero. The observed images
are in conventional memory, so it returns the raw far pointer from the image
header and does not use EMS or another backing store. The current work model
rejects those unobserved storage types.

The pixel loop loads source bytes and performs writes against VRAM. Its branches
depend on row width, height, plane count and alignment, not the pixel values.
Consequently, the timing planner does not need to duplicate the framebuffer or
feed recorded pixel contents into the clock. This is a timing result; it does
not separately verify EGA latch/register contents or produced pixel colors.

## Image-header evidence

The observer captures 52 bytes from the far pointer passed to each masked draw,
both at entry and return. All observed headers are unchanged by the call. The
following fields are established by the executed source and capture:

| Offset | Width | Meaning in the recovered path |
| --- | --- | --- |
| `00` | word | Image signature `CA00` |
| `0A`, `0C` | words | Maximum source X and Y accepted by the origin helper |
| `12` | byte | Number of source planes |
| `13` | byte | Bits per pixel per plane for source-offset calculation |
| `14` | word | Stored row stride per plane |
| `16` | word | Storage type; zero selects conventional memory |
| `18`, `1A` | words | Pixel-data far pointer: offset, segment |
| `2C`, `2E` | words | Drawing width and height |
| `30` | word | Bytes to draw from each row/plane before right-edge clipping |
| `32` | word | End-mask information; low byte used by this EGA path |

The 24-pixel-wide samples use a stored stride of four bytes and draw three bytes
per row/plane. The observed end-mask low byte is `FF`. This distinction between
stored stride and drawn bytes is required to reproduce the row loops.

## Native coverage

`testing/output/wr1_masked_work_native.json/.jsonl/.map` is the authoritative
capture with image headers. The hash-verified paired fixture is
`testing/fixtures/wr1_masked_work.json.gz`; it also retains the other profiled
graphics calls and the separately identified death/restart tail.

The masked subset contains 22 distinct headers and these dimensions:

- 128 calls drawing 24x32 images.
- 68 calls drawing 24x24 images.
- 2 calls drawing 16x24 images.

All 198 calls have X divisible by eight and four source planes. There are 99
raster-operation-1 calls and 99 raster-operation-2 calls, the mask/color passes.
There is no intervening timer interrupt in any sampled draw: game-clock and
music state remain unchanged across each paired interval.

The source-derived planner also includes shifted and clipped loops, but this
route does not validate them. Single-plane images, shifted or clipped draws,
other graphics devices/backing stores and IRQ delivery during drawing need
additional native coverage where the game uses them. Initialization is already
complete at the playable-frame checkpoint.

## Validation and next work

- 30 focused Python tests pass in 22.020 seconds, including catalogue extraction
  against the original executable and all previous clock/graphics fixtures.
- Godot passes 167,730 cumulative graphics checks: 129 drawing-page selections,
  1,050 aligned copies and 198 masked draws.
- The maintained observation patch reverse-applies cleanly against the core
  checkout.

Logs: `testing/output/wr1_twentieth_python_tests.log`, `wr1_masked_godot.log` and
`wr1_masked_work_analysis.json`.

Next, recover display-page work and generate the surrounding renderer work and
graphics calls from original gameplay state. Contacts/entities and interrupts
during an update must be composed with that work and the existing idle clock
before replacing the runtime gate. The original admission-frame residuals,
frontend input cadence, audio/PCM, remaining routes/levels, menus and ending
remain open; the exact-clone goal is not complete.
