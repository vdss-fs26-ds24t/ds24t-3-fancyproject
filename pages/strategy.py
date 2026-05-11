import streamlit as st

from data_acquisition.loader import get_all_laps, get_ferrari_laps
from viz.strategy import build_stint_chart


def show():
    if "race_key" not in st.session_state:
        st.info("Select a race in the sidebar and click **Load Race** to begin.")
        st.stop()

    year, gp = st.session_state["race_key"]

    with st.spinner(f"Loading {gp} {year}…"):
        all_laps = get_all_laps(year, gp)
        ferrari_laps = get_ferrari_laps(year, gp)

    ferrari_drivers = ferrari_laps["Driver"].unique().tolist()

    st.subheader(f"Race Strategy — {gp} {year}")
    st.caption("All drivers · compound colours · Ferrari rows highlighted with white border")

    fig = build_stint_chart(all_laps, ferrari_drivers)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Raw lap data"):
        st.dataframe(all_laps, use_container_width=True)
