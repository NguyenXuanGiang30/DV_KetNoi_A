# Check for administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Requesting administrator privileges..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Configuring Windows Firewall for Smart Campus Ports" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

$ports = @(8001, 8002, 8003, 8004, 8005, 8006, 8007)

foreach ($port in $ports) {
    $ruleName = "Smart Campus - Service Port $port"
    
    # Remove old rule if exists to avoid duplication
    netsh advfirewall firewall delete rule name=$ruleName | Out-Null
    
    # Add new inbound TCP allow rule
    netsh advfirewall firewall add rule name=$ruleName dir=in action=allow protocol=TCP localport=$port | Out-Null
    Write-Host "[OK] Allowed TCP Port $port ($ruleName)" -ForegroundColor Cyan
}

Write-Host "`n[SUCCESS] Firewall configuration completed! Press Enter to exit..." -ForegroundColor Green
Read-Host
