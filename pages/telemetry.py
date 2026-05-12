import streamlit as st

from data_acquisition.loader import get_all_laps, get_ferrari_laps, get_telemetry
from viz.telemetry import build_telemetry_chart


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
    with col3:
        driver_b = st.selectbox(
            "Driver B", all_drivers,
            index=all_drivers.index(default_b),
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
        lap_a = st.selectbox("Lap A (fastest by default)", a_lap_nums, index=a_default_idx, key="tel_lap_a")
    with col4:
        lap_b = st.selectbox("Lap B (fastest by default)", b_lap_nums, index=b_default_idx, key="tel_lap_b")

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
