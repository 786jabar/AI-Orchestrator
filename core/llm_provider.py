"""
LLM Provider Interface
Supports both mock and real OpenAI API calls.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import os


@dataclass
class LLMResponse:
    """LLM response structure"""
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"


class LLMProvider:
    """Unified LLM provider supporting mock and real APIs"""
    
    def __init__(self, api_key: Optional[str] = None, use_real_api: bool = False):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.use_real_api = use_real_api and self.api_key is not None
        self.call_count = 0
    
    def generate(self, prompt: str, max_tokens: int = 1000, 
                 temperature: float = 0.7, model: str = "gpt-3.5-turbo") -> LLMResponse:
        """Generate response using real API or mock"""
        self.call_count += 1
        
        if self.use_real_api:
            return self._call_openai_api(prompt, max_tokens, temperature, model)
        else:
            return self._generate_mock_response(prompt)
    
    def _call_openai_api(self, prompt: str, max_tokens: int,
                         temperature: float, model: str) -> LLMResponse:
        """Call real OpenAI API"""
        try:
            import openai
            
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")
            
            openai.api_key = self.api_key
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for software development."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens,
                finish_reason=response.choices[0].finish_reason
            )
        except ImportError:
            return self._generate_mock_response(prompt)
        except Exception as e:
            return LLMResponse(
                content=f"Error calling API: {str(e)}. Falling back to mock.",
                model=model,
                tokens_used=0,
                finish_reason="error"
            )
    
    def _generate_mock_response(self, prompt: str) -> LLMResponse:
        """Generate mock response"""
        if "plan" in prompt.lower() or "goal" in prompt.lower():
            content = """Plan:
1. Requirements Analysis
2. System Design
3. Implementation
4. Testing
5. Deployment"""
        elif "code" in prompt.lower() or "implement" in prompt.lower():
            content = """def implementation():
    # Implementation code
    return result"""
        elif "test" in prompt.lower():
            content = """def test_implementation():
    assert implementation() == expected_result"""
        elif "review" in prompt.lower() or "critique" in prompt.lower():
            content = "Code review: No issues found. Implementation looks good."
        else:
            content = f"Mock response for: {prompt[:50]}..."
        
        return LLMResponse(
            content=content,
            model="mock-llm",
            tokens_used=len(content.split()),
            finish_reason="stop"
        )


class LLMInterface:
    """Interface for LLM operations"""
    
    def __init__(self, api_key: Optional[str] = None, use_real_api: bool = False):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.use_real_api = use_real_api and self.api_key is not None
        self.provider = LLMProvider(self.api_key, self.use_real_api)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using LLM or mock"""
        response = self.provider.generate(prompt, **kwargs)
        return response.content
    
    def get_call_count(self) -> int:
        """Get number of LLM calls made"""
        return self.provider.call_count
    
    def is_using_real_api(self) -> bool:
        """Check if using real API"""
        return self.use_real_api

