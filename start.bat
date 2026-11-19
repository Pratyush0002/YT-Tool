@echo off
chcp 65001 >nul
title ShortsViral AI - YouTube Shorts Generator
cd /d "%~dp0"

echo =====================================================================
echo       ShortsViral AI - YouTube Shorts Comedy Generator
echo       Website: http://127.0.0.1:5000
echo =====================================================================
echo.
echo Starting server and opening your browser...
echo.

python run.py
if errorlevel 1 (
    echo.
    echo Trying with py launcher...
    py run.py
)

if errorlevel 1 (
    echo.
    echo ===============================================================
    echo Error: Could not start python automatically.
    echo Please make sure Python is installed and run: python run.py
    echo ===============================================================
    pause
)
pause
