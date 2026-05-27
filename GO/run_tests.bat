@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo INFODriver Tests
echo ========================================
echo.

cd /d "%~dp0"

set CC=C:\soft\TDM-GCC-64\bin\gcc.exe
set CGO_ENABLED=1

echo [1/2] Running unit tests (bot)...
echo.
go test -v -count=1 ./bot/
if errorlevel 1 (
    echo.
    echo [FAIL] Unit tests failed!
) else (
    echo.
    echo [PASS] Unit tests passed!
)
echo.
echo --------------------------------
echo.

echo [2/2] Running integration tests...
echo.
go test -v -count=1 ./tests/
if errorlevel 1 (
    echo.
    echo [FAIL] Integration tests failed!
) else (
    echo.
    echo [PASS] Integration tests passed!
)
echo.
echo ========================================
echo Done.
echo ========================================
pause
