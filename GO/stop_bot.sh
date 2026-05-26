#!/bin/bash

echo "========================================"
echo " INFODriver Bot - Stop"
echo "========================================"
echo ""

PID=$(pgrep -f "infodriver" | grep -v "start_bot" | head -1)
if [ -z "$PID" ]; then
    echo "[!] Bot is not running"
    exit 0
fi

echo "[*] Stopping bot (PID: $PID)..."
kill $PID 2>/dev/null
sleep 2

if kill -0 $PID 2>/dev/null; then
    echo "[!] Force killing..."
    kill -9 $PID 2>/dev/null
fi

echo "[OK] Bot stopped"

echo ""
echo "[*] Removing auto-start..."
(crontab -l 2>/dev/null | grep -v "infodriver") | crontab -
sudo sed -i "/infodriver/d" /etc/rc.local 2>/dev/null || true
echo "[OK] Auto-start removed"
