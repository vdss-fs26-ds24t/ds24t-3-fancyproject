from plotly.subplots import make_subplots
import numpy as np
import plotly.graph_objects as go
import pandas as pd

COMPOUND_COLORS = {
    "SOFT": "#e8002d",
    "MEDIUM": "#ffd600",
    "HARD": "#d9d9d9",
    "INTERMEDIATE": "#43b02a",
    "WET": "#0067ff",
}

_FERRARI_LINE_COLORS = ["#e8002d", "#ffffff"]
_COMPETITOR_COLOR = "#4fc3f7"


def format_laptime(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:06.3f}"


def _strip_y(idx: int) -> tuple[float, float]:
    """y-coords for strip at position idx (0=bottom). Fills 90% of each unit slot."""
    return (idx * 1.0 + 0.05, idx * 1.0 + 0.95)


def _draw_strip(
    fig: go.Figure,
    laps_df: pd.DataFrame,
    strip_idx: int,
    compounds_out: set,
) -> float:
    """Draw one seamless compound strip. Never filters — always shows all stints."""
    y_bot, y_top = _strip_y(strip_idx)
    y_mid = (y_bot + y_top) / 2

    df = laps_df.dropna(subset=["Stint", "LapNumber"]).sort_values("LapNumber")
    if df.empty:
        return y_mid

    stints = sorted(df["Stint"].unique())
    # Build per-stint boundaries so they tile seamlessly with no gaps
    stint_info = []
    for stint_num in stints:
        s = df[df["Stint"] == stint_num]
        if s.empty:
            continue
        stint_info.append({
            "num": stint_num,
            "first": float(s["LapNumber"].min()),
            "last": float(s["LapNumber"].max()),
            "compound": str(s["Compound"].iloc[0]).upper(),
        })

    for j, si in enumerate(stint_info):
        compounds_out.add(si["compound"])
        comp_color = COMPOUND_COLORS.get(si["compound"], "#aaaaaa")
        text_color = "#000000" if si["compound"] in ("MEDIUM", "HARD") else "#ffffff"

        # Seamless tiling: share exact boundary with adjacent stints
        if j == 0:
            x0 = si["first"] - 0.5
        else:
            x0 = (stint_info[j - 1]["last"] + si["first"]) / 2

        if j == len(stint_info) - 1:
            x1 = si["last"] + 0.5
        else:
            x1 = (si["last"] + stint_info[j + 1]["first"]) / 2

        # Filled rectangle — no border so stints touch seamlessly
        fig.add_trace(go.Scatter(
            x=[x0, x0, x1, x1, x0],
            y=[y_bot, y_top, y_top, y_bot, y_bot],
            fill="toself",
            fillcolor=comp_color,
            line=dict(width=0),
            mode="lines",
            showlegend=False,
            hoverinfo="skip",
        ), row=2, col=1)

        fig.add_trace(go.Scatter(
            x=[(x0 + x1) / 2],
            y=[y_mid],
            mode="text",
            text=[f"Stint {int(si['num'])}"],
            textfont=dict(size=11, color=text_color),
            showlegend=False,
            hoverinfo="skip",
        ), row=2, col=1)

    return y_mid


def build_lap_chart(
    laps: pd.DataFrame,
    show_stints: list | None = None,
    hide_outliers: bool = True,
    competitor_laps: pd.DataFrame | None = None,
) -> go.Figure:
    has_competitor = competitor_laps is not None and not competitor_laps.empty
    n_strips = min(len(laps["Driver"].unique()), 2) + (1 if has_competitor else 0)

    strip_frac = 0.10 * n_strips
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[1.0 - strip_frac - 0.04, strip_frac + 0.04],
        shared_xaxes=True,
        vertical_spacing=0.04,
    )

    drivers = laps["Driver"].unique().tolist()

    # Filtered laps for the line chart only
    filtered = laps.copy()
    if hide_outliers:
        median_time = filtered.groupby("Driver")["LapTimeSec"].transform("median")
        filtered = filtered[filtered["LapTimeSec"] <= median_time * 1.07]
    if show_stints is not None:
        filtered = filtered[filtered["Stint"].isin(show_stints)]

    # Pit stop lines — span both rows, based on filtered Ferrari laps
    pit_laps_drawn: set = set()
    for driver in drivers:
        for stint_num in sorted(filtered[filtered["Driver"] == driver]["Stint"].unique()):
            if stint_num <= 1:
                continue
            s_laps = filtered[(filtered["Driver"] == driver) & (filtered["Stint"] == stint_num)]
            if s_laps.empty:
                continue
            pit_x = float(s_laps["LapNumber"].min()) - 0.5
            if pit_x not in pit_laps_drawn:
                pit_laps_drawn.add(pit_x)
                fig.add_vline(
                    x=pit_x,
                    line_color="#3a3a3a",
                    line_dash="dot",
                    line_width=1.5,
                    annotation_text="PIT",
                    annotation_font_color="#666666",
                    annotation_font_size=9,
                    annotation_position="top",
                )

    # Invisible header trace — first entry in unified hover shows "Lap X" prominently
    if not filtered.empty:
        all_lx = sorted(filtered["LapNumber"].unique().tolist())
        _med_y = filtered["LapTimeSec"].median()
        fig.add_trace(go.Scatter(
            x=all_lx,
            y=[_med_y] * len(all_lx),
            mode="markers",
            marker=dict(size=0, opacity=0),
            showlegend=False,
            hovertemplate="<b>Lap %{x:.0f}</b><extra></extra>",
            name="",
        ), row=1, col=1)

    # Ferrari lines + per-stint degradation trendlines (row 1)
    for i, driver in enumerate(drivers):
        d_laps = filtered[filtered["Driver"] == driver].sort_values("LapNumber")
        if d_laps.empty:
            continue
        line_color = _FERRARI_LINE_COLORS[i % len(_FERRARI_LINE_COLORS)]

        # Pre-compute slopes so they appear in hover and trendline traces
        stint_trends: dict = {}
        for stint_num in sorted(d_laps["Stint"].unique()):
            s = d_laps[d_laps["Stint"] == stint_num]
            if len(s) >= 4:
                xv = s["LapNumber"].values.astype(float)
                yv = s["LapTimeSec"].values
                sl, ic = np.polyfit(xv, yv, 1)
                stint_trends[int(stint_num)] = (float(sl), float(ic))

        slope_strs = [
            (f"{stint_trends[int(s)][0]:+.3f} s/lap" if int(s) in stint_trends else "—")
            for s in d_laps["Stint"].values
        ]
        custom = list(zip(
            d_laps["Stint"].values,
            d_laps["Compound"].fillna("?").values,
            d_laps["TyreLife"].values,
            [format_laptime(t) for t in d_laps["LapTimeSec"].values],
            slope_strs,
        ))
        fig.add_trace(go.Scatter(
            x=d_laps["LapNumber"],
            y=d_laps["LapTimeSec"],
            mode="lines",
            name=driver,
            line=dict(color=line_color, width=2.5),
            customdata=custom,
            hovertemplate=(
                f"<b>{driver}</b>  %{{customdata[3]}}<br>"
                "S%{customdata[0]} · %{customdata[1]} · %{customdata[2]:.0f} laps<br>"
                "Trend: %{customdata[4]}<extra></extra>"
            ),
        ), row=1, col=1)

        # Trendlines using pre-computed slopes
        for stint_num, (slope, intercept) in stint_trends.items():
            s = d_laps[d_laps["Stint"] == stint_num]
            x_v = s["LapNumber"].values.astype(float)
            fig.add_trace(go.Scatter(
                x=x_v,
                y=slope * x_v + intercept,
                mode="lines",
                line=dict(color=line_color, width=1.5, dash="dot"),
                opacity=0.5,
                showlegend=False,
                hoverinfo="skip",
            ), row=1, col=1)

    # Competitor (row 1) — light blue; outlier filter for line only
    if has_competitor:
        comp = competitor_laps.copy().sort_values("LapNumber")
        if hide_outliers:
            median_c = comp["LapTimeSec"].median()
            comp = comp[comp["LapTimeSec"] <= median_c * 1.07]
        comp_driver = str(competitor_laps["Driver"].iloc[0])

        # Pre-compute competitor slopes
        comp_trends: dict = {}
        for stint_num in sorted(comp["Stint"].unique()):
            cs = comp[comp["Stint"] == stint_num]
            if len(cs) >= 4:
                xv = cs["LapNumber"].values.astype(float)
                yv = cs["LapTimeSec"].values
                sl, ic = np.polyfit(xv, yv, 1)
                comp_trends[int(stint_num)] = (float(sl), float(ic))

        comp_slope_strs = [
            (f"{comp_trends[int(s)][0]:+.3f} s/lap" if int(s) in comp_trends else "—")
            for s in comp["Stint"].values
        ]
        custom_c = list(zip(
            comp["Stint"].values,
            comp["Compound"].fillna("?").values,
            comp["TyreLife"].values,
            [format_laptime(t) for t in comp["LapTimeSec"].values],
            comp_slope_strs,
        ))
        fig.add_trace(go.Scatter(
            x=comp["LapNumber"],
            y=comp["LapTimeSec"],
            mode="lines",
            name=comp_driver,
            line=dict(color=_COMPETITOR_COLOR, width=1.5),
            customdata=custom_c,
            hovertemplate=(
                f"<b>{comp_driver}</b>  %{{customdata[3]}}<br>"
                "S%{customdata[0]} · %{customdata[1]} · %{customdata[2]:.0f} laps<br>"
                "Trend: %{customdata[4]}<extra></extra>"
            ),
        ), row=1, col=1)

        # Competitor trendlines
        for stint_num, (slope, intercept) in comp_trends.items():
            cs = comp[comp["Stint"] == stint_num]
            x_v = cs["LapNumber"].values.astype(float)
            fig.add_trace(go.Scatter(
                x=x_v,
                y=slope * x_v + intercept,
                mode="lines",
                line=dict(color=_COMPETITOR_COLOR, width=1.5, dash="dot"),
                opacity=0.5,
                showlegend=False,
                hoverinfo="skip",
            ), row=1, col=1)

    # Compound strips (row 2) — always use raw unfiltered laps, never outlier-filter
    compounds_in_data: set = set()
    y_tick_vals: list = []
    y_tick_text: list = []

    n_ferrari = min(len(drivers), 2)
    for i, driver in enumerate(drivers[:n_ferrari]):
        strip_idx = n_strips - 1 - i  # LEC → top slot, HAM → next
        # Use raw laps (not filtered) so no stints are dropped from the strip
        d_laps_raw = laps[laps["Driver"] == driver].sort_values("LapNumber")
        if d_laps_raw.empty:
            continue
        y_mid = _draw_strip(fig, d_laps_raw, strip_idx, compounds_in_data)
        y_tick_vals.append(y_mid)
        y_tick_text.append(driver)

    if has_competitor:
        comp_driver = str(competitor_laps["Driver"].iloc[0])
        y_mid = _draw_strip(fig, competitor_laps.copy(), 0, compounds_in_data)
        y_tick_vals.append(y_mid)
        y_tick_text.append(comp_driver)

    # Trendline legend entry (explains dotted lines in chart)
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines",
        name="Stint trend (s/lap)",
        line=dict(color="#888888", width=1.5, dash="dot"),
        showlegend=True,
    ), row=1, col=1)

    # Compound legend chips
    for compound in ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]:
        if compound in compounds_in_data:
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=10, color=COMPOUND_COLORS[compound], symbol="square"),
                name=compound.capitalize(),
                showlegend=True,
            ), row=1, col=1)

    # Y-axis range — exclude outlier/inter laps so scale stays tight
    all_times = filtered["LapTimeSec"].tolist()
    if has_competitor:
        comp_range = competitor_laps.copy()
        if hide_outliers:
            median_c = comp_range["LapTimeSec"].median()
            comp_range = comp_range[comp_range["LapTimeSec"] <= median_c * 1.07]
        all_times += comp_range["LapTimeSec"].dropna().tolist()

    if all_times:
        min_t, max_t = min(all_times), max(all_times)
        tick_vals = np.arange(int(min_t) - 2, int(max_t) + 4, 2).tolist()
        tick_text = [format_laptime(t) for t in tick_vals]
    else:
        tick_vals, tick_text = [], []

    fig.update_xaxes(gridcolor="#222222", zeroline=False, showspikes=False, row=1, col=1)
    fig.update_xaxes(title_text="Lap", gridcolor="#222222", zeroline=False, showspikes=False, row=2, col=1)
    fig.update_yaxes(
        title_text="Lap Time (min:sec)",
        tickvals=tick_vals,
        ticktext=tick_text,
        gridcolor="#222222",
        zeroline=False,
        row=1, col=1,
    )
    fig.update_yaxes(
        tickmode="array",
        tickvals=y_tick_vals,
        ticktext=y_tick_text,
        tickfont=dict(color="#aaaaaa", size=9),
        showgrid=False,
        zeroline=False,
        range=[0, n_strips],
        fixedrange=True,
        row=2, col=1,
    )

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=520 + n_strips * 20,
        margin=dict(l=70, r=20, t=20, b=40),
        legend=dict(bgcolor="#12141f", bordercolor="#1e1e2e", borderwidth=1),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1a1a2e",
            bordercolor="#3a3a5c",
            font=dict(color="#ffffff", size=12),
            align="left",
        ),
    )
    return fig


def compute_stint_stats(
    laps: pd.DataFrame,
    show_stints: list | None = None,
    hide_outliers: bool = True,
) -> dict:
    """Return per-driver, per-stint degradation stats for the analysis panel.

    Structure: {driver: {stint_num: {compound, slope, best_sec, avg_sec, laps}}}
    slope is seconds-per-lap (positive = degrading).
    """
    filtered = laps.copy()
    if hide_outliers:
        m = filtered.groupby("Driver")["LapTimeSec"].transform("median")
        filtered = filtered[filtered["LapTimeSec"] <= m * 1.07]
    if show_stints is not None:
        filtered = filtered[filtered["Stint"].isin(show_stints)]

    result: dict = {}
    for driver in filtered["Driver"].unique():
        result[driver] = {}
        d_laps = filtered[filtered["Driver"] == driver].sort_values("LapNumber")
        for stint_num in sorted(d_laps["Stint"].unique()):
            s = d_laps[d_laps["Stint"] == stint_num]
            if len(s) < 3:
                continue
            x = s["LapNumber"].values.astype(float)
            y = s["LapTimeSec"].values
            slope = float(np.polyfit(x, y, 1)[0])
            result[driver][int(stint_num)] = {
                "compound": str(s["Compound"].iloc[0]).capitalize(),
                "slope": slope,
                "best_sec": float(y.min()),
                "avg_sec": float(y.mean()),
                "laps": len(s),
            }
    return result
