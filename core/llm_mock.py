"""
Mock LLM Interface
Provides mock implementations when real LLM models are unavailable.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM response structure"""
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"


class MockLLM:
    """Mock LLM implementation for when real models are unavailable"""
    
    def __init__(self, model_name: str = "mock-llm"):
        self.model_name = model_name
        self.call_count = 0
    
    def generate(self, prompt: str, max_tokens: int = 1000, 
                 temperature: float = 0.7) -> LLMResponse:
        """Generate mock response"""
        self.call_count += 1
        
        if "plan" in prompt.lower() or "goal" in prompt.lower():
            content = self._generate_plan_response(prompt)
        elif "code" in prompt.lower() or "implement" in prompt.lower():
            content = self._generate_code_response(prompt)
        elif "test" in prompt.lower():
            content = self._generate_test_response(prompt)
        elif "review" in prompt.lower() or "critique" in prompt.lower():
            content = self._generate_review_response(prompt)
        else:
            content = f"Mock response for: {prompt[:50]}..."
        
        return LLMResponse(
            content=content,
            model=self.model_name,
            tokens_used=len(content.split()),
            finish_reason="stop"
        )
    
    def _generate_plan_response(self, prompt: str) -> str:
        """Generate mock plan response"""
        return """Plan:
1. Requirements Analysis
2. System Design
3. Implementation
4. Testing
5. Deployment"""
    
    def _generate_code_response(self, prompt: str) -> str:
        """Generate mock code response"""
        return """def implementation():
    # Implementation code
    return result"""
    
    def _generate_test_response(self, prompt: str) -> str:
        """Generate mock test response"""
        return """def test_implementation():
    assert implementation() == expected_result"""
    
    def _generate_review_response(self, prompt: str) -> str:
        """Generate mock review response"""
        return "Code review: No issues found. Implementation looks good."


class LLMInterface:
    """Interface for LLM operations"""
    
    def __init__(self, use_mock: bool = True, model_name: Optional[str] = None):
        self.use_mock = use_mock
        self.model_name = model_name or "mock-llm"
        self.llm = MockLLM(self.model_name) if use_mock else None
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using LLM or mock"""
        if self.use_mock or self.llm is None:
            if self.llm is None:
                self.llm = MockLLM(self.model_name)
            response = self.llm.generate(prompt, **kwargs)
            return response.content
        else:
            raise NotImplementedError("Real LLM integration not implemented")
    
    def get_call_count(self) -> int:
        """Get number of LLM calls made"""
        if self.llm:
            return self.llm.call_count
        return 0


