
# data.gov.in Resource Finder

A tiny Streamlit tool to help you choose the correct **Resource ID (UUID)** for your rice price app.

## What it does
- Accepts a **dataset page URL**, **API URL**, or **UUID**.
- Extracts the **Resource ID** automatically.
- Tests it using your **API key**.
- Shows a **data preview** and **suggested filter columns** (commodity/state/centre/date/price).

## How to run (Streamlit Cloud)
1. Create a new repo and upload these 3 files:
   - `resource_finder_app.py`
   - `utils_resource.py`
   - `requirements.txt`
2. Deploy on Streamlit:
   - Main file: `resource_finder_app.py`
3. Enter your **API key** and paste a dataset page URL → click **Test Resource**.

## Next
Once you confirm a working Resource ID, copy the UUID and paste it into your main automatic app's secrets:
- `DATA_GOV_IN_RESOURCE_ID = <UUID>`
