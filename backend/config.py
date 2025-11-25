import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Application configuration (SQLite locally, PostgreSQL on Render)."""

    # ================= SECURITY =================
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # ================= DATABASE =================
    # If DATABASE_URL is set (Render / production), use it.
    # Otherwise fall back to local SQLite file: site.db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "site.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ================= AUDIO STORAGE =================
    AUDIO_OUTPUT_DIR = os.environ.get("AUDIO_OUTPUT_DIR", "static/audio")

    # ================= APP SETTINGS =================
    MAX_TEXT_LENGTH = int(os.environ.get("MAX_TEXT_LENGTH", 5000))

    # ================= RAZORPAY (TEST / LIVE) =================
    # These should be set in the environment on Render.
    RAZORPAY_KEY_ID = os.environ.get(
        "RAZORPAY_KEY_ID",
        "rzp_test_XXXXXXXXXXXX"  # optional local default
    )
    RAZORPAY_KEY_SECRET = os.environ.get(
        "RAZORPAY_KEY_SECRET",
        "your_test_key_secret_here"  # optional local default
    )

    # Optional: webhook secret can also be environment-driven if you want
    RAZORPAY_WEBHOOK_SECRET = os.environ.get(
        "RAZORPAY_WEBHOOK_SECRET",
        "test_webhook_secret"
    )


def get_config():
    """Return the config class used by app.py"""
    return Config
