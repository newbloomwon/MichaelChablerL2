"""
texas_ingestion.py — ERCOT Real-Time Data Ingestion for Texas
===============================================================
AI Grid Orchestrator — Texas Module

Pulls live data from ERCOT every 60 seconds:
  1. Grid Frequency  → Hz  (Reliability Mode trigger: freq < 59.97 Hz)
  2. Real-Time Prices → $/MWh (Settlement Point Prices)
  3. System Load      → MW demand forecast

When frequency drops below 59.97 Hz the grid is under stress —
this is the signal that demand is overwhelming supply and blackouts
are possible.  Our build steps in and "dims" the data center load
by 40 % to help stabilize the grid.

Usage:
    # Stand-alone (prints to terminal every 60s):
    python texas_ingestion.py

    # As an import (for Logic Engine / FastAPI / Dashboard):
    from texas_ingestion import fetch_texas_snapshot
    snapshot = fetch_texas_snapshot()
"""

import os
import time
import json
import logging
import requests
from html.parser import HTMLParser
from datetime import datetime, timezone
from typing import Optional, Tuple, List
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ERCOT_SUBSCRIPTION_KEY = os.getenv("ERCOT_SUBSCRIPTION_KEY", "")
ERCOT_USERNAME = os.getenv("ERCOT_USERNAME", "")
ERCOT_PASSWORD = os.getenv("ERCOT_PASSWORD", "")
ERCOT_CLIENT_ID = os.getenv("ERCOT_CLIENT_ID", "")
ERCOT_TOKEN_URL = os.getenv(
    "ERCOT_TOKEN_URL",
    "https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token",
)
ERCOT_BASE_URL = os.getenv("ERCOT_BASE_URL", "https://api.ercot.com/api/public-reports")
ERCOT_FREQUENCY_URL = os.getenv(
    "ERCOT_FREQUENCY_URL",
    "https://www.ercot.com/content/cdr/html/real_time_system_conditions.html",
)

POLL_INTERVAL_SECONDS = 60

# Texas Reliability Mode threshold (from PRD / Logic Engine)
FREQUENCY_THRESHOLD_HZ = 59.97   # below this → Reliability Mode
RELIABILITY_REDUCTION_PCT = 40   # reduce data center load by 40 %

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("texas_ingestion")


# ---------------------------------------------------------------------------
# OAuth2 token management (synchronous — mirrors maine_ingestion style)
# ---------------------------------------------------------------------------
_access_token: Optional[str] = None


def _get_ercot_token() -> str:
    """Fetch an OAuth2 bearer token from ERCOT's B2C ROPC flow."""
    global _access_token
    if not ERCOT_CLIENT_ID or ERCOT_CLIENT_ID == "YOUR_PUBLIC_CLIENT_ID":
        # Don't try to auth if no client ID is provided
        return ""

    resp = requests.post(
        ERCOT_TOKEN_URL,
        data={
            "grant_type": "password",
            "client_id": ERCOT_CLIENT_ID,
            "username": ERCOT_USERNAME,
            "password": ERCOT_PASSWORD,
            "scope": f"openid {ERCOT_CLIENT_ID} offline_access",
        },
        timeout=15,
    )
    if resp.status_code == 200:
        _access_token = resp.json().get("access_token")
        return _access_token
    else:
        log.error(f"ERCOT token request failed ({resp.status_code}): {resp.text[:200]}")
        return ""


def _ercot_api_get(path: str) -> Optional[dict]:
    """Authenticated GET against the ERCOT public-reports API."""
    global _access_token
    if not _access_token:
        _get_ercot_token()
    if not _access_token:
        return None

    url = ERCOT_BASE_URL + path
    headers = {
        "Authorization": f"Bearer {_access_token}",
        "Ocp-Apim-Subscription-Key": ERCOT_SUBSCRIPTION_KEY,
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 401:
            # token expired — refresh once
            _get_ercot_token()
            headers["Authorization"] = f"Bearer {_access_token}"
            resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            return resp.json()
        else:
            log.warning(f"ERCOT API {path} returned {resp.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        log.error(f"ERCOT API {path} error: {e}")
        return None


# ---------------------------------------------------------------------------
# HTML parser for the ERCOT Real-Time System Conditions page
# (works with NO credentials — this is our frequency fallback)
# ---------------------------------------------------------------------------

class _ERCOTConditionsParser(HTMLParser):
    """Parse the ERCOT real_time_system_conditions.html page."""

    def __init__(self) -> None:
        super().__init__()
        self._capture = False
        self.cells: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"td", "th"}:
            self._capture = True

    def handle_endtag(self, tag):
        if tag in {"td", "th"}:
            self._capture = False

    def handle_data(self, data):
        if self._capture:
            text = data.strip()
            if text:
                self.cells.append(text)


def _parse_conditions_page(html: str) -> dict:
    """
    Extract key values from ERCOT's Real-Time System Conditions HTML.

    Returns dict with any of:
      frequency_hz, current_load_mw, total_gen_mw, wind_output_mw, etc.
    """
    parser = _ERCOTConditionsParser()
    parser.feed(html)
    cells = parser.cells

    result = {}
    for idx, cell in enumerate(cells):
        low = cell.lower()
        if idx + 1 >= len(cells):
            continue
        next_val = cells[idx + 1]

        # Frequency
        if "frequency" in low and "current" in low:
            try:
                result["frequency_hz"] = float(next_val)
            except ValueError:
                pass

        # System-wide demand / load
        if "demand" in low or ("system" in low and "load" in low):
            try:
                result["current_load_mw"] = float(next_val.replace(",", ""))
            except ValueError:
                pass

        # Total generation capacity
        if "capacity" in low or ("total" in low and "gen" in low):
            try:
                result["total_gen_mw"] = float(next_val.replace(",", ""))
            except ValueError:
                pass

        # Wind output
        if "wind" in low and "output" not in low:
            pass
        if "wind" in low:
            try:
                result["wind_output_mw"] = float(next_val.replace(",", ""))
            except ValueError:
                pass

    return result


# ---------------------------------------------------------------------------
# Data fetchers — one per data source
# ---------------------------------------------------------------------------

def fetch_frequency() -> dict:
    """
    Fetch current ERCOT grid frequency.

    Primary: HTML scrape of real_time_system_conditions.html (no auth needed).
    Returns dict like:
    {
        "frequency_hz": 59.98,
        "source": "html",
        "current_load_mw": 45000,
        "total_gen_mw": 78000,
        "wind_output_mw": 12000,
        "below_threshold": False
    }
    """
    try:
        resp = requests.get(ERCOT_FREQUENCY_URL, timeout=15)
        if resp.status_code == 200:
            conditions = _parse_conditions_page(resp.text)
            freq = conditions.get("frequency_hz")
            if freq is not None:
                conditions["source"] = "html"
                conditions["below_threshold"] = freq < FREQUENCY_THRESHOLD_HZ
                return conditions
            else:
                log.warning("Frequency not found in ERCOT HTML page")
                return {}
        else:
            log.warning(f"ERCOT HTML page returned {resp.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        log.error(f"ERCOT HTML scrape error: {e}")
        return {}


def fetch_real_time_prices() -> dict:
    """
    Fetch ERCOT real-time settlement-point prices.

    ERCOT API returns records as arrays (not dicts).
    Fields: [deliveryDate, deliveryHour, deliveryInterval,
             settlementPoint, settlementPointType, settlementPointPrice, DSTFlag]

    Returns dict like:
    {
        "timestamp": "2026-03-03",
        "hub_avg_price": 42.50,
        "num_nodes": 50,
        "prices": [ { "node": "HB_HOUSTON", "price": 43.2 }, ... ]
    }
    """
    data = _ercot_api_get("/np6-905-cd/spp_node_zone_hub?size=50")
    if not data:
        return {}

    records = data.get("data", [])
    if not isinstance(records, list):
        records = []

    prices = []
    total_price = 0.0
    count = 0
    timestamp = ""

    for rec in records:
        # Records can be arrays or dicts depending on API version
        if isinstance(rec, list) and len(rec) >= 6:
            # Array format: [date, hour, interval, node, type, price, dst]
            ts = str(rec[0])
            node = str(rec[3])
            price_val = rec[5]
        elif isinstance(rec, dict):
            ts = rec.get("deliveryDate", rec.get("DeliveryDate", ""))
            node = rec.get("settlementPoint", rec.get("SettlementPointName", "Unknown"))
            price_val = rec.get("settlementPointPrice", rec.get("SettlementPointPrice", 0))
        else:
            continue

        if ts:
            timestamp = str(ts)

        try:
            price_float = float(price_val)
        except (TypeError, ValueError):
            price_float = 0.0

        prices.append({"node": node, "price": price_float})
        total_price += price_float
        count += 1

    avg_price = (total_price / count) if count > 0 else 0.0

    return {
        "timestamp": timestamp,
        "hub_avg_price": round(avg_price, 2),
        "num_nodes": count,
        "prices": prices,
    }


def fetch_load_forecast() -> dict:
    """
    Fetch ERCOT system-wide load forecast.

    ERCOT API returns records as arrays for the lf_by_model_study_area endpoint.
    Fields: [postedDatetime, deliveryDate, hourEnding, valley, model, DSTFlag]

    NOTE: The 'valley' field is the minimum load for a SINGLE study area
    (typically ~1,000-1,500 MW), NOT the system total (~50,000-60,000 MW).
    We sum across all models for each hour to approximate system forecast,
    but the HTML scraper's current_load_mw is the authoritative real-time value.

    Returns dict like:
    {
        "timestamp": "2026-03-03T18:30:00",
        "forecast_mw": 52000,
        "num_records": 20,
        "source_note": "Sum of study-area valleys (approximate)"
    }
    """
    data = _ercot_api_get("/np3-566-cd/lf_by_model_study_area?size=100")
    if not data:
        return {}

    records = data.get("data", [])
    if not isinstance(records, list):
        records = []

    # Sum valley values by (date, hour) for model 'E' (primary model)
    # to approximate system-wide totals
    by_date_hour = {}
    timestamp = ""

    for rec in records:
        if isinstance(rec, list) and len(rec) >= 5:
            ts = str(rec[0])
            date = str(rec[1])
            hour = str(rec[2])
            mw_val = rec[3]
            model = str(rec[4])

            if ts:
                timestamp = ts

            # Use model 'E' (primary ensemble) only to avoid double-counting
            if model != "E":
                continue

            try:
                mw_float = float(mw_val)
            except (TypeError, ValueError):
                continue

            key = (date, hour)
            by_date_hour.setdefault(key, 0.0)
            by_date_hour[key] += mw_float

        elif isinstance(rec, dict):
            ts = rec.get("postedDatetime", rec.get("DeliveryDate", ""))
            if ts:
                timestamp = str(ts)
            mw_val = rec.get("valley", rec.get("SystemTotal", rec.get("forecast", 0)))
            try:
                mw_float = float(mw_val)
            except (TypeError, ValueError):
                continue

            key = (str(rec.get("deliveryDate", "")), str(rec.get("hourEnding", "")))
            by_date_hour.setdefault(key, 0.0)
            by_date_hour[key] += mw_float

    # Find the peak hour across all forecast periods
    forecast_mw = max(by_date_hour.values()) if by_date_hour else 0.0

    return {
        "timestamp": timestamp,
        "forecast_mw": round(forecast_mw, 1),
        "num_records": len(records),
        "source_note": "Sum of study-area valleys (approximate)",
    }


# ---------------------------------------------------------------------------
# Combined snapshot — the single function everyone imports
# ---------------------------------------------------------------------------

def fetch_texas_snapshot() -> dict:
    """
    Pull all Texas / ERCOT data into one clean snapshot.

    This is the single function the Logic Engine, Dashboard, and
    background worker import.

    Returns:
    {
        "state": "texas",
        "fetched_at": "2026-03-03T...",
        "frequency": {
            "frequency_hz": 59.98,
            "below_threshold": False,
            "source": "html",
            "current_load_mw": 45000,
            ...
        },
        "prices": {
            "hub_avg_price": 42.50,
            ...
        },
        "load_forecast": {
            "forecast_mw": 52000,
            ...
        },
        "reliability_mode_triggered": True/False,
        "trigger_reasons": [...]
    }
    """
    frequency = fetch_frequency()
    prices = fetch_real_time_prices()
    load_forecast = fetch_load_forecast()

    # Determine if Reliability Mode should activate
    trigger_reasons = []
    freq_hz = frequency.get("frequency_hz")
    if freq_hz is not None and freq_hz < FREQUENCY_THRESHOLD_HZ:
        trigger_reasons.append(
            f"frequency_at_{freq_hz:.4f}Hz_below_{FREQUENCY_THRESHOLD_HZ}Hz"
        )

    reliability_mode = len(trigger_reasons) > 0

    snapshot = {
        "state": "texas",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "frequency": frequency,
        "prices": prices,
        "load_forecast": load_forecast,
        "reliability_mode_triggered": reliability_mode,
        "trigger_reasons": trigger_reasons,
    }

    return snapshot


# ---------------------------------------------------------------------------
# Pretty-print for terminal monitoring
# ---------------------------------------------------------------------------

def print_snapshot(snap: dict):
    """Print a human-readable summary of the Texas grid snapshot."""
    ts = snap.get("fetched_at", "N/A")
    freq = snap.get("frequency", {})
    prices = snap.get("prices", {})
    lf = snap.get("load_forecast", {})
    reliability = snap.get("reliability_mode_triggered", False)
    reasons = snap.get("trigger_reasons", [])

    hz = freq.get("frequency_hz", "N/A")
    load_mw = freq.get("current_load_mw", "N/A")
    gen_mw = freq.get("total_gen_mw", "N/A")
    wind_mw = freq.get("wind_output_mw", "N/A")

    print("\n" + "=" * 65)
    print(f"  🤠  TEXAS / ERCOT GRID SNAPSHOT")
    print(f"  Fetched: {ts}")
    print("=" * 65)

    # Frequency
    if isinstance(hz, float):
        freq_status = "🔴 BELOW THRESHOLD" if freq.get("below_threshold") else "🟢 Normal"
        delta = hz - FREQUENCY_THRESHOLD_HZ
        print(f"\n  ⚡ GRID FREQUENCY: {hz:.4f} Hz  {freq_status}")
        print(f"     Threshold: {FREQUENCY_THRESHOLD_HZ} Hz  (delta: {delta:+.4f} Hz)")
    else:
        print(f"\n  ⚡ GRID FREQUENCY: unavailable")

    # System conditions from HTML
    if isinstance(load_mw, (int, float)):
        print(f"     Current Load: {load_mw:,.0f} MW")
    if isinstance(gen_mw, (int, float)):
        print(f"     Total Gen Capacity: {gen_mw:,.0f} MW")
    if isinstance(wind_mw, (int, float)):
        print(f"     Wind Output: {wind_mw:,.0f} MW")

    # Prices
    avg_price = prices.get("hub_avg_price", "N/A")
    print(f"\n  💰 AVG SETTLEMENT PRICE: ${avg_price}/MWh")
    print(f"     Nodes sampled: {prices.get('num_nodes', 0)}")

    # Reserve margin (authoritative from HTML scraper)
    load_mw = conds.get("current_load_mw")
    gen_mw = conds.get("total_gen_mw")
    if load_mw and gen_mw and gen_mw > 0:
        reserve = gen_mw - load_mw
        reserve_pct = reserve / gen_mw * 100
        icon = "🟢" if reserve_pct > 20 else "🟡" if reserve_pct > 10 else "🔴"
        print(f"\n  {icon} RESERVE MARGIN: {reserve:,.0f} MW ({reserve_pct:.1f}%)")

    # Reliability Mode Status
    print(f"\n  {'─' * 50}")
    if reliability:
        print(f"  🔴 RELIABILITY MODE: TRIGGERED")
        print(f"     Action: Reduce data center load by {RELIABILITY_REDUCTION_PCT}%")
        for r in reasons:
            print(f"       → {r}")
    else:
        print(f"  🟢 RELIABILITY MODE: INACTIVE — Grid frequency normal")

    print("=" * 65)


# ---------------------------------------------------------------------------
# Main loop — standalone terminal monitoring
# ---------------------------------------------------------------------------

def main():
    """Poll ERCOT every 60 seconds and print to terminal."""
    print("🤠  AI Grid Orchestrator — Texas Data Ingestion")
    print(f"   Polling ERCOT every {POLL_INTERVAL_SECONDS} seconds...")
    print(f"   Reliability Mode triggers:")
    print(f"     • Frequency < {FREQUENCY_THRESHOLD_HZ} Hz")
    print(f"     • Action: Reduce load {RELIABILITY_REDUCTION_PCT}%")
    print(f"   Press Ctrl+C to stop.\n")

    cycle = 0
    while True:
        cycle += 1
        log.info(f"Cycle {cycle} — fetching data...")
        try:
            snapshot = fetch_texas_snapshot()
            print_snapshot(snapshot)

            freq_hz = snapshot["frequency"].get("frequency_hz", "?")
            log.info(
                f"Freq={freq_hz}Hz | "
                f"AvgPrice=${snapshot['prices'].get('hub_avg_price', '?')}/MWh | "
                f"Reliability={'ON' if snapshot['reliability_mode_triggered'] else 'OFF'}"
            )
        except Exception as e:
            log.error(f"Cycle {cycle} failed: {e}")

        log.info(f"Next refresh in {POLL_INTERVAL_SECONDS}s...\n")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Texas ingestion stopped.")
