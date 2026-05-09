from pathlib import Path
from datetime import datetime

import pandas as pd
import fastf1

def setup_cache():
    cache_dir = Path("/tmp/fastf1_cache")
    cache_dir.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))


def get_event_schedule(year: int) -> pd.DataFrame:
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    today = datetime.today()
    completed = schedule[pd.to_datetime(schedule["EventDate"]) < today]
    return completed[["RoundNumber", "EventName", "Country", "EventDate"]].reset_index(drop=True)


def load_race(year: int, gp: str) -> fastf1.core.Session:
    session = fastf1.get_session(year, gp, "R")
    session.load(telemetry=False, weather=False, messages=False)
    return session


def get_ferrari_laps(session: fastf1.core.Session) -> pd.DataFrame:
    try:
        all_laps = session.laps
    except fastf1.exceptions.DataNotLoadedError:
        raise RuntimeError(
            "Lap data could not be loaded. The race data may not be available yet "
            "on the FastF1 servers — try again later or select a different race."
        )
    laps = all_laps.pick_team("Ferrari").copy()
    laps = laps[["Driver", "LapNumber", "LapTime", "Compound", "Stint", "TyreLife"]].dropna(subset=["LapTime"])
    laps["LapTimeSec"] = laps["LapTime"].dt.total_seconds()
    return laps.reset_index(drop=True)


def get_all_laps(session: fastf1.core.Session) -> pd.DataFrame:
    try:
        all_laps = session.laps
    except fastf1.exceptions.DataNotLoadedError:
        raise RuntimeError(
            "Lap data could not be loaded. The race data may not be available yet "
            "on the FastF1 servers — try again later or select a different race."
        )
    laps = all_laps.copy()
    laps = laps[["Driver", "LapNumber", "LapTime", "Compound", "Stint", "TyreLife", "Team"]].dropna(subset=["LapTime", "Compound"])
    laps["LapTimeSec"] = laps["LapTime"].dt.total_seconds()
    return laps.reset_index(drop=True)
