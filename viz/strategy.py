import plotly.graph_objects as go
import pandas as pd

COMPOUND_COLORS = {
    "SOFT": "#e8002d",
    "MEDIUM": "#ffd600",
    "HARD": "#ebebeb",
    "INTERMEDIATE": "#43b02a",
    "WET": "#0067ff",
}

_FERRARI_RED = "#e8002d"
_FERRARI_BORDER = "#ff4444"


def build_stint_chart(laps: pd.DataFrame, ferrari_drivers: list, height: int | None = None) -> go.Figure:
    fig = go.Figure()
    added_compounds: set = set()

    pos_data = laps.dropna(subset=["Position"])
    if not pos_data.empty:
        final_pos = (
            pos_data.sort_values("LapNumber")
            .groupby("Driver")["Position"]
            .last()
        )
        driver_order = final_pos.sort_values().index.tolist()
    else:
        driver_order = laps["Driver"].unique().tolist()
    driver_order_reversed = driver_order[::-1]

    for driver in driver_order_reversed:
        driver_laps = laps[laps["Driver"] == driver].copy()
        is_ferrari = driver in ferrari_drivers

        for stint_num in sorted(driver_laps["Stint"].unique()):
            stint_laps = driver_laps[driver_laps["Stint"] == stint_num].sort_values("LapNumber")
            if stint_laps.empty:
                continue
            compound = str(stint_laps["Compound"].iloc[0])
            color = COMPOUND_COLORS.get(compound, "#aaaaaa")
            start_lap = int(stint_laps["LapNumber"].min())
            end_lap = int(stint_laps["LapNumber"].max())
            lap_count = end_lap - start_lap + 1
            tyre_life = int(stint_laps["TyreLife"].max()) if "TyreLife" in stint_laps.columns else lap_count

            show_legend = compound not in added_compounds
            if show_legend:
                added_compounds.add(compound)

            fig.add_trace(go.Bar(
                name=compound.capitalize(),
                orientation="h",
                y=[driver],
                x=[lap_count],
                base=[start_lap - 1],
                marker_color=color,
                marker_line_color=_FERRARI_BORDER if is_ferrari else "rgba(0,0,0,0)",
                marker_line_width=3 if is_ferrari else 0,
                legendgroup=compound,
                showlegend=show_legend,
                hovertemplate=(
                    f"<b>{driver}</b>{'  ★' if is_ferrari else ''}<br>"
                    f"Stint {stint_num} · {compound.capitalize()}<br>"
                    f"Laps {start_lap}–{end_lap} ({lap_count} laps)<br>"
                    f"Tyre age: {tyre_life} laps<extra></extra>"
                ),
            ))

    computed_height = height or max(420, len(driver_order_reversed) * 30 + 80)

    fig.update_layout(
        barmode="overlay",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=computed_height,
        margin=dict(l=50, r=20, t=20, b=60),
        xaxis=dict(title="Lap", gridcolor="#222222", zeroline=False),
        yaxis=dict(
            title="",
            categoryorder="array",
            categoryarray=driver_order_reversed,
            tickfont=dict(
                color="#ff4444",
            ) if False else dict(),
        ),
        legend=dict(
            title="Compound",
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="left",
            x=0,
        ),
    )
    return fig


def build_position_chart(laps: pd.DataFrame, ferrari_drivers: list) -> go.Figure:
    fig = go.Figure()

    pos_data = laps.dropna(subset=["Position"]).copy()
    pos_data["Position"] = pos_data["Position"].astype(int)

    final_pos = (
        pos_data.sort_values("LapNumber")
        .groupby("Driver")["Position"]
        .last()
    )
    driver_order = final_pos.sort_values().index.tolist()

    # Non-Ferrari first so Ferrari renders on top
    for driver in driver_order:
        if driver in ferrari_drivers:
            continue
        driver_laps = pos_data[pos_data["Driver"] == driver].sort_values("LapNumber")
        if driver_laps.empty:
            continue
        fig.add_trace(go.Scatter(
            x=driver_laps["LapNumber"],
            y=driver_laps["Position"],
            mode="lines",
            name=driver,
            line=dict(color="#3a3a3a", width=1),
            showlegend=False,
            hovertemplate=f"<b>{driver}</b> · Lap %{{x}}<br>P%{{y:.0f}}<extra></extra>",
        ))

    # Ferrari drivers on top — bold red
    for driver in ferrari_drivers:
        driver_laps = pos_data[pos_data["Driver"] == driver].sort_values("LapNumber")
        if driver_laps.empty:
            continue
        fig.add_trace(go.Scatter(
            x=driver_laps["LapNumber"],
            y=driver_laps["Position"],
            mode="lines+markers",
            name=driver,
            line=dict(color=_FERRARI_RED, width=3),
            marker=dict(size=4, color=_FERRARI_RED),
            showlegend=True,
            hovertemplate=f"<b>{driver}</b> · Lap %{{x}}<br>P%{{y:.0f}}<extra></extra>",
        ))
        last_row = driver_laps.iloc[-1]
        fig.add_annotation(
            x=last_row["LapNumber"],
            y=last_row["Position"],
            text=f"<b>{driver}</b>",
            showarrow=False,
            xanchor="left",
            xshift=7,
            font=dict(color=_FERRARI_RED, size=11),
        )

    num_drivers = pos_data["Driver"].nunique()
    max_lap = int(pos_data["LapNumber"].max())

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=420,
        margin=dict(l=50, r=80, t=20, b=50),
        xaxis=dict(
            title="Lap",
            gridcolor="#222222",
            zeroline=False,
            range=[1, max_lap + 7],
        ),
        yaxis=dict(
            title="Position",
            gridcolor="#222222",
            zeroline=False,
            range=[num_drivers + 0.5, 0.5],
            tickvals=list(range(1, num_drivers + 1)),
            ticktext=[f"P{i}" for i in range(1, num_drivers + 1)],
        ),
        legend=dict(bgcolor="#12141f", bordercolor="#1e1e2e", borderwidth=1),
        hovermode="closest",
    )
    return fig
