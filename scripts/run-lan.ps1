# Start Django so phones on the same Wi-Fi can connect.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$py = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  Write-Error "Missing .venv. Run: python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt"
}

& (Join-Path $PSScriptRoot "show-lan-url.ps1")
Write-Host ""
Write-Host "Starting server on 0.0.0.0:8001 ..."
& $py manage.py runserver 0.0.0.0:8001
