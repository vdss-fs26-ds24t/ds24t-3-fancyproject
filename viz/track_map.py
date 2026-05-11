import plotly.graph_objects as go
import pandas as pd

_COLORSCALES = {
    "Speed": "RdYlGn",
    "Throttle": "RdYlGn",
    "Brake": "RdYlGn_r",
    "Gear": "Viridis",
}
_UNITS = {"Speed": " km/h", "Throttle": "%", "Brake": "", "Gear": ""}


def build_track_map(tel: pd.DataFrame, color_by: str = "Speed") -> go.Figure:
    col = color_by
    colorscale = _COLORSCALES.get(col, "RdYlGn")
    unit = _UNITS.get(col, "")

    fig = go.Figure(go.Scatter(
        x=tel["X"],
        y=tel["Y"],
        mode="markers",
        marker=dict(
            color=tel[col],
            colorscale=colorscale,
            size=3,
            colorbar=dict(
                title=dict(text=f"{col}{unit}", font=dict(color="#ffffff")),
                tickfont=dict(color="#ffffff"),
                outlinecolor="#1e1e2e",
            ),
            showscale=True,
        ),
        customdata=list(zip(tel["Distance"].values, tel[col].values)),
        hovertemplate=f"Distance: %{{customdata[0]:.0f}} m<br>{col}: %{{customdata[1]}}{unit}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=550,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig
