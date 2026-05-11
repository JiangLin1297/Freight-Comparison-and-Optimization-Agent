#!/usr/bin/env python3
"""
运输方案比价与优化智能体 - 启动脚本
"""
import os
import sys
import subprocess
import threading
import socket

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_port_process(port):
    """终止占用端口的进程（Windows）"""
    try:
        result = subprocess.run(
            ['netstat', '-ano', '|', 'findstr', f':{port}'],
            capture_output=True, text=True, shell=True
        )
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if f':{port}' in line and 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                    print(f"Terminated process {pid} on port {port}")
    except Exception as e:
        print(f"Warning: Could not kill process on port {port}: {e}")

def find_npm():
    """查找npm命令路径"""
    # 尝试直接使用npm
    try:
        subprocess.run(['npm', '--version'], capture_output=True, check=True)
        return 'npm'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # 尝试使用npm.cmd（Windows）
    npm_cmd = os.path.join(os.environ.get('APPDATA', ''), 'npm', 'npm.cmd')
    if os.path.exists(npm_cmd):
        return npm_cmd

    # 尝试在PATH中查找
    for path in os.environ.get('PATH', '').split(';'):
        npm_path = os.path.join(path, 'npm.cmd')
        if os.path.exists(npm_path):
            return npm_path

    return None

def start_backend():
    """启动后端服务"""
    import uvicorn
    from main import app
    uvicorn.run(app, host="0.0.0.0", port=8000)

def start_frontend():
    """启动前端开发服务"""
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    npm_cmd = find_npm()

    if npm_cmd is None:
        print("ERROR: npm not found. Please install Node.js 18+")
        print("Download from: https://nodejs.org/")
        return

    print(f"Using npm: {npm_cmd}")
    subprocess.run([npm_cmd, 'run', 'dev'], cwd=frontend_dir)

if __name__ == "__main__":
    print("=" * 60)
    print("Freight Comparison Agent")
    print("=" * 60)
    print(f"Frontend: http://localhost:3000")
    print(f"Backend:  http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print("=" * 60)

    # 检查并清理端口
    if is_port_in_use(8000):
        print("Port 8000 is in use. Attempting to free it...")
        kill_port_process(8000)

    if is_port_in_use(3000):
        print("Port 3000 is in use. Attempting to free it...")
        kill_port_process(3000)

    # 在后台线程启动前端
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    frontend_thread.start()

    # 在主线程启动后端
    start_backend()
