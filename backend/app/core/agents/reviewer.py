from app.core.agents.base import BaseAgent
from app.core.scanner.semgrep import SemgrepScanner


class ReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="代码审查员",
            role="你是一位资深的代码安全审查专家。你的职责是初步审查代码，标记可疑的代码模式。你需要关注：SQL注入、XSS、命令注入、路径遍历、硬编码密钥、不安全的反序列化等常见漏洞。"
        )
        self.semgrep = SemgrepScanner()

    async def analyze(self, code: str, language: str = "python") -> dict:
        semgrep_results = await self.semgrep.scan(code, language)

        prompt = f"""请审查以下代码，找出潜在的安全漏洞。

语言：{language}

代码：
```{language}
{code}
```

Semgrep扫描结果：
{semgrep_results}

请输出JSON格式：
{{
  "findings": [
    {{
      "type": "漏洞类型",
      "severity": "critical/high/medium/low",
      "line": 行号,
      "description": "问题描述",
      "confidence": 0-100,
      "source": "semgrep" 或 "llm"
    }}
  ],
  "summary": "总体评价",
  "risk_score": 0-100
}}
只输出JSON。"""
        result = await self._llm_call_json(prompt)
        result["_semgrep_raw"] = semgrep_results
        result["_agent"] = self.name
        return result

    async def revise(self, previous_result: dict, challenges: list) -> dict:
        prompt = f"""你之前的审查结果是：
{previous_result}

其他Agent对你的判断提出了以下质疑：
{challenges}

请重新审视你的判断，是否接受质疑？输出修正后的JSON（格式同上）。"""
        result = await self._llm_call_json(prompt)
        result["_agent"] = self.name
        return result
