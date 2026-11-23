"""Database integration module for MGH Logistics Assessment Dashboard.

Supports PostgreSQL with automated table creation, seeding from DataService,
safe read-only SQL query execution, and an SQLite fallback mirror for zero-downtime reliability.
"""

import logging
import os
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    create_engine,
    text,
)
from pathlib import Path
from sqlalchemy.engine import Engine

logger = logging.getLogger("database")

# Load environment variables from backend/.env or root .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

# Schema definition for shipments table
metadata = MetaData()

shipments_table = Table(
    "shipments",
    metadata,
    Column("shipment_id", String(50), primary_key=True),
    Column("mode", String(20), nullable=False),
    Column("container_mode", String(20), nullable=True),
    Column("carrier", String(100), nullable=False),
    Column("origin_port", String(50), nullable=False),
    Column("destination_port", String(50), nullable=False),
    Column("trade_lane", String(100), nullable=False),
    Column("shipper", String(200), nullable=False),
    Column("consignee", String(200), nullable=False),
    Column("etd", Date, nullable=True),
    Column("eta", Date, nullable=True),
    Column("atd", Date, nullable=True),
    Column("ata", Date, nullable=True),
    Column("weight_kg", Numeric, nullable=True),
    Column("volume_cbm", Numeric, nullable=True),
    Column("status", String(50), nullable=False),
    Column("delay_days", Numeric, nullable=True),
    Column("on_time", Boolean, nullable=True),
    Column("is_evaluated", Boolean, nullable=False, default=False),
    Column("ata_before_atd", Boolean, nullable=False, default=False),
    Column("data_quality_flags", Text, nullable=True),
)


class DatabaseManager:
    """Manages connection, schema creation, data seeding, and query execution."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.engine: Optional[Engine] = None
        self.db_type: str = "none"
        self._init_connection()

    def _normalize_pg_url(self, raw_url: str) -> str:
        """Clean brackets, encode password special characters, and ensure psycopg2 driver."""
        url = raw_url.strip()
        # Remove placeholder brackets if present e.g. :<password>@ -> :password@
        url = re.sub(r":<([^>]+)>@", r":\1@", url)

        # Ensure sqlalchemy uses psycopg2 driver
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)

        # Handle unescaped @ or # in password if needed
        # Pattern: postgresql+psycopg2://user:password@host:port/db
        match = re.match(r"^(postgresql\+psycopg2://)([^:]+):(.+)@([^@/]+)(/.*)$", url)
        if match:
            proto, user, raw_pass, host_port, path = match.groups()
            quoted_pass = urllib.parse.quote_plus(urllib.parse.unquote(raw_pass))
            url = f"{proto}{user}:{quoted_pass}@{host_port}{path}"

        return url

    def _init_connection(self) -> None:
        """Attempt PostgreSQL connection first, fallback to local SQLite if needed."""
        # 1. Try PostgreSQL from environment if configured
        if self.database_url and ("postgres" in self.database_url or "postgresql" in self.database_url):
            clean_url = self._normalize_pg_url(self.database_url)
            try:
                engine = create_engine(clean_url, pool_pre_ping=True)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self.engine = engine
                self.db_type = "postgres"
                self.database_url = clean_url
                logger.info("Successfully connected to PostgreSQL at %s", clean_url.split("@")[-1])
                return
            except Exception as e:
                logger.warning("Could not connect to configured PostgreSQL (%s). Falling back.", e)

        # 2. Try default local PostgreSQL if user/pass specified
        pg_user = os.getenv("PGUSER", "postgres")
        pg_pass = os.getenv("PGPASSWORD", "")
        pg_host = os.getenv("PGHOST", "localhost")
        pg_port = os.getenv("PGPORT", "5433")
        pg_db = os.getenv("PGDATABASE", "postgres")

        if pg_pass:
            quoted_pass = urllib.parse.quote_plus(pg_pass)
            for port in [pg_port, "5433", "5432"]:
                candidate_url = f"postgresql+psycopg2://{pg_user}:{quoted_pass}@{pg_host}:{port}/{pg_db}"
                try:
                    engine = create_engine(candidate_url, pool_pre_ping=True)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    self.engine = engine
                    self.db_type = "postgres"
                    self.database_url = candidate_url
                    logger.info("Successfully connected to local PostgreSQL on %s:%s", pg_host, port)
                    return
                except Exception as e:
                    logger.debug("Local PostgreSQL connection failed on port %s: %s", port, e)

        # 3. Fallback to SQLite database file in backend directory
        sqlite_path = os.path.join(os.path.dirname(__file__), "mgh_logistics.db")
        sqlite_url = f"sqlite:///{sqlite_path}"
        try:
            self.engine = create_engine(sqlite_url)
            self.db_type = "sqlite"
            self.database_url = sqlite_url
            logger.info("Initialized local SQLite mirror at %s", sqlite_path)
        except Exception as e:
            logger.error("Failed to initialize SQLite fallback: %s", e)
            self.engine = None
            self.db_type = "none"
            self.engine = None
            self.db_type = "none"

    def seed_data(self, df: pd.DataFrame) -> bool:
        """Seed clean shipment DataFrame into the database table."""
        if self.engine is None:
            return False

        try:
            # Create schema if not exists
            metadata.create_all(self.engine)

            # Map dataframe columns to database schema columns
            records = []
            for _, row in df.iterrows():
                flags = row.get("data_quality_flags")
                flags_str = ", ".join(flags) if isinstance(flags, (list, tuple)) else (str(flags) if flags is not None and str(flags) != "nan" else None)
                
                weight_val = row.get("Weight (KG)")
                vol_val = row.get("Volume (CBM)")
                delay_val = row.get("delay_days")
                ontime_val = row.get("on_time")

                rec = {
                    "shipment_id": row.get("Shipment ID"),
                    "mode": row.get("Mode"),
                    "container_mode": row.get("Container Mode") if row.get("Container Mode") is not None and str(row.get("Container Mode")) != "nan" else None,
                    "carrier": row.get("Carrier"),
                    "origin_port": row.get("Origin Port"),
                    "destination_port": row.get("Destination Port"),
                    "trade_lane": row.get("trade_lane"),
                    "shipper": row.get("Shipper"),
                    "consignee": row.get("Consignee"),
                    "etd": pd.to_datetime(row.get("ETD")).date() if row.get("ETD") is not None and str(row.get("ETD")) != "NaT" else None,
                    "eta": pd.to_datetime(row.get("ETA")).date() if row.get("ETA") is not None and str(row.get("ETA")) != "NaT" else None,
                    "atd": pd.to_datetime(row.get("ATD")).date() if row.get("ATD") is not None and str(row.get("ATD")) != "NaT" else None,
                    "ata": pd.to_datetime(row.get("ATA")).date() if row.get("ATA") is not None and str(row.get("ATA")) != "NaT" else None,
                    "weight_kg": float(weight_val) if weight_val is not None and not (isinstance(weight_val, float) and pd.isna(weight_val)) else None,
                    "volume_cbm": float(vol_val) if vol_val is not None and not (isinstance(vol_val, float) and pd.isna(vol_val)) else None,
                    "status": row.get("Status"),
                    "delay_days": float(delay_val) if delay_val is not None and not (isinstance(delay_val, float) and pd.isna(delay_val)) else None,
                    "on_time": bool(ontime_val) if ontime_val is not None and not (isinstance(ontime_val, float) and pd.isna(ontime_val)) else None,
                    "is_evaluated": bool(row.get("is_evaluated", False)),
                    "ata_before_atd": bool(row.get("ata_before_atd", False)),
                    "data_quality_flags": flags_str,
                }
                records.append(rec)

            with self.engine.begin() as conn:
                # Clear existing and insert clean rows
                conn.execute(text("DELETE FROM shipments;"))
                conn.execute(shipments_table.insert(), records)

            logger.info("Successfully seeded %d shipments into %s table.", len(records), self.db_type)
            return True
        except Exception as e:
            logger.error("Failed to seed database: %s", e)
            return False

    def execute_sql(self, sql_query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Safely execute a read-only SQL SELECT query against the active database."""
        if self.engine is None:
            raise RuntimeError("Database engine is not connected.")

        # Clean query string
        query = sql_query.strip().rstrip(";")

        # Security check: disallow modifying queries
        disallowed_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE", "CREATE", "GRANT", "REVOKE"
        ]
        upper_query = query.upper()
        for kw in disallowed_keywords:
            if re.search(rf"\b{kw}\b", upper_query):
                raise ValueError(f"Security error: Query contains disallowed keyword '{kw}'. Read-only SELECT queries only.")

        # Ensure query starts with SELECT or WITH
        if not (upper_query.startswith("SELECT") or upper_query.startswith("WITH")):
            raise ValueError("Query must start with SELECT or WITH.")

        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchmany(100)]
            return rows, columns


# Singleton
_db_manager_instance: Optional[DatabaseManager] = None


def get_db_manager(database_url: Optional[str] = None) -> DatabaseManager:
    """Return singleton DatabaseManager instance."""
    global _db_manager_instance
    if _db_manager_instance is None or database_url:
        _db_manager_instance = DatabaseManager(database_url=database_url)
    return _db_manager_instance
