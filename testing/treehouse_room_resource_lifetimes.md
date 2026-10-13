# Initial room resource ownership

The generated startup now continues through child-archive opening and initial
room construction for both children. This supports the unresolved money-game
cursor-resource dependency. It is not yet connected to live activity events.

## Operations covered

The room model restores VGA colors, loads the five interior palettes, draws
the background, date/month table, theater sign, nest, cloud and clock, and
constructs saved backgrounds for the character and room objects. It restores
the normal cursor after releasing the temporary room surface.

Palette IDs, banks, rectangles, object metadata and archive bytes are derived
from the pinned executable and data files. The harness supplies new-game
semantics (cloud 5, noon, default objects), as well as the previously documented
two entrance credit events. No captured resource address, initial heap RAM,
allocation request stream or native image drives these operations.

## Two lifetime errors isolated and fixed

- Calendar drawing clears its top-edge selection mode at main 340A. The later
  character redraw therefore uses AD72's bottom-edge rule, including the nut
  bag and basket. The model previously retained their saved backgrounds while
  saving the character, changing handle reuse. Check F fixes near allocations,
  catalog handles and payload ownership, while retaining arena failures.
- Main 22E1 keeps the converted cloud alive while drawing the calendar overlay,
  releasing it only at 23D7. Releasing it before the overlay changes subsequent
  clock-source placement. Check G corrects the arena differences too.

## Evidence

Paths below are under `testing/output/treehouse/`.

- `room-resource-check-d`: repeats the four previous final ownership failures.
- `resource-room-objects-boy-a`: adds boundaries immediately before and after
  initial object drawing, using ordinary startup and character-selection input.
- `room-objects-control-boy-b.json`: 423 checks show that these observers and
  the earlier room observer preserve ordinary PNG/WAV/RAM outputs, callback
  timelines and common event timelines. Attempt A retains a failed requirement
  for two independent observer runs because only one was supplied; its ordinary
  output comparisons passed. B supplies the required second run.
- `room-resource-check-e`: preserves the failures and exposes arena differences
  before character drawing. It rules out character drawing as the only cause.
- `room-resource-check-f`: foreground selection correction; three arena fields
  remain failed, with all other boundary comparisons passing.
- `room-resource-check-g`: all 246 comparisons and six focused checks pass for
  the boy, including the additional palette and object boundaries.
- `room-resource-girl-check-b`: all 204 comparisons and six focused checks pass
  for the girl, including final room ownership.

The current model generates ownership continuously from executable, platform
and archive inputs. These checks cover allocator, DOS, catalog and modeled
source/font/cursor/sound payloads. Converted shape pixels and saved background
pixels are outside this comparison. Semantic completion is not a claim of
native drawing, animation or audio timing.

`room-resource-build-a/index.html` is byte-identical to the delivered basket
fix, SHA-256 `27689144aa93085bc22f6e2b282b0563f08960659bfeb2b489bf307ac1804413`.
The money-loss failure remains unresolved. Required next work is activity
resource lifetimes, live event integration, and continuous payment replay;
there is no full-fidelity or money-game completion claim.
