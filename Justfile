# Path to the Godot 4.6 binary. Override with the GODOT env var, e.g.
#   GODOT=/path/to/godot just run
set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

godot := env_var_or_default("GODOT", "C:/Users/nitch/AppData/Local/Microsoft/WinGet/Packages/GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe/Godot_v4.6.1-stable_win64_console.exe")

# List recipes
default:
    @just --list

# Play the new game: Clear Text and smooth motion on the recovered engine.
run *args:
    & "{{godot}}" --path . -- {{args}}

# Play the pixel-exact original Word Rescue (the game `just parity` checks).
legacy *args:
    & "{{godot}}" --path . -- --legacy {{args}}

# The original game with reading text rendered at window resolution.
legacy-clear *args:
    & "{{godot}}" --path . -- --legacy --clear-text {{args}}

# Export the browser build to build/web (needs Godot's web export templates).
web:
    New-Item -ItemType Directory -Force build/web | Out-Null; & "{{godot}}" --headless --export-release "Web" build/web/index.html

# Maintained suite: all 15 original demos, sequentially, against native captures.
# Override PYTHON if Python with Pillow is not on PATH.
parity *args:
    & "{{env_var_or_default("PYTHON", "python")}}" tools/run_wr1_parity.py --godot "{{godot}}" {{args}}; exit $LASTEXITCODE

# Fast clock-only diagnostic; not a replacement for actual-game parity.
clock-probe level updates output *args:
    & "{{godot}}" --headless --path . --script tools/probe_wr1_demo_clock.gd -- {{level}} {{updates}} "{{output}}" {{args}}; exit $LASTEXITCODE
