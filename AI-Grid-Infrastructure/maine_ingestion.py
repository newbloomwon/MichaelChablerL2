"""
maine_ingestion.py — ISO-NE Real-Time Data Ingestion for Maine
================================================================
AI Grid Orchestrator — Gary's Module (Tuesday Build)

Pulls live data from ISO-NE every 60 seconds:
  1. Fuel Mix       → gas % (Green Mode trigger #1: gas > 50%)
  2. Maine LMP      → $/MWh  (Green Mode trigger #2: price > $150)
  3. System Load    → MW demand
  4. Power Status   → grid condition

Outputs a clean GridSnapshot dict that the Logic Engine can consume.

Usage:
    # Stand-alone (prints to terminal every 60s):
    python maine_ingestion.py

    # As an import (for Logic Engine / FastAPI):
    from maine_ingestion import fetch_maine_snapshot
    snapshot = fetch_maine_snapshot()
"""

import os
import time
import json
import logging
import requests
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ISONE_USERNAME = os.getenv("ISONE_USERNAME")
ISONE_PASSWORD = os.getenv("ISONE_PASSWORD")
BASE_URL = "https://webservices.iso-ne.com/api/v1.1"

POLL_INTERVAL_SECONDS = 60  # how often to refresh (PRD says every 60s)

# Maine Green Mode thresholds (from PRD Section 5, Feature 2)
GAS_THRESHOLD_PCT = 50.0     # gas above 50% → Green Mode
PRICE_THRESHOLD_MWH = 150.0  # price above $150/MWh → Green Mode

# ISO-NE location ID for Maine load zone
MAINE_LOCATION_ID = "4001"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("maine_ingestion")

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _get(endpoint: str) -> Optional[dict]:
    """Make an authenticated GET to the ISO-NE API. Returns parsed JSON or None."""
    url = BASE_URL + endpoint
    try:
        resp = requests.get(
            url,
            auth=(ISONE_USERNAME, ISONE_PASSWORD),
            timeout=15,
            headers={"Accept": "application/json"},
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            log.warning(f"API {endpoint} returned {resp.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        log.error(f"API {endpoint} error: {e}")
        return None


# ---------------------------------------------------------------------------
# Data parsers — one per endpoint
# ---------------------------------------------------------------------------

def fetch_fuel_mix() -> dict:
    """
    Fetch current generation fuel mix from ISO-NE.

    Returns dict like:
    {
        "timestamp": "2026-03-02T21:08:43-05:00",
        "fuels": {
            "Natural Gas": {"mw": 8634, "pct": 51.2, "marginal": True},
            "Nuclear":     {"mw": 3364, "pct": 19.9, "marginal": False},
            ...
        },
        "total_mw": 16860,
        "gas_pct": 51.2,
        "renewables_pct": 6.8,
        "gas_above_threshold": True
    }
    """
    data = _get("/genfuelmix/current.json")
    if not data:
        return {}

    mixes = data.get("GenFuelMixes", {}).get("GenFuelMix", [])
    if not mixes:
        # Sometimes the API returns a single object instead of a list
        single = data.get("GenFuelMixes", {})
        if "BeginDate" in single:
            mixes = [single]

    # Aggregate by FuelCategoryRollup (groups sub-renewables together)
    rollup = {}
    timestamp = None
    for entry in mixes:
        ts = entry.get("BeginDate", "")
        if ts:
            timestamp = ts
        cat = entry.get("FuelCategoryRollup", entry.get("FuelCategory", "Unknown"))
        mw = entry.get("GenMw", 0)
        marginal = entry.get("MarginalFlag", "N") == "Y"
        fuel_detail = entry.get("FuelCategory", cat)

        if cat not in rollup:
            rollup[cat] = {"mw": 0, "marginal": False, "subcategories": {}}
        rollup[cat]["mw"] += mw
        if marginal:
            rollup[cat]["marginal"] = True
        rollup[cat]["subcategories"][fuel_detail] = mw

    total_mw = sum(v["mw"] for v in rollup.values())

    # Calculate percentages
    fuels = {}
    for cat, info in rollup.items():
        pct = (info["mw"] / total_mw * 100) if total_mw > 0 else 0
        fuels[cat] = {
            "mw": info["mw"],
            "pct": round(pct, 1),
            "marginal": info["marginal"],
            "subcategories": info["subcategories"],
        }

    gas_pct = fuels.get("Natural Gas", {}).get("pct", 0)
    renewables_pct = fuels.get("Renewables", {}).get("pct", 0)

    return {
        "timestamp": timestamp,
        "fuels": fuels,
        "total_mw": total_mw,
        "gas_pct": gas_pct,
        "renewables_pct": renewables_pct,
        "gas_above_threshold": gas_pct > GAS_THRESHOLD_PCT,
    }


def fetch_maine_lmp() -> dict:
    """
    Fetch 5-minute real-time LMP for the Maine load zone.

    Returns dict like:
    {
        "timestamp": "2026-03-02T21:15:00-05:00",
        "lmp_total": 111.4,
        "energy_component": 114.53,
        "congestion_component": 0,
        "loss_component": -3.13,
        "price_above_threshold": False
    }
    """
    data = _get(f"/fiveminutelmp/current/location/{MAINE_LOCATION_ID}.json")
    if not data:
        return {}

    # Handle both single-object and list responses
    lmp = data.get("FiveMinLmp")
    if not lmp:
        lmps = data.get("FiveMinLmps", {}).get("FiveMinLmp", [])
        lmp = lmps[-1] if isinstance(lmps, list) and lmps else lmps

    if not lmp:
        return {}

    price = lmp.get("LmpTotal", 0)
    return {
        "timestamp": lmp.get("BeginDate", ""),
        "lmp_total": price,
        "energy_component": lmp.get("EnergyComponent", 0),
        "congestion_component": lmp.get("CongestionComponent", 0),
        "loss_component": lmp.get("LossComponent", 0),
        "price_above_threshold": price > PRICE_THRESHOLD_MWH,
    }


def fetch_system_load() -> dict:
    """
    Fetch 5-minute system load for all of New England.

    Returns dict like:
    {
        "timestamp": "2026-03-02T21:10:00-05:00",
        "load_mw": 16746.85,
        "native_load_mw": 16723.95
    }
    """
    data = _get("/fiveminutesystemload/current.json")
    if not data:
        return {}

    # Can be a list or single object
    loads = data.get("FiveMinSystemLoad", [])
    if isinstance(loads, list) and loads:
        latest = loads[-1]
    elif isinstance(loads, dict):
        latest = loads
    else:
        return {}

    return {
        "timestamp": latest.get("BeginDate", ""),
        "load_mw": latest.get("LoadMw", 0),
        "native_load_mw": latest.get("NativeLoad", 0),
    }


# ---------------------------------------------------------------------------
# Combined snapshot — this is what the Logic Engine will call
# ---------------------------------------------------------------------------

def fetch_grid_forecast() -> dict:
    """
    Fetch ISO-NE 7-Day Capacity Forecast — includes peak load, imports,
    available generation, surplus/deficit, and Power Watch/Warn status.

    This tells us:
      - How much power is being IMPORTED (e.g., from Québec, NY)
      - Today's projected PEAK demand
      - How much SURPLUS capacity we have (or if we're in deficit)
      - Whether ISO-NE has issued any grid alerts

    Returns dict like:
    {
        "today": {
            "date": "2026-03-04",
            "peak_load_mw": 15600,
            "peak_import_mw": 4170,
            "total_available_gen_mw": 26191,
            "total_gen_plus_imports_mw": 30361,
            "surplus_mw": 12276,
            "reserve_required_mw": 2305,
            "outages_mw": 2652,
            "power_watch": False,
            "power_warn": False,
            "cold_weather_watch": False,
            "cold_weather_warn": False,
            "cold_weather_event": False,
            "weather": { "Boston": {"high_f": 46, "dew_f": 31}, ... }
        },
        "week": [ ... ]   # remaining forecast days
    }
    """
    data = _get("/sevendayforecast/current.json")
    if not data:
        return {}

    forecasts = data.get("SevenDayForecasts", {}).get("SevenDayForecast", [])
    if not forecasts:
        return {}

    days_raw = forecasts[0].get("MarketDay", [])
    if not days_raw:
        return {}

    def _parse_day(d: dict) -> dict:
        """Parse a single forecast day."""
        # Weather
        weather = {}
        weather_data = d.get("Weather", {}).get("CityWeather", [])
        for cw in weather_data:
            city = cw.get("CityName", "Unknown")
            weather[city] = {
                "high_f": cw.get("HighTempF"),
                "dew_f": cw.get("DewPointF"),
            }

        return {
            "date": d.get("MarketDate", ""),
            "peak_load_mw": d.get("PeakLoadMw", 0),
            "peak_import_mw": d.get("PeakImportMw", 0),
            "total_available_gen_mw": d.get("TotAvailGenMw", 0),
            "total_gen_plus_imports_mw": d.get("TotAvailGenImportMw", 0),
            "surplus_mw": d.get("SurplusDeficiencyMw", 0),
            "reserve_required_mw": d.get("ReqdReserveMw", 0),
            "outages_mw": d.get("OtherGenOutagesMw", 0),
            "power_watch": d.get("PowerWatch", "N") == "Y",
            "power_warn": d.get("PowerWarn", "N") == "Y",
            "cold_weather_watch": d.get("ColdWeatherWatch", "N") == "Y",
            "cold_weather_warn": d.get("ColdWeatherWarn", "N") == "Y",
            "cold_weather_event": d.get("ColdWeatherEvent", "N") == "Y",
            "weather": weather,
        }

    parsed_days = [_parse_day(d) for d in days_raw]

    return {
        "today": parsed_days[0] if parsed_days else {},
        "week": parsed_days,
    }


def fetch_hourly_load_forecast() -> dict:
    """
    Fetch the ISO-NE hourly load forecast for current/next day.

    Returns dict like:
    {
        "forecast_mw": 12560,
        "net_load_mw": 12560,
        "timestamp": "..."
    }
    """
    data = _get("/hourlyloadforecast/current.json")
    if not data:
        return {}

    entry = data.get("HourlyLoadForecast")
    if isinstance(entry, list) and entry:
        entry = entry[-1]
    elif isinstance(entry, dict):
        pass
    else:
        return {}

    return {
        "forecast_mw": entry.get("LoadMw", 0),
        "net_load_mw": entry.get("NetLoadMw", 0),
        "timestamp": entry.get("BeginDate", ""),
    }


def fetch_maine_snapshot() -> dict:
    """
    Pull all Maine / ISO-NE data into one clean snapshot.

    This is the single function the Logic Engine and Dashboard import.

    Returns:
    {
        "state": "maine",
        "fetched_at": "2026-03-02T21:15:00Z",
        "fuel_mix": { ... },
        "lmp": { ... },
        "system_load": { ... },
        "grid_forecast": { "today": { peak_load_mw, peak_import_mw, surplus_mw, ... }, "week": [...] },
        "hourly_forecast": { forecast_mw, net_load_mw },
        "green_mode_triggered": True/False,
        "trigger_reasons": ["gas_above_50pct", "price_above_150"]
    }
    """
    fuel_mix = fetch_fuel_mix()
    lmp = fetch_maine_lmp()
    system_load = fetch_system_load()
    grid_forecast = fetch_grid_forecast()
    hourly_forecast = fetch_hourly_load_forecast()

    # Determine if Green Mode should activate
    trigger_reasons = []
    if fuel_mix.get("gas_above_threshold"):
        trigger_reasons.append(f"gas_at_{fuel_mix.get('gas_pct', 0)}pct_above_{GAS_THRESHOLD_PCT}pct")
    if lmp.get("price_above_threshold"):
        trigger_reasons.append(f"price_at_${lmp.get('lmp_total', 0)}_above_${PRICE_THRESHOLD_MWH}")

    green_mode = len(trigger_reasons) > 0

    snapshot = {
        "state": "maine",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "fuel_mix": fuel_mix,
        "lmp": lmp,
        "system_load": system_load,
        "grid_forecast": grid_forecast,
        "hourly_forecast": hourly_forecast,
        "green_mode_triggered": green_mode,
        "trigger_reasons": trigger_reasons,
    }

    return snapshot


# ---------------------------------------------------------------------------
# Pretty-print for terminal monitoring
# ---------------------------------------------------------------------------

def print_snapshot(snap: dict):
    """Print a human-readable summary of the grid snapshot to the terminal."""
    ts = snap.get("fetched_at", "N/A")
    fm = snap.get("fuel_mix", {})
    lmp = snap.get("lmp", {})
    load = snap.get("system_load", {})
    gf = snap.get("grid_forecast", {})
    hf = snap.get("hourly_forecast", {})
    green = snap.get("green_mode_triggered", False)
    reasons = snap.get("trigger_reasons", [])

    print("\n" + "=" * 65)
    print(f"  🏔️  MAINE / ISO-NE GRID SNAPSHOT")
    print(f"  Fetched: {ts}")
    print("=" * 65)

    # Fuel Mix
    print(f"\n  ⛽ FUEL MIX  (Total: {fm.get('total_mw', 0):,.0f} MW)")
    print(f"  {'─' * 50}")
    for cat, info in sorted(fm.get("fuels", {}).items(), key=lambda x: -x[1]["mw"]):
        bar_len = int(info["pct"] / 2)
        bar = "█" * bar_len
        marginal_tag = " ← MARGINAL" if info.get("marginal") else ""
        print(f"    {cat:<16} {info['mw']:>6,} MW  ({info['pct']:>5.1f}%)  {bar}{marginal_tag}")

    gas_pct = fm.get("gas_pct", 0)
    print(f"\n    🔥 Natural Gas: {gas_pct:.1f}%  (threshold: {GAS_THRESHOLD_PCT}%)")
    if fm.get("gas_above_threshold"):
        print(f"    🔴 GAS ABOVE THRESHOLD — Green Mode trigger active")
    else:
        print(f"    🟢 Gas below threshold ({GAS_THRESHOLD_PCT - gas_pct:.1f}% away)")

    # Price
    price = lmp.get("lmp_total", 0)
    print(f"\n  💰 MAINE LMP: ${price:.2f}/MWh  (threshold: ${PRICE_THRESHOLD_MWH})")
    print(f"     Energy: ${lmp.get('energy_component', 0):.2f}  "
          f"Congestion: ${lmp.get('congestion_component', 0):.2f}  "
          f"Loss: ${lmp.get('loss_component', 0):.2f}")
    if lmp.get("price_above_threshold"):
        print(f"    🔴 PRICE ABOVE THRESHOLD — Green Mode trigger active")
    else:
        print(f"    🟢 Price below threshold (${PRICE_THRESHOLD_MWH - price:.2f} away)")

    # System Load
    print(f"\n  ⚡ SYSTEM LOAD: {load.get('load_mw', 0):,.1f} MW")

    # Grid Forecast — Imports, Peak, Reserves
    today = gf.get("today", {})
    if today:
        print(f"\n  📊 GRID FORECAST (Today)")
        print(f"  {'─' * 50}")
        peak = today.get("peak_load_mw", 0)
        imports = today.get("peak_import_mw", 0)
        avail_gen = today.get("total_available_gen_mw", 0)
        surplus = today.get("surplus_mw", 0)
        outages = today.get("outages_mw", 0)

        current_mw = load.get("load_mw", 0)
        pct_of_peak = (current_mw / peak * 100) if peak > 0 else 0

        print(f"    📈 Peak Demand Forecast: {peak:,.0f} MW")
        print(f"    📍 Current vs Peak: {current_mw:,.0f} / {peak:,.0f} MW ({pct_of_peak:.0f}%)")
        print(f"    🔌 Peak Imports (Québec/NY): {imports:,.0f} MW")
        print(f"    🏭 Available Generation: {avail_gen:,.0f} MW")
        print(f"    ⚠️  Gen Outages: {outages:,.0f} MW offline")
        print(f"    {'🟢' if surplus > 0 else '🔴'} Surplus Capacity: {surplus:+,.0f} MW")

        # ISO-NE alerts
        alerts = []
        if today.get("power_watch"):
            alerts.append("⚠️  POWER WATCH")
        if today.get("power_warn"):
            alerts.append("🔴 POWER WARNING")
        if today.get("cold_weather_event"):
            alerts.append("❄️  COLD WEATHER EVENT")
        elif today.get("cold_weather_warn"):
            alerts.append("❄️  Cold Weather Warning")
        elif today.get("cold_weather_watch"):
            alerts.append("❄️  Cold Weather Watch")
        if alerts:
            print(f"    🚨 ALERTS: {' | '.join(alerts)}")
        else:
            print(f"    🟢 No grid alerts active")

        # Weather
        weather = today.get("weather", {})
        if weather:
            temps = ", ".join(f"{c}: {w.get('high_f', '?')}°F" for c, w in weather.items())
            print(f"    🌡️  Weather: {temps}")

    # Hourly forecast
    if hf.get("forecast_mw"):
        print(f"\n  📅 Hourly Load Forecast: {hf['forecast_mw']:,.0f} MW")

    # Green Mode Status
    print(f"\n  {'─' * 50}")
    if green:
        print(f"  🔴 GREEN MODE: TRIGGERED")
        print(f"     Action: Reduce data center load by 25%")
        for r in reasons:
            print(f"       → {r}")
    else:
        print(f"  🟢 GREEN MODE: INACTIVE — Grid conditions normal")

    print("=" * 65)


# ---------------------------------------------------------------------------
# Main loop — runs standalone for terminal monitoring
# ---------------------------------------------------------------------------

def main():
    """Poll ISO-NE every 60 seconds and print to terminal."""
    if not ISONE_USERNAME or not ISONE_PASSWORD:
        print("❌ ERROR: Set ISONE_USERNAME and ISONE_PASSWORD in .env")
        return

    print("🏔️  AI Grid Orchestrator — Maine Data Ingestion")
    print(f"   Polling ISO-NE every {POLL_INTERVAL_SECONDS} seconds...")
    print(f"   Green Mode triggers:")
    print(f"     • Gas > {GAS_THRESHOLD_PCT}%")
    print(f"     • Price > ${PRICE_THRESHOLD_MWH}/MWh")
    print(f"   Press Ctrl+C to stop.\n")

    cycle = 0
    while True:
        cycle += 1
        log.info(f"Cycle {cycle} — fetching data...")
        try:
            snapshot = fetch_maine_snapshot()
            print_snapshot(snapshot)
            log.info(
                f"Gas={snapshot['fuel_mix'].get('gas_pct', '?')}% | "
                f"Price=${snapshot['lmp'].get('lmp_total', '?')}/MWh | "
                f"Load={snapshot['system_load'].get('load_mw', '?')}MW | "
                f"GreenMode={'ON' if snapshot['green_mode_triggered'] else 'OFF'}"
            )
        except Exception as e:
            log.error(f"Cycle {cycle} failed: {e}")

        log.info(f"Next refresh in {POLL_INTERVAL_SECONDS}s...\n")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Maine ingestion stopped.")
