# app/ui/views/report/components/badges.py

from infrastructure.config.evaluation import (
    REPORT_SCORE_GREEN_THRESHOLD,
    REPORT_SCORE_YELLOW_THRESHOLD,
)


def badge(value, color):
    return f'<span style="background:{color};color:white;padding:6px 10px;border-radius:6px;font-size:12px;">{value}</span>'


def score_badge(score):
    if score is None:
        return badge("N/A", "#4b5563")
    if score >= REPORT_SCORE_GREEN_THRESHOLD:
        return badge(f"{score}/100", "#16a34a")
    if score >= REPORT_SCORE_YELLOW_THRESHOLD:
        return badge(f"{score}/100", "#ca8a04")
    return badge(f"{score}/100", "#dc2626")
