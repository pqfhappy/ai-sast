from app.core.agents.base import BaseAgent


class SecurityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="安全专家",
            role="你是一位顶级安全专家，擅长深度分析漏洞的利用路径和影响范围。你熟悉OWASP Top 10、CWE漏洞分类体系和CVSS评分标准。你习惯质疑他人的判断，确保不放过任何真正的威胁。"
        )

    async def analyze(self, code: str, reviewer_result: dict, language: str = "python") -> dict:
        prompt = f"""请对以下代码进行深度安全分析。

代码：
```{language}
{code}
```

代码审查员的初步分析结果：
{reviewer_result}

请验证审查员的发现，并深入分析：
1. 是否存在审查员遗漏的漏洞？
2. 审查员标记的漏洞中，哪些是误报？为什么？
3. 每个真实漏洞的攻击路径是什么？

输出JSON格式：
{{
  "confirmed_findings": [
    {{
      "type": "漏洞类型",
      "severity": "critical/high/medium/low",
      "line": 行号,
      "cvss_score": "CVSS评分 如 7.5",
      "attack_vector": "攻击路径描述",
      "impact": "影响范围",
      "confidence": 0-100
    }}
  ],
  "disputed": [
    {{
      "type": "被质疑的漏洞类型",
      "reason": "质疑理由"
    }}
  ],
  "new_findings": [
    {{
      "type": "新发现的漏洞类型",
      "severity": "critical/high/medium/low",
      "line": 行号,
      "description": "漏洞描述"
    }}
  ],
  "summary": "深度分析总结"
}}
只输出JSON。"""
        return await self._llm_call_json(prompt, language)

    async def revise(self, previous_result: dict, challenges: list) -> dict:
        prompt = f"""你之前的安全分析结果是：
{previous_result}

其他Agent对你的判断提出了以下质疑：
{challenges}

请重新审视你的分析，是否接受质疑？输出修正后的JSON（格式同上）。"""
        return await self._llm_call_json(prompt)
