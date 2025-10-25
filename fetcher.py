
from __future__ import annotations
import os, io, re, sys
import pandas as pd, requests

BASE = "https://api.data.gov.in/resource"

def _extract_resource_id(s: str) -> str:
    s = (s or "").strip()
    m = re.search(r"/resource/([A-Za-z0-9\-]+)$", s)
    if m: return m.group(1)
    if s.startswith("resource/"): return s.split("/", 1)[1]
    return s

def fetch_datagov_prices_csv(api_key: str, resource_id: str, out_csv: str,
                             commodity_filter: str = "Rice", state: str | None = None,
                             centre: str | None = None, date_from: str | None = None,
                             date_to: str | None = None, prefer_csv: bool = False) -> str:
    rid = _extract_resource_id(resource_id)
    if not rid:
        raise ValueError("Invalid Resource ID: please use the UUID.")
    url = f"{BASE}/{rid}"
    session = requests.Session()
    limit, offset, rows = 1000, 0, []

    while True:
        params = {"api-key": api_key, "limit": limit, "offset": offset, "format": "csv" if prefer_csv else "json"}
        if date_from: params["from"] = date_from
        if date_to: params["to"] = date_to
        r = session.get(url, params=params, timeout=45)
        if r.status_code in (404,405):
            raise requests.HTTPError(f"{r.status_code} for {url}. Check Resource ID rid='{rid}'. Full: {r.url}", response=r)
        r.raise_for_status()
        ct = (r.headers.get("content-type") or "").lower()
        if prefer_csv or "csv" in ct:
            df_chunk = pd.read_csv(io.StringIO(r.text))
            if df_chunk.empty: break
            rows.append(df_chunk); break
        else:
            try:
                payload = r.json()
            except Exception as e:
                raise ValueError(f"Non-JSON response (first 300 chars): {(r.text or '')[:300]}") from e
            chunk = payload.get("records", [])
            if not chunk: break
            rows.extend(chunk)
            if len(chunk) < limit: break
            offset += limit

    if not rows:
        pd.DataFrame(columns=["Date","Price"]).to_csv(out_csv, index=False); return out_csv

    if isinstance(rows[0], pd.DataFrame):
        df = pd.concat(rows, ignore_index=True)
    else:
        df = pd.DataFrame(rows)

    df.columns = [c.lower() for c in df.columns]
    # Optional filters
    if "commodity" in df.columns and commodity_filter:
        df = df[df["commodity"].str.contains(commodity_filter, case=False, na=False)]
    if state and "state" in df.columns:
        df = df[df["state"].str.contains(state, case=False, na=False)]
    if centre and "centre" in df.columns:
        df = df[df["centre"].str.contains(centre, case=False, na=False)]

    # Date/Price detection
    date_candidates = [c for c in ["date","reported_date","price_date","created_date","month","day"] if c in df.columns]
    if not date_candidates:
        for c in df.columns:
            try:
                pd.to_datetime(df[c]); date_candidates.append(c); break
            except Exception: pass
    if not date_candidates:
        raise ValueError("No date-like column found in dataset.")

    price_candidates = [c for c in ["retail","wholesale","modal_price","price","wholesale_price","retail_price"] if c in df.columns]
    if not price_candidates:
        num_cols = [c for c in df.columns if pd.to_numeric(df[c], errors='coerce').notna().any()]
        if not num_cols: raise ValueError("No numeric price column detected.")
        price_candidates = [num_cols[0]]

    date_col, price_col = date_candidates[0], price_candidates[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    df = df.dropna(subset=[date_col, price_col])

    daily = (df.groupby(df[date_col].dt.date, as_index=False)[price_col].mean()
             .rename(columns={date_col:"Date", price_col:"Price"}).sort_values("Date"))
    os.makedirs("data", exist_ok=True)
    daily.to_csv(out_csv, index=False)
    return out_csv
