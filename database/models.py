"""
Data models and schemas for TETHER
"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class PatientModel:
    id: Optional[int]
    name: str
    age: int
    gender: str
    date_of_birth: str
    blood_group: str
    height: float
    weight: float
    dementia_stage: str
    allergies: str
    medical_conditions: str
    doctor_name: str
    doctor_contact: str
    address: str
    preferred_language: str
    device_id: str
    baseline_hr: float = 72.0

    def to_dict(self):
        return asdict(self)


@dataclass
class CaregiverModel:
    id: Optional[int]
    patient_id: int
    name: str
    relationship: str
    phone: str
    emergency_contact: str
    notification_enabled: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass
class SafetyZoneModel:
    id: Optional[int]
    patient_id: int
    latitude: float
    longitude: float
    radius_meters: float
    name: str = "Home Safe Zone"

    def to_dict(self):
        return asdict(self)


@dataclass
class SensorReadingModel:
    heart_rate: Optional[int]
    spo2: Optional[int]
    temperature: Optional[float]
    fall_status: str
    gps_status: str
    latitude: Optional[float]
    longitude: Optional[float]
    ble_room: str
    timestamp: str

    def to_dict(self):
        return asdict(self)


@dataclass
class AlertModel:
    id: Optional[int]
    patient_id: int
    alert_type: str
    severity: str
    message: str
    value: str
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: str
    notification_status: str = "PENDING"

    def to_dict(self):
        return asdict(self)
