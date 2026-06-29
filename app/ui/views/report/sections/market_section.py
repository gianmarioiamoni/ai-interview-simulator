# app/ui/views/report/sections/market_section.py

from app.ui.views.report.charts.distribution_chart import percentile_distribution
from app.ui.views.report.components.badges import score_badge


def _plain_english_percentile(percentile: float, seniority: str, role: str) -> str:
    pct = round(percentile)
    role_label = role.replace("_", " ").title() if role else "candidate"
    seniority_label = seniority.capitalize() if seniority else ""
    level_str = f"{seniority_label} {role_label}".strip()
    return f"You performed better than approximately <strong>{pct}%</strong> of {level_str} candidates evaluated on this platform."


def render_market(vm):

    report = vm["report"]

    gaussian = percentile_distribution(report.overall_score)

    seniority = getattr(report, "seniority_level", "mid") or "mid"
    role = getattr(report, "role", "")
    role_str = role.value if hasattr(role, "value") else str(role)

    plain_percentile = _plain_english_percentile(report.percentile_rank, seniority, role_str)

    return f"""
<h2>Interview Benchmark</h2>

<p>
Candidate is positioned in <strong>{vm["percentile_segment"]}</strong><br>
({score_badge(report.percentile_rank)})
</p>

{gaussian}

<p style="color:#374151;font-size:0.95em;">
{plain_percentile}
</p>

<div style="margin-top:10px;padding:10px;border-left:4px solid #2563eb;">
{vm["percentile_narrative"]}
</div>
"""
