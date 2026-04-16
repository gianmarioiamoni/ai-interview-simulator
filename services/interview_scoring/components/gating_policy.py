# services/interview_scoring/components/gating_policy.py

from typing import Dict, Optional
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from domain.contracts.user.role import RoleType


class GatingPolicy:

    CRITICAL_DIMENSIONS = {
        RoleType.BACKEND_ENGINEER: [PerformanceDimensionType.SYSTEM_DESIGN],
    }

    def apply(
        self,
        dimension_scores: Dict[PerformanceDimensionType, float],
        role: RoleType,
    ) -> tuple[bool, Optional[str]]:

        for dim in self.CRITICAL_DIMENSIONS.get(role, []):
            if dimension_scores.get(dim) is None:
                return True, f"Critical dimension '{dim.value}' not evaluated"

        return False, None
