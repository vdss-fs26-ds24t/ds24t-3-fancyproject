import streamlit as st

from data_acquisition.loader import get_ferrari_laps
from viz.lap_times import build_lap_chart


def show():
    if "race_key" not in st.session_state:
        st.info("Select a race in the sidebar and click **Load Race** to begin.")
        st.stop()

    year, gp = st.session_state["race_key"]

    with st.spinner("Loading lap data…"):
        laps = get_ferrari_laps(year, gp)

    stints = sorted(laps["Stint"].dropna().unique().tolist())

    with st.sidebar:
        st.markdown("---")
        st.markdown("**Lap Time Filters**")
        selected_stints = st.multiselect("Stints", stints, default=stints, key="lt_stints")
        hide_outliers = st.checkbox("Hide safety car / outlier laps", value=True, key="lt_outliers")

    st.subheader(f"Lap Time Progression — {gp} {year}")
    st.caption("Dashed trendlines show degradation rate per stint · PIT = pit stop lap")

    fig = build_lap_chart(laps, show_stints=selected_stints, hide_outliers=hide_outliers)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Raw lap data"):
        st.dataframe(laps, use_container_width=True)
