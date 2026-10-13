# The Treehouse playable demo

**Runtime correction, 2026-10-05:** the final game is being ported to Godot,
following Word Rescue and Math Rescue. This JavaScript build is retained as a
development reference. See `../treehouse-godot/README.md` for the current port
and `../testing/treehouse/remaining-work.json` for required migration work.

An independent browser reconstruction using the original DOS v1.1 resource
data. The browser executes JavaScript, decoded graphics, sound samples, and
original SCR animation instructions. It does not run DOSBox, execute the DOS
binary, or play back recorded screenshots.

## Play

The generated portable file is
`testing/output/treehouse/playable/index.html`. Open it in Edge or Chrome.
No server or network connection is required. The original ZIP is needed only
to rebuild the file, not to play it.

From the repository root, rebuild and open it:

```powershell
./treehouse-demo/play.ps1
```

Or build without opening:

```powershell
python tools/treehouse/build_demo.py
```

Python 3 and Pillow are build dependencies. The default original archive is
`testing/output/treehouse/source/The_Treehouse_1991.zip`; use `--source` to
provide the same pinned package elsewhere. A different executable/archive
fails explicitly instead of being interpreted with this build's offsets.

## Playable scope

- Choose either character and watch the original entrance animation and rotating credits.
- Revisit the yard without restarting. Play with the pond, sun, cloud and birdhouse,
  call your friend at the window, and enter the squirrel hollow to toss three nuts.
- Enter the reconstructed treehouse; click the keyboard, nature picture, theater curtains, board game, chalk, or telescope.
- Play 17 chromatic piano keys using mouse, touch, or the original keyboard
  layout: `Z S X D C V G B H N J M , L . ; /`.
- Explore seven original instrument-family menus, choose 35 individual
  instruments or seven ensembles, and hear their original samples/animations.
- Play 24 original songs with five speed settings and large or two-staff notation.
- Record a monophonic tune, save it locally, and replay it.
- Compose in both original songbooks: 42 short and 42 long songs, with note/rest
  dragging, replacement, erasing, naming, copying, random songs and repeat.
  Songbooks save locally and import/export the original SONGS.DAT format.
- Play the musical maze: match five types of sound challenges across nine
  scenes, collect notes, guess the song, win, and play again.
- Read the original daily calendar stories with enlarged text, browse days, and
  return to today. The room shows the local date and a live clock. Cycle clouds
  and use the original exit ladder.
- Explore all four telescope views, including the robot's animated earned-prize shelf.
  Original character walks and bubble/ring transitions connect the rooms.
- Build a sentence play with eight actors, eight actions, six places, and four
  time settings, original spoken phrases, weather, and movable decorations.
- Hold and drag sentence tokens to swap or remove them, add words from the
  notebook, shuffle, correct sentence order, and receive original grammar feedback.
- Explore all 92 original animals, read their facts, filter their characteristics,
  and build separate day/night collages with up to 40 animals each.
- Play the animal guessing game with a friend or robot, ask questions, cross out
  candidates, and reveal the winning animal with original resource animations.
  Inspect candidates and read original attribute definitions in matching panels.
- Draw with six original chalk colors and the eraser. An enlarged pad adds smooth
  mouse/touch strokes, undo and clear; the room retains original brush geometry.
- Play Money and Chip board games with three goals and a friend or robot. Follow
  the original directed roads, compare rewards, and perform chip carries/borrows.
  Dashboard, reward delivery, moneybag and chip-transfer sequences now animate.
  Arrow keys move the original pointer; Enter/Space activate its current target.
  Hold Space while moving to drag, and hold Shift for faster pointer movement.
- Increase readable text to 30px; your chosen size survives reloading. Read aloud uses an installed local English
  voice when one is available. Original bitmap text remains on the game image.
- F1 opens original contextual help; F2 opens preferences. Ctrl+S toggles sound
  and Ctrl+V shows the original version panel.
- Save and load original STATUS.DAT files, including creations and room prizes.
- Home returns to character selection. Back/Escape returns from an activity.

The side panel provides readable instructions, accessible controls, and original
instrument facts. These controls, local tune recording, and responsive layout
are demo additions. They are not claims of equivalence to the original editor.

## Fidelity and current boundaries

The target is faithful reproduction first, including original redraw timing and
intermediate displays. Improvements follow that baseline. The
[timing fidelity report](../testing/treehouse_timing_fidelity.md) records the
strict comparison failures separately from passing gameplay regressions.

`presentation.js` is the verified four-part scanout component under development.
It is not bundled into the live game yet: its isolated 306-callback check uses
original clock fixtures, and independently reproducing the drawing schedule is
still required. See [redraw reconstruction](../testing/treehouse_redraw_reconstruction.md).

The current verified build and exact counts are recorded in
[completion progress](../testing/treehouse_completion_progress.md) and its
[machine-readable verification](../testing/treehouse/completion_verification.json).
The [remaining-work ledger](../testing/treehouse/remaining-work.md) tracks the
active completion loop. `python tools/treehouse/completion_status.py` reports
open issues and rejects completion while strict integrated comparisons fail.
All activities are playable, including original help, confirmations, printing,
prizes, preferences and file interchange. Modern readable controls coexist with
the original 320Ã—200 framebuffer.

Pixel comparisons cover complete native screens, selected regions, and ordered
stages. They do not establish exhaustive native timing parity. The current pass
includes ordered room transfers, telescope walks, yard and squirrel animations,
robot shelf playback, and a complete robot nature turn. Exhaustive global random
call ordering and complete audio waveform equality are not established. The
browser now uses an AudioWorklet with the pinned mixer's interpolation and stop
decay: all 336 measured instrument windows match exactly after one attack
alignment per note. Actual input, mute, replacement ownership and focus-loss
checks pass on both file and HTTP origins. Absolute sound timing, complete
unaligned waveforms and speech/effect journeys remain open. See the
[audio delivery report](../testing/treehouse_audio_mixer.md).
An original video callback caught halfway through
redrawing a counter is documented separately from completed-frame comparisons.

The theater now includes original click feedback, notebook-to-sentence token
travel, curtain transitions and narration ordering. Its complete observed
sound journey matches all 73 original source observations, including 33 cues
previously absent. All 29 theater and 14 notebook endpoint images/state checks
pass; intermediate presentation and whole-waveform timing remain incomplete.
See the [theater sound journey](../testing/treehouse_theater_sound_journey.md).

Chalk and nature erase use the original confirmation dialogs and animation.
Enlarged drawing-pad interpolation, undo, readable controls, local narration,
and responsive layout are modern additions. The fourth telescope view shows the robot's prizes and plays its original
celebration when the robot has earned a prize.

Original assets and generated HTML stay in ignored `testing/output/`. Source
files here are the app, renderer, styles, and recovered numeric music tables.
The existing Letter Rescue game is unchanged.

## Verification

With Python Playwright and installed Edge:

Run the complete suite against an immutable candidate:

```powershell
python tools/treehouse/verify_all.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/all-checks-new
python tools/treehouse/verify_environment.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/environment-check-new
python tools/treehouse/verify_timing.py --strict --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/timing-strict-new
```

The suite includes fresh desktop and touch journeys through the visible controls,
with saving/reloading of creations, both character entrances, and reading settings.
Individual checks can also run separately:

```powershell
python tools/treehouse/verify_demo.py --output testing/output/treehouse/demo-check-new
python tools/treehouse/verify_theater.py --output testing/output/treehouse/theater-check-new
python tools/treehouse/verify_entrance.py --output testing/output/treehouse/entrance-check-new.json
python tools/treehouse/verify_nature.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/nature-check-new
python tools/treehouse/verify_continuation.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/continuation-check-new
python tools/treehouse/verify_chalkboard.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/chalk-check-new
python tools/treehouse/verify_boardgame.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/boardgame-check-new
python tools/treehouse/verify_theater_playback.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/playback-check-new.json
python tools/treehouse/verify_music_followup.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/music-followup-check-new
python tools/treehouse/verify_music_editor.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/music-editor-check-new
python tools/treehouse/verify_music_maze.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/music-maze-check-new
python tools/treehouse/verify_room.py --html testing/output/treehouse/playable/index.html --output testing/output/treehouse/room-check-new
```

Output directories must be new. This exercises both character entrances, all
instrument samples and auditions, every song, recording/replay, telescope views,
mobile layout, and the ordinary real-time animation loop. It also compares full
native frames and exports lossless differences, retaining every mismatch.

See [scene research](../testing/treehouse_demo_scene_research.md),
[music and sound research](../testing/treehouse_demo_music_research.md), and
[capture infrastructure](../tools/treehouse/README.md).

The [current delivery report](../testing/treehouse_completion_progress.md) records
verification of this build and the remaining reconstruction work. Earlier reports
retain the hashes and results of earlier builds.
