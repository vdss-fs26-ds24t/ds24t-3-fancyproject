import streamlit as st

from data_acquisition.loader import setup_cache, get_event_schedule, preload_telemetry
import pages.home as _home
import pages.strategy as _strategy
import pages.lap_times as _lap_times
import pages.telemetry as _telemetry
import pages.track_map as _track_map

setup_cache()

st.set_page_config(page_title="Ferrari Race Analysis", layout="wide")

pg = st.navigation([
    st.Page(_home.show, title="Home", icon="🏠", default=True, url_path="home"),
    st.Page(_strategy.show, title="Strategy", icon="📊", url_path="strategy"),
    st.Page(_lap_times.show, title="Lap Times", icon="📈", url_path="lap-times"),
    st.Page(_telemetry.show, title="Telemetry", icon="🎮", url_path="telemetry"),
    st.Page(_track_map.show, title="Track Map", icon="🗺️", url_path="track-map"),
])

with st.sidebar:
    st.markdown("## Ferrari Race Analysis")
    year = st.selectbox("Season", [2026, 2025], index=0)
    schedule = get_event_schedule(year)
    gp_names = schedule["EventName"].tolist()
    gp = st.selectbox("Grand Prix", gp_names, index=len(gp_names) - 1)
    if st.button("Load Race", type="primary", use_container_width=True):
        st.session_state["race_key"] = (year, gp)
        preload_telemetry(year, gp)
    if "race_key" in st.session_state:
        loaded_year, loaded_gp = st.session_state["race_key"]
        st.caption(f"Loaded: {loaded_gp} {loaded_year}")

pg.run()
