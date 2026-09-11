# Eighteenth slice: graphics work profile and drawing-page selection

The native probe now pairs the graphics-library calls inside 64 complete
ordinary updates. Rectangle copies and masked sprite draws together account
for about 90% of the measured renderer interval. Every rectangle copy in this
route uses the aligned EGA fast path. This identifies the next substantial
pieces needed to predict time spent inside updates.

The shared device lookup and drawing-page selector are recovered in Python
and Godot. All 129 measured drawing-page calls match their return time, modeled
hardware state, page index and page offset. No measured call duration is used
as a runtime replacement for instruction work.

## Native profile

`tools/prepare_wr1_graphics.py` verifies the capture/trace hashes, pairs nested
calls by kind and saved return address, and preserves their initial hardware,
arguments, graphics state, device handle/record/descriptor and expected return
state. It also records the main update stages. The result is measurement
evidence; most graphics routines do not yet have predictive work models.

The first probe, `testing/output/wr1_graphics_profile_native`, retained only the
wrapper returns. The original EGA dispatch paths have their own returns, so
that probe cannot supply paired copy/sprite durations. It remains diagnostic
evidence. The corrected observer covers all statically identified returns;
the authoritative capture is `testing/output/wr1_graphics_complete_native`
with its `.json`, `.jsonl` and matching `.map`.

`testing/fixtures/wr1_graphics_profile.json.gz` preserves 1,505 paired calls:

| Routine | Calls | Inclusive guest cycles, total | Observed return file offset |
| --- | ---: | ---: | --- |
| Rectangle copy | 1,050 | 1,790,056 | `13D79` |
| Masked sprite | 198 | 1,194,897 | `16995` |
| Drawing-page selection | 129 | 16,501 | `0F453` |
| Renderer | 64 | 3,329,034 | `0C1A9` |
| Display-page selection | 64 | 20,285 | `17695` |

Renderer time includes its child calls. These durations also include any
interrupts occurring inside the interval; they are not isolated instruction
counts. The two drawing primitives are responsible for 89.7% of the renderer
interval in this route. Their mathematical work must still be recovered and
run against the existing independently simulated hardware/IRQ clock.

The measured update stages, in guest cycles:

| Interval | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| Admission to movement complete | 102 | 120 | 199 |
| Contacts | 189 | 892 | 4,140 |
| Speaker check before entities | 3 | 3 | 53 |
| Entities/actions | 188 | 303 | 865 |
| Renderer call | 45,430 | 49,296 | 68,166 |
| Post-render checks and display selection | 320 | 323 | 323 |
| Ordinary post-display completion | 4 | 4 | 4 |

The final update starts at frontend call 938 and enters the death/restart path
after display selection. It does not reach the ordinary completed-update hook
before the capture ends. Its observed stages and open-call status are retained
as `incomplete_tail`, and its calls are excluded from the 64 complete-update
profile. This is not evidence that the death/restart interval has been modeled.

## Recovered shared work

`tools/wr1_graphics_work.py` and `scripts/wr1_graphics_work.gd` recover:

- Active device lookup, file `1934E..19377`.
- Handle-record search, `190EF..19137`, including the observed slot count.
- Device descriptor resolution, `1913A..19197`.
- Drawing-page selection, `0F3F5..0F453`, stopping before the outer RETF.

The selector writes the original page word and the low 16 bits of page times
descriptor stride. Valid device/page paths are currently supported; invalid
handles and unsupported descriptors fail explicitly. Instruction work is
expanded from the extracted catalogue, including nested near/far calls and
returns. The hardware executor now recognizes RETF as a block boundary.

The route uses device handle 2, slot 2, the 320x200x16 EGA descriptor, eight
pages and a `0x2000` page stride. Its rectangle copier dispatches to file
`13C91`; all measured calls take the aligned copy path ending at `13D79`.
The descriptor's coordinate-to-VRAM helper corresponds to file `163B6..163D8`:
it computes a 40-byte row stride and an X/8 byte offset. These observations
provide the next source boundaries for recovering copy work.

## Validation and remaining scope

- 28 focused Python tests pass in 21.384 seconds, including original-executable
  catalogue reproduction and previous music, IRQ, keyboard and idle fixtures.
- Godot drawing-page tests pass all 129 calls and 16,126 checks.
- Godot continuous-idle tests still pass 83,057 cumulative checks across the
  old omitted-input fixture and the final timed-key fixture.
- The maintained core patch passes reverse-application validation against the
  instrumented checkout.

Logs are `testing/output/wr1_eighteenth_python_tests.log`,
`wr1_graphics_godot.log`, and `wr1_eighteenth_idle_godot.log`.

Next: recover the aligned copy path and masked-sprite path using their actual
arguments and device state. Copy setup also reads library initialization and
mode flags; those should be observed explicitly before treating their branches
as proven. Recovering these routines must include their IO and REP costs and
any IRQ delivery during them, not replace each routine with its measured mean.

The runtime gameplay gate is unchanged. Continuous timing across complete
updates, frontend input delivery cadence, the older 122 admission-frame
residuals, audio/PCM, broader routes/levels, menus and ending remain open.
