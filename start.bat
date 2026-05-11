@echo off
chcp 65001 >nul
echo ========================================
echo 运输方案比价与优化智能体 - 启动脚本
echo ========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

:: 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)

:: 安装后端依赖
echo [1/3] 安装后端依赖...
pip install -r requirements.txt -q

:: 安装前端依赖
echo [2/3] 安装前端依赖...
cd frontend
call npm install
cd ..

:: 启动服务
echo [3/3] 启动服务...
echo.
echo ========================================
echo 前端界面: http://localhost:3000
echo 后端API: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo ========================================
echo.
echo 按 Ctrl+C 停止服务
echo.

python run.py
pause
