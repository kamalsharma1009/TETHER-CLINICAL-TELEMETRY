"""
Patient Profile Management Page for TETHER
Displays complete patient medical dossier, caregiver links, and allows updating baseline HR and safe zones.
"""
import streamlit as st
from database.database import (
    get_all_patients,
    get_patient,
    get_caregiver,
    get_safety_zone,
    update_patient_profile,
    update_safety_zone
)
from utils.constants import MEDICAL_DISCLAIMER


def render_patient_profile_page():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h2 style="margin: 0; color: #FFFFFF; font-weight: 800; letter-spacing: 1px;">PATIENT CLINICAL & SAFETY PROFILE</h2>
            <p style="color: #94A3B8; font-size: 14px; margin-top: 4px;">
                Caregiver links, resting physiological baseline parameters, and configured geofence safe zones.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    all_patients = get_all_patients()
    if not all_patients:
        st.info("No registered patients found.")
        return

    patient_ids = [p["id"] for p in all_patients]
    selected_id = st.session_state.get("selected_patient_id", patient_ids[0])
    if selected_id not in patient_ids:
        selected_id = patient_ids[0]

    patient_options = {p["id"]: f"{p['name']} (ID: {p['id']}) - {p['dementia_stage']}" for p in all_patients}
    chosen_id = st.selectbox(
        "Select Patient Profile",
        options=patient_ids,
        index=patient_ids.index(selected_id),
        format_func=lambda pid: patient_options[pid]
    )

    patient = get_patient(chosen_id)
    caregiver = get_caregiver(chosen_id)
    safe_zone = get_safety_zone(chosen_id)

    if not patient:
        st.error("Patient details not found.")
        return

    # Tabs for Overview vs Edit Profile
    tab_view, tab_edit = st.tabs(["📋 Profile Overview", "✏️ Edit Patient & Baseline"])

    with tab_view:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### Patient Information")
            st.markdown(
                f"""
                <div style="background: #121824; border: 1px solid #1F2A3E; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
                    <p style="margin: 0 0 8px 0;"><b>Full Name:</b> {patient.get('name')}</p>
                    <p style="margin: 0 0 8px 0;"><b>Age:</b> {patient.get('age')} years | <b>Gender:</b> {patient.get('gender') or 'Not specified'}</p>
                    <p style="margin: 0 0 8px 0;"><b>Blood Group:</b> {patient.get('blood_group') or 'Unknown'} | <b>DOB:</b> {patient.get('date_of_birth') or 'N/A'}</p>
                    <p style="margin: 0 0 8px 0;"><b>Height:</b> {patient.get('height')} cm | <b>Weight:</b> {patient.get('weight')} kg</p>
                    <p style="margin: 0 0 8px 0;"><b>Home Address:</b> {patient.get('address')}</p>
                    <p style="margin: 0;"><b>Preferred Language:</b> {patient.get('preferred_language')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("#### Dementia & Clinical Baseline")
            baseline_hr = float(patient.get("baseline_hr") or 72.0)
            threshold_hr = round(baseline_hr * 1.25, 1)
            st.markdown(
                f"""
                <div style="background: #121824; border: 1px solid #1F2A3E; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
                    <p style="margin: 0 0 8px 0;"><b>Dementia Stage:</b> <span style="color: #FBBF24; font-weight: bold;">{patient.get('dementia_stage')}</span></p>
                    <p style="margin: 0 0 8px 0;"><b>Resting Heart Rate Baseline:</b> <span style="color: #10B981; font-weight: bold;">{baseline_hr:.0f} BPM</span></p>
                    <p style="margin: 0;"><b>Elevated HR Stress Threshold (+25%):</b> <span style="color: #EF4444; font-weight: bold;">{threshold_hr:.1f} BPM</span></p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_p2:
            st.markdown("#### Primary Caregiver")
            if caregiver:
                notif_badge = "✅ Enabled" if caregiver.get("notification_enabled") else "❌ Disabled"
                st.markdown(
                    f"""
                    <div style="background: #121824; border: 1px solid #1F2A3E; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
                        <p style="margin: 0 0 8px 0;"><b>Caregiver Name:</b> {caregiver.get('name')}</p>
                        <p style="margin: 0 0 8px 0;"><b>Relationship:</b> {caregiver.get('relationship')}</p>
                        <p style="margin: 0 0 8px 0;"><b>Phone:</b> {caregiver.get('phone')}</p>
                        <p style="margin: 0 0 8px 0;"><b>Emergency Contact:</b> {caregiver.get('emergency_contact') or 'N/A'}</p>
                        <p style="margin: 0;"><b>Push Notifications:</b> {notif_badge}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("No caregiver registered.")

            st.markdown("#### Medical Contacts & History")
            st.markdown(
                f"""
                <div style="background: #121824; border: 1px solid #1F2A3E; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
                    <p style="margin: 0 0 8px 0;"><b>Allergies:</b> {patient.get('allergies') or 'None reported'}</p>
                    <p style="margin: 0 0 8px 0;"><b>Existing Conditions:</b> {patient.get('medical_conditions') or 'None reported'}</p>
                    <p style="margin: 0 0 8px 0;"><b>Attending Doctor:</b> {patient.get('doctor_name') or 'N/A'}</p>
                    <p style="margin: 0;"><b>Doctor Contact:</b> {patient.get('doctor_contact') or 'N/A'}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("#### Configured Safe Zone & Device")
            if safe_zone:
                st.markdown(
                    f"""
                    <div style="background: #121824; border: 1px solid #1F2A3E; border-radius: 10px; padding: 16px;">
                        <p style="margin: 0 0 8px 0;"><b>Zone Name:</b> {safe_zone.get('name')}</p>
                        <p style="margin: 0 0 8px 0;"><b>Center Coordinates:</b> {safe_zone.get('latitude'):.5f}, {safe_zone.get('longitude'):.5f}</p>
                        <p style="margin: 0 0 8px 0;"><b>Safe Radius:</b> {safe_zone.get('radius_meters'):.0f} meters</p>
                        <p style="margin: 0;"><b>Wearable Device ID:</b> <code>{patient.get('device_id')}</code></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with tab_edit:
        st.markdown("#### Modify Patient & Baseline Settings")
        with st.form("edit_patient_form"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                edit_name = st.text_input("Patient Name", value=patient.get("name"))
                edit_age = st.number_input("Age", min_value=1, max_value=125, value=int(patient.get("age")))
                edit_stage = st.selectbox(
                    "Dementia Stage",
                    ["Mild", "Moderate", "Severe"],
                    index=["Mild", "Moderate", "Severe"].index(patient.get("dementia_stage")) if patient.get("dementia_stage") in ["Mild", "Moderate", "Severe"] else 1
                )
                edit_baseline_hr = st.number_input(
                    "Resting Baseline Heart Rate (BPM)",
                    min_value=40.0,
                    max_value=120.0,
                    value=float(patient.get("baseline_hr") or 72.0),
                    step=1.0,
                    help="Elevated HR stress alert will trigger at +25% above this value"
                )
                edit_address = st.text_area("Home Address", value=patient.get("address"))

            with col_e2:
                edit_device = st.text_input("Blynk Device ID / Template", value=patient.get("device_id"))
                edit_allergies = st.text_input("Allergies", value=patient.get("allergies") or "")
                edit_conditions = st.text_input("Medical Conditions", value=patient.get("medical_conditions") or "")
                edit_doctor = st.text_input("Doctor Name", value=patient.get("doctor_name") or "")
                edit_doctor_contact = st.text_input("Doctor Contact", value=patient.get("doctor_contact") or "")

            st.markdown("##### Safe Zone Geofence Updates")
            col_z1, col_z2, col_z3 = st.columns(3)
            with col_z1:
                z_name = st.text_input("Safe Zone Name", value=safe_zone.get("name", "Home") if safe_zone else "Home")
            with col_z2:
                z_lat = st.number_input("Latitude", value=float(safe_zone.get("latitude", 16.7050)) if safe_zone else 16.7050, format="%.6f")
            with col_z3:
                z_lon = st.number_input("Longitude", value=float(safe_zone.get("longitude", 74.2433)) if safe_zone else 74.2433, format="%.6f")
            z_radius = st.slider("Safe Zone Radius (meters)", min_value=25, max_value=1000, value=int(safe_zone.get("radius_meters", 100)) if safe_zone else 100, step=25)

            submit_edit = st.form_submit_button("Save Changes to Profile", use_container_width=True)

        if submit_edit:
            try:
                update_patient_profile(chosen_id, {
                    "name": edit_name.strip(),
                    "age": int(edit_age),
                    "dementia_stage": edit_stage,
                    "baseline_hr": float(edit_baseline_hr),
                    "address": edit_address.strip(),
                    "device_id": edit_device.strip(),
                    "allergies": edit_allergies.strip(),
                    "medical_conditions": edit_conditions.strip(),
                    "doctor_name": edit_doctor.strip(),
                    "doctor_contact": edit_doctor_contact.strip()
                })
                update_safety_zone(chosen_id, float(z_lat), float(z_lon), float(z_radius), z_name.strip())
                st.success("Patient profile and safety parameters updated successfully!")
                st.rerun()
            except Exception as ex:
                st.error(f"Error updating profile: {ex}")

    # Disclaimer
    st.markdown(
        f"""
        <div class="disclaimer-card">
            {MEDICAL_DISCLAIMER}
        </div>
        """,
        unsafe_allow_html=True
    )
