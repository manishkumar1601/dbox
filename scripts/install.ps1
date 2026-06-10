<#
.SYNOPSIS
    PHPBox installer (Windows).

.DESCRIPTION
    Installs PHPBox so the `phpbox` command works anywhere on your system.
    The install is NON-editable (the package + templates are copied into an
    isolated location), so you can safely delete this cloned repository
    afterward.

    Missing prerequisites are installed automatically via winget:
      * Python 3.12+  (required to run the PHPBox CLI)
      * Docker Desktop (required only when you `phpbox start` a project)

.PARAMETER Pip
    Install PHPBox via `pip install --user` instead of pipx.

.PARAMETER SkipDeps
    Do not attempt to install Python / Docker; only install PHPBox.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -SkipDeps
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Pip
#>
param(
    [switch]$Pip,
    [switch]$SkipDeps
)

# Continue (not Stop): native tools like pip/winget write progress to stderr,
# which PowerShell would otherwise treat as terminating errors. We check exit
# codes ($LASTEXITCODE) explicitly instead.
$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot

function Test-Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

function Update-PathFromRegistry {
    # Pick up PATH changes made by an installer in the current session.
    $machine = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = (@($machine, $user) | Where-Object { $_ }) -join ';'
}

function Get-Python {
    # Return the name of a Python >= 3.12 on PATH, or $null.
    foreach ($c in @("python", "python3", "py")) {
        if (Test-Have $c) {
            $ok = & $c -c "import sys;print(1 if sys.version_info[:2]>=(3,12) else 0)" 2>$null
            if ($ok -eq "1") { return $c }
        }
    }
    return $null
}

Write-Host "Installing PHPBox from: $RepoRoot" -ForegroundColor Cyan

# === 1. Ensure Python (needed to install + run PHPBox) ===================
$py = Get-Python
if (-not $py) {
    if ($SkipDeps) {
        Write-Host "Python 3.12+ not found and -SkipDeps was given." -ForegroundColor Red
        Write-Host "Install it from https://www.python.org/downloads/ (tick 'Add Python to PATH')."
        exit 1
    }
    if (Test-Have winget) {
        Write-Host "Python 3.12+ not found - installing via winget..." -ForegroundColor Cyan
        winget install -e --id Python.Python.3.12 --scope user `
            --accept-package-agreements --accept-source-agreements
        Update-PathFromRegistry
        $py = Get-Python
    }
    if (-not $py) {
        Write-Host "Could not install Python automatically." -ForegroundColor Red
        Write-Host "Install it from https://www.python.org/downloads/ (tick 'Add Python to PATH'),"
        Write-Host "open a NEW terminal, and re-run this script."
        exit 1
    }
}
$ver = & $py -c "import sys;print('%d.%d'%sys.version_info[:2])"
Write-Host "Using $py (Python $ver)" -ForegroundColor Green

# === 2. Install PHPBox ===================================================
if ($Pip) {
    Write-Host "Installing PHPBox with pip (--user)..." -ForegroundColor Cyan
    & $py -m pip install --user --upgrade "$RepoRoot"
    $hint = "Make sure your Python user Scripts directory is on your PATH."
}
else {
    # Installing pipx is idempotent (fast no-op if present) — avoids fragile
    # "is it installed?" probing that breaks under strict error handling.
    Write-Host "Ensuring pipx is available..." -ForegroundColor Cyan
    & $py -m pip install --user --upgrade pipx
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Could not install pipx. Try the pip method:  scripts\install.ps1 -Pip" -ForegroundColor Red
        exit 1
    }
    & $py -m pipx ensurepath | Out-Null
    Write-Host "Installing PHPBox with pipx..." -ForegroundColor Cyan
    & $py -m pipx install --force "$RepoRoot"
    $hint = "pipx put 'phpbox' on your PATH."
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "PHPBox install failed (exit $LASTEXITCODE)." -ForegroundColor Red
    exit 1
}

# === 3. Ensure Docker (needed only when you run a project) ===============
$dockerNote = ""
if (Test-Have docker) {
    docker info *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is installed and running." -ForegroundColor Green
    }
    else {
        Write-Host "Docker is installed but not running - start Docker Desktop before 'phpbox start'." -ForegroundColor Yellow
    }
}
elseif ($SkipDeps) {
    $dockerNote = "Docker not found. Install Docker Desktop before running projects: https://www.docker.com/products/docker-desktop/"
}
elseif (Test-Have winget) {
    Write-Host "Docker not found - installing Docker Desktop via winget..." -ForegroundColor Cyan
    winget install -e --id Docker.DockerDesktop `
        --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
        $dockerNote = "Docker Desktop was installed. REBOOT, then launch Docker Desktop once (accept the license) before 'phpbox start'."
    }
    else {
        $dockerNote = "Docker Desktop install did not complete (it may need admin rights). Install it from https://www.docker.com/products/docker-desktop/"
    }
}
else {
    $dockerNote = "Docker not found and winget is unavailable. Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
}

# === Done ================================================================
Write-Host ""
Write-Host "PHPBox installed." -ForegroundColor Green
Write-Host $hint
if ($dockerNote) { Write-Host $dockerNote -ForegroundColor Yellow }
Write-Host "Open a NEW terminal, then run:  phpbox --help"
Write-Host "You can now safely delete this cloned repository."
