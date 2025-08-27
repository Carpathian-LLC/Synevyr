# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Configuration classes for Flask application

# ------------------------------------------------------------------------------------
# Imports:
import os
import tempfile
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Local Imports
import app.utils.initialize_db as initialize_db

# ------------------------------------------------------------------------------------
# Vars
BASE_DIR = Path(__file__).resolve().parents[2]

dotenv_path = os.path.join(BASE_DIR, "keys.env")
load_dotenv(dotenv_path)

# Server Version(s)
BACKEND_VERSION = "1.0.0"

FRONTEND_VERSION = "1.0.0"

# ------------------------------------------------------------------------------------
# Classes
class Config:
    SECRET_KEY = os.getenv("FLASK_SESSION_KEY", "fallback_session_key")
    SESSION_TYPE = "redis"
    SESSION_FILE_DIR = os.path.join(BASE_DIR, "session_files")
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_NAME = "session"
    permanent_session_lifetime = timedelta(days=2)
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
    IP_BLOCK_TIME = timedelta(minutes=15)
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "redis://localhost:6379")
    RELOAD_FILES = [str(p) for p in Path("templates").glob("**/*.html")]
    # Logging and Debugging
    LOGGING_DETAIL = os.getenv("LOGGING_DETAIL", "comprehensive")  # Options: "comprehensive", "simple"
    SPECIFIC_PAGES = os.getenv("SPECIFIC_PAGES", "").split(",") if os.getenv("SPECIFIC_PAGES") else []
    SQL_LOGGING = os.getenv("SQL_LOGGING", "true").lower() == "true"
    DB_MODE = os.getenv("DB_MODE", "prod")

class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"
    SERVER_NAME = "api.synevyr.org"
    PREFERRED_URL_SCHEME = "https"
    SESSION_COOKIE_SECURE = "Lax"
    SESSION_COOKIE_SAMESITE = "Strict"
    SESSION_COOKIE_DOMAIN = ".synevyr.org"
    SESSION_PROTECTION = "strong"
    SQLALCHEMY_DATABASE_URI = initialize_db.get_sqlalchemy_database_uri("production")
    STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    MAX_ATTEMPTS = 5
    SUSPENSION_TIME = timedelta(minutes=15)
    MAX_IP_ATTEMPTS = 10
    DOMAIN = "https://api.synevyr.org"
    HOST = "192.168.2.110"
    PORT = 2001

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"
    SQLALCHEMY_DATABASE_URI = initialize_db.get_sqlalchemy_database_uri("development")
    PREFERRED_URL_SCHEME = "http"
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_DOMAIN = None
    STRIPE_API_KEY = os.getenv("STRIPE_TEST_API_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_TEST_WEBHOOK")
    MAX_ATTEMPTS = 9999
    SUSPENSION_TIME = timedelta(minutes=2)
    MAX_IP_ATTEMPTS = 100
    DOMAIN = "http://127.0.0.1:2001/"
    HOST = "127.0.0.1"
    PORT = 2001
    ADMIN_PASSWORD = os.getenv("DEV_ADMIN_PASSWORD")

class DeploymentError(Exception):
    def __init__(self, stage: str, details: dict):
        super().__init__(f"{stage} failed: {details}")
        self.stage = stage
        self.details = details
