#!/bin/bash

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "========================================"
echo " INFODriver Bot - Start"
echo "========================================"
echo ""

if [ ! -f "./infodriver" ]; then
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
pkill -f "infodriver" 2>/dev/null || true
sleep 1
echo "[OK] Old instances stopped"
echo ""

echo "[*] Starting bot in background..."
nohup ./infodriver > bot.log 2>&1 &
PID=$!
echo "[OK] Bot started (PID: $PID)"
echo ""

echo "[*] Setting up auto-start on boot..."
CRONLINE="@reboot cd $DIR && nohup ./infodriver > $DIR/bot.log 2>&1 &"
(crontab -l 2>/dev/null | grep -v "infodriver"; echo "$CRONLINE") | crontab -
echo "[OK] Added to crontab"

# Also add to rc.local as fallback
RCLOCAL_LINE="cd $DIR && nohup ./infodriver > $DIR/bot.log 2>&1 &"
if grep -q "infodriver" /etc/rc.local 2>/dev/null; then
    echo "[OK] Already in rc.local"
else
    sudo sed -i "s|^exit 0|$RCLOCAL_LINE\\nexit 0|" /etc/rc.local 2>/dev/null && echo "[OK] Added to rc.local" || echo "[!] Could not add to rc.local (run with sudo?)"
fi
echo ""

echo "[*] Current crontab:"
crontab -l | grep infodriver
echo ""

echo "========================================"
echo " Bot is running!"
echo " Logs: tail -f $DIR/bot.log"
echo " Stop: ./stop_bot.sh"
echo "========================================"
