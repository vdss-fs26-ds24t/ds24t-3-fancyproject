import plotly.graph_objects as go
import pandas as pd

COMPOUND_COLORS = {
    "SOFT": "#e8002d",
    "MEDIUM": "#ffd600",
    "HARD": "#ebebeb",
    "INTERMEDIATE": "#43b02a",
    "WET": "#0067ff",
}

_FERRARI_LINE_COLORS = ["#e8002d", "#ffffff"]
_FERRARI_BORDER = "#ff4444"
_COMPETITOR_COLOR = "#4fc3f7"
_SC_COLOR = "rgba(255,200,0,0.08)"
_VSC_COLOR = "rgba(100,200,255,0.06)"


def _sc_vsc_bands(laps: pd.DataFrame) -> list[dict]:
    """Return list of {x0, x1, color, label} for SC/VSC runs."""
    if "TrackStatus" not in laps.columns:
        return []
    status_by_lap = (
        laps.dropna(subset=["LapNumber", "TrackStatus"])
        .groupby("LapNumber")["TrackStatus"]
        .first()
        .sort_index()
    )
    bands: list[dict] = []
    current: dict | None = None
    for lap, ts in status_by_lap.items():
        ts_str = str(ts)
        if ts_str in ("4", "5"):
            label, color = "SC", _SC_COLOR
        elif ts_str in ("6", "7"):
            label, color = "VSC", _VSC_COLOR
        else:
            if current:
                bands.append(current)
                current = None
            continue
        if current and current["label"] == label:
            current["x1"] = lap
        else:
            if current:
                bands.append(current)
            current = {"x0": lap, "x1": lap, "color": color, "label": label}
    if current:
        bands.append(current)
    return bands


def _add_bands(fig: go.Figure, bands: list[dict]) -> None:
    for b in bands:
        fig.add_vrect(
            x0=b["x0"] - 0.5,
            x1=b["x1"] + 0.5,
            fillcolor=b["color"],
            line_width=0,
            annotation_text=b["label"],
            annotation_position="top left",
            annotation_font=dict(color="#aaaaaa", size=9),
        )


def _pit_laps_for(driver_laps: pd.DataFrame) -> list[int]:
    """Return lap numbers where a new stint begins (pit lap = first lap of new stint)."""
    d = driver_laps.sort_values("LapNumber").copy()
    d["StintShift"] = d["Stint"].shift(1)
    pits = d[d["Stint"] != d["StintShift"]]["LapNumber"].tolist()
    return [int(p) for p in pits if not pd.isna(p)]


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

    bands = _sc_vsc_bands(laps)
    _add_bands(fig, bands)

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

    ferrari_colors = ["#e8002d", "#ffffff"]
    for ci, driver in enumerate(ferrari_drivers):
        driver_laps = pos_data[pos_data["Driver"] == driver].sort_values("LapNumber")
        if driver_laps.empty:
            continue
        line_color = ferrari_colors[ci % len(ferrari_colors)]
        fig.add_trace(go.Scatter(
            x=driver_laps["LapNumber"],
            y=driver_laps["Position"],
            mode="lines+markers",
            name=driver,
            line=dict(color=line_color, width=3),
            marker=dict(size=4, color=line_color),
            showlegend=False,
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
            font=dict(color=line_color, size=11),
        )

        pit_laps = _pit_laps_for(driver_laps)
        if pit_laps:
            pit_rows = driver_laps[driver_laps["LapNumber"].isin(pit_laps)]
            fig.add_trace(go.Scatter(
                x=pit_rows["LapNumber"],
                y=pit_rows["Position"],
                mode="markers",
                name=f"{driver} pit",
                marker=dict(
                    symbol="diamond",
                    size=8,
                    color=line_color,
                    line=dict(color="#ffffff", width=1),
                ),
                showlegend=False,
                hovertemplate=f"<b>{driver}</b> PIT · Lap %{{x}}<br>P%{{y:.0f}}<extra></extra>",
            ))

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


def build_gap_chart(
    all_laps: pd.DataFrame,
    ferrari_drivers: list,
    reference_driver: str | None = None,
    ref_label: str | None = None,
) -> go.Figure:
    fig = go.Figure()

    available_drivers = all_laps["Driver"].unique().tolist()

    if reference_driver and reference_driver in available_drivers:
        ref = reference_driver
    else:
        last_lap = all_laps["LapNumber"].max()
        last_laps = all_laps[all_laps["LapNumber"] == last_lap]
        if "Position" in last_laps.columns:
            winner_rows = last_laps.dropna(subset=["Position"])
            if not winner_rows.empty:
                ref = str(winner_rows.sort_values("Position").iloc[0]["Driver"])
            else:
                ref = None
        else:
            ref = None

    if ref is None or ref not in available_drivers:
        fig.add_annotation(
            text="Reference driver not found — cannot compute gap",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#aaaaaa", size=14),
        )
        fig.update_layout(
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(color="#ffffff"), height=420,
        )
        return fig

    def _cumtime(driver: str) -> pd.DataFrame:
        d = all_laps[all_laps["Driver"] == driver].sort_values("LapNumber").copy()
        d = d.dropna(subset=["LapTimeSec"])
        d["CumTimeSec"] = d["LapTimeSec"].cumsum()
        return d[["LapNumber", "CumTimeSec"]]

    ref_cum = _cumtime(ref).rename(columns={"CumTimeSec": "ref_cum"})

    bands = _sc_vsc_bands(all_laps)
    _add_bands(fig, bands)

    ref_driver_laps = all_laps[all_laps["Driver"] == ref].sort_values("LapNumber")
    ref_pit_laps = _pit_laps_for(ref_driver_laps)
    for pl in ref_pit_laps:
        fig.add_vline(
            x=pl,
            line_color=_COMPETITOR_COLOR,
            line_dash="dot",
            line_width=1,
            annotation_text=f"{ref} PIT",
            annotation_font=dict(color=_COMPETITOR_COLOR, size=8),
            annotation_position="top right",
        )

    fig.add_hline(
        y=0,
        line_color="#666666",
        line_width=1,
        annotation_text=f"← {ref_label or ref}",
        annotation_position="right",
        annotation_font=dict(color="#aaaaaa", size=10),
    )

    ferrari_colors = ["#e8002d", "#ffffff"]
    for ci, driver in enumerate(ferrari_drivers):
        if driver not in available_drivers:
            continue
        ferrari_cum = _cumtime(driver).rename(columns={"CumTimeSec": "ferrari_cum"})
        merged = pd.merge(ref_cum, ferrari_cum, on="LapNumber", how="inner")
        merged["gap"] = (merged["ferrari_cum"] - merged["ref_cum"]).round(3)

        line_color = ferrari_colors[ci % len(ferrari_colors)]
        fig.add_trace(go.Scatter(
            x=merged["LapNumber"],
            y=merged["gap"],
            mode="lines",
            name=driver,
            line=dict(color=line_color, width=2.5),
            showlegend=False,
            hovertemplate=f"<b>{driver}</b><br>Gap: %{{y:.2f}} s<extra></extra>",
        ))
        if not merged.empty:
            last_row = merged.iloc[-1]
            fig.add_annotation(
                x=last_row["LapNumber"],
                y=last_row["gap"],
                text=f"<b>{driver}</b>",
                showarrow=False,
                xanchor="left",
                xshift=7,
                font=dict(color=line_color, size=11),
            )

        driver_laps_df = all_laps[all_laps["Driver"] == driver].sort_values("LapNumber")
        ferrari_pit_laps = _pit_laps_for(driver_laps_df)
        for pl in ferrari_pit_laps:
            fig.add_vline(
                x=pl,
                line_color="#555555",
                line_dash="dot",
                line_width=1,
            )

    max_lap = int(all_laps["LapNumber"].max())

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#ffffff"),
        height=420,
        margin=dict(l=90, r=80, t=30, b=50),
        xaxis=dict(title="Lap", gridcolor="#222222", zeroline=False, range=[1, max_lap + 7]),
        yaxis=dict(
            title=f"Gap to {ref_label or ref} (s)  (+ = behind, − = ahead)",
            gridcolor="#222222",
            zeroline=False,
            tickformat=".1f",
            hoverformat=".2f",
        ),
        legend=dict(bgcolor="#12141f", bordercolor="#1e1e2e", borderwidth=1),
        hovermode="x unified",
    )
    return fig


def build_stint_chart(
    laps: pd.DataFrame,
    ferrari_drivers: list,
    top_n: int = 10,
    top_n_drivers: list | None = None,
) -> go.Figure:
    fig = go.Figure()
    added_compounds: set = set()

    if top_n_drivers is not None:
        # Use officially classified list from session results
        available = set(laps["Driver"].unique())
        driver_order = [d for d in top_n_drivers if d in available]
    else:
        pos_data = laps.dropna(subset=["Position"])
        if not pos_data.empty:
            final_pos = (
                pos_data.sort_values("LapNumber")
                .groupby("Driver")["Position"]
                .last()
            )
            top_drivers = final_pos[final_pos <= top_n].sort_values().head(top_n).index.tolist()
            driver_order = top_drivers if top_drivers else final_pos.sort_values().index.tolist()
        else:
            driver_order = laps["Driver"].unique().tolist()

    driver_order_reversed = driver_order[::-1]

    bands = _sc_vsc_bands(laps)
    _add_bands(fig, bands)

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

            inside_text = f"L{start_lap}" if lap_count >= 3 else ""

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
                text=[inside_text],
                textposition="inside",
                textfont=dict(
                    color="#000000" if compound in ("MEDIUM", "HARD") else "#ffffff",
                    size=9,
                ),
                hovertemplate=(
                    f"<b>{driver}</b>{'  ★' if is_ferrari else ''}<br>"
                    f"Stint {stint_num} · {compound.capitalize()}<br>"
                    f"Laps {start_lap}–{end_lap} ({lap_count} laps)<br>"
                    f"Tyre age: {tyre_life} laps<extra></extra>"
                ),
            ))

    computed_height = max(420, len(driver_order_reversed) * 30 + 80)

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


def compute_pit_summary(ferrari_laps: pd.DataFrame) -> dict:
    """Return pit stop details per Ferrari driver."""
    result = {}
    for driver in ferrari_laps["Driver"].unique():
        d = ferrari_laps[ferrari_laps["Driver"] == driver].sort_values("LapNumber").copy()
        stops = []
        stints = sorted(d["Stint"].unique())
        for idx, stint_num in enumerate(stints):
            if idx == 0:
                continue  # first stint is not a pit stop
            prev_stint = stints[idx - 1]
            prev_laps = d[d["Stint"] == prev_stint]
            cur_laps = d[d["Stint"] == stint_num]
            if prev_laps.empty or cur_laps.empty:
                continue

            in_lap_row = prev_laps.sort_values("LapNumber").iloc[-1]
            out_lap_row = cur_laps.sort_values("LapNumber").iloc[0]
            pit_lap = int(out_lap_row["LapNumber"])

            compound_in = str(in_lap_row.get("Compound", "?")).upper() if pd.notna(in_lap_row.get("Compound")) else "?"
            compound_out = str(out_lap_row.get("Compound", "?")).upper() if pd.notna(out_lap_row.get("Compound")) else "?"

            # Position: look a few laps back from pit / a few laps after
            pos_before = None
            for ln in range(int(in_lap_row["LapNumber"]), int(in_lap_row["LapNumber"]) - 4, -1):
                row = d[d["LapNumber"] == ln]
                if not row.empty and pd.notna(row.iloc[0].get("Position")):
                    pos_before = int(row.iloc[0]["Position"])
                    break

            pos_after = None
            for ln in range(pit_lap + 1, pit_lap + 5):
                row = d[d["LapNumber"] == ln]
                if not row.empty and pd.notna(row.iloc[0].get("Position")):
                    pos_after = int(row.iloc[0]["Position"])
                    break

            # Duration: PitInTime on in-lap, PitOutTime on out-lap
            duration_sec = None
            pit_in = in_lap_row.get("PitInTime") if "PitInTime" in in_lap_row.index else None
            pit_out = out_lap_row.get("PitOutTime") if "PitOutTime" in out_lap_row.index else None
            if pit_in is not None and pit_out is not None and pd.notna(pit_in) and pd.notna(pit_out):
                try:
                    duration_sec = float((pit_out - pit_in).total_seconds())
                    if duration_sec <= 0 or duration_sec > 120:
                        duration_sec = None
                except Exception:
                    duration_sec = None

            stops.append({
                "lap": pit_lap,
                "compound_in": compound_in.capitalize(),
                "compound_out": compound_out.capitalize(),
                "pos_before": pos_before,
                "pos_after": pos_after,
                "duration_sec": duration_sec,
            })
        result[driver] = stops
    return result
