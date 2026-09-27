"""
Standardized Metric Cards Component for TETHER Dashboard
Medical-grade telemetry styling with status pills and sensor health checks.
"""
import streamlit as st
import textwrap
from typing import Dict, Any, Optional
from utils.constants import HRV_STATUS_LABEL


def render_metric_cards(
    reading: Dict[str, Any],
    baseline_hr: float = 72.0
):
    """
    Renders standardized medical IoT vitals cards with high-contrast telemetry numbers.
    """
    hr = reading.get("heart_rate")
    spo2 = reading.get("spo2")
    temp = reading.get("temperature")
    fall_status = str(reading.get("fall_status", "NORMAL")).upper()
    gps_status = str(reading.get("gps_status", "NO GPS FIX")).upper()
    ble_room = str(reading.get("ble_room", "UNKNOWN")).title()

    # 1. Heart Rate Telemetry
    hr_threshold = round(baseline_hr * 1.25, 1)
    if hr is None or hr <= 20:
        hr_val_str = "--"
        hr_unit_str = "BPM"
        hr_status_str = "NO SIGNAL"
        hr_theme = "status-card-gray"
    elif hr >= hr_threshold:
        hr_val_str = f"{hr}"
        hr_unit_str = "BPM"
        hr_status_str = f"ELEVATED (≥{hr_threshold})"
        hr_theme = "status-card-red"
    elif hr < 50:
        hr_val_str = f"{hr}"
        hr_unit_str = "BPM"
        hr_status_str = "BRADYCARDIA"
        hr_theme = "status-card-amber"
    else:
        hr_val_str = f"{hr}"
        hr_unit_str = "BPM"
        hr_status_str = "NORMAL"
        hr_theme = "status-card-green"

    # 2. SpO2 Oxygen Telemetry
    if spo2 is None or spo2 <= 0:
        spo2_val_str = "--"
        spo2_unit_str = "%"
        spo2_status_str = "NO SIGNAL"
        spo2_theme = "status-card-gray"
    elif spo2 < 90:
        spo2_val_str = f"{spo2}"
        spo2_unit_str = "%"
        spo2_status_str = "CRITICAL HYPOXIA"
        spo2_theme = "status-card-red"
    elif spo2 < 95:
        spo2_val_str = f"{spo2}"
        spo2_unit_str = "%"
        spo2_status_str = "BORDERLINE"
        spo2_theme = "status-card-amber"
    else:
        spo2_val_str = f"{spo2}"
        spo2_unit_str = "%"
        spo2_status_str = "NORMAL"
        spo2_theme = "status-card-green"

    # 3. Body Temperature Telemetry (Sanity check: temperatures <= 20°C indicate disconnected sensor)
    if temp is None or temp <= 20.0:
        temp_val_str = "--"
        temp_unit_str = "°C"
        temp_status_str = "UNAVAILABLE"
        temp_theme = "status-card-gray"
    elif temp >= 38.0:
        temp_val_str = f"{temp:.1f}"
        temp_unit_str = "°C"
        temp_status_str = "FEVER ELEVATED"
        temp_theme = "status-card-red"
    elif temp < 35.5:
        temp_val_str = f"{temp:.1f}"
        temp_unit_str = "°C"
        temp_status_str = "HYPOTHERMIC"
        temp_theme = "status-card-amber"
    else:
        temp_val_str = f"{temp:.1f}"
        temp_unit_str = "°C"
        temp_status_str = "NORMAL"
        temp_theme = "status-card-green"

    # 4. Fall Detection Telemetry
    if "FALL" in fall_status:
        fall_val_str = "FALL DETECTED"
        fall_status_str = "CRITICAL EMERGENCY"
        fall_theme = "status-card-red pulse-critical"
    else:
        fall_val_str = "STABLE"
        fall_status_str = "NO FALL DETECTED"
        fall_theme = "status-card-green"

    # 5. GPS Satellite Lock Telemetry
    if "LOCK" in gps_status:
        gps_val_str = "GPS LOCKED"
        gps_status_str = "SATELLITE ACTIVE"
        gps_theme = "status-card-green"
    else:
        gps_val_str = "NO GPS FIX"
        gps_status_str = "SEARCHING / INDOOR"
        gps_theme = "status-card-amber"

    # 6. BLE Indoor Room Telemetry
    ble_val_str = ble_room if (ble_room and ble_room.lower() != "unknown") else "Unknown"
    if ble_val_str != "Unknown":
        ble_status_str = "INDOOR BEACON"
        ble_theme = "status-card-cyan"
    else:
        ble_status_str = "OUT OF RANGE"
        ble_theme = "status-card-gray"

    # Row 1: Physiological Vitals
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
        st.markdown(textwrap.dedent(f"""
<div class="standard-vital-card {hr_theme}">
    <div class="vital-card-top">
        <span class="vital-title">HEART RATE</span>
        <span class="vital-icon-badge">❤️</span>
    </div>
    <div class="vital-card-center">
        <span class="vital-number">{hr_val_str}</span>
        <span class="vital-unit">{hr_unit_str}</span>
    </div>
    <div class="vital-card-bottom">
        <span class="vital-pill pill-{hr_theme}">{hr_status_str}</span>
        <span class="vital-sub-note">Resting: {int(baseline_hr)} BPM</span>
    </div>
</div>
"""), unsafe_allow_html=True)

    with r1_c2:
        st.markdown(textwrap.dedent(f"""
<div class="standard-vital-card {spo2_theme}">
    <div class="vital-card-top">
        <span class="vital-title">SpO₂ OXYGEN SATURATION</span>
        <span class="vital-icon-badge">🫁</span>
    </div>
    <div class="vital-card-center">
        <span class="vital-number">{spo2_val_str}</span>
        <span class="vital-unit">{spo2_unit_str}</span>
    </div>
    <div class="vital-card-bottom">
        <span class="vital-pill pill-{spo2_theme}">{spo2_status_str}</span>
        <span class="vital-sub-note">Optimal ≥95%</span>
    </div>
</div>
"""), unsafe_allow_html=True)

    with r1_c3:
        st.markdown(textwrap.dedent(f"""
<div class="standard-vital-card {temp_theme}">
    <div class="vital-card-top">
        <span class="vital-title">BODY TEMPERATURE</span>
        <span class="vital-icon-badge">🌡️</span>
    </div>
    <div class="vital-card-center">
        <span class="vital-number">{temp_val_str}</span>
        <span class="vital-unit">{temp_unit_str}</span>
    </div>
    <div class="vital-card-bottom">
        <span class="vital-pill pill-{temp_theme}">{temp_status_str}</span>
        <span class="vital-sub-note">Normal 36.5–37.5°C</span>
    </div>
</div>
"""), unsafe_allow_html=True)

    # Row 2: Safety & Motion Vitals
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
        st.markdown(textwrap.dedent(f"""
<div class="standard-vital-card {fall_theme}">
    <div class="vital-card-top">
        <span class="vital-title">FALL STATUS SENSOR</span>
        <span class="vital-icon-badge">⚠️</span>
    </div>
    <div class="vital-card-center">
        <span class="vital-status-text">{fall_val_str}</span>
    </div>
    <div class="vital-card-bottom">
        <span class="vital-pill pill-{fall_theme}">{fall_status_str}</span>
        <span class="vital-sub-note">Stream: Blynk V3</span>
    </div>
</div>
"""), unsafe_allow_html=True)

    with r2_c2:
        st.markdown(textwrap.dedent(f"""
<div class="standard-vital-card {gps_theme}">
    <div class="vital-card-top">
        <span class="vital-title">GPS FIX TELEMETRY</span>
        <span class="vital-icon-badge">📍</span>
    </div>
    <div class="vital-card-center">
        <span class="vital-status-text">{gps_val_str}</span>
    </div>
    <div class="vital-card-bottom">
        <span class="vital-pill pill-{gps_theme}">{gps_status_str}</span>
        <span class="vital-sub-note">Stream: Blynk V4</span>
    </div>
</div>
"""), unsafe_allow_html=True)

    with r2_c3:
        st.markdown(textwrap.dedent(f"""
<div class="standard-vital-card {ble_theme}">
    <div class="vital-card-top">
        <span class="vital-title">BLE INDOOR ROOM BEACON</span>
        <span class="vital-icon-badge">🏠</span>
    </div>
    <div class="vital-card-center">
        <span class="vital-status-text">{ble_val_str}</span>
    </div>
    <div class="vital-card-bottom">
        <span class="vital-pill pill-{ble_theme}">{ble_status_str}</span>
        <span class="vital-sub-note">Stream: Blynk V7</span>
    </div>
</div>
"""), unsafe_allow_html=True)

    # Hardware Stream Transparency Note
    st.markdown(textwrap.dedent(f"""
<div class="stream-transparency-pill">
    <span class="transparency-tag">● {HRV_STATUS_LABEL}</span>
    <span class="transparency-desc">
        Live wearable provides V0–V7 (HR, SpO₂, Temp, Fall, GPS, Lat, Lon, BLE Room). HRV, ECG, and GSR streams are not in the current hardware template and are never fabricated.
    </span>
</div>
"""), unsafe_allow_html=True)
