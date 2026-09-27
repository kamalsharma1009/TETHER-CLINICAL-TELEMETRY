"""
Alert Engine Service for TETHER
Handles threshold rules, fall detection, geofence breaches, cooldowns, and caregiver notifications.
"""
import datetime
from typing import Dict, Any, List, Optional
from database.database import (
    insert_alert,
    get_latest_alert_by_type,
    update_alert_notification_status,
    get_caregiver,
    get_safety_zone,
    get_patient
)
from utils.constants import (
    ALERT_ELEVATED_HEART_RATE,
    ALERT_FALL_DETECTED,
    ALERT_GEOFENCE_BREACH,
    ALERT_DEVICE_OFFLINE,
    ALERT_GPS_LOST,
    SEVERITY_WARNING,
    SEVERITY_CRITICAL,
    DEFAULT_COOLDOWNS,
    HR_STRESS_MULTIPLIER
)
from utils.calculations import (
    is_elevated_hr,
    normalize_fall_status,
    calculate_hr_threshold
)
from services.location_service import location_service
from services.firebase_service import notification_service


class AlertService:
    def __init__(self, cooldowns: Optional[Dict[str, int]] = None):
        self.cooldowns = cooldowns or DEFAULT_COOLDOWNS.copy()
        # In-memory track of latest alerts for real-time dashboard banners
        self.active_alerts: List[Dict[str, Any]] = []

    def set_cooldown(self, alert_type: str, seconds: int):
        self.cooldowns[alert_type] = seconds

    def is_in_cooldown(self, patient_id: int, alert_type: str) -> bool:
        """
        Checks whether an alert of this type was created within its cooldown window.
        """
        latest = get_latest_alert_by_type(patient_id, alert_type)
        if not latest or not latest.get("created_at"):
            return False

        try:
            created_str = str(latest["created_at"])
            # Handle standard SQLite timestamp format
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                try:
                    last_time = datetime.datetime.strptime(created_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return False

            now = datetime.datetime.now()
            diff_seconds = (now - last_time).total_seconds()
            cooldown_period = self.cooldowns.get(alert_type, 60)
            return diff_seconds < cooldown_period
        except Exception:
            return False

    def process_reading(self, patient_id: int, reading: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluates a normalized sensor reading against all safety & vital thresholds.
        Creates alerts in SQLite and notifies caregiver if cooldown permits.
        """
        generated_alerts: List[Dict[str, Any]] = []
        patient = get_patient(patient_id)
        if not patient:
            return generated_alerts

        patient_name = patient.get("name", f"Patient #{patient_id}")
        baseline_hr = float(patient.get("baseline_hr") or 72.0)
        caregiver = get_caregiver(patient_id)
        safe_zone = get_safety_zone(patient_id)

        # 1. Heart Rate Check (Elevated Heart Rate)
        hr = reading.get("heart_rate")
        if hr is not None and hr > 0:
            elevated, threshold = is_elevated_hr(hr, baseline_hr, HR_STRESS_MULTIPLIER)
            if elevated:
                if not self.is_in_cooldown(patient_id, ALERT_ELEVATED_HEART_RATE):
                    msg = (
                        f"Elevated Heart Rate: Current {hr} BPM exceeds baseline {int(baseline_hr)} BPM "
                        f"(Threshold: {threshold} BPM, +25%)."
                    )
                    alert_info = self._trigger_alert(
                        patient_id=patient_id,
                        patient_name=patient_name,
                        caregiver=caregiver,
                        alert_type=ALERT_ELEVATED_HEART_RATE,
                        severity=SEVERITY_WARNING,
                        message=msg,
                        value=f"{hr} BPM (Threshold {threshold})",
                        lat=reading.get("latitude"),
                        lon=reading.get("longitude")
                    )
                    generated_alerts.append(alert_info)

        # 2. Fall Detection Check
        fall_raw = reading.get("fall_status", "NORMAL")
        if normalize_fall_status(fall_raw):
            if not self.is_in_cooldown(patient_id, ALERT_FALL_DETECTED):
                room_str = reading.get("ble_room", "Unknown Room")
                msg = f"Possible Fall Detected! Immediate caregiver attention required. Location: {room_str}."
                alert_info = self._trigger_alert(
                    patient_id=patient_id,
                    patient_name=patient_name,
                    caregiver=caregiver,
                    alert_type=ALERT_FALL_DETECTED,
                    severity=SEVERITY_CRITICAL,
                    message=msg,
                    value=str(fall_raw),
                    lat=reading.get("latitude"),
                    lon=reading.get("longitude")
                )
                generated_alerts.append(alert_info)

        # 3. GPS & Geofence Check
        lat = reading.get("latitude")
        lon = reading.get("longitude")
        gps_status = reading.get("gps_status", "")

        geo_eval = location_service.evaluate_geofence(lat, lon, gps_status, safe_zone)

        # Check Geofence breach
        if geo_eval.get("is_breach"):
            if not self.is_in_cooldown(patient_id, ALERT_GEOFENCE_BREACH):
                dist = int(geo_eval.get("distance_meters", 0))
                rad = int(geo_eval.get("radius_meters", 100))
                zone = geo_eval.get("zone_name", "Safe Zone")
                msg = f"Geofence Breach: Patient moved outside {zone}! Distance: {dist}m (Safe radius: {rad}m)."
                alert_info = self._trigger_alert(
                    patient_id=patient_id,
                    patient_name=patient_name,
                    caregiver=caregiver,
                    alert_type=ALERT_GEOFENCE_BREACH,
                    severity=SEVERITY_CRITICAL,
                    message=msg,
                    value=f"{dist}m from {zone}",
                    lat=lat,
                    lon=lon
                )
                generated_alerts.append(alert_info)

        # Check GPS loss if device is online but GPS became invalid
        if reading.get("online") and not geo_eval.get("gps_valid"):
            if str(gps_status).upper() in ["NO GPS FIX", "SEARCHING", "LOST"]:
                if not self.is_in_cooldown(patient_id, ALERT_GPS_LOST):
                    msg = "GPS Signal Lost or Searching. Outdoor tracking temporarily unavailable."
                    alert_info = self._trigger_alert(
                        patient_id=patient_id,
                        patient_name=patient_name,
                        caregiver=caregiver,
                        alert_type=ALERT_GPS_LOST,
                        severity=SEVERITY_WARNING,
                        message=msg,
                        value=gps_status,
                        lat=None,
                        lon=None
                    )
                    generated_alerts.append(alert_info)

        # Check Device Offline
        if not reading.get("online", True):
            if not self.is_in_cooldown(patient_id, ALERT_DEVICE_OFFLINE):
                msg = "Wearable Device Offline or Unreachable. Unable to sync live sensor stream."
                alert_info = self._trigger_alert(
                    patient_id=patient_id,
                    patient_name=patient_name,
                    caregiver=caregiver,
                    alert_type=ALERT_DEVICE_OFFLINE,
                    severity=SEVERITY_WARNING,
                    message=msg,
                    value="OFFLINE",
                    lat=None,
                    lon=None
                )
                generated_alerts.append(alert_info)

        # Keep active alerts up to date
        if generated_alerts:
            self.active_alerts = (generated_alerts + self.active_alerts)[:10]

        return generated_alerts

    def _trigger_alert(
        self,
        patient_id: int,
        patient_name: str,
        caregiver: Optional[Dict[str, Any]],
        alert_type: str,
        severity: str,
        message: str,
        value: str,
        lat: Optional[float],
        lon: Optional[float]
    ) -> Dict[str, Any]:
        """
        Inserts alert record into SQLite, dispatches notification, and updates delivery status.
        """
        # 1. Insert alert in database
        alert_id = insert_alert(
            patient_id=patient_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            value=value,
            latitude=lat if lat and abs(lat) > 1e-6 else None,
            longitude=lon if lon and abs(lon) > 1e-6 else None,
            notification_status="DISPATCHING"
        )

        # 2. Dispatch caregiver notification
        notif_result = notification_service.dispatch_alert_notification(
            alert_type=alert_type,
            severity=severity,
            message=message,
            patient_name=patient_name,
            caregiver_info=caregiver
        )

        notif_status_str = notif_result.get("status", "UNKNOWN")
        if notif_result.get("message"):
            notif_status_str += f" ({notif_result['message']})"

        # 3. Update alert record with notification dispatch outcome
        update_alert_notification_status(alert_id, notif_status_str)

        return {
            "id": alert_id,
            "patient_id": patient_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "value": value,
            "latitude": lat,
            "longitude": lon,
            "notification_status": notif_status_str,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
        }


alert_service = AlertService()
