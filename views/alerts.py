"""
Alert History and Notification Audit Log Page for TETHER
"""
import streamlit as st
import pandas as pd
from database.database import get_all_patients, get_recent_alerts, get_patient
from utils.constants import MEDICAL_DISCLAIMER


def render_alerts_page():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h2 style="margin: 0; color: #FFFFFF; font-weight: 800; letter-spacing: 1px;">INCIDENT & ALERT AUDIT LOG</h2>
            <p style="color: #94A3B8; font-size: 14px; margin-top: 4px;">
                Complete chronological log of vital threshold triggers, fall events, wander alerts, and caregiver push notification statuses.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    all_patients = get_all_patients()
    if not all_patients:
        st.info("No registered patients found.")
        return

    patient_ids = [p["id"] for p in all_patients]
    selected_id = st.session_state.get("selected_patient_id", patient_ids[0])
    if selected_id not in patient_ids:
        selected_id = patient_ids[0]

    col_pat, col_sev, col_limit = st.columns([2, 1.5, 1])
    with col_pat:
        patient_options = {p["id"]: f"{p['name']} (ID: {p['id']})" for p in all_patients}
        chosen_id = st.selectbox(
            "Filter Patient",
            options=patient_ids,
            index=patient_ids.index(selected_id),
            format_func=lambda pid: patient_options[pid]
        )
    with col_sev:
        severity_filter = st.selectbox("Severity Filter", ["All Severities", "CRITICAL", "WARNING", "INFO"])
    with col_limit:
        limit_count = st.selectbox("Log Limit", [25, 50, 100, 200], index=1)

    alerts = get_recent_alerts(chosen_id, limit=limit_count)

    if severity_filter != "All Severities":
        alerts = [a for a in alerts if a.get("severity") == severity_filter]

    if not alerts:
        st.markdown(
            """
            <div class="empty-alerts-box" style="margin-top: 20px;">
                <span class="empty-icon" style="font-size: 32px;">🛡️</span><br>
                <span style="font-weight: 600; font-size: 14px; margin-top: 8px; display: inline-block;">
                    No recorded alerts matching the current filter.
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # Metrics summary
        total_alerts = len(alerts)
        critical_count = sum(1 for a in alerts if a.get("severity") == "CRITICAL")
        warning_count = sum(1 for a in alerts if a.get("severity") == "WARNING")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Logged Events", total_alerts)
        with m2:
            st.metric("Critical Incidents (Falls / Wanders)", critical_count)
        with m3:
            st.metric("Warnings (Elevated HR / Lost Signal)", warning_count)

        st.markdown("<br>", unsafe_allow_html=True)

        # Build clean DataFrame
        table_data = []
        for a in alerts:
            table_data.append({
                "Timestamp": a.get("created_at"),
                "Type": str(a.get("alert_type")).replace("_", " ").title(),
                "Severity": a.get("severity"),
                "Message": a.get("message"),
                "Sensor Value": a.get("value") or "--",
                "Coordinates": f"{a.get('latitude'):.4f}, {a.get('longitude'):.4f}" if a.get("latitude") else "Indoor / Unlocked",
                "Caregiver Notification": a.get("notification_status") or "LOGGED"
            })

        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
                "Severity": st.column_config.TextColumn("Severity", width="small"),
                "Message": st.column_config.TextColumn("Incident Details", width="large"),
                "Caregiver Notification": st.column_config.TextColumn("Dispatch Status", width="medium")
            },
            hide_index=True
        )

    # Footer disclaimer
    st.markdown(
        f"""
        <div class="disclaimer-card">
            {MEDICAL_DISCLAIMER}
        </div>
        """,
        unsafe_allow_html=True
    )
