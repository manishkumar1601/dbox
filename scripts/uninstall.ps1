<#
.SYNOPSIS
    DBox uninstaller (Windows).

.DESCRIPTION
    Removes the `dbox` command, whether it was installed via pipx or pip.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\uninstall.ps1
#>

$ErrorActionPreference = "SilentlyContinue"

$py = $null
foreach ($c in @("python", "python3", "py")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break }
}
if (-not $py) { $py = "python" }

$removed = $false

# Try pipx first.
$pipxList = & $py -m pipx list 2>$null
if ($pipxList -match "package dbox") {
    Write-Host "Removing pipx install..."
    & $py -m pipx uninstall dbox
    if ($LASTEXITCODE -eq 0) { $removed = $true }
}

# Fall back to pip.
if (-not $removed) {
    Write-Host "Removing pip install..."
    & $py -m pip uninstall -y dbox
}

Write-Host "DBox uninstalled." -ForegroundColor Green
Write-Host "Your projects and their .dbox/ folders are untouched."
Write-Host "Remove a project's containers with: docker compose -f <project>\.dbox\docker-compose.yml down -v"
