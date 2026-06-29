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


def score_band_label(score: float) -> str:
    """Return human-readable band name matching the written_evaluation.txt rubric."""
    if score is None:
        return ""
    if score >= 90:
        return "EXCEPTIONAL"
    if score >= 80:
        return "STRONG"
    if score >= 65:
        return "ACCEPTABLE"
    if score >= 40:
        return "WEAK"
    return "INCORRECT"


def score_band_badge(score: float) -> str:
    """Return a coloured band badge for a given score."""
    band = score_band_label(score)
    color_map = {
        "EXCEPTIONAL": "#7c3aed",
        "STRONG":      "#16a34a",
        "ACCEPTABLE":  "#ca8a04",
        "WEAK":        "#dc2626",
        "INCORRECT":   "#991b1b",
    }
    color = color_map.get(band, "#4b5563")
    return badge(band, color)
