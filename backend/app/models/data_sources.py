# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# PLATFORM MODELS - Data Source Management
# ------------------------------------------------------------------------------------
# These models manage how Synevyr's platform users configure and ingest their data.
# This includes data source definitions, raw data storage, and processing pipelines.
#
# Platform Models in this file:
# - DataSource: Platform users' data source configurations (API connections, etc.)
# - UserDatasetRaw: Raw data ingested from platform users' data sources
# - AnalyticsEtlState: ETL job state tracking for data processing
#
# These are platform infrastructure models, not the actual customer data being analyzed.
# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime
from app.extensions import db
from sqlalchemy import ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.mysql import DATETIME as MySQLDateTime

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

    id          = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id     = db.Column(db.Integer,    ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_id   = db.Column(db.BigInteger,  ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False)

    record_time = db.Column(MySQLDateTime(fsp=6), nullable=True)   # informational only
    ingested_at = db.Column(MySQLDateTime(fsp=6), nullable=False, default=datetime.now)
    created_at  = db.Column(MySQLDateTime(fsp=6), nullable=False, default=datetime.now)

    content       = db.Column(db.JSON, nullable=False)
    content_hash  = db.Column(db.BINARY(32), nullable=False)  # SHA-256 digest of canonical JSON (32 bytes fixed)
    content_type  = db.Column(db.Enum("json", "csv", "xml", "text"), nullable=False, default="json")
    schema_hint   = db.Column(db.String(128), nullable=True)
    status        = db.Column(db.Enum("ok", "error", "skipped"), nullable=False, default="ok")
    error_message = db.Column(db.Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("content_hash", name="uq_global_content_hash"),
        Index("idx_ingested_at", "ingested_at", "id"),
        Index("idx_record_time", "record_time", "id"),
        Index("idx_source", "source_id"),
    )

    def __repr__(self):
        return f"<UserDatasetRaw id={self.id} src={self.source_id} user={self.user_id}>"

class AnalyticsEtlState(db.Model):
    __tablename__ = "analytics_etl_state"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job = db.Column(db.String(64), nullable=False, unique=True)  # e.g., "source_metrics_daily"
    last_raw_id = db.Column(db.Integer, nullable=False, default=0)
    last_run_at = db.Column(db.DateTime, nullable=False, default=datetime.now(), onupdate=datetime.now())
