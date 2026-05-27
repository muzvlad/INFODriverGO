#!/bin/bash

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "========================================"
echo " INFODriver Bot - Start"
echo "========================================"
echo ""

if [ -f "./infodriver_arm64" ]; then
    echo "[OK] Pre-compiled ARM64 binary found"
    if [ ! -f "./infodriver" ] || [ "./infodriver_arm64" -nt "./infodriver" ]; then
        cp ./infodriver_arm64 ./infodriver
        chmod +x ./infodriver
        echo "[OK] Binary updated from infodriver_arm64"
    fi
elif [ ! -f "./infodriver" ]; then
    echo "[!] Binary not found, trying to build..."
    go build -o infodriver .
    if [ $? -ne 0 ]; then
        echo ""
        echo "[ERROR] Build failed!"
        exit 1
    fi
    echo "[OK] Build completed!"
else
    echo "[OK] Binary found"
fi
echo ""

echo "[*] Stopping old bot instance..."

# If managed by systemd, restart via service
if systemctl is-active --quiet infodriver 2>/dev/null; then
    echo "[*] Bot is managed by systemd, restarting service..."
    sudo systemctl restart infodriver
    echo "[OK] Bot restarted via systemd"
    echo ""
    systemctl status infodriver --no-pager | head -5
    exit 0
fi

# Manual kill — SIGKILL to ensure the process dies instantly
pkill -9 -f "infodriver" 2>/dev/null || true
sleep 1
echo "[OK] Old instances stopped"
echo ""

echo "[*] Starting bot in background..."
nohup ./infodriver > bot.log 2>&1 &
PID=$!
echo "[OK] Bot started (PID: $PID)"
echo ""

echo "[*] Checking autostart..."
if systemctl is-enabled --quiet infodriver 2>/dev/null; then
    echo "[OK] systemd autostart is already configured (infodriver.service)"
else
    echo "[!] systemd autostart not found — run: sudo systemctl enable infodriver"
fi

# Clean up old crontab/rc.local entries to prevent duplicates
OLD_CRON=$(crontab -l 2>/dev/null | grep "infodriver")
if [ -n "$OLD_CRON" ]; then
    (crontab -l 2>/dev/null | grep -v "infodriver") | crontab -
    echo "[OK] Removed old crontab entry (superseded by systemd)"
fi
if grep -q "infodriver" /etc/rc.local 2>/dev/null; then
    sudo sed -i "/infodriver/d" /etc/rc.local 2>/dev/null
    echo "[OK] Removed old rc.local entry (superseded by systemd)"
fi
echo ""

echo "========================================"
echo " Bot is running!"
echo " Logs: tail -f $DIR/bot.log"
echo " Stop: ./stop_bot.sh"
echo "========================================"
