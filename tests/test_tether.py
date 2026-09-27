"""
Unit tests for TETHER Core Services, Calculations, and Alert Engine.
"""
import unittest
from utils.calculations import (
    haversine_distance,
    is_valid_coordinates,
    is_outside_geofence,
    calculate_hr_threshold,
    is_elevated_hr,
    normalize_fall_status,
    is_gps_locked
)
from services.blynk_service import BlynkService
from database.database import init_db, save_patient, get_latest_alert_by_type
from services.alert_service import AlertService
from utils.constants import ALERT_ELEVATED_HEART_RATE, ALERT_FALL_DETECTED, ALERT_GEOFENCE_BREACH


class TestTetherCalculations(unittest.TestCase):
    def test_haversine_distance_zero(self):
        dist = haversine_distance(16.7050, 74.2433, 16.7050, 74.2433)
        self.assertEqual(dist, 0.0)

    def test_haversine_distance_nonzero(self):
        # 16.7050, 74.2433 to 16.7060, 74.2433 is roughly ~111 meters
        dist = haversine_distance(16.7050, 74.2433, 16.7060, 74.2433)
        self.assertTrue(100 < dist < 125, f"Expected ~111m, got {dist}")

    def test_is_valid_coordinates(self):
        # Null island / uninitialized
        self.assertFalse(is_valid_coordinates(0.0, 0.0))
        self.assertFalse(is_valid_coordinates(0, 0))
        self.assertFalse(is_valid_coordinates(None, None))
        # Out of bounds
        self.assertFalse(is_valid_coordinates(100.0, 50.0))
        self.assertFalse(is_valid_coordinates(20.0, 200.0))
        # Valid
        self.assertTrue(is_valid_coordinates(16.7050, 74.2433))

    def test_geofence_inside_and_outside(self):
        safe_lat, safe_lon = 16.7050, 74.2433
        radius = 100.0  # 100m

        # Very close (inside)
        outside, dist = is_outside_geofence(16.7051, 74.2433, safe_lat, safe_lon, radius)
        self.assertFalse(outside)
        self.assertLess(dist, 100.0)

        # Far away (outside)
        outside_far, dist_far = is_outside_geofence(16.7100, 74.2433, safe_lat, safe_lon, radius)
        self.assertTrue(outside_far)
        self.assertGreater(dist_far, 100.0)

    def test_stress_heart_rate_threshold(self):
        baseline = 72
        # threshold = 72 * 1.25 = 90.0
        threshold = calculate_hr_threshold(baseline)
        self.assertEqual(threshold, 90.0)

        # HR 89 -> no alert
        is_elevated, _ = is_elevated_hr(89, baseline)
        self.assertFalse(is_elevated)

        # HR 90 -> alert
        is_elevated_90, _ = is_elevated_hr(90, baseline)
        self.assertTrue(is_elevated_90)

        # HR 128 -> alert
        is_elevated_128, _ = is_elevated_hr(128, baseline)
        self.assertTrue(is_elevated_128)

    def test_fall_status_normalization(self):
        self.assertFalse(normalize_fall_status("NORMAL"))
        self.assertFalse(normalize_fall_status("normal"))
        self.assertFalse(normalize_fall_status(""))
        self.assertTrue(normalize_fall_status("FALL"))
        self.assertTrue(normalize_fall_status("fall"))
        self.assertTrue(normalize_fall_status("FALL DETECTED"))
        self.assertTrue(normalize_fall_status("fall detected"))

    def test_gps_locked(self):
        self.assertFalse(is_gps_locked("NO GPS FIX", 0.0, 0.0))
        self.assertFalse(is_gps_locked("NO GPS FIX", 16.7050, 74.2433))
        self.assertTrue(is_gps_locked("GPS LOCKED", 16.7050, 74.2433))


class TestBlynkNormalization(unittest.TestCase):
    def test_normalize_raw_readings(self):
        svc = BlynkService(token="test_token")
        raw = {
            "V0": "76",
            "V1": "97",
            "V2": "36.7",
            "V3": "NORMAL",
            "V4": "GPS LOCKED",
            "V5": "16.7050",
            "V6": "74.2433",
            "V7": "Living Room"
        }
        res = svc.normalize_readings(raw, "2026-09-27 20:30:00")
        self.assertEqual(res["heart_rate"], 76)
        self.assertEqual(res["spo2"], 97)
        self.assertEqual(res["temperature"], 36.7)
        self.assertEqual(res["fall_status"], "NORMAL")
        self.assertEqual(res["gps_status"], "GPS LOCKED")
        self.assertEqual(res["latitude"], 16.7050)
        self.assertEqual(res["longitude"], 74.2433)
        self.assertEqual(res["ble_room"], "Living Room")


class TestAlertEngineAndCooldown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_cooldown_duplicate_prevention(self):
        # Create a test patient
        patient_id = save_patient(
            patient_data={
                "name": "Test Patient",
                "age": 75,
                "dementia_stage": "Moderate",
                "address": "123 Street",
                "device_id": "TETHER-TEST-01",
                "baseline_hr": 72.0
            },
            caregiver_data={
                "name": "Test Caregiver",
                "relationship": "Daughter",
                "phone": "+1234567890"
            },
            safety_zone_data={
                "latitude": 16.7050,
                "longitude": 74.2433,
                "radius_meters": 100.0,
                "name": "Home"
            }
        )

        engine = AlertService()
        reading_high_hr = {
            "heart_rate": 128,  # > 90 threshold
            "spo2": 98,
            "temperature": 36.6,
            "fall_status": "NORMAL",
            "gps_status": "GPS LOCKED",
            "latitude": 16.7050,
            "longitude": 74.2433,
            "ble_room": "Living Room",
            "online": True
        }

        # First reading should trigger elevated HR alert
        alerts1 = engine.process_reading(patient_id, reading_high_hr)
        hr_alerts = [a for a in alerts1 if a["alert_type"] == ALERT_ELEVATED_HEART_RATE]
        self.assertEqual(len(hr_alerts), 1, "First high HR reading must trigger an alert")

        # Second immediate reading with same or another high HR should NOT trigger due to cooldown
        alerts2 = engine.process_reading(patient_id, reading_high_hr)
        hr_alerts_second = [a for a in alerts2 if a["alert_type"] == ALERT_ELEVATED_HEART_RATE]
        self.assertEqual(len(hr_alerts_second), 0, "Duplicate high HR alert must be prevented by cooldown")


if __name__ == "__main__":
    unittest.main()
