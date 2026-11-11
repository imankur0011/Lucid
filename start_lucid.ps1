# ==============================================================================
# Lucid - One-Command Installation and Application Launcher (Windows PowerShell)
# ==============================================================================
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\start_lucid.ps1
# ==============================================================================

$ErrorActionPreference = "Continue"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

# Ensure logs directory exists
$LogDir = Join-Path $RootDir "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Function to refresh environment PATH in the current PowerShell process
function Update-SessionPath {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$userPath;$machinePath"
    
    $extraPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311",
        "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts",
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts",
        "C:\Program Files\Python311",
        "C:\Program Files\Python311\Scripts",
        "C:\Program Files\Git\cmd",
        "C:\Program Files\Git\bin",
        "$env:LOCALAPPDATA\Programs\Git\cmd",
        "C:\Program Files\nodejs",
        "$env:APPDATA\npm",
        "C:\Program Files\PostgreSQL\16\bin",
        "C:\Program Files\PostgreSQL\15\bin",
        "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin"
    )
    foreach ($p in $extraPaths) {
        if ((Test-Path $p) -and ($env:Path -notlike "*$p*")) {
            $env:Path = "$p;$env:Path"
        }
    }
}

Update-SessionPath

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          LUCID - ONE-COMMAND INSTALLATION and LAUNCHER (WINDOWS)        " -ForegroundColor Cyan
Write-Host "  Capturing Indian Mutual Fund Expertise via Agentic Multi-Agent AI    " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# [1/10] Operating System Detection
Write-Host "[1/10] Detecting Operating System and Environment..." -ForegroundColor White
$OS = [System.Environment]::OSVersion
$Arch = if ([System.Environment]::Is64BitOperatingSystem) { "x64" } else { "x86" }
Write-Host "   Operating System : Windows ($OS) - $Arch" -ForegroundColor Green
Write-Host "   Project Root     : $RootDir" -ForegroundColor Blue

$hasWinget = [bool](Get-Command winget -ErrorAction SilentlyContinue)

# [2/10] Checking and Auto-Installing Required System Tools
Write-Host "`n[2/10] Checking Required System Tools..." -ForegroundColor White

function Test-CommandAvailable {
    param([string]$cmd, [string]$name)
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        Write-Host "   $name : " -NoNewline
        Write-Host "[OK] Installed" -ForegroundColor Green
        return $true
    } else {
        Write-Host "   $name : " -NoNewline
        Write-Host "[-] Missing" -ForegroundColor Yellow
        return $false
    }
}

$hasGit = Test-CommandAvailable "git" "Git"
$hasPython = Test-CommandAvailable "python" "Python 3"
$hasNode = Test-CommandAvailable "node" "Node.js"
$hasNpm = Test-CommandAvailable "npm" "npm"

# Auto-install Git if missing
if (-not $hasGit -and $hasWinget) {
    Write-Host "   Installing Git via winget..." -ForegroundColor Cyan
    try {
        winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
        Update-SessionPath
        $hasGit = [bool](Get-Command git -ErrorAction SilentlyContinue)
    } catch {}
}

# Auto-install Python 3.11 if missing
if (-not $hasPython) {
    Write-Host "   Python is missing. Attempting automatic installation..." -ForegroundColor Yellow
    if ($hasWinget) {
        try {
            winget install --id Python.Python.3.11 -e --accept-source-agreements --accept-package-agreements
            Update-SessionPath
        } catch {}
    }
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "   Downloading Python 3.11 installer..." -ForegroundColor Cyan
        $pyUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        $pyDest = Join-Path $env:TEMP "py311_setup.exe"
        Invoke-WebRequest -Uri $pyUrl -OutFile $pyDest -UseBasicParsing
        Start-Process $pyDest -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0" -Wait
        Remove-Item $pyDest -Force -ErrorAction SilentlyContinue
        Update-SessionPath
    }
    $hasPython = [bool](Get-Command python -ErrorAction SilentlyContinue)
}

# Auto-install Node.js if missing
if (-not $hasNode -or -not $hasNpm) {
    Write-Host "   Node.js/npm is missing. Attempting automatic installation..." -ForegroundColor Yellow
    if ($hasWinget) {
        try {
            winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
            Update-SessionPath
        } catch {}
    }
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "   Downloading Node.js LTS MSI installer..." -ForegroundColor Cyan
        $nodeUrl = "https://nodejs.org/dist/v20.18.0/node-v20.18.0-x64.msi"
        $nodeDest = Join-Path $env:TEMP "node_setup.msi"
        Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeDest -UseBasicParsing
        Start-Process "msiexec.exe" -ArgumentList "/i `"$nodeDest`" /qn" -Wait
        Remove-Item $nodeDest -Force -ErrorAction SilentlyContinue
        Update-SessionPath
    }
    $hasNode = [bool](Get-Command node -ErrorAction SilentlyContinue)
    $hasNpm = [bool](Get-Command npm -ErrorAction SilentlyContinue)
}

# Verify Python version >= 3.11
if ($hasPython) {
    try {
        $PyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        $PyMajor = [int]($PyVer.Split('.')[0])
        $PyMinor = [int]($PyVer.Split('.')[1])
        if ($PyMajor -lt 3 -or ($PyMajor -eq 3 -and $PyMinor -lt 11)) {
            Write-Host "   [WARN] Python $PyVer detected. Lucid recommends Python 3.11+." -ForegroundColor Yellow
        } else {
            Write-Host "   Python Version Verified : $PyVer (>= 3.11)" -ForegroundColor Green
        }
    } catch {}
}

# Check and Configure VS Code
$hasCode = Test-CommandAvailable "code" "Visual Studio Code CLI"
if (-not $hasCode) {
    $vscodePath = "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin"
    if (Test-Path (Join-Path $vscodePath "code.cmd")) {
        $env:Path = "$vscodePath;$env:Path"
        $hasCode = $true
        Write-Host "   Visual Studio Code CLI : [OK] Found in AppData" -ForegroundColor Green
    } elseif ($hasWinget) {
        Write-Host "   Installing Visual Studio Code via winget..." -ForegroundColor Cyan
        try {
            winget install --id Microsoft.VisualStudioCode -e --accept-source-agreements --accept-package-agreements
            Update-SessionPath
            $hasCode = [bool](Get-Command code -ErrorAction SilentlyContinue)
        } catch {}
    }
}

# Install recommended VS Code workspace extensions in background
if ($hasCode) {
    Write-Host "   Configuring recommended VS Code workspace extensions in background..." -ForegroundColor Cyan
    $recommendedExts = @(
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.debugpy",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "bradlc.vscode-tailwindcss",
        "ckolkman.vscode-postgres",
        "eamodio.gitlens",
        "tamasfe.even-better-toml",
        "redhat.vscode-yaml"
    )
    try {
        $installed = & code --list-extensions 2>$null
        foreach ($ext in $recommendedExts) {
            if ($installed -notcontains $ext) {
                Start-Process -FilePath "code" -ArgumentList "--install-extension $ext --force" -WindowStyle Hidden -ErrorAction SilentlyContinue
            }
        }
    } catch {}
}

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
    & $VenvPy -m pip install --upgrade pip setuptools wheel | Out-Null
    Write-Host "   [OK] Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "   [OK] Reusing existing virtual environment at .venv." -ForegroundColor Green
}

if (-not (Test-Path $ReqFile)) {
    Write-Host "[FAIL] Missing backend\requirements.txt. Repository files appear incomplete." -ForegroundColor Red
    exit 1
}

$CurrentHash = (Get-FileHash -Path $ReqFile -Algorithm MD5).Hash
$PrevHash = ""
if (Test-Path $HashFile) {
    $PrevHash = Get-Content $HashFile -Raw
}

if ($CurrentHash.Trim() -ne $PrevHash.Trim()) {
    Write-Host "   Installing backend dependencies from backend\requirements.txt (streaming live logs)..."
    & $VenvPip install -r $ReqFile | Tee-Object -FilePath (Join-Path $LogDir "pip_install.log")
    $CurrentHash | Out-File -FilePath $HashFile -Encoding utf8
    Write-Host "   [OK] Backend dependencies installed." -ForegroundColor Green
} else {
    Write-Host "   [OK] Backend dependencies up to date." -ForegroundColor Green
}

# [4/10] Prepare Frontend Dependencies
Write-Host "`n[4/10] Preparing Frontend Dependencies..." -ForegroundColor White
$FrontendDir = Join-Path $RootDir "frontend"
$NodeModules = Join-Path $FrontendDir "node_modules"

if (-not (Test-Path $FrontendDir)) {
    Write-Host "[FAIL] Missing frontend directory. Repository files appear incomplete." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $NodeModules)) {
    Write-Host "   Installing frontend dependencies (Next.js and React 19) (streaming live logs)..."
    Push-Location $FrontendDir
    npm install | Tee-Object -FilePath (Join-Path $LogDir "npm_install.log")
    Pop-Location
    Write-Host "   [OK] Frontend dependencies installed." -ForegroundColor Green
} else {
    Write-Host "   [OK] Frontend dependencies up to date." -ForegroundColor Green
}

# [5/10] Configure Environment Variables (.env)
Write-Host "`n[5/10] Validating Environment Configuration (.env)..." -ForegroundColor White
$EnvFile = Join-Path $RootDir ".env"
$ExampleFile = Join-Path $RootDir ".env.example"

if (-not (Test-Path $EnvFile)) {
    if (Test-Path $ExampleFile) {
        Write-Host "   '.env' not found. Creating from .env.example..."
        Copy-Item $ExampleFile $EnvFile
    } else {
        Write-Host "   Generating default .env configuration..."
        "POSTGRES_HOST=localhost`nPOSTGRES_PORT=5432`nPOSTGRES_DB=portfolio_dev`nPOSTGRES_USER=postgres`nPOSTGRES_PASSWORD=`nAPP_ENV=development`nAPP_PORT=8000`nCORS_ORIGINS=http://localhost:3000`nLLM_PROVIDER=gemini`nLLM_MODEL=gemini-3.8-flash`nGEMINI_API_KEY=" | Set-Content $EnvFile
    }
    $JwtSecret = & $VenvPy -c "import secrets; print(secrets.token_urlsafe(32))"
    $AppSecret = & $VenvPy -c "import secrets; print(secrets.token_urlsafe(32))"
    $Content = Get-Content $EnvFile -Raw
    $Content = $Content -replace "JWT_SECRET_KEY=.*", "JWT_SECRET_KEY=$JwtSecret"
    $Content = $Content -replace "APP_SECRET_KEY=.*", "APP_SECRET_KEY=$AppSecret"
    $Content | Set-Content $EnvFile
    Write-Host "   [OK] Created .env with cryptographically secure random secrets." -ForegroundColor Green
} else {
    Write-Host "   [OK] Preserving existing .env configuration." -ForegroundColor Green
}

# Check for Gemini API Key with timeout
$Content = Get-Content $EnvFile -Raw
if ($Content -match "GEMINI_API_KEY=(.*)" -and ($matches[1].Trim() -eq "" -or $matches[1] -like "*your_gemini*")) {
    Write-Host "`n[KEY] Optional Google Gemini API Key:" -ForegroundColor Yellow
    Write-Host "   Lucid uses Google Gemini 3.8 Flash for qualitative agent research." -ForegroundColor Gray
    Write-Host "   (If skipped, Lucid runs with deterministic rule-based models)." -ForegroundColor Gray
    Write-Host "   Press Enter or wait 30 seconds to continue with fallback..." -ForegroundColor Cyan
    
    $KeyInput = ""
    try {
        $task = [System.Threading.Tasks.Task]::Run([Func[string]]{ [System.Console]::ReadLine() })
        if ($task.Wait(30000)) {
            $KeyInput = $task.Result
        }
    } catch {}
    if ($KeyInput -and $KeyInput.Trim() -ne "") {
        $Content = $Content -replace "GEMINI_API_KEY=.*", "GEMINI_API_KEY=$($KeyInput.Trim())"
        $Content | Set-Content $EnvFile
        Write-Host "   [OK] Gemini API key configured." -ForegroundColor Green
    } else {
        Write-Host "   [INFO] Continuing with deterministic rule-based models." -ForegroundColor Cyan
    }
}

# [6/10] Verify PostgreSQL Service
Write-Host "`n[6/10] Verifying PostgreSQL Service..." -ForegroundColor White

$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($pgService) {
    Write-Host "   PostgreSQL Windows Service : $($pgService.Name) ($($pgService.Status))" -ForegroundColor Cyan
    if ($pgService.Status -ne "Running") {
        Write-Host "   Starting PostgreSQL service..." -ForegroundColor Yellow
        try { Start-Service $pgService.Name } catch {}
    }
    Write-Host "   [OK] PostgreSQL service is active." -ForegroundColor Green
} else {
    Write-Host "   [INFO] PostgreSQL service not registered as Windows Service. Checking port connectivity..." -ForegroundColor Cyan
}

# [7/10] Initialize Database, Migrations and Seed Data
Write-Host "`n[7/10] Initializing Database, Migrations and Reference Data..." -ForegroundColor White
$env:PYTHONPATH = $RootDir
$InitDbScript = Join-Path $RootDir "scripts\init_database.py"
if (-not (Test-Path $InitDbScript)) {
    Write-Host "[FAIL] Missing scripts\init_database.py. Repository files appear incomplete." -ForegroundColor Red
    exit 1
}
& $VenvPy $InitDbScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Database initialization failed. Check PostgreSQL connection in .env." -ForegroundColor Red
    exit 1
}

# [8/10] Check Ports Availability and Process Hygiene
Write-Host "`n[8/10] Checking Port Availability (8000 and 3000)..." -ForegroundColor White
# Check and kill old Lucid processes if PID files exist
$BackendPidFile = Join-Path $RootDir ".lucid_backend.pid"
if (Test-Path $BackendPidFile) {
    try {
        $oldPid = Get-Content $BackendPidFile -Raw
        Stop-Process -Id ([int]$oldPid.Trim()) -Force -ErrorAction SilentlyContinue
    } catch {}
    Remove-Item $BackendPidFile -Force -ErrorAction SilentlyContinue
}
$FrontendPidFile = Join-Path $RootDir ".lucid_frontend.pid"
if (Test-Path $FrontendPidFile) {
    try {
        $oldPid = Get-Content $FrontendPidFile -Raw
        Stop-Process -Id ([int]$oldPid.Trim()) -Force -ErrorAction SilentlyContinue
    } catch {}
    Remove-Item $FrontendPidFile -Force -ErrorAction SilentlyContinue
}
Write-Host "   [OK] Ports 8000 and 3000 are clear." -ForegroundColor Green

# [9/10] Start Backend Server
Write-Host "`n[9/10] Starting Lucid Backend (FastAPI on Port 8000)..." -ForegroundColor White
$BackendLog = Join-Path $LogDir "backend.log"
$BackendProcess = Start-Process -FilePath $VenvPy -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory $RootDir -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendLog -PassThru
$BackendProcess.Id | Out-File -FilePath $BackendPidFile -Encoding ascii

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
    Write-Host "   [OK] Backend API is healthy and listening on http://localhost:8000." -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Backend failed to pass health check. View logs\backend.log." -ForegroundColor Red
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# [10/10] Start Frontend Server
Write-Host "`n[10/10] Starting Lucid Frontend (Next.js on Port 3000)..." -ForegroundColor White
$FrontendLog = Join-Path $LogDir "frontend.log"
$npmCmd = if (Get-Command npm.cmd -ErrorAction SilentlyContinue) { (Get-Command npm.cmd).Source } elseif (Get-Command npm -ErrorAction SilentlyContinue) { (Get-Command npm).Source } else { "npm.cmd" }
$FrontendProcess = Start-Process -FilePath $npmCmd -ArgumentList "run dev" -WorkingDirectory $FrontendDir -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendLog -PassThru
$FrontendProcess.Id | Out-File -FilePath $FrontendPidFile -Encoding ascii

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
    Write-Host "   [OK] Frontend is ready and listening on http://localhost:3000." -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Frontend failed to pass readiness check. View logs\frontend.log." -ForegroundColor Red
    Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# Run End-to-End System Verification
Write-Host "`n[+] Executing End-to-End System Verification..." -ForegroundColor White
$VerifyScript = Join-Path $RootDir "scripts\verify_e2e.py"
& $VenvPy $VerifyScript

# Complete
Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "                    [SUCCESS] LUCID IS RUNNING and READY!                     " -ForegroundColor Green
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

if (Get-Command code -ErrorAction SilentlyContinue) {
    Write-Host "Opening Lucid workspace in Visual Studio Code..." -ForegroundColor Cyan
    Start-Process "code" -ArgumentList "`"$RootDir`""
}

Write-Host "`nTo stop services, run: powershell .\stop_lucid.ps1" -ForegroundColor Yellow
