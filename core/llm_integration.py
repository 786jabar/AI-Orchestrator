"""
LLM integration with mock fallback.
"""

from dataclasses import dataclass
from typing import Optional
import os

try:
    import openai
except ImportError:
    openai = None


@dataclass
class LLMConfig:
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 512
    use_real_api: bool = False
    api_key: Optional[str] = None


class ConfigurableLLMInterface:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        if self.config.api_key is None:
            self.config.api_key = os.getenv("OPENAI_API_KEY")
        self.config.use_real_api = self.config.use_real_api and bool(self.config.api_key)
        self.use_mock = not self.config.use_real_api

    def generate(self, prompt: str) -> str:
        if self.config.use_real_api and openai:
            try:
                openai.api_key = self.config.api_key
                resp = openai.ChatCompletion.create(
                    model=self.config.model,
                    messages=[{"role": "system", "content": "You are a helpful software assistant."}, {"role": "user", "content": prompt}],
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
                return resp.choices[0].message.content
            except Exception:
                return self._mock(prompt)
        return self._mock(prompt)

    def _mock(self, prompt: str) -> str:
        return f"[mock llm response] {prompt[:200]}"