@echo off
chcp 65001 >nul

echo 正在停止服务...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo 已停止进程 %%a
)

echo 服务已停止。
pause
