"""
Standardized Healthcare & IoT Telemetry Header Component for TETHER
"""
import streamlit as st
import textwrap
from typing import Dict, Any, Optional


def render_header(
    patient: Optional[Dict[str, Any]],
    is_live_mode: bool,
    device_online: bool,
    last_updated: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Renders standardized medical IoT header banner with telemetry chips and pulsing live indicator.
    """
    if not is_live_mode:
        status_class = "status-demo"
        status_text = "DEMO SIMULATION"
        dot_color = "#F59E0B"
    elif device_online:
        status_class = "status-online"
        status_text = "DEVICE ONLINE"
        dot_color = "#10B981"
    else:
        status_class = "status-offline"
        status_text = "CONNECTION LOST"
        dot_color = "#EF4444"

    patient_name = patient.get("name", "No Patient Selected") if patient else "Aarav Sharma"
    patient_age = patient.get("age", 72) if patient else 72
    patient_gender = patient.get("gender", "M")[:1] if patient and patient.get("gender") else "M"
    dementia_stage = patient.get("dementia_stage", "Moderate") if patient else "Moderate"
    device_id = patient.get("device_id", "Health Guard") if patient else "Health Guard"
    baseline_hr = int(patient.get("baseline_hr", 72)) if patient else 72
    stress_threshold = round(baseline_hr * 1.25, 1)

    time_display = last_updated.split(" ")[-1] if (last_updated and " " in last_updated) else (last_updated or "Live")

    html_content = textwrap.dedent(f"""
<div class="telemetry-header-card">
    <div class="header-main-row">
        <div class="header-brand-section">
            <div class="brand-title-wrap">
                <span class="header-main-title">TETHER</span>
                <span class="header-badge-tag">CLINICAL TELEMETRY</span>
            </div>
            <div class="header-sub-tag">DEMENTIA PATIENT SAFETY & IOT MONITORING SYSTEM</div>
        </div>
        <div class="header-status-section">
            <div class="live-status-pill {status_class}">
                <span class="pulse-radar-dot" style="background-color: {dot_color};"></span>
                <span class="status-label">{status_text}</span>
            </div>
            <div class="header-clock-tag">
                <span class="clock-label">LAST TELEMETRY PACKET:</span>
                <span class="clock-val">{time_display}</span>
            </div>
        </div>
    </div>
    <div class="header-telemetry-chips">
        <div class="chip-item">
            <span class="chip-label">PATIENT</span>
            <span class="chip-val highlight-val">{patient_name}</span>
        </div>
        <div class="chip-divider"></div>
        <div class="chip-item">
            <span class="chip-label">AGE / GENDER</span>
            <span class="chip-val">{patient_age} yrs · {patient_gender}</span>
        </div>
        <div class="chip-divider"></div>
        <div class="chip-item">
            <span class="chip-label">DEMENTIA STAGE</span>
            <span class="chip-val stage-chip-val">{dementia_stage}</span>
        </div>
        <div class="chip-divider"></div>
        <div class="chip-item">
            <span class="chip-label">WEARABLE IOT UNIT</span>
            <span class="chip-val code-val">{device_id}</span>
        </div>
        <div class="chip-divider"></div>
        <div class="chip-item">
            <span class="chip-label">RESTING BASELINE HR</span>
            <span class="chip-val metric-val-accent">{baseline_hr} BPM <span class="chip-note">(Alert ≥{stress_threshold})</span></span>
        </div>
    </div>
</div>
""")

    st.markdown(html_content, unsafe_allow_html=True)

    if error_message:
        warn_html = textwrap.dedent(f"""
<div class="telemetry-warning-bar">
    <span class="warn-icon">⚠</span>
    <span>{error_message}</span>
</div>
""")
        st.markdown(warn_html, unsafe_allow_html=True)
