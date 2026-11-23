"""Unit tests for DataService and verified shipment data cleaning rules.

Verifies:
1. Deduplication: 500 unique shipments (11 duplicates removed).
2. On-Time Performance: 450 evaluated shipments, 260 on-time (57.78%).
3. Top Trade Lane: 'BDCGP → ESVLC' with exactly 77 shipments.
4. Most Delayed Shipment: 'S00158545' with 26 days of delay.
5. Weight Cleaning: ~6,648,333.5 kg total cleaned weight, 5 non-positive flagged, 1 grams typo corrected.
6. JSON Safety & Zero NaN values: all output records have None instead of NaN/NaT/Inf.
7. Impossible Arrivals: 6 rows where ATA < ATD flagged as ata_before_atd.
8. Consignee & Status Mismatches: 7 missing consignees, 6 delivered missing ATA, 4 in transit with ATA.
"""

import math
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pytest

from backend.data_service import DataService, clean_shipments, get_data_service


@pytest.fixture(scope="module")
def data_service() -> DataService:
    """Fixture providing an initialized DataService instance."""
    return get_data_service()


def test_unique_shipments_count(data_service: DataService):
    """Rule 1: Result MUST be 500 unique shipments after deduplication."""
    df = data_service.get_df()
    audit = data_service.get_audit_log()

    assert len(df) == 500, f"Expected 500 unique shipments, got {len(df)}"
    assert df["Shipment ID"].nunique() == 500, "Shipment ID must be unique"
    assert audit["total_raw_rows"] == 511, "Expected 511 raw rows"
    assert audit["duplicates_removed"] == 11, "Expected 11 duplicate rows dropped"


def test_deduplication_priority(data_service: DataService):
    """Rule 1: Deduplication must keep Delivered and non-null ATA records first."""
    df = data_service.get_df()

    # S00158734 had duplicates: one 'Delivered' with ATA, one 'In Transit' with null ATA
    dup_row = df[df["Shipment ID"] == "S00158734"].iloc[0]
    assert dup_row["Status"] == "Delivered"
    assert dup_row["ATA"] is not None


def test_port_normalization_and_trade_lanes(data_service: DataService):
    """Rule 2: Port normalization and top lane BDCGP → ESVLC (77 shipments)."""
    df = data_service.get_df()
    kpis = data_service.get_kpis()
    audit = data_service.get_audit_log()

    # Verify no unnormalized port variants or trailing whitespaces exist
    forbidden_ports = {"bdcgp", "chattogram", "cgp", "CGP", "Chattogram"}
    for p in df["Origin Port"]:
        assert p not in forbidden_ports, f"Found unnormalized origin port: {p}"
        assert p == p.upper()
        assert p == p.strip()

    for p in df["Destination Port"]:
        assert p == p.upper()
        assert p == p.strip()

    # Top trade lane
    lane_counts = df["trade_lane"].value_counts()
    assert lane_counts.index[0] == "BDCGP → ESVLC"
    assert lane_counts.iloc[0] == 77, f"Expected 77 shipments on top lane, got {lane_counts.iloc[0]}"

    assert kpis["top_trade_lane"] == "BDCGP → ESVLC"
    assert kpis["top_trade_lane_shipments"] == 77
    assert audit["ports_normalized"] == 24


def test_smart_date_parsing_and_typos(data_service: DataService):
    """Rule 3: Year typo /2062 -> /2026 and smart date parsing."""
    df = data_service.get_df()
    audit = data_service.get_audit_log()

    # Check shipment S00158650 which had 2/19/2062 typo
    row_2062 = df[df["Shipment ID"] == "S00158650"].iloc[0]
    assert row_2062["ETA"] == "2026-02-19"
    assert "year_typo_fixed" in row_2062["data_quality_flags"]

    assert audit["year_typo_fixed"] == 1
    assert audit["ambiguous_dates_resolved"] > 0


def test_impossible_arrivals_flagged(data_service: DataService):
    """Rule 4: Flag any row where ATA < ATD (6 rows) as ata_before_atd."""
    df = data_service.get_df()
    audit = data_service.get_audit_log()

    impossible_rows = df[df["ata_before_atd"] == True]
    assert len(impossible_rows) == 6, f"Expected 6 impossible arrival rows, got {len(impossible_rows)}"
    assert audit["ata_before_atd"] == 6

    expected_ids = {"S00159115", "S00158459", "S00159174", "S00158864", "S00159407", "S00158304"}
    actual_ids = set(impossible_rows["Shipment ID"])
    assert actual_ids == expected_ids, f"Mismatch in impossible arrival IDs: {actual_ids ^ expected_ids}"

    # Verify each impossible arrival row is NOT evaluated
    for _, row in impossible_rows.iterrows():
        assert row["is_evaluated"] is False
        assert pd.isna(row["delay_days"]) or row["delay_days"] is None
        assert pd.isna(row["on_time"]) or row["on_time"] is None
        assert "ata_before_atd" in row["data_quality_flags"]

    # Verify in JSON-exported shipments that delay_days is strictly None
    shipment_map = {s["Shipment ID"]: s for s in data_service.get_shipments()}
    for s_id in expected_ids:
        assert shipment_map[s_id]["delay_days"] is None
        assert shipment_map[s_id]["on_time"] is None
        assert shipment_map[s_id]["is_evaluated"] is False
        assert shipment_map[s_id]["ata_before_atd"] is True


def test_on_time_performance_metrics(data_service: DataService):
    """Rule 4: 450 evaluated shipments, 260 on-time (57.78%)."""
    df = data_service.get_df()
    kpis = data_service.get_kpis()
    audit = data_service.get_audit_log()

    eval_df = df[df["is_evaluated"] == True]
    assert len(eval_df) == 450, f"Expected 450 evaluated shipments, got {len(eval_df)}"
    assert kpis["evaluated_shipments"] == 450
    assert audit["evaluated_shipments"] == 450

    on_time_df = eval_df[eval_df["on_time"] == True]
    assert len(on_time_df) == 260, f"Expected 260 on-time shipments, got {len(on_time_df)}"
    assert kpis["on_time_shipments"] == 260
    assert audit["on_time_shipments"] == 260

    # On-time rate = 260 / 450 = 57.777...% -> 57.78%
    assert kpis["on_time_percentage"] == 57.78
    calculated_pct = round((260 / 450) * 100, 2)
    assert calculated_pct == 57.78


def test_most_delayed_shipment(data_service: DataService):
    """Rule 4: #1 most delayed shipment is S00158545 with 26 days."""
    df = data_service.get_df()
    kpis = data_service.get_kpis()

    eval_df = df[df["is_evaluated"] == True]
    top_delayed = eval_df.sort_values(by="delay_days", ascending=False).iloc[0]

    assert top_delayed["Shipment ID"] == "S00158545"
    assert top_delayed["delay_days"] == 26
    assert kpis["most_delayed_shipment_id"] == "S00158545"
    assert kpis["most_delayed_days"] == 26


def test_cleaned_weight_calculation(data_service: DataService):
    """Rule 5: Cleaned weight ~6,648,333.5 kg, 5 non-positive flagged, 1 grams typo corrected."""
    df = data_service.get_df()
    kpis = data_service.get_kpis()
    audit = data_service.get_audit_log()

    # 5 non-positive weight rows
    le_zero_rows = df[df["data_quality_flags"].apply(lambda flags: "weight_zero_or_negative" in flags)]
    assert len(le_zero_rows) == 5, f"Expected 5 non-positive weight rows, got {len(le_zero_rows)}"
    assert audit["weight_non_positive"] == 5
    for _, row in le_zero_rows.iterrows():
        assert pd.isna(row["Weight (KG)"]) or row["Weight (KG)"] is None

    # Check exported dicts have None for weight <= 0
    shipment_map = {s["Shipment ID"]: s for s in data_service.get_shipments()}
    for s_id in le_zero_rows["Shipment ID"]:
        assert shipment_map[s_id]["Weight (KG)"] is None

    # 1 grams typo (>100,000 kg)
    grams_typo_rows = df[df["data_quality_flags"].apply(lambda flags: "weight_grams_typo_divided_by_1000" in flags)]
    assert len(grams_typo_rows) == 1, f"Expected 1 grams typo row, got {len(grams_typo_rows)}"
    assert grams_typo_rows.iloc[0]["Shipment ID"] == "S00158128"
    assert grams_typo_rows.iloc[0]["Weight (KG)"] == 21816.0
    assert audit["weight_grams_typo_corrected"] == 1
    assert shipment_map["S00158128"]["Weight (KG)"] == 21816.0

    # Total cleaned weight
    valid_weights = [w for w in df["Weight (KG)"] if pd.notna(w)]
    total_cleaned_weight = sum(valid_weights)
    assert total_cleaned_weight == pytest.approx(6648333.5, abs=0.5)
    assert kpis["total_weight_kg"] == pytest.approx(6648333.5, abs=0.5)


def test_consignee_and_status_mismatches(data_service: DataService):
    """Rule 6: Missing Consignee (7 rows) and Status Mismatches (6 delivered missing ATA, 4 in transit with ATA)."""
    df = data_service.get_df()
    audit = data_service.get_audit_log()

    # Missing consignees filled with "Unknown"
    unknown_consignees = df[df["Consignee"] == "Unknown"]
    assert len(unknown_consignees) == 7, f"Expected 7 Unknown consignees, got {len(unknown_consignees)}"
    assert audit["missing_consignee_filled"] == 7

    # Delivered rows with missing ATA
    deliv_missing_ata = df[df["data_quality_flags"].apply(lambda flags: "delivered_missing_ata" in flags)]
    assert len(deliv_missing_ata) == 6, f"Expected 6 delivered missing ATA, got {len(deliv_missing_ata)}"
    assert audit["delivered_missing_ata"] == 6

    # In Transit rows with present ATA
    transit_with_ata = df[df["data_quality_flags"].apply(lambda flags: "in_transit_present_ata" in flags)]
    assert len(transit_with_ata) == 4, f"Expected 4 in transit with present ATA, got {len(transit_with_ata)}"
    assert audit["in_transit_with_ata"] == 4


def test_zero_nan_values_in_exported_shipments(data_service: DataService):
    """Rule 7: Ensure all output helper functions convert NaN/NaT/Infinity to None."""
    shipments = data_service.get_shipments()
    assert len(shipments) == 500

    nan_occurrences = []
    nat_occurrences = []
    inf_occurrences = []

    for i, record in enumerate(shipments):
        for key, val in record.items():
            if isinstance(val, float):
                if math.isnan(val) or np.isnan(val):
                    nan_occurrences.append((i, key, val))
                if math.isinf(val) or np.isinf(val):
                    inf_occurrences.append((i, key, val))
            if val is pd.NaT:
                nat_occurrences.append((i, key, val))
            if str(val).lower() == "nan":
                nan_occurrences.append((i, key, val))

    assert len(nan_occurrences) == 0, f"Found NaN values in shipments: {nan_occurrences[:5]}"
    assert len(nat_occurrences) == 0, f"Found NaT values in shipments: {nat_occurrences[:5]}"
    assert len(inf_occurrences) == 0, f"Found Inf values in shipments: {inf_occurrences[:5]}"


def test_trade_lanes_summary(data_service: DataService):
    """Verify get_trade_lanes returns aggregated metrics with top lane BDCGP → ESVLC."""
    lanes = data_service.get_trade_lanes()
    assert len(lanes) > 0

    top_lane = lanes[0]
    assert top_lane["trade_lane"] == "BDCGP → ESVLC"
    assert top_lane["total_shipments"] == 77
    assert top_lane["origin_port"] == "BDCGP"
    assert top_lane["destination_port"] == "ESVLC"

    # Verify zero NaNs in lanes
    for lane in lanes:
        for k, v in lane.items():
            if isinstance(v, float):
                assert not math.isnan(v), f"NaN found in lane {lane['trade_lane']} key {k}"


def test_carrier_performance_summary(data_service: DataService):
    """Verify get_carrier_performance returns carriers with valid metrics."""
    carriers = data_service.get_carrier_performance()
    assert len(carriers) > 0

    # Ensure all numbers are clean
    for c in carriers:
        assert c["total_shipments"] > 0
        assert c["carrier"] is not None
        for k, v in c.items():
            if isinstance(v, float):
                assert not math.isnan(v), f"NaN found in carrier {c['carrier']} key {k}"


def test_clean_shipments_helper():
    """Verify top-level clean_shipments() helper function."""
    df, audit = clean_shipments()
    assert len(df) == 500
    assert audit["unique_shipments"] == 500
    assert audit["on_time_shipments"] == 260
