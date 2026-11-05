# Data dictionary and model grain

## Source entities

- Customer: one row per `customer_id` (900 source rows).
- Subscription: one row per `subscription_id` (1,400 source rows); references customer.
- Network element: one row per `network_element_id` (400 source rows); parent element models hierarchy.
- Usage transaction: one row per `usage_transaction_id` (2,200 source rows); references subscription, customer and network element.
- Trouble ticket: one row per `ticket_id` (700 source rows); references customer, subscription and optionally incident.
- Network incident: one row per `network_incident_id` (400 source rows); references primary network element.
- Network event: one row per `event_id` (900 source rows); nested metric, alarm, geo and array contexts are preserved in Bronze VARIANT and projected in Silver.

## Gold grains

| Object | Grain |
|---|---|
| DIM_CUSTOMER | one customer |
| DIM_SUBSCRIPTION | one subscription |
| DIM_NETWORK_ELEMENT | one network element |
| DIM_DATE | one calendar date |
| FACT_USAGE | one usage transaction |
| FACT_NETWORK_INCIDENT | one incident |
| FACT_TROUBLE_TICKET | one ticket |
| FACT_NETWORK_EVENT | one NMS event |
| MART_USAGE_SUMMARY | usage date × usage type × roaming flag |
| MART_NETWORK_RELIABILITY | one network element |
| MART_TICKET_SLA | category × priority × status × assigned team |
| MART_NETWORK_RISK | one network element and risk inputs |

## KPI definitions

- Active subscriptions: distinct subscriptions with status `Active`.
- Voice/SMS/data: sum of voice minutes, SMS count and data volume from FACT_USAGE.
- Average data: average `DATA_VOLUME_MB` (state whether per transaction or per subscription in presentation).
- Incident duration: minutes between incident start and end; open incidents have null duration.
- MTTR: average resolved incident duration (add `WHERE INCIDENT_END_TS IS NOT NULL` when presenting formal MTTR).
- Ticket resolution: minutes between ticket creation and resolution.
- SLA compliance: resolved tickets with resolution minutes ≤ SLA target divided by resolved tickets.
- Open critical alarms: critical events with event status Open.
- High-risk network elements: count rows with RISK_CATEGORY='HIGH' after Snowpark execution.

## Data quality ownership and source notes

- IDMC owns source profiling, null handling, duplicate resolution, business-rule validation, date/time standardisation, relationship/orphan checks and reject routing.
- Snowflake assumes IDMC has delivered cleansed, deduplicated target files. The Silver layer performs data-type conformance and JSON attribute extraction only.
- `DQ_STATUS` in Silver is set to `IDMC_CLEAN` as lineage metadata; it is not the result of a second Snowflake profiling pass.
- `source_updated_ts` is the incremental ordering field where supplied.
- The row counts above describe the original reference files, not guaranteed post-IDMC target counts. Use the IDMC successful/rejected output manifest as the authoritative reconciliation baseline.
