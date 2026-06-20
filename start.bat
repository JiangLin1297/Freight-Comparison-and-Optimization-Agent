@echo off
chcp 65001 >nul
title 运输方案比价与优化智能体

echo ============================================================
echo   运输方案比价与优化智能体
echo   http://localhost:8000
echo ============================================================
echo.

:: 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境，请先运行 setup.bat 完成初始化
    pause
    exit /b 1
)

:: 检查端口占用
netstat -ano 2>nul | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo [错误] 端口 8000 已被占用，请先关闭占用该端口的程序
    echo        查看占用: netstat -ano ^| findstr ":8000"
    pause
    exit /b 1
)

:: 启动后端
echo 正在启动服务...
cd backend
start "" http://localhost:8000
..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000

cd ..
echo.
echo 服务已停止。按 Ctrl+C 可随时停止。
pause
