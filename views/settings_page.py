"""
System and IoT Settings Page for TETHER
Allows configuring Blynk IoT server/token, alert cooldowns, and notification parameters.
"""
import streamlit as st
import os
from config import BLYNK_TOKEN, BLYNK_SERVER, FIREBASE_CREDENTIALS_PATH, FIREBASE_CAREGIVER_FCM_TOKEN
from services.blynk_service import blynk_service
from services.alert_service import alert_service
from utils.constants import (
    DEFAULT_COOLDOWNS,
    ALERT_ELEVATED_HEART_RATE,
    ALERT_FALL_DETECTED,
    ALERT_GEOFENCE_BREACH,
    ALERT_GPS_LOST,
    ALERT_DEVICE_OFFLINE,
    MEDICAL_DISCLAIMER
)


def render_settings_page():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h2 style="margin: 0; color: #FFFFFF; font-weight: 800; letter-spacing: 1px;">SYSTEM & IOT CONFIGURATION</h2>
            <p style="color: #94A3B8; font-size: 14px; margin-top: 4px;">
                Configure Blynk IoT cloud gateway, notification endpoints, and alert suppression cooldowns.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_blynk, tab_cooldowns, tab_notif = st.tabs([
        "🌐 Blynk IoT Cloud",
        "⏱️ Alert Cooldowns",
        "🔔 Push Notifications"
    ])

    with tab_blynk:
        st.markdown("#### Blynk Cloud Gateway Settings")
        st.info("Template: Health Guard | Datastreams: V0 (HR), V1 (SpO2), V2 (Temp), V3 (Fall), V4 (GPS), V5 (Lat), V6 (Lon), V7 (BLE)")

        with st.form("blynk_settings_form"):
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                blynk_server_input = st.text_input("Blynk Server Address", value=blynk_service.server)
            with col_b2:
                # Mask token for security
                current_masked = blynk_service.token[:4] + "..." + blynk_service.token[-4:] if len(blynk_service.token) >= 8 else ""
                token_input = st.text_input("Blynk Auth Token", value=blynk_service.token, type="password", help="Kept secure; never logged or exposed in client UI")

            submit_blynk = st.form_submit_button("Test Connection & Save Blynk Settings")

        if submit_blynk:
            blynk_service.server = blynk_server_input.strip()
            blynk_service.token = token_input.strip()
            blynk_service.base_url = f"https://{blynk_service.server}/external/api"

            # Test connection
            with st.spinner("Connecting to Blynk Cloud..."):
                if blynk_service.is_configured():
                    status = blynk_service.check_hardware_status()
                    test_readings = blynk_service.fetch_all_pins()
                    if test_readings.get("online"):
                        st.success("✅ Successfully connected to Blynk Cloud! Wearable device datastreams verified.")
                    else:
                        st.warning(f"⚠ Reached Blynk gateway, but hardware device reported: {test_readings.get('status_message', 'No stream')}")
                else:
                    st.info("Blynk token cleared. Dashboard will use Demo Simulation mode.")

    with tab_cooldowns:
        st.markdown("#### Duplicate Alert Protection Cooldowns")
        st.markdown("Configure minimum wait periods before repeating identical alerts while a condition persists.")

        with st.form("cooldown_settings_form"):
            col_cd1, col_cd2 = st.columns(2)
            with col_cd1:
                hr_cd = st.number_input(
                    "Elevated Heart Rate Cooldown (seconds)",
                    min_value=10, max_value=600,
                    value=alert_service.cooldowns.get(ALERT_ELEVATED_HEART_RATE, 60),
                    step=10
                )
                fall_cd = st.number_input(
                    "Fall Alert Cooldown (seconds)",
                    min_value=10, max_value=300,
                    value=alert_service.cooldowns.get(ALERT_FALL_DETECTED, 30),
                    step=5
                )
            with col_cd2:
                geo_cd = st.number_input(
                    "Geofence Breach Cooldown (seconds)",
                    min_value=30, max_value=1800,
                    value=alert_service.cooldowns.get(ALERT_GEOFENCE_BREACH, 300),
                    step=30
                )
                gps_cd = st.number_input(
                    "GPS Lost Signal Cooldown (seconds)",
                    min_value=30, max_value=1800,
                    value=alert_service.cooldowns.get(ALERT_GPS_LOST, 300),
                    step=30
                )

            submit_cd = st.form_submit_button("Update Cooldown Limits")

        if submit_cd:
            alert_service.set_cooldown(ALERT_ELEVATED_HEART_RATE, hr_cd)
            alert_service.set_cooldown(ALERT_FALL_DETECTED, fall_cd)
            alert_service.set_cooldown(ALERT_GEOFENCE_BREACH, geo_cd)
            alert_service.set_cooldown(ALERT_GPS_LOST, gps_cd)
            st.success("Alert suppression cooldown thresholds saved!")

    with tab_notif:
        st.markdown("#### Caregiver Push Notification Architecture")
        st.info("TETHER uses Firebase Cloud Messaging (FCM) Admin SDK for native push notifications to registered caregiver mobile/web clients.")

        fcm_status = "Initialized" if alert_service.active_alerts else "Ready / Mock Mode Active"
        st.markdown(
            f"""
            <div style="background: #121824; border: 1px solid #1F2A3E; border-radius: 10px; padding: 16px;">
                <p><b>Firebase Service Account:</b> <code>{FIREBASE_CREDENTIALS_PATH or 'Simulated / Streamlit Secrets'}</code></p>
                <p><b>FCM Token Target:</b> <code>{FIREBASE_CAREGIVER_FCM_TOKEN or 'Registered Client Device Token'}</code></p>
                <p><b>Delivery Status:</b> <span style="color: #10B981;">{fcm_status}</span></p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div class="disclaimer-card">
            {MEDICAL_DISCLAIMER}
        </div>
        """,
        unsafe_allow_html=True
    )
