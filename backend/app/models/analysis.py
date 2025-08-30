# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# 📊 DATASET MODELS - Customer Analytics Data
# ------------------------------------------------------------------------------------
# These models represent the customer data that Synevyr's platform users upload
# for analysis. This is the "data about their customers" that gets analyzed.
#
# NOT to be confused with platform models (User, Customer) which represent
# Synevyr's own users and paying customers.
#
# Dataset Models in this file:
# - MetaLead: Lead generation data from Meta/Facebook ads
# - WooCommerceOrder: E-commerce order data from WooCommerce
# - CustomerAnalysis: Processed customer analysis results
# - CustomerStats: Customer statistics and metrics
#
# Note: UserCustomer model is in user.py but represents dataset data too
# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime

# Local Imports
from app.extensions import db
# ------------------------------------------------------------------------------------
# Var Decs

# ------------------------------------------------------------------------------------
# Classes

class MetaLead(db.Model):
    __tablename__ = "meta_leads"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    ad_id = db.Column(db.BigInteger, nullable=True)
    ad_name = db.Column(db.String(255), nullable=True)
    adset_id = db.Column(db.BigInteger, nullable=True)
    adset_name = db.Column(db.String(255), nullable=True)
    campaign_id = db.Column(db.BigInteger, nullable=True)
    campaign_name = db.Column(db.String(255), nullable=True)
    form_id = db.Column(db.BigInteger, nullable=True)
    form_name = db.Column(db.String(255), nullable=True)
    is_organic = db.Column(db.Boolean, nullable=False, default=False)
    platform = db.Column(db.String(100), nullable=True)
    retailer_item_id = db.Column(db.String(255), nullable=True)
    lead_status = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.Date, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<MetaLead(id={self.id}, email='{self.email}', platform='{self.platform}')>"

class WooCommerceOrder(db.Model):
    __tablename__ = "wc_orders"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    parent_id = db.Column(db.BigInteger, nullable=False, default=0)
    status = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="USD")
    version = db.Column(db.String(20), nullable=False, default="1.0")
    prices_include_tax = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    date_modified = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    discount_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    discount_tax = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    shipping_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    shipping_tax = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    cart_tax = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    total_tax = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    customer_id = db.Column(db.BigInteger, nullable=True)
    order_key = db.Column(db.String(255), nullable=True)
    billing = db.Column(db.Text, nullable=True)
    shipping = db.Column(db.Text, nullable=True)
    payment_method = db.Column(db.String(100), nullable=True)
    payment_method_title = db.Column(db.String(255), nullable=True)
    transaction_id = db.Column(db.String(255), nullable=True)
    customer_ip_address = db.Column(db.String(100), nullable=True)
    customer_user_agent = db.Column(db.Text, nullable=True)
    created_via = db.Column(db.String(100), nullable=True)
    customer_note = db.Column(db.Text, nullable=True)
    date_completed = db.Column(db.DateTime, nullable=True)
    date_paid = db.Column(db.DateTime, nullable=True)
    cart_hash = db.Column(db.String(255), nullable=True)
    number = db.Column(db.String(100), nullable=True)
    meta_data = db.Column(db.Text, nullable=True)
    line_items = db.Column(db.Text, nullable=True)
    tax_lines = db.Column(db.Text, nullable=True)
    shipping_lines = db.Column(db.Text, nullable=True)
    fee_lines = db.Column(db.Text, nullable=True)
    coupon_lines = db.Column(db.Text, nullable=True)
    refunds = db.Column(db.Text, nullable=True)
    payment_url = db.Column(db.String(255), nullable=True)
    is_editable = db.Column(db.Boolean, nullable=False, default=False)
    needs_payment = db.Column(db.Boolean, nullable=False, default=False)
    needs_processing = db.Column(db.Boolean, nullable=False, default=False)
    date_created_gmt = db.Column(db.DateTime, nullable=True)
    date_modified_gmt = db.Column(db.DateTime, nullable=True)
    date_completed_gmt = db.Column(db.DateTime, nullable=True)
    date_paid_gmt = db.Column(db.DateTime, nullable=True)
    store_credit_used = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    currency_symbol = db.Column(db.String(10), nullable=False, default="$")

    def __repr__(self):
        return f"<WooCommerceOrder(id={self.id}, status='{self.status}', total={self.total})>"

class CustomerAnalysis(db.Model):
    __tablename__ = "customer_analysis"

    master_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    wc_cx_id = db.Column(db.BigInteger, unique=True, nullable=True)
    ck_cx_id = db.Column(db.BigInteger, unique=True, nullable=True)
    source = db.Column(db.String(255), nullable=True)
    ad_name = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    created_at = db.Column(db.Date, nullable=True)
    unsubscribed_on = db.Column(db.Date, nullable=True)
    cx_tenure = db.Column(db.String(30), nullable=True)
    activity_status = db.Column(db.String(255), nullable=True)
    order_total = db.Column(db.Numeric(10, 2), nullable=True)
    subscription_total = db.Column(db.Numeric(10, 2), nullable=True)
    order_status = db.Column(db.String(255), nullable=True)
    subscription_status = db.Column(db.String(255), nullable=True)
    total_spend = db.Column(db.Numeric(10, 2), nullable=True)
    created_at_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<CustomerAnalysis(master_id={self.master_id}, email='{self.email}', source='{self.source}')>"

class CustomerStats(db.Model):
    __tablename__ = "cx_stats"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.BigInteger, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    origin = db.Column(db.String(255), nullable=True)
    activity_status = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.Date, nullable=True)
    unsubscribed_on = db.Column(db.Date, nullable=True)
    cx_tenure = db.Column(db.String(30), nullable=True)
    subscribed_days = db.Column(db.Integer, nullable=True)
    lifetime_value = db.Column(db.Numeric(10, 2), nullable=True)
    purchased_items = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(255), nullable=True)
    state = db.Column(db.String(255), nullable=True)
    country = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<CustomerStats(id={self.id}, email='{self.email}', origin='{self.origin}')>"

# Note: Customer model (user_customers table) is defined in general.py
