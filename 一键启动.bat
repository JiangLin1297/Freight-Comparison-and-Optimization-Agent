@echo off
chcp 65001 >nul
title 运输方案比价与优化智能体 - 一键启动

echo ========================================
echo   运输方案比价与优化智能体 - 一键启动
echo ========================================
echo.

:: =============================================
:: 第一步：检查基础环境
:: =============================================
echo [检查环境] ...

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] 未检测到 Python！
    echo 请前往 https://www.python.org/downloads/ 下载安装 Python 3.9+
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

:: 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] 未检测到 Node.js！
    echo 请前往 https://nodejs.org/ 下载安装 Node.js 18+
    echo.
    pause
    exit /b 1
)

echo [√] Python 已安装
echo [√] Node.js 已安装
echo.

:: =============================================
:: 第二步：检查并安装依赖
:: =============================================

:: 检查 Python 依赖（尝试导入关键模块）
echo [检查Python依赖] ...
python -c "import fastapi; import uvicorn; import pandas; import pydantic; import dotenv" >nul 2>&1
if errorlevel 1 (
    echo [提示] 检测到缺少Python依赖，正在安装...
    pip install -r requirements.txt -q
    if errorlevel 1 (
        echo [错误] Python依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [√] Python依赖安装完成
) else (
    echo [√] Python依赖已就绪
)

:: 检查前端依赖
echo [检查前端依赖] ...
if not exist "frontend\node_modules" (
    echo [提示] 检测到缺少前端依赖，正在安装...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    cd ..
    echo [√] 前端依赖安装完成
) else (
    echo [√] 前端依赖已就绪
)

echo.
echo ========================================
echo   所有依赖已就绪，正在启动服务...
echo ========================================
echo.
echo   前端地址: http://localhost:3000
echo   后端地址: http://localhost:8000
echo   API文档:  http://localhost:8000/docs
echo.
echo   按 Ctrl+C 停止服务
echo ========================================
echo.

:: =============================================
:: 第三步：启动服务并自动打开浏览器
:: =============================================

:: 延迟3秒后打开浏览器（给服务启动时间）
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:3000"

:: 启动应用
python run.py
pause
