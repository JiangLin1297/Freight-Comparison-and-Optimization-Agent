@echo off
chcp 65001 >nul
echo ========================================
echo   推送到 GitHub
echo ========================================
echo.

echo [1/2] 检查 Git 状态...
git status
echo.

echo [2/2] 推送到 GitHub...
git push origin main

if errorlevel 1 (
    echo.
    echo [错误] 推送失败！
    echo 可能的原因：
    echo   1. 网络连接问题
    echo   2. GitHub 认证问题
    echo   3. 代理配置问题
    echo.
    echo 请检查网络连接后重试，或使用以下命令手动推送：
    echo   git push origin main
    echo.
) else (
    echo.
    echo [成功] 已推送到 GitHub！
    echo 仓库地址: https://github.com/JiangLin1297/Freight-Comparison-and-Optimization-Agent
    echo.
)

pause
