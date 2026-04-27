import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from data_acquisition.loader import setup_cache, get_event_schedule, load_race, get_ferrari_laps

setup_cache()

COMPOUND_COLORS = {
    "SOFT": "#e8002d",
    "MEDIUM": "#ffd600",
    "HARD": "#ebebeb",
    "INTERMEDIATE": "#43b02a",
    "WET": "#0067ff",
}


@st.cache_data(show_spinner=False)
def fetch_race_data(year: int, gp: str):
    session = load_race(year, gp)
    laps = get_ferrari_laps(session)
    return laps


st.set_page_config(page_title="Ferrari Race Analysis", layout="wide")
st.title("Ferrari Race Analysis")

with st.sidebar:
    st.header("Race Selection")
    year = st.selectbox("Season", [2026, 2025], index=0)

    schedule = get_event_schedule(year)
    gp_names = schedule["EventName"].tolist()
    gp = st.selectbox("Grand Prix", gp_names, index=len(gp_names) - 1)

    load_btn = st.button("Load Race", type="primary", use_container_width=True)

if load_btn:
    st.session_state["race_key"] = (year, gp)

if "race_key" not in st.session_state:
    st.info("Select a race in the sidebar and click **Load Race** to begin.")
    st.stop()

loaded_year, loaded_gp = st.session_state["race_key"]

with st.spinner(f"Loading {loaded_gp} {loaded_year}..."):
    laps = fetch_race_data(loaded_year, loaded_gp)

st.subheader(f"Lap Time Progression — {loaded_gp} {loaded_year}")

fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor("#0e1117")
ax.set_facecolor("#0e1117")

line_styles = ["-", "--"]
drivers = laps["Driver"].unique().tolist()
stints = sorted(laps["Stint"].unique().tolist())

for i, driver in enumerate(drivers):
    driver_laps = laps[laps["Driver"] == driver]
    for stint in stints:
        stint_laps = driver_laps[driver_laps["Stint"] == stint].sort_values("LapNumber")
        if stint_laps.empty:
            continue
        compound = stint_laps["Compound"].iloc[0]
        color = COMPOUND_COLORS.get(compound, "#aaaaaa")
        label = f"{driver} — Stint {stint} ({compound.capitalize()})"
        ax.plot(
            stint_laps["LapNumber"], stint_laps["LapTimeSec"],
            linestyle=line_styles[i % 2], color=color,
            linewidth=2, marker="o", markersize=3, label=label,
        )

ax.set_xlabel("Lap", color="#ffffff")
ax.set_ylabel("Lap Time (s)", color="#ffffff")
ax.tick_params(colors="#ffffff")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["bottom", "left"]:
    ax.spines[spine].set_color("#444444")

ax.yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda val, _: f"{int(val // 60)}:{val % 60:05.2f}")
)
ax.legend(
    loc="upper right", framealpha=0.3, labelcolor="#ffffff",
    facecolor="#1a1a2e", edgecolor="#444444", fontsize=9,
)
ax.grid(axis="y", color="#333333", linewidth=0.5)

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

with st.expander("Raw lap data"):
    st.dataframe(laps, use_container_width=True)
