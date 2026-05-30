import plotly.graph_objects as go
import pandas as pd

_COLOR_A = "#e8002d"   # red
_COLOR_B = "#00cfff"   # sky blue

# y-axis domains: speed top, throttle middle, brake bottom
_DOM_SPEED    = [0.62, 1.00]
_DOM_THROTTLE = [0.33, 0.58]
_DOM_BRAKE    = [0.00, 0.25]


def build_telemetry_chart(
    tel_a: pd.DataFrame,
    tel_b: pd.DataFrame,
    driver_a: str,
    driver_b: str,
    lap_a: int,
    lap_b: int,
) -> go.Figure:
    fig = go.Figure()

    traces = [
        (tel_a, driver_a, lap_a, _COLOR_A, "solid"),
        (tel_b, driver_b, lap_b, _COLOR_B, "dash"),
    ]

    for tel, driver, lap_num, color, dash in traces:
        label = f"{driver} · Lap {lap_num}"
        r, g, b_val = (232, 0, 45) if color == _COLOR_A else (0, 207, 255)

        # Speed — primary y-axis (y1)
        fig.add_trace(go.Scatter(
            x=tel["Distance"], y=tel["Speed"],
            name=label, legendgroup=label, showlegend=True,
            yaxis="y1",
            line=dict(color=color, dash=dash, width=1.5),
            hovertemplate=f"<b>{driver}</b>  %{{y:.0f}} km/h<extra></extra>",
        ))

        # Throttle — secondary y-axis, same x-axis
        fig.add_trace(go.Scatter(
            x=tel["Distance"], y=tel["Throttle"],
            name=label, legendgroup=label, showlegend=False,
            xaxis="x", yaxis="y2",
            line=dict(color=color, dash=dash, width=1.5),
            hovertemplate=f"{driver}  %{{y:.0f}}%<extra></extra>",
        ))

        # Brake — tertiary y-axis, same x-axis
        brake_vals = tel["Brake"].astype(int)
        fig.add_trace(go.Scatter(
            x=tel["Distance"], y=brake_vals,
            name=label, legendgroup=label, showlegend=False,
            xaxis="x", yaxis="y3",
            line=dict(color=color, dash=dash, width=1.5),
            fill="tozeroy", fillcolor=f"rgba({r},{g},{b_val},0.15)",
            hovertemplate=f"{driver}  Brake %{{y}}<extra></extra>",
        ))

    _ax = dict(gridcolor="#222222", zeroline=False, showline=False,
               tickfont=dict(color="#aaaaaa"), linecolor="#222222")

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=560,
        margin=dict(l=70, r=20, t=50, b=65),
        legend=dict(bgcolor="#12141f", bordercolor="#1e1e2e", borderwidth=1),
        hovermode="x unified",   # single x-axis → unified hover covers all 6 traces
        hoversubplots="axis",    # aggregate hover across all y-axis domains sharing xaxis
        title_text=f"{driver_a} vs {driver_b}",
        title_font_color="#ffffff",

        # Single shared x-axis
        xaxis=dict(
            **_ax,
            showspikes=True,
            spikemode="toaxis+across",
            spikesnap="cursor",
            spikecolor="#555555",
            spikethickness=1,
            spikedash="dot",
        ),

        # Speed y-axis (top panel)
        yaxis=dict(**_ax, domain=_DOM_SPEED,
                   title=dict(text="Speed (km/h)", standoff=5)),

        # Throttle y-axis (middle panel)
        yaxis2=dict(**_ax, domain=_DOM_THROTTLE, anchor="x",
                    title=dict(text="Throttle (%)", standoff=5)),

        # Brake y-axis (bottom panel)
        yaxis3=dict(**_ax, domain=_DOM_BRAKE, anchor="x",
                    title=dict(text="Brake", standoff=5)),

        # Panel labels as annotations
        annotations=[
            dict(text="Speed (km/h)", x=0, xref="paper",
                 y=_DOM_SPEED[1], yref="paper",
                 xanchor="left", yanchor="bottom",
                 showarrow=False, font=dict(color="#888888", size=11)),
            dict(text="Throttle (%)", x=0, xref="paper",
                 y=_DOM_THROTTLE[1], yref="paper",
                 xanchor="left", yanchor="bottom",
                 showarrow=False, font=dict(color="#888888", size=11)),
            dict(text="Brake", x=0, xref="paper",
                 y=_DOM_BRAKE[1], yref="paper",
                 xanchor="left", yanchor="bottom",
                 showarrow=False, font=dict(color="#888888", size=11)),
            dict(text="Distance (m)", x=0.5, xref="paper",
                 y=-0.08, yref="paper",
                 xanchor="center", yanchor="top",
                 showarrow=False, font=dict(color="#888888", size=11)),
        ],
    )

    return fig
