#!/usr/bin/env python3
"""
运输方案比价与优化智能体 - 启动脚本
"""
import os
import sys
import subprocess
import threading

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def start_backend():
    """启动后端服务"""
    import uvicorn
    from main import app
    uvicorn.run(app, host="0.0.0.0", port=8000)

def start_frontend():
    """启动前端开发服务"""
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    subprocess.run(['npm', 'run', 'dev'], cwd=frontend_dir)

if __name__ == "__main__":
    print("=" * 60)
    print("运输方案比价与优化智能体")
    print("=" * 60)
    print(f"前端界面: http://localhost:3000")
    print(f"后端API: http://localhost:8000")
    print(f"API文档: http://localhost:8000/docs")
    print("=" * 60)

    # 在后台线程启动前端
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    frontend_thread.start()

    # 在主线程启动后端
    start_backend()
