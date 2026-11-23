"""FastAPI application for MGH Logistics Assessment Dashboard.

Exposes RESTful APIs for KPI summaries, trade lanes, shipments query/filter,
and natural language query grounding ("Ask the Data").
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .data_service import DataService, get_data_service, sanitize_for_json
from .database import DatabaseManager, get_db_manager
from .qa_engine import QAEngine, get_qa_engine
from .schemas import (
    AskRequest,
    AskResponse,
    ShipmentItem,
    SummaryResponse,
    TopDelayedItem,
    TradeLaneItem,
)

# Global service singletons
data_service: Optional[DataService] = None
db_manager: Optional[DatabaseManager] = None
qa_engine: Optional[QAEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load and clean shipment CSV data and seed database once at startup."""
    global data_service, db_manager, qa_engine
    data_service = get_data_service()
    db_manager = get_db_manager()
    db_manager.seed_data(data_service.get_df())
    # Initialize QA engine with database manager
    qa_engine = get_qa_engine(data_service, db_manager=db_manager)
    yield


app = FastAPI(
    title="MGH Logistics Assessment API",
    description="High-performance logistics analytics and Ask-the-Data backend powered by FastAPI & Gemini.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/summary", response_model=SummaryResponse, tags=["Dashboard"])
def get_summary() -> Dict[str, Any]:
    """Retrieve high-level KPIs and data quality audit metrics."""
    ds = data_service or get_data_service()
    kpis = ds.get_kpis()
    audit = ds.get_audit_log()
    return {**kpis, "data_quality_audit": audit}


@app.get("/api/trade-lanes", response_model=List[TradeLaneItem], tags=["Dashboard"])
def get_trade_lanes() -> List[Dict[str, Any]]:
    """Retrieve aggregated trade lane performance ranked by shipment volume."""
    ds = data_service or get_data_service()
    return ds.get_trade_lanes()


@app.get("/api/top-delayed", response_model=List[TopDelayedItem], tags=["Dashboard"])
def get_top_delayed(limit: int = Query(default=10, ge=1, le=100)) -> List[Dict[str, Any]]:
    """Retrieve the top delayed shipments ranked by delay_days descending."""
    ds = data_service or get_data_service()
    df = ds.get_df()

    # Filter evaluated shipments with positive delay
    eval_df = df[(df["is_evaluated"] == True) & (df["delay_days"] > 0)]
    top_df = eval_df.sort_values(by="delay_days", ascending=False).head(limit)

    export_cols = [
        "Shipment ID",
        "delay_days",
        "Carrier",
        "trade_lane",
        "Mode",
        "Status",
        "ETD",
        "ETA",
        "ATD",
        "ATA",
        "Weight (KG)",
        "Consignee",
        "Shipper",
    ]
    records = top_df[export_cols].to_dict(orient="records")
    return sanitize_for_json(records)


@app.get("/api/shipments", response_model=List[ShipmentItem], tags=["Shipments"])
def get_shipments(
    response: Response,
    q: Optional[str] = Query(default=None, description="Search across ID, parties, ports, carrier"),
    mode: Optional[str] = Query(default=None, description="Filter by Mode (SEA, AIR)"),
    carrier: Optional[str] = Query(default=None, description="Filter by Carrier"),
    status: Optional[str] = Query(default=None, description="Filter by Status (Delivered, In Transit)"),
    trade_lane: Optional[str] = Query(default=None, description="Filter by trade lane"),
    limit: Optional[int] = Query(default=None, ge=1, le=1000, description="Pagination limit"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
) -> List[Dict[str, Any]]:
    """Query and filter shipments dataset with text search and pagination."""
    ds = data_service or get_data_service()
    df = ds.get_df().copy()

    # Text search
    if q and q.strip():
        term = q.strip().lower()
        search_mask = (
            df["Shipment ID"].str.lower().str.contains(term, na=False)
            | df["Shipper"].str.lower().str.contains(term, na=False)
            | df["Consignee"].str.lower().str.contains(term, na=False)
            | df["Carrier"].str.lower().str.contains(term, na=False)
            | df["Origin Port"].str.lower().str.contains(term, na=False)
            | df["Destination Port"].str.lower().str.contains(term, na=False)
            | df["trade_lane"].str.lower().str.contains(term, na=False)
        )
        df = df[search_mask]

    # Mode filter
    if mode and mode.strip():
        df = df[df["Mode"].str.upper() == mode.strip().upper()]

    # Carrier filter
    if carrier and carrier.strip():
        df = df[df["Carrier"].str.upper() == carrier.strip().upper()]

    # Status filter
    if status and status.strip():
        df = df[df["Status"].str.lower() == status.strip().lower()]

    # Trade lane filter
    if trade_lane and trade_lane.strip():
        df = df[df["trade_lane"] == trade_lane.strip()]

    total_count = len(df)
    response.headers["X-Total-Count"] = str(total_count)

    # Pagination
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


@app.get("/api/shipments/{shipment_id}", response_model=ShipmentItem, tags=["Shipments"])
def get_shipment_by_id(shipment_id: str) -> Dict[str, Any]:
    """Retrieve detailed record for a specific Shipment ID."""
    ds = data_service or get_data_service()
    df = ds.get_df()

    matches = df[df["Shipment ID"].str.upper() == shipment_id.strip().upper()]
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"Shipment with ID '{shipment_id}' not found")

    row = matches.iloc[0]
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
    record = row[columns_to_export].to_dict()
    return sanitize_for_json(record)


@app.post("/api/ask", response_model=AskResponse, tags=["Ask the Data"])
def ask_the_data(request: AskRequest) -> Dict[str, Any]:
    """Milestone 3: Grounded Synthesis Natural Language Query powered by Gemini API."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    engine = qa_engine or get_qa_engine(data_service, db_manager=db_manager or get_db_manager())
    result = engine.ask(request.question)
    return sanitize_for_json(result)


# Mount frontend single-page application static files when built
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if frontend_dist.exists():
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_root():
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Do not catch API or documentation routes
        if (
            full_path.startswith("api/")
            or full_path == "api"
            or full_path.startswith("docs")
            or full_path.startswith("openapi.json")
            or full_path.startswith("redoc")
        ):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))

