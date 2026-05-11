# 运输方案比价与优化智能体

基于大模型的物流运输方案比价与优化系统。根据用户输入的订单信息，自动匹配承运商运输报价，完成运费核算与多方案比价，最终推荐符合要求的最优运输方案。

## 项目概述

本项目为华南理工大学软件学院 2024 级软件开发综合实训项目，对应百景大赛赛题「运输方案比价与优化智能体」。系统聚焦于实际物流场景，通过智能匹配和成本计算，提升运输方案选择的效率与准确性。

### 核心功能

- **订单信息录入**：支持用户输入货物总重量、起运港代码、目的港代码及最大运输天数。
- **承运商方案匹配**：根据订单信息从费率表中自动筛选符合条件的运输方案。
- **运输成本计算**：严格遵循行业计费规则 `Cost = max(Min_Cost, Rate × Weight)` 进行精确核算。
- **最优方案推荐**：在满足时效要求的前提下，推荐成本最低的运输方案。

### 技术栈

| 层级   | 技术                                    |
|--------|----------------------------------------|
| 前端   | Vue.js 3、Element Plus                  |
| 后端   | Python FastAPI                         |
| 数据处理 | Pandas                                |
| 数据源 | 承运商费率表（CSV）                     |

## 项目结构

```
freight-comparison-agent/
├── backend/
│   ├── main.py              # FastAPI 主应用入口
│   ├── models.py            # 数据模型定义
│   ├── freight_service.py   # 核心业务逻辑（方案筛选、成本计算、推荐）
│   └── requirements.txt     # Python 依赖声明
├── frontend/
│   ├── src/
│   │   ├── main.js          # Vue 应用入口
│   │   ├── App.vue          # 根组件
│   │   └── components/      # Vue 组件
│   │       ├── AppHeader.vue
│   │       ├── StatisticsCard.vue
│   │       ├── CompareForm.vue
│   │       ├── ResultTable.vue
│   │       ├── RecommendCard.vue
│   │       └── ExportCard.vue
│   ├── index.html           # HTML 入口
│   ├── package.json         # 前端依赖配置
│   └── vite.config.js       # Vite 构建配置
├── data/
│   └── FreightRates.csv     # 承运商费率数据
├── run.py                   # 一键启动脚本
├── requirements.txt         # 项目整体依赖
├── .gitignore               # Git 忽略规则
└── README.md                # 项目说明文档
```

## 快速开始

### 环境要求

- Python 3.9 及以上版本
- Node.js 18 及以上版本

### 一键启动（推荐）

**Windows 用户：**

双击运行 `start.bat`，脚本会自动安装依赖并启动服务。

**或使用命令行：**

```bash
# 克隆项目
git clone https://github.com/JiangLin1297/Freight-Comparison-and-Optimization-Agent.git
cd Freight-Comparison-and-Optimization-Agent

# 一键启动（自动安装依赖）
python run.py
```

服务启动后，访问以下地址：

- **前端界面**：http://localhost:3000
- **后端 API**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs

### 手动启动

如果一键启动遇到问题，可以手动操作：

```bash
# 1. 安装后端依赖
pip install -r requirements.txt

# 2. 安装前端依赖
cd frontend
npm install
cd ..

# 3. 启动后端（终端1）
cd backend
python main.py

# 4. 启动前端（终端2）
cd frontend
npm run dev
```

### 构建生产版本

```bash
cd frontend
npm run build
```

构建后的文件将输出到 `backend/static/`，后端会自动提供静态文件服务。

## 数据说明

### 承运商费率表 (`FreightRates.csv`)

| 字段               | 说明             | 示例                      |
|--------------------|------------------|---------------------------|
| Carrier            | 承运商代码       | V444_0 ~ V444_9           |
| Orig_Port          | 起运港代码       | PORT02 ~ PORT11           |
| Dest_Port          | 目的港代码       | PORT09                    |
| Min_Weight_Quant   | 最小重量（kg）   | 0                         |
| Max_Weight_Quant   | 最大重量（kg）   | 99999.99                  |
| Service_Level      | 服务级别         | DTD（门到门） / DTP（门到港） |
| Min_Cost           | 最低费用         | 43.23                     |
| Rate               | 费率             | 0.7132                    |
| Mode_DSC           | 运输方式         | AIR（空运） / GROUND（陆运） |
| TPT_Day_Count      | 运输天数         | 0 ~ 14                    |
| Carrier_Type       | 承运商类型       | V88888888_0 / V888888883_1 |

**数据规模**：共 1540 条报价记录，涵盖 9 家承运商、10 个起运港。

### 计费规则

```
总成本 = max(最低费用， 费率 × 重量)
```

**计算示例**：

> 费率：0.7132  
> 最低费用：43.23  
> 货物重量：100 kg  
> 计算过程：max(43.23, 0.7132 × 100) = max(43.23, 71.32) = 71.32

## API 接口

### 获取可用港口列表

```http
GET /api/ports
```

返回所有可选的起运港与目的港代码。

### 获取数据概览统计

```http
GET /api/statistics
```

返回承运商数量、报价条目数等统计信息。

### 执行方案比价

```http
POST /api/compare
```

**请求体示例**：

```json
{
  "weight": 100,
  "orig_port": "PORT08",
  "dest_port": "PORT09",
  "max_days": 5
}
```

**响应说明**：返回符合重量、起运港、目的港及最大运输天数约束的所有方案，并按成本升序排列，首个为推荐方案。

### 导出报告

```http
POST /api/export
```

将当前比价结果导出为文件（格式视具体实现而定，如 CSV/Excel）。

## 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   前端界面       │────▶│   FastAPI 后端   │────▶│   业务逻辑层     │
│   Vue.js 3      │     │   RESTful API   │     │  - 方案筛选     │
│   Element Plus  │     │                 │     │  - 成本计算     │
└─────────────────┘     └─────────────────┘     │  - 方案推荐     │
                                                └────────┬────────┘
                                                         │
                                                ┌────────▼────────┐
                                                │     数据层       │
                                                │   Pandas/CSV    │
                                                │  FreightRates   │
                                                └─────────────────┘
```

## 开发计划

| 阶段   | 时间            | 核心任务                         | 交付物                           |
|--------|-----------------|----------------------------------|----------------------------------|
| 第 1 周 | 05-06 ～ 05-12  | 赛题理解、原型设计               | 需求分析说明书、前端原型         |
| 第 2 周 | 05-13 ～ 05-19  | 基线智能体实现、前后端联调       | 基线评测报告、可运行系统         |
| 第 3 周 | 05-20 ～ 05-26  | 功能增强与优化                   | 优化对比报告                     |
| 第 4 周 | 05-27 ～ 06-02  | 系统测试与评测                   | 测试报告                         |
| 第 5 周 | 06-03 ～ 06-09  | BadCase 分析与迭代              | 优化报告                         |
| 第 6 周 | 06-10 ～ 06-15  | 完整交付与答辩                   | 最终系统、演示视频               |

## 评测指标

| 指标               | 目标值     |
|--------------------|------------|
| 方案匹配准确率      | 100%       |
| 运费计算准确率      | 100%       |
| 推荐方案合理率      | ≥ 85%      |
| 系统响应时间        | < 5 秒      |

## 许可证

本项目为华南理工大学软件学院实训项目，仅供学习交流使用。

## 致谢

- 华南理工大学软件学院
- 百景大赛组委会
- 指导教师：郭芬、杜卿