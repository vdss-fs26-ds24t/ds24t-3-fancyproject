import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from data_acquisition.loader import setup_cache, get_event_schedule, load_race, get_ferrari_laps, get_all_laps

setup_cache()

COMPOUND_COLORS = {
    "SOFT": "#e8002d",
    "MEDIUM": "#ffd600",
    "HARD": "#ebebeb",
    "INTERMEDIATE": "#43b02a",
    "WET": "#0067ff",
}


def _tint(hex_color: str, factor: float = 0.45) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"#{int(r+(255-r)*factor):02x}{int(g+(255-g)*factor):02x}{int(b+(255-b)*factor):02x}"


COMPOUND_COLORS_TINTED = {k: _tint(v) for k, v in COMPOUND_COLORS.items()}

DRIVER_STYLES = [
    {"colors": COMPOUND_COLORS,        "marker": "o", "linestyle": "-"},
    {"colors": COMPOUND_COLORS_TINTED, "marker": "D", "linestyle": "--"},
]


@st.cache_data(show_spinner=False)
def fetch_race_data(year: int, gp: str):
    session = load_race(year, gp)
    laps = get_ferrari_laps(session)
    return laps


@st.cache_data(show_spinner=False)
def fetch_all_laps_data(year: int, gp: str):
    session = load_race(year, gp)
    return get_all_laps(session)


def draw_lap_time_chart(laps) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    drivers = laps["Driver"].unique().tolist()
    stints = sorted(laps["Stint"].unique().tolist())

    for i, driver in enumerate(drivers):
        style = DRIVER_STYLES[i % len(DRIVER_STYLES)]
        driver_laps = laps[laps["Driver"] == driver]
        last_lap_x, last_lap_y = None, None
        for stint in stints:
            stint_laps = driver_laps[driver_laps["Stint"] == stint].sort_values("LapNumber")
            if stint_laps.empty:
                continue
            compound = stint_laps["Compound"].iloc[0]
            color = style["colors"].get(compound, "#aaaaaa")
            ax.plot(
                stint_laps["LapNumber"], stint_laps["LapTimeSec"],
                linestyle=style["linestyle"],
                color=color,
                linewidth=2.5,
            )
            last_lap_x = stint_laps["LapNumber"].iloc[-1]
            last_lap_y = stint_laps["LapTimeSec"].iloc[-1]
        if last_lap_x is not None:
            ax.annotate(
                driver,
                xy=(last_lap_x, last_lap_y),
                xytext=(6, 0),
                textcoords="offset points",
                color="#ffffff",
                fontsize=8,
                fontweight="bold",
                va="center",
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

    legend_kw = dict(framealpha=0.3, labelcolor="#ffffff", facecolor="#1a1a2e", edgecolor="#444444", fontsize=9)
    used_compounds = [c for c in ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"] if c in laps["Compound"].values]
    handles = (
        [Line2D([0], [0], color="#ffffff", linestyle=DRIVER_STYLES[i % len(DRIVER_STYLES)]["linestyle"],
                linewidth=2.5, label=d) for i, d in enumerate(drivers)]
        + [Patch(alpha=0, label="")]
        + [Patch(facecolor=COMPOUND_COLORS.get(c, "#aaaaaa"), edgecolor="#555555", label=c.capitalize())
           for c in used_compounds]
    )
    legend = ax.legend(handles=handles, loc="upper right", **legend_kw,
                       title="Driver / Compound", title_fontsize=8)
    legend.get_title().set_color("#aaaaaa")

    ax.grid(axis="y", color="#333333", linewidth=0.5)
    plt.tight_layout()
    return fig


def draw_stint_chart(all_laps) -> plt.Figure:
    stint_summary = (
        all_laps.groupby(["Driver", "Stint"])
        .agg(
            start_lap=("LapNumber", "min"),
            end_lap=("LapNumber", "max"),
            compound=("Compound", "first"),
            team=("Team", "first"),
        )
        .reset_index()
    )

    driver_order = (
        all_laps.groupby("Driver")["LapNumber"]
        .max()
        .sort_values(ascending=True)
        .index.tolist()
    )
    ferrari_drivers = set(all_laps[all_laps["Team"] == "Ferrari"]["Driver"].unique())

    fig_height = max(6, len(driver_order) * 0.42)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    y_positions = {driver: idx for idx, driver in enumerate(driver_order)}
    bar_height = 0.7

    for _, row in stint_summary.iterrows():
        driver = row["Driver"]
        y = y_positions[driver]
        width = row["end_lap"] - row["start_lap"] + 1
        color = COMPOUND_COLORS.get(row["compound"], "#aaaaaa")
        is_ferrari = driver in ferrari_drivers
        ax.barh(
            y, width,
            left=row["start_lap"],
            height=bar_height,
            color=color,
            edgecolor="#ffffff" if is_ferrari else "#222222",
            linewidth=2 if is_ferrari else 0.5,
        )

    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels(
        [f"$\\bf{{{d}}}$" if d in ferrari_drivers else d for d in driver_order],
        fontsize=8,
        color="#ffffff",
    )
    ax.set_xlabel("Lap Number", color="#ffffff")
    ax.tick_params(colors="#ffffff")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for spine in ["bottom", "left"]:
        ax.spines[spine].set_color("#444444")
    ax.grid(axis="x", color="#333333", linewidth=0.5)

    seen_compounds = stint_summary["compound"].unique()
    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=COMPOUND_COLORS.get(c, "#aaaaaa"), label=c.capitalize())
        for c in ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
        if c in seen_compounds
    ]
    ax.legend(
        handles=legend_handles,
        loc="lower right",
        framealpha=0.3,
        labelcolor="#ffffff",
        facecolor="#1a1a2e",
        edgecolor="#444444",
        fontsize=9,
    )

    ax.set_xlim(left=0)
    ax.invert_yaxis()
    plt.tight_layout()
    return fig


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
    try:
        laps = fetch_race_data(loaded_year, loaded_gp)
        all_laps = fetch_all_laps_data(loaded_year, loaded_gp)
    except Exception as e:
        st.error(str(e))
        st.stop()

st.subheader(f"Lap Time Progression — {loaded_gp} {loaded_year}")
fig_lap = draw_lap_time_chart(laps)
st.pyplot(fig_lap)
plt.close(fig_lap)

st.subheader(f"Race Stint Strategy — {loaded_gp} {loaded_year}")
try:
    fig_stint = draw_stint_chart(all_laps)
    st.pyplot(fig_stint)
    plt.close(fig_stint)
except Exception:
    st.warning("Stint strategy data unavailable for this race.")

with st.expander("Raw lap data"):
    st.dataframe(laps, use_container_width=True)
