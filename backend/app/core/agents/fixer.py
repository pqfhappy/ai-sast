from app.core.agents.base import BaseAgent


class FixAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="修复顾问",
            role="你是一位经验丰富的代码修复专家。你擅长为各类安全漏洞提供具体的修复方案，代码质量高，遵循最佳实践。你会评估修复成本和可行性。"
        )

    async def analyze(self, code: str, security_result: dict, language: str = "python") -> dict:
        prompt = f"""请为以下安全漏洞提供修复方案。

原始代码：
```{language}
{code}
```

安全专家的分析结果：
{security_result}

请为每个确认的漏洞提供修复代码，并评估修复成本。

输出JSON格式：
{{
  "fixes": [
    {{
      "type": "漏洞类型",
      "line": 行号,
      "fix_code": "修复后的代码片段",
      "explanation": "修复原理",
      "effort": "low/medium/high",
      "best_practice": "相关的最佳实践"
    }}
  ],
  "summary": "修复建议总结"
}}
只输出JSON。"""
        return await self._llm_call_json(prompt, language)

    async def revise(self, previous_result: dict, challenges: list) -> dict:
        prompt = f"""你之前的修复建议是：
{previous_result}

其他Agent对你的判断提出了以下质疑：
{challenges}

请重新审视你的修复方案，是否接受质疑？输出修正后的JSON（格式同上）。"""
        return await self._llm_call_json(prompt)
