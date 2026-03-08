"""
tests/test_texas_ingestion.py — Tests for Texas data ingestion module
======================================================================
Tests the parsing logic, threshold evaluation, and snapshot structure.
Uses mock data so tests run without network / API credentials.
"""

import pytest
from unittest.mock import patch, MagicMock
from texas_ingestion import (
    _parse_conditions_page,
    fetch_texas_snapshot,
    FREQUENCY_THRESHOLD_HZ,
    RELIABILITY_REDUCTION_PCT,
)


# ---------------------------------------------------------------------------
# HTML parser tests
# ---------------------------------------------------------------------------

MOCK_ERCOT_HTML = """
<html><body>
<table>
  <tr><th>Actual System Demand</th><td>45,231</td></tr>
  <tr><th>Total System Capacity</th><td>78,500</td></tr>
  <tr><th>Current Frequency</th><td>59.9845</td></tr>
  <tr><th>Wind Output</th><td>12,345</td></tr>
</table>
</body></html>
"""

MOCK_ERCOT_HTML_LOW_FREQ = """
<html><body>
<table>
  <tr><th>Current Frequency</th><td>59.9500</td></tr>
  <tr><th>Actual System Demand</th><td>62,000</td></tr>
</table>
</body></html>
"""


def test_parse_conditions_normal():
    """Parse HTML page and extract frequency and load data."""
    result = _parse_conditions_page(MOCK_ERCOT_HTML)
    assert result["frequency_hz"] == 59.9845
    assert result["wind_output_mw"] == 12345.0


def test_parse_conditions_low_freq():
    """Parse HTML page with dangerously low frequency."""
    result = _parse_conditions_page(MOCK_ERCOT_HTML_LOW_FREQ)
    assert result["frequency_hz"] == 59.9500
    assert result["frequency_hz"] < FREQUENCY_THRESHOLD_HZ


def test_parse_conditions_empty():
    """Parse empty/broken HTML returns empty dict."""
    result = _parse_conditions_page("<html></html>")
    assert result == {} or "frequency_hz" not in result


# ---------------------------------------------------------------------------
# Snapshot structure tests (with mocked network calls)
# ---------------------------------------------------------------------------

def _mock_frequency_response():
    """Create a mock requests.Response for the HTML frequency page."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_ERCOT_HTML
    return mock_resp


@patch("texas_ingestion.requests.get")
@patch("texas_ingestion._ercot_api_get")
def test_snapshot_structure(mock_api_get, mock_requests_get):
    """Snapshot should have all required keys."""
    mock_requests_get.return_value = _mock_frequency_response()
    mock_api_get.return_value = None  # prices/forecast will return empty dicts

    snap = fetch_texas_snapshot()

    assert snap["state"] == "texas"
    assert "fetched_at" in snap
    assert "frequency" in snap
    assert "prices" in snap
    assert "load_forecast" in snap
    assert "reliability_mode_triggered" in snap
    assert "trigger_reasons" in snap


@patch("texas_ingestion.requests.get")
@patch("texas_ingestion._ercot_api_get")
def test_snapshot_normal_frequency(mock_api_get, mock_requests_get):
    """Normal frequency (59.98 Hz) should NOT trigger Reliability Mode."""
    mock_requests_get.return_value = _mock_frequency_response()
    mock_api_get.return_value = None

    snap = fetch_texas_snapshot()

    assert snap["reliability_mode_triggered"] is False
    assert snap["frequency"]["frequency_hz"] == 59.9845
    assert snap["frequency"]["below_threshold"] is False
    assert len(snap["trigger_reasons"]) == 0


@patch("texas_ingestion.requests.get")
@patch("texas_ingestion._ercot_api_get")
def test_snapshot_low_frequency_triggers_reliability(mock_api_get, mock_requests_get):
    """Low frequency (59.95 Hz) SHOULD trigger Reliability Mode."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_ERCOT_HTML_LOW_FREQ
    mock_requests_get.return_value = mock_resp
    mock_api_get.return_value = None

    snap = fetch_texas_snapshot()

    assert snap["reliability_mode_triggered"] is True
    assert snap["frequency"]["below_threshold"] is True
    assert len(snap["trigger_reasons"]) > 0
    assert "59.9500" in snap["trigger_reasons"][0]


# ---------------------------------------------------------------------------
# Threshold boundary tests
# ---------------------------------------------------------------------------

def test_threshold_values():
    """Verify the threshold constants are set correctly per PRD."""
    assert FREQUENCY_THRESHOLD_HZ == 59.97
    assert RELIABILITY_REDUCTION_PCT == 40
