@echo off
echo ========================================
echo 运输方案比价与优化智能体 - 安装脚本
echo ========================================
echo.

echo [1/2] 安装Python依赖...
pip install -r requirements.txt
echo.

echo [2/2] 安装完成!
echo.
echo 运行方式: python run.py
echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
pause
