
import os, json, time
import streamlit as st, pandas as pd, matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Automatic Rice Prices", page_icon="🌾", layout="wide")
st.title("🌾 Automatic Rice Price Dashboard")

st.caption("Data auto-updates daily via GitHub Actions. You can also refresh from the latest commit here.")

colA, colB = st.columns([2,1])
with colB:
    auto_refresh = st.toggle("Auto-refresh every 60s", value=False, key="autorefresh")
    if auto_refresh:
        st.experimental_rerun()

# Show latest dataset
if os.path.exists("data/basmati_prices.csv"):
    df = pd.read_csv("data/basmati_prices.csv")
    st.subheader("Latest Daily Prices")
    st.dataframe(df.tail(30), use_container_width=True)
else:
    st.warning("No data yet. The first scheduled run will create it.")

# Forecasts
st.subheader("Forecasts")
row = st.columns(3)
for i, h in enumerate([7,30,180]):
    csvp = f"data/forecast_{h}d.csv"
    imgp = f"data/forecast_{h}d.png"
    with row[i]:
        st.markdown(f"**{h}-day forecast**")
        if os.path.exists(csvp):
            fdf = pd.read_csv(csvp)
            st.dataframe(fdf.head(), use_container_width=True)
            if os.path.exists(imgp):
                st.image(imgp, use_column_width=True)
            st.download_button(f"Download {h}d CSV", data=fdf.to_csv(index=False).encode("utf-8"),
                               file_name=f"forecast_{h}d.csv", mime="text/csv", key=f"dl{h}")
        else:
            st.info("Not generated yet.")

st.divider()
st.subheader("Manual Rebuild (optional)")
if st.button("Rebuild now (local run)", key="rebuild"):
    try:
        import subprocess, sys
        r = subprocess.run([sys.executable, "scripts/fetch_and_build.py"], check=True, capture_output=True, text=True)
        st.success("Rebuild complete.")
        st.text(r.stdout or "")
    except Exception as e:
        st.exception(e)
