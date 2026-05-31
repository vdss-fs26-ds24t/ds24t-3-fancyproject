# Ferrari Race Analysis Dashboard

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
![FastF1](https://img.shields.io/badge/FastF1-E8002D?style=for-the-badge&logo=formula1&logoColor=white)
![uv](https://img.shields.io/badge/uv-DE5FE9?style=for-the-badge&logo=astral&logoColor=white)
![Quarto](https://img.shields.io/badge/Quarto-39729E?style=for-the-badge&logo=quarto&logoColor=white)
![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-222222?style=for-the-badge&logo=github&logoColor=white)
![Streamlit Cloud](https://img.shields.io/badge/Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

An interactive Streamlit dashboard for post-race analysis of Formula 1 races, with a focus on Scuderia Ferrari. Users pick a season and Grand Prix; the app loads the corresponding data from [FastF1](https://docs.fastf1.dev/) and visualises strategy, lap-time degradation, driver-vs-driver telemetry and the colour-coded circuit map.

> **Live app:** [ds24t-3.streamlit.app](https://ds24t-3.streamlit.app)  
> **Documentation site (Quarto):** built from `docs/`, deployed via GitHub Actions: [Documentation](https://vdss-fs26-ds24t.github.io/ds24t-3-fancyproject/)  
> **Course:** VDSS · ZHAW BSc Data Science · Group DS24T-3

## At a glance

| Page | What you see |
|------|--------------|
| **Home** | KPI cards + strategy snapshot + race narrative for the selected race |
| **Strategy** | Position progression, gap to a chosen reference, tyre-strategy stint chart, pit stop summary |
| **Lap Times** | Lap-by-lap progression with per-stint trendlines, compound strip, competitor overlay |
| **Telemetry** | Driver-vs-driver comparison (speed/throttle/brake over distance) with delta chart and corner analysis |
| **Track Map** | Circuit outline coloured by speed, throttle, brake or gear for any selected lap |

## Repository structure

```
streamlit_app.py          ← entry point: page config, sidebar race selector, navigation
data_acquisition/         ← FastF1 data fetching with @st.cache_data decorators
pages/                    ← one module per Streamlit page (Home, Strategy, Lap Times, Telemetry, Track Map)
viz/                      ← Plotly chart builders (dark theme, Ferrari red #e8002d)
docs/                     ← Quarto documentation (deployed to GitHub Pages)
  ├─ project_charta.qmd
  ├─ data_report.qmd
  ├─ viz_design_report.qmd
  └─ presentation.qmd
```

The data flow is **FastF1 API → `loader.py` (cached) → `pages/*.py` → `viz/*.py` → Plotly → Streamlit.**

## Run the app locally

Requires **Python 3.12** and [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

```bash
# 1. clone
git clone https://github.com/vdss-fs26-ds24t/ds24t-3-fancyproject.git
cd ds24t-3-fancyproject

# 2. create the environment + install dependencies
uv sync

# 3. start the app
uv run streamlit run streamlit_app.py
```

The app opens at [http://localhost:8501](http://localhost:8501). In the sidebar pick a season and Grand Prix, then click **Load Race**.

The first telemetry load for a race takes ~30 seconds (FastF1 fetches and caches the raw timing data). A background thread warms the cache as soon as you click **Load Race**, so subsequent pages feel instant.

## Documentation site (Quarto)

The project documentation is a Quarto website rendered from the `docs/` folder.

```bash
# preview locally
cd docs && uv run quarto preview

# build static site to docs/build
cd docs && uv run quarto render
```

Every push to `main` triggers `.github/workflows/publish.yml`, which renders the Quarto project and deploys it to GitHub Pages. Python computations use the cached results in `docs/_freeze`, so the runner does not need Python.

## Tech stack

| Layer | Tool |
|-------|------|
| Data | FastF1 |
| Processing | Pandas, NumPy |
| Visualisation | Plotly (dark theme, Ferrari red `#e8002d`) |
| App framework | Streamlit |
| Documentation | Quarto on GitHub Pages |
| Hosting | Streamlit Community Cloud |
| Environment | uv (Python 3.12) |

## Team

Claudio Calamia · Stefan Hohl · Fynn Fischer — ZHAW BSc Data Science, group DS24T-3.

## AI declaration  

Claude Opus 4.7 (Anthropic) was used as a writing aid and for debugging support during the development of this project. All desing decisions, analyses and final content were reviewed and approved by the authors.

## Licence

See [`LICENSE`](LICENSE).
