"""
LLM Integration for AI Agent Orchestrator
Supports OpenAI API and mock fallback.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .llm_mock import LLMResponse, MockLLM, LLMInterface


@dataclass
class LLMConfig:
    """LLM configuration"""
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    use_real_api: bool = False
    max_tokens: int = 1000
    temperature: float = 0.7


class OpenAILLM:
    """OpenAI API integration"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.call_count = 0
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
            self._available = True
        except ImportError:
            self._available = False
        except Exception:
            self._available = False
    
    def generate(self, prompt: str, max_tokens: int = 1000, 
                 temperature: float = 0.7) -> LLMResponse:
        """Generate response using OpenAI API"""
        if not self._available or not self._client:
            raise RuntimeError("OpenAI client not available")
        
        self.call_count += 1
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=tokens_used,
                finish_reason="stop"
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")


class ConfigurableLLMInterface(LLMInterface):
    """LLM interface with configuration support"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig()
        
        self.config = config
        self.real_llm = None
        self.mock_llm = MockLLM("mock-llm")
        
        if config.use_real_api and config.api_key:
            try:
                self.real_llm = OpenAILLM(config.api_key, config.model)
                self.use_mock = False
            except Exception:
                self.use_mock = True
        else:
            self.use_mock = True
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using configured LLM"""
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.config.temperature)
        
        if not self.use_mock and self.real_llm:
            try:
                response = self.real_llm.generate(prompt, max_tokens, temperature)
                return response.content
            except Exception:
                response = self.mock_llm.generate(prompt, max_tokens, temperature)
                return response.content
        else:
            response = self.mock_llm.generate(prompt, max_tokens, temperature)
            return response.content
    
    def get_call_count(self) -> int:
        """Get number of LLM calls made"""
        if self.real_llm:
            return self.real_llm.call_count
        return self.mock_llm.call_count
    
    def is_using_real_api(self) -> bool:
        """Check if using real API"""
        return not self.use_mock and self.real_llm is not None


def load_llm_config() -> LLMConfig:
    """Load LLM configuration from environment or config file"""
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    use_real = os.getenv("USE_REAL_LLM", "false").lower() == "true"
    
    return LLMConfig(
        api_key=api_key,
        model=model,
        use_real_api=use_real and api_key is not None,
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7"))
    )

