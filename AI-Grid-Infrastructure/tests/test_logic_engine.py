import pytest
from api.logic_engine import evaluate_texas_grid, evaluate_maine_grid, GridMode

def test_texas_normal_operation():
    result = evaluate_texas_grid(frequency=60.0)
    assert result["mode"] == GridMode.NORMAL
    assert result["reduction_percentage"] == 0.0

def test_texas_reliability_mode():
    result = evaluate_texas_grid(frequency=59.95)
    assert result["mode"] == GridMode.RELIABILITY
    assert result["reduction_percentage"] == 40.0

def test_maine_normal_operation():
    result = evaluate_maine_grid(gas_mix_percentage=40.0, price_mwh=100.0)
    assert result["mode"] == GridMode.NORMAL
    assert result["reduction_percentage"] == 0.0

def test_maine_green_mode_high_gas():
    result = evaluate_maine_grid(gas_mix_percentage=55.0, price_mwh=100.0)
    assert result["mode"] == GridMode.GREEN
    assert result["reduction_percentage"] == 25.0

def test_maine_green_mode_high_price():
    result = evaluate_maine_grid(gas_mix_percentage=45.0, price_mwh=160.0)
    assert result["mode"] == GridMode.GREEN
    assert result["reduction_percentage"] == 25.0

def test_maine_green_mode_both_high():
    result = evaluate_maine_grid(gas_mix_percentage=60.0, price_mwh=200.0)
    assert result["mode"] == GridMode.GREEN
    assert result["reduction_percentage"] == 25.0
