
import streamlit as st
import pandas as pd
from utils_resource import extract_resource_id, test_resource, suggest_filters

st.set_page_config(page_title="data.gov.in Resource Finder", page_icon="🔎", layout="wide")
st.title("🔎 data.gov.in Resource Finder (for Rice Prices)")

st.write("Paste a **dataset page URL** or a **resource API URL** or just the **UUID**. Enter your API key and test.")

with st.form("finder"):
    c1, c2 = st.columns([2,1])
    with c1:
        inp = st.text_input("Dataset page URL / API URL / UUID", key="input_url", placeholder="https://api.data.gov.in/resource/<UUID> or https://data.gov.in/... or <UUID>")
    with c2:
        api_key = st.text_input("API key", type="password", key="api_key")
    c3, c4 = st.columns([1,1])
    with c3:
        prefer_csv = st.checkbox("Prefer CSV", value=False)
    with c4:
        limit = st.number_input("Preview rows", min_value=1, max_value=1000, value=50, step=1)
    submitted = st.form_submit_button("Test Resource")

if submitted:
    if not api_key:
        st.error("Please enter your API key.")
    elif not inp.strip():
        st.error("Please paste a dataset URL or Resource UUID.")
    else:
        ok, info, df, err = test_resource(api_key, inp.strip(), limit=limit, prefer_csv=prefer_csv)
        rid = extract_resource_id(inp)
        st.write("**Extracted Resource ID:**", rid or "❌ (could not extract)")
        st.write("**Request URL:**", info.get("request_url",""))
        st.write("**HTTP status:**", info.get("status",""))
        st.write("**Content-Type:**", info.get("content_type",""))
        if ok and df is not None:
            st.success("Looks good! Showing a preview of the data below.")
            st.dataframe(df.head(min(len(df), limit)), use_container_width=True)
            sugg = suggest_filters(df)
            st.markdown("### Suggested filters")
            st.json(sugg)
            st.info("Copy the **Resource ID (UUID)** above and paste it into your main app. Use suggested columns for Commodity/State/Centre if present.")
        else:
            st.error("Failed to fetch/parse this resource.")
            if err:
                st.code(err)

st.divider()
st.caption("Tip: Pick resources that have clear date and numeric price columns, plus optional commodity/state/centre fields.")
