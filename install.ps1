# Claude Code Installer for Windows
# Usage: irm https://claude.ai/install.ps1 | iex

param(
    [string]$Version = "latest"
)

$ErrorActionPreference = "Stop"

function Write-Status([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Success([string]$Message) {
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Failure([string]$Message) {
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Get-NodeVersion {
    try {
        $ver = & node --version 2>$null
        return $ver
    } catch {
        return $null
    }
}

function Get-NpmVersion {
    try {
        $ver = & npm --version 2>$null
        return $ver
    } catch {
        return $null
    }
}

function Test-MinNodeVersion([string]$VersionString) {
    # Claude Code requires Node.js >= 18
    $min = 18
    if ($VersionString -match "v(\d+)\.") {
        return [int]$Matches[1] -ge $min
    }
    return $false
}

function Install-NodeViaWinget {
    Write-Status "Installing Node.js via winget..."
    try {
        winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements | Out-Null
        # Refresh PATH so node/npm are available in this session
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH", "User")
        return $true
    } catch {
        return $false
    }
}

function Install-NodeViaNvmWindows {
    Write-Status "Installing nvm-windows and Node.js LTS..."
    try {
        $nvmInstaller = Join-Path $env:TEMP "nvm-setup.exe"
        $nvmRelease = "https://github.com/coreybutler/nvm-windows/releases/latest/download/nvm-setup.exe"
        Invoke-WebRequest -Uri $nvmRelease -OutFile $nvmInstaller -UseBasicParsing
        Start-Process -FilePath $nvmInstaller -Args "/silent" -Wait
        Remove-Item $nvmInstaller -Force -ErrorAction SilentlyContinue

        $env:NVM_HOME = "$env:APPDATA\nvm"
        $env:NVM_SYMLINK = "$env:ProgramFiles\nodejs"
        $env:PATH = "$env:NVM_HOME;$env:NVM_SYMLINK;$env:PATH"

        & nvm install lts 2>$null
        & nvm use lts 2>$null
        return $true
    } catch {
        return $false
    }
}

function Install-ClaudeCode([string]$Version) {
    $package = if ($Version -eq "latest") { "@anthropic-ai/claude-code" } else { "@anthropic-ai/claude-code@$Version" }
    Write-Status "Installing $package..."
    & npm install -g $package
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed with exit code $LASTEXITCODE"
    }
}

# ── Main ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  Claude Code Installer" -ForegroundColor Magenta
Write-Host "  https://claude.ai" -ForegroundColor DarkGray
Write-Host ""

# 1. Check for Node.js
Write-Status "Checking for Node.js..."
$nodeVersion = Get-NodeVersion

if ($null -eq $nodeVersion) {
    Write-Host "  Node.js not found. Attempting automatic installation..." -ForegroundColor Yellow

    # Try winget first (available on Windows 10/11)
    $wingetAvailable = $null -ne (Get-Command winget -ErrorAction SilentlyContinue)
    $installed = $false

    if ($wingetAvailable) {
        $installed = Install-NodeViaWinget
    }

    if (-not $installed) {
        $installed = Install-NodeViaNvmWindows
    }

    if (-not $installed) {
        Write-Failure "Could not install Node.js automatically."
        Write-Host ""
        Write-Host "  Please install Node.js >= 18 manually from https://nodejs.org" -ForegroundColor Yellow
        Write-Host "  Then re-run this installer." -ForegroundColor Yellow
        exit 1
    }

    $nodeVersion = Get-NodeVersion
}

if ($null -eq $nodeVersion) {
    Write-Failure "Node.js installation succeeded but 'node' is not in PATH."
    Write-Host "  Please open a new terminal and re-run this installer." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-MinNodeVersion $nodeVersion)) {
    Write-Failure "Node.js $nodeVersion is installed but Claude Code requires >= v18."
    Write-Host "  Please upgrade Node.js from https://nodejs.org and re-run this installer." -ForegroundColor Yellow
    exit 1
}

Write-Success "Node.js $nodeVersion"

# 2. Check for npm
Write-Status "Checking for npm..."
$npmVersion = Get-NpmVersion
if ($null -eq $npmVersion) {
    Write-Failure "npm not found. Please reinstall Node.js from https://nodejs.org"
    exit 1
}
Write-Success "npm $npmVersion"

# 3. Install Claude Code
try {
    Install-ClaudeCode $Version
} catch {
    Write-Failure "Installation failed: $_"
    Write-Host ""
    Write-Host "  If you see a permission error, try running this script in an" -ForegroundColor Yellow
    Write-Host "  elevated (Administrator) PowerShell session." -ForegroundColor Yellow
    exit 1
}

# 4. Verify
Write-Status "Verifying installation..."
try {
    $claudeVersion = & claude --version 2>$null
    Write-Success "Claude Code $claudeVersion installed successfully!"
} catch {
    Write-Host "  Claude Code was installed but 'claude' was not found in PATH." -ForegroundColor Yellow
    Write-Host "  You may need to open a new terminal window." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Get started by running: claude" -ForegroundColor Magenta
Write-Host ""
