
import re, requests, pandas as pd, io

RESOURCE_BASE = "https://api.data.gov.in/resource"

def extract_resource_id(s: str) -> str:
    """Accepts a full dataset page URL, a full API URL, or just the UUID. Returns the UUID string."""
    s = (s or "").strip()
    # Full API URL
    m = re.search(r"/resource/([a-fA-F0-9\-]{36})(?:\b|/|$)", s)
    if m:
        return m.group(1)
    # Maybe the user put the page URL with query params; still try to match a UUID anywhere
    m = re.search(r"\b([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})\b", s)
    if m:
        return m.group(1)
    # Raw UUID
    if re.fullmatch(r"[a-fA-F0-9\-]{36}", s):
        return s
    # Resource path like resource/<uuid>
    if s.startswith("resource/"):
        return s.split("/", 1)[1]
    return ""

def test_resource(api_key: str, resource_id_or_url: str, limit: int = 20, prefer_csv: bool = False):
    """Return (ok, info_dict, df_preview_or_none, error_message_or_none)."""
    rid = extract_resource_id(resource_id_or_url)
    if not rid:
        return False, {}, None, "Could not extract a Resource ID from the input."
    base = RESOURCE_BASE + "/" + rid
    params = {"api-key": api_key, "limit": limit, "offset": 0, "format": "csv" if prefer_csv else "json"}
    try:
        r = requests.get(base, params=params, timeout=45)
    except Exception as e:
        return False, {"request_url": base, "params": params}, None, f"Request failed: {e}"
    info = {"request_url": r.url, "status": r.status_code, "content_type": r.headers.get("content-type","")}
    if r.status_code in (404, 405):
        return False, info, None, f"HTTP {r.status_code}. This usually means wrong Resource ID or path."
    try:
        r.raise_for_status()
    except Exception as e:
        return False, info, None, f"HTTP error: {e}"

    ct = (r.headers.get("content-type") or "").lower()
    if prefer_csv or "csv" in ct:
        try:
            df = pd.read_csv(io.StringIO(r.text))
            return True, info, df, None
        except Exception as e:
            return False, info, None, f"CSV parse error: {e}"
    else:
        # Expect JSON
        try:
            payload = r.json()
        except Exception:
            head = (r.text or "")[:300]
            return False, info, None, f"Non-JSON response. First 300 chars: {head}"
        records = payload.get("records", [])
        df = pd.DataFrame(records)
        return True, info, df, None

def suggest_filters(df: pd.DataFrame):
    """Look at columns and suggest which filters make sense."""
    cols = [c.lower() for c in df.columns]
    suggestions = {
        "date_columns": [c for c in cols if any(k in c for k in ["date","month","day"])],
        "commodity_columns": [c for c in cols if "commodity" in c],
        "state_columns": [c for c in cols if "state" in c],
        "centre_columns": [c for c in cols if c in ("centre","center","city","market") or any(k in c for k in ["centre","center","city","market"])],
        "price_columns": [c for c in cols if any(k in c for k in ["price","retail","wholesale","modal"])],
        "all_columns": cols,
    }
    return suggestions
