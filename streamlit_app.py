
import os, subprocess, sys
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Automatic Rice Prices", page_icon="🌾", layout="wide")
st.title("🌾 Automatic Rice Price Dashboard")

st.caption("Data auto-updates daily via GitHub Actions. Use the controls below to rebuild manually here.")

# --- Panel: Current Data ---
if os.path.exists("data/basmati_prices.csv"):
    df = pd.read_csv("data/basmati_prices.csv")
    st.subheader("Latest Daily Prices")
    st.dataframe(df.tail(30), use_container_width=True)
else:
    st.warning("No data yet. The first scheduled run or a manual rebuild will create it.")

# --- Panel: Forecasts ---
st.subheader("Forecasts")
row = st.columns(3)
for i, h in enumerate([7, 30, 180]):
    csvp = f"data/forecast_{h}d.csv"
    imgp = f"data/forecast_{h}d.png"
    with row[i]:
        st.markdown(f"**{h}-day forecast**")
        if os.path.exists(csvp):
            fdf = pd.read_csv(csvp)
            st.dataframe(fdf.head(), use_container_width=True)
            if os.path.exists(imgp):
                st.image(imgp, use_column_width=True)
            st.download_button(
                f"Download {h}d CSV",
                data=fdf.to_csv(index=False).encode("utf-8"),
                file_name=f"forecast_{h}d.csv",
                mime="text/csv",
                key=f"dl{h}",
            )
        else:
            st.info("Not generated yet.")

st.divider()

# --- Manual Rebuild (Streamlit runtime) ---
st.subheader("Manual Rebuild (runs here in Streamlit)")

col1, col2 = st.columns(2)
with col1:
    api_key_ui = st.text_input("data.gov.in API key", value=st.secrets.get("DATA_GOV_IN_API_KEY", ""), type="password")
    resource_id_ui = st.text_input("Resource ID (UUID or full URL)", value=st.secrets.get("DATA_GOV_IN_RESOURCE_ID", ""))
    commodity_ui = st.text_input("Commodity filter", value=st.secrets.get("COMMODITY_FILTER", "Rice"))
with col2:
    state_ui = st.text_input("State (optional)", value=st.secrets.get("STATE_FILTER", ""))
    centre_ui = st.text_input("Centre/City (optional)", value=st.secrets.get("CENTRE_FILTER", ""))
    date_from_ui = st.text_input("From (YYYY-MM-DD)", value=st.secrets.get("DATE_FROM", ""))
    date_to_ui = st.text_input("To (YYYY-MM-DD)", value=st.secrets.get("DATE_TO", ""))

run_it = st.button("Run fetch & forecast now")
if run_it:
    if not api_key_ui or not resource_id_ui:
        st.error("Please provide API key and Resource ID (set them above or in Streamlit Secrets).")
    else:
        env = dict(os.environ)
        env.update(
            DATA_GOV_IN_API_KEY=api_key_ui,
            DATA_GOV_IN_RESOURCE_ID=resource_id_ui,
            COMMODITY_FILTER=commodity_ui or "Rice",
            STATE_FILTER=state_ui or "",
            CENTRE_FILTER=centre_ui or "",
            DATE_FROM=date_from_ui or "",
            DATE_TO=date_to_ui or "",
        )
        try:
            r = subprocess.run(
                [sys.executable, "scripts/fetch_and_build.py"],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            st.success("Rebuild complete.")
            if r.stdout:
                st.code(r.stdout, language="bash")
            if r.stderr:
                st.code(r.stderr, language="bash")
            # Show updated tables
            if os.path.exists("data/basmati_prices.csv"):
                df2 = pd.read_csv("data/basmati_prices.csv")
                st.dataframe(df2.tail(10), use_container_width=True)
        except subprocess.CalledProcessError as e:
            st.error("Fetch/build failed. See details below.")
            st.code(e.stdout or "", language="bash")
            st.code(e.stderr or "", language="bash")
        except Exception as e:
            st.exception(e)

st.divider()
st.caption("Tip: set your API key and resource id in Streamlit → Settings → Secrets for one-click rebuilds.")
