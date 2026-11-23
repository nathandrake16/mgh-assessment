"""Smoke tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
import pytest
from backend.main import app

client = TestClient(app)


def test_smoke_summary():
    """Verify GET /api/summary returns HTTP 200 and valid KPIs & audit."""
    response = client.get("/api/summary")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["total_shipments"] == 500
    assert data["evaluated_shipments"] == 450
    assert data["on_time_shipments"] == 260
    assert data["on_time_percentage"] == 57.78
    assert data["top_trade_lane"] == "BDCGP → ESVLC"
    assert data["top_trade_lane_shipments"] == 77
    assert data["most_delayed_shipment_id"] == "S00158545"
    assert data["most_delayed_days"] == 26
    assert "data_quality_audit" in data
    assert data["data_quality_audit"]["duplicates_removed"] == 11


def test_smoke_trade_lanes():
    """Verify GET /api/trade-lanes returns HTTP 200 and valid list of trade lanes."""
    response = client.get("/api/trade-lanes")
    assert response.status_code == 200
    lanes = response.json()
    assert isinstance(lanes, list)
    assert len(lanes) > 0
    top_lane = lanes[0]
    assert top_lane["trade_lane"] == "BDCGP → ESVLC"
    assert top_lane["total_shipments"] == 77


def test_smoke_top_delayed():
    """Verify GET /api/top-delayed returns HTTP 200 and top delayed shipments."""
    response = client.get("/api/top-delayed?limit=10")
    assert response.status_code == 200
    delayed = response.json()
    assert isinstance(delayed, list)
    assert len(delayed) == 10
    assert delayed[0]["Shipment ID"] == "S00158545"
    assert delayed[0]["delay_days"] == 26


def test_smoke_shipments_list_and_search():
    """Verify GET /api/shipments returns HTTP 200 and supports query filtering."""
    # Full list
    res_all = client.get("/api/shipments")
    assert res_all.status_code == 200
    items = res_all.json()
    assert len(items) == 500
    assert res_all.headers.get("X-Total-Count") == "500"

    # Search query
    res_search = client.get("/api/shipments?q=S00158545")
    assert res_search.status_code == 200
    search_items = res_search.json()
    assert len(search_items) == 1
    assert search_items[0]["Shipment ID"] == "S00158545"

    # Mode filter
    res_mode = client.get("/api/shipments?mode=AIR")
    assert res_mode.status_code == 200
    assert len(res_mode.json()) == 21


def test_smoke_shipment_by_id():
    """Verify GET /api/shipments/{shipment_id} returns 200 for valid ID and 404 for invalid."""
    res_valid = client.get("/api/shipments/S00158545")
    assert res_valid.status_code == 200
    s = res_valid.json()
    assert s["Shipment ID"] == "S00158545"
    assert s["delay_days"] == 26
    assert s["on_time"] is False

    res_invalid = client.get("/api/shipments/NON_EXISTENT_ID")
    assert res_invalid.status_code == 404


def test_smoke_ask_carrier_delayed():
    """Verify POST /api/ask with question 'which carrier is delayed the most?' returns HTTP 200."""
    payload = {"question": "which carrier is delayed the most?"}
    response = client.post("/api/ask", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "answer" in data and isinstance(data["answer"], str) and len(data["answer"]) > 0
    assert "supporting_data" in data and isinstance(data["supporting_data"], list)
    assert "engine" in data
    assert data["engine"] in ["gemini-3.8-flash", "deterministic_fallback"]
    print("\nAsk response answer:", data["answer"])
    print("Supporting data:", data["supporting_data"])
    print("Engine:", data["engine"])


def test_smoke_ask_least_delayed_carrier():
    """Verify POST /api/ask with question 'least delayed carrier' identifies CMA CGM (0.82d delay)."""
    payload = {"question": "least delayed carrier"}
    response = client.post("/api/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "CMA CGM" in data["answer"]
    assert "0.82" in data["answer"]


def test_smoke_ask_specific_carrier():
    """Verify POST /api/ask for specific carrier 'tell me about Maersk' returns exact metrics."""
    payload = {"question": "tell me about Maersk"}
    response = client.post("/api/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "MAERSK" in data["answer"]
    assert "53.97%" in data["answer"]


def test_smoke_frontend_serving():
    """Verify GET / returns HTTP 200 with HTML when frontend is built."""
    response = client.get("/")
    assert response.status_code == 200
    assert "MGH Freight Visibility Dashboard" in response.text
    assert "text/html" in response.headers.get("content-type", "")

