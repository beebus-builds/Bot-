@echo off
REM PowerBot Desktop Windows Application Launcher
REM Run PowerBot.exe if available, otherwise fallback to Python script
setlocal
if exist "%~dp0dist\PowerBot.exe" (
    start "" "%~dp0dist\PowerBot.exe"
    exit /b 0
)
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found in PATH. Install Python 3.10+ and try again.
    pause
    exit /b 1
)
python "%~dp0Unified_Laptop_Power_Bot.py"
if errorlevel 1 (
    echo PowerBot failed to start.
    pause
)
