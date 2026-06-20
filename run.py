"""运输方案比价与优化智能体 - 一键启动脚本"""

import os
import sys
import webbrowser
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
INDEX_HTML = os.path.join(STATIC_DIR, "index.html")

VENV_PYTHON = os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe")


def main():
    # 检查虚拟环境
    if not os.path.exists(VENV_PYTHON):
        print("=" * 60)
        print("  未找到虚拟环境 (.venv)")
        print("  请先运行 setup.bat 完成初始化")
        print("=" * 60)
        sys.exit(1)

    # 检查前端是否已构建
    if not os.path.exists(INDEX_HTML):
        print("=" * 60)
        print("  未找到前端静态文件 (backend/static/index.html)")
        print("  请先运行 setup.bat 或执行:")
        print("    cd frontend && npm run build")
        print("=" * 60)
        sys.exit(1)

    # 启动
    print("=" * 60)
    print("  运输方案比价与优化智能体")
    print("  http://localhost:8000")
    print("=" * 60)
    print()

    webbrowser.open("http://localhost:8000")

    subprocess.run(
        [VENV_PYTHON, "-m", "uvicorn", "main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
    )


if __name__ == "__main__":
    main()
