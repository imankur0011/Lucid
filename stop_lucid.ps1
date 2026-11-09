# ==============================================================================
# Lucid — Service Stop Script (Windows PowerShell)
# Gracefully terminates Lucid Backend and Frontend services on Windows.
# ==============================================================================
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\stop_lucid.ps1
# ==============================================================================

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "                    LUCID SERVICE STOP UTILITY                        " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$stoppedAnything = $false

function Stop-ByPidFile {
    param([string]$serviceName, [string]$pidFileName)
    $pidFile = Join-Path $RootDir $pidFileName
    if (Test-Path $pidFile) {
        $procId = (Get-Content $pidFile -Raw).Trim()
        if ($procId -match '^\d+$') {
            try {
                $proc = Get-Process -Id [int]$procId -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "   Stopping $serviceName (PID: $procId)..."
                    Stop-Process -Id [int]$procId -Force -ErrorAction SilentlyContinue
                    Write-Host "   ✓ $serviceName stopped." -ForegroundColor Green
                    $script:stoppedAnything = $true
                }
            } catch {}
        }
        Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
    }
}

function Stop-ByPort {
    param([string]$serviceName, [int]$port)
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            $pId = $c.OwningProcess
            if ($pId -gt 0) {
                Write-Host "   Releasing port $port (PID: $pId - $serviceName)..."
                Stop-Process -Id $pId -Force -ErrorAction SilentlyContinue
                Write-Host "   ✓ Port $port released." -ForegroundColor Green
                $script:stoppedAnything = $true
            }
        }
    } catch {}
}

Write-Host "`n[1/2] Terminating Lucid Processes by PID file..." -ForegroundColor White
Stop-ByPidFile "Lucid Frontend" ".lucid_frontend.pid"
Stop-ByPidFile "Lucid Backend" ".lucid_backend.pid"

Write-Host "`n[2/2] Checking Ports 8000 and 3000 for Remaining Listeners..." -ForegroundColor White
Stop-ByPort "FastAPI Backend" 8000
Stop-ByPort "Next.js Frontend" 3000

Write-Host ""
if ($stoppedAnything) {
    Write-Host "✅ All Lucid application services have been stopped successfully." -ForegroundColor Green
} else {
    Write-Host "ℹ️ No running Lucid services were found on ports 8000 or 3000." -ForegroundColor Yellow
}

Write-Host "Note: PostgreSQL database server remains untouched and running." -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
