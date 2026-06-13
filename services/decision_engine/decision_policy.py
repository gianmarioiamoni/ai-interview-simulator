# services/decision_engine/decision_policy.py

from typing import Dict, Any

from infrastructure.config.evaluation import (
    HIRE_SCORE_THRESHOLD,
    LEAN_HIRE_SCORE_THRESHOLD,
    LEAN_NO_HIRE_SCORE_THRESHOLD,
    SYSTEM_DESIGN_GATE_THRESHOLD,
    SYSTEM_DESIGN_PENALTY,
    TECHNICAL_DEPTH_GATE_THRESHOLD,
    TECHNICAL_DEPTH_PENALTY,
)


POLICY: Dict[str, Any] = {
    # ---------------------------------------------------------
    # GLOBAL DECISION THRESHOLDS
    # ---------------------------------------------------------
    "decision_thresholds": {
        "HIRE": HIRE_SCORE_THRESHOLD,
        "LEAN_HIRE": LEAN_HIRE_SCORE_THRESHOLD,
        "LEAN_NO_HIRE": LEAN_NO_HIRE_SCORE_THRESHOLD,
    },
    # ---------------------------------------------------------
    # DIMENSION RULES
    # ---------------------------------------------------------
    "dimension_rules": {
        "system_design": {
            "threshold": SYSTEM_DESIGN_GATE_THRESHOLD,
            "penalty": SYSTEM_DESIGN_PENALTY,
            "downgrade": True,
            "reason": "system_design_below_threshold",
        },
        # future-ready
        "technical_depth": {
            "threshold": TECHNICAL_DEPTH_GATE_THRESHOLD,
            "penalty": TECHNICAL_DEPTH_PENALTY,
            "downgrade": False,
        },
    },
    # ---------------------------------------------------------
    # GLOBAL FLAGS
    # ---------------------------------------------------------
    "global": {
        "enable_penalties": True,
        "enable_downgrade": True,
    },
}
