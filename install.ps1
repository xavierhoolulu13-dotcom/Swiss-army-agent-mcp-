# ============================================================
# 🌋 XKSH808 Ultimate Concierge — No-Click Installer (Windows)
# Run (PowerShell as user, no admin needed):
#   irm https://raw.githubusercontent.com/xavierhoolulu13-dotcom/Swiss-army-agent-mcp-/main/install.ps1 | iex
# ============================================================
$ErrorActionPreference = "Stop"

$Repo      = "https://github.com/xavierhoolulu13-dotcom/Swiss-army-agent-mcp-.git"
$InstallDir = "$env:USERPROFILE\.xksh808\mcp"
$VenvDir    = "$InstallDir\.venv"
$EnvFile    = "$InstallDir\.env"
$CfgPath    = "$env:APPDATA\Claude\claude_desktop_config.json"

function Write-Banner($msg) { Write-Host "`n🌋 XKSH808 $msg" -ForegroundColor Magenta }
function Write-Ok($msg)     { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Info($msg)   { Write-Host "  → $msg" -ForegroundColor Yellow }

Write-Banner "Ultimate Concierge — No-Click Installer"
Write-Host "  FloatForge808 · Volcano IS · SpiffyCloud OS`n"

# 1. Python check
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Error "Python 3.11+ required. Install from https://python.org and re-run." }
Write-Info "Python found: $($py.Source)"

# 2. Clone / update
if (Test-Path "$InstallDir\.git") {
    Write-Info "Updating existing install..."
    git -C $InstallDir pull --ff-only origin main 2>$null
} else {
    Write-Info "Cloning into $InstallDir"
    New-Item -ItemType Directory -Force -Path (Split-Path $InstallDir) | Out-Null
    git clone --depth=1 --branch main $Repo $InstallDir
}
Write-Ok "Repo ready"

# 3. Virtualenv + deps
if (-not (Test-Path $VenvDir)) { python -m venv $VenvDir }
& "$VenvDir\Scripts\pip" install --quiet --upgrade pip
& "$VenvDir\Scripts\pip" install --quiet -e $InstallDir
Write-Ok "Dependencies installed"

# 4. .env
if (-not (Test-Path $EnvFile)) {
    Copy-Item "$InstallDir\.env.example" $EnvFile
    Write-Info ".env created — fill in HF_TOKEN and OWNER_TOKEN"
} else {
    Write-Info ".env already exists — skipping"
}

# 5. Patch Claude Desktop config
$McpBin = "$VenvDir\Scripts\xksh808-mcp.exe"
New-Item -ItemType Directory -Force -Path (Split-Path $CfgPath) | Out-Null
$cfg = if (Test-Path $CfgPath) { Get-Content $CfgPath -Raw | ConvertFrom-Json } else { @{} }
if (-not $cfg.mcpServers) { $cfg | Add-Member -NotePropertyName mcpServers -NotePropertyValue @{} }
$cfg.mcpServers."xksh808-ultimate" = @{
    command = $McpBin
    args    = @()
    env     = @{ PYTHONPATH = $InstallDir }
}
$cfg | ConvertTo-Json -Depth 10 | Set-Content $CfgPath -Encoding UTF8
Write-Ok "Claude Desktop config patched: $CfgPath"

# 6. Register as a Scheduled Task (auto-start on login, no admin needed)
$TaskName = "xksh808-mcp"
$Action   = New-ScheduledTaskAction -Execute $McpBin -WorkingDirectory $InstallDir
$Trigger  = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -RunLevel Limited | Out-Null
Start-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
Write-Ok "Scheduled Task registered — server auto-starts on every login"

# 7. Done
Write-Banner "Installation complete 🌋"
Write-Host "  Next: fill in HF_TOKEN + OWNER_TOKEN in:"
Write-Host "  $EnvFile" -ForegroundColor Cyan
Write-Host "`n  Restart Claude Desktop — xksh808-ultimate tools will appear automatically.`n"
