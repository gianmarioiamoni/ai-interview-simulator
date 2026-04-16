# app/ui/views/report/charts/distribution_chart.py

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


def percentile_distribution(score, mean=63, std=14):

    x = np.linspace(mean - 4 * std, mean + 4 * std, 500)
    y = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std) ** 2)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(x, y)
    ax.axvline(score, linestyle="--")

    ax.set_title("Role Distribution (Gaussian Model)")

    return _fig_to_base64(fig)
