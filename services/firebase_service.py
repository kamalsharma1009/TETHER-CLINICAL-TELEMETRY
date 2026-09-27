"""
Firebase Cloud Messaging (FCM) & Caregiver Notification Service for TETHER
Abstracted notification architecture to send push notifications via Firebase Admin SDK.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from config import FIREBASE_CREDENTIALS_PATH, FIREBASE_CAREGIVER_FCM_TOKEN

logger = logging.getLogger("TETHER_Firebase")


class FirebaseService:
    def __init__(self):
        self.initialized = False
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Attempts to initialize Firebase Admin SDK safely without raising uncaught exceptions."""
        try:
            import firebase_admin
            from firebase_admin import credentials

            # If already initialized
            if firebase_admin._apps:
                self.initialized = True
                return

            cred_path = FIREBASE_CREDENTIALS_PATH
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self.initialized = True
                logger.info("Firebase Admin initialized from credentials file.")
            elif os.getenv("FIREBASE_CREDENTIALS_JSON"):
                try:
                    cred_dict = json.loads(os.environ["FIREBASE_CREDENTIALS_JSON"])
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    self.initialized = True
                    logger.info("Firebase Admin initialized from JSON environment variable.")
                except Exception as ex:
                    logger.warning(f"Failed to parse FIREBASE_CREDENTIALS_JSON: {ex}")
            else:
                logger.info("Firebase credentials not configured. FCM notifications will be simulated/logged.")
        except Exception as e:
            logger.warning(f"Firebase Admin SDK initialization skipped/failed: {e}")
            self.initialized = False

    def send_push_notification(
        self,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends push notification via Firebase Cloud Messaging if configured,
        or logs simulation if running locally/demo.
        Returns delivery status dictionary.
        """
        target_token = token or FIREBASE_CAREGIVER_FCM_TOKEN

        if not self.initialized:
            return {
                "success": False,
                "status": "SIMULATED",
                "message": "Firebase service-account not configured (Notification logged locally)",
                "details": f"Title: {title} | Body: {body}"
            }

        if not target_token:
            return {
                "success": False,
                "status": "TOKEN_MISSING",
                "message": "Caregiver FCM device registration token unavailable",
                "details": f"Title: {title} | Body: {body}"
            }

        try:
            from firebase_admin import messaging
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=target_token
            )
            response = messaging.send(message)
            return {
                "success": True,
                "status": "SENT",
                "message_id": response,
                "message": "FCM Push Notification sent successfully"
            }
        except Exception as e:
            logger.error(f"FCM Notification dispatch error: {e}")
            return {
                "success": False,
                "status": "FAILED",
                "message": f"FCM Error: {str(e)}",
                "details": f"Title: {title} | Body: {body}"
            }


class NotificationService:
    """
    Unified, abstract notification coordinator.
    Delegates to Firebase FCM and supports future SMS providers seamlessly.
    """
    def __init__(self):
        self.firebase = FirebaseService()

    def dispatch_alert_notification(
        self,
        alert_type: str,
        severity: str,
        message: str,
        patient_name: str,
        caregiver_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Formats and dispatches the alert notification to the caregiver.
        """
        title = f"TETHER ALERT: {alert_type.replace('_', ' ').title()}"
        body = f"Patient: {patient_name}\n{message}"

        data_payload = {
            "alert_type": alert_type,
            "severity": severity,
            "patient": patient_name,
        }

        # Dispatch FCM Push Notification
        fcm_result = self.firebase.send_push_notification(
            title=title,
            body=body,
            data=data_payload
        )

        return fcm_result


notification_service = NotificationService()
