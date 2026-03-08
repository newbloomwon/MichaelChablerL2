from enum import Enum
from typing import Dict, Any

class GridMode(str, Enum):
    NORMAL = "Normal"
    RELIABILITY = "Reliability Mode"
    GREEN = "Green Mode"

def evaluate_texas_grid(frequency: float) -> dict:
    """
    Evaluates Texas (ERCOT) grid conditions.
    Triggers Reliability Mode (40% load reduction) if frequency is below 59.97 Hz.
    """
    if frequency < 59.97:
        return {
            "mode": GridMode.RELIABILITY,
            "reduction_percentage": 40.0,
            "trigger_reason": f"Frequency ({frequency} Hz) below threshold of 59.97 Hz"
        }
    return {
        "mode": GridMode.NORMAL,
        "reduction_percentage": 0.0,
        "trigger_reason": "Normal grid operations"
    }

def evaluate_maine_grid(gas_mix_percentage: float, price_mwh: float) -> dict:
    """
    Evaluates Maine (ISO-NE) grid conditions.
    Triggers Green Mode (25% load reduction) if gas mix > 50% OR price > $150/MWh.
    """
    if gas_mix_percentage > 50.0:
        return {
            "mode": GridMode.GREEN,
            "reduction_percentage": 25.0,
            "trigger_reason": f"Gas mix ({gas_mix_percentage}%) exceeds threshold of 50%"
        }
    if price_mwh > 150.0:
        return {
            "mode": GridMode.GREEN,
            "reduction_percentage": 25.0,
            "trigger_reason": f"Price (${price_mwh}/MWh) exceeds threshold of $150/MWh"
        }
    return {
        "mode": GridMode.NORMAL,
        "reduction_percentage": 0.0,
        "trigger_reason": "Normal grid operations"
    }
