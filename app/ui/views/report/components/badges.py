# app/ui/views/report/components/badges.py


def badge(value, color):
    return f'<span style="background:{color};color:white;padding:6px 10px;border-radius:6px;font-size:12px;">{value}</span>'


def score_badge(score):
    if score is None:
        return badge("N/A", "#6b7280")
    if score >= 80:
        return badge(f"{score}/100", "#16a34a")
    if score >= 60:
        return badge(f"{score}/100", "#ca8a04")
    return badge(f"{score}/100", "#dc2626")
