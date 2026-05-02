from __future__ import annotations

from dataclasses import dataclass

from ..config import ACTIVE_SESSION_THRESHOLD_SECONDS


@dataclass
class RuleResult:
    should_break: bool


class RuleEngine:
    def __init__(self, active_threshold_seconds: int = ACTIVE_SESSION_THRESHOLD_SECONDS) -> None:
        self.active_threshold_seconds = active_threshold_seconds

    def evaluate(self, active_seconds: int, is_idle: bool) -> RuleResult:
        if is_idle:
            return RuleResult(should_break=False)
        return RuleResult(should_break=active_seconds >= self.active_threshold_seconds)
