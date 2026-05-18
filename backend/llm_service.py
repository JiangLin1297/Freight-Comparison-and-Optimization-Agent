import os
import json
import re
from typing import Optional, Dict, Any

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


class LLMService:
    """LLM 服务 - 小米 MiMo v2 Token Plan"""

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.model = os.getenv("DASHSCOPE_MODEL", "mimo-v2.5")
        self.base_url = "https://token-plan-cn.xiaomimimo.com/v1"
        self.client = None
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

    def parse_order(self, text: str) -> Dict[str, Any]:
        """将自然语言描述解析为结构化订单数据"""
        if not self.client:
            # 无API key时使用简单的正则解析
            return self._fallback_parse(text)

        system_prompt = """你是一个物流订单信息提取助手。请从用户描述中提取以下信息并以JSON格式返回：
{
  "weight": 数字（货物重量，单位kg），
  "orig_port": "起运港代码（如PORT08）"，
  "dest_port": "目的港代码（如PORT09）"，
  "max_days": 数字（最大运输天数，可选，如果没有提到则为null）
}

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
可用的目的港：PORT09

重要规则：
1. 只返回JSON，不要有其他文字
2. 重量必须是数字（如果用户说"斤"需要除以2换算为kg）
3. 港口代码必须大写
4. 如果用户使用中文港口名，必须转换为对应的PORT代码
5. 如果信息缺失，对应字段设为null
6. 如果用户只提到一个港口名且上下文是"从...发/运"，则为起运港；目的港默认PORT09"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            # 尝试提取JSON
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content)
            # 验证并修正港口代码
            result = self._validate_ports(result, text)
            return result
        except Exception as e:
            return self._fallback_parse(text)

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
        result = {"weight": None, "orig_port": None, "dest_port": None, "max_days": None}

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

        # 提取天数
        days_match = re.search(r'(\d+)\s*(?:天|日|days?)', text, re.IGNORECASE)
        if days_match:
            result["max_days"] = int(days_match.group(1))

        return result

    def is_configured(self) -> bool:
        """检查是否已配置 API Key"""
        return bool(self.api_key)
