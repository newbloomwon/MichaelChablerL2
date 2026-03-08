"""
panels/texas.py — Texas (ERCOT) Dashboard Panel
===================================================
Live ERCOT grid monitoring with Reliability Mode detection.

When grid frequency drops below 59.97 Hz (demand overwhelming supply),
Reliability Mode activates and the data center reduces load by 40%.

This is the Texas equivalent of panels/maine.py.
"""

import streamlit as st
from datetime import datetime

from texas_ingestion import (
    fetch_texas_snapshot,
    FREQUENCY_THRESHOLD_HZ,
    RELIABILITY_REDUCTION_PCT,
)
from panels.shared import render_metric_card, render_fuel_bar, render_data_center_mock


def get_sidebar_info() -> dict:
    """Return sidebar content specific to Texas Reliability Mode rules."""
    return {
        "thresholds_title": "Reliability Mode Thresholds",
        "rules": [
            f"Frequency < **{FREQUENCY_THRESHOLD_HZ} Hz**",
            f"Action: **Reduce load {RELIABILITY_REDUCTION_PCT}%**",
            "Protects grid from blackout conditions",
        ],
    }


def render():
    """Main render function — called by dashboard.py when Texas is selected."""

    # Fetch live data
    with st.spinner("Fetching live ERCOT data..."):
        snap = fetch_texas_snapshot()

    if not snap or not snap.get("frequency"):
        st.error("❌ Could not fetch data from ERCOT. Check your .env credentials or network.")
        st.stop()

    freq = snap["frequency"]
    prices = snap["prices"]
    load_forecast = snap["load_forecast"]
    reliability_mode = snap["reliability_mode_triggered"]
    reasons = snap["trigger_reasons"]

    freq_hz = freq.get("frequency_hz")
    current_load = freq.get("current_load_mw")
    total_gen = freq.get("total_gen_mw")
    wind_mw = freq.get("wind_output_mw")

    # ── Reliability Mode Banner ──
    if reliability_mode:
        reason_text = " | ".join(reasons)
        st.markdown(
            f'<div class="reliability-mode-on">'
            f'🔴 RELIABILITY MODE ACTIVE — Grid stressed! Load reduced {RELIABILITY_REDUCTION_PCT}% — {reason_text}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="reliability-mode-off">'
            '🟢 GRID NORMAL — Frequency stable, no throttling needed'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Header ──
    # ── Header with flag ──
    col_title, col_img = st.columns([8, 1])
    with col_title:
        st.markdown("## Texas Grid — ERCOT")
    with col_img:
        st.image("assets/texas_flag.png", width=60)
    ts = snap.get("fetched_at", "")
    if ts:
        try:
            dt = datetime.fromisoformat(ts)
            st.caption(f"Last updated: {dt.strftime('%B %d, %Y at %I:%M:%S %p UTC')}")
        except Exception:
            st.caption(f"Last updated: {ts}")

    # ── Key Metrics (top row) ──
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if freq_hz is not None:
            delta = freq_hz - FREQUENCY_THRESHOLD_HZ
            if freq.get("below_threshold"):
                freq_status = "🔴 BELOW THRESHOLD"
            elif delta < 0.05:
                freq_status = "🟡 Close to threshold"
            else:
                freq_status = "🟢 Normal range"
            render_metric_card(
                f"{freq_hz:.4f} Hz",
                "Grid Frequency",
                f"{freq_status} ({FREQUENCY_THRESHOLD_HZ} Hz limit)",
            )
        else:
            render_metric_card("N/A", "Grid Frequency", "⚠️ Data unavailable")

    with col2:
        avg_price = prices.get("hub_avg_price", 0)
        render_metric_card(
            f"${avg_price:.2f}",
            "Avg Settlement Price",
            f"Across {prices.get('num_nodes', 0)} nodes",
        )

    with col3:
        if current_load is not None:
            render_metric_card(
                f"{current_load:,.0f}",
                "Current Load (MW)",
                "ERCOT system demand",
            )
        else:
            forecast_mw = load_forecast.get("forecast_mw", 0)
            render_metric_card(
                f"{forecast_mw:,.0f}",
                "Load Forecast (MW)",
                "ERCOT projected demand",
            )

    with col4:
        if total_gen is not None:
            render_metric_card(
                f"{total_gen:,.0f}",
                "Total Generation (MW)",
                "All sources combined",
            )
        elif wind_mw is not None:
            render_metric_card(
                f"{wind_mw:,.0f}",
                "Wind Output (MW)",
                "Current wind generation",
            )
        else:
            render_metric_card("—", "Generation Data", "⚠️ Unavailable")

    st.markdown("")

    # ── Two-column layout: Frequency Detail + Prices ──
    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.markdown("### ⚡ Frequency & Grid Health")

        # Frequency gauge visualization
        if freq_hz is not None:
            delta = freq_hz - FREQUENCY_THRESHOLD_HZ
            # Map frequency to a 0-100 bar (59.90 = danger, 60.05 = great)
            bar_pct = max(0, min(100, (freq_hz - 59.90) / (60.05 - 59.90) * 100))

            if freq.get("below_threshold"):
                bar_color = "#ef4444"  # red
                status_emoji = "🔴"
                status_text = "DANGER — Grid frequency below safe threshold"
            elif delta < 0.03:
                bar_color = "#f59e0b"  # amber
                status_emoji = "🟡"
                status_text = "WARNING — Frequency approaching threshold"
            else:
                bar_color = "#22c55e"  # green
                status_emoji = "🟢"
                status_text = "HEALTHY — Grid frequency within normal range"

            freq_gauge_html = (
                '<div class="metric-card" style="text-align:left;">'
                '<div style="font-size:1rem;font-weight:700;margin-bottom:0.6rem;">'
                f'{status_emoji} {status_text}</div>'
                '<div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:0.3rem;">'
                '<span>59.90 Hz (Blackout Risk)</span><span>60.05 Hz (Ideal)</span></div>'
                '<div style="background:#334155;border-radius:8px;height:32px;overflow:hidden;position:relative;">'
                f'<div style="width:{bar_pct:.1f}%;height:100%;background:{bar_color};border-radius:8px;'
                'display:flex;align-items:center;justify-content:center;'
                f'font-weight:700;font-size:0.85rem;color:white;min-width:80px;">'
                f'{freq_hz:.4f} Hz</div></div>'
                '<div style="display:flex;justify-content:space-between;margin-top:0.5rem;font-size:0.8rem;color:#94a3b8;">'
                f'<span>Threshold: {FREQUENCY_THRESHOLD_HZ} Hz</span>'
                f'<span>Delta: {delta:+.4f} Hz</span></div>'
                '</div>'
            )
            st.markdown(freq_gauge_html, unsafe_allow_html=True)

        st.markdown("")

        # System conditions from HTML scraper
        conditions_data = []
        if current_load is not None:
            conditions_data.append(("⚡ Current System Load", f"{current_load:,.0f} MW"))
        if total_gen is not None:
            conditions_data.append(("🏭 Total Generation Capacity", f"{total_gen:,.0f} MW"))
        if current_load is not None and total_gen is not None and total_gen > 0:
            reserve_mw = total_gen - current_load
            reserve_pct = (reserve_mw / total_gen * 100)
            reserve_status = "🟢" if reserve_pct > 20 else "🟡" if reserve_pct > 10 else "🔴"
            conditions_data.append((f"{reserve_status} Reserve Margin", f"{reserve_mw:,.0f} MW ({reserve_pct:.1f}%)"))
        if wind_mw is not None:
            wind_pct = (wind_mw / current_load * 100) if current_load and current_load > 0 else 0
            conditions_data.append(("💨 Wind Output", f"{wind_mw:,.0f} MW ({wind_pct:.0f}% of load)"))

        if conditions_data:
            st.markdown("### 📋 System Conditions")

            # Load vs Capacity visual bar
            if current_load is not None and total_gen is not None and total_gen > 0:
                usage_pct = (current_load / total_gen * 100)
                bar_color = "#22c55e" if usage_pct < 75 else "#f59e0b" if usage_pct < 90 else "#ef4444"
                reserve_label = "🟢 Healthy reserves" if usage_pct < 75 else "🟡 Reserves tightening" if usage_pct < 90 else "🔴 Critical — blackout risk"
                cap_bar_html = (
                    '<div class="metric-card" style="text-align:left;margin-bottom:0.8rem;">'
                    '<div style="font-size:0.9rem;font-weight:700;margin-bottom:0.5rem;">Load vs Generation Capacity</div>'
                    '<div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:0.3rem;">'
                    f'<span>0 MW</span><span>{total_gen:,.0f} MW (Max Capacity)</span></div>'
                    '<div style="background:#334155;border-radius:8px;height:28px;overflow:hidden;">'
                    f'<div style="width:{usage_pct:.1f}%;height:100%;background:{bar_color};border-radius:8px;'
                    'display:flex;align-items:center;justify-content:center;'
                    f'font-weight:700;font-size:0.8rem;color:white;min-width:100px;">'
                    f'{current_load:,.0f} MW ({usage_pct:.0f}%)</div></div>'
                    f'<div style="font-size:0.75rem;color:#94a3b8;margin-top:0.3rem;">{reserve_label}</div>'
                    '</div>'
                )
                st.markdown(cap_bar_html, unsafe_allow_html=True)

            # Conditions table rows
            rows_html = ""
            for label, value in conditions_data:
                rows_html += (
                    '<div style="display:flex;justify-content:space-between;padding:0.5rem 0;'
                    'border-bottom:1px solid #334155;">'
                    f'<span>{label}</span>'
                    f'<span style="font-weight:700;">{value}</span>'
                    '</div>'
                )
            table_html = f'<div class="metric-card" style="text-align:left;">{rows_html}</div>'
            st.markdown(table_html, unsafe_allow_html=True)

    with right_col:
        st.markdown("### 💰 Settlement Point Prices")
        avg_price = prices.get("hub_avg_price", 0)
        top_prices = prices.get("prices", [])

        num_nodes = prices.get('num_nodes', 0)
        price_card_html = (
            '<div class="metric-card" style="text-align:left;">'
            '<div style="font-size:0.9rem;margin-bottom:0.8rem;"><strong>ERCOT Real-Time SPP</strong></div>'
            '<div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #334155;">'
            f'<span>📊 Avg Price</span><span style="font-weight:700;">${avg_price:.2f}/MWh</span></div>'
            '<div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #334155;">'
            f'<span>📍 Nodes Sampled</span><span style="font-weight:700;">{num_nodes}</span></div>'
            '</div>'
        )
        st.markdown(price_card_html, unsafe_allow_html=True)

        # Top settlement points
        if top_prices:
            sorted_prices = sorted(top_prices, key=lambda x: -x.get("price", 0))[:8]
            with st.expander(f"🔍 Top {min(8, len(sorted_prices))} Settlement Points"):
                for sp in sorted_prices:
                    node = sp.get("node", "Unknown")
                    price_val = sp.get("price", 0)
                    st.markdown(f"- **{node}**: ${price_val:.2f}/MWh")

        st.markdown("")
        st.markdown("### 🎯 Reliability Mode Rules")
        freq_icon = "🔴" if freq.get("below_threshold") else "⚪"
        freq_display = f"{freq_hz:.4f} Hz" if freq_hz is not None else "N/A"
        rules_html = (
            '<div class="metric-card" style="text-align:left;font-size:0.9rem;">'
            f'<div style="padding:0.3rem 0;">{freq_icon} Frequency &lt; {FREQUENCY_THRESHOLD_HZ} Hz → '
            f'currently <strong>{freq_display}</strong></div>'
            '<div style="padding:0.5rem 0 0.2rem;border-top:1px solid #334155;margin-top:0.3rem;">'
            f'Trigger = <strong>Reduce data center load {RELIABILITY_REDUCTION_PCT}%</strong></div>'
            '<div style="padding:0.3rem 0;font-size:0.8rem;color:#94a3b8;">'
            'Why? Low frequency = demand exceeding supply.<br>'
            'Without intervention → rolling blackouts.</div>'
            '</div>'
        )
        st.markdown(rules_html, unsafe_allow_html=True)

    # ── Data Center Response ──
    st.markdown("---")
    st.markdown("### 🖥️ Data Center Response")
    render_data_center_mock("Texas", reliability_mode, reduction_pct=RELIABILITY_REDUCTION_PCT)

    # ── Raw data ──
    st.markdown("---")
    with st.expander("📋 Raw Snapshot Data (for debugging)"):
        st.json(snap)
