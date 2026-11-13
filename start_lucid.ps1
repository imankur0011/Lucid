# ==============================================================================
# Lucid - One-Command Installation and Application Launcher (Windows PowerShell)
# ==============================================================================
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\start_lucid.ps1
# ==============================================================================

$ErrorActionPreference = "Continue"

# Force UTF-8 encoding across Windows PowerShell and child Python runtimes
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
} catch {}

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
        Write-Host "   Downloading Node.js 22 LTS MSI installer..." -ForegroundColor Cyan
        $nodeUrl = "https://nodejs.org/dist/v22.14.0/node-v22.14.0-x64.msi"
        $nodeDest = Join-Path $env:TEMP "node_setup.msi"
        Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeDest -UseBasicParsing
        Start-Process "msiexec.exe" -ArgumentList "/i `"$nodeDest`" /qn" -Wait
        Remove-Item $nodeDest -Force -ErrorAction SilentlyContinue
        Update-SessionPath
    }
    $hasNode = [bool](Get-Command node -ErrorAction SilentlyContinue)
    $hasNpm = [bool](Get-Command npm -ErrorAction SilentlyContinue)
}

# Verify Node.js version >= 20.19.0 (required by eslint-visitor-keys@5+ in next.js 16)
if ($hasNode) {
    try {
        $nodeVerRaw = node --version 2>$null   # e.g. "v20.14.0"
        $nodeVer = $nodeVerRaw.TrimStart('v')
        $nodeParts = $nodeVer.Split('.')
        $nodeMajor = [int]$nodeParts[0]
        $nodeMinor = if ($nodeParts.Length -gt 1) { [int]$nodeParts[1] } else { 0 }
        $nodePatch = if ($nodeParts.Length -gt 2) { [int]$nodeParts[2] } else { 0 }

        # Need >= 20.19.0 (LTS Hydrogen min compatible with eslint-visitor-keys@5) OR >= 22.x
        $nodeOk = ($nodeMajor -gt 22) -or
                  ($nodeMajor -eq 22 -and $nodeMinor -ge 0) -or
                  ($nodeMajor -eq 20 -and (($nodeMinor -gt 19) -or ($nodeMinor -eq 19 -and $nodePatch -ge 0)))

        if (-not $nodeOk) {
            Write-Host "   [WARN] Node.js $nodeVerRaw detected. Lucid requires Node.js >=20.19.0 or >=22.x (LTS)." -ForegroundColor Yellow
            Write-Host "          Some dependencies (eslint-visitor-keys@5) may show EBADENGINE warnings." -ForegroundColor Yellow
            Write-Host "          Attempting to upgrade Node.js to v22 LTS..." -ForegroundColor Cyan
            if ($hasWinget) {
                try {
                    winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
                    Update-SessionPath
                } catch {}
            }
            if (-not (Get-Command node -ErrorAction SilentlyContinue) -or ((node --version 2>$null).TrimStart('v').Split('.')[0] -lt 22)) {
                $nodeUrl22 = "https://nodejs.org/dist/v22.14.0/node-v22.14.0-x64.msi"
                $nodeDest22 = Join-Path $env:TEMP "node22_setup.msi"
                Write-Host "   Downloading Node.js 22 LTS (v22.14.0)..." -ForegroundColor Cyan
                Invoke-WebRequest -Uri $nodeUrl22 -OutFile $nodeDest22 -UseBasicParsing
                Start-Process "msiexec.exe" -ArgumentList "/i `"$nodeDest22`" /qn" -Wait
                Remove-Item $nodeDest22 -Force -ErrorAction SilentlyContinue
                Update-SessionPath
                $nodeVerRaw = node --version 2>$null
            }
            Write-Host "   Node.js Version After Upgrade : $nodeVerRaw" -ForegroundColor Green
        } else {
            Write-Host "   Node.js Version Verified : $nodeVerRaw (>= 20.19.0)" -ForegroundColor Green
        }
    } catch {}
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
    # --no-audit skips the audit network round-trip; --no-fund suppresses funding messages.
    # On Windows, antivirus software can hold file locks causing EPERM on rmdir during install.
    # We retry once on failure which usually resolves transient lock conflicts.
    $npmInstallLog = Join-Path $LogDir "npm_install.log"
    npm install --no-audit --no-fund 2>&1 | Tee-Object -FilePath $npmInstallLog
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   [WARN] npm install had issues. Retrying with --legacy-peer-deps..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        npm install --no-audit --no-fund --legacy-peer-deps 2>&1 | Tee-Object -FilePath $npmInstallLog -Append
    }
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
        "POSTGRES_HOST=127.0.0.1`nPOSTGRES_PORT=5432`nPOSTGRES_DB=portfolio_dev`nPOSTGRES_USER=postgres`nPOSTGRES_PASSWORD=`nAPP_ENV=development`nAPP_PORT=8000`nCORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001`nLLM_PROVIDER=gemini`nLLM_MODEL=gemini-3.8-flash`nGEMINI_API_KEY=" | Set-Content $EnvFile
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
    # Check if postgres port is reachable even without a Windows service entry (portable installs)
    $pgPortOpen = $false
    foreach ($pgPort in @(5432, 5433)) {
        try {
            $testConn = New-Object System.Net.Sockets.TcpClient
            $testResult = $testConn.BeginConnect("127.0.0.1", $pgPort, $null, $null)
            $testWait = $testResult.AsyncWaitHandle.WaitOne(1000)
            if ($testWait -and $testConn.Connected) {
                $pgPortOpen = $true
                Write-Host "   [OK] PostgreSQL detected on port $pgPort (portable/custom install)." -ForegroundColor Green
            }
            $testConn.Close()
        } catch {}
        if ($pgPortOpen) { break }
    }

    if (-not $pgPortOpen) {
        Write-Host "   [WARN] PostgreSQL not found. Attempting automatic installation..." -ForegroundColor Yellow
        $pgInstalled = $false

        # Try winget first
        if ($hasWinget) {
            try {
                Write-Host "   Installing PostgreSQL 16 via winget..." -ForegroundColor Cyan
                winget install --id PostgreSQL.PostgreSQL.16 -e --accept-source-agreements --accept-package-agreements
                Update-SessionPath
                Start-Sleep -Seconds 5
                $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
                if ($pgService) {
                    try { Start-Service $pgService.Name -ErrorAction SilentlyContinue } catch {}
                    $pgInstalled = $true
                    Write-Host "   [OK] PostgreSQL 16 installed and started via winget." -ForegroundColor Green
                }
            } catch {}
        }

        # Fallback: download PostgreSQL interactive installer
        if (-not $pgInstalled) {
            Write-Host "   Downloading PostgreSQL 16 installer (this may take 2-3 minutes)..." -ForegroundColor Cyan
            $pgUrl = "https://get.enterprisedb.com/postgresql/postgresql-16.8-1-windows-x64.exe"
            $pgDest = Join-Path $env:TEMP "postgresql_setup.exe"
            try {
                Invoke-WebRequest -Uri $pgUrl -OutFile $pgDest -UseBasicParsing
                Write-Host "   Running PostgreSQL installer silently (password: LucidDevPass123!)..." -ForegroundColor Cyan
                Start-Process $pgDest -ArgumentList "--unattendedmodeui minimal --mode unattended --superpassword LucidDevPass123! --servicename postgresql-16 --servicepassword LucidDevPass123! --serverport 5432" -Wait
                Remove-Item $pgDest -Force -ErrorAction SilentlyContinue
                Update-SessionPath
                Start-Sleep -Seconds 8
                $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
                if ($pgService) {
                    try { Start-Service $pgService.Name -ErrorAction SilentlyContinue } catch {}
                    $pgInstalled = $true
                    # Persist the auto-generated password to .env
                    $envContent = Get-Content $EnvFile -Raw -ErrorAction SilentlyContinue
                    if ($envContent) {
                        $envContent = $envContent -replace "POSTGRES_PASSWORD=.*", "POSTGRES_PASSWORD=LucidDevPass123!"
                        $envContent | Set-Content $EnvFile
                    }
                    Write-Host "   [OK] PostgreSQL 16 installed via direct download." -ForegroundColor Green
                }
            } catch {
                Write-Host "   [WARN] Automatic PostgreSQL install failed: $_" -ForegroundColor Yellow
            }
        }

        if (-not $pgInstalled) {
            Write-Host "" -ForegroundColor Red
            Write-Host "   =================================================================" -ForegroundColor Red
            Write-Host "   [FAIL] PostgreSQL could not be automatically installed." -ForegroundColor Red
            Write-Host "   Please install PostgreSQL 16 manually:" -ForegroundColor Yellow
            Write-Host "     1. Visit: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
            Write-Host "     2. Install PostgreSQL 16 with default settings" -ForegroundColor Yellow
            Write-Host "     3. Set a password for the 'postgres' user" -ForegroundColor Yellow
            Write-Host "     4. Update POSTGRES_PASSWORD in the .env file" -ForegroundColor Yellow
            Write-Host "     5. Re-run: powershell -ExecutionPolicy Bypass -File .\start_lucid.ps1" -ForegroundColor Yellow
            Write-Host "   =================================================================" -ForegroundColor Red
            exit 1
        }
    }
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

# Release ports 8000 and 3000 directly from any lingering orphan processes
function Release-Port {
    param([int]$port, [string]$name)
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            $pId = $c.OwningProcess
            if ($pId -gt 0) {
                Write-Host "   Releasing port $port (PID: $pId - $name)..." -ForegroundColor Yellow
                Stop-Process -Id $pId -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {}
}
Release-Port 8000 "FastAPI Backend"
Release-Port 3000 "Next.js Frontend"

Write-Host "   [OK] Ports 8000 and 3000 are clear." -ForegroundColor Green

# [9/10] Start Backend Server
Write-Host "`n[9/10] Starting Lucid Backend (FastAPI on Port 8000)..." -ForegroundColor White
$BackendLog = Join-Path $LogDir "backend.log"
$BackendErrLog = Join-Path $LogDir "backend_err.log"

$UvicornExe = Join-Path $VenvDir "Scripts\uvicorn.exe"
if (Test-Path $UvicornExe) {
    $BackendProcess = Start-Process -FilePath $UvicornExe -ArgumentList @("backend.main:app", "--host", "0.0.0.0", "--port", "8000") -WorkingDirectory $RootDir -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendErrLog -PassThru
} else {
    $BackendProcess = Start-Process -FilePath $VenvPy -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000") -WorkingDirectory $RootDir -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendErrLog -PassThru
}

if ($BackendProcess -and $BackendProcess.Id) {
    $BackendProcess.Id | Out-File -FilePath $BackendPidFile -Encoding ascii
}

Write-Host "   Waiting for Backend API readiness (http://localhost:8000/api/health)..."
$BackendReady = $false
for ($i = 0; $i -lt 40; $i++) {
    if ($BackendProcess.HasExited) {
        Write-Host "   [FAIL] Backend process exited unexpectedly (Exit Code: $($BackendProcess.ExitCode))." -ForegroundColor Red
        break
    }
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($resp) {
            $BackendReady = $true
            break
        }
    } catch {}
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
    Write-Host "   [FAIL] Backend failed to pass health check." -ForegroundColor Red
    if (Test-Path $BackendErrLog) {
        $errContent = Get-Content $BackendErrLog -Raw -ErrorAction SilentlyContinue
        if ($errContent -and $errContent.Trim()) {
            Write-Host "`n--- Backend Error Log (logs\backend_err.log) ---" -ForegroundColor Yellow
            Write-Host $errContent.Trim() -ForegroundColor Yellow
            Write-Host "------------------------------------------------`n" -ForegroundColor Yellow
        }
    }
    if (Test-Path $BackendLog) {
        $outContent = Get-Content $BackendLog -Tail 25 -ErrorAction SilentlyContinue
        if ($outContent) {
            Write-Host "`n--- Backend Output Log (logs\backend.log) ---" -ForegroundColor Gray
            $outContent | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
            Write-Host "--------------------------------------------`n" -ForegroundColor Gray
        }
    }
    if ($BackendProcess -and -not $BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    exit 1
}

# [10/10] Start Frontend Server
Write-Host "`n[10/10] Starting Lucid Frontend (Next.js on Port 3000)..." -ForegroundColor White
$FrontendLog = Join-Path $LogDir "frontend.log"
$FrontendErrLog = Join-Path $LogDir "frontend_err.log"
$npmCmd = if (Get-Command npm.cmd -ErrorAction SilentlyContinue) { (Get-Command npm.cmd).Source } elseif (Get-Command npm -ErrorAction SilentlyContinue) { (Get-Command npm).Source } else { "npm.cmd" }
$FrontendProcess = Start-Process -FilePath $npmCmd -ArgumentList @("run", "dev") -WorkingDirectory $FrontendDir -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendErrLog -PassThru
if ($FrontendProcess -and $FrontendProcess.Id) {
    $FrontendProcess.Id | Out-File -FilePath $FrontendPidFile -Encoding ascii
}

Write-Host "   Waiting for Frontend readiness (http://localhost:3000)..."
$FrontendReady = $false
for ($i = 0; $i -lt 40; $i++) {
    if ($FrontendProcess.HasExited) {
        Write-Host "   [FAIL] Frontend process exited unexpectedly (Exit Code: $($FrontendProcess.ExitCode))." -ForegroundColor Red
        break
    }
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200 -or $resp.StatusCode -eq 304) {
            $FrontendReady = $true
            break
        }
    } catch {}
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
    Write-Host "   [FAIL] Frontend failed to pass readiness check." -ForegroundColor Red
    if (Test-Path $FrontendErrLog) {
        $fErr = Get-Content $FrontendErrLog -Raw -ErrorAction SilentlyContinue
        if ($fErr -and $fErr.Trim()) {
            Write-Host "`n--- Frontend Error Log (logs\frontend_err.log) ---" -ForegroundColor Yellow
            Write-Host $fErr.Trim() -ForegroundColor Yellow
            Write-Host "-------------------------------------------------`n" -ForegroundColor Yellow
        }
    }
    if (Test-Path $FrontendLog) {
        $fOut = Get-Content $FrontendLog -Tail 25 -ErrorAction SilentlyContinue
        if ($fOut) {
            Write-Host "`n--- Frontend Output Log (logs\frontend.log) ---" -ForegroundColor Gray
            $fOut | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
            Write-Host "---------------------------------------------`n" -ForegroundColor Gray
        }
    }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($BackendProcess -and -not $BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
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
Start-Process "http://127.0.0.1:3000"

if (Get-Command code -ErrorAction SilentlyContinue) {
    Write-Host "Opening Lucid workspace in Visual Studio Code..." -ForegroundColor Cyan
    Start-Process "code" -ArgumentList "`"$RootDir`""
}

Write-Host "`nTo stop services, run: powershell .\stop_lucid.ps1" -ForegroundColor Yellow
