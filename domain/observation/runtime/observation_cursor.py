# domain/observation/runtime/observation_cursor.py
# Deterministic, stateful iterator over an ordered sequence of Observations.

from __future__ import annotations

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.observation.observation_status import ObservationStatus


class ObservationCursor:
    """Deterministic forward-only cursor for iterating Observations.

    The cursor maintains a fixed, immutable window over a sequence of
    Observations. Position is tracked via an integer offset that advances
    monotonically. The underlying sequence never changes after construction.

    Thread-safety: a single cursor instance is NOT safe for concurrent use;
    create one cursor per consumer.
    """

    def __init__(self, observations: tuple[Observation, ...]) -> None:
        self._observations: tuple[Observation, ...] = observations
        self._position: int = 0

    @classmethod
    def from_list(cls, observations: list[Observation]) -> "ObservationCursor":
        return cls(tuple(observations))

    @property
    def position(self) -> int:
        return self._position

    @property
    def total(self) -> int:
        return len(self._observations)

    @property
    def remaining(self) -> int:
        return max(0, self.total - self._position)

    @property
    def exhausted(self) -> bool:
        return self._position >= self.total

    def peek(self) -> Observation | None:
        """Return next Observation without advancing the cursor."""
        if self.exhausted:
            return None
        return self._observations[self._position]

    def next(self) -> Observation | None:
        """Advance and return the next Observation, or None if exhausted."""
        if self.exhausted:
            return None
        obs = self._observations[self._position]
        self._position += 1
        return obs

    def seek(self, position: int) -> None:
        """Seek to an absolute position in [0, total].

        Raises:
            ValueError: if position is out of range.
        """
        if position < 0 or position > self.total:
            raise ValueError(
                f"position {position} is out of range [0, {self.total}]"
            )
        self._position = position

    def reset(self) -> None:
        """Rewind cursor to the beginning."""
        self._position = 0

    def collect_remaining(self) -> tuple[Observation, ...]:
        """Consume and return all remaining Observations."""
        result = self._observations[self._position:]
        self._position = self.total
        return result

    def skip_while(
        self,
        predicate: "Callable[[Observation], bool]",  # noqa: F821
    ) -> None:
        """Advance past all leading Observations that satisfy the predicate."""
        while not self.exhausted and predicate(self._observations[self._position]):
            self._position += 1

    def slice(self, start: int, end: int) -> tuple[Observation, ...]:
        """Return a sub-sequence [start, end) without moving the cursor position."""
        return self._observations[max(0, start): min(self.total, end)]
