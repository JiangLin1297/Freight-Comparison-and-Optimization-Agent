# 🚢 运输方案比价与优化智能体

> Freight Comparison and Optimization Agent

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-42b883.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Educational-orange.svg)]()

基于大语言模型的物流运费比价与优化系统。输入订单信息，自动匹配承运商报价，精确计算成本，推荐最优运输方案。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 📋 智能比价 | 输入重量、起运港、目的港、时效，自动匹配所有符合条件的方案 |
| 💰 精确计费 | 按行业公式 `Cost = max(Min_Cost, Rate × Weight)` 核算运费 |
| 🏆 最优推荐 | 在满足时效约束的前提下，推荐成本最低的运输方案 |
| 📊 报告导出 | 一键导出比价结果报告 |
| 🤖 LLM 智能体 | 集成大语言模型，支持自然语言交互 |

## 🛠 技术栈

```
前端: Vue 3 + Element Plus + Vite 5
后端: Python + FastAPI + Uvicorn
数据: Pandas + SQLAlchemy
LLM:  OpenAI SDK
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+

### 一键启动

```bash
# 克隆项目
git clone https://github.com/JiangLin1297/Freight-Comparison-and-Optimization-Agent.git
cd Freight-Comparison-and-Optimization-Agent

# 配置 API Key
echo "OPENAI_API_KEY=your_key_here" > .env

# 一键启动
python run.py
```

或双击 `start.bat`（Windows）。

启动后访问：
- 前端界面：`http://localhost:3000`
- 后端 API：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

### 手动启动

```bash
# 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 启动后端
cd backend && python main.py

# 启动前端 (新终端)
cd frontend && npm run dev
```

## 📁 项目结构

```
freight-comparison-agent/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── freight_service.py   # 核心业务逻辑
│   ├── llm_service.py       # LLM 服务
│   └── models.py            # 数据模型
├── frontend/
│   └── src/
│       ├── App.vue          # 根组件
│       └── components/      # 页面组件
├── data/
│   └── FreightRates.csv     # 运价数据 (1540 条, 9 家承运商)
├── run.py                   # 一键启动
└── requirements.txt         # Python 依赖
```

## 📡 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ports` | GET | 获取可用港口列表 |
| `/api/statistics` | GET | 获取数据概览统计 |
| `/api/compare` | POST | 执行方案比价 |
| `/api/export` | POST | 导出比价报告 |

**比价请求示例：**

```json
{
  "weight": 100,
  "orig_port": "PORT08",
  "dest_port": "PORT09",
  "max_days": 5
}
```

## 📊 数据说明

运价数据包含 **1540 条**报价记录，涵盖 **9 家**承运商、**10 个**起运港。

计费规则：
```
总成本 = max(最低费用, 费率 × 重量)
```

## 🏫 关于项目

华南理工大学软件学院 2024 级实训项目，参加百景大赛「运输方案比价与优化智能体」赛题。

**指导教师：** 郭芬、杜卿

---

<p align="center">Made with ❤️ by SCUT SE 2024</p>
