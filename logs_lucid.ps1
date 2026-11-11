# ==============================================================================
# Lucid - Log Streaming Utility (Windows PowerShell)
# ==============================================================================
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\logs_lucid.ps1 [backend|frontend|all|clear]
# ==============================================================================

param(
    [string]$Target = "all",
    [int]$Lines = 50
)

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

$LogDir = Join-Path $RootDir "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$BackendLog = Join-Path $LogDir "backend.log"
$FrontendLog = Join-Path $LogDir "frontend.log"

if (-not (Test-Path $BackendLog)) { New-Item -ItemType File -Path $BackendLog | Out-Null }
if (-not (Test-Path $FrontendLog)) { New-Item -ItemType File -Path $FrontendLog | Out-Null }

switch ($Target.ToLower()) {
    "backend" {
        Write-Host "==> Streaming Lucid Backend Logs (logs\backend.log)..." -ForegroundColor Cyan
        Get-Content -Path $BackendLog -Tail $Lines -Wait
    }
    "frontend" {
        Write-Host "==> Streaming Lucid Frontend Logs (logs\frontend.log)..." -ForegroundColor Cyan
        Get-Content -Path $FrontendLog -Tail $Lines -Wait
    }
    "clear" {
        Clear-Content -Path $BackendLog -ErrorAction SilentlyContinue
        Clear-Content -Path $FrontendLog -ErrorAction SilentlyContinue
        Clear-Content -Path (Join-Path $LogDir "backend_err.log") -ErrorAction SilentlyContinue
        Clear-Content -Path (Join-Path $LogDir "frontend_err.log") -ErrorAction SilentlyContinue
        Write-Host "[OK] All log files cleared." -ForegroundColor Green
    }
    default {
        Write-Host "==> Streaming Lucid Backend Logs (logs\backend.log)..." -ForegroundColor Cyan
        Get-Content -Path $BackendLog -Tail $Lines -Wait
    }
}

