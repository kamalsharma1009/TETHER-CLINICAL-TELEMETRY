"""
Blynk IoT Service for TETHER
Template: Health Guard
Virtual Pin Mapping:
  V0 -> Heart Rate (Integer)
  V1 -> SpO2 (Integer)
  V2 -> Temperature (Double)
  V3 -> Fall Status (String)
  V4 -> GPS Status (String)
  V5 -> Latitude (Double)
  V6 -> Longitude (Double)
  V7 -> BLE Room (String)
"""
import datetime
import logging
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import BLYNK_TOKEN, BLYNK_SERVER
from utils.constants import BLYNK_PINS

logger = logging.getLogger("TETHER_Blynk")
logging.basicConfig(level=logging.INFO)


class BlynkService:
    def __init__(self, token: Optional[str] = None, server: Optional[str] = None):
        self.token = (token or BLYNK_TOKEN or "").strip()
        self.server = (server or BLYNK_SERVER or "blynk.cloud").strip()
        self.base_url = f"https://{self.server}/external/api"

        # Setup requests session with retry strategy
        self.session = requests.Session()
        retries = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

        self.last_successful_reading: Optional[str] = None
        self.consecutive_failures: int = 0
        self.is_connected: bool = False

    def is_configured(self) -> bool:
        """Check if Blynk token is provided."""
        return bool(self.token)

    def check_hardware_status(self) -> bool:
        """
        Queries Blynk API isHardwareConnected endpoint.
        Returns True if hardware device is online, False otherwise.
        """
        if not self.is_configured():
            return False

        try:
            url = f"{self.base_url}/isHardwareConnected"
            params = {"token": self.token}
            response = self.session.get(url, params=params, timeout=3.0)
            if response.status_code == 200:
                text = response.text.strip().lower()
                return text in ["true", "1"]
        except Exception as e:
            logger.warning(f"Blynk hardware status check failed: {type(e).__name__}")
        return False

    def fetch_pin_value(self, pin: str) -> Optional[str]:
        """
        Fetch a single virtual pin value from Blynk external API.
        Endpoint: /external/api/get?token={token}&{pin}
        """
        if not self.is_configured():
            return None

        try:
            url = f"{self.base_url}/get"
            params = {"token": self.token, pin: ""}
            response = self.session.get(url, params=params, timeout=3.0)
            if response.status_code == 200:
                return response.text.strip()
            else:
                logger.warning(f"Blynk returned status {response.status_code} for pin {pin}")
                return None
        except Exception as e:
            logger.warning(f"Error fetching pin {pin}: {type(e).__name__}")
            return None

    def fetch_all_pins(self) -> Dict[str, Any]:
        """
        Retrieves all datastreams (V0 - V7) from Blynk API.
        Attempts batch /getAll first, falls back to individual pin calls if needed.
        Returns a normalized data dictionary.
        """
        timestamp_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not self.is_configured():
            return {
                "heart_rate": None,
                "spo2": None,
                "temperature": None,
                "fall_status": "NORMAL",
                "gps_status": "NO GPS FIX",
                "latitude": 0.0,
                "longitude": 0.0,
                "ble_room": "UNKNOWN",
                "timestamp": timestamp_now,
                "online": False,
                "status_message": "Blynk token not configured",
                "raw_pins": {}
            }

        raw_values: Dict[str, Any] = {}
        fetch_success = False

        # Try multi-pin get endpoint: /external/api/getAll?token=...&v0&v1...
        try:
            url = f"{self.base_url}/getAll"
            pins_query = {f"v{i}": "" for i in range(8)}
            pins_query["token"] = self.token
            response = self.session.get(url, params=pins_query, timeout=4.0)

            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        for k, v in data.items():
                            raw_values[k.upper()] = v
                        fetch_success = True
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Batch getAll failed, falling back to individual pins: {type(e).__name__}")

        # Fallback to individual pin fetching if batch did not populate
        if not fetch_success or len(raw_values) < 4:
            for pin_name, pin_code in BLYNK_PINS.items():
                val = self.fetch_pin_value(pin_code)
                if val is not None:
                    raw_values[pin_code] = val
                    fetch_success = True

        if fetch_success:
            self.consecutive_failures = 0
            self.last_successful_reading = timestamp_now
            self.is_connected = True
            status_msg = "ONLINE"
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= 3:
                self.is_connected = False
                status_msg = "CONNECTION LOST"
            else:
                status_msg = "RETRYING"

        # Parse and normalize values
        normalized = self.normalize_readings(raw_values, timestamp_now)
        normalized["online"] = self.is_connected
        normalized["status_message"] = status_msg
        normalized["last_successful_reading"] = self.last_successful_reading
        normalized["raw_pins"] = raw_values

        return normalized

    def normalize_readings(self, raw_pins: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """
        Converts raw Blynk pin values to typed, clean Python types.
        V0: int, V1: int, V2: float, V3: str, V4: str, V5: float, V6: float, V7: str.
        """
        # V0: Heart Rate (int)
        v0 = raw_pins.get("V0")
        hr_val: Optional[int] = None
        if v0 is not None:
            try:
                hr_val = int(float(str(v0).strip()))
                if hr_val <= 20 or hr_val > 250:
                    hr_val = None
            except (ValueError, TypeError):
                hr_val = None

        # V1: SpO2 (int)
        v1 = raw_pins.get("V1")
        spo2_val: Optional[int] = None
        if v1 is not None:
            try:
                spo2_val = int(float(str(v1).strip()))
                if spo2_val <= 0 or spo2_val > 100:
                    spo2_val = None
            except (ValueError, TypeError):
                spo2_val = None

        # V2: Temperature (float)
        v2 = raw_pins.get("V2")
        temp_val: Optional[float] = None
        if v2 is not None:
            try:
                temp_val = round(float(str(v2).strip()), 1)
                # Temperatures <= 20°C or > 50°C indicate disconnected or invalid sensor
                if temp_val <= 20.0 or temp_val > 50.0:
                    temp_val = None
            except (ValueError, TypeError):
                temp_val = None

        # V3: Fall Status (String: "NORMAL", "FALL", "FALL DETECTED")
        v3 = raw_pins.get("V3")
        fall_val = str(v3).strip() if v3 is not None and str(v3).strip() else "NORMAL"

        # V4: GPS Status (String: "GPS LOCKED", "NO GPS FIX")
        v4 = raw_pins.get("V4")
        gps_status_val = str(v4).strip() if v4 is not None and str(v4).strip() else "NO GPS FIX"

        # V5: Latitude (float)
        v5 = raw_pins.get("V5")
        lat_val = 0.0
        if v5 is not None:
            try:
                lat_val = float(str(v5).strip())
            except (ValueError, TypeError):
                lat_val = 0.0

        # V6: Longitude (float)
        v6 = raw_pins.get("V6")
        lon_val = 0.0
        if v6 is not None:
            try:
                lon_val = float(str(v6).strip())
            except (ValueError, TypeError):
                lon_val = 0.0

        # V7: BLE Room (String: "Living Room", "Bedroom", "UNKNOWN")
        v7 = raw_pins.get("V7")
        ble_room_val = str(v7).strip() if v7 is not None and str(v7).strip() else "UNKNOWN"

        return {
            "heart_rate": hr_val,
            "spo2": spo2_val,
            "temperature": temp_val,
            "fall_status": fall_val,
            "gps_status": gps_status_val,
            "latitude": lat_val,
            "longitude": lon_val,
            "ble_room": ble_room_val,
            "timestamp": timestamp
        }


blynk_service = BlynkService()
