# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Description:
# -> Populates `wc_orders` with simulated ecommerce transactions by source type <-
#
# Orders are sampled from leads in `user_customers`, weighted by referrer type. 
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
    # Step 1: Pull leads from user_customers table
    cursor.execute("SELECT id, email, referrer FROM user_customers")
    all_leads = cursor.fetchall()

    if not all_leads:
        raise Exception("No leads found in user_customers table.")

    meta_leads     = [lead for lead in all_leads if lead[2] == "meta"]
    organic_leads  = [lead for lead in all_leads if lead[2] == "organic"]
    email_leads    = [lead for lead in all_leads if lead[2] == "email"]
    other_leads    = [lead for lead in all_leads if lead[2] not in {"meta", "organic", "email"}]

    # Step 2: Sampling strategy
    meta_orders    = random.sample(meta_leads, k=min(len(meta_leads), max(1, int(total_orders * 0.05))))
    organic_orders = random.sample(organic_leads, k=min(len(organic_leads), int(total_orders * 0.5)))
    email_orders   = random.sample(email_leads, k=min(len(email_leads), int(total_orders * 0.25)))

    remaining = total_orders - (len(meta_orders) + len(organic_orders) + len(email_orders))
    other_orders = random.sample(other_leads, k=min(len(other_leads), remaining))

    selected_leads = meta_orders + organic_orders + email_orders + other_orders
    random.shuffle(selected_leads)

    # Step 3: Get list of customer IDs
    cursor.execute("SELECT id FROM user_customers")
    user_ids = [row[0] for row in cursor.fetchall()]
    if not user_ids:
        raise Exception("No users found in users table.")

    # Step 4: Build order rows
    orders = []
    for i, (lead_id, email, referrer) in enumerate(selected_leads):
        now = datetime.now()
        past = now - timedelta(days=random.randint(1, 30))

        if referrer == "meta":
            order_total = round(random.uniform(20.00, 80.00), 2)
        elif referrer == "email":
            order_total = round(random.uniform(60.00, 200.00), 2)
        elif referrer == "organic":
            order_total = round(random.uniform(150.00, 500.00), 2)
        else:
            order_total = round(random.uniform(40.00, 300.00), 2)

        discount = round(order_total * random.uniform(0, 0.2), 2)
        shipping = round(random.uniform(0, 20.00), 2)

        orders.append((
            fake.unique.random_int(min=10**9, max=10**10-1),  # id
            0,  # parent_id
            random.choice(["completed", "processing", "on-hold", "cancelled"]),
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
            random.choice(user_ids),
            fake.uuid4()[:32],
            fake.text(max_nb_chars=200),
            fake.text(max_nb_chars=200),
            "credit_card",
            "Credit Card",
            fake.uuid4(),
            fake.ipv4_public(),
            fake.user_agent(),
            referrer,
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
