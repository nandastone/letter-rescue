# Clear Text presentation

Launch with `just run` or `just legacy-clear`. Clear Text is the default;
`just legacy` retains the original display. This is a presentation adapter, not a new ruleset
or a general executable plugin framework.

## Scope

The current word, mystery/bonus word, score, collectible letters, book covers,
question marks, world word cards, floating bonuses, recap cards, level titles,
W word list, menus, help, instructions, profiles, high scores, intro, story and
ending screens use Andika 7.000 Regular. It is bundled, unmodified, with its SIL Open Font License;
see `assets/fonts/andika/README.md` for provenance, hash and font metrics.
The font is [designed for beginning readers](https://software.sil.org/andika/design/).
That design purpose is the basis for choosing it, not evidence that a typeface
alone improves reading outcomes. Keep `OFL.txt` with any distributed build.

Frontend artwork is cleaned once before composition, then transparent font
controls are drawn at window resolution. `data/wr1/clear_artwork.json` identifies
original ink colours and source regions independently from the label positions
in `data/wr1/clear_text_pages.json`. Cleanup preserves overlapping characters,
panel edges and illustrations. The title board is reconstructed from its surviving
edges while retaining the episode strip and foreground characters. The original
assets remain available for the legacy renderer. Moving or resizing modern text
cannot repaint its background.
The help screen corrects the original artwork's reversed Ctrl/Alt descriptions
to match the recovered input behavior. Tiny decorative marks on illustrated
books and the artist's logo remain part of the pictures. Changing vocabulary or
learning rules is a separate content/gameplay change.

## Display and rules

- Game coordinates, contact cells, actor state, RNG, input admission and simulated
  drawing costs remain the original model. Text does not write to these models.
- Original mode retains its existing 320×200 viewport and VGA presentation path.
- Clear Text uses Godot's `canvas_items` window scaling. Original sprites remain
  nearest-neighbour pixel art; font glyphs render at actual window resolution.
  It displays the live scene, without emulating VGA scanout/tearing on the readable
  screen. The preserved reference video stream still models original scanout.
- In Clear Text, a 320×200 SubViewport shares the scene's World2D for reference
  rasterization. HUD/recap CanvasLayers are temporarily directed to that viewport
  for synchronous capture, then restored. No scene/input update is performed by
  this capture. The reference viewport cannot receive input.
- Visibility bits: 1 = shared original scene; 2 = readable/output display;
  4 = original glyphs/chrome replaced on the readable display. Reference capture
  sees 1+4 and the readable scene sees 1+2. Original mode retains its old masks.
- World letters remain children of their original collectible. Camera motion,
  foreground occlusion and collection therefore use the existing scene order.
- HUD text follows explicit presentation values. Hard hides the unrevealed
  suffix, and collecting another letter preserves an already-revealed book hint.
  Popups overlay the paused readable scene, avoiding bitmap text in their backdrop.
- Frontend text runs preserve the BIOS layout's leading-space indentation around
  illustrations, while visible letters use proportional spacing. Name-entry
  caret placement follows the font advances. Demo transitions hide the readable
  page controls with the original page sprite.
- Recap text fades over the same twenty dissolve events; the original raster
  retains its original random-pixel dissolve. No extra RNG calls are made.

## Descender regression

The first layout let the current-word bevel overlap the bottom of the text.
The test reproduced this with `gypqj`: only 1194 solid foreground pixels remained
inside the word strip, versus 1236 in an unconstrained Label of the same font.
The readable strip now restores the original beveled panel and uses smaller
text fitted within its interior. Layout uses the bundled font's Latin ink bounds
with padding and a stable baseline. Font
metrics cover the original ASCII vocabulary, including all five descenders.

`testing/test_wr1_clear_text.py` runs the actual game in both display modes. It
compares their original 320×200 raster, checks that readable glyphs contain detail
above the old resolution, and compares complete descenders in both HUD fields
with unconstrained Labels using the same Andika font and size. The scene checks
also exercise hidden suffixes, book hints, long words, collectible letters,
word-list cleanup, state immutability, resizing to 960×600, and unchanged original
projection when the window aspect ratio changes. World word-card, bonus and recap
reference images must also match between display modes. Every frontend page is
captured at actual window resolution for review. The graphical attract test also
runs in Clear Text mode, starts all 15 demos, naturally completes one, and checks
that it restores the exact paused game image and initial-menu image afterward.

Run with `GODOT` set:

```text
python -m unittest testing.test_wr1_clear_text testing.test_wr1_frontend testing.test_wr1_parity_runner
python -m unittest testing.test_wr1_clean_art
python -m unittest testing.test_wr1_attract
just parity --clear-text
```

The demo report explicitly distinguishes reference pixel parity from the actual
Clear Text display. `*_clear.png` files are visual-review evidence, not native
pixel comparisons. Existing one-frame timing residuals are not allowlisted.

## Expanded text validation (2026-09-09)

The expanded display/frontend/runner checks and Clear Text attract-session test
passed (10 tests). The original frontend checks include 46 immutable native page
fixtures. The focused graphical check also passed after the final title cleanup
and bonus-text outline adjustment. Visual captures are under
`testing/output/clear-text-20260909/`.

`testing/output/parity/clear-text-complete-20260909/report.md` covers demo 11 and
demo 4: 2,080/2,080 observed states and 18/18 preserved reference images match;
inputs, timing and terminal boundaries match as well. This is a representative
regression run, not a new full fifteen-demo parity claim. The attract check
starts all fifteen and naturally finishes one, checking live-session restoration.

## Visual alignment pass

`testing/output/clear-text-alignment-20260909/` contains actual window screenshots
of the HUD, question/word cards, letters, bonuses, recap, longest level title,
every frontend page, and resized word lists. `review_*.png` are contact sheets
of those screenshots. Alignment was judged visually: the shared Andika baseline
now sits lower, with a smaller bonus word and a separate recap adjustment to
retain breathing room in its shallow caption area. Dialogs, page headings and
footers are centered in their panels, and name entry draws its caret with the
same font layout as its text.

The screenshot review also caught duplicate word-list lettering: the frontend
text runs had been drawing over the older dedicated word-list labels. The word
list now uses only the shared runs. The automated capture checks guard against
duplicate labels and clipping; they do not replace visual screenshot review.
