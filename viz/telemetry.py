import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

_COLOR_A = "#e8002d"   # red
_COLOR_B = "#00cfff"   # sky blue


def build_telemetry_chart(
    tel_a: pd.DataFrame,
    tel_b: pd.DataFrame,
    driver_a: str,
    driver_b: str,
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
        (tel_a, driver_a, lap_a, _COLOR_A, "solid"),
        (tel_b, driver_b, lap_b, _COLOR_B, "dash"),
    ]

    for tel, driver, lap_num, color, dash in traces:
        label = f"{driver} · Lap {lap_num}"

        fig.add_trace(go.Scatter(
            x=tel["Distance"], y=tel["Speed"],
            name=label, legendgroup=label, showlegend=True,
            line=dict(color=color, dash=dash, width=1.5),
            hovertemplate=f"<b>{driver}</b> · %{{x:.0f}} m<br>Speed: %{{y:.0f}} km/h<extra></extra>",
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=tel["Distance"], y=tel["Throttle"],
            name=label, legendgroup=label, showlegend=False,
            line=dict(color=color, dash=dash, width=1.5),
            hovertemplate=f"<b>{driver}</b> · Throttle: %{{y:.0f}}%<extra></extra>",
        ), row=2, col=1)

        r, g, b = (232, 0, 45) if color == _COLOR_A else (0, 207, 255)
        brake_vals = tel["Brake"].astype(int)
        fig.add_trace(go.Scatter(
            x=tel["Distance"], y=brake_vals,
            name=label, legendgroup=label, showlegend=False,
            line=dict(color=color, dash=dash, width=1.5),
            fill="tozeroy", fillcolor=f"rgba({r},{g},{b},0.15)",
            hovertemplate=f"<b>{driver}</b> · Brake: %{{y}}<extra></extra>",
        ), row=3, col=1)

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=540,
        margin=dict(l=60, r=20, t=50, b=50),
        legend=dict(bgcolor="#12141f", bordercolor="#1e1e2e", borderwidth=1),
        hovermode="x unified",
        title_text=f"{driver_a} vs {driver_b}",
        title_font_color="#ffffff",
    )

    for row in range(1, 4):
        fig.update_xaxes(gridcolor="#222222", zeroline=False, row=row, col=1)
        fig.update_yaxes(gridcolor="#222222", zeroline=False, row=row, col=1)

    fig.update_xaxes(title_text="Distance (m)", row=3, col=1)

    return fig
