"""
Patient and Caregiver Registration Page for TETHER
"""
import streamlit as st
from database.database import save_patient, get_all_patients
from utils.validators import validate_patient_registration
from utils.constants import MEDICAL_DISCLAIMER


def render_registration_page():
    """Renders the comprehensive patient and caregiver registration form."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h2 style="margin: 0; color: #FFFFFF; font-weight: 800; letter-spacing: 1px;">PATIENT & CAREGIVER REGISTRATION</h2>
            <p style="color: #94A3B8; font-size: 14px; margin-top: 4px;">
                Register a dementia patient, link their wearable IoT device, and configure geofence safe zones.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("patient_registration_form", clear_on_submit=False):
        # Section 1: Personal Information
        st.markdown("#### 1. Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Patient Full Name *", placeholder="e.g. Aarav Sharma")
            age = st.number_input("Age *", min_value=1, max_value=125, value=72, step=1)
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
            dob = st.text_input("Date of Birth", placeholder="YYYY-MM-DD (e.g. 1954-05-14)")
        with col2:
            blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])
            col_hw1, col_hw2 = st.columns(2)
            with col_hw1:
                height = st.number_input("Height (cm)", min_value=0.0, max_value=250.0, value=170.0, step=0.5)
            with col_hw2:
                weight = st.number_input("Weight (kg)", min_value=0.0, max_value=250.0, value=68.0, step=0.5)
            preferred_language = st.selectbox("Preferred Language", ["English", "Hindi", "Marathi", "Tamil", "Other"])
            address = st.text_area("Home Address *", placeholder="Residential home address...")

        st.divider()

        # Section 2: Dementia Details
        st.markdown("#### 2. Clinical Assessment")
        col_dem1, col_dem2 = st.columns(2)
        with col_dem1:
            dementia_stage = st.selectbox(
                "Dementia Stage *",
                ["Mild", "Moderate", "Severe"],
                index=1,
                help="Clinical assessment stage determines wander-risk thresholds and monitoring urgency."
            )
        with col_dem2:
            baseline_hr = st.number_input(
                "Resting Baseline Heart Rate (BPM)",
                min_value=40.0,
                max_value=120.0,
                value=72.0,
                step=1.0,
                help="Caregiver-configured resting HR. Elevated HR alert triggers at +25% above this value."
            )

        st.divider()

        # Section 3: Caregiver Information
        st.markdown("#### 3. Primary Caregiver Details")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            caregiver_name = st.text_input("Caregiver Name *", placeholder="e.g. Rohit Sharma")
            relationship = st.selectbox("Relationship to Patient *", ["Son", "Daughter", "Spouse", "Sibling", "Professional Nurse", "Other"])
        with col_c2:
            phone = st.text_input("Primary Phone Number *", placeholder="+91 9876543210")
            emergency_contact = st.text_input("Secondary Emergency Contact", placeholder="+91 9876543211")
        notifications_enabled = st.checkbox("Enable Push & Alert Notifications for this Caregiver", value=True)

        st.divider()

        # Section 4: Medical Details
        st.markdown("#### 4. Medical Background (Optional)")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            allergies = st.text_input("Allergies", placeholder="Penicillin, Sulfa, Dust, etc.")
            medical_conditions = st.text_input("Existing Conditions", placeholder="Hypertension, Diabetes Type 2, etc.")
        with col_m2:
            doctor_name = st.text_input("Attending Physician", placeholder="Dr. V. Rao")
            doctor_contact = st.text_input("Doctor Contact Number", placeholder="+91 9123456780")

        st.divider()

        # Section 5: Safety Zone & Geofence
        st.markdown("#### 5. Safety Geofence & Wearable IoT Device")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            safe_name = st.text_input("Safe Zone Label", value="Home Residence")
            device_id = st.text_input("Blynk Device ID / Tag *", value="Health Guard", help="Hardware device identifier or Blynk template name")
        with col_s2:
            safe_lat = st.number_input("Safe Zone Latitude", value=16.7050, format="%.6f", help="Center point for safe zone")
        with col_s3:
            safe_lon = st.number_input("Safe Zone Longitude", value=74.2433, format="%.6f", help="Center point for safe zone")
        safe_radius = st.slider("Safe Geofence Radius (meters)", min_value=25, max_value=1000, value=100, step=25)

        st.markdown("<br>", unsafe_allow_html=True)
        submit_button = st.form_submit_button("Complete Registration & Launch Dashboard", use_container_width=True)

    if submit_button:
        form_payload = {
            "name": name,
            "age": age,
            "gender": gender,
            "date_of_birth": dob,
            "blood_group": blood_group,
            "height": height,
            "weight": weight,
            "address": address,
            "preferred_language": preferred_language,
            "dementia_stage": dementia_stage,
            "baseline_hr": baseline_hr,
            "caregiver_name": caregiver_name,
            "relationship": relationship,
            "phone": phone,
            "emergency_contact": emergency_contact,
            "device_id": device_id,
            "safe_zone_lat": safe_lat,
            "safe_zone_lon": safe_lon,
            "safe_zone_radius": safe_radius
        }

        is_valid, error_msgs = validate_patient_registration(form_payload)

        if not is_valid:
            for err in error_msgs:
                st.error(f"⚠ {err}")
        else:
            try:
                patient_data = {
                    "name": name.strip(),
                    "age": int(age),
                    "gender": gender,
                    "date_of_birth": dob.strip(),
                    "blood_group": blood_group,
                    "height": float(height),
                    "weight": float(weight),
                    "dementia_stage": dementia_stage,
                    "allergies": allergies.strip(),
                    "medical_conditions": medical_conditions.strip(),
                    "doctor_name": doctor_name.strip(),
                    "doctor_contact": doctor_contact.strip(),
                    "address": address.strip(),
                    "preferred_language": preferred_language,
                    "device_id": device_id.strip(),
                    "baseline_hr": float(baseline_hr)
                }

                caregiver_data = {
                    "name": caregiver_name.strip(),
                    "relationship": relationship,
                    "phone": phone.strip(),
                    "emergency_contact": emergency_contact.strip(),
                    "notification_enabled": notifications_enabled
                }

                safety_zone_data = {
                    "latitude": float(safe_lat),
                    "longitude": float(safe_lon),
                    "radius_meters": float(safe_radius),
                    "name": safe_name.strip() or "Home Safe Zone"
                }

                new_id = save_patient(patient_data, caregiver_data, safety_zone_data)
                st.session_state["selected_patient_id"] = new_id
                st.session_state["current_page"] = "Dashboard"
                st.success(f"Patient '{name}' successfully registered with ID #{new_id}!")
                st.rerun()

            except Exception as e:
                st.error(f"Error saving patient: {str(e)}")

    # Footer disclaimer
    st.markdown(
        f"""
        <div class="disclaimer-card">
            {MEDICAL_DISCLAIMER}
        </div>
        """,
        unsafe_allow_html=True
    )
