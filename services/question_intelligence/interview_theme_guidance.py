# services/question_intelligence/interview_theme_guidance.py

from domain.contracts.interview.interview_area import InterviewArea


def build_theme_guidance(
    theme_anchor: str | None,
    area: InterviewArea,
) -> str | None:

    if not theme_anchor:
        return None

    readable_theme = theme_anchor.replace("_", " ")

    area_focus = {
        InterviewArea.TECH_BACKGROUND: (
            f"Prefer background questions that connect to {readable_theme} experience."
        ),
        InterviewArea.TECH_TECHNICAL_KNOWLEDGE: (
            f"Prefer knowledge questions grounded in {readable_theme} concepts."
        ),
        InterviewArea.TECH_CASE_STUDY: (
            f"Prefer case studies that explore realistic {readable_theme} scenarios."
        ),
        InterviewArea.TECH_DATABASE: (
            f"Prefer database questions that relate to {readable_theme} data concerns."
        ),
        InterviewArea.TECH_CODING: (
            f"Prefer coding problems that illustrate {readable_theme} engineering patterns."
        ),
    }

    focus = area_focus.get(
        area,
        f"Prefer questions that naturally relate to {readable_theme}.",
    )

    return (
        f"Interview theme anchor: {readable_theme}. "
        f"{focus} "
        "Use the theme as soft guidance only; prefer natural, high-quality questions."
    )
