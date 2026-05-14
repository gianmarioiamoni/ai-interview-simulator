# services/decision_engine/decision_engine.py

from typing import Dict, Tuple, Optional

from domain.contracts.user.role import RoleType
from domain.contracts.interview.hire_decision import HireDecision

from services.decision_engine.decision_policy import POLICY

from app.core.logger import get_logger

logger = get_logger(__name__)


class DecisionEngine:

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    def compute_decision(
        self,
        dimension_scores: Dict,
        overall_score: float,
        role: RoleType,
    ) -> Tuple[HireDecision, float, bool, Optional[str]]:

        thresholds = POLICY["decision_thresholds"]
        rules = POLICY["dimension_rules"]
        global_flags = POLICY["global"]

        decision = self._base_decision(overall_score, thresholds)

        adjusted_score = overall_score
        gating_triggered = False
        gating_reason = None

        # -----------------------------------------------------
        # APPLY POLICY RULES
        # -----------------------------------------------------

        for dim_key, rule in rules.items():

            dim_score = self._get_dimension_score(dimension_scores, dim_key)

            if dim_score is None:
                continue

            threshold = rule.get("threshold")

            if threshold is None:
                continue

            if dim_score < threshold:

                logger.info(f"POLICY TRIGGERED: {dim_key}={dim_score} < {threshold}")

                gating_triggered = True
                gating_reason = rule.get("reason", f"{dim_key}_rule_triggered")

                # ---------------------------------------------
                # PENALTY
                # ---------------------------------------------

                if global_flags.get("enable_penalties"):

                    penalty = rule.get("penalty", 1.0)
                    adjusted_score = round(adjusted_score * penalty, 1)

                # ---------------------------------------------
                # DOWNGRADE
                # ---------------------------------------------

                if global_flags.get("enable_downgrade") and rule.get("downgrade"):
                    decision = self._downgrade(decision)

        # -----------------------------------------------------
        # FINAL DECISION AFTER POLICY
        # -----------------------------------------------------

        final_decision = self._base_decision(adjusted_score, thresholds)

        return final_decision, adjusted_score, gating_triggered, gating_reason

    # ---------------------------------------------------------
    # BASE DECISION
    # ---------------------------------------------------------

    def _base_decision(
        self,
        score: float,
        thresholds: Dict[str, float],
    ) -> HireDecision:

        if score >= thresholds["HIRE"]:
            return HireDecision.HIRE
        elif score >= thresholds["LEAN_HIRE"]:
            return HireDecision.LEAN_HIRE
        elif score >= thresholds["LEAN_NO_HIRE"]:
            return HireDecision.LEAN_NO_HIRE
        else:
            return HireDecision.NO_HIRE

    # ---------------------------------------------------------
    # DOWNGRADE
    # ---------------------------------------------------------

    def _downgrade(self, decision: HireDecision) -> HireDecision:

        if decision == HireDecision.HIRE:
            return HireDecision.LEAN_HIRE
        elif decision == HireDecision.LEAN_HIRE:
            return HireDecision.LEAN_NO_HIRE
        elif decision == HireDecision.LEAN_NO_HIRE:
            return HireDecision.NO_HIRE

        return decision

    # ---------------------------------------------------------
    # UTILS
    # ---------------------------------------------------------

    def _get_dimension_score(self, scores: Dict, key: str):

        for dim, value in scores.items():
            dim_key = dim.value if hasattr(dim, "value") else dim
            if dim_key == key:
                return value

        return None
