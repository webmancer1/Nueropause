from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..config import WELLNESS_PROMPTS


@dataclass
class WellnessState:
    prompt: str
    index: int


class WellnessEngine:
    def __init__(self, prompts: List[str] | None = None) -> None:
        self.prompts = prompts if prompts is not None else list(WELLNESS_PROMPTS)
        self._index = 0

    def next_prompt(self) -> WellnessState:
        if not self.prompts:
            return WellnessState(prompt="Take a mindful break", index=0)
        prompt = self.prompts[self._index % len(self.prompts)]
        state = WellnessState(prompt=prompt, index=self._index)
        self._index += 1
        return state
