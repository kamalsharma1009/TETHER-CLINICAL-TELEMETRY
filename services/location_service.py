"""
Location and Geofencing Service for TETHER
"""
from typing import Dict, Any, Optional
from utils.calculations import (
    haversine_distance,
    is_valid_coordinates,
    is_outside_geofence,
    is_gps_locked
)


class LocationService:
    @staticmethod
    def evaluate_geofence(
        patient_lat: Optional[float],
        patient_lon: Optional[float],
        gps_status_raw: str,
        safe_zone: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates current patient GPS position against the patient's safe zone.
        Returns:
            {
                "gps_valid": bool,
                "has_safe_zone": bool,
                "is_breach": bool,
                "distance_meters": float,
                "radius_meters": float,
                "status_label": str,
                "message": str,
                "latitude": float,
                "longitude": float
            }
        """
        # Validate GPS coordinates and lock
        if not is_valid_coordinates(patient_lat, patient_lon) or not is_gps_locked(gps_status_raw, patient_lat, patient_lon):
            return {
                "gps_valid": False,
                "has_safe_zone": bool(safe_zone),
                "is_breach": False,
                "distance_meters": 0.0,
                "radius_meters": safe_zone.get("radius_meters", 100.0) if safe_zone else 100.0,
                "status_label": "GPS NO FIX",
                "message": "GPS location unavailable (No fix or invalid coordinates)",
                "latitude": None,
                "longitude": None
            }

        # If no safe zone configured
        if not safe_zone or not safe_zone.get("latitude") or not safe_zone.get("longitude"):
            return {
                "gps_valid": True,
                "has_safe_zone": False,
                "is_breach": False,
                "distance_meters": 0.0,
                "radius_meters": 100.0,
                "status_label": "NO SAFE ZONE",
                "message": "Safe zone not configured for patient.",
                "latitude": patient_lat,
                "longitude": patient_lon
            }

        safe_lat = float(safe_zone["latitude"])
        safe_lon = float(safe_zone["longitude"])
        radius = float(safe_zone.get("radius_meters", 100.0))
        zone_name = safe_zone.get("name", "Home")

        is_breach, distance = is_outside_geofence(
            patient_lat, patient_lon, safe_lat, safe_lon, radius
        )

        if is_breach:
            status_label = "OUTSIDE SAFE ZONE"
            msg = f"Patient is {int(distance)}m from {zone_name} (Safety limit: {int(radius)}m)."
        else:
            status_label = "INSIDE SAFE ZONE"
            msg = f"{int(distance)} meters from {zone_name} (Within safe radius {int(radius)}m)."

        return {
            "gps_valid": True,
            "has_safe_zone": True,
            "is_breach": is_breach,
            "distance_meters": distance,
            "radius_meters": radius,
            "status_label": status_label,
            "message": msg,
            "latitude": patient_lat,
            "longitude": patient_lon,
            "safe_lat": safe_lat,
            "safe_lon": safe_lon,
            "zone_name": zone_name
        }


location_service = LocationService()
