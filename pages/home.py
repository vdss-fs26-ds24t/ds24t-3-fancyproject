import pandas as pd
import streamlit as st

from data_acquisition.loader import get_ferrari_laps, get_all_laps, get_session_results
from viz.strategy import build_stint_chart
from viz.lap_times import format_laptime


def _driver_narrative(ferrari_laps: pd.DataFrame, results: pd.DataFrame, driver: str) -> str:
    driver_laps = ferrari_laps[ferrari_laps["Driver"] == driver].dropna(subset=["LapTimeSec"])
    if driver_laps.empty:
        return f"**{driver}**: no data"

    stints = (
        driver_laps.sort_values("LapNumber")
        .groupby("Stint", sort=True)["Compound"]
        .first()
        .str.capitalize()
        .tolist()
    )
    num_stops = len(stints) - 1
    strategy_str = " → ".join(stints)

    driver_result = results[results["Abbreviation"] == driver]
    if driver_result.empty:
        return f"**{driver}**: {num_stops}-stop ({strategy_str})"

    pos = driver_result["Position"].iloc[0]
    grid = driver_result["GridPosition"].iloc[0]

    if pd.isna(pos):
        return f"**{driver}**: {num_stops}-stop ({strategy_str}) — DNF"

    pos_int, grid_int = int(pos), int(grid)
    gained = grid_int - pos_int
    if gained > 0:
        move = f", gained {gained} position{'s' if gained != 1 else ''}"
    elif gained < 0:
        move = f", lost {abs(gained)} position{'s' if abs(gained) != 1 else ''}"
    else:
        move = ""
    return f"**{driver}**: {num_stops}-stop ({strategy_str}), P{grid_int} → P{pos_int}{move}"


def show():
    if "race_key" not in st.session_state:
        st.info("Select a race in the sidebar and click **Load Race** to begin.")
        st.stop()

    year, gp = st.session_state["race_key"]

    with st.spinner(f"Loading {gp} {year}…"):
        ferrari_laps = get_ferrari_laps(year, gp)
        all_laps = get_all_laps(year, gp)
        results = get_session_results(year, gp)

    ferrari_drivers = ferrari_laps["Driver"].unique().tolist()

    st.title(f"{gp} {year}")

    # KPI cards
    cols = st.columns(4)
    for i, driver in enumerate(ferrari_drivers[:2]):
        driver_result = results[results["Abbreviation"] == driver]
        if not driver_result.empty:
            pos = driver_result["Position"].iloc[0]
            grid = driver_result["GridPosition"].iloc[0]
            if pos == pos and grid == grid:
                pos_int = int(pos)
                grid_int = int(grid)
                gained = grid_int - pos_int
                delta_str = f"+{gained}" if gained > 0 else str(gained)
                with cols[i]:
                    st.metric(label=driver, value=f"P{pos_int}", delta=delta_str if gained != 0 else None)
            else:
                with cols[i]:
                    st.metric(label=driver, value="DNF")
        else:
            with cols[i]:
                st.metric(label=driver, value="—")

    best_row = ferrari_laps.loc[ferrari_laps["LapTimeSec"].idxmin()]
    best_driver = best_row["Driver"]
    best_time = format_laptime(float(best_row["LapTimeSec"]))
    with cols[2]:
        st.metric(label="Best Lap", value=best_time, delta=best_driver)

    ferrari_results = results[results["Abbreviation"].isin(ferrari_drivers)]
    total_pts = int(ferrari_results["Points"].fillna(0).sum())
    with cols[3]:
        st.metric(label="Points Scored", value=total_pts, delta="combined")

    # Race narrative
    narratives = [_driver_narrative(ferrari_laps, results, d) for d in ferrari_drivers]
    st.caption("  ·  ".join(narratives))

    # Strategy thumbnail
    st.subheader("Race Strategy")
    fig = build_stint_chart(all_laps, ferrari_drivers, height=260)
    st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})
