# app/ui/views/report/components/tables.py


def contribution_table(dimensions):

    rows = ""

    for d in dimensions:

        score = "N/A" if d.score is None else d.score

        status = (
            "⚪ N/A"
            if d.score is None
            else (
                "🟢 Strong"
                if d.score >= 80
                else "🟡 Medium" if d.score >= 60 else "🔴 Weak"
            )
        )

        rows += f"""
<tr>
<td>{d.name}</td>
<td>{score}</td>
<td>{d.weight if d.score else "-"}</td>
<td>{d.contribution if d.score else "-"}</td>
<td>{status}</td>
</tr>
"""

    return f"""
<table>
<tr>
<th>Dimension</th>
<th>Score</th>
<th>Weight</th>
<th>Contribution</th>
<th>Status</th>
</tr>
{rows}
</table>
"""
