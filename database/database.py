"""
SQLite Database Layer for TETHER.
Handles schema initialization, CRUD operations, and transaction management.
"""
import sqlite3
import datetime
from typing import Dict, Any, List, Optional
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Creates a database connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Patients table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT,
        date_of_birth TEXT,
        blood_group TEXT,
        height REAL,
        weight REAL,
        dementia_stage TEXT NOT NULL,
        allergies TEXT,
        medical_conditions TEXT,
        doctor_name TEXT,
        doctor_contact TEXT,
        address TEXT NOT NULL,
        preferred_language TEXT,
        device_id TEXT NOT NULL,
        baseline_hr REAL DEFAULT 72.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Caregivers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS caregivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        relationship TEXT NOT NULL,
        phone TEXT NOT NULL,
        emergency_contact TEXT,
        notification_enabled INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
    );
    """)

    # Safety zones table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS safety_zones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        radius_meters REAL NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
    );
    """)

    # Sensor readings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        heart_rate INTEGER,
        spo2 INTEGER,
        temperature REAL,
        fall_status TEXT,
        gps_status TEXT,
        latitude REAL,
        longitude REAL,
        ble_room TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
    );
    """)

    # Alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        alert_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        value TEXT,
        latitude REAL,
        longitude REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notification_status TEXT DEFAULT 'PENDING',
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()


# Patient operations
def save_patient(patient_data: Dict[str, Any], caregiver_data: Dict[str, Any], safety_zone_data: Optional[Dict[str, Any]] = None) -> int:
    """Inserts a new patient, caregiver, and initial safety zone atomically."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        now = datetime.datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO patients (
            name, age, gender, date_of_birth, blood_group, height, weight,
            dementia_stage, allergies, medical_conditions, doctor_name, doctor_contact,
            address, preferred_language, device_id, baseline_hr, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_data.get("name"),
            patient_data.get("age"),
            patient_data.get("gender", ""),
            patient_data.get("date_of_birth", ""),
            patient_data.get("blood_group", ""),
            patient_data.get("height", 0.0),
            patient_data.get("weight", 0.0),
            patient_data.get("dementia_stage"),
            patient_data.get("allergies", ""),
            patient_data.get("medical_conditions", ""),
            patient_data.get("doctor_name", ""),
            patient_data.get("doctor_contact", ""),
            patient_data.get("address"),
            patient_data.get("preferred_language", "English"),
            patient_data.get("device_id"),
            patient_data.get("baseline_hr", 72.0),
            now,
            now
        ))
        patient_id = cursor.lastrowid

        # Insert caregiver
        cursor.execute("""
        INSERT INTO caregivers (
            patient_id, name, relationship, phone, emergency_contact, notification_enabled, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            caregiver_data.get("name"),
            caregiver_data.get("relationship"),
            caregiver_data.get("phone"),
            caregiver_data.get("emergency_contact", ""),
            1 if caregiver_data.get("notification_enabled", True) else 0,
            now
        ))

        # Insert safety zone if provided
        if safety_zone_data and safety_zone_data.get("latitude") and safety_zone_data.get("longitude"):
            cursor.execute("""
            INSERT INTO safety_zones (
                patient_id, latitude, longitude, radius_meters, name, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                float(safety_zone_data["latitude"]),
                float(safety_zone_data["longitude"]),
                float(safety_zone_data.get("radius_meters", 100.0)),
                safety_zone_data.get("name", "Home Safe Zone"),
                now
            ))

        conn.commit()
        return patient_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_patient_profile(patient_id: int, updates: Dict[str, Any]):
    """Updates selected patient details."""
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in updates.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(datetime.datetime.now().isoformat())
    values.append(patient_id)
    query = f"UPDATE patients SET {', '.join(fields)}, updated_at = ? WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()


def get_all_patients() -> List[Dict[str, Any]]:
    """Fetches all registered patients."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_patient(patient_id: int) -> Optional[Dict[str, Any]]:
    """Gets patient by id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_caregiver(patient_id: int) -> Optional[Dict[str, Any]]:
    """Gets caregiver for patient."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM caregivers WHERE patient_id = ? ORDER BY id DESC LIMIT 1", (patient_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_safety_zone(patient_id: int) -> Optional[Dict[str, Any]]:
    """Gets primary safety zone for patient."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM safety_zones WHERE patient_id = ? ORDER BY id DESC LIMIT 1", (patient_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_safety_zone(patient_id: int, lat: float, lon: float, radius: float, name: str = "Home Safe Zone"):
    """Updates or inserts the safety zone for a patient."""
    conn = get_connection()
    cursor = conn.cursor()
    existing = get_safety_zone(patient_id)
    if existing:
        cursor.execute("""
        UPDATE safety_zones
        SET latitude = ?, longitude = ?, radius_meters = ?, name = ?
        WHERE patient_id = ?
        """, (lat, lon, radius, name, patient_id))
    else:
        cursor.execute("""
        INSERT INTO safety_zones (patient_id, latitude, longitude, radius_meters, name)
        VALUES (?, ?, ?, ?, ?)
        """, (patient_id, lat, lon, radius, name))
    conn.commit()
    conn.close()


# Sensor reading operations
def log_sensor_reading(patient_id: int, reading: Dict[str, Any]) -> int:
    """Logs a normalized sensor reading record to SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sensor_readings (
        patient_id, timestamp, heart_rate, spo2, temperature,
        fall_status, gps_status, latitude, longitude, ble_room
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        reading.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        reading.get("heart_rate"),
        reading.get("spo2"),
        reading.get("temperature"),
        reading.get("fall_status"),
        reading.get("gps_status"),
        reading.get("latitude"),
        reading.get("longitude"),
        reading.get("ble_room")
    ))
    reading_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reading_id


def get_recent_sensor_readings(patient_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Gets the last N sensor readings for rolling charts (ordered chronologically)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM (
        SELECT * FROM sensor_readings
        WHERE patient_id = ?
        ORDER BY id DESC
        LIMIT ?
    ) ORDER BY id ASC
    """, (patient_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# Alert operations
def insert_alert(patient_id: int, alert_type: str, severity: str,
                 message: str, value: str = "",
                 latitude: Optional[float] = None, longitude: Optional[float] = None,
                 notification_status: str = "PENDING") -> int:
    """Inserts a new alert event into SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO alerts (
        patient_id, alert_type, severity, message, value,
        latitude, longitude, notification_status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        alert_type,
        severity,
        message,
        str(value),
        latitude,
        longitude,
        notification_status,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alert_id


def update_alert_notification_status(alert_id: int, status: str):
    """Updates notification dispatch status for an alert."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET notification_status = ? WHERE id = ?", (status, alert_id))
    conn.commit()
    conn.close()


def get_recent_alerts(patient_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent alerts for patient in reverse chronological order."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM alerts
    WHERE patient_id = ?
    ORDER BY id DESC
    LIMIT ?
    """, (patient_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_latest_alert_by_type(patient_id: int, alert_type: str) -> Optional[Dict[str, Any]]:
    """Retrieves the most recent alert of a specific type to evaluate cooldowns."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM alerts
    WHERE patient_id = ? AND alert_type = ?
    ORDER BY id DESC
    LIMIT 1
    """, (patient_id, alert_type))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
