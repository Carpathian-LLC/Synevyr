# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - All general helper functions

# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime
import hashlib
import io
import random
import re
import os
import shlex
import string
import tempfile
import uuid
import time
import paramiko
import geoip2.database
from werkzeug.utils import secure_filename
from sqlalchemy.orm import sessionmaker

# Local Imports
from app.extensions import db
from flask import current_app as app
from app.models.user import User
from app.utils.CONSTS import BASE_DIR
# ------------------------------------------------------------------------------------
# Var Decs

# ------------------------------------------------------------------------------------
# Functions

# Hashing
def hash_input(input_to_hash):
    """Generate a secure hash of the guest ID."""
    return hashlib.sha256(input_to_hash.encode()).hexdigest()

# Validating Functions
def validate_phone(phone):
    return bool(re.match(r"^\+?\d{7,15}$", phone))

def validate_username(username):
    return re.match("^[a-zA-Z0-9_]{3,30}$", username) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*()_+{}:<>?~`-]", password):
        return False, "Password must contain at least one special character."
    return True, "Password is valid."

def validate_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None

def validate_email_format(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def get_geoip_data(ip_address):
    try:
        # Construct the relative path to the GeoIP database
        geoip_db_path = os.path.join(BASE_DIR, "resources", "GeoLite2-City_20241122", "GeoLite2-City.mmdb")
        # Initialize the GeoIP reader
        geoip_reader = geoip2.database.Reader(geoip_db_path)

        # Get GeoIP data for the given IP address
        geo_data = geoip_reader.city(ip_address)

        # Extract location details
        country = geo_data.country.name or "Unknown"
        city = geo_data.city.name or "Unknown"
        region = geo_data.subdivisions.most_specific.name or "Unknown"

        # Close the reader
        geoip_reader.close()

        return {
            "country": country,
            "city": city,
            "region": region
        }
    except geoip2.errors.AddressNotFoundError:
        return {
            "country": "Unknown",
            "city": "Unknown",
            "region": "Unknown"
        }
    
def find_keys_env(start_path="."):
    for root, dirs, files in os.walk(start_path):
        if "keys.env" in files:
            full_path = os.path.join(root, "keys.env")
            print(f"[FOUND] keys.env at: {full_path}\n")
            with open(full_path, "r") as f:
                content = f.read()
            print("==== File Content Start ====")
            print(content)
            print("==== File Content End ====")
            return full_path
    print("keys.env not found.")
    return None

def generate_referral_code(length=8):
    chars = string.ascii_letters + string.digits  # a-zA-Z0-9
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not db.session.query(User).filter_by(referral_code=code).first():
            return code
