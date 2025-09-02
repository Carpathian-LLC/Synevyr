# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Description:
# -> Populates `wc_orders` with simulated ecommerce transactions by source type <-
#
# Orders are sampled from customers in `crm_customers`, weighted by source type. 
# Higher-value orders are assigned to organic/email, with lowest to Meta as seen an a real
# customer dataset.
#
# Notes:
# - Encodes customer value hypothesis into spend ranges.
# - Used to test source-based LTV and purchase behavior patterns.
# ------------------------------------------------------------------------------------
# Imports
from faker import Faker
from datetime import datetime, timedelta
import random

# ------------------------------------------------------------------------------------
# Vars
fake = Faker()

# ------------------------------------------------------------------------------------
# Functions
def generate_wc_orders(cursor, total_orders=10000):
    # Step 1: Pull customers from crm_customers table (use source_id instead of referrer)
    cursor.execute("SELECT id, email, source_id FROM crm_customers")
    all_customers = cursor.fetchall()

    if not all_customers:
        raise Exception("No customers found in crm_customers table.")

    meta_customers    = [customer for customer in all_customers if customer[2] == "meta"]
    organic_customers = [customer for customer in all_customers if customer[2] == "organic"]
    email_customers   = [customer for customer in all_customers if customer[2] == "email"]
    other_customers   = [customer for customer in all_customers if customer[2] not in {"meta", "organic", "email"}]

    # Step 2: More realistic sampling strategy aligned with acquisition volumes
    # Order distribution should roughly follow customer quality, not extreme ratios
    meta_orders    = random.sample(meta_customers, k=min(len(meta_customers), max(1, int(total_orders * 0.12))))
    organic_orders = random.sample(organic_customers, k=min(len(organic_customers), int(total_orders * 0.40)))
    email_orders   = random.sample(email_customers, k=min(len(email_customers), int(total_orders * 0.20)))

    remaining = total_orders - (len(meta_orders) + len(organic_orders) + len(email_orders))
    other_orders = random.sample(other_customers, k=min(len(other_customers), remaining))

    selected_customers = meta_orders + organic_orders + email_orders + other_orders
    random.shuffle(selected_customers)

    # Step 3: Build order rows (customer_id, email, source_id are from selected_customers)
    orders = []
    for i, (customer_id, email, source_id) in enumerate(selected_customers):
        now = datetime.now()
        past = now - timedelta(days=random.randint(1, 30))

        # Realistic order value ranges with more nuanced distribution
        if source_id == "meta":
            # Meta ads: Lower AOV but volume-focused
            order_total = round(random.triangular(15.00, 120.00, 45.00), 2)
        elif source_id == "email":
            # Email: Good quality, mid-range AOV
            order_total = round(random.triangular(35.00, 250.00, 85.00), 2)
        elif source_id == "organic":
            # Organic: Highest quality, highest AOV
            order_total = round(random.triangular(60.00, 800.00, 180.00), 2)
        elif source_id == "referral":
            # Referrals: High quality, premium AOV
            order_total = round(random.triangular(80.00, 600.00, 220.00), 2)
        elif source_id == "google":
            # Google Ads: Solid mid-range performance
            order_total = round(random.triangular(25.00, 350.00, 95.00), 2)
        elif source_id == "billboard":
            # Traditional: Brand awareness, varied AOV
            order_total = round(random.triangular(40.00, 400.00, 120.00), 2)
        else:
            # Other sources: Mixed bag
            order_total = round(random.triangular(20.00, 300.00, 75.00), 2)

        discount = round(order_total * random.uniform(0, 0.2), 2)
        shipping = round(random.uniform(0, 20.00), 2)

        orders.append((
            fake.unique.random_int(min=10**9, max=10**10-1),  # id
            0,  # parent_id
            random.choices(
                population=["completed", "processing", "on-hold", "cancelled", "pending", "refunded"],
                weights=[0.70, 0.15, 0.08, 0.04, 0.02, 0.01],  # Realistic order status distribution
                k=1
            )[0],
            "USD",
            "1.0",
            random.choice([True, False]),
            past,
            now,
            discount,
            0.00,           # discount_tax
            shipping,
            0.00,           # shipping_tax
            0.00,           # cart_tax
            order_total,
            0.00,           # total_tax
            customer_id,  # Use the actual customer_id from selected_customers
            fake.uuid4()[:32],
            fake.text(max_nb_chars=200),
            fake.text(max_nb_chars=200),
            "credit_card",
            "Credit Card",
            fake.uuid4(),
            fake.ipv4_public(),
            fake.user_agent(),
            source_id,  # Use source_id instead of referrer
            fake.sentence(),
            now,
            now,
            fake.sha1(),
            str(fake.random_number(digits=8)),
            fake.text(max_nb_chars=200),
            fake.text(max_nb_chars=200),
            fake.text(max_nb_chars=200),
            fake.text(max_nb_chars=200),
            fake.text(max_nb_chars=200),
            fake.text(max_nb_chars=200),
            fake.text(max_nb_chars=200),
            fake.url(),
            False,  # is_editable
            False,  # needs_payment
            False,  # needs_processing
            past,
            now,
            now,
            now,
            round(random.uniform(0, 30.00), 2),  # store_credit_used
            "$"
        ))

    # Step 5: Insert into wc_orders
    cursor.executemany("""
        INSERT INTO wc_orders (
            id, parent_id, status, currency, version, prices_include_tax,
            date_created, date_modified, discount_total, discount_tax,
            shipping_total, shipping_tax, cart_tax, total, total_tax,
            customer_id, order_key, billing, shipping, payment_method,
            payment_method_title, transaction_id, customer_ip_address,
            customer_user_agent, created_via, customer_note, date_completed,
            date_paid, cart_hash, number, meta_data, line_items, tax_lines,
            shipping_lines, fee_lines, coupon_lines, refunds, payment_url,
            is_editable, needs_payment, needs_processing, date_created_gmt,
            date_modified_gmt, date_completed_gmt, date_paid_gmt,
            store_credit_used, currency_symbol
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s
        )
    """, orders)

    print(f"✅ Inserted {len(orders)} wc_orders. Meta: {len(meta_orders)}, Organic: {len(organic_orders)}, Email: {len(email_orders)}, Other: {len(other_orders)}")
