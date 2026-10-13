# Treehouse title music generation

`midi.py` reads the original SMF resources. `fm_music.py` generates register
writes from the instrument bank and recovered melodic driver rules. The title
track's 1,124 writes and timer-interrupt positions match the original boot.
Selection music adds 47,366 matched writes and 776 pitch-bend events, including
the original byte/fraction interpolation. Rhythm patches are still unsupported.

`render_title_music.py` synthesizes those generated writes with DBOPL. The
build copies `dbopl.cpp` and `dbopl.h` unchanged from the pinned DOSBox Pure
checkout at revision `db325ff427e3d0df2e6c38bc75b00b6771e03b38`, verifies their
SHA-256 hashes, and supplies the small type adapters in this directory. No DOS
emulator or game instructions execute during synthesis. Original captures and
register observations are verification fixtures, never renderer input.

DBOPL is copyright 2002–2021 The DOSBox Team, licensed under GPL version 2 or
later. Its original notices are retained in the copied build sources; the full
license is copied from the pinned checkout's `LICENSE` file. The standalone executable
is a development tool; Godot receives only the generated music asset.

Example (choose a new output directory for each build):

```powershell
python tools/treehouse/render_title_music.py --compiler path/to/g++.exe --output testing/output/treehouse/title-synth-new --install
python tools/treehouse/render_title_music.py --compiler path/to/g++.exe --output testing/output/treehouse/selection-synth-new --sound 20000 --after-title --install
python tools/treehouse/build_godot.py
```

The generated manifest binds the WAV to the original resource and synthesizer
source hashes. `build_godot.py` checks that manifest. Rendering currently groups
register writes by their source-derived timer interrupt, uses the pinned PIT
oscillator/divisor, and includes one second of release after end-of-track.
Looping tracks instead repeat their authored duration. Installation disables
Godot's default lossy WAV compression; the imported title and selection PCM
are checked byte for byte. Selection uses allocation state derived from the
complete title's source events. Fresh synth state and repeated PCM do not yet
reproduce retained oscillator/envelope state after interruption or across loops.
Intra-interrupt execution delays, native mixer resampling and Godot output
waveform equality remain unverified.
