# 🚢 运输方案比价与优化智能体

> Freight Comparison and Optimization Agent

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-42b883.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

基于大语言模型的物流运费比价与优化系统。输入订单信息，自动匹配承运商报价，精确计算成本，多维度评分推荐最优方案。支持自然语言交互。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🤖 LLM 智能体 | 集成大语言模型，自然语言输入需求，自动解析并推荐方案 |
| 📋 智能比价 | 输入重量、起运港、目的港、时效，自动匹配所有符合条件的方案 |
| 🔄 转运搜索 | 无直达路线时自动搜索经中转港的最优转运方案 |
| 💰 精确计费 | 按公式 `Cost = max(Min_Cost, Rate × Weight)` 核算运费 |
| 🏆 多维度推荐 | 成本、时效、服务评级加权评分，支持时效/成本优先 |
| 📊 报告导出 | 一键导出比价报告（纯文本/Word 文档） |

## 📦 内置数据

| 指标 | 数值 |
|------|------|
| 总记录数 | 10,277 |
| 承运商 | 14 家 |
| 起运港 | 10 个 (PORT02-PORT11) |
| 目的港 | 8 个 |
| 运输方式 | 空运 / 陆运 |
| 服务级别 | 门到门 (DTD) / 门到港 (DTP) |

支持上传 CSV / Excel 文件替换为自定义数据。

## 🚀 首次使用

### 环境要求

- **Python 3.9+**
- **Node.js 18+**

### 步骤

```bash
# 1. 克隆项目
git clone https://github.com/JiangLin1297/Freight-Comparison-and-Optimization-Agent.git
cd Freight-Comparison-and-Optimization-Agent

# 2. 初始化（Windows 双击 setup.bat）
setup.bat
```

初始化完成后：

1. 编辑 `.env`，填入你的 API Key：
```env
DASHSCOPE_API_KEY=你的密钥
```
或启动后在网页中配置（点击顶栏设置按钮）。

2. 启动：
```bash
# Windows 双击 start.bat
start.bat
```

浏览器会自动打开 `http://localhost:8000`。

### 自然语言示例

在 Agent 输入框中尝试：

```
从大连运100kg到厦门，越快越好
```

```
2吨货物从上海发往深圳，10天内到，最省钱的方案
```

```
我有500公斤货，从广州到青岛，3天内，要门到门
```

## 🔄 后续启动

```bash
# Windows 双击
start.bat

# 或命令行
python run.py
```

之前的数据和配置会自动复用，无需重新初始化。

## 🛑 停止服务

双击 `stop.bat`，或按 `Ctrl+C`。

## 🛠 技术栈

```
前端: Vue 3 + Element Plus + Vite 5
后端: Python + FastAPI + Uvicorn
数据: Pandas + SQLAlchemy + SQLite
LLM:  MiMo v2 (OpenAI SDK 兼容接口)
```

## 📡 关键 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/status` | GET | 系统状态 |
| `/api/ports` | GET | 港口列表 |
| `/api/statistics` | GET | 数据统计 |
| `/api/compare` | POST | 方案比价 |
| `/api/agentic_chat` | POST | Agent 对话 |
| `/api/parse` | POST | 自然语言解析 |
| `/api/upload_data` | POST | 上传数据文件 |
| `/api/export_docx` | POST | 导出 Word 报告 |

API 文档：`http://localhost:8000/docs`

## 📁 项目结构

```
├── backend/
│   ├── main.py              FastAPI 入口
│   ├── freight_service.py   核心业务（匹配/计费/评分/推荐）
│   ├── graph_router.py      转运路径搜索
│   ├── llm_service.py       LLM 服务（解析/对话/反馈）
│   ├── models.py            数据模型
│   └── static/              前端构建产物
├── frontend/                 Vue 3 前端源码
├── data/                     CSV 费率数据
├── setup.bat                首次初始化
├── start.bat                一键启动
├── stop.bat                 停止服务
├── run.py                   Python 启动脚本
└── .env.example             环境配置模板
```
