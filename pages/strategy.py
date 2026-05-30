import streamlit as st

from data_acquisition.loader import get_ferrari_laps, get_all_laps, get_session_results
from viz.strategy import build_stint_chart, build_position_chart, build_gap_chart, compute_pit_summary


def show():
    if "race_key" not in st.session_state:
        st.info("Select a race in the sidebar and click **Load Race** to begin.")
        st.stop()

    year, gp = st.session_state["race_key"]

    with st.spinner(f"Loading {gp} {year}…"):
        all_laps = get_all_laps(year, gp)
        ferrari_laps = get_ferrari_laps(year, gp)
        results = get_session_results(year, gp)

    ferrari_drivers = ferrari_laps["Driver"].unique().tolist()
    all_drivers = sorted(all_laps["Driver"].unique().tolist())

    st.subheader(f"Race Strategy — {gp} {year}")

    col1, col2 = st.columns([2, 1])
    with col1:
        rival_options = ["Race Leader"] + [d for d in all_drivers if d not in ferrari_drivers]
        reference = st.selectbox("Gap reference", rival_options, key="strat_reference")
        reference_driver = None if reference == "Race Leader" else reference
    with col2:
        top_n = st.slider("Drivers in strategy map", min_value=5, max_value=20, value=10, key="strat_topn")

    st.markdown("**Race Positions**")
    st.caption("Ferrari highlighted · pit stops marked ◆ · SC/VSC bands in yellow/blue")
    fig_pos = build_position_chart(all_laps, ferrari_drivers)
    st.plotly_chart(fig_pos, use_container_width=True)

    st.markdown(f"**Gap to {'Race Leader' if reference_driver is None else reference_driver}**")
    st.caption("Positive = behind · Negative = ahead · grey dotted = Ferrari pit · blue dotted = rival pit")
    fig_gap = build_gap_chart(
        all_laps,
        ferrari_drivers,
        reference_driver,
        ref_label="Race Leader" if reference_driver is None else reference_driver,
    )
    st.plotly_chart(fig_gap, use_container_width=True)

    # Official classified order — excludes retired/DNS drivers
    classified = (
        results[results["Status"].isin(["Finished", "Lapped"])]
        .sort_values("Position")
        .head(top_n)["Abbreviation"]
        .tolist()
    )

    st.markdown("**Tyre Strategy**")
    st.caption(f"Top {top_n} classified finishers · compound colours · Ferrari highlighted · L# = pit lap")
    fig_stint = build_stint_chart(all_laps, ferrari_drivers, top_n=top_n, top_n_drivers=classified)
    st.plotly_chart(fig_stint, use_container_width=True)

    st.divider()
    st.markdown("**Pit Stop Summary**")

    pit_summary = compute_pit_summary(ferrari_laps)

    for driver in ferrari_drivers:
        st.markdown(f"**{driver}**")
        stops = pit_summary.get(driver, [])

        if not stops:
            st.caption(f"{driver}: no pit stops recorded")
            continue

        for stop in stops:
            lap = stop["lap"]
            c_in = stop["compound_in"].capitalize() if stop["compound_in"] else "?"
            c_out = stop["compound_out"].capitalize() if stop["compound_out"] else "?"
            pos_before = stop["pos_before"]
            pos_after = stop["pos_after"]
            dur = stop["duration_sec"]

            if pos_before and pos_after:
                delta = pos_before - pos_after
                pos_str = f"P{pos_before} → P{pos_after}"
                gain_str = f"+{delta}" if delta > 0 else str(delta)
            else:
                pos_str = "—"
                gain_str = "—"

            dur_str = f"{dur:.1f}s" if dur is not None else "—"

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Lap", lap)
            with c2:
                st.metric("Compound", f"{c_in} → {c_out}")
            with c3:
                st.metric("Position", pos_str, delta=gain_str if gain_str != "—" else None, delta_color="inverse")
            with c4:
                st.metric("Stop time", dur_str)
