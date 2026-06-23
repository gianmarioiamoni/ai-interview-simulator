# app/ui/views/report/sections/roadmap_section.py


def render_roadmap(vm):

    suggestions: list[str] = vm.get("improvement_suggestions") or []
    roadmap: list[dict] = vm.get("roadmap") or []

    if not suggestions and not roadmap:
        return ""

    roadmap_html = ""

    if suggestions:
        for suggestion in suggestions:
            roadmap_html += f"""
<div style="margin-bottom:10px;">
{suggestion}
</div>
"""
    else:
        for r in roadmap:
            roadmap_html += f"""
<div style="margin-bottom:10px;">
<strong>[{r['priority']}] {r['dimension']}</strong><br>
{r['action']}
</div>
"""

    return f"""
<h2>Improvement Roadmap</h2>
{roadmap_html}
"""
