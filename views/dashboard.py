"""
Standardized Live Monitoring Dashboard Page for TETHER
Uses Streamlit @st.fragment for high-efficiency auto-refreshing real-time streaming.
Supports LIVE MODE (connected to Blynk IoT) and DEMO MODE (controlled presentation simulation).
"""
import streamlit as st
import datetime
import random
import textwrap
from typing import Dict, Any, Optional
from components.header import render_header
from components.metric_cards import render_metric_cards
from components.charts import render_hr_trend_chart
from components.map import render_location_map
from components.alerts_panel import (
    render_critical_fall_banner,
    render_critical_geofence_banner,
    render_alert_history_list
)
from database.database import (
    get_patient,
    get_caregiver,
    get_safety_zone,
    get_all_patients,
    log_sensor_reading,
    get_recent_sensor_readings,
    get_recent_alerts
)
from services.blynk_service import blynk_service
from services.alert_service import alert_service
from services.location_service import location_service
from utils.constants import MEDICAL_DISCLAIMER
from utils.calculations import is_outside_geofence, normalize_fall_status


def init_demo_state():
    """Initializes simulated scenario state variables in session_state."""
    if "demo_state" not in st.session_state:
        st.session_state["demo_state"] = {
            "heart_rate": 76,
            "spo2": 97,
            "temperature": 36.7,
            "fall_status": "NORMAL",
            "gps_status": "GPS LOCKED",
            "latitude": 16.7050,
            "longitude": 74.2433,
            "ble_room": "Living Room",
            "online": True
        }


def get_demo_reading(safe_zone: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Generates reading from demo simulation state with subtle natural jitter."""
    init_demo_state()
    state = st.session_state["demo_state"]
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # If HR is normal (around 70-80), add slight organic jitter ±1 BPM
    current_hr = state["heart_rate"]
    if current_hr and current_hr < 88:
        jitter_hr = max(68, min(84, current_hr + random.choice([-1, 0, 1])))
    else:
        jitter_hr = current_hr

    return {
        "heart_rate": jitter_hr,
        "spo2": state["spo2"],
        "temperature": state["temperature"],
        "fall_status": state["fall_status"],
        "gps_status": state["gps_status"],
        "latitude": state["latitude"],
        "longitude": state["longitude"],
        "ble_room": state["ble_room"],
        "timestamp": now_str,
        "online": state["online"],
        "status_message": "SIMULATED SENSOR STREAM"
    }


def render_dashboard_page():
    """Main container for the dashboard page."""
    all_patients = get_all_patients()
    if not all_patients:
        st.info("No registered patients found in local database. Load demo patient or register a new patient.")
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            if st.button("📝 Register New Patient", use_container_width=True):
                st.session_state["current_page"] = "Registration"
                st.rerun()
        with col_reg2:
            if st.button("🚀 Load Complete Demo Scenario (Aarav Sharma)", use_container_width=True):
                from database.database import save_patient
                new_id = save_patient(
                    patient_data={
                        "name": "Aarav Sharma",
                        "age": 72,
                        "gender": "Male",
                        "date_of_birth": "1954-08-15",
                        "blood_group": "B+",
                        "height": 168.0,
                        "weight": 65.0,
                        "dementia_stage": "Moderate",
                        "allergies": "Penicillin",
                        "medical_conditions": "Hypertension, Mild Cognitive Impairment",
                        "doctor_name": "Dr. V. Rao",
                        "doctor_contact": "+91 9123456780",
                        "address": "42 Green Valley Apartments, Kolhapur",
                        "preferred_language": "English",
                        "device_id": "Health Guard",
                        "baseline_hr": 72.0
                    },
                    caregiver_data={
                        "name": "Rohit Sharma",
                        "relationship": "Son",
                        "phone": "+91 9876543210",
                        "emergency_contact": "+91 9876543211",
                        "notification_enabled": True
                    },
                    safety_zone_data={
                        "latitude": 16.7050,
                        "longitude": 74.2433,
                        "radius_meters": 100.0,
                        "name": "Home Residence"
                    }
                )
                st.session_state["selected_patient_id"] = new_id
                st.rerun()
        return

    # Select Active Patient
    patient_ids = [p["id"] for p in all_patients]
    selected_id = st.session_state.get("selected_patient_id", patient_ids[0])
    if selected_id not in patient_ids:
        selected_id = patient_ids[0]

    patient = get_patient(selected_id)
    safe_zone = get_safety_zone(selected_id)
    baseline_hr = float(patient.get("baseline_hr", 72.0))

    # Command & Control Toolbar
    st.markdown('<div class="tether-control-bar">', unsafe_allow_html=True)
    col_mode, col_freq, col_pat = st.columns([1.6, 1.2, 2.2])
    with col_mode:
        mode_idx = 0 if st.session_state.get("is_demo_mode", True) else 1
        mode_choice = st.selectbox(
            "Telemetric Source",
            ["🟡 Demo Simulation Mode", "🟢 Live Blynk Cloud (Health Guard)"],
            index=mode_idx,
            label_visibility="collapsed"
        )
        is_live_mode = ("Live Blynk Cloud" in mode_choice)
        st.session_state["is_demo_mode"] = not is_live_mode

    with col_freq:
        refresh_sec = st.selectbox(
            "Auto Refresh Rate",
            [1, 3, 5, 10],
            index=1,  # default 3s
            format_func=lambda x: f"⏱ Stream Sync: {x}s",
            label_visibility="collapsed"
        )
    with col_pat:
        patient_options = {p["id"]: f"👤 {p['name']} (ID #{p['id']}) · {p['dementia_stage']} Stage" for p in all_patients}
        chosen_id = st.selectbox(
            "Active Patient",
            options=patient_ids,
            index=patient_ids.index(selected_id),
            format_func=lambda pid: patient_options[pid],
            label_visibility="collapsed"
        )
        if chosen_id != selected_id:
            st.session_state["selected_patient_id"] = chosen_id
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Demo Mode Simulation Controls
    if not is_live_mode:
        init_demo_state()
        st.markdown(textwrap.dedent("""
<div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 10px; padding: 10px 16px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between;">
    <span style="color: #FBBF24; font-weight: 800; font-size: 11px; letter-spacing: 0.8px;">
        ⚡ DEMO SCENARIO GENERATOR — ONE-CLICK SIMULATION TRIGGERS
    </span>
    <span style="color: #94A3B8; font-size: 11px; font-family: var(--font-mono);">
        Active Profile: Aarav Sharma (Baseline: 72 BPM)
    </span>
</div>
"""), unsafe_allow_html=True)

        sim_col1, sim_col2, sim_col3, sim_col4, sim_col5, sim_col6 = st.columns(6)
        with sim_col1:
            if st.button("❤️ High HR (128)", use_container_width=True, help="Simulate Heart Rate spike to 128 BPM (crosses 90 BPM threshold)"):
                st.session_state["demo_state"]["heart_rate"] = 128
                st.rerun()
        with sim_col2:
            if st.button("🚨 Fall Alert", use_container_width=True, help="Simulate fall detection event"):
                st.session_state["demo_state"]["fall_status"] = "FALL DETECTED"
                st.rerun()
        with sim_col3:
            if st.button("📍 Geofence Out", use_container_width=True, help="Simulate patient wandering outside safe radius"):
                st.session_state["demo_state"]["latitude"] = 16.7110
                st.session_state["demo_state"]["longitude"] = 74.2485
                st.session_state["demo_state"]["gps_status"] = "GPS LOCKED"
                st.rerun()
        with sim_col4:
            if st.button("📡 GPS Drop", use_container_width=True, help="Simulate GPS satellite lock loss"):
                st.session_state["demo_state"]["gps_status"] = "NO GPS FIX"
                st.session_state["demo_state"]["latitude"] = 0.0
                st.session_state["demo_state"]["longitude"] = 0.0
                st.rerun()
        with sim_col5:
            if st.button("🔌 Disconnect", use_container_width=True, help="Simulate device losing connection"):
                st.session_state["demo_state"]["online"] = False
                st.rerun()
        with sim_col6:
            if st.button("🔄 Normal All", use_container_width=True, help="Reset simulation to normal baseline"):
                st.session_state["demo_state"] = {
                    "heart_rate": 76,
                    "spo2": 97,
                    "temperature": 36.7,
                    "fall_status": "NORMAL",
                    "gps_status": "GPS LOCKED",
                    "latitude": 16.7050,
                    "longitude": 74.2433,
                    "ble_room": "Living Room",
                    "online": True
                }
                st.rerun()

    # Live Fragment for Auto-Refreshing Real-Time Stream
    @st.fragment(run_every=f"{refresh_sec}s")
    def live_stream_fragment():
        if is_live_mode:
            reading = blynk_service.fetch_all_pins()
            device_online = reading.get("online", False)
            error_msg = None if device_online else "Unable to reach wearable device gateway. Retrying automatically..."
        else:
            reading = get_demo_reading(safe_zone)
            device_online = reading.get("online", True)
            error_msg = None if device_online else "Wearable device simulated offline."

        # Process reading through Alert Engine (threshold checks, cooldowns, notifications)
        alert_service.process_reading(selected_id, reading)

        # Log reading to SQLite for rolling charts
        if device_online and reading.get("heart_rate") is not None:
            log_sensor_reading(selected_id, reading)

        # Render Standardized Telemetry Header
        render_header(
            patient=patient,
            is_live_mode=is_live_mode,
            device_online=device_online,
            last_updated=reading.get("timestamp"),
            error_message=error_msg
        )

        # Critical Fall Banner if Fall Detected
        fall_is_detected = normalize_fall_status(reading.get("fall_status", "NORMAL"))
        render_critical_fall_banner(
            fall_detected=fall_is_detected,
            time_str=reading.get("timestamp", "").split(" ")[-1] if " " in reading.get("timestamp", "") else "Now",
            room_str=reading.get("ble_room", "Unknown Room")
        )

        # Geofence Breach Banner if patient outside safe zone
        if safe_zone and reading.get("latitude") and abs(reading.get("latitude")) > 1e-6:
            is_breach, dist = is_outside_geofence(
                reading.get("latitude"),
                reading.get("longitude"),
                float(safe_zone["latitude"]),
                float(safe_zone["longitude"]),
                float(safe_zone.get("radius_meters", 100.0))
            )
            render_critical_geofence_banner(
                is_breach=is_breach,
                distance_meters=dist,
                zone_name=safe_zone.get("name", "Home Safe Zone")
            )

        # Live Standardized Metric Cards
        render_metric_cards(reading=reading, baseline_hr=baseline_hr)

        # Fetch recent readings for rolling chart
        recent_readings = get_recent_sensor_readings(selected_id, limit=60)
        recent_alerts = get_recent_alerts(selected_id, limit=6)

        # Lower Section: Chart on left, Location Map on right
        chart_col, map_col = st.columns(2)
        with chart_col:
            st.markdown('<div class="telemetry-panel-box">', unsafe_allow_html=True)
            render_hr_trend_chart(readings=recent_readings, baseline_hr=baseline_hr)
            st.markdown('</div>', unsafe_allow_html=True)
        with map_col:
            st.markdown('<div class="telemetry-panel-box">', unsafe_allow_html=True)
            render_location_map(
                patient_lat=reading.get("latitude"),
                patient_lon=reading.get("longitude"),
                gps_status=reading.get("gps_status", "NO GPS FIX"),
                safe_zone=safe_zone
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Alert History Section
        st.markdown('<div class="telemetry-panel-box">', unsafe_allow_html=True)
        render_alert_history_list(alerts=recent_alerts, max_items=5)
        st.markdown('</div>', unsafe_allow_html=True)

    # Execute fragment
    live_stream_fragment()

    # Footer Medical Disclaimer
    st.markdown(textwrap.dedent(f"""
<div class="disclaimer-card">
    {MEDICAL_DISCLAIMER}
</div>
"""), unsafe_allow_html=True)
