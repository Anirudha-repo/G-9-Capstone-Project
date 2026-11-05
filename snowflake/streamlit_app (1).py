# Project 9: Streamlit Telecom Operations Dashboard
# Intended for a Streamlit in Snowflake app using the app's active Snowpark session.
# The app reads only Consumption views/tables, not Bronze or Silver.

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

st.set_page_config(
    page_title="Telecom Network Operations",
    page_icon="📡",
    layout="wide"
)

st.title("Telecommunications Network Operations & Service Assurance")
st.caption("Project 9 | Gold and Consumption layer dashboard")

session = get_active_session()

def query_df(sql: str) -> pd.DataFrame:
    return session.sql(sql).to_pandas()

def show_query_error(label: str, exc: Exception):
    st.error(f"{label} could not be loaded. Check that the app role has SELECT access and the object exists.")
    st.code(str(exc))

# KPI: Usage summary
st.header("Usage")
try:
    usage = query_df("""
        SELECT
            SUM(TRANSACTION_COUNT) AS TRANSACTIONS,
            SUM(TOTAL_VOICE_MINUTES) AS VOICE_MINUTES,
            SUM(TOTAL_SMS_COUNT) AS SMS_COUNT,
            SUM(TOTAL_DATA_MB) AS DATA_MB,
            SUM(TOTAL_CHARGES) AS TOTAL_CHARGES
        FROM TELECOM_DB.CONSUMPTION.V_USAGE_KPI
    """)
    r = usage.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Transactions", f"{int(r['TRANSACTIONS'] or 0):,}")
    c2.metric("Voice minutes", f"{int(r['VOICE_MINUTES'] or 0):,}")
    c3.metric("SMS", f"{int(r['SMS_COUNT'] or 0):,}")
    c4.metric("Data (MB)", f"{float(r['DATA_MB'] or 0):,.2f}")
    c5.metric("Charges", f"{float(r['TOTAL_CHARGES'] or 0):,.2f}")
    usage_trend = query_df("""
        SELECT USAGE_DATE, SUM(TOTAL_DATA_MB) AS DATA_MB,
               SUM(TOTAL_VOICE_MINUTES) AS VOICE_MINUTES,
               SUM(TOTAL_SMS_COUNT) AS SMS_COUNT
        FROM TELECOM_DB.CONSUMPTION.V_USAGE_KPI
        GROUP BY USAGE_DATE
        ORDER BY USAGE_DATE
    """)
    if not usage_trend.empty:
        st.subheader("Daily usage trend")
        st.line_chart(usage_trend.set_index("USAGE_DATE")[["DATA_MB", "VOICE_MINUTES", "SMS_COUNT"]])
except Exception as exc:
    show_query_error("Usage KPIs", exc)

# Network reliability
st.header("Network reliability")
try:
    reliability = query_df("""
        SELECT NETWORK_ELEMENT_ID, ELEMENT_NAME, REGION, CITY,
               INCIDENT_COUNT, AVG_INCIDENT_DURATION_MINUTES,
               ESTIMATED_CUSTOMERS_IMPACTED, OPEN_CRITICAL_ALARMS,
               AVG_PACKET_LOSS_PCT, AVG_LATENCY_MS
        FROM TELECOM_DB.CONSUMPTION.V_NETWORK_RELIABILITY
        ORDER BY INCIDENT_COUNT DESC
    """)
    a, b, c = st.columns(3)
    a.metric("Network elements", f"{len(reliability):,}")
    b.metric("Incidents", f"{int(reliability['INCIDENT_COUNT'].fillna(0).sum()):,}" if not reliability.empty else "0")
    c.metric("Open critical alarms", f"{int(reliability['OPEN_CRITICAL_ALARMS'].fillna(0).sum()):,}" if not reliability.empty else "0")
    st.dataframe(reliability, use_container_width=True)
except Exception as exc:
    show_query_error("Network reliability", exc)

# Ticket SLA
st.header("Trouble-ticket SLA")
try:
    tickets = query_df("""
        SELECT TICKET_CATEGORY, PRIORITY_CODE, TICKET_STATUS, ASSIGNED_TEAM,
               TICKET_COUNT, RESOLVED_COUNT, OPEN_COUNT, AVG_RESOLUTION_MINUTES,
               SLA_MET_COUNT, SLA_BREACHED_COUNT, SLA_COMPLIANCE_PCT
        FROM TELECOM_DB.CONSUMPTION.V_TICKET_SLA
        ORDER BY TICKET_COUNT DESC
    """)
    st.dataframe(tickets, use_container_width=True)
except Exception as exc:
    show_query_error("Ticket SLA", exc)

# Snowpark persisted risk score
st.header("Snowpark network-risk classification")
try:
    risk = query_df("""
        SELECT NETWORK_ELEMENT_ID, ELEMENT_NAME, REGION, CITY,
               INCIDENT_SCORE, OPEN_ALARM_SCORE, PACKET_LOSS_SCORE,
               LATENCY_SCORE, CUSTOMER_IMPACT_SCORE,
               NETWORK_RISK_SCORE, RISK_CATEGORY, SCORED_AT
        FROM TELECOM_DB.CONSUMPTION.NETWORK_RISK_SNOWPARK
        ORDER BY NETWORK_RISK_SCORE DESC
    """)
    if not risk.empty:
        high = int((risk["RISK_CATEGORY"] == "HIGH").sum())
        medium = int((risk["RISK_CATEGORY"] == "MEDIUM").sum())
        low = int((risk["RISK_CATEGORY"] == "LOW").sum())
        x, y, z = st.columns(3)
        x.metric("High risk", high)
        y.metric("Medium risk", medium)
        z.metric("Low risk", low)
        st.bar_chart(risk.set_index("NETWORK_ELEMENT_ID")[["NETWORK_RISK_SCORE"]])
        st.dataframe(risk, use_container_width=True)
    else:
        st.info("No Snowpark risk scores are available. Run 10_snowpark_network_risk.py first.")
except Exception as exc:
    show_query_error("Snowpark risk scores", exc)

# Exceptions / quarantine dashboard. SELECT * avoids hard-coding an unknown
# exception-table column list; table-level permissions are still required.
st.header("Data-quality exceptions")
try:
    exceptions = query_df("""
        SELECT *
        FROM TELECOM_DB.CONTROL.SILVER_EXCEPTIONS
        LIMIT 1000
    """)
    st.metric("Exceptions displayed (maximum 1,000)", f"{len(exceptions):,}")
    st.dataframe(exceptions, use_container_width=True)
except Exception as exc:
    show_query_error("Exception register", exc)

st.caption("Dashboard values are read from Consumption secure views and the persisted Snowpark score table.")
