@echo off
chcp 65001 >nul
title 运输方案比价与优化智能体 - 初始化

echo ============================================================
echo   运输方案比价与优化智能体 - 首次初始化
echo ============================================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    echo        下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [1/6] Python 已就绪

:: 检查 Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    echo        下载地址: https://nodejs.org/
    pause
    exit /b 1
)
echo [2/6] Node.js 已就绪

:: 创建虚拟环境
if not exist ".venv" (
    echo [3/6] 创建 Python 虚拟环境...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
) else (
    echo [3/6] 虚拟环境已存在，跳过
)

:: 安装 Python 依赖
echo [4/6] 安装 Python 依赖...
.venv\Scripts\python.exe -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] Python 依赖安装失败
    pause
    exit /b 1
)
echo        Python 依赖安装完成

:: 安装前端依赖 + 构建
echo [5/6] 安装前端依赖并构建...
cd frontend
call npm install --silent 2>nul
if %errorlevel% neq 0 (
    echo [错误] 前端依赖安装失败
    cd ..
    pause
    exit /b 1
)
call npm run build --silent 2>nul
if %errorlevel% neq 0 (
    echo [错误] 前端构建失败
    cd ..
    pause
    exit /b 1
)
cd ..
echo       前端构建完成

:: 初始化数据库
echo [6/6] 初始化数据库...
cd backend
..\.venv\Scripts\python.exe init_db.py
if %errorlevel% neq 0 (
    echo [警告] 数据库初始化失败，首次启动时将使用 CSV 数据源
)
cd ..

:: 检查 .env 配置
if not exist ".env" (
    echo.
    echo [提示] 未找到 .env 文件，已从 .env.example 复制
    copy .env.example .env >nul
    echo        请编辑 .env 文件，填入 DASHSCOPE_API_KEY
)

echo.
echo ============================================================
echo   初始化完成！
echo.
echo   首次使用请先配置 API Key：
echo     1. 编辑项目根目录的 .env 文件
echo     2. 填入 DASHSCOPE_API_KEY=你的密钥
echo       （也可以在启动后通过网页配置）
echo.
echo   后续启动：双击 start.bat
echo   网页地址：http://localhost:8000
echo ============================================================
pause
