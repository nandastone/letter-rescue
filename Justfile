# Path to the Godot 4.6 binary. Override with the GODOT env var, e.g.
#   GODOT=/path/to/godot just run
set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

godot := env_var_or_default("GODOT", "C:/Users/nitch/AppData/Local/Microsoft/WinGet/Packages/GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe/Godot_v4.6.1-stable_win64_console.exe")

# List recipes
default:
    @just --list

# Start the game (runs the project's main scene)
run:
    & "{{godot}}" --path .

# Play with the recovered WR1 rules and original artwork.
run-original *args:
    & "{{godot}}" --path . -- --original-rules {{args}}

# Original rules and artwork, with reading text rendered at window resolution.
run-clear *args:
    & "{{godot}}" --path . -- --original-rules --clear-text {{args}}

# Maintained suite: all 15 original demos, sequentially, against native captures.
# Override PYTHON if Python with Pillow is not on PATH.
parity *args:
    & "{{env_var_or_default("PYTHON", "python")}}" tools/run_wr1_parity.py --godot "{{godot}}" {{args}}; exit $LASTEXITCODE

# Fast clock-only diagnostic; not a replacement for actual-game parity.
clock-probe level updates output *args:
    & "{{godot}}" --headless --path . --script tools/probe_wr1_demo_clock.gd -- {{level}} {{updates}} "{{output}}" {{args}}; exit $LASTEXITCODE
