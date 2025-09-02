# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Description:
# -> Populates `leads` with a blend of real and fake lead data for ad analysis <-
#
# 30% of leads are derived from real `crm_customers` to simulate captured leads from
# actual Meta campaigns seen in a client dataset. The rest are randomized to simulate ad variability.
#
# Notes:
# - Enables LTV and conversion tracking for Meta vs. other platforms.
# - Platform field includes source channel for attribution analysis.
# ------------------------------------------------------------------------------------
# Imports
import random
import string
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import text

# ------------------------------------------------------------------------------------
# Vars
fake = Faker()

# ------------------------------------------------------------------------------------
# Functions

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_leads(engine, total_leads=100):
    with engine.begin() as conn:
        # Step 1: Get all users
        result = conn.execute(text("SELECT id, first_name, last_name, email FROM crm_customers"))
        users = result.fetchall()

        if not users:
            raise Exception("No users found in the users table.")

        num_meta = int(total_leads * 0.3)
        num_fake = total_leads - num_meta

        meta_users = random.sample(users, min(num_meta, len(users)))
        leads = []

        # Step 2: Use real users as leads
        for user in meta_users:
            user_id, first_name, last_name, email = user
            leads.append({
                "id": random.randint(10**9, 10**10 - 1),
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "ad_id": random.randint(1000, 9999),
                "ad_name": fake.bs().title(),
                "adset_id": random.randint(1000, 9999),
                "adset_name": fake.catch_phrase(),
                "campaign_id": random.randint(1000, 9999),
                "campaign_name": fake.company(),
                "form_id": random.randint(1000, 9999),
                "form_name": fake.word().capitalize() + " Form",
                "is_organic": False,
                "platform": "meta",
                "retailer_item_id": generate_random_string(12),
                "lead_status": random.choices(
                    population=["new", "qualified", "converted", "rejected", "nurturing"],
                    weights=[0.35, 0.25, 0.15, 0.15, 0.10],  # Somewhat random, but designed to model real life leads
                    k=1
                )[0],
                "created_at": (datetime.today() - timedelta(days=random.randint(0, 730))).date(),
            })

        # Step 3: Generate random leads (non-meta)
        for _ in range(num_fake):
            leads.append({
                "id": random.randint(10**9, 10**10 - 1),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.unique.email(),
                "ad_id": random.randint(1000, 9999),
                "ad_name": fake.bs().title(),
                "adset_id": random.randint(1000, 9999),
                "adset_name": fake.catch_phrase(),
                "campaign_id": random.randint(1000, 9999),
                "campaign_name": fake.company(),
                "form_id": random.randint(1000, 9999),
                "form_name": fake.word().capitalize() + " Form",
                "is_organic": random.choice([True, False]),
                "platform": random.choices(
                    population=["google", "linkedin", "tiktok", "referral", "organic", "billboard"],
                    weights=[0.30, 0.15, 0.10, 0.20, 0.20, 0.05],  # Weights for how it will choose
                    k=1
                )[0],
                "retailer_item_id": generate_random_string(12),
                "lead_status": random.choices(
                    population=["new", "qualified", "converted", "rejected", "nurturing"],
                    weights=[0.35, 0.25, 0.15, 0.15, 0.10],  # Somewhat random, but designed to model real life leads
                    k=1
                )[0],
                "created_at": fake.date_between(start_date='-30d', end_date='today')
            })

        insert_stmt = text("""
            INSERT INTO leads (
                id, first_name, last_name, email,
                ad_id, ad_name, adset_id, adset_name,
                campaign_id, campaign_name, form_id, form_name,
                is_organic, platform, retailer_item_id, lead_status, created_at
            ) VALUES (
                :id, :first_name, :last_name, :email,
                :ad_id, :ad_name, :adset_id, :adset_name,
                :campaign_id, :campaign_name, :form_id, :form_name,
                :is_organic, :platform, :retailer_item_id, :lead_status, :created_at
            )
        """)

        conn.execute(insert_stmt, leads)
        print(f"✅ Inserted {len(leads)} leads.")
