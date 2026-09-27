"""
Mathematical and validation calculations for TETHER
"""
import math
from typing import Tuple
from utils.constants import HR_STRESS_MULTIPLIER, FALL_KEYWORDS, GPS_NO_FIX_KEYWORDS


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth in meters.
    Uses Haversine formula.
    """
    if None in (lat1, lon1, lat2, lon2):
        return 0.0

    R = 6371000.0  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = R * c
    return round(distance, 2)


def is_valid_coordinates(lat: float, lon: float) -> bool:
    """
    Validates whether latitude and longitude are valid GPS coordinates
    and not placeholder (0.0, 0.0) or out of bounds.
    """
    if lat is None or lon is None:
        return False
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return False

    # (0, 0) is null island / default uninitialized GPS
    if abs(lat) < 1e-6 and abs(lon) < 1e-6:
        return False

    if not (-90.0 <= lat <= 90.0):
        return False
    if not (-180.0 <= lon <= 180.0):
        return False

    return True


def is_outside_geofence(patient_lat: float, patient_lon: float,
                        safe_lat: float, safe_lon: float,
                        radius_meters: float) -> Tuple[bool, float]:
    """
    Checks if patient is outside the configured safe zone.
    Returns: (is_outside: bool, distance_in_meters: float)
    """
    if not is_valid_coordinates(patient_lat, patient_lon) or not is_valid_coordinates(safe_lat, safe_lon):
        return False, 0.0

    distance = haversine_distance(patient_lat, patient_lon, safe_lat, safe_lon)
    is_outside = distance > float(radius_meters)
    return is_outside, distance


def calculate_hr_threshold(baseline_hr: float, multiplier: float = HR_STRESS_MULTIPLIER) -> float:
    """
    Calculate elevated heart rate threshold based on baseline HR.
    Default formula: baseline_hr * 1.25
    """
    return round(float(baseline_hr) * multiplier, 1)


def is_elevated_hr(current_hr: float, baseline_hr: float,
                   multiplier: float = HR_STRESS_MULTIPLIER) -> Tuple[bool, float]:
    """
    Determine if current HR meets or exceeds the elevated threshold.
    Returns: (is_elevated: bool, threshold: float)
    """
    if current_hr is None or baseline_hr is None or current_hr <= 0 or baseline_hr <= 0:
        return False, 0.0

    threshold = calculate_hr_threshold(baseline_hr, multiplier)
    is_elevated = current_hr >= threshold
    return is_elevated, threshold


def normalize_fall_status(fall_raw: str) -> bool:
    """
    Normalize Blynk fall status string into boolean (True = fall detected).
    Handles "NORMAL", "FALL", "FALL DETECTED" case-insensitively.
    """
    if not fall_raw:
        return False

    cleaned = str(fall_raw).strip().upper()
    for kw in FALL_KEYWORDS:
        if kw in cleaned:
            return True
    return False


def is_gps_locked(gps_raw: str, lat: float, lon: float) -> bool:
    """
    Determines if GPS is currently locked with valid coordinates.
    """
    if not is_valid_coordinates(lat, lon):
        return False

    if not gps_raw:
        return False

    cleaned = str(gps_raw).strip().upper()
    for no_fix in GPS_NO_FIX_KEYWORDS:
        if cleaned == no_fix or "NO" in cleaned or "LOST" in cleaned:
            return False

    return True
