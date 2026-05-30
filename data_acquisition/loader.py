from pathlib import Path
from datetime import datetime

import pandas as pd
import fastf1
import streamlit as st


def setup_cache():
    cache_dir = Path(__file__).parent.parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))


@st.cache_data(show_spinner=False)
def get_event_schedule(year: int) -> pd.DataFrame:
    setup_cache()
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    today = datetime.today()
    completed = schedule[pd.to_datetime(schedule["EventDate"]) < today]
    return completed[["RoundNumber", "EventName", "Country", "EventDate"]].reset_index(drop=True)


@st.cache_resource(show_spinner=False)
def _load_session(year: int, gp: str, telemetry: bool = False) -> fastf1.core.Session:
    setup_cache()
    session = fastf1.get_session(year, gp, "R")
    session.load(telemetry=telemetry, weather=False, messages=False)
    return session


@st.cache_data(show_spinner=False)
def get_ferrari_laps(year: int, gp: str) -> pd.DataFrame:
    session = _load_session(year, gp, telemetry=False)
    laps = session.laps.pick_team("Ferrari").copy()
    laps = laps[["Driver", "LapNumber", "LapTime", "Compound", "Stint", "TyreLife",
                  "Position", "PitInTime", "PitOutTime"]].dropna(subset=["LapTime"])
    laps["LapTimeSec"] = laps["LapTime"].dt.total_seconds()
    laps["Stint"] = laps["Stint"].fillna(0).astype(int)
    return laps.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def get_all_laps(year: int, gp: str) -> pd.DataFrame:
    session = _load_session(year, gp, telemetry=False)
    laps = session.laps.copy()
    cols = ["Driver", "Team", "LapNumber", "LapTime", "Compound", "Stint", "TyreLife", "Position", "PitInTime", "PitOutTime", "TrackStatus"]
    laps = laps[cols].dropna(subset=["LapTime"])
    laps["LapTimeSec"] = laps["LapTime"].dt.total_seconds()
    laps["Stint"] = laps["Stint"].fillna(0).astype(int)
    return laps.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def get_track_status(year: int, gp: str) -> pd.DataFrame:
    session = _load_session(year, gp, telemetry=False)
    try:
        ts = session.track_status
        if ts is None or ts.empty:
            return pd.DataFrame(columns=["Time", "Status", "Message"])
        return ts.reset_index(drop=True)
    except Exception:
        return pd.DataFrame(columns=["Time", "Status", "Message"])


@st.cache_data(show_spinner=False)
def get_session_results(year: int, gp: str) -> pd.DataFrame:
    session = _load_session(year, gp, telemetry=False)
    results = session.results[["Abbreviation", "Position", "GridPosition", "Points", "Status"]].copy()
    results["Position"] = pd.to_numeric(results["Position"], errors="coerce")
    results["GridPosition"] = pd.to_numeric(results["GridPosition"], errors="coerce")
    results["Points"] = pd.to_numeric(results["Points"], errors="coerce").fillna(0)
    return results.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def get_telemetry(year: int, gp: str, driver: str, lap_number: int) -> pd.DataFrame:
    session = _load_session(year, gp, telemetry=True)
    driver_laps = session.laps.pick_driver(driver)
    lap_data = driver_laps[driver_laps["LapNumber"] == lap_number]
    if lap_data.empty:
        return pd.DataFrame(columns=["Distance", "Speed", "Throttle", "Brake", "Gear", "X", "Y"])
    tel = lap_data.iloc[0:1].get_telemetry()
    tel = tel[["Distance", "Speed", "Throttle", "Brake", "nGear", "X", "Y"]].copy()
    tel = tel.rename(columns={"nGear": "Gear"})
    tel["Brake"] = tel["Brake"].astype(float)
    return tel.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def get_circuit_rotation(year: int, gp: str) -> float:
    session = _load_session(year, gp, telemetry=False)
    try:
        return float(session.get_circuit_info().rotation)
    except Exception:
        return 0.0


def preload_telemetry(year: int, gp: str) -> None:
    """Start background thread to warm the telemetry session cache."""
    import threading
    def _load():
        try:
            _load_session(year, gp, telemetry=True)
        except Exception:
            pass
    threading.Thread(target=_load, daemon=True).start()
