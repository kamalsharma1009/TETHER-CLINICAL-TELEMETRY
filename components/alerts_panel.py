"""
Alerts Panel and Emergency Banner Components for TETHER Dashboard
Displays prominent critical banners (Fall & Geofence) and running event history.
"""
import streamlit as st
import textwrap
from typing import List, Dict, Any, Optional
from utils.constants import SEVERITY_CRITICAL, SEVERITY_WARNING


def render_critical_fall_banner(
    fall_detected: bool,
    time_str: str,
    room_str: str
):
    """
    Renders large prominent emergency banner if a fall is detected.
    """
    if not fall_detected:
        return

    html_content = textwrap.dedent(f"""
<div class="critical-fall-banner animate-pulse">
    <div class="fall-banner-icon">🚨</div>
    <div class="fall-banner-content">
        <div class="fall-banner-title">CRITICAL ALERT: POSSIBLE FALL DETECTED</div>
        <div class="fall-banner-desc">Patient may have fallen. Immediate caregiver attention required.</div>
        <div class="fall-banner-meta">
            <span><b>Time:</b> {time_str}</span>
            <span class="meta-sep">|</span>
            <span><b>Indoor Area:</b> {room_str}</span>
            <span class="meta-sep">|</span>
            <span><b>Caregiver Dispatch:</b> ATTEMPTED</span>
        </div>
    </div>
</div>
""")
    st.markdown(html_content, unsafe_allow_html=True)


def render_critical_geofence_banner(
    is_breach: bool,
    distance_meters: float,
    zone_name: str
):
    """
    Renders warning/critical banner when geofence safe zone is breached.
    """
    if not is_breach:
        return

    html_content = textwrap.dedent(f"""
<div class="critical-geofence-banner">
    <div class="geofence-banner-icon">⚠️</div>
    <div class="geofence-banner-content">
        <div class="geofence-banner-title">GEOFENCE BREACH: PATIENT OUTSIDE SAFE ZONE</div>
        <div class="geofence-banner-desc">
            Patient has wandered {int(distance_meters)} meters from {zone_name}.
        </div>
    </div>
</div>
""")
    st.markdown(html_content, unsafe_allow_html=True)


def render_alert_history_list(
    alerts: List[Dict[str, Any]],
    max_items: int = 6
):
    """
    Renders running alert history with severity indicators, timestamps, and notification status.
    """
    st.markdown('<div class="chart-section-title">RECENT ALERT EVENTS</div>', unsafe_allow_html=True)

    if not alerts:
        st.markdown(textwrap.dedent("""
<div class="empty-alerts-box">
    <span class="empty-icon">🛡️</span>
    <span>No alerts recorded. All monitored vitals and safety parameters are normal.</span>
</div>
"""), unsafe_allow_html=True)
        return

    st.markdown('<div class="alerts-history-container">', unsafe_allow_html=True)

    for alert in alerts[:max_items]:
        severity = str(alert.get("severity", "INFO")).upper()
        if severity == SEVERITY_CRITICAL:
            dot_class = "dot-critical"
            item_class = "alert-item-critical"
        elif severity == SEVERITY_WARNING:
            dot_class = "dot-warning"
            item_class = "alert-item-warning"
        else:
            dot_class = "dot-info"
            item_class = "alert-item-info"

        created_at = str(alert.get("created_at", ""))
        time_display = created_at.split(" ")[1] if " " in created_at else created_at
        alert_type = str(alert.get("alert_type", "")).replace("_", " ").title()
        msg = alert.get("message", "")
        notif_status = alert.get("notification_status", "LOGGED")

        st.markdown(textwrap.dedent(f"""
<div class="alert-history-item {item_class}">
    <div class="alert-item-left">
        <span class="alert-dot {dot_class}"></span>
        <span class="alert-time">{time_display}</span>
        <span class="alert-badge">{alert_type}</span>
    </div>
    <div class="alert-item-msg">{msg}</div>
    <div class="alert-item-notif">
        <span class="notif-tag">Notification: {notif_status}</span>
    </div>
</div>
"""), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
