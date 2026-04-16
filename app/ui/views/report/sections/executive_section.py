# app/ui/views/report/sections/executive_section.py


def render_executive(report):
    return f"""
<h2>Executive Summary</h2>
<p>{report.executive_summary}</p>
"""

