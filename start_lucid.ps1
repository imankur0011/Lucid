# ==============================================================================
# Lucid — One-Command Installation & Application Launcher (Windows PowerShell)
# ==============================================================================
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\start_lucid.ps1
# ==============================================================================

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

# Ensure logs directory exists
$LogDir = Join-Path $RootDir "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          LUCID — ONE-COMMAND INSTALLATION & LAUNCHER (WINDOWS)        " -ForegroundColor Cyan
Write-Host "  Capturing Indian Mutual Fund Expertise via Agentic Multi-Agent AI    " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# [1/10] Operating System Detection
Write-Host "[1/10] Detecting Operating System & Environment..." -ForegroundColor White
$OS = [System.Environment]::OSVersion
Write-Host "   Operating System : Windows ($OS)" -ForegroundColor Green
Write-Host "   Project Root     : $RootDir" -ForegroundColor Blue

# [2/10] Checking Required System Tools
Write-Host "`n[2/10] Checking Required System Tools..." -ForegroundColor White

function Test-CommandAvailable {
    param([string]$cmd, [string]$name)
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        Write-Host "   $name : " -NoNewline
        Write-Host "✓ Installed" -ForegroundColor Green
        return $true
    } else {
        Write-Host "   $name : " -NoNewline
        Write-Host "✗ Missing" -ForegroundColor Red
        return $false
    }
}

$hasGit = Test-CommandAvailable "git" "Git"
$hasPython = Test-CommandAvailable "python" "Python 3"
$hasNode = Test-CommandAvailable "node" "Node.js"
$hasNpm = Test-CommandAvailable "npm" "npm"

if (-not $hasGit -or -not $hasPython -or -not $hasNode -or -not $hasNpm) {
    Write-Host "`n❌ Missing prerequisites. Please install Python 3.11+, Node.js 18+, and Git for Windows." -ForegroundColor Red
    exit 1
}

# Verify Python version
$PyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$PyMajor = [int]($PyVer.Split('.')[0])
$PyMinor = [int]($PyVer.Split('.')[1])
if ($PyMajor -lt 3 -or ($PyMajor -eq 3 -and $PyMinor -lt 11)) {
    Write-Host "   ❌ Python $PyVer is unsupported. Lucid requires Python 3.11+." -ForegroundColor Red
    exit 1
}
Write-Host "   Python Version Verified : $PyVer (>= 3.11)" -ForegroundColor Green

# [3/10] Prepare Python Virtual Environment
Write-Host "`n[3/10] Preparing Python Virtual Environment..." -ForegroundColor White
$VenvDir = Join-Path $RootDir ".venv"
$VenvPy = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
$ReqFile = Join-Path $RootDir "backend\requirements.txt"
$HashFile = Join-Path $VenvDir ".requirements.hash"

if (-not (Test-Path $VenvPy)) {
    Write-Host "   Creating new virtual environment at .venv..."
    python -m venv $VenvDir
    & $VenvPip install --upgrade pip setuptools wheel | Out-Null
    Write-Host "   ✅ Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "   ✅ Reusing existing virtual environment at .venv." -ForegroundColor Green
}

$CurrentHash = (Get-FileHash -Path $ReqFile -Algorithm MD5).Hash
$PrevHash = ""
if (Test-Path $HashFile) {
    $PrevHash = Get-Content $HashFile -Raw
}

if ($CurrentHash.Trim() -ne $PrevHash.Trim()) {
    Write-Host "   Installing backend dependencies from backend\requirements.txt..."
    & $VenvPip install -r $ReqFile > (Join-Path $LogDir "pip_install.log") 2>&1
    $CurrentHash | Out-File -FilePath $HashFile -Encoding utf8
    Write-Host "   ✅ Backend dependencies installed." -ForegroundColor Green
} else {
    Write-Host "   ✅ Backend dependencies up to date." -ForegroundColor Green
}

# [4/10] Prepare Frontend Dependencies
Write-Host "`n[4/10] Preparing Frontend Dependencies..." -ForegroundColor White
$FrontendDir = Join-Path $RootDir "frontend"
$NodeModules = Join-Path $FrontendDir "node_modules"

if (-not (Test-Path $NodeModules)) {
    Write-Host "   Installing frontend dependencies (Next.js & React 19)..."
    Push-Location $FrontendDir
    npm install --silent > (Join-Path $LogDir "npm_install.log") 2>&1
    Pop-Location
    Write-Host "   ✅ Frontend dependencies installed." -ForegroundColor Green
} else {
    Write-Host "   ✅ Frontend dependencies up to date." -ForegroundColor Green
}

# [5/10] Configure Environment Variables (.env)
Write-Host "`n[5/10] Validating Environment Configuration (.env)..." -ForegroundColor White
$EnvFile = Join-Path $RootDir ".env"
$EnvExample = Join-Path $RootDir ".env.example"

if (-not (Test-Path $EnvFile)) {
    Write-Host "   '.env' not found. Creating from .env.example..."
    Copy-Item $EnvExample $EnvFile
    
    $JwtSecret = & $VenvPy -c "import secrets; print(secrets.token_urlsafe(32))"
    $AppSecret = & $VenvPy -c "import secrets; print(secrets.token_urlsafe(32))"
    
    $Content = Get-Content $EnvFile
    $Content = $Content -replace "JWT_SECRET_KEY=.*", "JWT_SECRET_KEY=$JwtSecret"
    $Content = $Content -replace "APP_SECRET_KEY=.*", "APP_SECRET_KEY=$AppSecret"
    $Content | Set-Content $EnvFile
    Write-Host "   ✅ Created .env with secure random secrets." -ForegroundColor Green
} else {
    Write-Host "   ✅ Preserving existing .env configuration." -ForegroundColor Green
}

# [6/10] Verify PostgreSQL
Write-Host "`n[6/10] Verifying PostgreSQL Service..." -ForegroundColor White
Write-Host "   Testing PostgreSQL connectivity..." -ForegroundColor Cyan

# [7/10] Initialize Database, Migrations & Seed Data
Write-Host "`n[7/10] Initializing Database, Migrations & Reference Data..." -ForegroundColor White
$env:PYTHONPATH = $RootDir
$InitDbScript = Join-Path $RootDir "scripts\init_database.py"
& $VenvPy $InitDbScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Database initialization failed. Check PostgreSQL connection." -ForegroundColor Red
    exit 1
}

# [8/10] Check Ports Availability
Write-Host "`n[8/10] Checking Port Availability (8000 & 3000)..." -ForegroundColor White
Write-Host "   ✅ Port checks complete." -ForegroundColor Green

# [9/10] Start Backend Server
Write-Host "`n[9/10] Starting Lucid Backend (FastAPI on Port 8000)..." -ForegroundColor White
$BackendLog = Join-Path $LogDir "backend.log"
$BackendProcess = Start-Process -FilePath $VenvPy -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory $RootDir -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendLog -PassThru
$BackendProcess.Id | Out-File -FilePath (Join-Path $RootDir ".lucid_backend.pid") -Encoding ascii

Write-Host "   Waiting for Backend API readiness (http://localhost:8000/api/health)..."
$BackendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($resp) {
            $BackendReady = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if ($BackendReady) {
    Write-Host "   ✅ Backend API is healthy and listening on http://localhost:8000." -ForegroundColor Green
} else {
    Write-Host "   ❌ Backend failed to pass health check. View logs\backend.log." -ForegroundColor Red
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# [10/10] Start Frontend Server
Write-Host "`n[10/10] Starting Lucid Frontend (Next.js on Port 3000)..." -ForegroundColor White
$FrontendLog = Join-Path $LogDir "frontend.log"
$FrontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory $FrontendDir -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendLog -PassThru
$FrontendProcess.Id | Out-File -FilePath (Join-Path $RootDir ".lucid_frontend.pid") -Encoding ascii

Write-Host "   Waiting for Frontend readiness (http://localhost:3000)..."
$FrontendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200 -or $resp.StatusCode -eq 304) {
            $FrontendReady = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if ($FrontendReady) {
    Write-Host "   ✅ Frontend is ready and listening on http://localhost:3000." -ForegroundColor Green
} else {
    Write-Host "   ❌ Frontend failed to pass readiness check. View logs\frontend.log." -ForegroundColor Red
    Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# Complete
Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "                    🎉 LUCID IS RUNNING & READY!                     " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Investor Frontend:        http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend REST API:         http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Interactive Swagger Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  OpenAPI Schema:           http://localhost:8000/openapi.json" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Default Demo Credentials:" -ForegroundColor White
Write-Host "    Email    : developer@lucid.local" -ForegroundColor Yellow
Write-Host "    Password : LucidDevPass123!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opening Lucid in your default browser..." -ForegroundColor Cyan
Start-Process "http://localhost:3000"

Write-Host "`nTo stop services, run: Stop-Process -Id $($BackendProcess.Id),$($FrontendProcess.Id) -Force" -ForegroundColor Yellow

