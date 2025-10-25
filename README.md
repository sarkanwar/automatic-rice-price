
# 🌾 Automatic Rice Price Website (Streamlit + GitHub Actions)

This repo gives you a **fully automatic** website:
- **GitHub Action** runs **daily** (03:30 IST), fetches rice prices from **data.gov.in**, builds **7d/30d/180d** forecasts, and **commits** the results.
- **Streamlit** site reads the committed files and displays tables/charts. You also get a **manual Rebuild button**.

## 🚀 Deploy

1. **Create a new GitHub repo** and upload everything in this ZIP.
2. In your repo, add **Secrets** (Settings → Secrets and variables → Actions → *New repository secret*):
   - `DATA_GOV_IN_API_KEY` = your data.gov.in API key
   - `DATA_GOV_IN_RESOURCE_ID` = the dataset resource id (UUID or full URL)
3. (Optional) Add **Repository variables** (Settings → Secrets and variables → Actions → *Variables*):
   - `COMMODITY_FILTER` (default "Rice")
   - `STATE_FILTER` (e.g., "Haryana")
   - `CENTRE_FILTER` (e.g., "Karnal")
   - `DATE_FROM`, `DATE_TO` (YYYY-MM-DD; optional)
4. Enable **Actions** for the repo if disabled.
5. **Streamlit Cloud → New app**
   - Repository: your repo
   - Branch: `main`
   - Main file path: `streamlit_app.py`
   - Python: 3.11

First run may show “No data yet” until the Action finishes. You can trigger it immediately with **Actions → Daily rice fetch & forecast → Run workflow**.

## 🛠 Local manual run (optional)
```
pip install -r requirements.txt
export DATA_GOV_IN_API_KEY=... DATA_GOV_IN_RESOURCE_ID=...
python scripts/fetch_and_build.py
streamlit run streamlit_app.py
```

## 📁 Outputs
- `data/basmati_prices.csv` — cleaned daily series (Date, Price)
- `data/forecast_7d.csv|png`, `data/forecast_30d.*`, `data/forecast_180d.*`
- `data/metrics.json`

Enjoy your automated rice price dashboard!
