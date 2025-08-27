# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Authorized.
# ------------------------------------------------------------------------------------
# Description:
# -> This is the main entrypoint for the Synevyr backend application <-
#
# This initializes the Flask app server using the factory pattern and 
# starts the server using configuration values for host and port.
#
# Notes:
# - This script should only be run directly for development or managed environments.
# - The `create_app` function initializes the full application context.

# ------------------------------------------------------------------------------------
# Imports:
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Local Imports
from app import create_app
import app.utils.initialize_db as initialize_db

# ------------------------------------------------------------------------------------
# Var Decs

# Set BASE_DIR and load .env (force file to override any shell export)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, "keys.env"), override=True)

app = create_app()

sys.path.append(str(Path(__file__).resolve().parent))

# ------------------------------------------------------------------------------------
# Main Run
if __name__ == "__main__":

    # Choose the env for the database init (having this here keeps celery from calling the db when it runs create_app())
    env = os.getenv("FLASK_ENV", "production").strip().lower()
    domain = os.getenv("DOMAIN", "localhost:2001").strip().lower()

    from app.core.config import ProductionConfig, DevelopmentConfig
    config_class = ProductionConfig if env == "production" else DevelopmentConfig

    # Apply the selected config to the app (was missing before)
    app.config.from_object(config_class)

    # Logs + one-time DB init per environment
    if env == "production":
        print("========================================")
        print("Server Environment:", os.getenv("FLASK_ENV", "NOT SET"))
        print(f"Server running on: {domain}")
        print("========================================")
        initialize_db.initialize_database("prod")
    else:
        print("========================================")
        print("Server Environment:", os.getenv("FLASK_ENV", "NOT SET"))
        print("Server running on: http://localhost:2001")
        print("========================================")
        initialize_db.initialize_database("dev")

    host = app.config.get("HOST", "127.0.0.1")
    port = app.config.get("PORT", 2001)

    # Do not force debug; derive from env or config
    debug_flag = (env == "development") if "DEBUG" not in app.config else bool(app.config["DEBUG"])

    app.run(host=host, port=port, debug=debug_flag)
