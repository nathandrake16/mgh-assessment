# MGH Freight Visibility Dashboard (2026 H1)
## Last-Minute Executive Presentation Script & Quick Cheat Sheet

This document is your **ready-to-speak 3-to-5 minute presentation script**. It addresses the four core assessment requirements with exact verified numbers, click-by-click live UI actions, data engineering findings, and your forward-looking production roadmap.

---

## 1. Quick-Glance Presentation Cue Card

```
┌────────────────────────────────────────────────────────────────────────┐
│  1. OPENING & NUMBERS (60s)                                            │
│     • 500 Unique Shipments (from 511 raw; 11 duplicates dropped)       │
│     • 57.78% On-Time Delivery Rate (260 on-time / 450 evaluated)       │
│     • Top Lane: BDCGP → ESVLC (77 shipments, 57.1% on-time)            │
│     • Cleaned Weight: 6,648.3 MT (6,648,333.5 kg)                      │
│                                                                        │
│  2. WHAT WE FOUND & FIXED (90s)                                        │
│     • 11 Duplicates: Prioritized Delivered + ATA, dropped extras        │
│     • 24 Port Names: 'bdcgp', 'chattogram', 'cgp' → 'BDCGP'            │
│     • 1 Year Typo: S00158650 /2062 → /2026                             │
│     • 216 Ambiguous Dates: Transit window heuristics (Air/Feeder/Sea)   │
│     • 6 Impossible Arrivals: ATA < ATD quarantined from SLA            │
│     • Weight Outliers: 5 non-positive cleared; 1 grams typo rescaled   │
│                                                                        │
│  3. LIVE DEMO (90s)                                                    │
│     • Top KPIs → Trade Lanes chart → S00158545 modal inspector (+26d)  │
│     • Ask the Data: CMA CGM (least delayed) vs Emirates/MSC (most)    │
│     • Data Quality Audit Drawer: All 9 fixes displayed live            │
│                                                                        │
│  4. NEXT 2 DAYS ROADMAP (45s)                                          │
│     • PostgreSQL + TimescaleDB & Redis caching                         │
│     • Streaming validation (Great Expectations) with dead-letter queue  │
│     • Enterprise SSO & RBAC (Exec vs Dispatcher vs Auditor)            │
│     • Real-time AIS vessel tracking & Slack webhook alerts             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Word-for-Word Spoken Presentation Script

### 1. Opening & Stating the Numbers (60 seconds)

> *"Good morning. Today, I'm presenting the **MGH Global Freight Visibility Dashboard** for 2026 H1.*
>
> *Our goal was to eliminate operational opacity across our international shipping corridors and provide leadership with dependable, mathematically grounded delivery intelligence.*
>
> *Before touching the UI, here are the exact verified baseline metrics of our fleet:*
> - ***Total Shipments:** We ingested 511 raw shipment records and deduplicated them to exactly **500 unique shipments**.*
> - ***On-Time Delivery Rate:** Our fleet achieved **57.78% on-time delivery**—that is **260 on-time shipments out of 450 evaluated**. 50 shipments were properly excluded: 44 active in-transit without arrival timestamps, and 6 corrupted records with impossible arrivals.*
> - ***Biggest Trade Lanes:** Our #1 volume corridor is **`BDCGP → ESVLC` (Chittagong to Valencia)** with **77 shipments** and a 57.1% on-time rate. Our #2 corridor is **`BDCGP → NLRTM` (Rotterdam)** with **73 shipments** at 47.0% on-time, and #3 is **`BDCGP → DEHAM` (Hamburg)** with **55 shipments** at 66.7% on-time.*
> - ***Fleet Cargo Volume:** We tracked **6,648.3 Metric Tons** (6,648,333.5 kg) and **18,157 CBM** across ocean and air operations.*
> - ***Fleet Status:** **42 shipments are currently active in transit** (8.4%), while 458 have been delivered.*"

---

### 2. What I Found in the Data & What I Did About It (90 seconds)

> *"When inspecting the raw CSV, I discovered that blind consumption would have severely corrupted our executive reporting. I engineered an automated **9-rule cleansing pipeline** in Pandas:*
>
> 1. ***Duplicate Shipment Syncs (11 rows):** Multiple system extracts created duplicate IDs. I sorted records so completed deliveries with actual arrival timestamps took priority, then dropped duplicates to establish our true 500-shipment fleet.*
> 2. ***Port Name Inconsistencies (24 rows):** Origin ports contained casing dirt and aliases like `bdcgp`, `Chattogram`, and `CGP`. I normalized all 24 records to the standardized UN/LOCODE `BDCGP` and uppercased destination ports, making trade lane aggregation accurate.*
> 3. ***Corrupt Year Typo (1 row):** Shipment `S00158650` was recorded with an arrival in the year `2062` due to keyboard error. My pipeline detected the anomaly and corrected `/2062` to `/2026`.*
> 4. ***Ambiguous Date Conventions (216 dates):** In slash dates where both day and month were 12 or less (like `04/05/2026`), standard datetime parsers arbitrarily guess and create 5-month errors. I built a **mode-specific transit window algorithm**: testing candidate dates against actual departure (`ATD`) using expected transit durations—0 to 15 days for Air Cargo, 7 to 35 days for China feeder routes, and 15 to 65 days for deep-sea container lines.*
> 5. ***Impossible Arrival Timestamps (6 rows):** Six shipments had recorded arrival dates earlier than departure dates (`ATA < ATD`). Including them would inject artificial negative delays into our SLA metrics. I flagged them as `ata_before_atd` and quarantined them from delay scoring, preserving the mathematical integrity of our 57.78% SLA.*
> 6. ***Weight Outliers & Clerical Typos (6 rows):** Five shipments had zero or negative weights, which were flagged and cleared to `None`. One shipment—`S00158128`—was recorded as 21,816,000 kg because it was entered in grams; my engine divided it by 1,000 to 21,816 kg, locking our total fleet weight at exactly 6,648,333.5 kg.*
> 7. ***Auditability:** Every single correction is tracked in a live audit trail that dispatchers and auditors can inspect.*"

---

### 3. Demo the App (90 seconds)

*(Switch to your browser open at `http://localhost:8000`)*

> *"Both the React frontend and FastAPI backend are served unified on **`http://localhost:8000`**.*
>
> 1. **Top KPI Row:** 
>    *(Point to the 4 cards)*
>    *'Here are our 4 executive cards: 500 Unique Shipments with our deduplication badge; 57.78% On-Time Delivery Rate; 6,648.3 MT Cleaned Weight; and 42 Active In-Transit Shipments.'*
>
> 2. **Trade Lanes Section:** 
>    *(Scroll to Shipments per Trade Lane)*
>    *'Below the KPIs, our interactive Recharts bar chart displays our top corridors, immediately highlighting BDCGP → ESVLC with 77 shipments. Toggling to "All Lanes Table" reveals granular volume, average delay, and reliability for all 15 routes.'*
>
> 3. **Top 10 Most Delayed Shipments & Modal Deep Dive:** 
>    *(Scroll to Top 10 Most Delayed Shipments table)*
>    *'For exception management, this table isolates shipments at risk of client penalties. Shipment `S00158545` is #1 with a +26-day delay on the New York corridor.'*
>    *(Click row S00158545)*
>    *'Clicking the row opens our 15-Field Operational Deep Dive Inspector, showing departure vs arrival milestones, cargo specs, shipper Meghna Fashion Wear, consignee Rhein Textil, and our data cleaning tag. Let's close this.'*
>
> 4. **Milestone 3 — Ask the Data (Grounded AI Synthesis):** 
>    *(Scroll to Ask the Data)*
>    *'We integrated natural language intelligence. Let's ask: "Which carrier is delayed the least?"'*
>    *(Click prompt chip or type and click Ask)*
>    *'The engine instantly synthesizes the verified answer: **CMA CGM** is our best-performing ocean carrier with an average delay of just **0.82 days** and a **66.67% on-time delivery rate**. If we ask for the most delayed carrier, it highlights **MSC** at 2.57 days in ocean and **Emirates SkyCargo** at 6.83 days in air cargo. Notice the engine badge and verified supporting metric cards.'*
>
> 5. **Data Quality Audit Drawer:** 
>    *(Click "Data Quality Audit (9 Fixes)" in the header)*
>    *'Finally, clicking the header button opens our live Audit Drawer, displaying exact counts for all 9 automated data corrections. Complete transparency for compliance.'*"

---

### 4. What Would You Build Next in Two More Days? (45 seconds)

> *"If given two more days to advance this platform to enterprise production, I would execute on four high-leverage initiatives:*
>
> 1. ***Database & Caching Layer:** Migrate from in-memory CSV/Pandas to **PostgreSQL with TimescaleDB** for time-series analytics, paired with **Redis** to cache pre-aggregated trade lane summaries with sub-5ms response times.*
> 2. ***Streaming Validation & Dead-Letter Quarantine:** Implement **Pydantic V2** and **Great Expectations** on the ingestion pipeline. Corrupted records (like impossible arrivals) would automatically route to an S3 quarantine bucket with alert webhooks.*
> 3. ***Enterprise Role-Based Access Control (RBAC):** Integrate Okta or Azure AD SSO with role partitioning: Executives see high-level KPIs and spend; Dispatchers have shipment edit permissions; Auditors access raw cleaning logs.*
> 4. ***Real-Time Carrier Telemetry & Webhooks:** Integrate live AIS vessel tracking and automated Slack / Email notifications triggered whenever a shipment variance exceeds +3 days.*
>
> *Thank you! I welcome any questions."*

---

## 3. Anticipated Q&A Cheat Sheet

| Question | Winning Response |
| :--- | :--- |
| **"Why not just drop the 6 impossible arrival rows?"** | *"Dropping rows hides data losses from dispatchers. We preserve them in the fleet count (500 unique shipments) so invoices can be tracked, but quarantine them from delay calculations to prevent artificial negative delays from skewing the 57.78% SLA rate."* |
| **"How do you ensure the AI doesn't hallucinate numbers?"** | *"Three safeguards: (1) The LLM is fed pre-calculated, verified JSON metrics from Pandas; (2) Responses require strict JSON key contracts; (3) We have an offline deterministic Pandas fallback with regex intent parsing that takes over with zero downtime if APIs fail."* |
| **"How would you scale this to 10M rows?"** | *"Move from Pandas DataFrame to ClickHouse or PostgreSQL with hypertable partitioning, pre-aggregate corridor rollups in materialized views, and use cursor-based pagination with trigram indexes for text search."* |
