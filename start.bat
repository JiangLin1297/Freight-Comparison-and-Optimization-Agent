@echo off
chcp 65001 >nul
echo ========================================
echo Freight Comparison Agent - Start Script
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

:: Install backend dependencies
echo [1/3] Installing backend dependencies...
pip install -r requirements.txt -q

:: Install frontend dependencies
echo [2/3] Installing frontend dependencies...
cd frontend
call npm install
cd ..

:: Start service
echo [3/3] Starting service...
echo.
echo ========================================
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Press Ctrl+C to stop
echo.

python run.py
pause
