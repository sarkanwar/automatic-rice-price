
import os, json, pandas as pd, matplotlib.pyplot as plt
from fetcher import fetch_datagov_prices_csv
from model import train_and_forecast

API_KEY = os.environ.get("DATA_GOV_IN_API_KEY", "")
RESOURCE_ID = os.environ.get("DATA_GOV_IN_RESOURCE_ID", "")
COMMODITY = os.environ.get("COMMODITY_FILTER", "Rice")
STATE = os.environ.get("STATE_FILTER", "")
CENTRE = os.environ.get("CENTRE_FILTER", "")
DATE_FROM = os.environ.get("DATE_FROM", "")
DATE_TO = os.environ.get("DATE_TO", "")

os.makedirs("data", exist_ok=True)

# 1) Fetch
csv_path = "data/basmati_prices.csv"
fetch_datagov_prices_csv(API_KEY, RESOURCE_ID, csv_path, COMMODITY, STATE or None, CENTRE or None,
                         DATE_FROM or None, DATE_TO or None, prefer_csv=False)

# 2) Train + Forecast
df = pd.read_csv(csv_path)
metrics, outs = train_and_forecast(df, horizons=[7,30,180])

with open("data/metrics.json","w") as f:
    json.dump(metrics, f, indent=2, default=str)

for h, fdf in outs.items():
    out_csv = f"data/forecast_{h}d.csv"
    fdf.to_csv(out_csv, index=False)
    # Chart
    fig = plt.figure()
    plt.plot(fdf['date'], fdf['forecast'], label='Forecast')
    plt.fill_between(fdf['date'], fdf['lower_95'], fdf['upper_95'], alpha=0.2, label='95% PI')
    plt.legend(); plt.tight_layout()
    fig.savefig(f"data/forecast_{h}d.png")
    plt.close(fig)

print("Build complete.")
