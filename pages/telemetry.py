import streamlit as st

from data_acquisition.loader import get_all_laps, get_ferrari_laps, get_telemetry
from viz.telemetry import build_telemetry_chart
from viz.telemetry_analysis import (
    compute_telemetry_stats,
    build_speed_delta_chart,
    find_corners,
    build_summary,
)


def show():
    if "race_key" not in st.session_state:
        st.info("Select a race in the sidebar and click **Load Race** to begin.")
        st.stop()

    year, gp = st.session_state["race_key"]

    with st.spinner("Loading lap data…"):
        all_laps = get_all_laps(year, gp)
        ferrari_laps = get_ferrari_laps(year, gp)

    all_drivers = sorted(all_laps["Driver"].unique().tolist())
    ferrari_drivers = ferrari_laps["Driver"].unique().tolist()

    default_a = ferrari_drivers[0] if ferrari_drivers else all_drivers[0]
    default_b = ferrari_drivers[1] if len(ferrari_drivers) > 1 else all_drivers[1]

    st.subheader(f"Telemetry — {gp} {year}")

    # Driver selectors first; lap selectors computed from selected drivers
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        driver_a = st.selectbox(
            "Driver A", all_drivers,
            index=all_drivers.index(default_a),
            key="tel_driver_a",
        )
    driver_b_options = [d for d in all_drivers if d != driver_a]
    default_b_idx = 0
    if default_b in driver_b_options:
        default_b_idx = driver_b_options.index(default_b)
    with col3:
        driver_b = st.selectbox(
            "Driver B", driver_b_options,
            index=default_b_idx,
            key="tel_driver_b",
        )

    a_laps_data = all_laps[all_laps["Driver"] == driver_a].dropna(subset=["LapTimeSec"])
    b_laps_data = all_laps[all_laps["Driver"] == driver_b].dropna(subset=["LapTimeSec"])

    a_lap_nums = sorted(a_laps_data["LapNumber"].astype(int).tolist())
    b_lap_nums = sorted(b_laps_data["LapNumber"].astype(int).tolist())

    if not a_laps_data.empty:
        a_fastest = int(a_laps_data.loc[a_laps_data["LapTimeSec"].idxmin(), "LapNumber"])
        a_default_idx = a_lap_nums.index(a_fastest) if a_fastest in a_lap_nums else 0
    else:
        a_default_idx = 0

    if not b_laps_data.empty:
        b_fastest = int(b_laps_data.loc[b_laps_data["LapTimeSec"].idxmin(), "LapNumber"])
        b_default_idx = b_lap_nums.index(b_fastest) if b_fastest in b_lap_nums else 0
    else:
        b_default_idx = 0

    with col2:
        lap_a = st.selectbox("Lap A (fastest by default)", a_lap_nums, index=a_default_idx, key=f"tel_lap_a_{driver_a}")
    with col4:
        lap_b = st.selectbox("Lap B (fastest by default)", b_lap_nums, index=b_default_idx, key=f"tel_lap_b_{driver_b}")

    st.caption(
        f"{driver_a} Lap {lap_a} (red) vs {driver_b} Lap {lap_b} (blue) · "
        "First load may take ~30 s"
    )

    with st.spinner(f"Loading telemetry for {driver_a} & {driver_b}…"):
        tel_a = get_telemetry(year, gp, driver_a, lap_a)
        tel_b = get_telemetry(year, gp, driver_b, lap_b)

    if tel_a.empty or tel_b.empty:
        st.warning("Telemetry not available for one or both selected laps.")
        return

    fig = build_telemetry_chart(tel_a, tel_b, driver_a, driver_b, lap_a, lap_b)
    st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # Automated telemetry analysis
    # ------------------------------------------------------------------
    st.divider()
    st.markdown("### Telemetry Analysis")

    stats = compute_telemetry_stats(tel_a, tel_b)
    a_stats = stats["a"]
    b_stats = stats["b"]
    delta = stats["delta"]

    # --- 1. Key metrics row ---
    col_ts, col_ft, col_bz, col_avs = st.columns(4)

    with col_ts:
        st.metric(
            label="Top Speed (km/h)",
            value=f"{a_stats['top_speed']:.0f}",
            delta=f"{delta['top_speed']:+.1f} vs {driver_b}",
        )
    with col_ft:
        st.metric(
            label="Full Throttle %",
            value=f"{a_stats['full_throttle_pct']:.1f}%",
            delta=f"{delta['full_throttle_pct']:+.1f} pp vs {driver_b}",
        )
    with col_bz:
        st.metric(
            label="Brake Zones",
            value=f"{a_stats['brake_zones']}",
            delta=f"{delta['brake_zones']:+d} vs {driver_b}",
            delta_color="off",
        )
    with col_avs:
        st.metric(
            label="Avg Speed (km/h)",
            value=f"{a_stats['avg_speed']:.1f}",
            delta=f"{delta['avg_speed']:+.1f} vs {driver_b}",
        )

    st.caption(
        f"Metrics shown for **{driver_a}** (Lap {lap_a}). "
        f"Delta = {driver_a} − {driver_b}. "
        f"{driver_b}: Top {b_stats['top_speed']:.0f} km/h · "
        f"FT {b_stats['full_throttle_pct']:.1f}% · "
        f"Brakes {b_stats['brake_zones']} · "
        f"Avg {b_stats['avg_speed']:.1f} km/h"
    )

    # --- 2. Speed delta mini-chart ---
    delta_fig = build_speed_delta_chart(tel_a, tel_b, driver_a, driver_b)
    st.plotly_chart(delta_fig, use_container_width=True)

    # --- 3. Corner analysis ---
    corners_df = find_corners(tel_a, tel_b)

    if not corners_df.empty:
        st.markdown("#### Slowest Corners")
        display_df = corners_df.rename(columns={
            "Corner": "Corner #",
            "Distance_m": "Distance (m)",
            "MinSpeed_A": f"Min Speed {driver_a} (km/h)",
            "MinSpeed_B": f"Min Speed {driver_b} (km/h)",
            "Delta": f"Δ (A−B) km/h",
        })
        st.dataframe(display_df, use_container_width=True, height=220, hide_index=True)

    # --- 4. Natural language summary ---
    bullets = build_summary(stats, corners_df, driver_a, driver_b, tel_a, tel_b)
    if bullets:
        st.markdown("#### Summary")
        for bullet in bullets:
            st.markdown(f"- {bullet}")
