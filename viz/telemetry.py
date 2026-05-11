import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def build_telemetry_chart(
    tel_a: pd.DataFrame,
    tel_b: pd.DataFrame,
    driver: str,
    lap_a: int,
    lap_b: int,
) -> go.Figure:
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=("Speed (km/h)", "Throttle (%)", "Brake"),
        row_heights=[0.4, 0.35, 0.25],
    )

    traces = [
        (tel_a, lap_a, "solid"),
        (tel_b, lap_b, "dash"),
    ]

    for tel, lap_num, dash in traces:
        label = f"Lap {lap_num}"
        show = dash == "solid"

        fig.add_trace(go.Scatter(
            x=tel["Distance"], y=tel["Speed"],
            name=label, legendgroup=label, showlegend=show,
            line=dict(color="#43b02a", dash=dash, width=1.5),
            hovertemplate=f"Lap {lap_num} · %{{x:.0f}}m<br>Speed: %{{y:.0f}} km/h<extra></extra>",
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=tel["Distance"], y=tel["Throttle"],
            name=label, legendgroup=label, showlegend=False,
            line=dict(color="#ffd600", dash=dash, width=1.5),
            hovertemplate=f"Lap {lap_num} · Throttle: %{{y:.0f}}%<extra></extra>",
        ), row=2, col=1)

        brake_vals = tel["Brake"].astype(int)
        fig.add_trace(go.Scatter(
            x=tel["Distance"], y=brake_vals,
            name=label, legendgroup=label, showlegend=False,
            line=dict(color="#e8002d", dash=dash, width=1.5),
            fill="tozeroy", fillcolor="#e8002d22",
            hovertemplate=f"Lap {lap_num} · Brake: %{{y}}<extra></extra>",
        ), row=3, col=1)

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=520,
        margin=dict(l=60, r=20, t=50, b=50),
        legend=dict(bgcolor="#12141f", bordercolor="#1e1e2e", borderwidth=1),
        hovermode="x unified",
        title_text=f"{driver} — Lap {lap_a} vs Lap {lap_b}",
        title_font_color="#ffffff",
    )

    for row in range(1, 4):
        fig.update_xaxes(gridcolor="#222222", zeroline=False, row=row, col=1)
        fig.update_yaxes(gridcolor="#222222", zeroline=False, row=row, col=1)

    fig.update_xaxes(title_text="Distance (m)", row=3, col=1)

    return fig
