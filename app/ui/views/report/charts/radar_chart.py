# app/ui/views/report/charts/radar_chart.py

import numpy as np
import matplotlib.pyplot as plt
import io
import base64


def _fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%;">'


def radar_chart(dimensions, scores):

    if not dimensions:
        return "<i>No dimension data available</i>"

    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    scores = list(scores) + [scores[0]]
    angles = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.plot(angles, scores)
    ax.fill(angles, scores, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dimensions)
    ax.set_ylim(0, 100)

    return _fig_to_base64(fig)
