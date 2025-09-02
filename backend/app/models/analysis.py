# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# ANALYSIS MODELS - Customer Analytics Results
# ------------------------------------------------------------------------------------
# These models represent processed analysis results and computed statistics
# from platform user data processing.
#
# Analysis Models in this file:
# - CustomerAnalysis: Processed customer analysis results
# - CustomerStats: Customer statistics and lifetime value calculations
# - SourceMetricsDaily: Daily source metrics table
# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime
from sqlalchemy import UniqueConstraint, Index

# Local Imports
from app.extensions import db

# ------------------------------------------------------------------------------------
# Var Decs

# ------------------------------------------------------------------------------------
# Classes

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

class SourceMetricsDaily(db.Model):
    """New source metrics daily table for analytics"""
    __tablename__ = "source_metrics_daily"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # Tenancy and bucketing
    user_id = db.Column(db.Integer, nullable=False, index=True)
    day = db.Column(db.Date, nullable=False)
    source_label = db.Column(db.String(64), nullable=False)
    
    # Core metrics from the analytics query
    leads = db.Column(db.Integer, nullable=False, default=0)
    cost_cents = db.Column(db.BigInteger, nullable=False, default=0)
    orders_ok = db.Column(db.Integer, nullable=False, default=0)
    revenue_cents = db.Column(db.BigInteger, nullable=False, default=0)
    orders_value_sum_cents = db.Column(db.BigInteger, nullable=False, default=0)
    high_value_orders = db.Column(db.Integer, nullable=False, default=0)
    subscription_revenue_cents = db.Column(db.BigInteger, nullable=False, default=0)
    new_customers = db.Column(db.Integer, nullable=False, default=0)
    churn_events = db.Column(db.Integer, nullable=False, default=0)
    
    # Audit fields
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        UniqueConstraint("user_id", "day", "source_label", name="uq_smdv2_user_day_source"),
        Index("ix_smdv2_user_source_day", "user_id", "source_label", "day"),
        Index("ix_smdv2_user_day", "user_id", "day"),
    )
    
    # Convenience properties
    @property
    def revenue(self) -> float:
        return float(self.revenue_cents) / 100.0
    
    @property
    def cost(self) -> float:
        return float(self.cost_cents) / 100.0
    
    @property
    def orders_value_sum(self) -> float:
        return float(self.orders_value_sum_cents) / 100.0
    
    @property
    def subscription_revenue(self) -> float:
        return float(self.subscription_revenue_cents) / 100.0
    
    @property
    def roi_pct(self) -> float:
        return 0.0 if self.cost_cents == 0 else ((self.revenue_cents - self.cost_cents) / self.cost_cents) * 100.0

    def __repr__(self):
        return f"<SourceMetricsDaily(id={self.id}, user_id={self.user_id}, day='{self.day}', source='{self.source_label}')>"
