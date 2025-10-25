
import os, sys, json, platform, traceback
import streamlit as st

st.set_page_config(page_title="Streamlit Diagnostics", page_icon="🛠", layout="wide")
st.title("🛠 Streamlit App Diagnostics")

st.subheader("Environment")
st.json({
    "python": sys.version.splitlines()[0],
    "executable": sys.executable,
    "cwd": os.getcwd(),
    "platform": platform.platform(),
})

st.subheader("Repository files (top-level)")
try:
    files = sorted(os.listdir("."))
    st.write(files)
except Exception as e:
    st.exception(e)

st.subheader("Key files present?")
checks = {}
for p in ["streamlit_app.py", "scripts/fetch_and_build.py", "fetcher.py", "model.py", "requirements.txt", "data"]:
    checks[p] = os.path.exists(p)
st.json(checks)

st.subheader("Secrets (just shows presence, not values)")
sec_keys = ["DATA_GOV_IN_API_KEY","DATA_GOV_IN_RESOURCE_ID","COMMODITY_FILTER","STATE_FILTER","CENTRE_FILTER","DATE_FROM","DATE_TO"]
present = {k: ("✅ set" if k in st.secrets else "❌ missing") for k in sec_keys}
st.json(present)

st.subheader("Import tests")
problems = []
def try_import(mod):
    try:
        __import__(mod)
        st.success(f"Imported: {mod}")
    except Exception as e:
        st.error(f"Failed import: {mod} -> {e.__class__.__name__}: {e}")
        problems.append((mod, e, traceback.format_exc()))

for mod in ["pandas","requests","statsmodels","sklearn","xgboost","matplotlib"]:
    try_import(mod)

st.subheader("Data folder listing")
try:
    if os.path.isdir("data"):
        st.write(sorted(os.listdir("data")))
    else:
        st.info("No 'data' folder yet (first build will create it).")
except Exception as e:
    st.exception(e)

st.divider()
st.caption("If everything above looks good, switch your main file back to streamlit_app.py and try again.")
