from pathlib import Path
from datetime import datetime

import pandas as pd
import fastf1
import streamlit as st


def setup_cache():
    cache_dir = Path("cache")
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
    laps = laps[["Driver", "LapNumber", "LapTime", "Compound", "Stint", "TyreLife"]].dropna(subset=["LapTime"])
    laps["LapTimeSec"] = laps["LapTime"].dt.total_seconds()
    laps["Stint"] = laps["Stint"].astype(int)
    return laps.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def get_all_laps(year: int, gp: str) -> pd.DataFrame:
    session = _load_session(year, gp, telemetry=False)
    laps = session.laps.copy()
    cols = ["Driver", "Team", "LapNumber", "LapTime", "Compound", "Stint", "TyreLife", "Position"]
    laps = laps[cols].dropna(subset=["LapTime"])
    laps["LapTimeSec"] = laps["LapTime"].dt.total_seconds()
    laps["Stint"] = laps["Stint"].astype(int)
    return laps.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def get_session_results(year: int, gp: str) -> pd.DataFrame:
    session = _load_session(year, gp, telemetry=False)
    results = session.results[["Abbreviation", "Position", "GridPosition", "Points", "Status"]].copy()
    results["Position"] = pd.to_numeric(results["Position"], errors="coerce").fillna(20).astype(int)
    results["GridPosition"] = pd.to_numeric(results["GridPosition"], errors="coerce").fillna(20).astype(int)
    results["Points"] = pd.to_numeric(results["Points"], errors="coerce").fillna(0).astype(int)
    return results.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def get_telemetry(year: int, gp: str, driver: str, lap_number: int) -> pd.DataFrame:
    session = _load_session(year, gp, telemetry=True)
    driver_laps = session.laps.pick_driver(driver)
    lap_data = driver_laps[driver_laps["LapNumber"] == lap_number]
    tel = lap_data.get_telemetry()
    return tel[["Distance", "Speed", "Throttle", "Brake", "nGear", "X", "Y"]].reset_index(drop=True)
