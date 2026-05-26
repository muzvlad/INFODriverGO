@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo INFODriver Bot - Build and Run
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Setting environment...
set CC=C:\soft\TDM-GCC-64\bin\gcc.exe
set CGO_ENABLED=1

echo [2/3] Building bot...
if exist infodriver.exe del /f /q infodriver.exe >nul 2>&1
go build -o infodriver.exe . 2>&1

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo [OK] Build completed!
echo.

echo ========================================
echo STARTING BOT...
echo ========================================
echo.
echo Press Ctrl+C to stop
echo.

infodriver.exe

echo.
echo Bot stopped.
pause