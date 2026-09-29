@echo off
cd /d "%~dp0"
title FitBuddy Setup and Server
echo ========================================
echo          FITBUDDY - START
echo ========================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python is not installed or "py" is unavailable.
  echo Install Python 3.11 or newer and enable Add Python to PATH.
  pause
  exit /b 1
)
if not exist ".venv\\Scripts\\python.exe" (
  echo Creating virtual environment...
  py -m venv .venv
  if errorlevel 1 goto error
)
echo Installing required packages...
".venv\\Scripts\\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto error
".venv\\Scripts\\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
if not exist ".env" copy ".env.example" ".env" >nul
echo.
echo Starting FitBuddy. Do not close this window.
echo Open http://127.0.0.1:8000 in your browser.
".venv\\Scripts\\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000
goto end
:error
echo.
echo Setup failed. Please take a screenshot of this window.
pause
:end
