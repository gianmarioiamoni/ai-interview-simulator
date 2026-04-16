# services/interview_scoring/components/percentile_calculator.py

import math
from domain.contracts.user.role import ROLE_DISTRIBUTION, RoleType


class PercentileCalculator:

    def compute(self, score: float, role: RoleType) -> float:

        params = ROLE_DISTRIBUTION[role]
        mean = params["mean"]
        std = params["std"]

        if std <= 0:
            return 50.0

        z = (score - mean) / std
        percentile = 0.5 * (1 + math.erf(z / math.sqrt(2)))

        return round(percentile * 100, 1)
