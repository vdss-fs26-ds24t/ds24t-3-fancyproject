"""
Telemetry analysis helpers — pure computation, no Streamlit imports.

All functions accept tel_a / tel_b DataFrames with columns:
  Distance (m), Speed (km/h), Throttle (0–100), Brake (0.0/1.0),
  Gear (int), X, Y
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

_COLOR_A = "#e8002d"   # red  (driver A)
_COLOR_B = "#00cfff"   # sky-blue (driver B)

_DARK = dict(paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
             font=dict(color="#ffffff"))


# ---------------------------------------------------------------------------
# 1. Key metrics
# ---------------------------------------------------------------------------

def compute_telemetry_stats(
    tel_a: pd.DataFrame,
    tel_b: pd.DataFrame,
) -> dict:
    """
    Return a dict with top_speed, full_throttle_pct, brake_zones, avg_speed
    for both drivers.  All values are floats/ints; deltas are A − B.
    """
    def _stats(tel: pd.DataFrame) -> dict:
        if tel.empty:
            return dict(top_speed=0.0, full_throttle_pct=0.0,
                        brake_zones=0, avg_speed=0.0)

        speed = tel["Speed"].astype(float)
        throttle = tel["Throttle"].astype(float)
        brake = tel["Brake"].astype(float)

        top_speed = speed.max()
        full_throttle_pct = (throttle > 98).sum() / max(len(throttle), 1) * 100.0
        avg_speed = speed.mean()

        # Count braking events: transitions 0→1
        brake_binary = (brake >= 0.5).astype(int)
        brake_zones = int((brake_binary.diff() == 1).sum())

        return dict(top_speed=top_speed, full_throttle_pct=full_throttle_pct,
                    brake_zones=brake_zones, avg_speed=avg_speed)

    a = _stats(tel_a)
    b = _stats(tel_b)

    return dict(
        a=a,
        b=b,
        delta=dict(
            top_speed=a["top_speed"] - b["top_speed"],
            full_throttle_pct=a["full_throttle_pct"] - b["full_throttle_pct"],
            brake_zones=a["brake_zones"] - b["brake_zones"],
            avg_speed=a["avg_speed"] - b["avg_speed"],
        ),
    )


# ---------------------------------------------------------------------------
# 2. Speed delta mini-chart
# ---------------------------------------------------------------------------

def build_speed_delta_chart(
    tel_a: pd.DataFrame,
    tel_b: pd.DataFrame,
    driver_a: str,
    driver_b: str,
) -> go.Figure:
    """
    Return a compact Plotly figure showing Speed_A − Speed_B vs distance.
    Red fill where A is faster; blue fill where B is faster.
    """
    if tel_a.empty or tel_b.empty:
        fig = go.Figure()
        fig.update_layout(**_DARK, height=200,
                          title="Speed Delta (A − B km/h)")
        return fig

    max_dist = min(tel_a["Distance"].max(), tel_b["Distance"].max())
    if max_dist <= 0:
        fig = go.Figure()
        fig.update_layout(**_DARK, height=200)
        return fig

    grid = np.linspace(0, max_dist, 500)

    speed_a_interp = np.interp(grid, tel_a["Distance"].values,
                               tel_a["Speed"].values.astype(float))
    speed_b_interp = np.interp(grid, tel_b["Distance"].values,
                               tel_b["Speed"].values.astype(float))
    delta = speed_a_interp - speed_b_interp

    # Segment the delta into positive (A faster) and negative (B faster) bands
    delta_pos = np.where(delta >= 0, delta, 0.0)
    delta_neg = np.where(delta < 0, delta, 0.0)

    fig = go.Figure()

    # Positive area (A faster) — red fill
    fig.add_trace(go.Scatter(
        x=grid, y=delta_pos,
        fill="tozeroy",
        fillcolor="rgba(232,0,45,0.30)",
        line=dict(color=_COLOR_A, width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # Negative area (B faster) — blue fill
    fig.add_trace(go.Scatter(
        x=grid, y=delta_neg,
        fill="tozeroy",
        fillcolor="rgba(0,207,255,0.30)",
        line=dict(color=_COLOR_B, width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # Delta line
    fig.add_trace(go.Scatter(
        x=grid, y=delta,
        line=dict(color="#ffffff", width=1.2),
        name="Δ Speed",
        hovertemplate="Dist %{x:.0f} m  Δ %{y:+.1f} km/h<extra></extra>",
    ))

    # Zero line
    fig.add_hline(y=0, line=dict(color="#444444", width=1, dash="dot"))

    _ax = dict(gridcolor="#222222", zeroline=False,
               tickfont=dict(color="#aaaaaa"))

    fig.update_layout(
        **_DARK,
        height=200,
        margin=dict(l=55, r=15, t=35, b=35),
        title=dict(
            text=f"Speed Delta  ({driver_a} − {driver_b}  km/h)",
            font=dict(color="#cccccc", size=13),
        ),
        xaxis=dict(**_ax, title=dict(text="Distance (m)",
                                     font=dict(color="#888888", size=11))),
        yaxis=dict(**_ax, title=dict(text="Δ km/h",
                                     font=dict(color="#888888", size=11))),
        showlegend=False,
    )

    return fig


# ---------------------------------------------------------------------------
# 3. Corner analysis  (manual peak-finding — no scipy required)
# ---------------------------------------------------------------------------

def find_corners(
    tel_a: pd.DataFrame,
    tel_b: pd.DataFrame,
    n_corners: int = 5,
    prominence: float = 20.0,
    speed_threshold_pct: float = 0.80,
) -> pd.DataFrame:
    """
    Identify the top `n_corners` slowest corners using a rolling-minimum
    approach on Driver A's speed trace.

    Parameters
    ----------
    tel_a, tel_b       : telemetry DataFrames
    n_corners          : how many corners to return
    prominence         : minimum speed drop (km/h) from surrounding speeds
    speed_threshold_pct: only consider points below this fraction of max speed

    Returns
    -------
    DataFrame with columns:
        Corner, Distance_m, MinSpeed_A, MinSpeed_B, Delta
    """
    if tel_a.empty:
        return pd.DataFrame(columns=["Corner", "Distance_m",
                                     "MinSpeed_A", "MinSpeed_B", "Delta"])

    dist_a = tel_a["Distance"].values.astype(float)
    speed_a = tel_a["Speed"].values.astype(float)

    max_speed_a = speed_a.max()
    threshold = max_speed_a * speed_threshold_pct

    # --- Manual local-minimum detection ---
    # A sample at index i is a local minimum if:
    #   1. speed_a[i] < threshold
    #   2. speed_a[i] is lower than its neighbours within a window
    #   3. The drop from the surrounding 'plateau' exceeds `prominence`

    n = len(speed_a)
    window = max(10, n // 80)   # adaptive window ~1–2% of lap

    candidates: list[int] = []
    for i in range(window, n - window):
        if speed_a[i] >= threshold:
            continue
        left_max = speed_a[max(0, i - window): i].max()
        right_max = speed_a[i + 1: min(n, i + window + 1)].max()
        prom = min(left_max, right_max) - speed_a[i]
        if prom >= prominence and speed_a[i] == speed_a[max(0, i - window): i + window + 1].min():
            candidates.append(i)

    if not candidates:
        return pd.DataFrame(columns=["Corner", "Distance_m",
                                     "MinSpeed_A", "MinSpeed_B", "Delta"])

    # --- Merge candidates that are within the same window (same corner) ---
    merged: list[int] = []
    for idx in candidates:
        if merged and (dist_a[idx] - dist_a[merged[-1]]) < window * 2:
            # Keep the one with lower speed
            if speed_a[idx] < speed_a[merged[-1]]:
                merged[-1] = idx
        else:
            merged.append(idx)

    # Sort by speed ascending (slowest first), then take top n_corners
    merged.sort(key=lambda i: speed_a[i])
    top_indices = merged[:n_corners]

    # Sort by distance for display
    top_indices.sort(key=lambda i: dist_a[i])

    rows = []
    for rank, idx in enumerate(top_indices, start=1):
        dist_corner = dist_a[idx]
        min_speed_a = speed_a[idx]

        # Interpolate Driver B speed at the same distance
        if not tel_b.empty:
            min_speed_b = float(np.interp(
                dist_corner,
                tel_b["Distance"].values.astype(float),
                tel_b["Speed"].values.astype(float),
            ))
        else:
            min_speed_b = float("nan")

        rows.append(dict(
            Corner=rank,
            Distance_m=int(round(dist_corner)),
            MinSpeed_A=round(min_speed_a, 1),
            MinSpeed_B=round(min_speed_b, 1) if not np.isnan(min_speed_b) else None,
            Delta=round(min_speed_a - min_speed_b, 1)
            if not np.isnan(min_speed_b) else None,
        ))

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Natural-language summary bullets
# ---------------------------------------------------------------------------

def build_summary(
    stats: dict,
    corners_df: pd.DataFrame,
    driver_a: str,
    driver_b: str,
    tel_a: pd.DataFrame,
    tel_b: pd.DataFrame,
) -> list[str]:
    """
    Return a list of plain-text bullet strings (without the leading "- ").
    Covers top speed, full-throttle %, and corner apex speed comparisons.
    """
    bullets: list[str] = []

    a = stats["a"]
    b = stats["b"]
    d = stats["delta"]

    # --- Top speed ---
    ts_diff = abs(d["top_speed"])
    if ts_diff < 0.5:
        bullets.append(
            f"Top speeds were nearly identical ({a['top_speed']:.0f} km/h each)."
        )
    else:
        faster = driver_a if d["top_speed"] > 0 else driver_b
        slower = driver_b if d["top_speed"] > 0 else driver_a
        bullets.append(
            f"**{faster}** had the higher top speed "
            f"({max(a['top_speed'], b['top_speed']):.0f} km/h vs "
            f"{min(a['top_speed'], b['top_speed']):.0f} km/h, "
            f"+{ts_diff:.1f} km/h over {slower})."
        )

    # --- Full throttle % ---
    ft_diff = abs(d["full_throttle_pct"])
    if ft_diff < 1.0:
        bullets.append(
            f"Both drivers spent a similar portion of the lap at full throttle "
            f"({a['full_throttle_pct']:.1f}% vs {b['full_throttle_pct']:.1f}%)."
        )
    else:
        more = driver_a if d["full_throttle_pct"] > 0 else driver_b
        less = driver_b if d["full_throttle_pct"] > 0 else driver_a
        pct_more = max(a["full_throttle_pct"], b["full_throttle_pct"])
        pct_less = min(a["full_throttle_pct"], b["full_throttle_pct"])
        bullets.append(
            f"**{more}** was at full throttle for {pct_more:.1f}% of the lap vs "
            f"{pct_less:.1f}% for {less} (+{ft_diff:.1f} pp more on-throttle time)."
        )

    # --- Corner apex speed ---
    if not corners_df.empty and "Delta" in corners_df.columns:
        valid = corners_df.dropna(subset=["Delta"])
        if not valid.empty:
            avg_delta = valid["Delta"].mean()
            abs_avg = abs(avg_delta)
            if abs_avg < 1.5:
                bullets.append(
                    "Corner minimum speeds were closely matched across the "
                    f"{len(valid)} analysed corners (avg Δ < 1.5 km/h)."
                )
            else:
                better = driver_a if avg_delta > 0 else driver_b
                bullets.append(
                    f"**{better}** carried more speed through corners on average "
                    f"(+{abs_avg:.1f} km/h at the apex across {len(valid)} corners)."
                )

            # Highlight any single corner with a large delta
            large = valid[valid["Delta"].abs() > 5]
            if not large.empty:
                worst = large.iloc[large["Delta"].abs().values.argmax()]
                lead = driver_a if worst["Delta"] > 0 else driver_b
                bullets.append(
                    f"Notable gap at ~{int(worst['Distance_m'])} m (corner {int(worst['Corner'])}): "
                    f"**{lead}** was {abs(worst['Delta']):.1f} km/h faster through the apex."
                )

    return bullets
