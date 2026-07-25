# Magic Sands Booking — local dev server (port 8001)
# DMC enterprise admin runs separately on port 8000 (voucher-system).

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$Port = if ($env:DEV_SERVER_PORT) { $env:DEV_SERVER_PORT } else { "8001" }
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error ".venv not found. Create it first: python -m venv .venv"
}

Write-Host "=== Magic Sands Booking ==="
Write-Host "Website:       http://127.0.0.1:$Port/"
Write-Host "Hotels:        http://127.0.0.1:$Port/hotels/"
Write-Host "Partner admin: http://127.0.0.1:$Port/admin/login/"
Write-Host "Django admin:  http://127.0.0.1:$Port/django-admin/"
Write-Host "DMC platform (separate project): http://127.0.0.1:8000/admin/"
Write-Host ""

try {
    $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health/" -UseBasicParsing -TimeoutSec 2
    if ($health.Content.Trim() -eq "ok") {
        Write-Host "DMC platform detected on port 8000."
    }
} catch {
    $status = $null
    if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
    if ($status -ne 404) {
        # Port free or not voucher-system — fine for booking-only dev.
    }
}

try {
    $probe = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/admin/login/" -UseBasicParsing -TimeoutSec 2
    if ($probe.Content -match "Magic Sands DMC Enterprise Platform") {
        Write-Warning "Port $Port is in use by voucher-system (DMC admin). Run that project on port 8000 instead."
        exit 1
    }
    Write-Warning "Port $Port is already in use. Stop the existing server or set DEV_SERVER_PORT to another value."
    exit 1
} catch {
    # Port likely free.
}

& $Python manage.py migrate
& $Python manage.py runserver "127.0.0.1:$Port"
