from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import (
    col, lit, when, least, coalesce, current_timestamp
)

DATABASE = "TELECOM_DB"
SOURCE = f"{DATABASE}.GOLD.MART_NETWORK_RELIABILITY"
TARGET = f"{DATABASE}.CONSUMPTION.NETWORK_RISK_SNOWPARK"

def main(session=None):
    session = session or get_active_session()

    reliability = session.table(SOURCE)

    # Explicit, explainable components. These thresholds mirror the SQL
    # baseline in the Gold build script.
    scored = (
        reliability
        .with_column(
            "INCIDENT_SCORE",
            least(coalesce(col("INCIDENT_COUNT"), lit(0)) * lit(5), lit(25))
        )
        .with_column(
            "OPEN_ALARM_SCORE",
            least(coalesce(col("OPEN_CRITICAL_ALARMS"), lit(0)) * lit(10), lit(30))
        )
        .with_column(
            "PACKET_LOSS_SCORE",
            when(coalesce(col("AVG_PACKET_LOSS_PCT"), lit(0)) >= 10, lit(20))
            .when(col("AVG_PACKET_LOSS_PCT") >= 5, lit(15))
            .when(col("AVG_PACKET_LOSS_PCT") >= 2, lit(10))
            .when(col("AVG_PACKET_LOSS_PCT") > 0, lit(5))
            .otherwise(lit(0))
        )
        .with_column(
            "LATENCY_SCORE",
            when(coalesce(col("AVG_LATENCY_MS"), lit(0)) >= 1000, lit(15))
            .when(col("AVG_LATENCY_MS") >= 500, lit(10))
            .when(col("AVG_LATENCY_MS") >= 200, lit(5))
            .otherwise(lit(0))
        )
        .with_column(
            "CUSTOMER_IMPACT_SCORE",
            when(coalesce(col("ESTIMATED_CUSTOMERS_IMPACTED"), lit(0)) >= 10000, lit(10))
            .when(col("ESTIMATED_CUSTOMERS_IMPACTED") >= 5000, lit(7))
            .when(col("ESTIMATED_CUSTOMERS_IMPACTED") >= 1000, lit(4))
            .when(col("ESTIMATED_CUSTOMERS_IMPACTED") > 0, lit(2))
            .otherwise(lit(0))
        )
    )

    total = (
        col("INCIDENT_SCORE")
        + col("OPEN_ALARM_SCORE")
        + col("PACKET_LOSS_SCORE")
        + col("LATENCY_SCORE")
        + col("CUSTOMER_IMPACT_SCORE")
    )

    result = (
        scored
        .with_column("NETWORK_RISK_SCORE", least(total, lit(100)))
        .with_column(
            "RISK_CATEGORY",
            when(col("NETWORK_RISK_SCORE") >= 65, lit("HIGH"))
            .when(col("NETWORK_RISK_SCORE") >= 35, lit("MEDIUM"))
            .otherwise(lit("LOW"))
        )
        .with_column("SCORED_AT", current_timestamp())
        .select(
            "NETWORK_ELEMENT_ID", "ELEMENT_NAME", "REGION", "CITY",
            "INCIDENT_COUNT", "CRITICAL_INCIDENT_COUNT", "OPEN_CRITICAL_ALARMS",
            "AVG_PACKET_LOSS_PCT", "AVG_LATENCY_MS",
            "MAX_CPU_UTILIZATION_PCT", "MAX_TRAFFIC_UTILIZATION_PCT",
            "ESTIMATED_CUSTOMERS_IMPACTED",
            "INCIDENT_SCORE", "OPEN_ALARM_SCORE", "PACKET_LOSS_SCORE",
            "LATENCY_SCORE", "CUSTOMER_IMPACT_SCORE",
            "NETWORK_RISK_SCORE", "RISK_CATEGORY", "SCORED_AT"
        )
    )

    # Replace the persisted scoring snapshot on each run.
    result.write.mode("overwrite").save_as_table(TARGET)
    written = session.table(TARGET).count()
    print(f"Snowpark risk scoring completed. Rows written: {written}")
    return session.table(TARGET).sort(col("NETWORK_RISK_SCORE").desc())

if __name__ == "__main__":
    main()