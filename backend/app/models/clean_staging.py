# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# CLEAN STAGING MODELS - Clean Data Staging Tables
# ------------------------------------------------------------------------------------
# These models represent clean staging tables for processed user data
# extracted from user_dataset_raw before final aggregation.
#
# Staging Models in this file:
# - LeadsClean: Clean leads data with attribution and classification
# - CustomersClean: Clean customer data with activity and lifetime metrics
# - OrdersClean: Clean order data with revenue and status validation
# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime
from sqlalchemy import UniqueConstraint, Index

# Local Imports
from app.extensions import db

# ------------------------------------------------------------------------------------
# Clean Staging Models
# ------------------------------------------------------------------------------------

class LeadsClean(db.Model):
    """Clean leads staging table for processed lead data"""
    __tablename__ = "leads_clean"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    raw_id = db.Column(db.BigInteger, nullable=False)
    item_idx = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False)
    day = db.Column(db.Date, nullable=False)
    source_label = db.Column(db.String(64), nullable=False)
    is_organic = db.Column(db.Boolean, nullable=True)
    platform = db.Column(db.String(64), nullable=True)
    channel = db.Column(db.String(64), nullable=True)
    network = db.Column(db.String(64), nullable=True)
    utm_source = db.Column(db.String(255), nullable=True)
    utm_medium = db.Column(db.String(255), nullable=True)
    utm_campaign = db.Column(db.String(255), nullable=True)
    utm_term = db.Column(db.String(255), nullable=True)
    utm_content = db.Column(db.String(255), nullable=True)
    campaign_id = db.Column(db.BigInteger, nullable=True)
    campaign_name = db.Column(db.String(255), nullable=True)
    adset_id = db.Column(db.BigInteger, nullable=True)
    adset_name = db.Column(db.String(255), nullable=True)
    ad_id = db.Column(db.BigInteger, nullable=True)
    ad_name = db.Column(db.String(255), nullable=True)
    form_id = db.Column(db.BigInteger, nullable=True)
    form_name = db.Column(db.String(255), nullable=True)
    lead_status = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(255), nullable=True)
    state = db.Column(db.String(255), nullable=True)
    country = db.Column(db.String(255), nullable=True)
    zipcode = db.Column(db.String(50), nullable=True)
    referrer = db.Column(db.String(255), nullable=True)
    cost_cents = db.Column(db.BigInteger, nullable=False, default=0)
    master_customer_id = db.Column(db.BigInteger, nullable=True)  # FK to CustomersClean.id
    raw_payload_json = db.Column(db.Text, nullable=False)
    created_ts = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now)
    
    __table_args__ = (
        UniqueConstraint("user_id", "raw_id", "item_idx", name="uq_leads_user_raw_idx"),
        Index("ix_leads_user_day", "user_id", "day"),
        Index("ix_leads_user_source_day", "user_id", "source_label", "day"),
        Index("ix_leads_email", "email"),
        Index("ix_leads_master_customer", "master_customer_id"),
    )
    
    @property
    def cost(self) -> float:
        return float(self.cost_cents) / 100.0

    def __repr__(self):
        return f"<LeadsClean(id={self.id}, user_id={self.user_id}, email='{self.email}', source='{self.source_label}')>"

class CustomersClean(db.Model):
    """Clean customers staging table for processed customer data"""
    __tablename__ = "customers_clean"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    raw_id = db.Column(db.BigInteger, nullable=False)
    item_idx = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False)
    day = db.Column(db.Date, nullable=False)
    source_label = db.Column(db.String(64), nullable=False)

    customer_id = db.Column(db.BigInteger, nullable=True)
    email = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(255), nullable=True)
    state = db.Column(db.String(255), nullable=True)
    country = db.Column(db.String(255), nullable=True)
    zipcode = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(512), nullable=True)

    activity_status = db.Column(db.String(64), nullable=True)
    subscription_status = db.Column(db.String(64), nullable=True)
    unsubscribed_on = db.Column(db.Date, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    signup_date = db.Column(db.Date, nullable=True)

    total_spend_cents = db.Column(db.BigInteger, nullable=False, default=0)
    subscription_value_cents = db.Column(db.BigInteger, nullable=False, default=0)

    raw_payload_json = db.Column(db.Text, nullable=False)
    created_ts = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "raw_id", "item_idx", name="uq_customers_clean_user_raw_idx"),
        UniqueConstraint("email", name="uq_customers_clean_email"),  # Master customer: unique email
        UniqueConstraint("customer_id", name="uq_customers_clean_customer_id"),  # Master customer: unique customer_id
        Index("ix_customers_user_day", "user_id", "day"),
        Index("ix_customers_email", "email"),
        Index("ix_customers_customer_id", "customer_id"),
        Index("ix_customers_status_day", "activity_status", "day"),
    )

    @property
    def total_spend(self) -> float:
        return float(self.total_spend_cents) / 100.0

    @property
    def subscription_value(self) -> float:
        return float(self.subscription_value_cents) / 100.0

    def __repr__(self):
        return f"<CustomersClean(id={self.id}, user_id={self.user_id}, email='{self.email}', status='{self.activity_status}')>"

class OrdersClean(db.Model):
    """Clean orders staging table for processed order data"""
    __tablename__ = "orders_clean"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    raw_id = db.Column(db.BigInteger, nullable=False)
    item_idx = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False)
    day = db.Column(db.Date, nullable=False)
    source_label = db.Column(db.String(64), nullable=False)
    order_number = db.Column(db.String(128), nullable=True)
    transaction_id = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(64), nullable=True)
    customer_id = db.Column(db.BigInteger, nullable=True)
    email = db.Column(db.String(255), nullable=True)
    currency = db.Column(db.String(16), nullable=True)
    payment_method = db.Column(db.String(64), nullable=True)
    created_via = db.Column(db.String(64), nullable=True)
    date_paid = db.Column(db.DateTime, nullable=True)
    date_completed = db.Column(db.DateTime, nullable=True)
    total_cents = db.Column(db.BigInteger, nullable=False, default=0)
    subtotal_cents = db.Column(db.BigInteger, nullable=False, default=0)
    discount_total_cents = db.Column(db.BigInteger, nullable=False, default=0)
    shipping_total_cents = db.Column(db.BigInteger, nullable=False, default=0)
    tax_total_cents = db.Column(db.BigInteger, nullable=False, default=0)
    store_credit_cents = db.Column(db.BigInteger, nullable=False, default=0)
    subscription_value_cents = db.Column(db.BigInteger, nullable=False, default=0)
    line_items = db.Column(db.Text, nullable=True)
    master_customer_id = db.Column(db.BigInteger, nullable=True)  # FK to CustomersClean.id
    raw_payload_json = db.Column(db.Text, nullable=False)
    created_ts = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now)
    
    __table_args__ = (
        UniqueConstraint("user_id", "raw_id", "item_idx", name="uq_orders_user_raw_idx"),
        Index("ix_orders_user_day", "user_id", "day"),
        Index("ix_orders_status_day", "status", "day"),
        Index("ix_orders_email", "email"),
        Index("ix_orders_master_customer", "master_customer_id"),
    )
    
    @property
    def total(self) -> float:
        return float(self.total_cents) / 100.0
    
    @property
    def subtotal(self) -> float:
        return float(self.subtotal_cents) / 100.0
    
    @property
    def tax_total(self) -> float:
        return float(self.tax_total_cents) / 100.0
    
    @property
    def shipping_total(self) -> float:
        return float(self.shipping_total_cents) / 100.0
    
    @property
    def discount_total(self) -> float:
        return float(self.discount_total_cents) / 100.0

    def __repr__(self):
        return f"<OrdersClean(id={self.id}, user_id={self.user_id}, order_number='{self.order_number}', total=${self.total:.2f})>"