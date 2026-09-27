"""
TETHER — Dementia Patient Monitoring System
Main Application Entrypoint (Streamlit)
"""
import streamlit as st
from pathlib import Path

# Page Configuration - MUST be the first Streamlit call
st.set_page_config(
    page_title="TETHER — Dementia Patient Monitoring",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from config import BASE_DIR
from database.database import init_db, get_all_patients
# pyrefly: ignore [missing-import]
from views.dashboard import render_dashboard_page
# pyrefly: ignore [missing-import]
from views.registration import render_registration_page
# pyrefly: ignore [missing-import]
from views.alerts import render_alerts_page
# pyrefly: ignore [missing-import]
from views.patient_profile import render_patient_profile_page
# pyrefly: ignore [missing-import]
from views.settings_page import render_settings_page
from utils.constants import MEDICAL_DISCLAIMER

# Initialize database tables
init_db()

# Load Custom CSS Stylesheet
css_path = BASE_DIR / "assets" / "style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Navigation State Handling
if "current_page" not in st.session_state:
    patients = get_all_patients()
    st.session_state["current_page"] = "Dashboard" if patients else "Registration"

# Sidebar Navigation
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand-box">
            <div class="sidebar-brand-logo">
                <span class="brand-shield">🛡️</span>
                <div class="brand-text-block">
                    <span class="brand-name">TETHER</span>
                    <span class="brand-sub">PATIENT TELEMETRY</span>
                </div>
            </div>
            <div class="brand-system-tag">CLINICAL IOT PLATFORM</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    nav_options = [
        "📊 Live Dashboard",
        "📝 Patient Registration",
        "🔔 Incident Alerts Log",
        "👤 Patient Profile",
        "⚙️ System Settings"
    ]

    page_to_nav = {
        "Dashboard": "📊 Live Dashboard",
        "Registration": "📝 Patient Registration",
        "Alerts": "🔔 Incident Alerts Log",
        "Profile": "👤 Patient Profile",
        "Settings": "⚙️ System Settings"
    }
    nav_to_page = {v: k for k, v in page_to_nav.items()}

    current_nav = page_to_nav.get(st.session_state["current_page"], "📊 Live Dashboard")
    selected_nav = st.radio(
        "Navigation",
        nav_options,
        index=nav_options.index(current_nav) if current_nav in nav_options else 0,
        label_visibility="collapsed"
    )
    st.session_state["current_page"] = nav_to_page[selected_nav]

    st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

    # Presentation Demo Preset
    st.markdown("<div class='sidebar-section-label'>DEMO PRESENTATION FLOW</div>", unsafe_allow_html=True)
    if st.button("🚀 Load Complete Demo Scenario", use_container_width=True, help="Registers Aarav Sharma with baseline 72 BPM and sets normal initial vitals"):
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
        st.session_state["current_page"] = "Dashboard"
        st.session_state["is_demo_mode"] = True
        st.rerun()

    # System Status Footer
    st.markdown(
        """
        <div class="sidebar-status-box">
            <div class="sidebar-status-row">
                <span class="status-indicator-dot online-dot"></span>
                <span>Blynk Cloud: Health Guard</span>
            </div>
            <div class="sidebar-status-row">
                <span class="status-indicator-dot stream-dot"></span>
                <span>Pins: V0–V7 Streaming</span>
            </div>
            <div class="sidebar-status-row">
                <span class="status-indicator-dot db-dot"></span>
                <span>SQLite: tether.db</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Page Router
current_page = st.session_state["current_page"]

if current_page == "Dashboard":
    render_dashboard_page()
elif current_page == "Registration":
    render_registration_page()
elif current_page == "Alerts":
    render_alerts_page()
elif current_page == "Profile":
    render_patient_profile_page()
elif current_page == "Settings":
    render_settings_page()
