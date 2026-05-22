# Prompt 和测试数据集说明

## 文件说明

### 1. prompt.md - 系统提示词

这是运输方案比价与优化智能体的完整系统提示词，包含：

- **角色定义**：智能体的职责和能力
- **计费规则**：运输成本计算公式和示例
- **输入参数**：货物重量、起运港、目的港、最大运输天数
- **输出格式**：标准化的结果展示格式
- **处理流程**：从需求解析到方案推荐的完整流程
- **异常处理**：各种异常情况的处理方式
- **交互示例**：用户与智能体的对话示例

### 2. testdataset.csv - 测试数据集

包含 70 个测试用例，覆盖以下场景：

| 类别 | 数量 | 说明 |
|------|------|------|
| 正常查询 | 4 | 标准的运输需求查询 |
| 单位转换 | 2 | 吨转千克等单位转换 |
| 边界条件 | 6 | 重量、时效等边界值测试 |
| 无时效要求 | 2 | 没有时间约束的查询 |
| 空运/陆运优先 | 2 | 特定运输方式的需求 |
| 服务级别 | 2 | 门到门/门到港服务 |
| 异常输入 | 6 | 无效参数、错误输入 |
| 模糊输入 | 4 | 缺少参数、中文输入 |
| 成本计算 | 4 | 不同成本场景验证 |
| 时效过滤 | 3 | 不同时效要求测试 |
| 多方案对比 | 2 | 方案数量和排序验证 |
| 推荐逻辑 | 3 | 推荐算法验证 |
| 综合场景 | 3 | 完整业务流程测试 |
| 港口覆盖 | 10 | 所有起运港测试 |
| 承运商覆盖 | 10 | 所有承运商测试 |
| 运输方式 | 2 | 空运/陆运筛选 |
| 服务级别 | 2 | DTD/DTP筛选 |
| 自然语言 | 4 | 口语化、省略表达 |

## 测试数据集字段说明

| 字段 | 说明 |
|------|------|
| test_id | 测试用例编号（TC001-TC070） |
| category | 测试类别 |
| description | 测试描述 |
| user_input | 用户输入的自然语言 |
| weight | 货物重量（kg） |
| orig_port | 起运港代码 |
| dest_port | 目的港代码 |
| max_days | 最大运输天数（可为空） |
| expected_plans_count | 预期方案数量（待填充） |
| expected_recommend_carrier | 预期推荐承运商（待填充） |
| expected_cost_formula | 预期成本公式（待填充） |
| expected_min_cost | 预期最低费用（待填充） |
| notes | 备注说明 |

## 使用方法

### 1. 使用 Prompt

将 `prompt.md` 中的内容作为系统提示词配置到智能体中：

```python
system_prompt = open("prompt.md", "r", encoding="utf-8").read()

response = llm.chat(
    system=system_prompt,
    messages=[{"role": "user", "content": user_input}]
)
```

### 2. 使用测试数据集

#### 方式一：手动测试

按照 `testdataset.csv` 中的 `user_input` 列，逐条输入到系统中，验证输出是否符合预期。

#### 方式二：自动化测试

```python
import pandas as pd

# 加载测试数据
test_data = pd.read_csv("testdataset.csv")

# 遍历测试用例
for _, row in test_data.iterrows():
    test_id = row['test_id']
    user_input = row['user_input']

    # 调用智能体
    response = agent.process(user_input)

    # 验证结果
    # 检查方案数量、推荐承运商、成本计算等
    validate_response(response, row)
```

### 3. 填充预期结果

运行系统后，将实际结果填入 `expected_*` 列：

```python
# 运行测试并记录结果
for _, row in test_data.iterrows():
    response = agent.process(row['user_input'])

    # 更新预期结果
    test_data.loc[row.name, 'expected_plans_count'] = response['total_plans']
    test_data.loc[row.name, 'expected_recommend_carrier'] = response['recommendation']['carrier']
    # ...

# 保存更新后的测试数据
test_data.to_csv("testdataset_with_expected.csv", index=False)
```

## 测试覆盖度

### 功能覆盖

- [x] 需求解析功能
- [x] 参数校验功能
- [x] 方案匹配功能
- [x] 成本计算功能
- [x] 时效过滤功能
- [x] 方案排序功能
- [x] 推荐生成功能
- [x] 异常处理功能

### 数据覆盖

- [x] 所有 10 个起运港（PORT02-PORT11）
- [x] 所有 10 个目的港（PORT02-PORT11）
- [x] 所有 9 家承运商（V444_0-V444_9）
- [x] 空运和陆运两种运输方式
- [x] 门到门和门到港两种服务级别
- [x] 不同重量范围（1kg-100000kg）
- [x] 不同时效要求（1天-14天）

### 边界覆盖

- [x] 最小重量边界
- [x] 最大重量边界
- [x] 重量分界点（50kg、49.99kg、500kg、499.99kg）
- [x] 最小时效边界
- [x] 最大时效边界
- [x] 无效输入处理
- [x] 缺失参数处理

## 扩展建议

### 1. 增加测试用例

可以增加以下场景的测试：

- 更多港口组合
- 更多重量区间
- 更多时效要求
- 更多自然语言表达方式

### 2. 自动化验证

开发自动化测试脚本，自动验证：

- 方案匹配准确性
- 成本计算准确性
- 推荐方案合理性
- 响应时间性能

### 3. 性能测试

增加压力测试用例：

- 并发查询测试
- 大数据量测试
- 响应时间测试

## 参考资料

- [FreightRates.csv](data/FreightRates.csv) - 承运商费率表
- [freight_service.py](backend/freight_service.py) - 核心业务逻辑
- [API文档](http://localhost:8000/docs) - FastAPI 自动生成的接口文档
