import streamlit as st

from data_acquisition.loader import get_ferrari_laps, get_telemetry
from viz.telemetry import build_telemetry_chart


def show():
    if "race_key" not in st.session_state:
        st.info("Select a race in the sidebar and click **Load Race** to begin.")
        st.stop()

    year, gp = st.session_state["race_key"]

    with st.spinner("Loading lap list…"):
        laps = get_ferrari_laps(year, gp)

    ferrari_drivers = laps["Driver"].unique().tolist()

    with st.sidebar:
        st.markdown("---")
        st.markdown("**Telemetry Controls**")
        driver = st.selectbox("Driver", ferrari_drivers, key="tel_driver")
        driver_lap_nums = sorted(laps[laps["Driver"] == driver]["LapNumber"].astype(int).tolist())
        lap_a = st.selectbox("Lap A (reference)", driver_lap_nums, index=0, key="tel_lap_a")
        lap_b = st.selectbox("Lap B (compare)", driver_lap_nums, index=len(driver_lap_nums) - 1, key="tel_lap_b")

    st.subheader(f"Telemetry — {driver} · {gp} {year}")
    st.caption(f"Comparing Lap {lap_a} (solid) vs Lap {lap_b} (dashed) · First load may take ~30 s")

    with st.spinner(f"Loading telemetry for {driver} laps {lap_a} & {lap_b}…"):
        tel_a = get_telemetry(year, gp, driver, lap_a)
        tel_b = get_telemetry(year, gp, driver, lap_b)

    if tel_a.empty or tel_b.empty:
        st.warning("Telemetry not available for one or both selected laps.")
        return

    fig = build_telemetry_chart(tel_a, tel_b, driver, lap_a, lap_b)
    st.plotly_chart(fig, use_container_width=True)
