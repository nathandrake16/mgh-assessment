# MGH Freight Visibility Dashboard (2026 H1)
## Executive Walkthrough & Presentation Guide

This guide is structured for delivering a polished, high-impact **7–10 minute presentation** of the **MGH Freight Visibility Platform** to both **Executive Leadership** (business value, SLA governance, operational visibility) and **Technical Evaluators** (data engineering heuristics, API design, grounded AI synthesis, system architecture).

---

## 1. Presentation Structure & Timing Blueprint

| Phase | Duration | Core Goal | Anchor Visual / Action |
| :--- | :---: | :--- | :--- |
| **1. Hook & Business Context** | 1.0 min | Define the problem: operational opacity in cross-border freight | Headline KPI summary & scope |
| **2. Data Engineering & Quality** | 2.0 min | Showcase senior engineering rigor: 9 cleaning rules & heuristics | Data Quality Audit Drawer (9 fixes) |
| **3. Live Application Walkthrough** | 3.5 min | Prove live working software on unified port 8000 | Interactive demo at `http://localhost:8000` |
| **4. Architecture & AI Grounding** | 1.5 min | Explain FastAPI + React stack & grounded GenAI design | System Architecture diagram & API Docs |
| **5. 2-Day Roadmap & Wrap-up** | 1.0 min | Demonstrate forward-deployed production roadmap | Production readiness & strategic Q&A |

---

## 2. Word-for-Word Spoken Script

### Phase 1: The Hook & Business Problem (1.0 Minute)

> *"Good morning, everyone. Today, I am presenting the **MGH Global Freight Visibility Dashboard** for the first half of 2026.*
>
> *At MGH Logistics, managing cross-border supply chains across South Asia, Europe, and North America requires precise schedule control. However, operations teams were struggling with **operational opacity**. Regional transport hubs and carrier EDI feeds were producing raw, uncleaned shipment logs fraught with real-world anomalies: duplicated records, mixed date conventions, impossible arrival timestamps, and miskeyed weights.*
>
> *If an executive looks at uncleaned data, they get distorted delivery SLAs and inaccurate freight volume calculations. Rather than treating this as a simple UI task, I approached this with a **Forward-Deployed Engineering mindset**: first building an automated data cleansing engine with strict mathematical heuristics, locking in verified numbers via 20 automated tests, and deploying a single-host, production-ready analytics dashboard powered by FastAPI, React, and Grounded Gemini AI.*
>
> *Let's look at what our data pipeline uncovered."*

---

### Phase 2: Data Quality & Engineering Heuristics (2.0 Minutes)

> *"When ingesting the raw 511-row shipment intake in `shipments_2026H1.csv`, my data service implemented **9 automated cleaning rules** before any analytical consumption:*
>
> 1. **Deduplication:** We identified 11 duplicate shipment syncs. By prioritizing records marked `Delivered` with recorded actual arrival dates (`ATA`), we deduplicated the dataset to exactly **500 unique shipments**.
> 2. **Port Aliases:** Origin ports had mixed casing and colloquial aliases like `bdcgp`, `Chattogram`, and `CGP`. We normalized all 24 instances to canonical `BDCGP` and uppercased destination ports, enabling clean trade lane grouping.
> 3. **Smart Mode-Specific Date Parsing:** Standard parsers fail on international dates where month and day are both 12 or less. For 216 ambiguous dates, our algorithm resolved `M/D/Y` versus `D/M/Y` by testing candidate arrival dates against departure dates using **mode-specific transit windows**: 0 to 15 days for Air Cargo, 7 to 35 days for China-to-Bangladesh sea feeders, and 15 to 65 days for deep-sea container lines.
> 4. **Impossible Arrivals (SLA Integrity):** We flagged 6 records where the recorded arrival preceded actual departure (`ATA < ATD`), such as shipment `S00159115`. Including these would produce artificial negative delays and corrupt executive SLA reports. We excluded them from delay scoring, yielding an exact verified **57.78% on-time delivery rate (260 on-time out of 450 evaluated shipments)**.
> 5. **Weight Unit Rescaling:** Shipment `S00158128` was entered as 21,816,000 kg due to a grams-entry clerical error. Our engine flagged values over 100,000 kg and divided by 1,000, while zeroing 5 non-positive weights. This established our verified fleet weight of **6,648,333.5 kg (~6,648.3 MT)**.
>
> *Every single fix is tracked in an automated audit trail. Now, let’s see the live system in action."*

---

### Phase 3: Live Dashboard Walkthrough (3.5 Minutes)

*(Switch to your browser open at `http://localhost:8000`)*

#### Step 1: Headline KPI Cards
> *"Here is the live dashboard running locally on unified port 8000. At the very top, operations leadership receives immediate visibility into high-level performance:*
> - **Total Unique Shipments:** **500** (with an audit sub-badge indicating 511 raw rows and 11 duplicates dropped).
> - **On-Time Delivery Rate:** **57.78%** across the 450 evaluated shipments (excluding 44 in-transit without ATA and the 6 impossible arrivals).
> - **Total Cleaned Cargo Weight:** **6,648.3 Metric Tons** alongside 18,157 CBM in volume.
> - **Fleet Status:** **42 Active Shipments In Transit** and 458 delivered.*"

#### Step 2: Trade Lanes Distribution
*(Scroll to the **Shipments per Trade Lane** section)*
> *"Our trade lane analysis dynamically aggregates shipment corridors:*
> - *The horizontal bar chart immediately spotlights **`BDCGP → ESVLC` (Chittagong to Valencia)** as our #1 highest-volume corridor, carrying **77 shipments**.*
> - *When I toggle to the **All Lanes Table**, leadership can audit all 15 corridors with volume, on-time percentage, average delay, and total weight. For example, Valencia maintains a 57.1% on-time rate with an average schedule delay of just 1.48 days, while Rotterdam (`BDCGP → NLRTM`) carries 70 shipments at a 44.3% on-time rate.*"

#### Step 3: Actionable Exception Management (Top 10 Delayed Shipments)
*(Point to the **Top 10 Most Delayed Shipments** table)*
> *"Rather than drowning dispatchers in tables, the dashboard isolates critical delivery defects:*
> - *The #1 most delayed shipment across the entire global network is **`S00158545`**, operated by container line **ONE** on the `BDCGP → USNYC` corridor, with a **+26-day delay**.*
> - *Let's click on `S00158545` to open the **15-Field Operational Deep Dive Inspector**."*
> 
*(Click row `S00158545`)*
> 
> *"In this modal, dispatchers see every operational parameter: ETD March 28 vs ATD March 29; ETA May 6 vs actual arrival June 1. It also displays cargo specs—15,357 kg, 35.5 CBM—the trading parties (Meghna Fashion Wear to Rhein Textil), and the exact data quality intervention badge confirming ambiguous date resolution. Let's close the inspector."*

#### Step 4: Milestone 3 — "Ask the Data" (Grounded AI Synthesis)
*(Scroll to the **Milestone 3 — Ask the Data** section)*
> *"A key differentiator of this platform is our natural language grounding engine. Operations executives don't always have time to filter tables—they want immediate answers to business questions.*
> - *Let's click the sample prompt: **'Which carrier is delayed the most?'** and click Ask."*
> 
*(Click 'Which carrier is delayed the most?')*
> 
> *"Notice the response:*
> - *The system returns an executive grounded summary: in Air Cargo, **EMIRATES SKYCARGO** experienced the highest average delay at **6.83 days**. In Ocean Cargo, **MSC** experienced the highest average delay at **2.57 days** (29 delayed shipments), closely followed by **MAERSK** (2.19 days) and **EVERGREEN** (2.18 days).*
> - *It calls out that carrier **ONE** holds the single most delayed shipment (`S00158545` at +26 days).*
> - *Below the grounded narrative, the UI renders **4 Verified Supporting Metric Cards** displaying exact statistics.*
> - *Notice the engine badge: if the Gemini API is live, it generates natural language synthesis; if an API quota or timeout occurs, our **local deterministic Pandas intent parser** seamlessly steps in with zero downtime."*

#### Step 5: Data Quality Audit Drawer
*(Click the **Data Quality Audit (9 Fixes)** button in the top header)*
> *"Finally, true enterprise software requires full transparency. Clicking the header button slides out our **Data Quality Audit Drawer**.*
> *Here, auditors and data engineers can inspect all 9 automated fixes: 11 duplicates dropped, 24 ports normalized, 1 corrupt year typo fixed (2062 to 2026), 216 ambiguous dates resolved, 6 impossible arrivals quarantined, 5 non-positive weights cleaned, 1 grams unit error rescaled, 7 missing consignees imputed, and 10 status mismatches flagged.*
> *This guarantees complete auditability for billing and compliance."*

---

### Phase 4: Architecture Rationale & Engineering Rigor (1.5 Minutes)

> *"Under the hood, three architectural decisions make this system robust:*
> 
> 1. **FastAPI + Pandas for High-Performance Vectorized Processing:**
>    - Logistics calculations require fast tabular operations. Pandas computes our entire 500-shipment deduplication, date resolution, and KPI aggregations in under 25 milliseconds at startup.
>    - FastAPI provides asynchronous execution, native OpenAPI documentation at `/docs`, and strict Pydantic schemas that enforce schema safety with zero NaN leakage.
> 
> 2. **Single-Host Unified Serving:**
>    - Rather than forcing operators to maintain two separate servers and navigate CORS configurations, the FastAPI backend mounts the production React build and serves both the dashboard and API on the same host (`http://localhost:8000`).
> 
> 3. **Defensive Testing Suite:**
>    - We codified every business rule and API endpoint into **20 automated Pytest tests** covering port mapping, SLA percentages, weight rescaling, and SPA serving—all passing in 6.2 seconds.*"

---

### Phase 5: Next 2 Days Production Roadmap (1.0 Minute)

> *"If given 2 more days to take this MVP into an enterprise production deployment, my roadmap focuses on four pillars:*
> 
> 1. **Database Migration & Caching:** Migrate from in-memory CSV/Pandas to **PostgreSQL** with SQLAlchemy 2.0 and Redis for 5-minute cached trade lane summaries.
> 2. **Streaming Ingestion & Data Quality Quarantine:** Replace batch ingestion with **Pydantic V2 / Great Expectations** validation pipelines that automatically isolate corrupted EDI files into an S3 quarantine bucket.
> 3. **Role-Based Access Control (RBAC):** Integrate Okta/Azure AD SSO with granular roles (Executives see aggregated KPIs; Dispatchers have shipment editing permissions; Auditors have read-only access to cleaning logs).
> 4. **Carrier Webhooks & Alerting:** Integrate live AIS vessel tracking and automated Slack/Email webhooks triggering whenever a shipment exceeds a 3-day delay threshold.*"

---

## 3. Anticipated Questions & Battle-Tested Answers

### A. Business & Problem-Solving Questions

#### Q1: "Why did you exclude the 6 shipments with ATA < ATD from on-time calculations?"
> **Answer:** *"In logistics data, an arrival timestamp earlier than departure is physically impossible—it usually indicates a clerical inversion or an unadjusted timezone rollover. If we treated them as on-time, they would contribute artificial negative delays (e.g. -144 days) that skew the fleet average delay and provide a false sense of SLA compliance. Quarantining them preserves the mathematical validity of our **57.78% on-time metric** while recording them in the audit drawer for dispatcher review."*

#### Q2: "How did you resolve dates where both numbers were 12 or less (e.g., 04/05/2026)?"
> **Answer:** *"A naive parser either forces MM/DD or DD/MM, creating spurious 5-month shipping delays. Our algorithm uses domain heuristics: it looks at the departure timestamp (`ETD`/`ATD`) and transportation mode. Air freight has an expected transit window of 0 to 15 days; China-to-Bangladesh feeder vessels take 7 to 35 days; deep-sea ocean routes take 15 to 65 days. The parser calculates the transit duration under both interpretations and selects the candidate that falls inside the plausible window."*

#### Q3: "What business impact does this dashboard offer compared to Excel sheets?"
> **Answer:** *"It replaces fragmented, multi-day manual reporting with instant operational decision-making. Operations leadership can immediately identify that Ocean Line MSC is averaging 2.57 days in delay across 29 shipments, and that Rotterdam and Valencia corridors represent over 29% of our global volume. This enables proactive carrier renegotiation and dynamic modal shifts from ocean to air cargo before SLA penalties hit."*

---

### B. Technical & Architectural Questions

#### Q1: "How do you prevent Gemini from hallucinating logistics numbers?"
> **Answer:** *"We use Grounded AI Synthesis with a strict three-tier defense:
> 1. The LLM is never given raw uncurated data; it receives pre-aggregated, verified JSON summaries generated directly by Pandas.
> 2. If a specific shipment ID is mentioned (e.g. `S00158545`), that exact 15-field record is injected into the context prompt.
> 3. We enforce strict JSON output schemas with verified metrics cards. If any API rate limit or outage occurs, our local deterministic parser executes regex-based intent extraction and answers with zero hallucination risk."*

#### Q2: "Why choose single-host hosting over microservice separation?"
> **Answer:** *"For an operational evaluation and containerized cloud deployment, single-host serving simplifies deployment topology. Operators can launch one container image without configuring cross-origin resource sharing (CORS), reverse proxy headers, or maintaining separate host configurations. For local development, the Vite dev server with proxy remains fully supported."*

#### Q3: "How would you scale this architecture to 10 million shipments?"
> **Answer:** *"In-memory Pandas is ideal for sub-second analysis of batches up to several hundred thousand rows. For 10M+ rows, we would:
> - Move data storage to a columnar relational database like **ClickHouse** or **PostgreSQL with TimescaleDB**.
> - Pre-aggregate hourly and daily corridor metrics into materialized views.
> - Implement cursor-based pagination and database-level text indexing (Trigram / Full-Text Search) for sub-50ms search across consignees and shipment IDs."*

---

## 4. Live Demo Quick-Reference Cheat Sheet

| Metric | Verified Value | Operational Context |
| :--- | :--- | :--- |
| **Total Ingestion** | `511 rows` | Raw intake from `shipments_2026H1.csv` |
| **Unique Shipments** | `500` | 11 duplicate IDs dropped |
| **Evaluated Shipments** | `450` | 44 null ATA, 6 impossible arrivals excluded |
| **On-Time Shipments** | `260` | Exact 57.78% SLA rate (`260 / 450`) |
| **Total Cleaned Weight** | `6,648,333.5 kg` | ~6,648.3 MT (1 grams typo rescaled, 5 negative/zero weights cleared) |
| **Total Cargo Volume** | `18,157.01 CBM` | Full fleet volume |
| **Active In-Transit** | `42 active` | 458 delivered (91.6% completed) |
| **#1 Trade Lane** | `BDCGP → ESVLC` | 77 shipments (57.14% on-time, 1.48 days avg delay) |
| **#1 Most Delayed** | `S00158545` | +26 days delay (ONE, `BDCGP → USNYC`) |
| **Local Unified URL** | `http://localhost:8000` | Single-host dashboard & REST APIs |
| **FastAPI Swagger Docs**| `http://localhost:8000/docs` | Interactive OpenAPI documentation |
| **GitHub Repository** | `https://github.com/nathandrake16/mgh-assessment` | Clean public repo with full commit history |
