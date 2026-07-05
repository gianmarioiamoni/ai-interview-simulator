# app/ui/views/report/sections/knowledge_gap_section.py
# EPIC-V13-05 Phase 9 — reads context_detail (was: interview_impact) per ScoringNarrativeItem.to_dict() contract.

from collections import defaultdict


def render_knowledge_gaps(report):

    gaps = getattr(report, "knowledge_gaps", []) or []

    if not gaps:
        return ""

    # Group by category
    by_category = defaultdict(list)
    for g in gaps:
        category = g.get("category", "Other")
        by_category[category].append(g)

    categories_html = ""
    for category, cat_gaps in by_category.items():
        gaps_html = ""
        for g in cat_gaps:
            concept = g.get("description", g.get("concept", ""))
            why = g.get("why_it_matters", "")
            impact = g.get("context_detail", "") or ""
            gaps_html += f"""
<div style="margin-bottom:10px;padding:10px;background:#f8fafc;border-radius:6px;border:1px solid #e2e8f0;">
<div style="font-weight:600;color:#1e293b;margin-bottom:4px;">{concept}</div>
<div style="font-size:0.88em;color:#475569;margin-bottom:2px;"><strong>Why it matters:</strong> {why}</div>
<div style="font-size:0.88em;color:#64748b;"><strong>Interview impact:</strong> {impact}</div>
</div>
"""
        categories_html += f"""
<div style="margin-bottom:16px;">
<div style="font-size:0.85em;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#2563eb;margin-bottom:8px;">{category}</div>
{gaps_html}
</div>
"""

    return f"""
<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:20px;margin-bottom:20px;">
<h2 style="margin:0 0 14px 0;color:#1e40af;">Knowledge Gap Summary</h2>
<p style="color:#3730a3;font-size:0.9em;margin-bottom:16px;">
Areas where deeper knowledge would improve your performance in future interviews.
</p>
{categories_html}
</div>
"""
