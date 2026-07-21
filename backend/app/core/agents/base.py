from openai import AsyncOpenAI
from app.config import settings


class BaseAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.client = AsyncOpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
        )
        self.model = settings.QWEN_MODEL

    async def _llm_call(self, prompt: str, response_format: dict = None) -> str:
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"你是{self.name}，{self.role}"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
        if response_format:
            kwargs["response_format"] = response_format
        resp = await self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content

    async def _llm_call_json(self, prompt: str) -> dict:
        import json
        content = await self._llm_call(
            prompt,
            response_format={"type": "json_object"},
        )
        return json.loads(content)
