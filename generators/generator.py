# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Description:
# -> Populates all key analytics tables with synthetic customer, lead, and order data <-
#
# This script seeds `crm_customers`, `leads`, `wc_orders`, and aggregate tables
#
# Notes:
# - Establishes user identities, source attribution, lead funnel paths, and purchase data.
# ------------------------------------------------------------------------------------

# Imports
import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
# ------------------------------------------------------------------------------------

# Ensure the project root is in the Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))

# Flask app setup for SQLAlchemy models
import os
os.environ['FLASK_ENV'] = 'development'  # Prevent production checks

# Import Flask app to get models
try:
    from backend.app import create_app
    from backend.app.extensions import db
    from backend.app.utils.create_tables import create_all_tables
    from backend.app.models.user import Customer
    from backend.app.models.analysis import CustomerAnalysis, CustomerStats
    from backend.app.models.public_data import Leads, WooCommerceOrder, UserCustomer
except Exception as e:
    print(f"Warning: Could not import some backend modules (likely due to metadata conflicts): {e}")
    print("This is normal if tables were already created. Continuing with seeding...")

# Local generators
from generators.make_me_a_person import generate_person_info
from generators.make_me_leads import generate_leads
from generators.make_me_wc_orders import generate_wc_orders

# === Load .env ===
env_path = Path(__file__).resolve().parents[1] / "keys.env"
load_dotenv(dotenv_path=env_path, override=True)

# === Build SQLAlchemy URI ===
db_uri = (
    "mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
).format(
    user=os.getenv("DEV_DB_USER"),
    password=os.getenv("DEV_DB_PASSWORD"),
    host=os.getenv("DEV_DB_HOST"),
    port=os.getenv("DEV_DB_PORT", "3306"),
    database=os.getenv("DATABASE", "db_synevyr")
)

engine = create_engine(db_uri)

# === Seed Functions ===
def seed_crm_customers():
    print("⏳ Inserting into crm_customers...")
    # Realistic customer activity distribution
    activity_weights = [
        ("active", 0.65),        # Most customers should be active
        ("inactive", 0.20),      # Some natural churn
        ("pending", 0.08),       # New signups being processed
        ("churned", 0.05),       # Definitely churned customers
        ("at-risk", 0.02),       # Customers showing decline signs
    ]
    
    activity_pool = []
    for status, weight in activity_weights:
        activity_pool.extend([status] * int(weight * 1000))

    batch_size = 1000
    total = 500000
    seen_emails = set()

    insert_stmt = text("""
        INSERT INTO crm_customers (
            first_name, last_name, email, phone, address, city, state, country,
            zipcode, activity_status, created_at, source_id
        ) VALUES (
            :first_name, :last_name, :email, :phone, :address, :city, :state,
            :country, :zipcode, :activity_status, :created_at, :source_id
        )
    """)

    with engine.begin() as conn:
        inserted = 0
        while inserted < total:
            batch = []
            while len(batch) < batch_size:
                p = generate_person_info()
                email = p["email"]
                if email in seen_emails:
                    continue
                seen_emails.add(email)
                batch.append({
                    "first_name": p["first_name"],
                    "last_name": p["last_name"],
                    "email": email,
                    "phone": p["phone"],
                    "address": p["address"],
                    "city": p["city"],
                    "state": p["state"],
                    "country": p["country"],
                    "zipcode": p["zipcode"],
                    "activity_status": random.choice(activity_pool),
                    "created_at": (datetime.today() - timedelta(days=random.randint(0, 730))).date(),
                    "source_id": p["source_id"]
                })
            conn.execute(insert_stmt, batch)
            inserted += batch_size

    print("✅ crm_customers inserted.")

def seed_leads():
    print("⏳ Seeding leads...")
    generate_leads(engine, total_leads=10000)
    print("✅ leads inserted.")

def seed_wc_orders():
    print("⏳ Seeding wc_orders...")
    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        try:
            generate_wc_orders(cursor, total_orders=10000)
            raw_conn.commit()
        finally:
            cursor.close()
    finally:
        raw_conn.close()
    print("✅ wc_orders inserted.")

# === Helper Functions ===
def create_tables():
    """Create all tables using centralized SQLAlchemy models"""
    print("⏳ Creating database tables...")
    try:
        create_all_tables(engine)
        print("✅ All tables created.")
    except NameError:
        print("⚠️ Could not use centralized table creation (models not imported). Tables should already exist.")
    except Exception as e:
        print(f"⚠️ Table creation issue: {e}. Tables may already exist.")

# === Entrypoint ===
def main():
    print("Starting synthetic data generation...")
    
    # Skip table creation if centralized models aren't available (tables should already exist)
    try:
        create_tables()
    except NameError:
        print("⏩ Skipping table creation - using existing tables from centralized system")
    
    seed_crm_customers()
    seed_leads()
    seed_wc_orders()
    print("✅ All done.")

if __name__ == "__main__":
    main()
