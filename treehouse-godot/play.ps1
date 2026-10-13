param([switch]$ImportOnly, [switch]$BuildWeb)
$ErrorActionPreference = 'Stop'
$treehouseEngine = $env:GODOT
if (-not $treehouseEngine) {
    $treehouseCommand = Get-Command godot, godot4 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($treehouseCommand) { $treehouseEngine = $treehouseCommand.Source }
}
if (-not $treehouseEngine) {
    $treehouseEngine = Get-ChildItem "$env:LOCALAPPDATA/Microsoft/WinGet/Packages/GodotEngine.GodotEngine_*/Godot_v4.*_win64_console.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $treehouseEngine) { throw 'Install Godot 4.6 or set GODOT.' }
& python "$PSScriptRoot/../tools/treehouse/build_godot.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $treehouseEngine --headless --path $PSScriptRoot --editor --import
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($BuildWeb) {
    New-Item -ItemType Directory -Path "$PSScriptRoot/build/web" -Force | Out-Null
    & $treehouseEngine --headless --path $PSScriptRoot --export-release Web
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} elseif (-not $ImportOnly) { & $treehouseEngine --path $PSScriptRoot }
