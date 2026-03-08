"""
panels/maine.py — Maine (ISO-NE) Dashboard Panel
===================================================
Gary's module. Renders all Maine-specific content.
Ibrahima: you don't need to touch this file.
"""

import streamlit as st
from datetime import datetime

from maine_ingestion import (
    fetch_maine_snapshot,
    GAS_THRESHOLD_PCT,
    PRICE_THRESHOLD_MWH,
)
from panels.shared import render_metric_card, render_fuel_bar, render_data_center_mock


# Fuel colors
FUEL_COLORS = {
    "Natural Gas": "#ef4444",
    "Nuclear": "#8b5cf6",
    "Hydro": "#3b82f6",
    "Renewables": "#22c55e",
    "Coal": "#6b7280",
    "Other": "#a1a1aa",
}


def get_sidebar_info() -> dict:
    """Return sidebar content specific to Maine's Green Mode rules."""
    return {
        "thresholds_title": "Green Mode Thresholds",
        "rules": [
            f"Gas > **{GAS_THRESHOLD_PCT}%** of fuel mix",
            f"Price > **${PRICE_THRESHOLD_MWH:.0f}**/MWh",
            "Action: **Reduce load 25%**",
        ],
    }


def render():
    """Main render function — called by dashboard.py when Maine is selected."""

    # Fetch live data
    with st.spinner("Fetching live ISO-NE data..."):
        snap = fetch_maine_snapshot()

    if not snap or not snap.get("fuel_mix"):
        st.error("❌ Could not fetch data from ISO-NE. Check your .env credentials.")
        st.stop()

    fm = snap["fuel_mix"]
    lmp = snap["lmp"]
    load = snap["system_load"]
    gf = snap.get("grid_forecast", {})
    hf = snap.get("hourly_forecast", {})
    green_mode = snap["green_mode_triggered"]
    reasons = snap["trigger_reasons"]
    today = gf.get("today", {})

    # ── Green Mode Banner ──
    if green_mode:
        reason_text = " | ".join(reasons)
        st.markdown(
            f'<div class="green-mode-on">'
            f'🔴 GREEN MODE ACTIVE — Load reduced 25% — {reason_text}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="green-mode-off">'
            '🟢 GRID NORMAL — No throttling needed'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Header with flag ──
    col_title, col_img = st.columns([8, 1])
    with col_title:
        st.markdown("## Maine Grid — ISO New England")
    with col_img:
        st.image("assets/maine_flag.png", width=60)
    ts = snap.get("fetched_at", "")
    if ts:
        try:
            dt = datetime.fromisoformat(ts)
            st.caption(f"Last updated: {dt.strftime('%B %d, %Y at %I:%M:%S %p UTC')}")
        except Exception:
            st.caption(f"Last updated: {ts}")

    # ── Key Metrics ──
    col1, col2, col3, col4 = st.columns(4)

    gas_pct = fm.get("gas_pct", 0)
    price = lmp.get("lmp_total", 0)
    current_load = load.get("load_mw", 0)
    peak_load = today.get("peak_load_mw", 0)
    pct_of_peak = (current_load / peak_load * 100) if peak_load > 0 else 0

    with col1:
        gas_status = "🔴 ABOVE" if fm.get("gas_above_threshold") else "🟢 Below"
        render_metric_card(
            f"{gas_pct:.1f}%",
            "Natural Gas Share",
            f"{gas_status} {GAS_THRESHOLD_PCT}% threshold",
        )
    with col2:
        price_status = "🔴 ABOVE" if lmp.get("price_above_threshold") else "🟢 Below"
        render_metric_card(
            f"${price:.2f}",
            "Maine LMP ($/MWh)",
            f"{price_status} ${PRICE_THRESHOLD_MWH:.0f} threshold",
        )
    with col3:
        if peak_load > 0:
            render_metric_card(
                f"{current_load:,.0f}",
                "System Load (MW)",
                f"{pct_of_peak:.0f}% of today's {peak_load:,.0f} MW peak",
            )
        else:
            render_metric_card(
                f"{current_load:,.0f}",
                "System Load (MW)",
                "New England total demand",
            )
    with col4:
        render_metric_card(
            f"{fm.get('total_mw', 0):,.0f}",
            "Total Generation (MW)",
            "All fuel sources combined",
        )

    st.markdown("")

    # ── Two-column: Fuel Mix + Price Detail ──
    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.markdown("### ⛽ Generation Fuel Mix")
        fuels = fm.get("fuels", {})
        sorted_fuels = sorted(fuels.items(), key=lambda x: -x[1]["mw"])
        for fuel_name, fuel_info in sorted_fuels:
            color = FUEL_COLORS.get(fuel_name, "#64748b")
            render_fuel_bar(
                fuel_name,
                fuel_info["pct"],
                fuel_info["mw"],
                color,
                fuel_info.get("marginal", False),
            )

        renew = fuels.get("Renewables", {})
        subs = renew.get("subcategories", {})
        if subs:
            with st.expander("🌿 Renewables Breakdown"):
                for sub_name, sub_mw in sorted(subs.items(), key=lambda x: -x[1]):
                    st.markdown(f"- **{sub_name}**: {sub_mw:,} MW")

    with right_col:
        st.markdown("### 💰 Price Components")
        energy = lmp.get("energy_component", 0)
        congestion = lmp.get("congestion_component", 0)
        loss = lmp.get("loss_component", 0)

        price_color = '#ef4444' if lmp.get('price_above_threshold') else '#22c55e'
        lmp_html = (
            '<div class="metric-card" style="text-align:left;">'
            '<div style="font-size:0.9rem;margin-bottom:0.8rem;"><strong>LMP Breakdown for Maine (.Z.MAINE)</strong></div>'
            '<div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #334155;">'
            f'<span>⚡ Energy</span><span style="font-weight:700;">${energy:.2f}</span></div>'
            '<div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #334155;">'
            f'<span>🚧 Congestion</span><span style="font-weight:700;">${congestion:.2f}</span></div>'
            '<div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #334155;">'
            f'<span>📉 Loss</span><span style="font-weight:700;">${loss:.2f}</span></div>'
            '<div style="display:flex;justify-content:space-between;padding:0.6rem 0 0.2rem;font-size:1.1rem;">'
            f'<span style="font-weight:700;">Total LMP</span>'
            f'<span style="font-weight:800;color:{price_color};">${price:.2f}/MWh</span></div>'
            '</div>'
        )
        st.markdown(lmp_html, unsafe_allow_html=True)

        st.markdown("")
        st.markdown("### 🎯 Green Mode Rules")
        gas_icon = "🔴" if fm.get("gas_above_threshold") else "⚪"
        price_icon = "🔴" if lmp.get("price_above_threshold") else "⚪"
        rules_html = (
            '<div class="metric-card" style="text-align:left;font-size:0.9rem;">'
            f'<div style="padding:0.3rem 0;">{gas_icon} Gas &gt; {GAS_THRESHOLD_PCT}% → '
            f'currently <strong>{gas_pct:.1f}%</strong></div>'
            f'<div style="padding:0.3rem 0;">{price_icon} Price &gt; ${PRICE_THRESHOLD_MWH:.0f} → '
            f'currently <strong>${price:.2f}</strong></div>'
            '<div style="padding:0.5rem 0 0.2rem;border-top:1px solid #334155;margin-top:0.3rem;">'
            'Either trigger = <strong>Reduce data center load 25%</strong></div>'
            '</div>'
        )
        st.markdown(rules_html, unsafe_allow_html=True)

    # ── Data Center Response ──
    st.markdown("---")

    # ── Imports, Peak Demand & Grid Capacity (NEW) ──
    if today:
        st.markdown("### 🔌 Grid Capacity, Imports & Peak Demand")

        cap_left, cap_right = st.columns([3, 2])

        with cap_left:
            peak = today.get("peak_load_mw", 0)
            imports = today.get("peak_import_mw", 0)
            avail_gen = today.get("total_available_gen_mw", 0)
            gen_plus_imports = today.get("total_gen_plus_imports_mw", 0)
            surplus = today.get("surplus_mw", 0)
            outages = today.get("outages_mw", 0)
            reserve = today.get("reserve_required_mw", 0)

            # Current vs Peak bar
            load_bar_pct = min(100, pct_of_peak) if peak > 0 else 0
            load_bar_color = "#22c55e" if load_bar_pct < 80 else "#f59e0b" if load_bar_pct < 95 else "#ef4444"
            peak_status = "🟢 Well below peak" if pct_of_peak < 80 else "🟡 Approaching peak demand" if pct_of_peak < 95 else "🔴 At or above peak — grid under stress"

            peak_bar_html = (
                '<div class="metric-card" style="text-align:left;">'
                '<div style="font-size:1rem;font-weight:700;margin-bottom:0.6rem;">📈 Current Load vs Today\'s Forecasted Peak</div>'
                '<div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:0.3rem;">'
                f'<span>0 MW</span><span>{peak:,.0f} MW (Peak)</span></div>'
                '<div style="background:#334155;border-radius:8px;height:32px;overflow:hidden;">'
                f'<div style="width:{load_bar_pct:.1f}%;height:100%;background:{load_bar_color};border-radius:8px;'
                'display:flex;align-items:center;justify-content:center;'
                f'font-weight:700;font-size:0.85rem;color:white;min-width:100px;">'
                f'{current_load:,.0f} MW ({pct_of_peak:.0f}%)</div></div>'
                f'<div style="font-size:0.8rem;color:#94a3b8;margin-top:0.4rem;">{peak_status}</div>'
                '</div>'
            )
            st.markdown(peak_bar_html, unsafe_allow_html=True)

            st.markdown("")

            # Capacity breakdown table
            rows = [
                ("🏭 Local Generation Available", f"{avail_gen:,.0f} MW"),
                ("🔌 Peak Imports (Québec / NY)", f"{imports:,.0f} MW"),
                ("📊 Total Capacity (Gen + Imports)", f"{gen_plus_imports:,.0f} MW"),
                ("📈 Today's Peak Demand Forecast", f"{peak:,.0f} MW"),
                ("🔒 Required Reserves", f"{reserve:,.0f} MW"),
                ("⚠️ Generation Outages", f"{outages:,.0f} MW offline"),
                ("{'🟢' if surplus > 0 else '🔴'} Surplus / Deficiency", f"{surplus:+,.0f} MW"),
            ]
            rows_html = ""
            for label, value in rows:
                rows_html += (
                    '<div style="display:flex;justify-content:space-between;padding:0.45rem 0;'
                    'border-bottom:1px solid #334155;">'
                    f'<span>{label}</span><span style="font-weight:700;">{value}</span></div>'
                )
            cap_table_html = (
                '<div class="metric-card" style="text-align:left;">'
                '<div style="font-size:0.9rem;font-weight:700;margin-bottom:0.5rem;">Grid Capacity Breakdown (ISO-NE 7-Day Forecast)</div>'
                f'{rows_html}</div>'
            )
            st.markdown(cap_table_html, unsafe_allow_html=True)

        with cap_right:
            # Import highlight card
            import_pct = (imports / gen_plus_imports * 100) if gen_plus_imports > 0 else 0
            import_html = (
                '<div class="metric-card" style="text-align:center;">'
                '<div style="font-size:0.8rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;">Power Imports</div>'
                f'<div style="font-size:2.5rem;font-weight:800;color:#3b82f6;line-height:1.1;margin:0.3rem 0;">{imports:,.0f}</div>'
                '<div style="font-size:0.85rem;color:#94a3b8;">MW from Québec &amp; New York</div>'
                f'<div style="font-size:0.75rem;color:#64748b;margin-top:0.4rem;">{import_pct:.1f}% of total capacity</div>'
                '</div>'
            )
            st.markdown(import_html, unsafe_allow_html=True)

            st.markdown("")

            # ISO-NE Grid Alerts
            alerts = []
            if today.get("power_warn"):
                alerts.append(("🔴 POWER WARNING", "#ef4444"))
            if today.get("power_watch"):
                alerts.append(("⚠️ Power Watch", "#f59e0b"))
            if today.get("cold_weather_event"):
                alerts.append(("❄️ Cold Weather EVENT", "#ef4444"))
            if today.get("cold_weather_warn"):
                alerts.append(("❄️ Cold Weather Warning", "#f59e0b"))
            if today.get("cold_weather_watch"):
                alerts.append(("❄️ Cold Weather Watch", "#94a3b8"))

            if alerts:
                alert_html = ""
                for text, color in alerts:
                    alert_html += f'<div style="padding:0.3rem 0;color:{color};font-weight:600;">{text}</div>'
                alerts_card = (
                    '<div class="metric-card" style="text-align:left;">'
                    '<div style="font-size:0.9rem;font-weight:700;margin-bottom:0.3rem;">🚨 ISO-NE Alerts</div>'
                    f'{alert_html}</div>'
                )
                st.markdown(alerts_card, unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="metric-card" style="text-align:center;">'
                    '<div style="font-size:0.9rem;font-weight:700;margin-bottom:0.3rem;">🚨 ISO-NE Alerts</div>'
                    '<div style="color:#22c55e;font-weight:600;">🟢 No alerts active</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("")

            # Weather
            weather = today.get("weather", {})
            if weather:
                weather_rows = ""
                for city, w in weather.items():
                    high = w.get("high_f", "?")
                    dew = w.get("dew_f", "?")
                    weather_rows += (
                        '<div style="display:flex;justify-content:space-between;padding:0.3rem 0;'
                        'border-bottom:1px solid #334155;">'
                        f'<span>🌡️ {city}</span>'
                        f'<span style="font-weight:600;">{high}°F (dew: {dew}°F)</span></div>'
                    )
                weather_html = (
                    '<div class="metric-card" style="text-align:left;">'
                    '<div style="font-size:0.9rem;font-weight:700;margin-bottom:0.3rem;">Weather (Drives Demand)</div>'
                    f'{weather_rows}</div>'
                )
                st.markdown(weather_html, unsafe_allow_html=True)

        # Week-ahead mini table
        week = gf.get("week", [])
        if len(week) > 1:
            with st.expander(f"📅 Week-Ahead Forecast ({len(week)} days)"):
                for day in week:
                    date_str = day.get("date", "")
                    try:
                        dt = datetime.fromisoformat(date_str)
                        day_label = dt.strftime("%a %b %d")
                    except Exception:
                        day_label = date_str[:10]
                    dp = day.get("peak_load_mw", 0)
                    ds = day.get("surplus_mw", 0)
                    pw = "⚠️" if day.get("power_watch") or day.get("power_warn") else "🟢"
                    st.markdown(
                        f"- **{day_label}**: Peak {dp:,.0f} MW | "
                        f"Surplus {ds:+,.0f} MW | {pw}"
                    )

        st.markdown("---")

    st.markdown("### 🖥️ Data Center Response")
    render_data_center_mock("Maine", green_mode, reduction_pct=25)

    # ── Raw data ──
    st.markdown("---")
    with st.expander("📋 Raw Snapshot Data (for debugging)"):
        st.json(snap)
