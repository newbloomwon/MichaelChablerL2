"""
panels/__init__.py — State panel registry
===========================================
Each state has its own render function in its own file.
To add a new state, just create a new file (e.g., texas.py)
and register it in STATE_PANELS below.
"""

# Registry: maps sidebar label → (module, render_function_name)
# Ibrahima: add your entry here when Texas is ready ↓
STATE_PANELS = {
    "Maine (ISO-NE)": "panels.maine",
    "Texas (ERCOT)": "panels.texas",
}
