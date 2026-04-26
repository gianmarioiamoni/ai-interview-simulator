# app/ui/views/report/sections/signal_section.py


def render_signals(vm):

    signals = vm.get("signal_insights", [])

    if not signals:
        return ""

    items = "".join(
        f"<li>{s['severity']} {s['text']}</li>" 
        for s in signals
    )

    return f"""
<h2>Behavioral Insights</h2>
<ul>
{items}
</ul>
"""
