# TETHER — Dementia Patient Monitoring System

**TETHER** is a caregiver-facing web monitoring dashboard and IoT intelligence prototype engineered in Python and Streamlit. It connects to the Blynk Cloud IoT platform ("Health Guard" template) to monitor dementia patients in real-time, detect elevated physiological stress conditions, identify falls, track outdoor GPS coordinates with geofencing wandering detection, maintain auditable alert histories, and dispatch push notifications to caregivers.

---

## 🛡️ Key Features

- **Real-Time Streaming Dashboard**: Powered by modern `@st.fragment(run_every="3s")` for efficient partial-page re-rendering without full application reload.
- **Blynk IoT Cloud Integration**: Direct mapping to the official **Health Guard** template datastreams (V0–V7) with automated retry and connection loss detection.
- **Elevated Heart Rate / Stress Detection**: Triggers alerts when heart rate exceeds `baseline_hr * 1.25` (+25% increase).
- **Fall Detection**: Normalizes V3 fall status (`NORMAL`, `FALL`, `FALL DETECTED`) and renders prominent critical red emergency banners.
- **Outdoor GPS & Geofencing**: Computes Haversine distance from the patient's safe zone; flags geofence wander breaches and renders interactive Folium satellite/dark maps.
- **Hardware Data Transparency**: Distinguishes between live sensor data, calculated data, and unavailable streams (`HRV Data Unavailable`). No fabricated or fake biometric signals.
- **Alert Suppression Cooldowns**: Prevents repetitive duplicate alert spamming during persistent emergency states.
- **Caregiver Push Notifications**: Abstracted notification service supporting Firebase Cloud Messaging (FCM) Admin SDK.
- **Controlled Demo Mode**: One-click presentation triggers for simulating elevated heart rate, fall detection, wander breaches, and GPS loss.

---

## 📡 Blynk Datastream Configuration (Health Guard Template)

| Virtual Pin | Parameter | Data Type | Description |
|:---:|:---:|:---:|:---|
| **V0** | Heart Rate | Integer | Patient beats per minute (BPM) |
| **V1** | SpO₂ | Integer | Blood oxygen saturation percentage (%) |
| **V2** | Temperature | Double | Skin/body temperature (°C) |
| **V3** | Fall Status | String | `"NORMAL"`, `"FALL"`, `"FALL DETECTED"` |
| **V4** | GPS Status | String | `"GPS LOCKED"`, `"NO GPS FIX"` |
| **V5** | Latitude | Double | GPS Latitude coordinate |
| **V6** | Longitude | Double | GPS Longitude coordinate |
| **V7** | BLE Room | String | Indoor beacon room (`"Living Room"`, `"Bedroom"`, etc.) |

> **⚠️ Hardware Stream Limitations:**  
> The current hardware template does **not** expose HRV, ECG, or GSR. TETHER explicitly labels HRV as `"HRV Data Unavailable"` and does **not** fabricate synthetic biometric waveforms.

---

## 🏗️ Project Architecture

```
TETHER/
├── app.py                     # Streamlit application entrypoint & router
├── config.py                  # Environment config & secrets manager
├── requirements.txt           # Python dependencies
├── README.md                  # Comprehensive documentation
├── .env                       # Local environment variables (Blynk token)
├── .env.example               # Template environment configuration
├── .gitignore                 # Secrets, cache, and database protection
│
├── database/
│   ├── __init__.py
│   ├── database.py            # SQLite schema initialization & thread-safe CRUD
│   └── models.py              # Dataclass schemas
│
├── services/
│   ├── __init__.py
│   ├── blynk_service.py       # Blynk REST API client & stream normalizer
│   ├── alert_service.py       # Threshold evaluation, cooldowns & alert dispatcher
│   ├── location_service.py    # Haversine distance & geofence boundary evaluator
│   └── firebase_service.py    # Firebase Cloud Messaging push notification handler
│
├── pages/
│   ├── __init__.py
│   ├── dashboard.py           # Real-time monitoring dashboard with @st.fragment
│   ├── registration.py        # Patient & caregiver registration form
│   ├── alerts.py              # Chronological incident audit log & filters
│   ├── patient_profile.py     # Patient dossier & in-place baseline HR editor
│   └── settings_page.py       # Blynk token, cooldown limits, and FCM settings
│
├── components/
│   ├── __init__.py
│   ├── header.py              # Custom dark IoT header with live status pill
│   ├── metric_cards.py        # Vitals cards (HR, SpO2, Temp, Fall, GPS, BLE)
│   ├── charts.py              # Plotly rolling trend line with threshold guides
│   ├── map.py                 # Folium interactive map with geofence circle
│   └── alerts_panel.py        # Emergency red fall banner & recent event history
│
├── utils/
│   ├── __init__.py
│   ├── calculations.py        # Haversine distance, stress thresholds, fall checks
│   ├── validators.py          # Form input & coordinate validation
│   └── constants.py           # Pins, alert types, cooldowns, and disclaimer
│
├── tests/
│   ├── __init__.py
│   └── test_tether.py         # Unit tests (Blynk, Haversine, Fall, HR, Cooldown)
│
├── assets/
│   └── style.css              # Custom dark healthcare / IoT stylesheet
│
└── data/
    └── tether.db              # SQLite relational database
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.10+ installed

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Credentials (`.env`)
Copy `.env.example` to `.env`:
```env
BLYNK_TOKEN=your_blynk_auth_token_here
BLYNK_SERVER=blynk.cloud
```
*(Leave empty or unconfigured to automatically run in Demo Simulation mode).*

### 4. Run Unit Tests
```bash
python -m unittest tests/test_tether.py
```

### 5. Launch the Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🎓 College Presentation Demo Flow

To demonstrate the full end-to-end capabilities during your presentation:

1. Click **"🚀 Load Complete Demo Scenario"** in the sidebar. This registers patient **Aarav Sharma** (Age 72, Moderate Dementia, Resting Baseline 72 BPM, Safe Zone: Kolhapur 100m radius).
2. The **Live Dashboard** opens showing normal status:
   - Heart Rate: **76 BPM** (NORMAL)
   - SpO₂: **97%** (NORMAL)
   - Temperature: **36.7 °C** (NORMAL)
   - Fall: **NORMAL**
   - GPS: **GPS LOCKED**
   - Geofence: **INSIDE SAFE ZONE**
3. **Trigger High Heart Rate**:
   - Click the `❤️ High HR (128)` button in the demo bar.
   - The dashboard updates: Heart Rate turns red (`128 BPM`), the alert engine logs `ELEVATED_HEART_RATE`, and the Plotly rolling trend line shows the spike crossing the 90 BPM threshold (+25%).
4. **Trigger Fall Detection**:
   - Click the `🚨 Fall Alert` button.
   - A critical red banner `CRITICAL ALERT: POSSIBLE FALL DETECTED` pulses across the screen, and the incident is pushed to caregiver notifications.
5. **Trigger Geofence Breach**:
   - Click `📍 Geofence Out`.
   - The patient coordinates shift outside the 100m radius. The map updates showing the patient marker in red outside the green safe zone circle, and a `GEOFENCE BREACH` warning triggers.
6. **Review Incident Audit Log**:
   - Navigate to **"🔔 Incident Alerts Log"** in the sidebar to review timestamps, sensor readings, and notification delivery statuses.

---

## ⚕️ Medical Safety Disclaimer

> **TETHER is a monitoring prototype and is not a medical diagnostic system.**  
> Sensor readings and alerts should not replace professional medical advice, clinical diagnoses, or emergency medical response services.
