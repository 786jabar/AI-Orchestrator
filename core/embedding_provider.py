"""
Embedding provider with graceful fallback.
"""

from dataclasses import dataclass
from typing import List, Optional
import hashlib
import os


@dataclass
class EmbeddingConfig:
    model: str = "text-embedding-3-small"
    use_real: bool = False
    api_key: Optional[str] = None
    dim: int = 128


class EmbeddingProvider:
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        if self.config.api_key is None:
            self.config.api_key = os.getenv("OPENAI_API_KEY")
        self.config.use_real = self.config.use_real and bool(self.config.api_key)

    def embed(self, text: str) -> List[float]:
        if self.config.use_real:
            try:
                import openai

                openai.api_key = self.config.api_key
                resp = openai.embeddings.create(model=self.config.model, input=text)
                return resp.data[0].embedding
            except Exception:
                pass
        return self._hash_embed(text, self.config.dim)

    @staticmethod
    def _hash_embed(text: str, dim: int) -> List[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = [0.0] * dim
        for i, b in enumerate(h):
            vec[i % dim] += b
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(y * y for y in b) ** 0.5 or 1.0
    return dot / (na * nb)