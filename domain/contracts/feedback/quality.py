# domain/contracts/quality.py

from enum import Enum


class Quality(str, Enum):
    INCORRECT = "incorrect"
    PARTIAL = "partial"
    INEFFICIENT = "inefficient"
    CORRECT = "correct"
    OPTIMAL = "optimal"

    def rank(self) -> int:
        return {
            Quality.INCORRECT: 0,
            Quality.PARTIAL: 1,
            Quality.INEFFICIENT: 2,
            Quality.CORRECT: 3,
            Quality.OPTIMAL: 4,
        }[self]

    def is_at_least(self, other: "Quality") -> bool:
        return self.rank() >= other.rank()

    def is_better_than(self, other: "Quality") -> bool:
        return self.rank() > other.rank()
