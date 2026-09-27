"""
Validation utilities for patient registration and inputs
"""
import re
from typing import Dict, List, Tuple


def validate_patient_registration(data: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validates patient and caregiver registration form data.
    Returns: (is_valid: bool, error_messages: List[str])
    """
    errors: List[str] = []

    # Required patient fields
    if not data.get("name", "").strip():
        errors.append("Patient Name is required.")

    # Age validation
    age_str = str(data.get("age", "")).strip()
    if not age_str:
        errors.append("Age is required.")
    else:
        try:
            age = int(age_str)
            if age < 1 or age > 130:
                errors.append("Age must be between 1 and 130.")
        except ValueError:
            errors.append("Age must be a valid integer.")

    # Home address
    if not data.get("address", "").strip():
        errors.append("Home Address is required.")

    # Dementia stage
    dementia_stage = data.get("dementia_stage", "").strip()
    if not dementia_stage or dementia_stage not in ["Mild", "Moderate", "Severe"]:
        errors.append("Dementia Stage must be Mild, Moderate, or Severe.")

    # Caregiver fields
    if not data.get("caregiver_name", "").strip():
        errors.append("Caregiver Name is required.")

    if not data.get("relationship", "").strip():
        errors.append("Caregiver Relationship is required.")

    phone = str(data.get("phone", "")).strip()
    if not phone:
        errors.append("Caregiver Phone Number is required.")
    elif not re.match(r"^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$", phone):
        # Basic international or 10-digit phone format check
        if len(re.sub(r"\D", "", phone)) < 7:
            errors.append("Caregiver Phone Number seems invalid.")

    # Device ID
    if not data.get("device_id", "").strip():
        errors.append("Blynk Device ID is required.")

    # Coordinates validation if provided
    safe_lat = data.get("safe_zone_lat")
    safe_lon = data.get("safe_zone_lon")
    if safe_lat is not None and str(safe_lat).strip():
        try:
            lat_f = float(safe_lat)
            if not (-90.0 <= lat_f <= 90.0):
                errors.append("Safe Zone Latitude must be between -90 and 90.")
        except ValueError:
            errors.append("Safe Zone Latitude must be a numeric coordinate.")

    if safe_lon is not None and str(safe_lon).strip():
        try:
            lon_f = float(safe_lon)
            if not (-180.0 <= lon_f <= 180.0):
                errors.append("Safe Zone Longitude must be between -180 and 180.")
        except ValueError:
            errors.append("Safe Zone Longitude must be a numeric coordinate.")

    radius = data.get("safe_zone_radius")
    if radius is not None and str(radius).strip():
        try:
            rad_f = float(radius)
            if rad_f <= 0:
                errors.append("Safe Zone Radius must be greater than 0 meters.")
        except ValueError:
            errors.append("Safe Zone Radius must be a numeric value in meters.")

    return len(errors) == 0, errors
