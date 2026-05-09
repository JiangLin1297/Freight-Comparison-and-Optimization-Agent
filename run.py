#!/usr/bin/env python3
"""
运输方案比价与优化智能体 - 启动脚本
"""
import os
import sys

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    import uvicorn
    from main import app

    print("=" * 60)
    print("运输方案比价与优化智能体")
    print("=" * 60)
    print(f"启动服务: http://localhost:8000")
    print(f"API文档: http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
