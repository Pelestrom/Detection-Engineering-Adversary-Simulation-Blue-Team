# validate_detection.ps1 - Valide que Sysmon capture bien les evenements RANSIM
# Usage (PowerShell admin, dans le lab) :
#   .\validate_detection.ps1 -Target C:\Lab\canary -SimPath C:\Lab\simulator\ransomware_sim.py

param(
    [string]$Target  = "C:\Lab\canary",
    [string]$SimPath = "C:\Lab\simulator\ransomware_sim.py",
    [int]$LookbackMinutes = 15
)

$ErrorActionPreference = "Continue"
$results = @()

function Check($name, $condition) {
    $script:results += [PSCustomObject]@{ Check = $name; Result = $(if ($condition) { "PASS" } else { "FAIL" }) }
}

Write-Host "[*] Validation de detection RANSIM - $((Get-Date).ToString())"

# 0. Sysmon installe ?
$sysmon = Get-Service -Name Sysmon64 -ErrorAction SilentlyContinue
if (-not $sysmon) { $sysmon = Get-Service -Name Sysmon -ErrorAction SilentlyContinue }
Check "Service Sysmon actif" ($null -ne $sysmon -and $sysmon.Status -eq "Running")
if (-not $sysmon) {
    Write-Host "[!] Sysmon non installe. Voir lab/lab-guide.md phase 2."
    $results | Format-Table -AutoSize
    exit 1
}

# 1. Marqueur canary + execution du simulateur
if (-not (Test-Path (Join-Path $Target ".ransim_canary"))) {
    Write-Host "[*] Initialisation du canary..."
    python $SimPath --target $Target --init-canary
}
Write-Host "[*] Execution du simulateur sur le canary..."
python $SimPath --target $Target
Check "Simulation executee" ($LASTEXITCODE -eq 0)

Start-Sleep -Seconds 3

# 2. Recherche des evenements Sysmon attendus
$since = (Get-Date).AddMinutes(-$LookbackMinutes)
$events = Get-WinEvent -FilterHashtable @{
    LogName   = "Microsoft-Windows-Sysmon/Operational"
    StartTime = $since
} -ErrorAction SilentlyContinue

$noteEvt = $events | Where-Object { $_.Id -eq 11 -and $_.Message -match "README_RESTORE_FILES" }
$keyEvt  = $events | Where-Object { $_.Id -eq 11 -and $_.Message -match "ransim_key" }
$execEvt = $events | Where-Object { $_.Id -eq 1  -and $_.Message -match "ransomware_sim" }

Check "EvtID 11 - depose note de rancon" ($null -ne $noteEvt)
Check "EvtID 11 - creation fichier clef" ($null -ne $keyEvt)
Check "EvtID 1  - execution simulateur"  ($null -ne $execEvt)

# 3. Restauration (le canary doit redevenir vierge)
Write-Host "[*] Restauration via decryptor..."
python (Join-Path (Split-Path $SimPath) "decryptor.py") `
    --target $Target `
    --keyfile "ransim_key_DO_NOT_SHARE.key"
Check "Restauration complete" ($LASTEXITCODE -eq 0)

Write-Host ""
$results | Format-Table -AutoSize
$failed = ($results | Where-Object { $_.Result -eq "FAIL" }).Count
Write-Host ("[=] Resume: {0} PASS, {1} FAIL" -f ($results.Count - $failed), $failed)
