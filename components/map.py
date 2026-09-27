"""
Standardized Map Component for TETHER Dashboard
Displays patient GPS location, configured safe zone geofence radius, and distance calculation.
Uses Folium and streamlit-folium.
"""
import streamlit as st
import folium
import textwrap
from streamlit_folium import st_folium
from typing import Dict, Any, Optional
from utils.calculations import is_valid_coordinates, is_outside_geofence


def render_location_map(
    patient_lat: Optional[float],
    patient_lon: Optional[float],
    gps_status: str,
    safe_zone: Optional[Dict[str, Any]]
):
    """
    Renders standardized map with patient marker and safe zone geofence matching chart height.
    """
    st.markdown(textwrap.dedent("""
<div class="panel-header-row">
    <span class="panel-title">📍 GEOFENCE TRACKING & GPS POSITION</span>
    <span class="panel-datastream-badge">STREAMS: V4, V5, V6</span>
</div>
"""), unsafe_allow_html=True)

    # Validate patient GPS coordinates
    has_valid_gps = is_valid_coordinates(patient_lat, patient_lon) and "NO" not in str(gps_status).upper()
    has_safe_zone = bool(safe_zone and is_valid_coordinates(safe_zone.get("latitude"), safe_zone.get("longitude")))

    # Fallback if GPS is not valid
    if not has_valid_gps:
        st.markdown(textwrap.dedent(f"""
<div class="empty-map-box">
    <span style="font-size: 28px;">📡</span>
    <span class="map-warning-title">GPS LOCATION UNAVAILABLE</span>
    <span class="map-warning-desc">
        Wearable telemetry: <code>{gps_status or 'NO GPS FIX'}</code>.<br>
        Indoor or obstructed sky. Null island coordinates (0.0, 0.0) are suppressed for accuracy.
    </span>
</div>
"""), unsafe_allow_html=True)
        return

    safe_lat = float(safe_zone["latitude"]) if has_safe_zone else patient_lat
    safe_lon = float(safe_zone["longitude"]) if has_safe_zone else patient_lon
    radius_meters = float(safe_zone.get("radius_meters", 100.0)) if has_safe_zone else 100.0
    zone_name = safe_zone.get("name", "Home Safe Zone") if has_safe_zone else "Home Safe Zone"

    # Calculate geofence distance
    if has_safe_zone:
        is_breach, distance = is_outside_geofence(patient_lat, patient_lon, safe_lat, safe_lon, radius_meters)
        if is_breach:
            geo_class = "geo-breach"
            geo_text = f"🚨 OUTSIDE SAFE ZONE ({int(distance)}m from {zone_name})"
        else:
            geo_class = "geo-safe"
            geo_text = f"✅ INSIDE SAFE ZONE ({int(distance)}m from {zone_name})"
    else:
        distance = 0.0
        is_breach = False
        geo_class = "geo-warn"
        geo_text = "⚠ No Safe Zone Configured"

    # Status subbar
    st.markdown(textwrap.dedent(f"""
<div class="geofence-status-bar {geo_class}">
    <span class="geofence-tag">{geo_text}</span>
    <span class="geofence-coords">GPS: {patient_lat:.4f}° N, {patient_lon:.4f}° E</span>
</div>
"""), unsafe_allow_html=True)

    # Initialize Folium Map centered around patient
    map_center = [patient_lat, patient_lon]
    m = folium.Map(
        location=map_center,
        zoom_start=17,
        tiles="OpenStreetMap",
        control_scale=True
    )

    # Draw Safe Zone Geofence Circle if available
    if has_safe_zone:
        folium.Circle(
            location=[safe_lat, safe_lon],
            radius=radius_meters,
            color="#10B981" if not is_breach else "#EF4444",
            weight=2,
            fill=True,
            fill_color="#10B981" if not is_breach else "#EF4444",
            fill_opacity=0.15,
            popup=f"{zone_name} (Radius: {int(radius_meters)}m)"
        ).add_to(m)

        # Home Safe Zone Marker
        folium.Marker(
            location=[safe_lat, safe_lon],
            popup=f"<b>{zone_name}</b><br>Safe Radius: {int(radius_meters)}m",
            tooltip=f"{zone_name} Base",
            icon=folium.Icon(color="green", icon="home", prefix="fa")
        ).add_to(m)

    # Patient Marker
    patient_icon_color = "red" if is_breach else "blue"
    folium.Marker(
        location=[patient_lat, patient_lon],
        popup=f"<b>Patient Current Location</b><br>Lat: {patient_lat:.4f}<br>Lon: {patient_lon:.4f}",
        tooltip="Patient Wearable",
        icon=folium.Icon(color=patient_icon_color, icon="user", prefix="fa")
    ).add_to(m)

    st_folium(
        m,
        height=245,
        width=None,
        returned_objects=[]
    )
