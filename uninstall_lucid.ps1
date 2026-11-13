# ==============================================================================
# Lucid — Complete Application Teardown & Clean-Slate Reset for Windows
# Stops running services, drops portfolio_dev database, deletes .venv,
# deletes frontend/node_modules, frontend/.next, .env, and logs.
# ==============================================================================

$ErrorActionPreference = "SilentlyContinue"

Write-Host "======================================================================" -ForegroundColor Red
Write-Host "             LUCID — COMPLETE TEARDOWN & CLEAN-SLATE RESET            " -ForegroundColor Red
Write-Host "======================================================================" -ForegroundColor Red

# Determine target directory
$TargetDir = Join-Path $HOME "Lucid"
if ((Test-Path (Join-Path (Get-Location) "backend\requirements.txt")) -and (Test-Path (Join-Path (Get-Location) "scripts\init_database.py"))) {
    $TargetDir = (Get-Location).Path
}

# 1. Stop Processes
Write-Host "`n[1/5] Stopping all Lucid processes..." -ForegroundColor White
$stopScript = Join-Path $TargetDir "stop_lucid.ps1"
if (Test-Path $stopScript) {
    & powershell -ExecutionPolicy Bypass -File $stopScript
}
# Kill port 8000 and 3000
foreach ($port in @(8000, 3000)) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    } catch {}
}
Write-Host "   [OK] Processes stopped and ports 8000/3000 cleared." -ForegroundColor Green

# 2. Drop PostgreSQL Database
Write-Host "`n[2/5] Dropping PostgreSQL database 'portfolio_dev'..." -ForegroundColor White
$dropSql = "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'portfolio_dev'; DROP DATABASE IF EXISTS portfolio_dev;"
if (Get-Command psql -ErrorAction SilentlyContinue) {
    psql -U postgres -h 127.0.0.1 -c $dropSql 2>$null | Out-Null
} else {
    $psqlExe = Get-ChildItem -Path "C:\Program Files\PostgreSQL\*\bin\psql.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($psqlExe) {
        & $psqlExe.FullName -U postgres -h 127.0.0.1 -c $dropSql 2>$null | Out-Null
    }
}
Write-Host "   [OK] Database 'portfolio_dev' dropped." -ForegroundColor Green

# 3. Clean Python Virtual Environment
Write-Host "`n[3/5] Cleaning Python virtual environment..." -ForegroundColor White
Remove-Item (Join-Path $TargetDir ".venv") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $TargetDir ".pytest_cache") -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $TargetDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   [OK] .venv and Python cache removed." -ForegroundColor Green

# 4. Clean Frontend node_modules & Next.js Build
Write-Host "`n[4/5] Cleaning Frontend node_modules & build artifacts..." -ForegroundColor White
Remove-Item (Join-Path $TargetDir "frontend\node_modules") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $TargetDir "frontend\.next") -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   [OK] frontend\node_modules and frontend\.next removed." -ForegroundColor Green

# 5. Clean Environment & Logs
Write-Host "`n[5/5] Removing .env configuration, logs, and PID files..." -ForegroundColor White
Remove-Item (Join-Path $TargetDir ".env") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $TargetDir ".lucid_backend.pid") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $TargetDir ".lucid_frontend.pid") -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path (Join-Path $TargetDir "logs") -Filter "*.log" | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "   [OK] .env and log files removed." -ForegroundColor Green

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "🎉 Clean-slate reset complete! System is completely pristine." -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "`nTo test the fresh one-command installation from scratch, run:" -ForegroundColor Cyan
Write-Host "powershell -ExecutionPolicy Bypass -Command `"irm https://raw.githubusercontent.com/imankur0011/Lucid/main/bootstrap_lucid.ps1 | iex`"" -ForegroundColor Yellow

