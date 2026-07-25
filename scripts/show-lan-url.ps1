# Print LAN URL for opening the site from a phone on the same Wi-Fi.
$ips = @(Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object {
    $_.IPAddress -notlike '127.*' -and
    $_.IPAddress -notlike '169.254.*' -and
    $_.PrefixOrigin -ne 'WellKnown'
  } |
  Select-Object -ExpandProperty IPAddress -Unique)

Write-Host "Open on your phone (same Wi-Fi):"
if ($ips.Count -eq 0) {
  Write-Host "  (No LAN IPv4 found - check Wi-Fi is connected)"
} else {
  foreach ($ip in $ips) {
    Write-Host ("  http://{0}:8001/" -f $ip)
  }
}
Write-Host ""
Write-Host "Laptop local:"
Write-Host "  http://127.0.0.1:8001/"
