from openai import AsyncOpenAI
from app.config import settings


class BaseAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self._client = None
        self.model = settings.QWEN_MODEL

    @property
    def client(self):
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.QWEN_API_KEY,
                base_url=settings.QWEN_BASE_URL,
            )
        return self._client

    async def _llm_call(self, prompt: str, response_format: dict = None, language: str = "python") -> str:
        lang_map = {
            "c": ("C", "//"),
            "cpp": ("C++", "//"),
            "rust": ("Rust", "//"),
            "go": ("Go", "//"),
            "python": ("Python", "#"),
            "javascript": ("JavaScript", "//"),
            "java": ("Java", "//"),
        }
        lang_name = lang_map.get(language, (language, "#"))[0]
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"你是{self.name}，{self.role}。你精通{lang_name}代码安全分析。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
        if response_format:
            kwargs["response_format"] = response_format
        resp = await self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content

    async def _llm_call_json(self, prompt: str, language: str = "python") -> dict:
        import json
        content = await self._llm_call(
            prompt,
            response_format={"type": "json_object"},
            language=language,
        )
        return json.loads(content)
