# CoT思维链解析测试用例

## 测试环境
- 前端：http://localhost:3001
- 后端：http://localhost:8000
- API文档：http://localhost:8000/docs

---

## 一、完整输入测试（高置信度）

### 测试1：标准格式
```
从上海运输100公斤货物到深圳，希望5天内到达
```
**预期结果**：
- confidence: high
- weight: 100
- orig_port: PORT02
- dest_port: PORT03
- max_days: 5

### 测试2：使用PORT代码
```
帮我查一下从 PORT02 到 PORT09，重量 100 公斤，5天内到达的运输方案
```
**预期结果**：
- confidence: high
- weight: 100
- orig_port: PORT02
- dest_port: PORT09
- max_days: 5

### 测试3：单位转换（吨）
```
2吨货物从广州发往青岛，10天内到就行
```
**预期结果**：
- confidence: high
- weight: 2000
- orig_port: PORT04
- dest_port: PORT06
- max_days: 10

### 测试4：单位转换（斤）
```
500斤货物从天津运到厦门，一周内到达
```
**预期结果**：
- confidence: high
- weight: 250
- orig_port: PORT07
- dest_port: PORT09
- max_days: 7

---

## 二、部分输入测试（中置信度 - 触发引导）

### 测试5：缺少重量
```
我要运一批货从上海到深圳
```
**预期结果**：
- confidence: medium
- weight: null
- missing_fields: ["weight"]
- guidance: 引导用户提供重量信息

### 测试6：缺少时效要求
```
100公斤货物从北京运到广州
```
**预期结果**：
- confidence: high（时效非必填）
- weight: 100
- orig_port: PORT07（天津）
- dest_port: PORT04（广州）
- max_days: null

### 测试7：模糊重量描述
```
有一批货要从上海发到深圳，大概几百公斤
```
**预期结果**：
- confidence: medium
- weight: null
- guidance: 引导用户提供精确重量

---

## 三、模糊表达测试（低置信度 - 强引导）

### 测试8：完全模糊
```
帮我找个便宜的运输方案
```
**预期结果**：
- confidence: low
- 多个字段缺失
- guidance: 提供完整的输入示例

### 测试9：非标准术语
```
尽快把东西从上面运到下面
```
**预期结果**：
- confidence: low
- guidance: 引导使用标准港口名称

---

## 四、复杂场景测试

### 测试10：多个条件
```
从上海运输100公斤货物到深圳，希望5天内到达，要最便宜的方案
```
**预期结果**：
- confidence: high
- 所有字段正确提取

### 测试11：比较表达
```
从上海或广州发货到深圳，100公斤，哪个更便宜？
```
**预期结果**：
- confidence: medium
- guidance: 引导明确起运港

### 测试12：时间模糊表达
```
从上海运100公斤货到深圳，不急，慢慢来
```
**预期结果**：
- confidence: high
- max_days: 14（普通/常规）

---

## 五、多轮对话测试

### 测试13：逐步补充信息
**第一轮输入**：
```
我要运货从上海到深圳
```
**预期**：提示缺少重量和时效

**第二轮输入**：
```
100公斤
```
**预期**：weight更新为100，仍提示时效可选

**第三轮输入**：
```
5天内到
```
**预期**：所有信息完整，confidence: high

---

## 六、边界情况测试

### 测试14：极端重量
```
100吨货物从上海运到深圳
```
**预期结果**：
- confidence: high
- weight: 100000

### 测试15：最小重量
```
0.5公斤小包裹从上海寄到深圳
```
**预期结果**：
- confidence: high
- weight: 0.5

### 测试16：相同起运港和目的港
```
从上海运100公斤货到上海
```
**预期结果**：
- 可能触发警告或引导

---

## 测试方法

### 方法1：前端界面测试
1. 打开 http://localhost:3001
2. 在"智能语音输入"区域输入测试用例
3. 点击"智能解析"按钮
4. 观察：
   - CoT分析过程显示
   - 置信度标签
   - 引导提示（如果有）
   - 解析结果预览

### 方法2：API直接测试
```python
import requests
import json

response = requests.post('http://localhost:8000/api/parse', json={
    'text': '从上海运输100公斤货物到深圳，希望5天内到达'
})
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

### 方法3：多轮对话测试
```python
import requests
import json

# 第一轮
response1 = requests.post('http://localhost:8000/api/parse', json={
    'text': '我要运货从上海到深圳'
})
session_id = response1.json()['data']['session_id']

# 第二轮
response2 = requests.post('http://localhost:8000/api/continue', json={
    'session_id': session_id,
    'message': '100公斤，5天内到'
})
print(json.dumps(response2.json(), indent=2, ensure_ascii=False))
```

---

## 评估指标

### 解析正确率提升
- 基线：简单正则匹配
- 优化后：CoT思维链 + 多轮对话
- 目标：解析正确率提升10%

### 用户体验改进
- ✅ 复杂语义理解能力增强
- ✅ 模糊输入识别和引导
- ✅ 多轮对话支持
- ✅ 置信度评估
- ✅ 逐步信息补充

---

## 注意事项

1. **API Key配置**：确保 .env 文件中配置了有效的 DASHSCOPE_API_KEY
2. **服务状态**：确保前后端服务正常运行
3. **编码问题**：Windows环境下可能出现中文乱码，但不影响功能
4. **会话有效期**：多轮对话会话在服务重启后会丢失
