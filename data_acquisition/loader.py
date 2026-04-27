from pathlib import Path
from datetime import datetime

import pandas as pd
import fastf1


def setup_cache():
    cache_dir = Path("cache")
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
    laps = session.laps.pick_team("Ferrari").copy()
    laps = laps[["Driver", "LapNumber", "LapTime", "Compound", "Stint", "TyreLife"]].dropna(subset=["LapTime"])
    laps["LapTimeSec"] = laps["LapTime"].dt.total_seconds()
    return laps.reset_index(drop=True)
