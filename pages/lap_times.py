import streamlit as st

from data_acquisition.loader import get_ferrari_laps, get_all_laps
from viz.lap_times import build_lap_chart, compute_stint_stats, format_laptime


def show():
    if "race_key" not in st.session_state:
        st.info("Select a race in the sidebar and click **Load Race** to begin.")
        st.stop()

    year, gp = st.session_state["race_key"]

    with st.spinner("Loading lap data…"):
        laps = get_ferrari_laps(year, gp)
        all_laps = get_all_laps(year, gp)

    ferrari_drivers = laps["Driver"].unique().tolist()
    all_drivers = sorted(all_laps["Driver"].unique().tolist())
    competitor_options = ["None"] + [d for d in all_drivers if d not in ferrari_drivers]
    stints = sorted(laps["Stint"].dropna().unique().tolist())

    st.subheader(f"Lap Time Progression — {gp} {year}")

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        selected_stints = st.multiselect("Stints", stints, default=stints, key="lt_stints")
    with col2:
        hide_outliers = st.checkbox("Hide SC / outlier laps", value=True, key="lt_outliers")
    with col3:
        compare_with = st.selectbox(
            "Compare with competitor",
            competitor_options,
            index=0,
            key="lt_competitor",
        )

    caption = "Tyre strategy shown as coloured strip below chart · S1/S2 = stint number · PIT = pit stop"
    if compare_with != "None":
        caption += f" · {compare_with} shown in light blue"
    st.caption(caption)

    competitor_laps = None
    if compare_with != "None":
        # Pass raw data — build_lap_chart filters for the line internally
        # but uses all stints for the strategy strip
        competitor_laps = all_laps[all_laps["Driver"] == compare_with].copy()

    fig = build_lap_chart(
        laps,
        show_stints=selected_stints,
        hide_outliers=hide_outliers,
        competitor_laps=competitor_laps,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Stint Analysis ────────────────────────────────────────────────────────
    stats = compute_stint_stats(laps, selected_stints, hide_outliers)
    ferrari_drivers = [d for d in laps["Driver"].unique().tolist() if d in stats]

    # Merge competitor stats if selected
    if compare_with != "None" and competitor_laps is not None and not competitor_laps.empty:
        comp_stats = compute_stint_stats(competitor_laps, show_stints=None, hide_outliers=hide_outliers)
        stats.update(comp_stats)

    all_display_drivers = ferrari_drivers[:]
    if compare_with != "None" and compare_with in stats:
        all_display_drivers.append(compare_with)

    if all_display_drivers:
        st.divider()
        st.markdown("**Stint Analysis**")

        all_stints = sorted({s for d in all_display_drivers for s in stats[d]})
        n_cols = len(all_display_drivers)  # fixed grid width for every stint row

        for stint in all_stints:
            has_data = {d for d in all_display_drivers if stint in stats.get(d, {})}
            if not has_data:
                continue

            st.caption(f"Stint {stint}")

            # Always render n_cols columns so layout is consistent across stints
            metric_cols = st.columns(n_cols)
            for j, driver in enumerate(all_display_drivers):
                with metric_cols[j]:
                    if driver not in has_data:
                        st.metric(label=driver, value="—", delta=None, help="No data for this stint")
                        continue
                    s = stats[driver][stint]
                    slope_str = f"+{s['slope']:.3f} s/lap" if s["slope"] >= 0 else f"{s['slope']:.3f} s/lap"
                    st.metric(
                        label=f"{driver} · {s['compound']} · {s['laps']} laps",
                        value=format_laptime(s["best_sec"]),
                        delta=slope_str,
                        delta_color="off",
                        help=f"Avg: {format_laptime(s['avg_sec'])}",
                    )

            # Natural-language insight — compare only the two Ferrari drivers when both present in this stint
            ferrari_in_stint = [d for d in ferrari_drivers if d in has_data]
            if len(ferrari_in_stint) == 2:
                d1, d2 = ferrari_in_stint
                s1, s2 = stats[d1][stint], stats[d2][stint]
                slope_diff = s1["slope"] - s2["slope"]  # positive → d2 had better pace evolution
                pace_diff  = s1["avg_sec"] - s2["avg_sec"]  # positive → d2 was faster

                parts = []
                if abs(slope_diff) >= 0.005:
                    diff_str = f"{abs(slope_diff):.3f} s/lap"
                    # Both degrading (positive slopes)
                    if s1["slope"] > 0 and s2["slope"] > 0:
                        better = d2 if slope_diff > 0 else d1
                        parts.append(f"**{better}** managed tyres better ({diff_str} less degradation)")
                    # Both improving (negative slopes)
                    elif s1["slope"] <= 0 and s2["slope"] <= 0:
                        # more negative = improved faster
                        better = d1 if slope_diff < 0 else d2
                        parts.append(f"**{better}** improved faster ({diff_str})")
                    # One degrading, one improving
                    else:
                        improving = d1 if s1["slope"] < 0 else d2
                        degrading = d2 if s1["slope"] < 0 else d1
                        parts.append(f"**{improving}** improved while **{degrading}** degraded")
                else:
                    parts.append("Similar pace evolution")

                if abs(pace_diff) >= 0.05:
                    faster = d2 if pace_diff > 0 else d1
                    parts.append(f"**{faster}** {abs(pace_diff):.2f}s faster on average")

                st.caption("  ·  ".join(parts))

    with st.expander("Raw lap data"):
        st.dataframe(laps, use_container_width=True)
