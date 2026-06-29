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

    READINESS_LABELS = {
        HireDecision.NO_HIRE: "Not Ready Yet",
        HireDecision.LEAN_NO_HIRE: "Needs Improvement",
        HireDecision.LEAN_HIRE: "Nearly Ready",
        HireDecision.HIRE: "Interview Ready",
    }

    READINESS_COLORS = {
        HireDecision.NO_HIRE: "#dc2626",
        HireDecision.LEAN_NO_HIRE: "#d97706",
        HireDecision.LEAN_HIRE: "#2563eb",
        HireDecision.HIRE: "#16a34a",
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
    def to_readiness_label(cls, decision: HireDecision) -> str:
        return cls.READINESS_LABELS.get(
            decision,
            decision.value.replace("_", " ").title(),
        )

    @classmethod
    def to_readiness_color(cls, decision: HireDecision) -> str:
        return cls.READINESS_COLORS.get(decision, "#4b5563")

    # ---------------------------------------------------------

    @classmethod
    def to_badge(cls, decision: HireDecision) -> dict:
        return {
            "label": cls.to_label(decision),
            "color": cls.COLORS.get(decision, "gray"),
        }
