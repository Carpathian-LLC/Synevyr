# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Authorized.
# ------------------------------------------------------------------------------------
# Notes:

# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime
import hashlib
import os
import logging
from pathlib import Path
import traceback
import uuid
from flask import has_request_context, session, request, g
from flask_jwt_extended import current_user
from sqlalchemy import Engine, event
from sqlalchemy.engine import Connection

# Local Imports
from app.extensions import db
from app.core.config import Config

# ------------------------------------------------------------------------------------
# Var Decs
BASE_DIR = Path(__file__).resolve().parents[3]
LOG_DIR = BASE_DIR / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ------------------------------------------------------------------------------------
# Primary (app wide) Logger

def get_named_logger(name, filename, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        filepath = os.path.join(LOG_DIR, filename)
        fh = logging.FileHandler(filepath, mode='w')
        fh.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

def configure_logging(logging_detail="comprehensive", specific_pages=None, sql_logging=False):
    """
    Configure logging with optional SQL and page-level targeting.
    """
    # Set up base log config if desired
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if logging_detail == "comprehensive" else logging.INFO)

    if not root_logger.handlers:
        fh = logging.FileHandler(LOG_DIR / "app.log", mode="w")
        fh.setLevel(root_logger.level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)

    # Optional SQLAlchemy error logging
    if sql_logging:
        for name in [
            'sqlalchemy.engine', 'sqlalchemy.dialects',
            'sqlalchemy.pool', 'sqlalchemy.orm', 'sqlalchemy'
        ]:
            sql_logger = logging.getLogger(name)
            sql_logger.setLevel(logging.DEBUG)
            sql_logger.propagate = False

        @event.listens_for(Engine, "handle_error")
        def handle_sqlalchemy_error(context):
            exception = context.original_exception
            root_logger.error(f"SQLAlchemy Error: {exception}")
            if context.statement:
                root_logger.error(f"Statement: {context.statement}")
            if context.parameters:
                root_logger.error(f"Parameters: {context.parameters}")

    # Logger for specific pages
    if specific_pages:
        name = '_'.join(specific_pages)
        return get_named_logger(name, f"{name}.log")
    
    # Redirect Paramiko logs to their own file (auth info included)
    paramiko_logger = logging.getLogger("paramiko")
    paramiko_logger.setLevel(logging.INFO)  # INFO includes authentication success/failure

    # Prevent duplication if handlers exist
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith("paramiko.log") for h in paramiko_logger.handlers):
        fh = logging.FileHandler(os.path.join(LOG_DIR, "paramiko.log"), mode='w')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        paramiko_logger.addHandler(fh)

    # Optional: prevent it from flooding the root/app.log
    paramiko_logger.propagate = False

    # Return the general logger
    return logging.getLogger('general_logger')

# Main logger setup
logger = configure_logging()
logger.debug("Debug message for testing logging configuration.")

# Disable propagation of Flask-Limiter logs to root logger
logging.getLogger('flask_limiter').propagate = False

# Separate loggers as needed for focus areas.
bad_url_logger = get_named_logger("bad_url", "bad_url_logger.log") # MOVE TO SQL TABLE RECORDS!
http_logger = get_named_logger("network_logger", "network_logger.log")
unauthorized_logger = get_named_logger("unauthorized_logger", "unauthorized_logger.log")
celery_logger = get_named_logger("celery_logger", "celery_logger.log")

def log_activity(status_code, ip_address="0.0.0.0", user_id=None, guest_id=None, event_message=None, response_time=None, app_version=None):
    from app.models.logging import ActivityLog, FailedLoginAttempt
    try:
        log = ActivityLog(
            ip_address=ip_address,
            user_id=user_id,
            guest_id=guest_id,
            session_id=None,
            path=None,
            method=None,
            status_code=status_code,
            accessed_at=datetime.now(),
            query_params=None,
            referrer=None,
            user_agent=None,
            app_version=app_version,
            response_time=response_time,
            country=None,
            region=None,
            city=None,
            device_type=None,
            browser_name=None,
            os_name=None,
            event_message=event_message
        )

        if has_request_context():
            log.user_id = user_id or session.get("user_id")
            log.guest_id = guest_id or session.get("guest_id")
            log.session_id = session.get("session_id")
            log.path = request.path
            log.method = request.method
            log.query_params = str(request.args.to_dict())
            log.referrer = request.referrer
            log.user_agent = request.user_agent.string
            log.country = request.headers.get("X-Country")
            log.region = request.headers.get("X-Region")
            log.city = request.headers.get("X-City")
            log.device_type = request.user_agent.platform
            log.browser_name = request.user_agent.browser
            log.os_name = request.user_agent.platform

        db.session.add(log)
        db.session.commit()

    except Exception:
        traceback.print_exc()

# ------------------------------------------------------------------------------------
# User Specific Logging
def get_current_user():
    if current_user.is_authenticated:
        session.pop('guest_id', None)
        return current_user
    return get_guest_user()

def get_guest_user():
    return getattr(g, "guest_user", None)

def cleanup_expired_suspensions():
    """
    Remove expired IP-based suspensions and user suspensions.
    """
    # Local Imports (Don't import at the head)
    from app.models.logging import FailedLoginAttempt
    from app.models.user import User

    expiration_time = datetime.now() - Config.IP_BLOCK_TIME
    FailedLoginAttempt.query.filter(FailedLoginAttempt.timestamp < expiration_time).delete()

    suspended_users = User.query.filter(User.is_suspended == True, User.suspension_end < datetime.now()).all()
    for user in suspended_users:
        user.is_suspended = False
        user.failed_attempts = 0
        user.suspension_end = None

    db.session.commit()

def generate_guest_id() -> str:
    # new random UUID4 each first visit, hex-hashed to 64 chars
    raw = uuid.uuid4().hex
    return hashlib.sha256(raw.encode()).hexdigest()

def get_session_id():
    session_id=session.get("session_id"),
    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id
    return session_id

def user_access_data(ip_address, guest_user=None, endpoint=None):
    from app.utils.helpers import get_geoip_data
    """
    Logs and returns access data in a readable text format for tracking.
    """
    # Get geo-location data from the IP address
    geoip_data = get_geoip_data(ip_address)
    country = geoip_data.get("country", "Unknown")
    city = geoip_data.get("city", "Unknown")
    region = geoip_data.get("region", "Unknown")

    # Timestamp for when the access occurred
    access_time = datetime.now()().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Get guest user details (if provided)
    guest_user_details = (
        f"Guest ID: {guest_user.guest_id}, Authenticated: {guest_user.is_authenticated}"
        if guest_user
        else "No guest user information provided"
    )

    # Log endpoint/resource being accessed (if provided)
    resource_info = f"Endpoint: {endpoint}" if endpoint else "Endpoint: Unknown"

    # Combine all data into a single log entry
    log_entry = (
        f"Access logged: {access_time}, IP: {ip_address}, Location: {city}, {region}, {country}. "
        f"{guest_user_details}. {resource_info}."
    )

    return log_entry

