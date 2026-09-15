# PowerBot MSIX Build Script
# Requires Windows 10 SDK makeappx.exe and signtool.exe in PATH

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistPath = Join-Path $ProjectRoot "..\dist\PowerBot.exe"
$PackageRoot = Join-Path $ProjectRoot "Package"

if (-not (Test-Path $DistPath)) {
    Write-Error "PowerBot.exe not found at $DistPath. Build it first with PyInstaller."
    exit 1
}

# Clean and prepare package folder
if (Test-Path $PackageRoot) { Remove-Item $PackageRoot -Recurse -Force }
New-Item -ItemType Directory -Path $PackageRoot | Out-Null
New-Item -ItemType Directory -Path (Join-Path $PackageRoot "Assets") | Out-Null

# Copy app files
Copy-Item $DistPath (Join-Path $PackageRoot "PowerBot.exe")
Copy-Item (Join-Path $ProjectRoot "AppxManifest.xml") $PackageRoot

# Placeholder assets - replace with real 44x44,150x150, etc PNGs before submission
# For now create empty files to keep structure valid
@("StoreLogo.png","Square150x150Logo.png","Square44x44Logo.png","Wide310x150Logo.png","SmallTile.png","MediumTile.png","LargeTile.png") | ForEach-Object {
    $p = Join-Path $PackageRoot "Assets\$_"
    if (-not (Test-Path $p)) { New-Item -ItemType File -Path $p -Force | Out-Null }
}

Write-Host "Package folder ready at $PackageRoot"
Write-Host "Next steps:"
Write-Host "1. Replace placeholder PNGs in Assets with real 44x44,150x150,310x150 logos"
Write-Host "2. Sign the package:"
Write-Host "   signtool sign /fd SHA256 /a /n 'Beebus Builds' /t http://timestamp.digicert.com $PackageRoot\PowerBot.msix"
Write-Host "3. Create MSIX bundle with makeappx.exe:"
Write-Host "   makeappx pack /d $PackageRoot /p PowerBot.msix"

# Optional: create a basic MSIX with makeappx if available
if (Get-Command makeappx -ErrorAction SilentlyContinue) {
    makeappx pack /d $PackageRoot /p (Join-Path $ProjectRoot "PowerBot.msix")
    Write-Host "MSIX created at $(Join-Path $ProjectRoot "PowerBot.msix")"
} else {
    Write-Warning "makeappx.exe not found. Install Windows 10 SDK."
}
