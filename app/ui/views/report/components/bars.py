# app/ui/views/report/components/bars.py

def test_progress_bar(passed, total):
    percent = (passed / total) * 100 if total else 0
    return f"""
<div style="margin-top:6px;">
<div style="background:#e5e7eb;height:10px;border-radius:5px;">
<div style="width:{percent}%;background:#16a34a;height:10px;border-radius:5px;"></div>
</div>
<div style="font-size:12px;">{passed}/{total} tests passed</div>
</div>
"""


def confidence_bar(conf):
    percent = round(conf * 100, 1)
    return f"""
<div style="margin-top:8px;">
<strong>Confidence: {percent}%</strong>
<div style="background:#e5e7eb;height:10px;border-radius:5px;">
<div style="width:{percent}%;background:#16a34a;height:10px;border-radius:5px;"></div>
</div>
</div>
"""