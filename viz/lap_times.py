import numpy as np
import plotly.graph_objects as go
import pandas as pd

COMPOUND_COLORS = {
    "SOFT": "#e8002d",
    "MEDIUM": "#ffd600",
    "HARD": "#ebebeb",
    "INTERMEDIATE": "#43b02a",
    "WET": "#0067ff",
}
_LINE_DASHES = ["solid", "dash"]


def format_laptime(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:06.3f}"


def build_lap_chart(
    laps: pd.DataFrame,
    show_stints: list | None = None,
    hide_outliers: bool = True,
    competitor_laps: pd.DataFrame | None = None,
) -> go.Figure:
    fig = go.Figure()
    drivers = laps["Driver"].unique().tolist()

    filtered = laps.copy()
    if hide_outliers:
        median_time = filtered.groupby("Driver")["LapTimeSec"].transform("median")
        filtered = filtered[filtered["LapTimeSec"] <= median_time * 1.07]
    if show_stints:
        filtered = filtered[filtered["Stint"].isin(show_stints)]

    pit_laps_added: set = set()

    for i, driver in enumerate(drivers):
        driver_laps = filtered[filtered["Driver"] == driver]
        stints = sorted(driver_laps["Stint"].unique())

        for stint_num in stints:
            stint_laps = driver_laps[driver_laps["Stint"] == stint_num].sort_values("LapNumber")
            if stint_laps.empty:
                continue
            compound = str(stint_laps["Compound"].iloc[0])
            color = COMPOUND_COLORS.get(compound, "#aaaaaa")
            dash = _LINE_DASHES[i % len(_LINE_DASHES)]

            if stint_num > 1:
                pit_lap = float(stint_laps["LapNumber"].min()) - 0.5
                pit_key = (driver, stint_num)
                if pit_key not in pit_laps_added:
                    pit_laps_added.add(pit_key)
                    fig.add_vline(
                        x=pit_lap,
                        line_color="#555555",
                        line_dash="dot",
                        line_width=1,
                        annotation_text="PIT",
                        annotation_font_color="#555555",
                        annotation_font_size=9,
                        annotation_position="top",
                    )

            x_vals = stint_laps["LapNumber"].values
            y_vals = stint_laps["LapTimeSec"].values
            if len(x_vals) > 2:
                z = np.polyfit(x_vals, y_vals, 1)
                p = np.poly1d(z)
                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=p(x_vals),
                    mode="lines",
                    line=dict(color=color, width=1.5, dash="dot"),
                    opacity=0.5,
                    showlegend=False,
                    hoverinfo="skip",
                ))

            custom = list(zip(
                stint_laps["TyreLife"].values,
                [format_laptime(t) for t in stint_laps["LapTimeSec"].values],
            ))
            fig.add_trace(go.Scatter(
                x=stint_laps["LapNumber"],
                y=stint_laps["LapTimeSec"],
                mode="lines+markers",
                name=f"{driver} S{stint_num} ({compound.capitalize()})",
                line=dict(color=color, width=2, dash=dash),
                marker=dict(size=4, color=color),
                customdata=custom,
                hovertemplate=(
                    f"<b>{driver}</b> · Lap %{{x}}<br>"
                    f"{compound.capitalize()} (age: %{{customdata[0]:.0f}} laps)<br>"
                    f"Time: %{{customdata[1]}}<extra></extra>"
                ),
            ))

    # Competitor overlay — muted gray, no trendline
    if competitor_laps is not None and not competitor_laps.empty:
        comp = competitor_laps.copy()
        if hide_outliers:
            median_c = comp["LapTimeSec"].median()
            comp = comp[comp["LapTimeSec"] <= median_c * 1.07]

        comp_driver = str(comp["Driver"].iloc[0]) if not comp.empty else "Competitor"
        stints_c = sorted(comp["Stint"].dropna().unique())

        for stint_num in stints_c:
            stint_laps = comp[comp["Stint"] == stint_num].sort_values("LapNumber")
            if stint_laps.empty:
                continue
            compound = str(stint_laps["Compound"].iloc[0])
            custom = list(zip(
                stint_laps["TyreLife"].values,
                [format_laptime(t) for t in stint_laps["LapTimeSec"].values],
            ))
            fig.add_trace(go.Scatter(
                x=stint_laps["LapNumber"],
                y=stint_laps["LapTimeSec"],
                mode="lines+markers",
                name=f"{comp_driver} S{stint_num} ({compound.capitalize()})",
                line=dict(color="#888888", width=1.5, dash="dot"),
                marker=dict(size=3, color="#888888"),
                opacity=0.7,
                customdata=custom,
                hovertemplate=(
                    f"<b>{comp_driver}</b> · Lap %{{x}}<br>"
                    f"{compound.capitalize()} (age: %{{customdata[0]:.0f}} laps)<br>"
                    f"Time: %{{customdata[1]}}<extra></extra>"
                ),
            ))

    all_times = filtered["LapTimeSec"].tolist()
    if competitor_laps is not None and not competitor_laps.empty:
        all_times += competitor_laps["LapTimeSec"].dropna().tolist()

    if all_times:
        min_t = min(all_times)
        max_t = max(all_times)
        tick_vals = np.arange(int(min_t) - 2, int(max_t) + 4, 2).tolist()
        tick_text = [format_laptime(t) for t in tick_vals]
    else:
        tick_vals, tick_text = [], []

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=500,
        margin=dict(l=70, r=20, t=20, b=50),
        xaxis=dict(title="Lap", gridcolor="#222222", zeroline=False),
        yaxis=dict(
            title="Lap Time",
            tickvals=tick_vals,
            ticktext=tick_text,
            gridcolor="#222222",
            zeroline=False,
        ),
        legend=dict(bgcolor="#12141f", bordercolor="#1e1e2e", borderwidth=1),
        hovermode="x unified",
    )
    return fig
