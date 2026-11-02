# Project 9: Telecom Network Operations, Customer Experience & Service Assurance Analytics Platform

A five-day capstone that builds an end-to-end analytics platform for a telecom operator. It uses **IDMC, Snowflake (SnowSQL, Snowpark), Streamlit and Git** in a **Bronze → Silver → Gold** medallion architecture.

## 1. Business Problem

Customer, subscription, usage, network-element, incident, ticket and alarm data sit in separate sources. The business cannot easily answer: *"When this network element degraded, which services broke, which customers were affected, and how quickly did we restore them?"*

This project builds a governed, secure and reconciled analytical view that answers that question.

## 2. Objectives

- Build a trusted customer–subscription–network analytical view
- Measure voice, SMS and data usage
- Track incident frequency, duration, severity and customer impact
- Track ticket resolution and SLA compliance
- Correlate NMS events, incidents, services and tickets
- Calculate an explainable network-risk score with Snowpark
- Secure data with RBAC and masking, and serve dashboards through Streamlit

## 3. Scope

**In scope:** customers, subscriptions, network elements (with hierarchy), usage transactions, network incidents, trouble tickets, NMS events (JSON); one incremental usage pipeline; RBAC and masking.

**Out of scope:** account / plan / device master tables, billing, complaints, portability, offers, real-time OSS, Kafka/MQTT, network control, Cortex AI, MLOps.
`account_id`, `plan_id` and `device_id` are kept only as plain attributes on `DIM_SUBSCRIPTION`.

## 4. Data Sources

| File | Format | Records |
|---|---|---|
| customers | CSV | 900 |
| subscriptions | CSV | 1,400 |
| network_elements | CSV | 400 |
| usage_transactions | CSV | 2,200 |
| trouble_tickets | CSV | 700 |
| network_incidents | CSV | 400 |
| network_events | JSON | 900 |
| **Total** | | **6,900** |

### Controlled data-quality conditions

| Condition | Count | Handling |
|---|---|---|
| Optional nulls | 8 | Warning, retained |
| Duplicate records | 3 | Duplicate route (quarantine) |
| Impossible sequence anomalies | 3 | Reject (quarantine) |
| Extreme outliers | 2 | Warning, retained and flagged |
| Mixed date formats | 4 | Standardised to ISO and kept |

Row routing priority: **Reject > Duplicate > Warning > Clean**.

## 5. Architecture

```
Sources (CSV/JSON)
   → IDMC (cleanse, standardise, route: clean / warning / duplicate / reject)
   → Snowflake Internal Stage
   → BRONZE  (raw, source-aligned, with load metadata)
   → SILVER  (typed, de-duplicated, relationship-validated)
   → GOLD    (dimensions, facts, marts, secure views)
   → Consumption (Snowpark risk score, Streamlit dashboards)
   → Control (RBAC, masking, audit, monitoring, recovery)
```

### Gold model

- **Dimensions:** `DIM_DATE`, `DIM_CUSTOMER`, `DIM_SUBSCRIPTION`, `DIM_NETWORK_ELEMENT`
- **Facts:** `FACT_USAGE`, `FACT_NETWORK_INCIDENT`, `FACT_TROUBLE_TICKET`, `FACT_NETWORK_EVENT`
- **Marts:** `MART_USAGE_SUMMARY`, `MART_NETWORK_RELIABILITY`, `MART_TICKET_SLA`, `MART_NETWORK_RISK`

## 6. Tech Stack

IDMC · Snowflake · SnowSQL · Snowpark (Python) · Streamlit in Snowflake · SQL · Python · Git

## 7. Repository Structure

```
.
├── docs/                  # architecture, mapping, grain/keys, KPI catalogue, runbook, reports
├── idmc/                  # mapping and taskflow exports / screenshots
├── snowflake/
│   ├── 01_setup/
│   ├── 02_stage_bronze/
│   ├── 03_silver/
│   ├── 04_gold/
│   ├── 05_pipeline/       # stream and tasks
│   ├── 06_security/       # roles, masking, secure views
│   ├── 07_monitoring/
│   └── 09_recovery/
├── snowpark/              # network-risk scoring
├── streamlit/             # dashboard app
├── tests/                 # test SQL, reconciliation queries
├── data/                  # sample or synthetic files only (see note below)
├── evidence/              # day1 … day5 screenshots and outputs
└── README.md
```

> **Do not commit real credentials or sensitive customer data.** Keep account names, users and passwords out of the repo; use placeholders and a local, git-ignored config.

## 8. Implementation Roadmap

| Day | Focus | Key outputs |
|---|---|---|
| 1 | Discovery, profiling, design, environment | Profiling workbook, DQ register, grain/keys, KPI catalogue, architecture, mapping |
| 2 | IDMC cleansing, routing, stage, Bronze | 7 mappings, taskflow, routed files, Bronze tables, audit and reconciliation v1 |
| 3 | Silver and Gold | Silver tables, 4 dimensions, 4 facts, marts, KPI validation, reconciliation v2 |
| 4 | Incremental, security, Snowpark, recovery | Stream/Task tests, roles and masking, risk score, Time Travel and clone evidence |
| 5 | Streamlit, testing, UAT, demo | App, test report, defect log, runbook, final presentation |

## 9. Getting Started

### Prerequisites

- Snowflake account with SYSADMIN and SECURITYADMIN access
- SnowSQL installed and configured
- IDMC access (connections and taskflow permissions)
- Python 3.10+ with `snowflake-snowpark-python`

### Setup order

```bash
# 1. Create warehouse, database and schemas
snowsql -f snowflake/01_setup/01_environment.sql

# 2. Upload cleansed files to the internal stage
snowsql -q "PUT file://<local_path>/customers_clean.csv @STG.INT_TELCO_STAGE/customers/"

# 3. Load Bronze, then build Silver and Gold
snowsql -f snowflake/02_stage_bronze/load_bronze.sql
snowsql -f snowflake/03_silver/build_silver.sql
snowsql -f snowflake/04_gold/build_gold.sql

# 4. Pipeline, security, scoring
snowsql -f snowflake/05_pipeline/stream_task.sql
snowsql -f snowflake/06_security/rbac_masking.sql
python snowpark/risk_score.py
```

> Script names above are examples; align them with your actual files.

## 10. Incremental Pipeline (Usage)

- A **Stream** on the Bronze usage table detects new rows.
- A **Task** merges them into Silver on `usage_transaction_id`, inserting new rows and updating only when `source_updated_ts` is newer.
- A dependent task refreshes `FACT_USAGE` and `MART_USAGE_SUMMARY`.

Tests: initial load, second file (new and corrected records), idempotent replay, mart refresh.

## 11. Security

| Role | Access |
|---|---|
| `NETWORK_ENGINEER_ROLE` | Bronze, Silver and Gold read; customer contact data masked |
| `SERVICE_ASSURANCE_ROLE` | Gold read; customer contact and address unmasked |
| `TELECOM_MANAGER_ROLE` | Gold read; customer contact data masked |

Masking policies cover email, phone and address. Consumers use **secure views** only, and admin roles are used only to create roles and grants.

## 12. Network Risk Score (Snowpark)

A transparent, rule-based score per network element made of incident frequency, severity, restore time, open critical alarms and customer-experience impact, each scaled 0–100 and weighted. Output columns: component scores, total score, risk category (Low / Medium / High) and scoring timestamp. Runs are reproducible.

## 13. Testing and Reconciliation

Source = Clean + Warning + Duplicate + Reject, and Bronze = Clean + Warning. Counts and value sums are reconciled across Source → Bronze → Silver → Gold, and Streamlit numbers are verified against Gold SQL. See `tests/` and `docs/`.

## 14. Acceptance Criteria

- [ ] All seven files and 6,900 records processed
- [ ] Every documented column present in the correct order
- [ ] Controlled DQ records detected and routed exactly
- [ ] Relationships, grain, KPIs and reconciliations correct
- [ ] Incremental processing is idempotent
- [ ] Roles and masking demonstrated
- [ ] Snowpark score reproducible
- [ ] Streamlit reconciles with Gold
- [ ] Recovery and rerun procedures work

## 15. Team

| Member | Role |
|---|---|
| M1 | Team lead, architecture, Gold modelling, KPIs |
| M2 | IDMC lead, DQ routing and reports |
| M3 | Snowflake engineering, Bronze/Silver, performance, recovery |
| M4 | Security, incremental pipeline, runbook |
| M5 | Snowpark, Streamlit, QA and testing |

## 16. Git Workflow

- `main` holds reviewed, working code only
- One feature branch per task, for example `feature/bronze-load`
- Pull request with at least one peer review before merge
- Clear commit messages, for example `feat(silver): dedupe customers by latest source_updated_ts`

## 17. Documentation

Key documents live in `/docs`: architecture diagram, source-to-target mapping, KPI catalogue, DQ and reconciliation reports, test report, runbook and final presentation.

## 18. Status

| Day | Status |
|---|---|
| Day 1 | ⬜ Not started |
| Day 2 | ⬜ Not started |
| Day 3 | ⬜ Not started |
| Day 4 | ⬜ Not started |
| Day 5 | ⬜ Not started |
