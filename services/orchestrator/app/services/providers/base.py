from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AiResponse:
    content: str
    provider: str
    model: str
    raw: dict = field(default_factory=dict)


class AiProviderClient(ABC):
    name: str

    @abstractmethod
    async def send_prompt(self, task: str, context: str) -> AiResponse:
        raise NotImplementedError
