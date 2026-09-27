"""
Constants for TETHER - Dementia Patient Monitoring System
"""

# Blynk Virtual Pin Mapping (Health Guard Template)
BLYNK_PINS = {
    "HEART_RATE": "V0",     # Type: Integer
    "SPO2": "V1",           # Type: Integer
    "TEMPERATURE": "V2",    # Type: Double
    "FALL_STATUS": "V3",    # Type: String ("NORMAL", "FALL", "FALL DETECTED")
    "GPS_STATUS": "V4",     # Type: String ("GPS LOCKED", "NO GPS FIX", etc.)
    "LATITUDE": "V5",       # Type: Double
    "LONGITUDE": "V6",      # Type: Double
    "BLE_ROOM": "V7",       # Type: String ("Living Room", "Bedroom", "UNKNOWN", etc.)
}

# Explicitly Unavailable Sensor Streams in Current Hardware
UNAVAILABLE_SENSORS = ["HRV", "ECG", "GSR"]
HRV_STATUS_LABEL = "HRV Data Unavailable"

# Alert Types
ALERT_ELEVATED_HEART_RATE = "ELEVATED_HEART_RATE"
ALERT_FALL_DETECTED = "FALL_DETECTED"
ALERT_GEOFENCE_BREACH = "GEOFENCE_BREACH"
ALERT_DEVICE_OFFLINE = "DEVICE_OFFLINE"
ALERT_GPS_LOST = "GPS_LOST"

# Alert Severities
SEVERITY_INFO = "INFO"
SEVERITY_WARNING = "WARNING"
SEVERITY_CRITICAL = "CRITICAL"

ALERT_SEVERITY_MAP = {
    ALERT_ELEVATED_HEART_RATE: SEVERITY_WARNING,
    ALERT_FALL_DETECTED: SEVERITY_CRITICAL,
    ALERT_GEOFENCE_BREACH: SEVERITY_CRITICAL,
    ALERT_DEVICE_OFFLINE: SEVERITY_WARNING,
    ALERT_GPS_LOST: SEVERITY_WARNING,
}

# Default Cooldowns (in seconds) to prevent duplicate alert spamming
DEFAULT_COOLDOWNS = {
    ALERT_ELEVATED_HEART_RATE: 60,      # 60 seconds
    ALERT_FALL_DETECTED: 30,            # 30 seconds
    ALERT_GEOFENCE_BREACH: 300,         # 5 minutes
    ALERT_GPS_LOST: 300,                # 5 minutes
    ALERT_DEVICE_OFFLINE: 300,          # 5 minutes
}

# Heart Rate Calculations
DEFAULT_BASELINE_HR = 72
HR_STRESS_MULTIPLIER = 1.25  # 25% increase above baseline

# SpO2 Thresholds (Guidance display, not clinical diagnosis)
SPO2_NORMAL_MIN = 95
SPO2_LOW_THRESHOLD = 90

# Fall Keywords
FALL_KEYWORDS = ["FALL", "FALL DETECTED", "FALL_DETECTED", "YES", "TRIPPED"]

# GPS Status Keywords
GPS_NO_FIX_KEYWORDS = ["NO GPS FIX", "NO FIX", "SEARCHING", "UNAVAILABLE", "NONE", ""]

# Medical Safety Disclaimer
MEDICAL_DISCLAIMER = (
    "TETHER is a monitoring prototype and is not a medical diagnostic system. "
    "Sensor readings and alerts should not replace professional medical advice."
)
