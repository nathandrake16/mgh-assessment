"""Pydantic schemas and response models for the Logistics Dashboard API."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with alias population and JSON serialization configuration."""
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"
    )


class DataQualityAudit(BaseSchema):
    """Data quality audit anomaly counts."""
    total_raw_rows: int
    unique_shipments: int
    duplicates_removed: int
    ports_normalized: int
    year_typo_fixed: int
    ambiguous_dates_resolved: int
    ata_before_atd: int
    weight_non_positive: int
    weight_grams_typo_corrected: int
    missing_consignee_filled: int
    delivered_missing_ata: int
    in_transit_with_ata: int
    evaluated_shipments: int
    on_time_shipments: int


class SummaryResponse(BaseSchema):
    """High-level KPIs and data quality metrics for the dashboard."""
    total_shipments: int
    evaluated_shipments: int
    on_time_shipments: int
    on_time_percentage: float
    total_weight_kg: float
    total_volume_cbm: float
    average_delay_days: float
    top_trade_lane: str
    top_trade_lane_shipments: int
    most_delayed_shipment_id: Optional[str] = None
    most_delayed_days: Optional[int] = None
    data_quality_audit: Dict[str, Any]


class TradeLaneItem(BaseSchema):
    """Aggregated trade lane performance item."""
    trade_lane: str
    origin_port: str
    destination_port: str
    total_shipments: int
    evaluated_shipments: int
    on_time_shipments: int
    on_time_percentage: Optional[float] = None
    average_delay_days: Optional[float] = None
    total_weight_kg: float
    total_volume_cbm: float


class ShipmentItem(BaseSchema):
    """Detailed shipment item schema."""
    shipment_id: str = Field(..., alias="Shipment ID")
    mode: str = Field(..., alias="Mode")
    container_mode: str = Field(..., alias="Container Mode")
    carrier: str = Field(..., alias="Carrier")
    origin_port: str = Field(..., alias="Origin Port")
    destination_port: str = Field(..., alias="Destination Port")
    trade_lane: str
    shipper: str = Field(..., alias="Shipper")
    consignee: str = Field(..., alias="Consignee")
    etd: Optional[str] = Field(None, alias="ETD")
    eta: Optional[str] = Field(None, alias="ETA")
    atd: Optional[str] = Field(None, alias="ATD")
    ata: Optional[str] = Field(None, alias="ATA")
    weight_kg: Optional[float] = Field(None, alias="Weight (KG)")
    volume_cbm: Optional[float] = Field(None, alias="Volume (CBM)")
    status: str = Field(..., alias="Status")
    delay_days: Optional[int] = None
    on_time: Optional[bool] = None
    is_evaluated: bool = False
    ata_before_atd: bool = False
    data_quality_flags: List[str] = Field(default_factory=list)


class TopDelayedItem(BaseSchema):
    """Representation of a delayed shipment."""
    shipment_id: str = Field(..., alias="Shipment ID")
    delay_days: int
    carrier: str = Field(..., alias="Carrier")
    trade_lane: str
    mode: str = Field(..., alias="Mode")
    status: str = Field(..., alias="Status")
    etd: Optional[str] = Field(None, alias="ETD")
    eta: Optional[str] = Field(None, alias="ETA")
    atd: Optional[str] = Field(None, alias="ATD")
    ata: Optional[str] = Field(None, alias="ATA")
    weight_kg: Optional[float] = Field(None, alias="Weight (KG)")
    consignee: str = Field(..., alias="Consignee")
    shipper: str = Field(..., alias="Shipper")


class ShipmentsListResponse(BaseSchema):
    """Paginated list of shipments with total count."""
    total: int
    items: List[ShipmentItem]
    limit: Optional[int] = None
    offset: int = 0


class AskRequest(BaseSchema):
    """Request payload for Milestone 3 'Ask the Data'."""
    question: str


class SupportingDataItem(BaseSchema):
    """Grounding key-value pair for Milestone 3 synthesis."""
    label: str
    value: Union[str, int, float, bool, None]


class AskResponse(BaseSchema):
    """Grounded AI response containing natural language answer and supporting metrics."""
    answer: str
    supporting_data: List[SupportingDataItem] = Field(default_factory=list)
    engine: str = Field(..., description="gemini-3.8-flash or deterministic_fallback")
