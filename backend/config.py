import os


class Config:
    # ==================================================
    # General App Config
    # ==================================================
    SECRET_KEY = "your-secret-key-change-this-before-production"

    # SQLite DB location
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==================================================
    # Audio Config
    # ==================================================
    AUDIO_OUTPUT_DIR = "static/audio"
    MAX_TEXT_LENGTH = 5000  # Max characters per request

    # ==================================================
    # Razorpay Credentials (USE TEST KEYS FIRST)
    # ==================================================
    RAZORPAY_KEY_ID = "rzp_test_Rinv0dKvfIqeWm"
    RAZORPAY_KEY_SECRET = "XKWKAWvBZSBcNE7XiUvp67Vd"

    # ==================================================
    # Session / Security
    # ==================================================
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False   # Set True only if using HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 86400  # 1 day


# Optional: Development config
class DevelopmentConfig(Config):
    DEBUG = True


# Optional: Production config
class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Only if using HTTPS


# Function used in app.py
def get_config():
    return DevelopmentConfig
