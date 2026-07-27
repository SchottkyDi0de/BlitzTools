$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    throw "Poetry is required. Install it and run this script from the repo root."
}

$exePath = Join-Path $Root "dist\BlitzTools.exe"
Get-Process -Name "BlitzTools","main" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
if (Test-Path $exePath) {
    Start-Sleep -Milliseconds 500
    Remove-Item $exePath -Force -ErrorAction SilentlyContinue
}
$legacyExe = Join-Path $Root "dist\main.exe"
if (Test-Path $legacyExe) {
    Remove-Item $legacyExe -Force -ErrorAction SilentlyContinue
}

$env:PYINSTALLER_LOG_LEVEL = "WARN"

poetry run pyinstaller packaging/blitztools.spec --noconfirm --distpath dist --workpath build --log-level WARN
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "Build complete: $exePath"
