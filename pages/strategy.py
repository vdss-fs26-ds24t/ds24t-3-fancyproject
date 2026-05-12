import streamlit as st

from data_acquisition.loader import get_all_laps, get_ferrari_laps
from viz.strategy import build_stint_chart, build_position_chart


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

    st.markdown("**Race Positions**")
    st.caption("Ferrari in red · all other drivers in grey · hover for exact position")
    fig_pos = build_position_chart(all_laps, ferrari_drivers)
    st.plotly_chart(fig_pos, use_container_width=True)

    st.markdown("**Tyre Strategy**")
    st.caption("All drivers · compound colours · Ferrari highlighted with red border")
    fig_stint = build_stint_chart(all_laps, ferrari_drivers)
    st.plotly_chart(fig_stint, use_container_width=True)

    with st.expander("Raw lap data"):
        st.dataframe(all_laps, use_container_width=True)
