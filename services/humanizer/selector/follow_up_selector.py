# services/humanizer/selector/follow_up_selector.py

import math
from infrastructure.config.settings import Settings


class FollowUpSelector:
    """Deterministic pre-selector of follow-up eligible question indices.

    Called once at session start. Given the planned question count and
    configuration, returns a frozenset of indices at which the Humanizer
    policy engine is permitted to trigger a follow-up turn.

    Constraints enforced (see M1-3 Section D):
    - Index 0 (first question) is always excluded.
    - Index total_questions - 1 (last question) is always excluded.
    - No two selected indices are consecutive (spacing > 1).
    - Selected count <= floor(total * percentage) capped by max_follow_ups.
    - Only areas in allowed_areas are eligible (empty = all written areas).
    - Only types in allowed_types are eligible.

    The algorithm maximises spacing (uniform distribution) and avoids
    clustering at session start or end.
    """

    def select(
        self,
        *,
        total_questions: int,
        planned_areas: list[str],
        settings: Settings,
    ) -> frozenset[int]:
        """Return eligible follow-up indices as a frozenset.

        All decisions derive exclusively from ``settings``.
        Same inputs always produce the same output.
        """
        if not settings.humanizer_follow_up_enabled:
            return frozenset()

        quota = self._compute_quota(total_questions, settings)
        if quota == 0:
            return frozenset()

        candidates = self._filter_candidates(total_questions, planned_areas, settings)
        if not candidates:
            return frozenset()

        selected = self._distribute(candidates, quota)
        return frozenset(selected)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_quota(self, total_questions: int, settings: Settings) -> int:
        """Number of follow-ups to select, respecting percentage and hard cap."""
        if settings.follow_up_selector_policy == "fixed":
            raw = settings.max_follow_ups_per_interview
        else:
            raw = math.floor(total_questions * settings.follow_up_percentage)
        return min(raw, settings.max_follow_ups_per_interview)

    def _filter_candidates(
        self,
        total_questions: int,
        planned_areas: list[str],
        settings: Settings,
    ) -> list[int]:
        """Indices that are structurally eligible (area/type filters + boundary rules)."""
        allowed_areas = self._parse_allowed_areas(settings.follow_up_allowed_areas)
        allowed_types = {t.strip().lower() for t in settings.follow_up_allowed_types.split(",") if t.strip()}

        candidates: list[int] = []

        for idx in range(total_questions):
            # Boundary exclusions: first question and last question never eligible
            if idx == 0 or idx == total_questions - 1:
                continue

            # Area filter: check planned_areas if available
            if idx < len(planned_areas):
                area = planned_areas[idx].lower()
                if allowed_areas and area not in allowed_areas:
                    continue
                # Type filter: derive QuestionType from area name
                if not self._area_matches_types(area, allowed_types):
                    continue

            candidates.append(idx)

        return candidates

    def _area_matches_types(self, area: str, allowed_types: set[str]) -> bool:
        """Determine whether an area corresponds to an allowed question type.

        Written areas: all areas that are not CODING or DATABASE.
        Coding area: technical_coding.
        Database area: technical_database.
        """
        if "coding" in area:
            return "coding" in allowed_types
        if "database" in area:
            return "database" in allowed_types
        # HR and all other written areas
        return "written" in allowed_types

    def _parse_allowed_areas(self, raw: str) -> set[str]:
        if not raw:
            return set()
        return {a.strip().lower() for a in raw.split(",") if a.strip()}

    def _distribute(self, candidates: list[int], quota: int) -> list[int]:
        """Select ``quota`` indices from ``candidates`` with maximum spacing.

        For quota == 1: select the candidate closest to the centre of the
        candidate list to avoid boundary placement.

        For quota > 1: space indices as evenly as possible by stepping with
        stride = len(candidates) / quota. The first step starts at
        stride / 2 (half-offset) so the distribution is centred rather than
        front-loaded.

        After selection the no-consecutive constraint is enforced by a greedy
        scan that removes any adjacent pair, keeping the earlier element.
        """
        if not candidates:
            return []

        if quota >= len(candidates):
            return self._enforce_no_consecutive(candidates)

        if quota == 1:
            mid = len(candidates) // 2
            return [candidates[mid]]

        # Half-offset stride: start at stride/2 so indices are centred
        stride = len(candidates) / quota
        selected: list[int] = []
        for i in range(quota):
            pos = int((i + 0.5) * stride)
            pos = min(pos, len(candidates) - 1)
            selected.append(candidates[pos])

        # Deduplicate
        seen: set[int] = set()
        deduped: list[int] = []
        for idx in selected:
            if idx not in seen:
                seen.add(idx)
                deduped.append(idx)

        return self._enforce_no_consecutive(sorted(deduped))

    def _enforce_no_consecutive(self, indices: list[int]) -> list[int]:
        """Remove consecutive pairs from a sorted list, keeping the first of each pair."""
        result: list[int] = []
        for idx in indices:
            if result and idx - result[-1] <= 1:
                continue
            result.append(idx)
        return result
