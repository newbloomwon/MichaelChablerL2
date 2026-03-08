"""
ISO-NE API Connection Test
===========================
Tests your ISO Express credentials against the live API.
Replace YOUR_EMAIL and YOUR_PASSWORD with your ISO Express login.

Usage:
    python test_isone_api.py
"""

import os
import requests
import json
from datetime import datetime

# ============================================================
# Credentials loaded from .env file (never committed to git)
# ============================================================
from dotenv import load_dotenv
load_dotenv()

USERNAME = os.getenv("ISONE_USERNAME")
PASSWORD = os.getenv("ISONE_PASSWORD")
# ============================================================

BASE_URL = "https://webservices.iso-ne.com/api/v1.1"

ENDPOINTS = {
    "Fuel Mix (Green Mode Trigger #1)": "/genfuelmix/current.json",
    "5-Min LMP Maine (Green Mode Trigger #2)": "/fiveminutelmp/current/location/4001.json",
    "System Load": "/fiveminutesystemload/current.json",
    "Power System Status": "/powersystem/status.json",
}


def test_connection():
    print("=" * 60)
    print("ISO-NE API Connection Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not USERNAME or not PASSWORD:
        print("\n⚠️  ERROR: Credentials not found in .env file!")
        print("   Make sure .env exists with:")
        print("   ISONE_USERNAME=your_email")
        print("   ISONE_PASSWORD=your_password")
        return

    for name, endpoint in ENDPOINTS.items():
        url = BASE_URL + endpoint
        print(f"\n--- {name} ---")
        print(f"    URL: {url}")

        try:
            resp = requests.get(url, auth=(USERNAME, PASSWORD), timeout=15)
            print(f"    Status: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                print(f"    ✅ SUCCESS — Data received!")
                # Print a readable summary depending on the endpoint
                parse_response(name, data)

            elif resp.status_code == 401:
                print(f"    ❌ UNAUTHORIZED — Check your email/password")
                print(f"       Make sure you use your ISO Express login credentials")

            elif resp.status_code == 403:
                print(f"    ❌ FORBIDDEN — Account may not have API access yet")
                print(f"       Try logging into https://www.iso-ne.com/isoexpress first")

            else:
                print(f"    ⚠️  Unexpected status: {resp.status_code}")
                print(f"    Response: {resp.text[:200]}")

        except requests.exceptions.ConnectionError:
            print(f"    ❌ CONNECTION ERROR — Can't reach the server")
        except requests.exceptions.Timeout:
            print(f"    ❌ TIMEOUT — Server took too long to respond")
        except Exception as e:
            print(f"    ❌ ERROR: {e}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


def parse_response(name, data):
    """Pretty-print the key values from each API response."""
    try:
        if "Fuel Mix" in name:
            mixes = data.get("GenFuelMixes", {}).get("GenFuelMix", [])
            if mixes:
                # Get the most recent entry
                latest = mixes[-1] if isinstance(mixes, list) else mixes
                print(f"    📊 Fuel Mix Breakdown:")
                # The response contains MW by fuel category
                if isinstance(mixes, list):
                    for mix in mixes[-6:]:  # last few entries
                        cat = mix.get("FuelCategory", "Unknown")
                        mw = mix.get("GenMw", 0)
                        print(f"       {cat}: {mw} MW")

        elif "LMP" in name:
            lmps = data.get("FiveMinLmps", {}).get("FiveMinLmp", [])
            if lmps:
                latest = lmps[-1] if isinstance(lmps, list) else lmps
                price = latest.get("LmpTotal", "N/A")
                ts = latest.get("BeginDate", "N/A")
                print(f"    💰 Maine LMP: ${price}/MWh")
                print(f"       Timestamp: {ts}")
                # Check against your trigger
                try:
                    price_val = float(price)
                    if price_val > 150:
                        print(f"    🔴 ABOVE $150 TRIGGER — Green Mode would activate!")
                    else:
                        print(f"    🟢 Below $150 trigger (${150 - price_val:.2f} away)")
                except (ValueError, TypeError):
                    pass

        elif "System Load" in name:
            loads = data.get("FiveMinSystemLoads", {}).get("FiveMinSystemLoad", [])
            if loads:
                latest = loads[-1] if isinstance(loads, list) else loads
                load_mw = latest.get("LoadMw", "N/A")
                print(f"    ⚡ System Load: {load_mw} MW")

        elif "Power System" in name:
            print(f"    🔋 Power System Status retrieved")
            # Just show the raw data structure keys
            for key in list(data.keys())[:5]:
                print(f"       Key: {key}")

    except Exception as e:
        print(f"    (Could not parse details: {e})")
        # Still show raw data preview
        raw = json.dumps(data, indent=2)
        print(f"    Raw preview: {raw[:300]}...")


if __name__ == "__main__":
    test_connection()
