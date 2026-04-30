# services/decision_engine/decision_policy.py

from typing import Dict, Any


POLICY: Dict[str, Any] = {
    # ---------------------------------------------------------
    # GLOBAL DECISION THRESHOLDS
    # ---------------------------------------------------------
    "decision_thresholds": {
        "HIRE": 85,
        "LEAN_HIRE": 70,
        "LEAN_NO_HIRE": 60,
    },
    # ---------------------------------------------------------
    # DIMENSION RULES
    # ---------------------------------------------------------
    "dimension_rules": {
        "system_design": {
            "threshold": 60,
            "penalty": 0.9,
            "downgrade": True,
            "reason": "system_design_below_threshold",
        },
        # future-ready
        "technical_depth": {
            "threshold": 50,
            "penalty": 0.95,
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
