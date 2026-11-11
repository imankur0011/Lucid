# ==============================================================================
# Lucid - System and Service Status Inspector (Windows PowerShell)
# ==============================================================================
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\status_lucid.ps1
# ==============================================================================

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "                    LUCID SYSTEM STATUS INSPECTOR                     " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. System Environment
Write-Host "`n[1] System and Runtime Environment:" -ForegroundColor White
$OS = [System.Environment]::OSVersion
Write-Host "   OS / Arch        : Windows ($OS)"

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
    Write-Host "   Python           : $pyVer" -ForegroundColor Green
} else {
    Write-Host "   Python           : Not installed" -ForegroundColor Red
}

$venvPy = Join-Path $RootDir ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    Write-Host "   Virtualenv       : Active (.venv)" -ForegroundColor Green
} else {
    Write-Host "   Virtualenv       : Missing (.venv)" -ForegroundColor Yellow
}

if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVer = node -v
    Write-Host "   Node.js          : $nodeVer" -ForegroundColor Green
} else {
    Write-Host "   Node.js          : Not installed" -ForegroundColor Red
}

if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmVer = npm -v
    Write-Host "   npm              : $npmVer" -ForegroundColor Green
} else {
    Write-Host "   npm              : Not installed" -ForegroundColor Red
}

# 2. Backend Service Status
Write-Host "`n[2] Backend API Service (Port 8000):" -ForegroundColor White
$backendRunning = $false
try {
    $healthResp = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($healthResp) {
        $backendRunning = $true
        Write-Host "   Status           : [*] RUNNING and HEALTHY" -ForegroundColor Green
        Write-Host "   URL              : http://localhost:8000"
        Write-Host "   API Status       : $($healthResp.api)" -ForegroundColor Cyan
    }
} catch {}

if (-not $backendRunning) {
    Write-Host "   Status           : [-] STOPPED (Port 8000 is free)" -ForegroundColor Red
}

# 3. Frontend Web Application Status
Write-Host "`n[3] Frontend Web Application (Port 3000):" -ForegroundColor White
$frontendRunning = $false
try {
    $webResp = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($webResp.StatusCode -eq 200 -or $webResp.StatusCode -eq 304) {
        $frontendRunning = $true
        Write-Host "   Status           : [*] RUNNING and READY" -ForegroundColor Green
        Write-Host "   URL              : http://localhost:3000"
        Write-Host "   HTTP Status      : $($webResp.StatusCode) OK" -ForegroundColor Green
    }
} catch {}

if (-not $frontendRunning) {
    Write-Host "   Status           : [-] STOPPED (Port 3000 is free)" -ForegroundColor Red
}

# 4. PostgreSQL Database Inspection
Write-Host "`n[4] PostgreSQL Database Status and Record Counts:" -ForegroundColor White
$dbOk = $false
if (Test-Path (Join-Path $RootDir ".env")) {
    $pyCmd = if (Test-Path $venvPy) { $venvPy } else { "python" }
    $code = @"
import sys, os
from pathlib import Path
root = Path(r'$RootDir')
sys.path.insert(0, str(root))
try:
    from backend.database.session import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        t_count = conn.execute(text(\"SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'\")).scalar()
        s_count = conn.execute(text('SELECT count(*) FROM securities')).scalar()
        u_count = conn.execute(text('SELECT count(*) FROM app_users')).scalar()
        print(f'OK|{t_count}|{s_count}|{u_count}')
except Exception as e:
    print(f'ERR|{str(e)}')
"@
    $dbOutput = & $pyCmd -c $code 2>$null
    if ($dbOutput -like "OK*") {
        $dbOk = $true
        $parts = $dbOutput.Split('|')
        Write-Host "   Connection       : [OK] CONNECTED" -ForegroundColor Green
        Write-Host "   Schema Tables    : $($parts[1]) tables registered" -ForegroundColor Green
        Write-Host "   Exchange Stocks  : $($parts[2]) securities stored" -ForegroundColor Green
        Write-Host "   User Accounts    : $($parts[3]) user account(s)" -ForegroundColor Green
    } else {
        Write-Host "   Connection       : [FAIL] FAILED" -ForegroundColor Red
    }
} else {
    Write-Host "   Configuration    : [FAIL] .env file missing" -ForegroundColor Red
}

# 5. Overall Status
Write-Host "`n======================================================================" -ForegroundColor White
if ($backendRunning -and $frontendRunning -and $dbOk) {
    Write-Host "[OK] OVERALL STATUS: ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    Write-Host "   Lucid is fully running at http://localhost:3000" -ForegroundColor Cyan
} elseif ($backendRunning -or $frontendRunning) {
    Write-Host "[WARN] OVERALL STATUS: PARTIALLY RUNNING" -ForegroundColor Yellow
} else {
    Write-Host "[STOPPED] OVERALL STATUS: ALL SERVICES STOPPED" -ForegroundColor Red
    Write-Host "   Start Lucid using: powershell .\start_lucid.ps1"
}
Write-Host "======================================================================" -ForegroundColor White

