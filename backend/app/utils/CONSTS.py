# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Consts that SHOULD NOT change - the only reason they should get removed is if the record becomes
#   dynamic and moves to the db.

# ------------------------------------------------------------------------------------
# Imports
import os
from pathlib import Path

# ------------------------------------------------------------------------------------
# Decs
BASE_DIR = Path(__file__).resolve().parents[2]

WEBHOOK_SECRET = os.getenv("FLASK_WEBHOOK_SECRET")