# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Application primary entry point

# To import the server functions, use the code below
    # from flask import current_app as app
    # from app import csrf
    # from app import db

# To import the dynamic components:
    # from flask import current_app
    # MAX_ATTEMPTS = current_app.config["MAX_ATTEMPTS"]
    # SUSPENSION_TIME = current_app.config["SUSPENSION_TIME"]
    # IP_BLOCK_TIME = current_app.config["IP_BLOCK_TIME"]
    # MAX_IP_ATTEMPTS = current_app.config["MAX_IP_ATTEMPTS"]

# ------------------------------------------------------------------------------------
# Imports:
from pathlib import Path
import os
import json
from flask import Flask, request, abort
from flask_cors import CORS
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from sqlalchemy.sql import text
from celery.signals import after_setup_task_logger
import stripe

# Local Imports
from app.utils.logging import logger
from flask import Flask, request, session as flask_session

# ------------------------------------------------------------------------------------
# Load the Env - try multiple possible locations
env_paths = [
    Path(__file__).resolve().parents[2] / "keys.env",  # Normal path: backend/app/../../keys.env
    Path.cwd() / "keys.env",  # Current working directory
    Path(__file__).resolve().parent / "keys.env",  # Same directory as this file
]

env_path = None
for path in env_paths:
    if path.exists():
        env_path = path
        break

if env_path:
    load_dotenv(env_path)
    print(f"✓ Loaded keys.env from: {env_path}")
else:
    print(f"✗ keys.env not found at any of: {[str(p) for p in env_paths]}")
os.environ["FLASK_ENV"] = os.getenv("FLASK_ENV", "production")
env = os.environ["FLASK_ENV"]

# ------------------------------------------------------------------------------------
# Application Entry Point

def create_app():
    from app.core.config import Config, ProductionConfig, DevelopmentConfig
    from app.extensions import db, migrate, csrf, mail, limiter, session, celery
    from app.utils.logging import http_logger, celery_logger
    from app.core.init_celery import init_celery

    # Hook Celery task logs into your logger
    @after_setup_task_logger.connect
    def redirect_celery_logs(*args, **kwargs):
        task_logger = kwargs.get("logger") or kwargs.get("task_logger")
        if task_logger:
            task_logger.handlers = celery_logger.handlers
            task_logger.setLevel(celery_logger.level)


    from app.core.init_celery import init_celery

    config_class = ProductionConfig if env == "production" else DevelopmentConfig
     
    # Make Flask app & apply config
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Celery Setup
    init_celery(app)

    CORS(app, supports_credentials=True, resources={
        r"/*": {
            "origins": [
                "https://synevyr.org",
                "http://localhost:2000",
                "http://localhost:2001"
            ]
        }
    })

    # Middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Import + Register Blueprints
    from app.endpoints.auth import auth_bp
    from app.endpoints.general import general_bp
    from app.endpoints.open_data import public_bp
    from app.endpoints.data_sources import data_sources_bp
    from app.endpoints.tasks import tasks_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(general_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(data_sources_bp)
    app.register_blueprint(tasks_bp)


    # Extensions
    Session(app)
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    celery.conf.update(app.config)

    stripe.api_key = app.config.get("STRIPE_API_KEY")
    webhook_key = app.config.get("STRIPE_WEBHOOK_SECRET")
    logger.debug(f"Stripe Key Set: {stripe.api_key}")
    logger.debug(f"Webhook Key Set: {webhook_key}")

    if not webhook_key:
        logger.warning("⚠️  STRIPE_WEBHOOK_KEY is not set! Stripe integration will fail.")
    if not stripe.api_key:
        logger.warning("⚠️  STRIPE_API_KEY is not set! Stripe integration will fail.")


    @app.before_request
    def ignore_socketio():
        if request.path.startswith("/socket.io"):
            return "", 204  # no logging, no error

    # Log all incoming requests
    @app.before_request
    def log_request_info():
        # Skip noisy websocket handshake paths and health checks
        p = request.path or ""
        if p.startswith("/socket.io") or p == "/health":
            return

        try:
            # Flask session is a dict-like; guard in case something overwrote it
            try:
                session_id = flask_session.get("_id")  # ok for SecureCookieSession / server-side sessions
            except Exception:
                session_id = None

            logger.info({
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.user_agent.string if request.user_agent else None,
                "session_id": session_id,
            })
        except Exception:
            # Never allow logging to break the request cycle
            logger.exception("Failed to log request")

    @app.after_request
    def log_response_info(response):
        try:
            http_logger.info(
                f"{request.method} {request.path} {response.status_code}",
                extra={"extra_data": {
                    "status_code": response.status_code,
                    "length": response.content_length
                }}
            )

            # Optional: log to DB for auditing public endpoints
            if request.path.startswith("/public/"):
                db.session.execute(
                    text("""
                        INSERT INTO activity_log (
                            ip_address, path, method, status_code, query_params,
                            referrer, user_agent, event_message
                        )
                        VALUES (:ip, :path, :method, :status, :query_params,
                                :referrer, :ua, :event)
                    """),
                    {
                        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
                        "path": request.path,
                        "method": request.method,
                        "status": response.status_code,
                        "query_params": json.dumps(request.args),
                        "referrer": request.referrer,
                        "ua": request.headers.get("User-Agent"),
                        "event": "public endpoint hit"
                    }
                )
                db.session.commit()

        except Exception as e:
            logger.error("Failed to log response", exc_info=e)
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error("Unhandled exception", exc_info=e)
        return {"error": "Internal server error"}, 500
    
    @app.before_request
    def enforce_session_lifetime():
        from flask import session
        session.permanent = True

    # Log all outgoing responses
    @app.after_request
    def log_response_info(response):
        http_logger.info(f"Response status: {response.status_code} for {request.method} {request.path}")
        return response

    return app

__all__ = ["create_app"]
