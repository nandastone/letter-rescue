$ErrorActionPreference = 'Stop'
$treehouseRoot = Split-Path -Parent $PSScriptRoot
& python (Join-Path $treehouseRoot 'tools/treehouse/build_demo.py')
if ($LASTEXITCODE -ne 0) { throw 'Treehouse demo build failed. See the error above.' }
Start-Process (Join-Path $treehouseRoot 'testing/output/treehouse/playable/index.html')
