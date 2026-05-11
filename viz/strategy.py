import plotly.graph_objects as go
import pandas as pd

COMPOUND_COLORS = {
    "SOFT": "#e8002d",
    "MEDIUM": "#ffd600",
    "HARD": "#ebebeb",
    "INTERMEDIATE": "#43b02a",
    "WET": "#0067ff",
}


def build_stint_chart(laps: pd.DataFrame, ferrari_drivers: list, height: int | None = None) -> go.Figure:
    fig = go.Figure()
    added_compounds: set = set()

    results_pos = laps.groupby("Driver")["Position"].min()
    try:
        driver_order = results_pos.sort_values().index.tolist()
    except Exception:
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
                marker_line_color="white" if is_ferrari else color,
                marker_line_width=1.5 if is_ferrari else 0,
                legendgroup=compound,
                showlegend=show_legend,
                hovertemplate=(
                    f"<b>{driver}</b><br>"
                    f"Stint {stint_num} · {compound.capitalize()}<br>"
                    f"Laps {start_lap}–{end_lap} ({lap_count} laps)<br>"
                    f"Tyre age: {tyre_life} laps<extra></extra>"
                ),
            ))

    computed_height = height or max(400, len(driver_order_reversed) * 30 + 80)

    fig.update_layout(
        barmode="overlay",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=computed_height,
        margin=dict(l=50, r=20, t=20, b=50),
        xaxis=dict(title="Lap", gridcolor="#222222", zeroline=False),
        yaxis=dict(
            title="",
            categoryorder="array",
            categoryarray=driver_order_reversed,
        ),
        legend=dict(
            title="Compound",
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="left",
            x=0,
        ),
    )
    return fig
