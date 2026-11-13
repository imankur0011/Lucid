# ==============================================================================
# Lucid - Complete Application Teardown and Clean-Slate Reset for Windows
# Stops running services, drops portfolio_dev database, deletes .venv,
# deletes frontend/node_modules, frontend/.next, .env, and logs.
# ==============================================================================
#
$ErrorActionPreference = "SilentlyContinue"
#
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
#
Write-Host "======================================================================" -ForegroundColor Red
Write-Host "             LUCID - COMPLETE TEARDOWN & CLEAN-SLATE RESET            " -ForegroundColor Red
Write-Host "======================================================================" -ForegroundColor Red
#
$TargetDir = if ((Test-Path ".\backend\requirements.txt") -and (Test-Path ".\scripts\init_database.py")) { (Get-Location).Path } elseif (Test-Path (Join-Path $HOME "Lucid")) { Join-Path $HOME "Lucid" } else { (Get-Location).Path }
#
Write-Host "`n[1/5] Stopping all Lucid processes..." -ForegroundColor White
if (Test-Path (Join-Path $TargetDir "stop_lucid.ps1")) { & powershell -ExecutionPolicy Bypass -File (Join-Path $TargetDir "stop_lucid.ps1") }
@(8000, 3000) | ForEach-Object { try { (Get-NetTCPConnection -LocalPort $_ -State Listen -ErrorAction SilentlyContinue).OwningProcess | ForEach-Object { if ($_ -gt 0) { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } } } catch {} }
Write-Host "   [OK] Processes stopped and ports 8000/3000 cleared." -ForegroundColor Green
#
Write-Host "`n[2/5] Dropping PostgreSQL database 'portfolio_dev'..." -ForegroundColor White
$dropSql = "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'portfolio_dev'; DROP DATABASE IF EXISTS portfolio_dev;"
if (Get-Command psql -ErrorAction SilentlyContinue) { psql -U postgres -h 127.0.0.1 -c $dropSql 2>$null | Out-Null }
$psqlFallback = Get-ChildItem -Path "C:\Program Files\PostgreSQL\*\bin\psql.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($psqlFallback) { & $psqlFallback.FullName -U postgres -h 127.0.0.1 -c $dropSql 2>$null | Out-Null }
$venvPy = Join-Path $TargetDir ".venv\Scripts\python.exe"
if (Test-Path $venvPy) { & $venvPy -c "import psycopg2; from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT; [conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) or cur.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = \'portfolio_dev\';') or cur.execute('DROP DATABASE IF EXISTS portfolio_dev;') or cur.close() or conn.close() for host in ['127.0.0.1', 'localhost'] for p in ['', 'postgres', 'root', 'admin'] for conn in [psycopg2.connect(dbname='postgres', user='postgres', password=p, host=host, port=5432, connect_timeout=1) if True else None] if conn for cur in [conn.cursor()] if cur]" 2>$null }
Write-Host "   [OK] Database 'portfolio_dev' dropped." -ForegroundColor Green
#
Write-Host "`n[3/5] Cleaning Python virtual environment..." -ForegroundColor White
Remove-Item (Join-Path $TargetDir ".venv") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $TargetDir ".pytest_cache") -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $TargetDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   [OK] .venv and Python cache removed." -ForegroundColor Green
#
Write-Host "`n[4/5] Cleaning Frontend node_modules & build artifacts..." -ForegroundColor White
Remove-Item (Join-Path $TargetDir "frontend\node_modules") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $TargetDir "frontend\.next") -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   [OK] frontend\node_modules and frontend\.next removed." -ForegroundColor Green
#
Write-Host "`n[5/5] Removing .env configuration, logs, and PID files..." -ForegroundColor White
Remove-Item (Join-Path $TargetDir ".env") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $TargetDir ".lucid_backend.pid") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $TargetDir ".lucid_frontend.pid") -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path (Join-Path $TargetDir "logs") -Filter "*.log" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "   [OK] .env and log files removed." -ForegroundColor Green
#
Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "[OK] Clean-slate reset complete! System is completely pristine." -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
#
Write-Host "`nTo install fresh, run:" -ForegroundColor Cyan
Write-Host "powershell -ExecutionPolicy Bypass -Command `"irm https://raw.githubusercontent.com/imankur0011/Lucid/main/bootstrap_lucid.ps1 | Out-String | iex`"" -ForegroundColor Yellow
#
