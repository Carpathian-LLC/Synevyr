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
    activity_pool = ['active'] * 80 + ['inactive'] * 10 + ['pending'] * 10

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

    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        try:
            # Ensure both tables exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_analysis (
                    master_id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    wc_cx_id BIGINT UNIQUE, 
                    ck_cx_id BIGINT UNIQUE,
                    source VARCHAR(255),  
                    ad_name VARCHAR(255),  
                    first_name VARCHAR(255),
                    last_name VARCHAR(255), 
                    email VARCHAR(255) UNIQUE,
                    created_at DATE,
                    unsubscribed_on DATE,
                    cx_tenure VARCHAR(30),
                    activity_status VARCHAR(255),
                    order_total DECIMAL(10, 2),
                    subscription_total DECIMAL(10, 2),
                    order_status VARCHAR(255),
                    subscription_status VARCHAR(255),
                    total_spend DECIMAL(10, 2),
                    created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("TRUNCATE TABLE customer_analysis")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cx_stats (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    customer_id BIGINT,
                    email VARCHAR(255) UNIQUE,
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    origin VARCHAR(255),
                    activity_status VARCHAR(255),
                    created_at DATE,
                    unsubscribed_on DATE,
                    cx_tenure VARCHAR(30),
                    subscribed_days INT,
                    lifetime_value DECIMAL(10, 2),
                    purchased_items TEXT,
                    city VARCHAR(255),
                    state VARCHAR(255),
                    country VARCHAR(255),
                    phone VARCHAR(50)
                );
            """)
            cursor.execute("TRUNCATE TABLE cx_stats")

            cursor.execute("""
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
            """)
            rows = cursor.fetchall()

            insert_analysis = """
                INSERT INTO customer_analysis (
                    wc_cx_id, ck_cx_id, source, ad_name, first_name, last_name, email,
                    created_at, unsubscribed_on, cx_tenure, activity_status,
                    order_total, subscription_total, order_status,
                    subscription_status, total_spend
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            insert_stats = """
                INSERT INTO cx_stats (
                    customer_id, email, first_name, last_name, origin, activity_status,
                    created_at, unsubscribed_on, cx_tenure, subscribed_days,
                    lifetime_value, purchased_items, city, state, country, phone
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '', %s, %s, %s, %s)
            """

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

                # Inject source-based behavioral bias based on customer data (churchanswers.com)
                if source:
                    s = source.lower()
                    if s in {"organic", "referral"}:
                        tenure_days += random.randint(30, 90)
                        total_spend *= random.uniform(1.3, 1.7)
                    elif s == "meta":
                        tenure_days -= random.randint(10, 40)
                        total_spend *= random.uniform(0.6, 0.9)
                    elif s in {"google", "linkedin", "tiktok"}:
                        tenure_days += random.randint(5, 20)
                        total_spend *= random.uniform(0.9, 1.2)

                # Clamp minimum tenure to 0
                tenure_days = max(0, tenure_days)
                subscribed_days = tenure_days

                unsubscribed_on = None
                if activity_status and activity_status.lower() in {"inactive", "churned", "unsubscribed"}:
                    if created_at and tenure_days > 30:
                        unsubscribed_on = created_at + timedelta(days=random.randint(30, tenure_days))
                elif created_at and tenure_days > 45 and random.random() < 0.15:  # 15% random churn
                    unsubscribed_on = created_at + timedelta(days=random.randint(45, tenure_days))

                cursor.execute(insert_analysis, (
                    uc_id, meta_id, source or 'organic', ad_name or '',
                    first_name, last_name, email, created_at,
                    unsubscribed_on, f"{tenure_days} days", activity_status,
                    order_total, 0, order_status or '', 'N/A', total_spend
                ))

                cursor.execute(insert_stats, (
                    uc_id, email, first_name, last_name, source or 'organic',
                    activity_status, created_at, unsubscribed_on,
                    f"{tenure_days} days", subscribed_days,
                    total_spend, city or '', state or '', country or '', phone or ''
                ))

            raw_conn.commit()
        finally:
            cursor.close()
    finally:
        raw_conn.close()

    print("✅ customer_analysis and cx_stats seeded.")


# === Entrypoint ===
def main():
    print("Starting synthetic data generation...")
    seed_user_customers()
    seed_meta_leads()
    seed_wc_orders()
    seed_customer_analysis()
    print("✅ All done.")

if __name__ == "__main__":
    main()
