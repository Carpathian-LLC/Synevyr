# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Description:
# -> Populates all key analytics tables with synthetic customer, lead, and order data <-
#
# This script seeds `user_customers`, `meta_leads`, `wc_orders`, and aggregate tables
# (`customer_analysis`, `cx_stats`) for testing Synevyr's end-to-end analytics flow.
#
# Notes:
# - Establishes user identities, source attribution, lead funnel paths, and purchase data.
# - Includes behavioral modeling logic to simulate real customer lifespan and spend bias tuned
#   to a real client dataset.
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
    from backend.app.models.analysis import MetaLead, WooCommerceOrder, CustomerAnalysis, CustomerStats
except Exception as e:
    print(f"Warning: Could not import some backend modules (likely due to metadata conflicts): {e}")
    print("This is normal if tables were already created. Continuing with seeding...")

# Local generators
from generators.make_me_a_person import generate_person_info
from generators.make_me_meta_leads import generate_meta_leads
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
def seed_user_customers():
    print("⏳ Inserting into user_customers...")
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
    total = 50000
    seen_emails = set()

    insert_stmt = text("""
        INSERT INTO user_customers (
            first_name, last_name, email, phone, address, city, state, country,
            zipcode, activity_status, created_at, referrer
        ) VALUES (
            :first_name, :last_name, :email, :phone, :address, :city, :state,
            :country, :zipcode, :activity_status, :created_at, :referrer
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
                    "referrer": p["referrer"]
                })
            conn.execute(insert_stmt, batch)
            inserted += batch_size

    print("✅ user_customers inserted.")

def seed_meta_leads():
    print("⏳ Seeding meta_leads...")
    generate_meta_leads(engine, total_leads=10000)
    print("✅ meta_leads inserted.")

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

def seed_customer_analysis():
    print("⏳ Seeding customer_analysis and cx_stats...")

    # Use SQLAlchemy models instead of raw SQL
    with engine.begin() as conn:
        # Truncate tables (models are already created)
        conn.execute(text("TRUNCATE TABLE customer_analysis"))
        conn.execute(text("TRUNCATE TABLE cx_stats"))

        # Query customer data using SQLAlchemy text queries
        rows = conn.execute(text("""
            SELECT
                uc.id, uc.first_name, uc.last_name, uc.email, uc.city, uc.state, uc.country, uc.phone,
                uc.activity_status, uc.created_at,
                ml.id AS meta_id, ml.platform AS source, ml.ad_name,
                SUM(wo.total) AS total_amount,
                MAX(wo.status) AS order_status
            FROM user_customers uc
            LEFT JOIN meta_leads ml ON ml.email = uc.email
            LEFT JOIN wc_orders wo ON wo.customer_id = uc.id
            GROUP BY uc.id
        """)).fetchall()

        insert_analysis = text("""
            INSERT INTO customer_analysis (
                wc_cx_id, ck_cx_id, source, ad_name, first_name, last_name, email,
                created_at, unsubscribed_on, cx_tenure, activity_status,
                order_total, subscription_total, order_status,
                subscription_status, total_spend
            ) VALUES (:wc_cx_id, :ck_cx_id, :source, :ad_name, :first_name, :last_name, :email,
                     :created_at, :unsubscribed_on, :cx_tenure, :activity_status,
                     :order_total, :subscription_total, :order_status,
                     :subscription_status, :total_spend)
        """)

        insert_stats = text("""
            INSERT INTO cx_stats (
                customer_id, email, first_name, last_name, origin, activity_status,
                created_at, unsubscribed_on, cx_tenure, subscribed_days,
                lifetime_value, purchased_items, city, state, country, phone
            ) VALUES (:customer_id, :email, :first_name, :last_name, :origin, :activity_status,
                     :created_at, :unsubscribed_on, :cx_tenure, :subscribed_days,
                     :lifetime_value, :purchased_items, :city, :state, :country, :phone)
        """)

        for row in rows:
            (
                uc_id, first_name, last_name, email, city, state, country, phone,
                activity_status, created_at,
                meta_id, source, ad_name,
                total_amount, order_status
            ) = row
            
            tenure_days = 0
            order_total = float(total_amount or 0)
            total_spend = order_total
            subscribed_days = tenure_days

            # Enhanced source-based behavioral modeling with realistic customer patterns
            if source:
                s = source.lower()
                if s == "organic":
                    # Organic: Highest quality, longest tenure, highest LTV
                    tenure_days += random.triangular(60, 365, 180)
                    total_spend *= random.triangular(1.4, 2.2, 1.8)
                elif s == "referral":
                    # Referrals: High quality, good tenure, premium LTV
                    tenure_days += random.triangular(45, 300, 120) 
                    total_spend *= random.triangular(1.2, 2.0, 1.6)
                elif s == "email":
                    # Email: Good quality, solid tenure and spend
                    tenure_days += random.triangular(20, 180, 90)
                    total_spend *= random.triangular(1.1, 1.6, 1.3)
                elif s == "google":
                    # Google: Decent quality, moderate tenure
                    tenure_days += random.triangular(10, 120, 45)
                    total_spend *= random.triangular(0.9, 1.4, 1.1)
                elif s == "meta":
                    # Meta: Lower quality, shorter tenure, lower LTV
                    tenure_days += random.triangular(-20, 60, 10)
                    total_spend *= random.triangular(0.5, 1.1, 0.8)
                elif s == "billboard":
                    # Traditional: Mixed quality, varies widely
                    tenure_days += random.triangular(-10, 150, 60)
                    total_spend *= random.triangular(0.8, 1.5, 1.0)
                else:
                    # Other: Neutral baseline
                    tenure_days += random.triangular(-5, 90, 30)
                    total_spend *= random.triangular(0.8, 1.3, 1.0)

            # Clamp minimum tenure to 0
            tenure_days = max(0, tenure_days)
            subscribed_days = tenure_days

            unsubscribed_on = None
            if activity_status and activity_status.lower() in {"inactive", "churned", "unsubscribed"}:
                if created_at and tenure_days > 30:
                    unsubscribed_on = created_at + timedelta(days=random.randint(30, int(tenure_days)))
            elif created_at and tenure_days > 45 and random.random() < 0.15:  # 15% random churn
                unsubscribed_on = created_at + timedelta(days=random.randint(45, int(tenure_days)))

            # Execute parameterized insert statements
            conn.execute(insert_analysis, {
                'wc_cx_id': uc_id,
                'ck_cx_id': meta_id,
                'source': source or 'organic',
                'ad_name': ad_name or '',
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'created_at': created_at,
                'unsubscribed_on': unsubscribed_on,
                'cx_tenure': f"{int(tenure_days)} days",
                'activity_status': activity_status,
                'order_total': order_total,
                'subscription_total': 0,
                'order_status': order_status or '',
                'subscription_status': 'N/A',
                'total_spend': total_spend
            })

            conn.execute(insert_stats, {
                'customer_id': uc_id,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'origin': source or 'organic',
                'activity_status': activity_status,
                'created_at': created_at,
                'unsubscribed_on': unsubscribed_on,
                'cx_tenure': f"{int(tenure_days)} days",
                'subscribed_days': int(subscribed_days),
                'lifetime_value': total_spend,
                'purchased_items': '',
                'city': city or '',
                'state': state or '',
                'country': country or '',
                'phone': phone or ''
            })

    print("✅ customer_analysis and cx_stats seeded.")


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
    
    seed_user_customers()
    seed_meta_leads()
    seed_wc_orders()
    seed_customer_analysis()
    print("✅ All done.")

if __name__ == "__main__":
    main()
