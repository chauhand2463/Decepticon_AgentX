@echo off
setlocal enabledelayedexpansion

:: DECEPTICON - EXTREME LEVEL LAUNCHER
:: "Vibe Hacking Tool" - Perfectly Fixed Edition

set "VERSION=2.5.0"
set "CODENAME=DECEPTICON"

title %CODENAME% v%VERSION% - Tactical HUD

:: Set console size and color
mode con: cols=120 lines=40
color 0B

echo.
echo  [91m  ██████╗ ███████╗ ██████╗███████╗██████╗ ████████╗██╗ ██████╗ ██████╗ ███╗   ██╗ [0m
echo  [91m  ██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔═══██╗████╗  ██║ [0m
echo  [91m  ██║  ██║█████╗  ██║     █████╗  ██████╔╝   ██║   ██║██║     ██║   ██║██╔██╗ ██║ [0m
echo  [91m  ██║  ██║██╔══╝  ██║     ██╔══╝  ██╔═══╝    ██║   ██║██║     ██║   ██║██║╚██╗██║ [0m
echo  [91m  ██████╔╝███████╗╚██████╗███████╗██║        ██║   ██║╚██████╗╚██████╔╝██║ ╚████║ [0m
echo  [91m  ╚═════╝ ╚══════╝ ╚═════╝╚══════╝╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝ [0m
echo.
echo           [96m [ TACTICAL VIBE HACKING INTERFACE ] [0m
echo           [90m Version %VERSION% | Codename: %CODENAME% [0m
echo.
echo  [90m-------------------------------------------------------------------------------- [0m
echo   [93m[*] SYSTEM CHECK [0m
echo  [90m-------------------------------------------------------------------------------- [0m

:: Check for UV
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [91m[!] Missing 'uv' package manager. [0m
    echo   [97mPlease install it: 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"' [0m
    pause
    exit /b 1
)
echo   [92m[+] UV System: ONLINE [0m

:: Check for Ollama (optional)
tasklist /fi "imagename eq ollama exe" | find /i "ollama" >nul 2>&1
if %errorlevel% eq 0 (
    echo   [92m[+] Ollama Service: DETECTED [0m
) else (
    echo   [93m[!] Ollama Service: OFFLINE (Optional) [0m
)

echo.
echo  [90m-------------------------------------------------------------------------------- [0m
echo   [96m[1] Launch WEB HUD (Extreme Mode) [0m
echo   [96m[2] Launch TACTICAL CLI (Matrix Mode) [0m
echo   [96m[3] Run Full System Diagnostics [0m
echo   [96m[4] Exit [0m
echo  [90m-------------------------------------------------------------------------------- [0m
echo.

set /p choice=" [95mSELECT OPERATION > [0m "

if "%choice%"=="1" goto launch_web
if "%choice%"=="2" goto launch_cli
if "%choice%"=="3" goto diagnostics
if "%choice%"=="4" exit

:launch_web
echo.
echo  [92m[+] Starting Decepticon Web HUD... [0m
uv run streamlit run frontend/streamlit_app.py
pause
goto main

:launch_cli
echo.
echo  [92m[+] Initializing Decepticon Tactical CLI... [0m
uv run python frontend/cli/cli.py
pause
goto main

:diagnostics
echo.
echo  [93m[!] Running Diagnostics... [0m
uv run python .agent/scripts/verify_all.py
pause
goto main
