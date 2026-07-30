# Magic Sands Marketing Site — local dev server (port 8001)
# Enterprise admin: voucher-system on 8000
# Booking platform: magic-sands-booking-platform on 8002

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$Port = if ($env:DEV_SERVER_PORT) { $env:DEV_SERVER_PORT } else { "8001" }
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error ".venv not found. Create it first: python -m venv .venv"
}

Write-Host "=== Magic Sands Marketing Site ==="
Write-Host "Website:          http://127.0.0.1:$Port/"
Write-Host "Admin CMS:        http://127.0.0.1:$Port/admin/login/"
Write-Host "Enterprise (8000): http://127.0.0.1:8000/admin/"
Write-Host "Booking (8002):    http://127.0.0.1:8002/"
Write-Host ""

function Test-PortOwner($port, $label) {
    try {
        $probe = Invoke-WebRequest -Uri "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 2
        Write-Host "$label detected on port $port."
        return $true
    } catch {
        return $false
    }
}

[void](Test-PortOwner 8000 "Enterprise admin")
[void](Test-PortOwner 8002 "Booking platform")

try {
    $probe = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/admin/login/" -UseBasicParsing -TimeoutSec 2
    if ($probe.Content -match "Magic Sands DMC Enterprise Platform") {
        Write-Warning "Port $Port is in use by voucher-system (enterprise). Run that project on port 8000 instead."
        exit 1
    }
    Write-Warning "Port $Port is already in use. Stop the existing server or set DEV_SERVER_PORT to another value."
    exit 1
} catch {
    # Port likely free.
}

& $Python manage.py migrate
& $Python manage.py runserver "127.0.0.1:$Port"
