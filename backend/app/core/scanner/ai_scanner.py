from openai import AsyncOpenAI
from app.config import settings


class AIScanner:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
        )
        self.model = settings.QWEN_MODEL

    async def analyze_code(self, code: str, context: str = "") -> dict:
        prompt = f"""你是一个代码安全专家。请分析以下代码中的安全漏洞。

{context}

代码：
```python
{code}
```

请以JSON格式输出，格式为：
{{
  "vulnerabilities": [
    {{
      "type": "漏洞类型",
      "severity": "critical/high/medium/low",
      "line": 行号,
      "description": "漏洞描述",
      "remediation": "修复建议",
      "confidence": 0-100
    }}
  ]
}}
只输出JSON，不要其他内容。"""
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            import json
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            return {"vulnerabilities": [], "error": str(e)}

    async def generate_fix(self, code: str, vuln_type: str, description: str) -> str:
        prompt = f"""代码中存在 {vuln_type} 漏洞。
描述：{description}

请提供修复后的代码：

{code}

只输出修复后的代码，不要解释。"""
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception:
            return ""
