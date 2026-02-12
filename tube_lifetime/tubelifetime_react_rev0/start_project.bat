@echo off
setlocal

REM --- Configuration ---
set "BACKEND_DIR=backend"
set "FRONTEND_DIR=frontend"
set "VENV_DIR=.venv"
set "BROWSER_URL=http://localhost:5173"

title Tube Lifetime Tester Launcher

echo ==========================================
echo       Tube Lifetime Tester Pro
echo        [ React + FastAPI ]
echo ==========================================
echo.

REM 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.
    pause
    exit /b 1
)

REM 2. Check for Node.js
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js/npm not found. Please install Node.js.
    pause
    exit /b 1
)

REM 3. Check for backend entrypoint
if not exist "%BACKEND_DIR%\main.py" (
    echo [ERROR] Backend entrypoint not found: %BACKEND_DIR%\main.py
    pause
    exit /b 1
)

REM 4. Check for frontend entrypoint
if not exist "%FRONTEND_DIR%\package.json" (
    echo [ERROR] Frontend package.json not found at %FRONTEND_DIR%\package.json
    pause
    exit /b 1
)

REM 5. Check for frontend dependencies
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [WARN] Frontend dependencies (node_modules) not found.
    echo Please run the following command in a new terminal:
    echo.
    echo   cd %FRONTEND_DIR%
    echo   npm install
    echo.
    pause
)

REM 6. Check for backend dependencies
if not exist "%VENV_DIR%" (
    echo [WARN] Python virtual environment (.venv) not found.
    echo Please run the following commands in a new terminal:
    echo.
    echo   python -m venv .venv
    echo   %VENV_DIR%\Scripts\activate
    echo   pip install -r %BACKEND_DIR%\requirements.txt
    echo.
    pause
)

echo [1/3] Starting Backend Server (FastAPI)...
start "TubeBackend" /min cmd /c "call \"%VENV_DIR%\Scripts\activate.bat\" && python \"%CD%\%BACKEND_DIR%\main.py\""

echo [2/3] Starting Frontend Server (Vite)...
start "TubeFrontend" /min cmd /k "cd %FRONTEND_DIR% && npm run dev"

echo [3/3] Waiting for services to initialize...
timeout /t 5 /nobreak >nul

echo.
echo [INFO] If the browser shows a blank or error page, please check:
echo        1. Frontend dependencies are installed ('npm install' in 'frontend').
echo        2. Backend dependencies are installed and the venv is active.
echo        3. Ports 5173 or 8000 are not already in use.
echo        4. The backend and frontend terminal windows for any error messages.
echo.
echo [SUCCESS] System launch commands sent. Opening browser...
start %BROWSER_URL%

echo.
echo ==========================================
echo  Backend:  http://localhost:8000
echo  Frontend: %BROWSER_URL%
echo ==========================================
echo.
echo Close this window to stop both the backend and frontend services.
pause

REM Clean up by killing the started processes
taskkill /FI "WINDOWTITLE eq TubeBackend" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq TubeFrontend" /T /F >nul 2>&1