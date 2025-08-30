# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# 🔌 PLATFORM MODELS - Data Source Management
# ------------------------------------------------------------------------------------
# These models manage how Synevyr's platform users configure and ingest their data.
# This includes data source definitions, raw data storage, and processing pipelines.
#
# Platform Models in this file:
# - DataSource: Platform users' data source configurations (API connections, etc.)
# - UserDatasetRaw: Raw data ingested from platform users' data sources
# - SourceMetricsDaily: Processed daily metrics from the raw data
# - AnalyticsEtlState: ETL job state tracking for data processing
#
# These are platform infrastructure models, not the actual customer data being analyzed.
# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime
from app.extensions import db
from sqlalchemy import UniqueConstraint, Index

# ------------------------------------------------------------------------------------
# Var Decs

# ------------------------------------------------------------------------------------
# Classes

class DataSource(db.Model):
    __tablename__ = "data_sources"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_type = db.Column(db.String(32), nullable=False, default="api")  # 'api' | 'manual' | 'file'
    name = db.Column(db.String(255), nullable=False)
    base_url = db.Column(db.Text, nullable=True)
    api_key = db.Column(db.Text, nullable=True)
    config = db.Column(db.JSON, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("user_id", "name", name="uq_data_sources_user_name"),
        db.Index("idx_data_sources_last_updated", "last_updated"),
    )

    # Relationship to raw dataset
    raw_records = db.relationship("UserDatasetRaw", backref="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DataSource id={self.id} user_id={self.user_id} name={self.name}>"
   
    def to_summary(self):
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "base_url": self.base_url,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class UserDatasetRaw(db.Model):
    __tablename__ = "user_dataset_raw"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_id = db.Column(db.BigInteger, db.ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False)
    record_time = db.Column(db.DateTime(6), nullable=True)
    ingested_at = db.Column(db.DateTime(6), nullable=False, default=datetime.now)
    content = db.Column(db.JSON, nullable=False)
    content_hash = db.Column(db.LargeBinary(32), nullable=True)
    content_type = db.Column(db.Enum("json", "csv", "xml", "text"), nullable=False, default="json")
    schema_hint = db.Column(db.String(128), nullable=True)
    status = db.Column(db.Enum("ok", "error", "skipped"), nullable=False, default="ok")
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(6), nullable=False, default=datetime.now)

    __table_args__ = (
        db.Index("idx_user_source_time", "user_id", "source_id", "record_time", "id"),
        db.Index("idx_ingested_at", "ingested_at", "id"),
        # Note: Removed content_hash from unique constraint due to MySQL BLOB key length limitation
        # The hash is still available for duplicate detection but not enforced at DB level
        db.UniqueConstraint("user_id", "source_id", "record_time", name="uq_user_source_time"),
    )

    def __repr__(self):
        return f"<UserDatasetRaw id={self.id} source_id={self.source_id} user_id={self.user_id}>"

class SourceMetricsDaily(db.Model):
    __tablename__ = "source_metrics_daily"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # tenancy and bucketing
    user_id = db.Column(db.Integer, nullable=False, index=True)
    day = db.Column(db.Date, nullable=False)  # UTC date bucket of occurred_at
    source_label = db.Column(db.String(64), nullable=False)  # e.g., "Meta Ads", "Google", "Organic", "Email", "Direct", "Billboard", "Other", "Unknown"

    # funnel counts
    leads = db.Column(db.Integer, nullable=False, default=0)
    customers = db.Column(db.Integer, nullable=False, default=0)
    orders = db.Column(db.Integer, nullable=False, default=0)

    # revenue and cost in cents to avoid float error
    revenue_cents = db.Column(db.BigInteger, nullable=False, default=0)
    cost_cents = db.Column(db.BigInteger, nullable=False, default=0)

    # churn among customers for this day+source
    churn_customers = db.Column(db.Integer, nullable=False, default=0)
    total_customers = db.Column(db.Integer, nullable=False, default=0)

    # optional extras for debugging or deeper charts
    exits_total = db.Column(db.Integer, nullable=False, default=0)  # across leads+customers+orders if you want parity with previous "exit" idea

    # Enhanced customer analytics
    new_customers = db.Column(db.Integer, nullable=False, default=0)
    repeat_customers = db.Column(db.Integer, nullable=False, default=0)
    unique_customers = db.Column(db.Integer, nullable=False, default=0)
    active_customers = db.Column(db.Integer, nullable=False, default=0)
    reactivated_customers = db.Column(db.Integer, nullable=False, default=0)
    at_risk_customers = db.Column(db.Integer, nullable=False, default=0)
    
    # Revenue analytics
    subscription_revenue_cents = db.Column(db.BigInteger, nullable=False, default=0)
    average_order_value_cents = db.Column(db.BigInteger, nullable=False, default=0)
    high_value_orders = db.Column(db.Integer, nullable=False, default=0)
    
    # Customer lifetime analytics  
    avg_customer_lifetime_days = db.Column(db.Integer, nullable=False, default=0)
    customer_lifetime_days = db.Column(db.BigInteger, nullable=False, default=0)
    
    # Performance metrics
    conversion_rate_pct = db.Column(db.Float, nullable=False, default=0.0)
    customer_retention_pct = db.Column(db.Float, nullable=False, default=0.0)

    # audit
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("user_id", "day", "source_label", name="uq_smd_user_day_source"),
        Index("ix_smd_user_source_day", "user_id", "source_label", "day"),
        Index("ix_smd_user_day", "user_id", "day"),
    )

    # convenience properties for API responses (not persisted)
    @property
    def revenue(self) -> float:
        return float(self.revenue_cents) / 100.0

    @property
    def cost(self) -> float:
        return float(self.cost_cents) / 100.0

    @property
    def roi_pct(self) -> float:
        return 0.0 if self.cost_cents == 0 else ((self.revenue_cents - self.cost_cents) / self.cost_cents) * 100.0

    @property
    def churn_pct(self) -> float:
        return 0.0 if self.total_customers == 0 else (self.churn_customers / self.total_customers) * 100.0


class AnalyticsEtlState(db.Model):
    __tablename__ = "analytics_etl_state"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job = db.Column(db.String(64), nullable=False, unique=True)  # e.g., "source_metrics_daily"
    last_raw_id = db.Column(db.Integer, nullable=False, default=0)
    last_run_at = db.Column(db.DateTime, nullable=False, default=datetime.now(), onupdate=datetime.now())
