# MGH Freight Visibility Dashboard — 2026 H1

A production-grade, executive-ready Freight Visibility Dashboard built with **FastAPI (Python/Pandas)** and **React (Vite + Tailwind CSS + Recharts + Lucide Icons)**.

---

## 1. Executive Summary & Key Verified Numbers

| Metric | Verified Value | Operational Context |
| :--- | :--- | :--- |
| **Total Raw Ingestion** | **511 rows** | Raw CSV intake (`shipments_2026H1.csv`) |
| **Unique Shipments** | **500 shipments** | Deduplicated preserving Delivered & verified ATA records |
| **Evaluated Shipments** | **450 shipments** | 50 excluded (44 null ATA, 6 impossible arrivals ATA < ATD) |
| **On-Time Shipments** | **260 shipments** | `delay_days <= 0` against scheduled ETA |
| **On-Time Delivery Rate** | **57.78%** | Exact ratio: `260 / 450` evaluated shipments |
| **Total Cleaned Weight** | **6,648,333.5 kg** | `~6,648.3 MT` (non-positive zeroed; grams typo rescaled) |
| **Total Cargo Volume** | **18,157.01 CBM** | Across all container and breakbulk modes |
| **Average Schedule Delay** | **1.80 days** | Across evaluated shipments |
| **Top Trade Lane** | **`BDCGP → ESVLC`** | **77 shipments** (57.14% on-time, 1.48 days avg delay) |
| **#1 Most Delayed Shipment** | **`S00158545`** | **+26 days delay** (ONE line on `BDCGP → USNYC`) |
| **Active Fleet in Transit** | **42 shipments** | 458 delivered (91.6% completed) |

---

## 2. Data Quality Audit & Remediation Log

The data pipeline in [`backend/data_service.py`](backend/data_service.py) enforces **9 automated cleaning rules** before any analytical consumption:

| # | Anomaly / Rule | Caught Count | Root Cause & Heuristic Resolution | Verified Impact |
| :---: | :--- | :---: | :--- | :--- |
| **1** | **Duplicate Shipment IDs** | **11 rows** | Multiple sync events for same shipment. Sorted so `Status == 'Delivered'` and non-null `ATA` come first; dropped duplicate IDs keeping the first record. | Fleet reduced from 511 to exactly **500 unique shipments**. |
| **2** | **Port Name Inconsistencies** | **24 rows** | Mixed casing, whitespace padding, and colloquial naming (`bdcgp`, `Chattogram`, `CGP`). Normalized all variants to canonical `BDCGP` and uppercased all destination ports. | Clean trade lane grouping (e.g. `BDCGP → ESVLC` with 77 shipments). |
| **3** | **Corrupt Year Typo** | **1 row** | Shipment `S00158650` recorded with `2/19/2062` due to clerical keying error. Replaced `/2062` with `/2026`. | Restored accurate 2-day delivery variance. |
| **4** | **Ambiguous Date Parsing** | **216 dates** | Slash dates where `p1 <= 12` and `p2 <= 12`. Disambiguated `M/D/Y` vs `D/M/Y` against departure dates (`ETD`/`ATD`) using mode-specific transit windows (`AIR`: 0–15d, `CNSHA→BDCGP`: 7–35d, other `SEA`: 15–65d). | Prevented spurious 5-month transit errors on air cargo and ocean liners. |
| **5** | **Impossible Arrivals** | **6 rows** | Identified records where arrival occurred before departure (`ATA < ATD`): `S00159115`, `S00158459`, `S00159174`, `S00158864`, `S00159407`, `S00158304`. Flagged as `ata_before_atd` and excluded from SLA scoring. | Prevented distorted negative delays from artificially inflating SLA metrics. |
| **6** | **Non-Positive Cargo Weights** | **5 rows** | Corrupted negative weights (e.g. `-12,406.9 kg`) and zero entries. Flagged as `weight_zero_or_negative` and set cleaned weight to `None`. | Preserved mathematical integrity of freight weight aggregations. |
| **7** | **Weight Unit Scale Typo** | **1 row** | Shipment `S00158128` recorded as `21,816,000 kg` (entered in grams). Rescaled by `÷ 1,000` to `21,816.0 kg`. | Total cleaned fleet weight matches verified **6,648,333.5 kg**. |
| **8** | **Missing Consignees** | **7 rows** | Missing or whitespace-only consignee names. Imputed with `'Unknown'` placeholder. | Prevented front-end table filter crashes and orphaned shipments. |
| **9** | **Status Mismatches** | **10 rows** | 6 `Delivered` shipments with missing `ATA` and 4 `In Transit` shipments with present `ATA`. Logged into `data_quality_flags`. | Full operational auditability for billing and dispatch reconciliation. |

---

## 3. Architecture & Architectural Decision Records (ADR)

```
┌─────────────────────────────────────────────────────────────┐
│                       React Frontend                        │
│   (Vite + Tailwind CSS + Recharts + Text-to-SQL Preview)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON (Port 8000)
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI REST API Server                  │
│       CORS Enabled • Pydantic Contracts • JSON-Sanitized    │
├──────────────────────────────┬──────────────────────────────┤
│      backend/schemas.py      │       backend/main.py        │
│  (Strict Response Models)    │  (Lifespan Cache & Endpoints)│
├──────────────────────────────┼──────────────────────────────┤
│    backend/qa_engine.py      │    backend/database.py       │
│  (Gemini Text-to-SQL +       │  (PostgreSQL + SQLAlchemy 2  │
│   Database Query Execution)  │   + Safe Read-Only Runner)   │
├──────────────────────────────┴──────────────────────────────┤
│                   backend/data_service.py                   │
│  (Pandas Ingestion Pipeline, Heuristics & Data Seeding)     │
└─────────────────────────────────────────────────────────────┘
```

### ADR 1: FastAPI (Python/Pandas) for Logistics Backend
- **Context:** Logistics data requires fast tabular vector manipulation, heuristic date resolution, and statistical aggregation.
- **Decision:** Utilize FastAPI with Pandas. FastAPI delivers asynchronous ASGI performance, automatic OpenAPI documentation, and strict Pydantic serialization. Pandas provides sub-millisecond vectorized filtering over the 500-shipment dataset.

### ADR 2: SOLID & Separation of Concerns
- **Data Layer (`backend/data_service.py`):** Encapsulates deduplication, port normalization, heuristic transit window algorithms, and weight unit cleaning.
- **Database Layer (`backend/database.py`):** Manages connection to PostgreSQL via SQLAlchemy 2.0, auto-seeds the cleaned 500 shipments into the `shipments` table, enforces strict read-only execution security (disallowing `DROP`, `DELETE`, `UPDATE`, `INSERT`), and provides a zero-downtime local mirror.
- **Contract Layer (`backend/schemas.py`):** Pydantic schemas enforce type safety and decoupling. All fields support both camelCase and original CSV column aliases, and includes `generated_sql` and `sql_rows`.
- **Intelligence Layer (`backend/qa_engine.py`):** Executes an end-to-end Text-to-SQL workflow: Gemini generates an exact PostgreSQL `SELECT` query given the database schema, executes it directly against the database, and synthesizes an executive grounded answer backed by returned rows.
- **Transport Layer (`backend/main.py`):** Handles HTTP, status codes, query filtering, database seeding on lifespan startup, and SPA static hosting.

### ADR 3: Grounded Text-to-SQL with Deterministic Fallback
- **Problem:** LLMs are prone to numerical hallucinations when answering open-ended logistical questions.
- **Solution:** 
  1. **Schema-Aware Text-to-SQL:** Natural language queries are translated into a read-only PostgreSQL `SELECT` query against the `shipments` table.
  2. **Live Database Execution:** The SQL query is safely executed against the database, returning exact matching rows.
  3. **Grounded Synthesis:** Gemini synthesizes a concise executive answer grounded directly in the live SQL results.
  4. **Full Offline Fallback:** If API quotas or network limits are encountered, a deterministic SQL generator produces the exact query, executes it on the database, and returns verified metrics with zero downtime.

---

## 4. Local Setup & Execution Guide

### Prerequisites
- **Python 3.10+** (Python 3.13 tested)
- **Node.js 18+** (Node v23.1.0 tested) and `npm`

### 4.1 Quickstart (Unified Single-Host Serving — Recommended)
Both the React frontend and FastAPI backend run together seamlessly on the same host and port (`http://localhost:8000`):

#### On Windows:
Double-click or run:
```powershell
.\start.bat
# or in PowerShell:
.\start.ps1
```
This automatically builds `frontend/dist` (if not already built) and launches the unified server at **`http://localhost:8000`**.

#### Manual One-Liner (Cross-Platform):
```bash
# 1. Build frontend once
cd frontend && npm install && npm run build && cd ..

# 2. Run unified server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Unified Web Dashboard:** `http://localhost:8000`
- **FastAPI Interactive Docs (Swagger):** `http://localhost:8000/docs`
- **FastAPI Alternative Docs (ReDoc):** `http://localhost:8000/redoc`

---

### 4.2 Independent Development Mode (Hot-Reloading)
For active UI development with Vite hot module replacement (HMR):
```bash
# Terminal 1 - Backend API:
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 - Vite Dev Server:
cd frontend
npm run dev
```
- Vite HMR UI: `http://localhost:5173` (proxies `/api` to `http://localhost:8000`)

---

### 4.3 PostgreSQL Configuration (Optional)
The system automatically connects to PostgreSQL if credentials are provided in `backend/.env`. If omitted, it automatically falls back to an internal SQLite mirror with identical schema and zero downtime:
```env
# backend/.env
GEMINI_API_KEY=your_gemini_api_key

# PostgreSQL Connection (via standard URI or individual parameters):
DATABASE_URL=postgresql://postgres:password@localhost:5432/mgh_logistics
# or
PGUSER=postgres
PGPASSWORD=your_password
PGHOST=localhost
PGPORT=5432
PGDATABASE=postgres
```

---

### 4.4 Running Test Suite
```bash
# Run all 23 data quality, heuristic, smoke, and database tests
pytest backend/ -v
```

---

## 5. API Reference

| Method | Endpoint | Description | Sample Query / Payload |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/summary` | Overall KPIs & 9-rule Data Quality Audit | — |
| `GET` | `/api/trade-lanes` | Aggregated trade lane volumes & on-time rates | — |
| `GET` | `/api/top-delayed` | Top delayed shipments ranked by delay days | `?limit=10` |
| `GET` | `/api/shipments` | Search & filter shipments across ID, parties, ports | `?q=S00158545&mode=SEA&status=Delivered` |
| `GET` | `/api/shipments/{id}` | Complete 15-field record with delay & flags | `/api/shipments/S00158545` |
| `POST` | `/api/ask` | Milestone 3 Grounded Natural Language Query | `{"question": "which carrier is delayed the most?"}` |

---

## 6. Next 2 Days Roadmap (Production Readiness)

1. **Persistent Relational Database & Caching:**
   - Migrate from in-memory CSV/Pandas to **PostgreSQL** managed by SQLAlchemy 2.0 and Alembic migrations.
   - Introduce **Redis** cache for pre-aggregated trade lane statistics and KPI summaries with 5-minute TTL.

2. **Automated Ingestion & Validation Pipeline:**
   - Implement **Great Expectations** or **Pydantic V2** streaming validators for incoming EDI / CSV batches.
   - Automated quarantine bucket for corrupt files and impossible arrival timestamps.

3. **Enterprise Security & Access Control (RBAC):**
   - Implement OAuth2 / OIDC authentication (Okta / Azure AD).
   - Role-Based Access Control: *Executives* (aggregate KPI views), *Dispatchers* (full shipment editing), *Auditors* (read-only audit logs).

4. **Real-Time Carrier Webhooks & Event-Driven Alerts:**
   - Ingest real-time milestone webhooks (AIS vessel tracking, air waybill milestone pings).
   - Automated Slack / Email notifications when a critical shipment delay exceeds 3 days.

5. **CI/CD & Observability:**
   - GitHub Actions pipeline running `pytest`, `flake8`, `npm run build`, and security vulnerability scans on every push.
   - Containerized multi-stage Docker builds (`Dockerfile` for backend and frontend) deployed to AWS ECS / Cloud Run with OpenTelemetry distributed tracing.
