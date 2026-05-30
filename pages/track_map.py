import streamlit as st

from data_acquisition.loader import get_ferrari_laps, get_telemetry, get_circuit_rotation
from viz.track_map import build_track_map


def show():
    if "race_key" not in st.session_state:
        st.info("Select a race in the sidebar and click **Load Race** to begin.")
        st.stop()

    year, gp = st.session_state["race_key"]

    with st.spinner("Loading lap list…"):
        laps = get_ferrari_laps(year, gp)

    ferrari_drivers = laps["Driver"].unique().tolist()

    st.subheader(f"Track Map — {gp} {year}")

    # Driver selector first; lap list depends on selected driver
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        driver = st.selectbox("Driver", ferrari_drivers, key="tm_driver")

    driver_lap_nums = sorted(laps[laps["Driver"] == driver]["LapNumber"].astype(int).tolist())
    mid = len(driver_lap_nums) // 2

    with col2:
        lap_num = st.select_slider("Lap", options=driver_lap_nums, value=driver_lap_nums[mid], key="tm_lap")
    with col3:
        color_by = st.radio("Colour by", ["Speed", "Throttle", "Brake", "Gear"], key="tm_color", horizontal=True)

    st.caption(f"Coloured by {color_by} · Hover for exact values · First load may take ~30 s")

    with st.spinner(f"Loading telemetry for {driver} lap {lap_num}…"):
        tel = get_telemetry(year, gp, driver, lap_num)

    if tel.empty:
        st.warning("Telemetry not available for this lap.")
        return

    rotation = get_circuit_rotation(year, gp)
    fig = build_track_map(tel, color_by=color_by, rotation=rotation)
    st.plotly_chart(fig, use_container_width=True)
