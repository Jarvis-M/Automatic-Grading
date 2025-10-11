from abc import ABC, abstractmethod
from typing import Dict
from scoring.llm.deepseek_scorer import LLMScore

class BaseLLMClient(ABC):
    @abstractmethod
    async def score_code(self, prompt: str) -> LLMScore:
        pass