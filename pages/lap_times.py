import streamlit as st

from data_acquisition.loader import get_ferrari_laps, get_all_laps
from viz.lap_times import build_lap_chart


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
        caption += f" · {compare_with} shown as dashed grey reference line"
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

    with st.expander("Raw lap data"):
        st.dataframe(laps, use_container_width=True)
