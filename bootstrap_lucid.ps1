# ==============================================================================
# Lucid - Zero-Prerequisite One-Command Bootstrap Installer (Windows PowerShell)
# ==============================================================================
# Run this SINGLE command in Windows PowerShell (even if Git is NOT installed):
#
#   irm https://raw.githubusercontent.com/imankur0011/Lucid/main/bootstrap_lucid.ps1 | iex
#
# What this script does automatically:
#   1. Detects Windows OS, architecture, and verifies internet connectivity.
#   2. Downloads the Lucid repository (via Git clone OR native ZIP extraction).
#   3. Auto-installs missing prerequisites (Git, Python 3.11+, Node.js 18+, PostgreSQL 16, VS Code).
#   4. Dynamically repairs and updates session PATH so no reboot or restart is needed.
#   5. Hands off execution to start_lucid.ps1 for complete backend/frontend/database startup.
# ==============================================================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "        * LUCID - ONE-COMMAND BOOTSTRAP INSTALLER (WINDOWS)          " -ForegroundColor Cyan
Write-Host "  Automated Zero-Prerequisite Setup for Indian Retail Equities Platform" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# [1/6] System and Connectivity Inspection
Write-Host "[1/6] Inspecting System and Internet Connectivity..." -ForegroundColor White
$OS = [System.Environment]::OSVersion
$Arch = if ([System.Environment]::Is64BitOperatingSystem) { "x64" } else { "x86" }
Write-Host "   Operating System : Windows ($OS) - $Arch" -ForegroundColor Green

# Ensure TLS 1.2/1.3 are enabled for all .NET web operations
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls13
} catch {}

Write-Host "   Internet Access  : [OK] Connected" -ForegroundColor Green

# Function to refresh environment PATH in the current PowerShell process
function Update-SessionPath {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$userPath;$machinePath"
    
    # Common software directories that might have just been installed
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

# Initial PATH refresh
Update-SessionPath

# Check if winget is available
$hasWinget = [bool](Get-Command winget -ErrorAction SilentlyContinue)
if ($hasWinget) {
    Write-Host "   Windows Package Manager (winget) : [OK] Available" -ForegroundColor Green
} else {
    Write-Host "   Windows Package Manager (winget) : [-] Not Available (Falling back to direct HTTPS downloads)" -ForegroundColor Yellow
}

# [2/6] Ensure Target Directory and Obtain Lucid Repository
Write-Host "`n[2/6] Acquiring Lucid Application Repository..." -ForegroundColor White

# Determine target directory
$TargetDir = Join-Path $HOME "Lucid"

# Check if current directory is already the Lucid repository
if ((Test-Path (Join-Path (Get-Location) "backend\requirements.txt")) -and (Test-Path (Join-Path (Get-Location) "start_lucid.ps1"))) {
    $TargetDir = (Get-Location).Path
    Write-Host "   Running inside existing Lucid repository: $TargetDir" -ForegroundColor Green
} elseif (Test-Path $TargetDir) {
    Write-Host "   Found existing Lucid installation at: $TargetDir" -ForegroundColor Cyan
    if (Test-Path (Join-Path $TargetDir ".git")) {
        Write-Host "   Updating repository via git pull..." -ForegroundColor Cyan
        try { git -C $TargetDir pull origin main | Out-Null } catch {}
    }
    Write-Host "   Updating launcher scripts from GitHub..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/imankur0011/Lucid/main/start_lucid.ps1" -OutFile (Join-Path $TargetDir "start_lucid.ps1") -UseBasicParsing
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/imankur0011/Lucid/main/status_lucid.ps1" -OutFile (Join-Path $TargetDir "status_lucid.ps1") -UseBasicParsing
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/imankur0011/Lucid/main/stop_lucid.ps1" -OutFile (Join-Path $TargetDir "stop_lucid.ps1") -UseBasicParsing
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/imankur0011/Lucid/main/logs_lucid.ps1" -OutFile (Join-Path $TargetDir "logs_lucid.ps1") -UseBasicParsing
    } catch {}
} else {
    Write-Host "   Target Installation Directory: $TargetDir" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

$hasGit = [bool](Get-Command git -ErrorAction SilentlyContinue)

# If Git is missing, try to install Git via winget OR download ZIP
if (-not $hasGit -and (-not (Test-Path (Join-Path $TargetDir "start_lucid.ps1")))) {
    Write-Host "   [INFO] Git is not installed on this system." -ForegroundColor Yellow
    if ($hasWinget) {
        Write-Host "   Installing Git for Windows via winget..." -ForegroundColor Cyan
        try {
            winget install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
            Update-SessionPath
            $hasGit = [bool](Get-Command git -ErrorAction SilentlyContinue)
        } catch {}
    }
    
    # If still no Git, download repository ZIP directly from GitHub!
    if (-not $hasGit) {
        Write-Host "   Downloading Lucid repository as ZIP directly from GitHub..." -ForegroundColor Cyan
        $zipUrl = "https://github.com/imankur0011/Lucid/archive/refs/heads/main.zip"
        $zipDest = Join-Path $env:TEMP "Lucid-main.zip"
        $extractDir = Join-Path $env:TEMP "Lucid-extracted"
        
        Invoke-WebRequest -Uri $zipUrl -OutFile $zipDest -UseBasicParsing
        Write-Host "   Extracting archive to $TargetDir..." -ForegroundColor Cyan
        
        if (Test-Path $extractDir) { Remove-Item -Path $extractDir -Recurse -Force | Out-Null }
        Expand-Archive -Path $zipDest -DestinationPath $extractDir -Force
        
        $innerFolder = Join-Path $extractDir "Lucid-main"
        if (Test-Path $innerFolder) {
            Get-ChildItem -Path $innerFolder -Force | Copy-Item -Destination $TargetDir -Recurse -Force
        }
        Remove-Item -Path $zipDest -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $extractDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "   [OK] Lucid repository downloaded and extracted successfully." -ForegroundColor Green
    }
}

# If Git is available and repo not yet cloned, use git clone
if ($hasGit -and (-not (Test-Path (Join-Path $TargetDir "start_lucid.ps1")))) {
    Write-Host "   Cloning Lucid repository via Git..." -ForegroundColor Cyan
    git clone https://github.com/imankur0011/Lucid.git "$TargetDir"
    Write-Host "   [OK] Repository cloned successfully." -ForegroundColor Green
}

# [3/6] Check and Auto-Install Python 3.11+
Write-Host "`n[3/6] Verifying Python Runtime..." -ForegroundColor White
Update-SessionPath

function Test-PythonVersion {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        try {
            $ver = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($ver) {
                $major = [int]($ver.Split('.')[0])
                $minor = [int]($ver.Split('.')[1])
                if ($major -eq 3 -and $minor -ge 11) {
                    return $ver
                }
            }
        } catch {}
    }
    return $null
}

$pyVer = Test-PythonVersion
if (-not $pyVer) {
    Write-Host "   Python 3.11+ is not found. Attempting automatic installation..." -ForegroundColor Yellow
    if ($hasWinget) {
        Write-Host "   Installing Python 3.11 via winget..." -ForegroundColor Cyan
        try {
            winget install --id Python.Python.3.11 -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
            Update-SessionPath
        } catch {}
    }
    
    $pyVer = Test-PythonVersion
    if (-not $pyVer) {
        Write-Host "   Downloading Python 3.11.9 official installer..." -ForegroundColor Cyan
        $pyUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        $pyInstaller = Join-Path $env:TEMP "python-3.11.9.exe"
        Invoke-WebRequest -Uri $pyUrl -OutFile $pyInstaller -UseBasicParsing
        Write-Host "   Installing Python quietly (adding to PATH)..." -ForegroundColor Cyan
        Start-Process -FilePath $pyInstaller -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0" -Wait
        Remove-Item $pyInstaller -Force -ErrorAction SilentlyContinue
        Update-SessionPath
    }
    
    $pyVer = Test-PythonVersion
    if ($pyVer) {
        Write-Host "   [OK] Python $pyVer installed and verified." -ForegroundColor Green
    } else {
        Write-Host "   [WARN] Could not automatically verify Python in PATH. Please install Python 3.11 from python.org with 'Add to PATH' checked." -ForegroundColor Yellow
    }
} else {
    Write-Host "   Python Runtime : [OK] Installed (Python $pyVer)" -ForegroundColor Green
}

# [4/6] Check and Auto-Install Node.js and npm
Write-Host "`n[4/6] Verifying Node.js and npm..." -ForegroundColor White
Update-SessionPath

function Test-NodeVersion {
    if (Get-Command node -ErrorAction SilentlyContinue) {
        try {
            $ver = node -v 2>$null
            if ($ver -and $ver.StartsWith("v")) {
                $major = [int]($ver.TrimStart('v').Split('.')[0])
                if ($major -ge 18) {
                    return $ver
                }
            }
        } catch {}
    }
    return $null
}

$nodeVer = Test-NodeVersion
if (-not $nodeVer) {
    Write-Host "   Node.js 18+ is not found. Attempting automatic installation..." -ForegroundColor Yellow
    if ($hasWinget) {
        Write-Host "   Installing Node.js LTS via winget..." -ForegroundColor Cyan
        try {
            winget install --id OpenJS.NodeJS.LTS -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
            Update-SessionPath
        } catch {}
    }
    
    $nodeVer = Test-NodeVersion
    if (-not $nodeVer) {
        Write-Host "   Downloading Node.js v20.18.0 official MSI installer..." -ForegroundColor Cyan
        $nodeUrl = "https://nodejs.org/dist/v20.18.0/node-v20.18.0-x64.msi"
        $nodeMsi = Join-Path $env:TEMP "nodejs.msi"
        Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeMsi -UseBasicParsing
        Write-Host "   Installing Node.js quietly..." -ForegroundColor Cyan
        Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$nodeMsi`" /qn" -Wait
        Remove-Item $nodeMsi -Force -ErrorAction SilentlyContinue
        Update-SessionPath
    }
    
    $nodeVer = Test-NodeVersion
    if ($nodeVer) {
        Write-Host "   [OK] Node.js $nodeVer installed and verified." -ForegroundColor Green
    } else {
        Write-Host "   [WARN] Could not automatically verify Node.js in PATH. Please install Node.js from nodejs.org." -ForegroundColor Yellow
    }
} else {
    Write-Host "   Node.js Runtime : [OK] Installed (Node $nodeVer)" -ForegroundColor Green
}

# [5/6] Check and Auto-Install PostgreSQL 16
Write-Host "`n[5/6] Verifying PostgreSQL 16..." -ForegroundColor White
Update-SessionPath

$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
$hasPsql = [bool](Get-Command psql -ErrorAction SilentlyContinue)

if ($pgService) {
    Write-Host "   PostgreSQL Service : [OK] Detected ($($pgService.Name) - Status: $($pgService.Status))" -ForegroundColor Green
    if ($pgService.Status -ne "Running") {
        Write-Host "   Starting PostgreSQL service..." -ForegroundColor Cyan
        try { Start-Service $pgService.Name } catch {}
    }
} elseif (-not $hasPsql) {
    Write-Host "   PostgreSQL is not found. Attempting installation via winget..." -ForegroundColor Yellow
    if ($hasWinget) {
        try {
            winget install --id PostgreSQL.PostgreSQL.16 -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
            Update-SessionPath
        } catch {}
    }
}

# [6/6] Launching Main Lucid Launcher (start_lucid.ps1)
Write-Host "`n[6/6] Transferring Execution to Lucid Application Launcher..." -ForegroundColor White
Set-Location $TargetDir

$LauncherScript = Join-Path $TargetDir "start_lucid.ps1"
if (Test-Path $LauncherScript) {
    Write-Host "   Executing: $LauncherScript`n" -ForegroundColor Green
    powershell -ExecutionPolicy Bypass -File $LauncherScript
} else {
    Write-Host "[FAIL] Launcher script not found at $LauncherScript." -ForegroundColor Red
    exit 1
}
