# Nigeria & Peers: Economic Dashboard

[![tests](https://github.com/Bak-AbasiUdoessien/ng-economy-dashboard/actions/workflows/tests.yml/badge.svg)](https://github.com/Bak-AbasiUdoessien/ng-economy-dashboard/actions/workflows/tests.yml)

**▶ Live app:** _add your Streamlit Cloud link here after deploying (steps below)_

An interactive **Streamlit** dashboard that compares Nigeria with Ghana, Kenya, South Africa and Egypt on inflation, GDP growth, GDP per person, exchange rates, unemployment and remittances. The data comes from World Bank Open Data and is refreshed **every week** by my [ETL pipeline](https://github.com/Bak-AbasiUdoessien/ng-economic-data-pipeline). The two projects work together as one small data platform:

```
World Bank API → ETL pipeline (GitHub Actions, weekly) → indicators.csv → this dashboard (Streamlit Cloud)
```

## Features
- **KPI tiles** with Nigeria's latest values and the change from the previous year. A rise in inflation, the exchange rate or unemployment shows red.
- An **interactive trend chart** with hover tooltips and a label at the end of each line.
- **Exchange rates shown as an index** (first year = 100), because naira, cedi and shillings can't share one axis.
- A **latest-year ranking** chart.
- **Plain-English insights** generated from the selected data.
- A **data table and CSV download**, which is also the accessible view of every chart.
- **Colour-blind-checked palette**, where each country keeps its colour whatever you filter.
- A **safe fallback:** if the live data can't load, it shows clearly labelled demo data instead of crashing.

## Run locally
```bash
python -m venv .venv && .venv\Scripts\activate        # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
streamlit run app.py                                  # opens http://localhost:8501
python -m pytest -v                                   # 7 tests, including a headless render of the app
```

## Deploy free on Streamlit Community Cloud
1. Go to **share.streamlit.io** and sign in with GitHub (as Bak-AbasiUdoessien).
2. Click **Create app**, choose this repo, branch `main` and file `app.py`, then **Deploy**.
3. Copy the URL into the "Live app" line at the top of this README.

## Code structure
| File | What it does |
|---|---|
| `app.py` | The Streamlit page: filters, tiles, charts and table |
| `analysis.py` | Data loading and the calculations, unit-tested separately from the UI |
| `make_demo_data.py` | Builds the **made-up** fallback data |
| `tests/` | pytest tests, plus Streamlit's `AppTest` for rendering the app headlessly |

Source: World Bank Open Data (CC BY 4.0).
