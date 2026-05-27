#!/bin/bash
#
# Deploy script for Raspberry Pi
# Usage: ./deploy.sh
#
# Pulls latest code, installs pre-compiled ARM64 binary, restarts the bot.

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "========================================"
echo " INFODriver Deploy"
echo "========================================"
echo ""

# 1. Pull latest from git
echo "[*] Pulling latest code..."
git pull
echo "[OK] Pull complete"
echo ""

# 2. Install pre-compiled ARM64 binary
if [ -f "./infodriver_arm64" ]; then
    echo "[*] Installing ARM64 binary..."
    cp ./infodriver_arm64 ./infodriver
    chmod +x ./infodriver
    echo "[OK] Binary installed: $(ls -lh infodriver | awk '{print $5}')"
else
    echo "[!] No pre-compiled ARM64 binary found, building from source..."
    go build -o infodriver .
    echo "[OK] Built from source"
fi
echo ""

# 3. Restart via systemd or fallback
if systemctl is-active --quiet infodriver 2>/dev/null; then
    echo "[*] Restarting systemd service..."
    sudo systemctl restart infodriver
    echo "[OK] Service restarted"
    echo ""
    systemctl status infodriver --no-pager | head -5
else
    echo "[*] systemd not found, using start_bot.sh..."
    exec ./start_bot.sh
fi
echo ""
echo "========================================"
echo " Deploy complete!"
echo "========================================"
