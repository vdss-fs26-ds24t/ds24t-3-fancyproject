"""
Pre-download FastF1 race data for specified seasons so the Streamlit Cloud
deployment can load data from the committed cache without hitting the F1
timing servers (which block Streamlit's IPs).

Usage:
    uv run python scripts/precache_seasons.py

Loads lap data only (no telemetry/weather/messages) to keep cache size small.
After running, commit the fastf1_cache/ directory to git.
"""

import sys
from pathlib import Path

import fastf1
import pandas as pd

SEASONS = [2024, 2025]
CACHE_DIR = Path(__file__).parent.parent / "fastf1_cache"


def precache_season(year: int):
    print(f"\n{'='*50}")
    print(f"Season {year}")
    print(f"{'='*50}")

    schedule = fastf1.get_event_schedule(year, include_testing=False)
    races = schedule[schedule["EventFormat"] != "testing"].copy()

    # For past seasons load all rounds; for the current year only load completed ones
    today = pd.Timestamp.today(tz=None)
    races = races[pd.to_datetime(races["EventDate"]).dt.tz_localize(None) < today]

    print(f"Found {len(races)} completed races to cache\n")

    failed = []
    for _, event in races.iterrows():
        gp = event["EventName"]
        round_num = event["RoundNumber"]
        print(f"  [{round_num:02d}/{len(races):02d}] {gp} ... ", end="", flush=True)
        try:
            session = fastf1.get_session(year, gp, "R")
            session.load(telemetry=False, weather=False, messages=False)
            print("OK")
        except Exception as exc:
            print(f"FAILED ({exc})")
            failed.append((year, gp, str(exc)))

    return failed


def main():
    CACHE_DIR.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE_DIR))
    print(f"Cache directory: {CACHE_DIR.resolve()}")

    all_failed = []
    for year in SEASONS:
        all_failed.extend(precache_season(year))

    print(f"\n{'='*50}")
    if all_failed:
        print(f"Done with {len(all_failed)} failure(s):")
        for year, gp, err in all_failed:
            print(f"  {year} {gp}: {err}")
        sys.exit(1)
    else:
        print("All races cached successfully.")
        print(f"\nNext step: commit fastf1_cache/ to git.")


if __name__ == "__main__":
    main()
