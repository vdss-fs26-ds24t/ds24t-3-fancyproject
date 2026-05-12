import plotly.graph_objects as go
from plotly.colors import sample_colorscale
import pandas as pd

_COLORSCALES = {
    "Speed": "RdYlGn",
    "Throttle": "RdYlGn",
    "Brake": "RdYlGn_r",
    "Gear": "Viridis",
}
_UNITS = {"Speed": " km/h", "Throttle": "%", "Brake": "", "Gear": ""}

_STEP = 15
_OVERLAP = 2


def build_track_map(tel: pd.DataFrame, color_by: str = "Speed") -> go.Figure:
    col = color_by
    colorscale = _COLORSCALES.get(col, "RdYlGn")
    unit = _UNITS.get(col, "")

    values = tel[col].astype(float).values
    x, y = tel["X"].values, tel["Y"].values
    dist = tel["Distance"].values

    v_min, v_max = float(values.min()), float(values.max())
    if v_max <= v_min:
        v_max = v_min + 1.0

    fig = go.Figure()

    seg_starts = list(range(0, len(tel) - _STEP, _STEP - _OVERLAP))
    seg_norms = [
        min(max((values[i:i + _STEP].mean() - v_min) / (v_max - v_min), 0.0), 1.0)
        for i in seg_starts
    ]
    seg_colors = sample_colorscale(colorscale, seg_norms)

    for idx, i in enumerate(seg_starts):
        end = min(i + _STEP + 1, len(tel))
        fig.add_trace(go.Scatter(
            x=x[i:end], y=y[i:end],
            mode="lines",
            line=dict(color=seg_colors[idx], width=4),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Invisible markers layer: provides colorbar and hover tooltips
    fmt = ".0f" if col == "Gear" else ".1f"
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="markers",
        marker=dict(
            color=values,
            colorscale=colorscale,
            size=6,
            opacity=0,
            colorbar=dict(
                title=dict(text=f"{col}{unit}", font=dict(color="#ffffff")),
                tickfont=dict(color="#ffffff"),
                outlinecolor="#1e1e2e",
            ),
            showscale=True,
        ),
        customdata=list(zip(dist, values)),
        hovertemplate=f"Distance: %{{customdata[0]:.0f}} m<br>{col}: %{{customdata[1]:{fmt}}}{unit}<extra></extra>",
        showlegend=False,
    ))

    pad = 300
    x_range = [tel["X"].min() - pad, tel["X"].max() + pad]
    y_range = [tel["Y"].min() - pad, tel["Y"].max() + pad]

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=580,
        margin=dict(l=10, r=80, t=10, b=10),
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1, range=x_range),
        yaxis=dict(visible=False, range=y_range),
        showlegend=False,
    )
    return fig
