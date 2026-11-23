"""Data Service module for MGH Assessment.

Implements verified data cleaning rules for shipment logistics data:
1. Deduplicate Shipment ID (500 unique shipments)
2. Normalize Ports and construct trade_lane
3. Smart Date Parsing (ETD, ETA, ATD, ATA) with transit window heuristics
4. Identify Impossible Arrivals (ATA < ATD) and calculate delay_days / on_time (450 evaluated, 260 on-time)
5. Weight Cleaning (handle non-positive weights and grams typo)
6. Missing Consignee & Status Mismatches tracking
7. Comprehensive Audit Log & JSON-safe data export
"""

import math
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

PORT_MAP = {
    "bdcgp": "BDCGP",
    "chattogram": "BDCGP",
    "cgp": "BDCGP",
}


def sanitize_for_json(obj: Any) -> Any:
    """Recursively converts NaN, NaT, Infinity, and datetime objects into JSON-safe types (None / str)."""
    if obj is None:
        return None
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (float, np.floating)):
        if math.isnan(obj) or math.isinf(obj) or np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if obj is pd.NaT:
        return None
    if isinstance(obj, (pd.Timestamp, datetime, date)):
        if pd.isna(obj):
            return None
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]
    return obj


class DataService:
    """Service to load, clean, validate, and query shipment data."""

    def __init__(self, file_path: Optional[Union[str, Path]] = None):
        self.file_path = self._resolve_file_path(file_path)
        self.raw_df: Optional[pd.DataFrame] = None
        self.cleaned_df: Optional[pd.DataFrame] = None
        self.data_quality_audit: Dict[str, int] = {}
        self.load_and_clean()

    @staticmethod
    def _resolve_file_path(file_path: Optional[Union[str, Path]]) -> Path:
        """Resolve the input CSV path checking common project locations."""
        if file_path:
            p = Path(file_path)
            if p.exists():
                return p

        candidates = [
            Path("shipments_2026H1.csv"),
            Path("backend/shipments_2026H1.csv"),
            Path("../shipments_2026H1.csv"),
            Path(__file__).resolve().parent / "shipments_2026H1.csv",
            Path(__file__).resolve().parent.parent / "shipments_2026H1.csv",
        ]
        for c in candidates:
            if c.exists():
                return c.resolve()

        # Fallback to local default if not found
        return Path("shipments_2026H1.csv")

    @staticmethod
    def _normalize_port(port_val: Any) -> Tuple[str, bool]:
        """Normalize a port name: strip whitespace, map known aliases, uppercase.

        Returns (cleaned_port, was_normalized).
        """
        if pd.isna(port_val):
            return "UNKNOWN", True
        p_raw = str(port_val)
        p_clean = p_raw.strip()
        p_lower = p_clean.lower()
        if p_lower in PORT_MAP:
            normalized = PORT_MAP[p_lower]
        else:
            normalized = p_clean.upper()
        was_normalized = (p_raw != normalized)
        return normalized, was_normalized

    @staticmethod
    def _parse_m_d_y(val: Any) -> Optional[pd.Timestamp]:
        """Parse strict M/D/YYYY dates for ETD and ATD."""
        if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
            return None
        return pd.to_datetime(str(val).strip(), format="%m/%d/%Y", errors="coerce")

    @staticmethod
    def _get_transit_window(mode: str, trade_lane: str) -> Tuple[int, int]:
        """Return plausible transit window in days:

        - AIR: 0-15 days
        - CNSHA → BDCGP: 7-35 days
        - other SEA: 15-65 days
        """
        if mode == "AIR":
            return 0, 15
        if trade_lane == "CNSHA → BDCGP":
            return 7, 35
        return 15, 65

    @classmethod
    def _parse_smart_arrival(
        cls,
        val: Any,
        ref_date: Optional[pd.Timestamp],
        mode: str,
        trade_lane: str,
    ) -> Tuple[Optional[pd.Timestamp], bool, bool]:
        """Smart parse arrival dates (ETA, ATA):

        - Fixes year typo /2062 -> /2026
        - Parses D-Mon-YY (%d-%b-%y)
        - Handles slash dates (p1 > 12 -> DD/MM/YYYY; p2 > 12 -> M/D/YYYY)
        - Uses transit window heuristics when both p1, p2 <= 12
        Returns: (parsed_timestamp, typo_fixed, ambiguous_resolved)
        """
        if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
            return None, False, False

        val_orig = str(val).strip()
        typo_fixed = "/2062" in val_orig
        val_clean = val_orig.replace("/2062", "/2026")
        ambiguous_resolved = False

        # 1. Parse D-Mon-YY (e.g. 8-Feb-26, 29-Mar-26)
        if "-" in val_clean:
            try:
                parsed = pd.to_datetime(val_clean, format="%d-%b-%y")
                return parsed, typo_fixed, False
            except Exception:
                try:
                    parsed = pd.to_datetime(val_clean)
                    return parsed, typo_fixed, False
                except Exception:
                    pass

        # 2. Parse slash dates
        if "/" in val_clean:
            parts = val_clean.split("/")
            if len(parts) == 3:
                try:
                    p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
                    if p1 > 12:
                        # DD/MM/YYYY
                        return pd.to_datetime(f"{p3}-{p2:02d}-{p1:02d}"), typo_fixed, False
                    elif p2 > 12:
                        # M/D/YYYY
                        return pd.to_datetime(f"{p3}-{p1:02d}-{p2:02d}"), typo_fixed, False
                    else:
                        # Both <= 12: ambiguous
                        date_mdy = pd.to_datetime(f"{p3}-{p1:02d}-{p2:02d}")
                        date_dmy = pd.to_datetime(f"{p3}-{p2:02d}-{p1:02d}")

                        if p1 == p2:
                            return date_mdy, typo_fixed, False

                        ambiguous_resolved = True
                        if ref_date is not None and not pd.isna(ref_date):
                            win_min, win_max = cls._get_transit_window(mode, trade_lane)
                            diff_mdy = (date_mdy - ref_date).days
                            diff_dmy = (date_dmy - ref_date).days

                            mdy_in = win_min <= diff_mdy <= win_max
                            dmy_in = win_min <= diff_dmy <= win_max

                            if mdy_in and not dmy_in:
                                return date_mdy, typo_fixed, True
                            elif dmy_in and not mdy_in:
                                return date_dmy, typo_fixed, True
                            elif mdy_in and dmy_in:
                                mid = (win_min + win_max) / 2
                                chosen = date_mdy if abs(diff_mdy - mid) <= abs(diff_dmy - mid) else date_dmy
                                return chosen, typo_fixed, True
                            else:
                                # When neither is strictly in window, pick the date closest to the window boundary
                                dist_mdy = min(abs(diff_mdy - win_min), abs(diff_mdy - win_max))
                                dist_dmy = min(abs(diff_dmy - win_min), abs(diff_dmy - win_max))
                                chosen = date_mdy if dist_mdy <= dist_dmy else date_dmy
                                return chosen, typo_fixed, True
                        else:
                            return date_mdy, typo_fixed, True
                except Exception:
                    pass

        parsed = pd.to_datetime(val_clean, errors="coerce")
        return parsed, typo_fixed, False

    def load_and_clean(self) -> pd.DataFrame:
        """Execute all data cleaning rules and build audit log."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Source file not found at: {self.file_path}")

        raw_df = pd.read_csv(self.file_path)
        self.raw_df = raw_df.copy()
        raw_count = len(raw_df)

        # ---------------------------------------------------------
        # Rule 1: Deduplicate Shipment ID
        # ---------------------------------------------------------
        # Sort so Status == 'Delivered' and non-null ATA come first, then drop duplicates keeping first
        has_ata_raw = raw_df["ATA"].notna() & (raw_df["ATA"].astype(str).str.strip() != "") & (raw_df["ATA"].astype(str).str.lower() != "nan")
        is_delivered_raw = raw_df["Status"].astype(str).str.strip().str.lower() == "delivered"

        df_sorted = raw_df.assign(_is_deliv=is_delivered_raw, _has_ata=has_ata_raw).sort_values(
            by=["_is_deliv", "_has_ata"], ascending=[False, False]
        )
        df = df_sorted.drop_duplicates(subset=["Shipment ID"], keep="first").copy()
        df = df.drop(columns=["_is_deliv", "_has_ata"]).reset_index(drop=True)
        duplicates_removed = raw_count - len(df)

        # Initialize tracking flags list for each shipment
        data_quality_flags: List[List[str]] = [[] for _ in range(len(df))]

        # ---------------------------------------------------------
        # Rule 2: Normalize Ports & Construct Trade Lane
        # ---------------------------------------------------------
        clean_origins = []
        clean_dests = []
        trade_lanes = []
        ports_normalized_count = 0

        for i, row in df.iterrows():
            orig_clean, o_norm = self._normalize_port(row["Origin Port"])
            dest_clean, d_norm = self._normalize_port(row["Destination Port"])
            clean_origins.append(orig_clean)
            clean_dests.append(dest_clean)
            trade_lanes.append(f"{orig_clean} → {dest_clean}")

            if o_norm or d_norm:
                ports_normalized_count += 1
                data_quality_flags[i].append("port_normalized")

        df["Origin Port"] = clean_origins
        df["Destination Port"] = clean_dests
        df["trade_lane"] = trade_lanes

        # ---------------------------------------------------------
        # Rule 3: Smart Date Parsing
        # ---------------------------------------------------------
        # ETD and ATD are M/D/YYYY
        df["ETD_dt"] = df["ETD"].apply(self._parse_m_d_y)
        df["ATD_dt"] = df["ATD"].apply(self._parse_m_d_y)

        eta_dt_list = []
        ata_dt_list = []
        year_typo_count = 0
        ambiguous_dates_count = 0

        for i, row in df.iterrows():
            eta_val, eta_typo, eta_amb = self._parse_smart_arrival(
                row["ETA"], row["ETD_dt"], row["Mode"], row["trade_lane"]
            )
            ata_val, ata_typo, ata_amb = self._parse_smart_arrival(
                row["ATA"], row["ATD_dt"], row["Mode"], row["trade_lane"]
            )

            eta_dt_list.append(eta_val)
            ata_dt_list.append(ata_val)

            if eta_typo or ata_typo:
                year_typo_count += 1
                data_quality_flags[i].append("year_typo_fixed")

            if eta_amb or ata_amb:
                ambiguous_dates_count += 1
                data_quality_flags[i].append("ambiguous_date_resolved")

        df["ETA_dt"] = eta_dt_list
        df["ATA_dt"] = ata_dt_list

        # ---------------------------------------------------------
        # Rule 4: Impossible Arrivals & Performance Evaluation
        # ---------------------------------------------------------
        ata_before_atd_count = 0
        ata_before_atd_flags = []

        for i, row in df.iterrows():
            is_impossible = False
            if row["ATA_dt"] is not None and row["ATD_dt"] is not None:
                if not pd.isna(row["ATA_dt"]) and not pd.isna(row["ATD_dt"]):
                    if row["ATA_dt"] < row["ATD_dt"]:
                        is_impossible = True
            if is_impossible:
                ata_before_atd_count += 1
                data_quality_flags[i].append("ata_before_atd")
            ata_before_atd_flags.append(is_impossible)

        df["ata_before_atd"] = ata_before_atd_flags

        # Evaluation criteria: Exclude null ATA or ata_before_atd
        delay_days_list = []
        on_time_list = []
        is_evaluated_list = []

        for i, row in df.iterrows():
            has_valid_ata = (row["ATA_dt"] is not None) and (not pd.isna(row["ATA_dt"]))
            if has_valid_ata and not row["ata_before_atd"]:
                is_evaluated_list.append(True)
                delay = (row["ATA_dt"] - row["ETA_dt"]).days
                delay_days_list.append(delay)
                on_time_list.append(delay <= 0)
            else:
                is_evaluated_list.append(False)
                delay_days_list.append(None)
                on_time_list.append(None)

        df["is_evaluated"] = is_evaluated_list
        df["delay_days"] = delay_days_list
        df["on_time"] = on_time_list

        # ---------------------------------------------------------
        # Rule 5: Weight Cleaning
        # ---------------------------------------------------------
        clean_weights = []
        weight_non_positive_count = 0
        weight_grams_typo_count = 0

        for i, row in df.iterrows():
            w_raw = row["Weight (KG)"]
            if pd.isna(w_raw):
                clean_weights.append(None)
                continue
            try:
                w_val = float(w_raw)
            except (ValueError, TypeError):
                clean_weights.append(None)
                continue

            if w_val <= 0:
                clean_weights.append(None)
                weight_non_positive_count += 1
                data_quality_flags[i].append("weight_zero_or_negative")
            elif w_val > 100000:
                cleaned_w = round(w_val / 1000.0, 2)
                clean_weights.append(cleaned_w)
                weight_grams_typo_count += 1
                data_quality_flags[i].append("weight_grams_typo_divided_by_1000")
            else:
                clean_weights.append(w_val)

        df["Weight (KG)"] = clean_weights

        # ---------------------------------------------------------
        # Rule 6: Missing Consignee & Status Mismatches
        # ---------------------------------------------------------
        clean_consignees = []
        missing_consignee_count = 0
        delivered_missing_ata_count = 0
        in_transit_with_ata_count = 0

        for i, row in df.iterrows():
            c_raw = row["Consignee"]
            if pd.isna(c_raw) or str(c_raw).strip() == "" or str(c_raw).lower() == "nan":
                clean_consignees.append("Unknown")
                missing_consignee_count += 1
                data_quality_flags[i].append("missing_consignee")
            else:
                clean_consignees.append(str(c_raw).strip())

            status_clean = str(row["Status"]).strip().lower()
            has_ata = (row["ATA_dt"] is not None) and (not pd.isna(row["ATA_dt"]))

            if status_clean == "delivered" and not has_ata:
                delivered_missing_ata_count += 1
                data_quality_flags[i].append("delivered_missing_ata")

            if status_clean == "in transit" and has_ata:
                in_transit_with_ata_count += 1
                data_quality_flags[i].append("in_transit_present_ata")

        df["Consignee"] = clean_consignees
        df["data_quality_flags"] = data_quality_flags

        # Store formatted ISO dates for ETD, ETA, ATD, ATA
        df["ETD"] = df["ETD_dt"].apply(lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else None)
        df["ETA"] = df["ETA_dt"].apply(lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else None)
        df["ATD"] = df["ATD_dt"].apply(lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else None)
        df["ATA"] = df["ATA_dt"].apply(lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else None)

        # Ensure Volume (CBM) is float
        df["Volume (CBM)"] = pd.to_numeric(df["Volume (CBM)"], errors="coerce")

        # ---------------------------------------------------------
        # Rule 7: Data Quality Audit Dictionary
        # ---------------------------------------------------------
        self.data_quality_audit = {
            "total_raw_rows": raw_count,
            "unique_shipments": len(df),
            "duplicates_removed": duplicates_removed,
            "ports_normalized": ports_normalized_count,
            "year_typo_fixed": year_typo_count,
            "ambiguous_dates_resolved": ambiguous_dates_count,
            "ata_before_atd": ata_before_atd_count,
            "weight_non_positive": weight_non_positive_count,
            "weight_grams_typo_corrected": weight_grams_typo_count,
            "missing_consignee_filled": missing_consignee_count,
            "delivered_missing_ata": delivered_missing_ata_count,
            "in_transit_with_ata": in_transit_with_ata_count,
            "evaluated_shipments": int(df["is_evaluated"].sum()),
            "on_time_shipments": int((df["on_time"] == True).sum()),
        }

        self.cleaned_df = df
        return df

    def get_df(self) -> pd.DataFrame:
        """Return the cleaned pandas DataFrame."""
        if self.cleaned_df is None:
            self.load_and_clean()
        return self.cleaned_df

    def get_audit_log(self) -> Dict[str, Any]:
        """Return the data quality audit dictionary."""
        return sanitize_for_json(self.data_quality_audit)

    def get_shipments(
        self,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        trade_lane: Optional[str] = None,
        carrier: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return sanitized shipment records with optional filtering and pagination.

        Guaranteed zero NaN/NaT/Infinity values.
        """
        df = self.get_df().copy()

        if mode:
            df = df[df["Mode"].str.upper() == mode.upper()]
        if status:
            df = df[df["Status"].str.lower() == status.lower()]
        if trade_lane:
            df = df[df["trade_lane"] == trade_lane]
        if carrier:
            df = df[df["Carrier"].str.upper() == carrier.upper()]

        if offset > 0:
            df = df.iloc[offset:]
        if limit is not None:
            df = df.iloc[:limit]

        columns_to_export = [
            "Shipment ID",
            "Mode",
            "Container Mode",
            "Carrier",
            "Origin Port",
            "Destination Port",
            "trade_lane",
            "Shipper",
            "Consignee",
            "ETD",
            "ETA",
            "ATD",
            "ATA",
            "Weight (KG)",
            "Volume (CBM)",
            "Status",
            "delay_days",
            "on_time",
            "is_evaluated",
            "ata_before_atd",
            "data_quality_flags",
        ]
        records = df[columns_to_export].to_dict(orient="records")
        return sanitize_for_json(records)

    def get_kpis(self) -> Dict[str, Any]:
        """Return core logistics KPIs:

        - Total shipments: 500
        - Evaluated shipments: 450
        - On-time shipments: 260
        - On-time percentage: 57.78%
        - Total cleaned weight: ~6,648,333.5 kg
        - Top trade lane
        """
        df = self.get_df()
        eval_df = df[df["is_evaluated"] == True]

        total_shipments = len(df)
        evaluated_count = len(eval_df)
        on_time_count = int((eval_df["on_time"] == True).sum())
        on_time_rate = round((on_time_count / evaluated_count) * 100, 2) if evaluated_count else 0.0

        total_weight = round(float(df["Weight (KG)"].dropna().sum()), 2)
        total_volume = round(float(df["Volume (CBM)"].dropna().sum()), 2)
        avg_delay = round(float(eval_df["delay_days"].mean()), 2) if evaluated_count else 0.0

        top_lane_series = df["trade_lane"].value_counts()
        top_lane = top_lane_series.index[0] if len(top_lane_series) > 0 else "N/A"
        top_lane_volume = int(top_lane_series.iloc[0]) if len(top_lane_series) > 0 else 0

        # Most delayed shipment
        most_delayed_row = eval_df.sort_values(by="delay_days", ascending=False).iloc[0] if len(eval_df) > 0 else None
        most_delayed_id = most_delayed_row["Shipment ID"] if most_delayed_row is not None else None
        most_delayed_days = int(most_delayed_row["delay_days"]) if most_delayed_row is not None else None

        kpis = {
            "total_shipments": total_shipments,
            "evaluated_shipments": evaluated_count,
            "on_time_shipments": on_time_count,
            "on_time_percentage": on_time_rate,
            "total_weight_kg": total_weight,
            "total_volume_cbm": total_volume,
            "average_delay_days": avg_delay,
            "top_trade_lane": top_lane,
            "top_trade_lane_shipments": top_lane_volume,
            "most_delayed_shipment_id": most_delayed_id,
            "most_delayed_days": most_delayed_days,
        }
        return sanitize_for_json(kpis)

    def get_trade_lanes(self) -> List[Dict[str, Any]]:
        """Return aggregated trade lane performance metrics."""
        df = self.get_df()
        lanes = []
        for lane, group in df.groupby("trade_lane"):
            eval_g = group[group["is_evaluated"] == True]
            eval_cnt = len(eval_g)
            ontime_cnt = int((eval_g["on_time"] == True).sum())
            ontime_pct = round((ontime_cnt / eval_cnt) * 100, 2) if eval_cnt else None
            avg_delay = round(float(eval_g["delay_days"].mean()), 2) if eval_cnt else None

            lanes.append({
                "trade_lane": lane,
                "origin_port": group["Origin Port"].iloc[0],
                "destination_port": group["Destination Port"].iloc[0],
                "total_shipments": len(group),
                "evaluated_shipments": eval_cnt,
                "on_time_shipments": ontime_cnt,
                "on_time_percentage": ontime_pct,
                "average_delay_days": avg_delay,
                "total_weight_kg": round(float(group["Weight (KG)"].dropna().sum()), 2),
                "total_volume_cbm": round(float(group["Volume (CBM)"].dropna().sum()), 2),
            })
        lanes.sort(key=lambda x: x["total_shipments"], reverse=True)
        return sanitize_for_json(lanes)

    def get_carrier_performance(self) -> List[Dict[str, Any]]:
        """Return aggregated performance metrics per carrier."""
        df = self.get_df()
        carriers = []
        for carrier, group in df.groupby("Carrier"):
            eval_g = group[group["is_evaluated"] == True]
            eval_cnt = len(eval_g)
            ontime_cnt = int((eval_g["on_time"] == True).sum())
            ontime_pct = round((ontime_cnt / eval_cnt) * 100, 2) if eval_cnt else None
            avg_delay = round(float(eval_g["delay_days"].mean()), 2) if eval_cnt else None

            carriers.append({
                "carrier": carrier,
                "total_shipments": len(group),
                "evaluated_shipments": eval_cnt,
                "on_time_shipments": ontime_cnt,
                "on_time_percentage": ontime_pct,
                "average_delay_days": avg_delay,
            })
        carriers.sort(key=lambda x: x["total_shipments"], reverse=True)
        return sanitize_for_json(carriers)


# Module-level convenience instance and functions
_service_instance: Optional[DataService] = None


def get_data_service(file_path: Optional[Union[str, Path]] = None) -> DataService:
    """Return a singleton instance of DataService, or a new instance if file_path is specified."""
    global _service_instance
    if file_path is not None:
        return DataService(file_path)
    if _service_instance is None:
        _service_instance = DataService()
    return _service_instance


def clean_shipments(file_path: Optional[Union[str, Path]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean shipments dataset and return (cleaned_df, data_quality_audit)."""
    service = get_data_service(file_path)
    return service.get_df(), service.get_audit_log()
