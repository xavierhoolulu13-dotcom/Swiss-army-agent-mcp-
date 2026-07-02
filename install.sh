#!/usr/bin/env bash
# ============================================================
# 🌋 XKSH808 Ultimate Concierge — No-Click Installer
# Run: curl -fsSL https://raw.githubusercontent.com/xavierhoolulu13-dotcom/Swiss-army-agent-mcp-/main/install.sh | bash
# ============================================================
set -euo pipefail

REPO="https://github.com/xavierhoolulu13-dotcom/Swiss-army-agent-mcp-.git"
INSTALL_DIR="$HOME/.xksh808/mcp"
SERVICE_NAME="xksh808-mcp"
PYTHON="${PYTHON:-python3}"

# ── Colors ────────────────────────────────────────────────────────────────────
R='\033[0;35m'; C='\033[0;36m'; G='\033[0;32m'; Y='\033[0;33m'; N='\033[0m'
banner() { echo -e "\n${R}🌋 XKSH808${N} ${C}$*${N}"; }
ok()     { echo -e "  ${G}✓${N} $*"; }
info()   { echo -e "  ${Y}→${N} $*"; }

banner "Ultimate Concierge — No-Click Installer"
echo -e "  FloatForge808 · Volcano IS · SpiffyCloud OS\n"

# ── 1. Check Python ───────────────────────────────────────────────────────────
if ! command -v "$PYTHON" &>/dev/null; then
  echo "Python 3.11+ is required. Install it from https://python.org and re-run."
  exit 1
fi
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python $PY_VER detected"

# ── 2. Clone / update repo ────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
  info "Updating existing install at $INSTALL_DIR"
  git -C "$INSTALL_DIR" pull --ff-only origin main 2>/dev/null || true
else
  info "Cloning into $INSTALL_DIR"
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --depth=1 --branch main "$REPO" "$INSTALL_DIR"
fi
ok "Repo ready"

# ── 3. Create virtualenv + install deps ───────────────────────────────────────
VENV="$INSTALL_DIR/.venv"
if [ ! -d "$VENV" ]; then
  "$PYTHON" -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -e "$INSTALL_DIR"
ok "Dependencies installed"

# ── 4. Write .env (skip if already exists) ────────────────────────────────────
ENV_FILE="$INSTALL_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
  cp "$INSTALL_DIR/.env.example" "$ENV_FILE"
  info ".env created at $ENV_FILE — fill in HF_TOKEN and OWNER_TOKEN to unlock all modules"
else
  info ".env already exists — skipping (delete it to reset)"
fi

# ── 5. Auto-patch Claude Desktop MCP config ───────────────────────────────────
PYTHON_BIN="$VENV/bin/python"
MCP_ENTRY="$VENV/bin/xksh808-mcp"

patch_claude_config() {
  local cfg="$1"
  "$PYTHON_BIN" - "$cfg" "$MCP_ENTRY" "$INSTALL_DIR" <<'PYEOF'
import json, sys, os
cfg_path, mcp_bin, install_dir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
try:
    data = json.loads(open(cfg_path).read()) if os.path.exists(cfg_path) else {}
except json.JSONDecodeError:
    data = {}
data.setdefault("mcpServers", {})
data["mcpServers"]["xksh808-ultimate"] = {
    "command": mcp_bin,
    "args": [],
    "env": {
        "PYTHONPATH": install_dir
    }
}
open(cfg_path, "w").write(json.dumps(data, indent=2))
print(cfg_path)
PYEOF
}

PATCHED=""
OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
  Darwin)
    CFG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    PATCHED=$(patch_claude_config "$CFG")
    ;;
  Linux)
    CFG="$HOME/.config/Claude/claude_desktop_config.json"
    PATCHED=$(patch_claude_config "$CFG")
    ;;
  MINGW*|CYGWIN*|MSYS*)
    CFG="${APPDATA:-$HOME/AppData/Roaming}/Claude/claude_desktop_config.json"
    PATCHED=$(patch_claude_config "$CFG")
    ;;
esac
[ -n "$PATCHED" ] && ok "Claude Desktop config patched: $PATCHED"

# ── 6. Install system service (auto-start on boot) ────────────────────────────
case "$OS_TYPE" in
  Darwin)
    PLIST="$HOME/Library/LaunchAgents/com.xksh808.mcp.plist"
    cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>             <string>com.xksh808.mcp</string>
  <key>ProgramArguments</key>  <array><string>$MCP_ENTRY</string></array>
  <key>WorkingDirectory</key>  <string>$INSTALL_DIR</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PYTHONPATH</key> <string>$INSTALL_DIR</string>
  </dict>
  <key>RunAtLoad</key>         <true/>
  <key>KeepAlive</key>         <true/>
  <key>StandardOutPath</key>   <string>$HOME/.xksh808/mcp.log</string>
  <key>StandardErrorPath</key> <string>$HOME/.xksh808/mcp.err</string>
</dict>
</plist>
PLIST
    launchctl unload "$PLIST" 2>/dev/null || true
    launchctl load -w "$PLIST"
    ok "macOS LaunchAgent installed — server auto-starts on login"
    ;;
  Linux)
    if command -v systemctl &>/dev/null && [ -d "$HOME/.config/systemd/user" ] 2>/dev/null || mkdir -p "$HOME/.config/systemd/user"; then
      UNIT="$HOME/.config/systemd/user/${SERVICE_NAME}.service"
      cat > "$UNIT" <<UNIT
[Unit]
Description=XKSH808 Ultimate Concierge MCP Server
After=network.target

[Service]
ExecStart=$MCP_ENTRY
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
UNIT
      systemctl --user daemon-reload
      systemctl --user enable "$SERVICE_NAME" 2>/dev/null || true
      systemctl --user restart "$SERVICE_NAME" 2>/dev/null || true
      ok "systemd user service installed — server auto-starts on login"
    else
      info "systemd not available — server will run on next Claude Desktop launch only"
    fi
    ;;
  *)
    info "Windows: service registration skipped — Claude Desktop will launch the server on demand via mcp.json"
    ;;
esac

# ── 7. Done ───────────────────────────────────────────────────────────────────
echo ""
banner "Installation complete 🌋"
echo -e "  ${Y}Next: fill in HF_TOKEN + OWNER_TOKEN in:${N}"
echo -e "  ${C}$ENV_FILE${N}"
echo -e ""
echo -e "  Restart Claude Desktop and the ${C}xksh808-ultimate${N} tools will appear automatically."
echo -e "  Logs: ${C}$HOME/.xksh808/mcp.log${N}"
echo ""
