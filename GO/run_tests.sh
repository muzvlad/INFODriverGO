#!/bin/bash

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "========================================"
echo " INFODriver Tests"
echo "========================================"
echo ""

echo "[1/2] Running unit tests (bot)..."
echo ""
go test -v -count=1 ./bot/
if [ $? -ne 0 ]; then
    echo ""
    echo "[FAIL] Unit tests failed!"
else
    echo ""
    echo "[PASS] Unit tests passed!"
fi
echo ""
echo "--------------------------------"
echo ""

echo "[2/2] Running integration tests..."
echo ""
go test -v -count=1 ./tests/
if [ $? -ne 0 ]; then
    echo ""
    echo "[FAIL] Integration tests failed!"
else
    echo ""
    echo "[PASS] Integration tests passed!"
fi
echo ""
echo "========================================"
echo " Done."
echo "========================================"
