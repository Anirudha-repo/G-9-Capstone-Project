# Demonstration runbook

1. Explain the business problem: network health, customer usage, incidents and tickets are siloed.
2. Show the seven source feeds and the IDMC hand-off. Explain that the original files in `data/source/` are reference inputs; the files loaded into Snowflake must be the IDMC-cleansed target outputs.
3. Show the IDMC profiling/cleansing evidence and reject outputs in IDMC. IDMC is the single owner of business data quality.
4. Load IDMC outputs into Bronze; show source-file metadata and the JSON VARIANT payload.
5. Run Silver conformance transformations: date/numeric/boolean typing and extraction of nested JSON event attributes. No duplicate profiling, anomaly detection, null profiling, relationship profiling or DQ quarantine is repeated in Snowflake.
6. Show Gold dimensions/facts and mart grains.
7. Run the operational Bronze/Silver row-count reconciliation and KPI queries from `07_validation_and_recovery.sql`; compare counts with the IDMC successful-output manifest.
8. Run Snowpark scoring; explain component weights (incident 25%, critical alarms 30%, packet loss 20%, latency 15%, customer impact 10%).
9. Demonstrate masking using `USE ROLE TELECOM_MANAGER_ROLE` versus `USE ROLE NETWORK_ENGINEER_ROLE`.
10. Demonstrate usage delta: IDMC-cleansed new ID and corrected ID, then replay only if the upstream delivery contract guarantees idempotent business keys; show row count and `SOURCE_UPDATED_TS`.
11. Show clone/Time Travel recovery and close with limitations and future enhancements.

## Honest demo caveats

- Do not claim IDMC taskflows were built in this package; Item C is pending your existing mappings.
- Do not claim real-time streaming; this is staged batch plus Snowflake Stream/Task incremental processing.
- Do not load the raw reference CSV/JSON files as the final source when demonstrating the IDMC-integrated architecture. Replace them with the IDMC-cleansed target outputs while preserving the agreed schema and file naming contract.
- Snowflake SQL was statically reviewed and checked for internal object/column consistency in this package, but has not been executed against your Snowflake account. A live deployment run is required to verify account permissions, file-format behavior, task execution and role grants.
