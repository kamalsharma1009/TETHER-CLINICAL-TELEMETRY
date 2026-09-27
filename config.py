"""
Configuration module for TETHER.
Loads environment variables and sets defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = BASE_DIR / "assets"
(ASSETS_DIR / "logo").mkdir(parents=True, exist_ok=True)

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Database Path
DB_PATH = str(DATA_DIR / "tether.db")


def get_secret(key: str, default: str = "") -> str:
    """
    Safely retrieves a configuration key from environment variables or Streamlit secrets.
    Never exposes keys in exceptions or logs.
    """
    # First try os.environ
    val = os.getenv(key, "")
    if val:
        return val

    # Try Streamlit secrets if running inside streamlit
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass

    return default


# Blynk Configuration
BLYNK_TOKEN = get_secret("BLYNK_TOKEN", "")
BLYNK_SERVER = get_secret("BLYNK_SERVER", "blynk.cloud")
BLYNK_BASE_URL = f"https://{BLYNK_SERVER}/external/api"

# Firebase Cloud Messaging
FIREBASE_CREDENTIALS_PATH = get_secret("FIREBASE_CREDENTIALS_PATH", "")
FIREBASE_CAREGIVER_FCM_TOKEN = get_secret("FIREBASE_CAREGIVER_FCM_TOKEN", "")

# App Defaults
DEFAULT_REFRESH_INTERVAL = int(get_secret("DEFAULT_REFRESH_INTERVAL", "3"))
REFRESH_OPTIONS = [1, 3, 5, 10]
APP_ENV = get_secret("APP_ENV", "development")
