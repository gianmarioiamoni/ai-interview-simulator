# app/ui/mappers/hire_decision_mapper.py

from domain.contracts.interview.hire_decision import HireDecision


class HireDecisionMapper:

    LABELS = {
        HireDecision.NO_HIRE: "No Hire",
        HireDecision.LEAN_NO_HIRE: "Lean No Hire",
        HireDecision.LEAN_HIRE: "Lean Hire",
        HireDecision.HIRE: "Hire",
    }

    COLORS = {
        HireDecision.NO_HIRE: "red",
        HireDecision.LEAN_NO_HIRE: "orange",
        HireDecision.LEAN_HIRE: "yellow",
        HireDecision.HIRE: "green",
    }

    # ---------------------------------------------------------

    @classmethod
    def to_label(cls, decision: HireDecision) -> str:
        return cls.LABELS.get(
            decision,
            decision.value.replace("_", " ").title(),
        )

    # ---------------------------------------------------------

    @classmethod
    def to_badge(cls, decision: HireDecision) -> dict:
        return {
            "label": cls.to_label(decision),
            "color": cls.COLORS.get(decision, "gray"),
        }
