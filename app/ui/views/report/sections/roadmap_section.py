# app/ui/views/report/sections/roadmap_section.py


def render_roadmap(vm):

    roadmap_html = ""

    for r in vm["roadmap"]:
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
