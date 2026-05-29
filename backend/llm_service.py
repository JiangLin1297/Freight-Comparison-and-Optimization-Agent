import os
import json
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# 港口名称 -> PORT代码 映射（支持中文名、英文名、常见别名）
PORT_NAME_MAP = {
    # 中文港口名
    "上海": "PORT02", "上海港": "PORT02", "上海港码头": "PORT02",
    "深圳": "PORT03", "深圳港": "PORT03", "深圳港码头": "PORT03",
    "广州": "PORT04", "广州港": "PORT04", "广州港码头": "PORT04",
    "宁波": "PORT05", "宁波港": "PORT05", "宁波舟山港": "PORT05",
    "青岛": "PORT06", "青岛港": "PORT06",
    "天津": "PORT07", "天津港": "PORT07",
    "大连": "PORT08", "大连港": "PORT08",
    "厦门": "PORT09", "厦门港": "PORT09",
    "香港": "PORT10", "香港港": "PORT10", "HK": "PORT10",
    "釜山": "PORT11", "釜山港": "PORT11", "BUSAN": "PORT11",
    # 英文港口名
    "SHANGHAI": "PORT02", "SHENZHEN": "PORT03", "GUANGZHOU": "PORT04",
    "NINGBO": "PORT05", "QINGDAO": "PORT06", "TIANJIN": "PORT07",
    "DALIAN": "PORT08", "XIAMEN": "PORT09", "FUZHOU": "PORT09",
    "BEIHAI": "PORT09", "ZHUHAI": "PORT09",
}

# 有效的起运港列表
VALID_ORIG_PORTS = {"PORT02", "PORT03", "PORT04", "PORT05", "PORT06", "PORT07", "PORT08", "PORT09", "PORT10", "PORT11"}


def resolve_port_name(text: str) -> Optional[str]:
    """将自然语言港口名解析为PORT代码，支持直接PORT代码和中文/英文名称"""
    text_upper = text.strip().upper()
    # 直接是 PORT 代码
    if re.match(r'^PORT\d{2}$', text_upper):
        return text_upper if text_upper in VALID_ORIG_PORTS else None
    # 查映射表（大小写不敏感）
    for name, code in PORT_NAME_MAP.items():
        if text.strip() in (name, name.upper(), name.lower()):
            return code
    return None


def extract_ports_from_text(text: str):
    """从自然语言文本中提取起运港和目的港，支持中文港口名和PORT代码"""
    orig_port = None
    dest_port = None

    # 模式1: "从XXX到YYY" / "从XXX运/发/寄...到YYY"
    route_pattern = re.search(
        r'从\s*([^\s，,到发运寄]+)\s*(?:.*?到)\s*([^\s，,发运寄]+)',
        text
    )
    if route_pattern:
        orig_port = resolve_port_name(route_pattern.group(1))
        dest_port = resolve_port_name(route_pattern.group(2))

    # 模式2: 匹配 "PORTxx" 代码（兜底）
    if not orig_port and not dest_port:
        port_codes = re.findall(r'PORT(\d{2})', text, re.IGNORECASE)
        if len(port_codes) >= 2:
            orig_port = f"PORT{port_codes[0]}"
            dest_port = f"PORT{port_codes[1]}"
        elif len(port_codes) == 1:
            orig_port = f"PORT{port_codes[0]}"

    # 模式3: 逐词匹配中文港口名（兜底）
    if not orig_port:
        for name, code in PORT_NAME_MAP.items():
            if len(name) >= 2 and name in text:
                if orig_port is None:
                    orig_port = code
                elif dest_port is None and code != orig_port:
                    dest_port = code
                    break

    return orig_port, dest_port


@dataclass
class ConversationSession:
    """多轮对话会话"""
    session_id: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    current_state: str = "initial"  # initial, parsing, confirming, completed
    partial_data: Dict[str, Any] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    user_feedback: str = ""


class LLMService:
    """LLM 服务 - 小米 MiMo v2 Token Plan，支持工具调用"""

    def __init__(self, tool_manager=None):
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.model = os.getenv("DASHSCOPE_MODEL", "mimo-v2.5")
        self.base_url = "https://token-plan-cn.xiaomimimo.com/v1"
        self.client = None
        self.sessions: Dict[str, ConversationSession] = {}
        self.tool_manager = tool_manager
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                self.client = None

    def chat(self, user_message: str, system_prompt: str = None) -> str:
        """调用 LLM 进行对话"""
        if not self.client:
            return "错误：未配置 DASHSCOPE_API_KEY，请在 .env 文件中填写 API Key"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM 调用失败: {str(e)}"

    def chat_with_tools(self, user_message: str, session_id: str = None) -> Dict[str, Any]:
        """
        带工具调用的对话
        返回: {"response": "回复文本", "tool_calls": [{"tool": "工具名", "parameters": {...}}]}
        """
        if not self.client:
            return {
                "response": "错误：未配置 DASHSCOPE_API_KEY",
                "tool_calls": [],
                "configured": False
            }

        # 获取工具Schema
        tools_schema = self.tool_manager.get_tools_schema() if self.tool_manager else []

        # 构建系统提示词
        system_prompt = f"""你是一个物流运输方案比价助手。你可以使用以下工具来帮助用户查询和分析运输方案。

## 可用工具
{json.dumps(tools_schema, ensure_ascii=False, indent=2)}

## 工具调用规则
1. 当用户需要查询运费、比价、获取港口信息等操作时，使用相应的工具
2. 工具调用返回结果后，用清晰易懂的语言向用户解释结果
3. 如果用户的问题不需要工具调用，直接回答即可

## 重要：优先级自动识别规则
**你必须仔细分析用户的输入，自动识别优先级偏好，并在调用 compare_freight 工具时设置 priority 参数：**

### 时效优先（priority: "time"）
当用户表达以下意思时，设置 priority="time"：
- "尽快"、"越快越好"、"最快"、"最快速度"
- "时间优先"、"时效优先"、"速度优先"
- "加急"、"紧急"、"特急"、"急"
- "最快到达"、"最短时间"、"时效第一"
- "马上要"、"急需"、"很赶时间"
- "能多快就多快"、"越早越好"

### 成本优先（priority: "cost"）
当用户表达以下意思时，设置 priority="cost"：
- "最省钱"、"越便宜越好"、"最便宜"、"最低价"
- "成本优先"、"价格优先"、"省钱"
- "经济实惠"、"性价比高"、"划算"
- "预算有限"、"控制成本"、"费用最低"
- "能省则省"、"便宜点的"

### 均衡模式（不设置 priority 或 priority=null）
当用户没有明确偏好时，不设置 priority 参数，使用默认均衡模式

## 响应格式
返回JSON格式：
{{
  "response": "你的回复文本（对工具结果的解释或直接回答）",
  "tool_calls": [
    {{
      "tool": "工具名称",
      "parameters": {{"参数名": "参数值"}}
    }}
  ]
}}

如果不需要调用工具，tool_calls为空数组[]。

## 示例

### 示例1：普通查询
用户："从大连运100kg货物到厦门，多少钱？"
响应：
{{
  "response": "让我为您查询从大连（PORT08）到厦门（PORT09）100kg货物的运费方案。",
  "tool_calls": [
    {{
      "tool": "compare_freight",
      "parameters": {{"weight": 100, "orig_port": "PORT08", "dest_port": "PORT09"}}
    }}
  ]
}}

### 示例2：时效优先
用户："从上海运50kg到深圳，越快越好"
响应：
{{
  "response": "好的，我理解您需要尽快送达。让我为您查询从上海（PORT02）到深圳（PORT03）50kg货物的运费方案，优先推荐最快的方案。",
  "tool_calls": [
    {{
      "tool": "compare_freight",
      "parameters": {{"weight": 50, "orig_port": "PORT02", "dest_port": "PORT03", "priority": "time"}}
    }}
  ]
}}

### 示例3：成本优先
用户："从天津运200kg到香港，最省钱的方案"
响应：
{{
  "response": "好的，我理解您希望控制成本。让我为您查询从天津（PORT07）到香港（PORT10）200kg货物的运费方案，优先推荐最经济的方案。",
  "tool_calls": [
    {{
      "tool": "compare_freight",
      "parameters": {{"weight": 200, "orig_port": "PORT07", "dest_port": "PORT10", "priority": "cost"}}
    }}
  ]
}}

### 示例4：带时效要求的查询
用户："从广州运100kg到厦门，3天内到，越便宜越好"
响应：
{{
  "response": "好的，我理解您需要在3天内送达且希望费用最低。让我为您查询从广州（PORT04）到厦门（PORT09）100kg货物的运费方案。",
  "tool_calls": [
    {{
      "tool": "compare_freight",
      "parameters": {{"weight": 100, "orig_port": "PORT04", "dest_port": "PORT09", "max_days": 3, "priority": "cost"}}
    }}
  ]
}}
"""

        # 获取或创建会话
        session = self._get_or_create_session(session_id)

        # 构建消息
        messages = [{"role": "system", "content": system_prompt}]

        # 添加历史对话（保留最近5轮）
        if session.messages:
            recent_messages = session.messages[-10:]  # 最近5轮（10条消息）
            messages.extend(recent_messages)

        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=1500,
            )
            content = response.choices[0].message.content.strip()

            # 尝试解析JSON响应
            try:
                # 提取JSON内容
                json_content = self._extract_json(content)
                if json_content:
                    result = json.loads(json_content)
                else:
                    result = json.loads(content)

                # 更新会话历史
                session.messages.append({"role": "user", "content": user_message})
                session.messages.append({"role": "assistant", "content": content})

                return {
                    "response": result.get("response", ""),
                    "tool_calls": result.get("tool_calls", []),
                    "configured": True,
                    "session_id": session.session_id
                }

            except json.JSONDecodeError:
                # 如果不是JSON格式，作为普通对话处理
                session.messages.append({"role": "user", "content": user_message})
                session.messages.append({"role": "assistant", "content": content})

                return {
                    "response": content,
                    "tool_calls": [],
                    "configured": True,
                    "session_id": session.session_id
                }

        except Exception as e:
            return {
                "response": f"处理失败: {str(e)}",
                "tool_calls": [],
                "configured": True,
                "error": str(e)
            }

    def parse_order(self, text: str, session_id: str = None) -> Dict[str, Any]:
        """将自然语言描述解析为结构化订单数据，支持CoT思维链和多轮对话"""
        if not self.client:
            # 无API key时使用简单的正则解析
            return self._fallback_parse(text)

        # CoT思维链系统提示词
        system_prompt = """你是一个物流订单信息提取助手。请严格按照以下三个步骤进行分析：

## 步骤一：分析问题类型
首先判断用户输入属于以下哪种场景：
1. **完整订单描述** - 包含重量、起运港、目的港，可能包含时效要求
2. **部分信息描述** - 缺少必要字段（如只有港口没有重量）
3. **模糊表达** - 使用非标准术语（如"一批货"、"很快到"）
4. **复杂场景** - 包含多个条件、比较、特殊要求

## 步骤二：提取关键信息
从用户描述中识别并提取以下信息：
- **货物重量**：数字 + 单位（kg/公斤/吨/斤）
- **起运港**：港口名称或PORT代码
- **目的港**：港口名称或PORT代码
- **时效要求**：天数或模糊表述
- **优先级偏好**：用户更看重速度还是成本

港口名称与代码对应关系：
- 上海/SHANGHAI -> PORT02
- 深圳/SHENZHEN -> PORT03
- 广州/GUANGZHOU -> PORT04
- 宁波/NINGBO -> PORT05
- 青岛/QINGDAO -> PORT06
- 天津/TIANJIN -> PORT07
- 大连/DALIAN -> PORT08
- 厦门/XIAMEN -> PORT09
- 香港/HK -> PORT10
- 釜山/BUSAN -> PORT11

可用的起运港：PORT02, PORT03, PORT04, PORT05, PORT06, PORT07, PORT08, PORT09, PORT10, PORT11
可用的目的港：PORT02, PORT03, PORT04, PORT05, PORT06, PORT07, PORT08, PORT09, PORT10, PORT11

## 步骤三：生成JSON
根据分析结果生成JSON响应，包含以下字段：
```json
{
  "analysis": "问题类型分析结果",
  "extracted_info": {
    "weight": 数字或null,
    "orig_port": "PORT代码或null",
    "dest_port": "PORT代码或null",
    "max_days": 数字或null,
    "priority": "time或cost或null"
  },
  "confidence": "high/medium/low",
  "missing_fields": ["缺失的必要字段列表"],
  "guidance": "给用户的引导提示（如果有缺失或模糊信息）"
}
```

## 重要规则
1. 重量必须是数字（如果用户说"斤"需要除以2换算为kg，"吨"需要乘以1000）
2. 港口代码必须大写
3. 如果用户使用中文港口名，必须转换为对应的PORT代码
4. 如果信息缺失，对应字段设为null，并在guidance中提示用户补充
5. 最大天数(max_days)识别规则：
   - 识别"3天"、"5天"、"7天"等基本格式
   - 识别"最大3天"、"最多5天"、"不超过7天"等带修饰词的格式
   - 识别"3天内"、"5天以内"、"3天内到达"等带后缀的格式
   - 识别"3个工作日"、"5个工作日"等格式
   - 识别"1周"、"2周"、"3周"等周格式（自动转换为天数，1周=7天）
   - 识别"半个月"、"一个月"等中文数字月格式（自动转换为天数，1个月=30天）
   - 重要：当用户使用"尽快"、"加急"、"紧急"、"特急"等模糊时间表达时，不要设置max_days，而是设置priority="time"
   - 重要：当用户使用"普通"、"常规"、"一般"等表达时，不要设置max_days，保持为null
   - 只有用户明确提到具体天数时才设置max_days（如"3天内"、"5天以内"）
   - 如果用户没有明确提到时间要求，设为null
6. 优先级(priority)识别规则（非常重要！必须仔细识别）：

   **时效优先（priority设为"time"）- 当用户表达以下意思时：**
   - 直接表达："越快越好"、"最快"、"最快速度"、"尽快"、"尽早"
   - 时间优先："时间优先"、"时效优先"、"速度优先"
   - 紧急需求："加急"、"紧急"、"特急"、"急"、"急需"、"很赶时间"
   - 到达要求："最快到达"、"最短时间"、"时效第一"、"能多快就多快"
   - 期望表达："越早越好"、"马上要"、"立即"、"马上"

   **成本优先（priority设为"cost"）- 当用户表达以下意思时：**
   - 直接表达："最省钱"、"越便宜越好"、"最便宜"、"最低价"
   - 成本优先："成本优先"、"价格优先"、"省钱"、"费用最低"
   - 经济实惠："经济实惠"、"性价比高"、"划算"
   - 预算考虑："预算有限"、"控制成本"、"能省则省"、"省钱为主"
   - 期望表达："便宜点的"、"便宜一些"、"少花点钱"、"价格低的"

   **均衡模式（priority设为null）：**
   - 如果用户没有明确的优先级偏好，设为null（系统默认按综合评分推荐）
6. confidence设置规则：
   - high：所有必要字段（重量、起运港、目的港）都有明确值
   - medium：有部分字段缺失或模糊
   - low：大部分字段缺失或理解困难
7. guidance设置规则：
   - 如果有缺失字段，引导用户补充
   - 如果有模糊信息，引导用户澄清
   - 如果confidence为low，给出具体的输入示例"""

        # 获取或创建会话
        session = self._get_or_create_session(session_id)

        # 构建消息
        messages = [{"role": "system", "content": system_prompt}]

        # 添加历史对话
        if session.messages:
            messages.extend(session.messages)

        messages.append({"role": "user", "content": text})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=800,
            )
            content = response.choices[0].message.content.strip()

            # 尝试提取JSON
            json_content = self._extract_json(content)
            if json_content:
                result = json.loads(json_content)
            else:
                # 尝试解析整个内容作为JSON
                result = json.loads(content)

            # 验证并修正港口代码
            result = self._validate_ports(result, text)

            # 更新会话状态
            session.messages.append({"role": "user", "content": text})
            session.messages.append({"role": "assistant", "content": content})

            # 检查是否需要引导用户补充信息
            if result.get("confidence") == "low" or len(result.get("missing_fields", [])) > 0:
                session.current_state = "parsing"
                session.partial_data = result.get("extracted_info", {})
                session.missing_fields = result.get("missing_fields", [])
                session.user_feedback = result.get("guidance", "")
            else:
                session.current_state = "completed"
                session.partial_data = result.get("extracted_info", {})

            return {
                "weight": result.get("extracted_info", {}).get("weight"),
                "orig_port": result.get("extracted_info", {}).get("orig_port"),
                "dest_port": result.get("extracted_info", {}).get("dest_port"),
                "max_days": result.get("extracted_info", {}).get("max_days"),
                "priority": result.get("extracted_info", {}).get("priority"),
                "analysis": result.get("analysis", ""),
                "confidence": result.get("confidence", "high"),
                "missing_fields": result.get("missing_fields", []),
                "guidance": result.get("guidance", ""),
                "session_id": session.session_id
            }

        except Exception as e:
            # 解析失败时使用fallback
            fallback_result = self._fallback_parse(text)
            fallback_result["confidence"] = "low"
            fallback_result["guidance"] = "解析失败，请检查输入格式。建议使用：'从[起运港]运输[重量]货物到[目的港]，[天数]天内到达'"
            return fallback_result

    def _get_or_create_session(self, session_id: str = None) -> ConversationSession:
        """获取或创建会话"""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]

        # 创建新会话
        import uuid
        new_session_id = session_id or str(uuid.uuid4())
        session = ConversationSession(session_id=new_session_id)
        self.sessions[new_session_id] = session
        return session

    def _extract_json(self, text: str) -> Optional[str]:
        """从文本中提取JSON内容"""
        # 尝试提取```json```代码块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if json_match:
            return json_match.group(1).strip()

        # 尝试提取{...}内容
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            return brace_match.group(0)

        return None

    def continue_conversation(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """继续多轮对话"""
        if session_id not in self.sessions:
            return {"error": "会话不存在，请重新开始", "session_id": session_id}

        session = self.sessions[session_id]

        # 根据当前状态处理输入
        if session.current_state == "parsing":
            # 合并用户补充的信息
            combined_text = self._combine_session_info(session, user_input)
            return self.parse_order(combined_text, session_id)
        else:
            # 新的查询
            return self.parse_order(user_input, session_id)

    def _combine_session_info(self, session: ConversationSession, new_input: str) -> str:
        """合并会话中的信息和新输入"""
        parts = []

        # 添加已有信息
        if session.partial_data.get("weight"):
            parts.append(f"{session.partial_data['weight']}kg货物")
        if session.partial_data.get("orig_port"):
            parts.append(f"从{session.partial_data['orig_port']}")
        if session.partial_data.get("dest_port"):
            parts.append(f"到{session.partial_data['dest_port']}")
        if session.partial_data.get("max_days"):
            parts.append(f"{session.partial_data['max_days']}天内到达")

        # 添加新输入
        parts.append(new_input)

        return "，".join(parts)

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        if session_id not in self.sessions:
            return {"status": "not_found"}

        session = self.sessions[session_id]
        return {
            "status": session.current_state,
            "partial_data": session.partial_data,
            "missing_fields": session.missing_fields,
            "guidance": session.user_feedback
        }

    def _validate_ports(self, result: Dict[str, Any], text: str) -> Dict[str, Any]:
        """验证LLM返回的港口代码，无效时尝试从文本中重新提取"""
        orig = result.get("orig_port")
        dest = result.get("dest_port")

        # 验证起运港
        if orig and orig.upper() not in VALID_ORIG_PORTS:
            # LLM可能返回了中文港口名，尝试解析
            resolved = resolve_port_name(orig)
            result["orig_port"] = resolved
        elif orig:
            result["orig_port"] = orig.upper()

        # 验证目的港
        if dest and dest.upper() not in VALID_ORIG_PORTS:
            resolved = resolve_port_name(dest)
            result["dest_port"] = resolved
        elif dest:
            result["dest_port"] = dest.upper()

        # 如果港口仍然缺失，从文本中提取
        if not result.get("orig_port") or not result.get("dest_port"):
            text_orig, text_dest = extract_ports_from_text(text)
            if not result.get("orig_port"):
                result["orig_port"] = text_orig
            if not result.get("dest_port"):
                result["dest_port"] = text_dest

        # 如果只有起运港没有目的港，默认PORT09
        if result.get("orig_port") and not result.get("dest_port"):
            result["dest_port"] = "PORT09"

        return result

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """无API时的解析，支持中文港口名和PORT代码"""
        result = {"weight": None, "orig_port": None, "dest_port": None, "max_days": None, "priority": None}

        # 提取重量（支持kg/公斤/千克/斤）
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|公斤|千克)', text, re.IGNORECASE)
        if weight_match:
            result["weight"] = float(weight_match.group(1))
        else:
            # 也支持"斤"
            jin_match = re.search(r'(\d+(?:\.\d+)?)\s*斤', text, re.IGNORECASE)
            if jin_match:
                result["weight"] = float(jin_match.group(1)) / 2

        # 使用通用函数提取港口
        orig_port, dest_port = extract_ports_from_text(text)
        result["orig_port"] = orig_port
        result["dest_port"] = dest_port

        # 如果只有起运港没有目的港，默认PORT09
        if result["orig_port"] and not result["dest_port"]:
            result["dest_port"] = "PORT09"

        # 提取天数（支持多种表达方式）
        days_patterns = [
            r'(\d+)\s*(?:天|日|days?|工作日|个工作日)',  # 基本格式：3天、5日、7days、3工作日
            r'(?:最大|最多|不超过|限|要求|需要|希望)\s*(\d+)\s*(?:天|日|days?|工作日|个工作日)',  # 带修饰词：最大3天、最多5天
            r'(\d+)\s*(?:天|日|days?|工作日|个工作日)\s*(?:内|以内|之内|到达|送达)',  # 带后缀：3天内、5天以内
            r'(\d+)\s*(?:周|星期|weeks?)',  # 周格式：1周、2星期、3weeks
            r'(?:最大|最多|不超过|限|要求|需要|希望)\s*(\d+)\s*(?:周|星期|weeks?)',  # 带修饰词的周格式
            r'(\d+)\s*(?:周|星期|weeks?)\s*(?:内|以内|之内)',  # 带后缀的周格式
            r'(半|一|二|三|四|五|六|七|八|九|十)\s*(?:个月|月)',  # 中文数字月格式：半个月、一个月
            r'(?:最大|最多|不超过|限|要求|需要|希望)\s*(半|一|二|三|四|五|六|七|八|九|十)\s*(?:个月|月)',  # 带修饰词的中文数字月格式
        ]
        # 中文数字映射
        cn_num_map = {'半': 0.5, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        for pattern in days_patterns:
            days_match = re.search(pattern, text, re.IGNORECASE)
            if days_match:
                days_str = days_match.group(1)
                # 处理中文数字
                if days_str in cn_num_map:
                    days = cn_num_map[days_str]
                else:
                    days = int(days_str)
                # 如果是周格式，转换为天数
                if '周' in pattern or '星期' in pattern or 'weeks?' in pattern:
                    days = days * 7
                # 如果是月格式，转换为天数（按30天计算）
                elif '个月' in pattern or '月' in pattern:
                    days = days * 30
                result["max_days"] = int(days)
                break

        # 识别优先级偏好（注意：不再将模糊时间表达转换为具体天数）
        time_priority_patterns = [
            r'尽快', r'加急', r'紧急', r'特急', r'越快越好', r'速度优先', r'最快',
            r'时间优先', r'尽快送达', r'最快速度', r'最快到达', r'最短时间',
            r'时效第一', r'急', r'快', r'越早越好', r'马上要', r'立即', r'马上'
        ]
        cost_priority_patterns = [
            r'最省钱', r'越便宜越好', r'成本优先', r'最便宜', r'省钱', r'经济实惠',
            r'价格优先', r'便宜', r'低成本', r'预算有限', r'控制成本', r'能省则省',
            r'性价比高', r'划算'
        ]

        for pattern in time_priority_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                result["priority"] = "time"
                break

        if result["priority"] is None:
            for pattern in cost_priority_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    result["priority"] = "cost"
                    break

        return result

    def is_configured(self) -> bool:
        """检查是否已配置 API Key"""
        return bool(self.api_key)
