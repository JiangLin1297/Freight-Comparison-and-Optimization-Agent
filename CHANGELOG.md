# 更新日志 (Changelog)

## 版本 2.0.0 - 2024-05-29

### 🎯 重大更新

本次更新实现了三大核心功能：多维度评分机制、数据覆盖范围扩展、Agentic工具调用框架。

---

## 📊 功能一：多维度评分机制

### 新增功能
- **加权评分算法**：实现 `Score = w1×成本 + w2×时效 + w3×服务评级` 的综合评分公式
- **自动权重配置**：根据用户选择的优先级自动调整权重
  - 时效优先：成本30% + 时效50% + 服务20%
  - 成本优先：成本50% + 时效30% + 服务20%
  - 均衡模式：成本40% + 时效30% + 服务30%
- **优先级三列显示**：界面上显示三个可点击的优先级选项（成本优先、时效优先、均衡模式）
- **评分明细展示**：每个方案都显示综合评分和评分明细（成本得分、时效得分、服务得分）

### 修改文件
- `backend/models.py` - 添加 ScoringWeights 模型、CarrierPlan 添加评分字段
- `backend/freight_service.py` - 实现 calculate_score() 和 recommend_plan() 方法
- `frontend/src/components/CompareForm.vue` - 添加优先级三列显示
- `frontend/src/components/ResultTable.vue` - 展示评分和评分明细

---

## 📈 功能二：数据覆盖范围扩展

### 新增功能
- **数据生成脚本**：`data/generate_extended_data.py` 自动生成扩展数据
- **更多目的港**：新增 PORT01-PORT07 共 7 个目的港
- **更多承运商**：新增 V555_0、V555_1、V666_0、V666_1、V777_0 共 5 个承运商
- **数据量扩展**：从 1540 条扩展到 9556 条记录
- **多数据源支持**：支持合并原始数据和扩展数据

### 数据统计
| 项目 | 原始数据 | 扩展数据 |
|------|----------|----------|
| 记录数 | 1,540 | 9,556 |
| 起运港 | 10个 | 10个 |
| 目的港 | 1个 | 8个 |
| 承运商 | 9个 | 14个 |

### 新增文件
- `data/generate_extended_data.py` - 数据生成脚本
- `data/FreightRates_extended.csv` - 扩展数据
- `data/FreightRates_combined.csv` - 合并数据

---

## 🤖 功能三：Agentic工具调用框架

### 新增功能
- **工具框架**：定义 ToolParameter、ToolDefinition、ToolManager 类
- **6个工具函数**：
  1. `compare_freight` - 执行运费比价查询
  2. `get_ports` - 获取可用港口列表
  3. `get_statistics` - 获取系统统计信息
  4. `export_report` - 生成比价报告
  5. `explain_cost` - 解释运费计算规则
  6. `compare_carriers` - 比较指定承运商
- **Agentic对话接口**：`/api/agentic_chat` 支持LLM自动调用工具
- **前端Agent模式**：聊天面板支持Agent模式/普通模式切换

### 新增文件
- `backend/tools.py` - 工具框架和6个工具函数

### 新增API
- `POST /api/agentic_chat` - Agentic对话接口
- `GET /api/tools` - 获取工具列表
- `POST /api/execute_tool` - 直接执行工具

---

## 🧠 功能四：智能语言识别增强

### 新增功能
- **优先级自动识别**：识别"尽快"、"最省钱"等词汇，自动设置优先级
- **去除默认天数**：当输入包含"尽快"等词汇时，不再默认设置 max_days=3
- **支持的关键词**：
  - 时效优先：越快越好、尽快、加急、紧急、最快到达、马上要等
  - 成本优先：最省钱、越便宜越好、经济实惠、预算有限等
- **前端展示**：智能输入组件显示识别出的优先级标签

### 修改文件
- `backend/llm_service.py` - 优化系统提示词，增强优先级识别
- `frontend/src/components/NLInput.vue` - 显示识别出的优先级

---

## 🎨 界面优化

### 比价表单
- 移除手动权重调整滑块
- 添加优先级三列显示（可点击切换）
- 按钮改为"推荐方案"
- 识别优先级后自动触发推荐

### 结果表格
- 新增"排名"、"服务评级"、"综合评分"、"评分明细"列
- 评分使用颜色标签：绿色(≥0.8)、黄色(≥0.6)、红色(<0.6)
- 悬停显示评分明细
- 显示当前使用的权重配置

### 聊天面板
- 新增Agent模式/普通模式切换
- 工具调用结果格式化展示
- 支持比价结果、港口列表、统计信息等展示

---

## 📝 文档更新

### 新增文档
- `CHANGELOG.md` - 更新日志（本文件）
- `IMPLEMENTATION_SUMMARY.md` - 实现总结
- `PRIORITY_RECOGNITION_GUIDE.md` - 优先级识别指南

---

## 🔧 技术改进

### 后端
- 优化评分算法，使用归一化加权评分
- 支持多数据源合并
- 工具管理器支持动态注册和执行
- LLM服务支持工具调用

### 前端
- 组件化设计，提高代码复用
- 响应式布局，支持移动端
- 交互优化，提升用户体验

---

## 🧪 测试验证

### 多维度评分测试
```
均衡模式: V444_2 - 5天 - $21.03 - 评级B - 评分0.861
时效优先: V444_6 - 2天 - $71.32 - 评级C - 评分0.846
成本优先: V444_2 - 5天 - $21.03 - 评级B - 评分0.88
```

### 数据扩展测试
```
查询新目的港 PORT01: 找到5个方案 ✓
查询新承运商 V555_0: 已存在 ✓
多港口查询: 全部成功 ✓
```

### 优先级识别测试
```
"尽快" → priority=time, max_days=null ✓
"越快越好" → priority=time, max_days=null ✓
"3天内" → max_days=3, priority=null ✓
"最省钱" → priority=cost, max_days=null ✓
```

### Agentic对话测试
```
查询运费: 工具调用成功 ✓
获取港口: 工具调用成功 ✓
获取统计: 工具调用成功 ✓
```

---

## 🚀 部署说明

### 环境要求
- Python 3.9+
- Node.js 18+
- 依赖包：见 requirements.txt

### 启动方式
```bash
# 一键启动
python run.py

# 或使用启动脚本
start.bat
```

### 访问地址
- 前端界面：http://localhost:3000（或3001/3002）
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

---

## 📋 文件清单

### 后端文件
- ✅ `backend/models.py` - 数据模型（添加评分字段）
- ✅ `backend/freight_service.py` - 业务逻辑（评分算法、数据扩展）
- ✅ `backend/llm_service.py` - LLM服务（优先级识别、工具调用）
- ✅ `backend/main.py` - API端点（新增Agentic接口）
- ✅ `backend/tools.py` - 工具框架（新增）

### 前端文件
- ✅ `frontend/src/App.vue` - 主应用（表单扩展）
- ✅ `frontend/src/components/CompareForm.vue` - 比价表单（优先级显示）
- ✅ `frontend/src/components/ResultTable.vue` - 结果表格（评分展示）
- ✅ `frontend/src/components/NLInput.vue` - 智能输入（优先级识别）
- ✅ `frontend/src/components/ChatPanel.vue` - 聊天面板（Agent模式）

### 数据文件
- ✅ `data/generate_extended_data.py` - 数据生成脚本（新增）
- ✅ `data/FreightRates_extended.csv` - 扩展数据（新增）
- ✅ `data/FreightRates_combined.csv` - 合并数据（新增）

### 文档文件
- ✅ `CHANGELOG.md` - 更新日志（新增）
- ✅ `IMPLEMENTATION_SUMMARY.md` - 实现总结（新增）
- ✅ `PRIORITY_RECOGNITION_GUIDE.md` - 优先级识别指南（新增）

---

## 🎉 总结

本次更新实现了：
1. ✅ 多维度评分机制 - 支持成本、时效、服务三维度加权评分
2. ✅ 数据覆盖范围扩展 - 目的港从1个扩展到8个，承运商从9个扩展到14个
3. ✅ Agentic工具调用框架 - 支持6个工具的对话式调用
4. ✅ 智能语言识别增强 - 自动识别优先级偏好
5. ✅ 界面优化 - 优先级三列显示、评分展示、Agent模式

系统现在能够：
- 根据用户需求灵活调整推荐策略
- 支持更多港口和承运商的查询
- 通过自然语言对话完成复杂查询任务
- 提供更智能、更准确的运输方案推荐
