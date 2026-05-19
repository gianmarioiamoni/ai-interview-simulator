# services/planning_validation/recovery_action.py

from enum import Enum


class RecoveryAction(str, Enum):

    RELAX_DIFFICULTY = "relax_difficulty"

    EXPAND_ROLE_SCOPE = "expand_role_scope"

    RELAX_AREA_LIMITS = "relax_area_limits"

    REDUCE_REQUIRED_QUESTIONS = "reduce_required_questions"
