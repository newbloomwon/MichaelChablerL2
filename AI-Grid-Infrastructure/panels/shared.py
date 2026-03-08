"""
panels/shared.py — Shared UI components for all state panels
==============================================================
Reusable rendering functions so Maine and Texas (and any future
state) get a consistent look without duplicating CSS/HTML.
"""

import streamlit as st


# ──────────────────────────────────────────────────────────────
# Shared CSS (injected once by dashboard.py)
# ──────────────────────────────────────────────────────────────
SHARED_CSS = """
<style>
    .main .block-container { padding-top: 1rem; }

    .green-mode-on {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 12px;
        text-align: center;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);
        animation: pulse 2s ease-in-out infinite;
    }
    .green-mode-off, .reliability-mode-off {
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 12px;
        text-align: center;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(22, 163, 74, 0.4);
    }
    .reliability-mode-on {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 12px;
        text-align: center;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);
        animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.85; }
    }

    .metric-card {
        background: #1e293b;
        color: #f1f5f9;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        border: 1px solid #334155;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #f1f5f9;
        line-height: 1.1;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.3rem;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 0.2rem;
    }

    .fuel-bar-container {
        background: #1e293b;
        color: #f1f5f9;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        border: 1px solid #334155;
    }
    .fuel-bar-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.3rem;
        font-size: 0.9rem;
    }
    .fuel-bar-track {
        background: #334155;
        border-radius: 6px;
        height: 24px;
        overflow: hidden;
    }
    .fuel-bar-fill {
        height: 100%;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 600;
        color: white;
        min-width: 2rem;
        transition: width 0.5s ease;
    }

    .dc-card {
        background: #1e293b;
        color: #f1f5f9;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        border: 1px solid #334155;
        margin-bottom: 0.5rem;
    }
    .dc-card-active { border-left: 4px solid #22c55e; }
    .dc-card-throttled { border-left: 4px solid #f59e0b; }
</style>
"""


def render_metric_card(value: str, label: str, sub: str = ""):
    """Render a styled metric card."""
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    html = (
        '<div class="metric-card">'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-label">{label}</div>'
        f'{sub_html}</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_fuel_bar(name: str, pct: float, mw: int, color: str, marginal: bool = False):
    """Render a horizontal fuel mix bar."""
    tag = " ⚡ MARGINAL" if marginal else ""
    width = max(pct, 2)
    html = (
        '<div class="fuel-bar-container">'
        '<div class="fuel-bar-label">'
        f'<span>{name}{tag}</span><span>{mw:,} MW ({pct:.1f}%)</span></div>'
        '<div class="fuel-bar-track">'
        f'<div class="fuel-bar-fill" style="width:{width}%;background:{color};">{pct:.1f}%</div>'
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_data_center_mock(state_name: str, throttled: bool, reduction_pct: int = 25):
    """
    Show a simulated data center response.
    Works for both Maine (Green Mode, 25%) and Texas (Reliability Mode, 40%).
    """
    if throttled:
        flexible_pct = 100 - reduction_pct
        total_draw = 10.0 * (1 - reduction_pct / 200)  # rough calc
        status_text = f"⚠️ THROTTLED — Flexible load reduced {reduction_pct}%"
        status_class = "dc-card-throttled"
    else:
        flexible_pct = 100
        total_draw = 10.0
        status_text = "✅ NORMAL — Full capacity"
        status_class = "dc-card-active"

    dc_html = (
        f'<div class="dc-card {status_class}">'
        '<div style="font-size:1.1rem;font-weight:700;margin-bottom:0.5rem;">'
        f'🖥️ {state_name} Data Center (Mock)</div>'
        f'<div style="font-size:0.85rem;color:#94a3b8;margin-bottom:0.8rem;">{status_text}</div>'
        '</div>'
    )
    st.markdown(dc_html, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        render_metric_card("100%", "Critical AI (Inference)", "Never throttled")
    with col_b:
        render_metric_card(
            f"{flexible_pct}%",
            "Flexible AI (Training)",
            f"Reduced {reduction_pct}%" if throttled else "Full capacity",
        )
    with col_c:
        render_metric_card(f"{total_draw:.1f} MW", "Total Power Draw", "of 10 MW capacity")
