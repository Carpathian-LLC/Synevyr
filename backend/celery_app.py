# worker.py
# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized
# ------------------------------------------------------------------------------------
# Celery Worker/Beat unified entrypoint
# ------------------------------------------------------------------------------------

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment from keys.env
env_path = Path(__file__).resolve().parents[1] / "keys.env"
if env_path.exists():
    load_dotenv(str(env_path), override=True)

os.environ.setdefault("FLASK_ENV", "development")

# Import create_app and celery
from app import create_app
from app.core.init_celery import init_celery

# Create the Flask app first
flask_app = create_app()

# Bind Flask to Celery, ensure ContextTask is set, schedule loaded, and tasks imported
celery = init_celery(flask_app)

# debug
from app.utils.logging import celery_logger
celery_logger.info("[WORKER] Celery initialized with Flask context")
