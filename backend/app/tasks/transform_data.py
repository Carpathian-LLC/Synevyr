# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# ETL: user_dataset_raw -> leads_clean, customers_clean, orders_clean
#
# Purpose:
#   Normalize raw user events into three clean, denormalized tables.
#   NO analytics here. A separate "analyze" task can roll up daily/weekly KPIs later.
#
# Features:
#   - Robust JSON parsing (dict, list[dict], bytes, JSON strings)
#   - Stable datetime parsing (RFC1123, ISO8601, unix seconds/floats) -> UTC
#   - Amount normalization -> integer cents
#   - Source attribution normalization (honors is_organic)
#   - Idempotent via AnalyticsEtlState cursor + unique (user_id, raw_id, item_idx)
#   - Optional scoped rebuild (force_reprocess + user_ids/since/until)
#   - Extremely verbose logging via debug_logger
#   - Optional auto-DDL for three clean tables (MySQL)
# ------------------------------------------------------------------------------------
from __future__ import annotations

import json
import time
from datetime import datetime, date, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, Iterator, List, Tuple, Set, Optional

from sqlalchemy import text
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError, OperationalError

# Local Imports
from app.utils.logging import debug_logger  # <-- use debug_logger everywhere
from app.extensions import celery, db
from app.models.data_sources import AnalyticsEtlState, UserDatasetRaw
from app.models.clean_staging import LeadsClean, CustomersClean, OrdersClean

# ------------------------------------------------------------------------------------
# Constants

JOB_NAME = "transform_data"
BATCH_SIZE = 5000
LOCK_KEY = "etl:clean_stage_tables"

# Clean staging table references using SQLAlchemy models
LEADS_TBL = LeadsClean.__table__.name
CUSTOMERS_TBL = CustomersClean.__table__.name
ORDERS_TBL = OrdersClean.__table__.name

LABEL_MAP = {
    "meta": "Meta Ads",
    "facebook": "Meta Ads",
    "fb": "Meta Ads",
    "facebook ads": "Meta Ads",
    "google": "Google",
    "google ads": "Google",
    "sem": "Google",
    "email": "Email",
    "newsletter": "Email",
    "organic": "Organic",
    "referral": "Referral",
    "referrer": "Referral",
    "direct": "Direct",
    "billboard": "Billboard",
    "other": "Other",
    "unknown": "Unknown",
}

OK_ORDER_STATUSES = {"completed", "processing", "paid", "shipped", "delivered", "success", "confirmed"}
BAD_ORDER_STATUSES = {"cancelled", "canceled", "refunded", "failed", "declined", "void", "rejected"}

LEAD_EXIT_STATUSES = {"unsubscribed", "disqualified", "invalid", "spam", "optout", "opt-out", "rejected", "bounced"}

CUSTOMER_INACTIVE = {"inactive", "cancelled", "canceled", "churned", "deleted", "suspended", "deactivated"}
CUSTOMER_ACTIVE = {"active", "subscribed", "premium", "verified", "confirmed"}
CUSTOMER_REACTIVATED = {"reactivated", "winback", "returned"}
CUSTOMER_AT_RISK = {"at-risk", "declining", "low-engagement", "inactive-warning"}

# ------------------------------------------------------------------------------------
# Helpers

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _norm_label(s: Optional[str]) -> str:
    raw = (s or "").strip().lower()
    if not raw:
        return "Unknown"
    if raw in LABEL_MAP:
        return LABEL_MAP[raw]
    parts = [w.capitalize() for w in raw.replace("_", " ").replace("-", " ").split() if w]
    return " ".join(parts) if parts else "Unknown"

def _safe_json_loads(s: str):
    try:
        return json.loads(s)
    except Exception:
        return {}

def _iter_payloads(content) -> Iterator[dict]:
    """
    Yield zero or more dict payloads from content:
    - dict
    - list[dict]
    - JSON string of dict or list[dict]
    - bytes/bytearray containing JSON
    """
    if content is None:
        return
    if isinstance(content, dict):
        yield content
        return
    if isinstance(content, list):
        for it in content:
            if isinstance(it, dict):
                yield it
        return
    if isinstance(content, (bytes, bytearray)):
        try:
            obj = json.loads(content.decode("utf-8"))
        except Exception:
            debug_logger.warning("[iter_payloads] Failed bytes->JSON decode")
            return
        if isinstance(obj, dict):
            yield obj
        elif isinstance(obj, list):
            for it in obj:
                if isinstance(it, dict):
                    yield it
        return
    if isinstance(content, str):
        t = content.strip()
        if not t:
            return
        if (t.startswith("{") and t.endswith("}")) or (t.startswith("[") and t.endswith("]")):
            obj = _safe_json_loads(t)
            if isinstance(obj, dict):
                yield obj
            elif isinstance(obj, list):
                for it in obj:
                    if isinstance(it, dict):
                        yield it
        return
    # Unsupported -> yield nothing

def _to_cents(x) -> int:
    if x is None:
        return 0
    
    original_value = x
    
    if isinstance(x, (int, float)):
        try:
            q = Decimal(str(x))
            result = int((q * 100).quantize(Decimal("1")))
            if abs(original_value) >= 1000:  # Only log large amounts to avoid spam
                debug_logger.debug(f"[TRANSFORM] Amount conversion numeric: {original_value} -> {result} cents")
            return result
        except InvalidOperation:
            debug_logger.warning(f"[TRANSFORM] Amount conversion failed for numeric: {original_value}, returning 0")
            return 0
    
    if isinstance(x, str):
        digits = "".join(ch for ch in x if ch.isdigit() or ch in ".-")
        if digits in {"", ".", "-"}:
            debug_logger.debug(f"[TRANSFORM] Amount conversion empty string: '{original_value}' -> 0 cents")
            return 0
        try:
            q = Decimal(digits)
            result = int((q * 100).quantize(Decimal("1")))
            if "$" in original_value or "," in original_value or abs(float(digits)) >= 100:  # Log formatted amounts
                debug_logger.debug(f"[TRANSFORM] Amount conversion string: '{original_value}' -> {result} cents (extracted: {digits})")
            return result
        except InvalidOperation:
            debug_logger.warning(f"[TRANSFORM] Amount conversion failed for string: '{original_value}' (digits: '{digits}'), returning 0")
            return 0
    
    debug_logger.warning(f"[TRANSFORM] Amount conversion failed for type {type(original_value)}: {original_value}, returning 0")
    return 0

def _parse_dt(dt_str: Optional[str], fallback: Optional[datetime]) -> Optional[datetime]:
    if not dt_str:
        return fallback
    s = str(dt_str).strip()
    
    # ISO 8601
    try:
        iso_str = s.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(iso_str)
        debug_logger.debug(f"[TRANSFORM] Parsed datetime ISO: '{dt_str}' -> {parsed}")
        return parsed
    except Exception:
        pass
    
    # RFC 1123 (e.g., Sun, 28 Jan 2024 00:00:00 GMT)
    try:
        parsed = datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
        debug_logger.debug(f"[TRANSFORM] Parsed datetime RFC1123: '{dt_str}' -> {parsed}")
        return parsed
    except Exception:
        pass
    
    # Unix epoch
    try:
        if s.isdigit():
            parsed = datetime.fromtimestamp(int(s), tz=timezone.utc)
            debug_logger.debug(f"[TRANSFORM] Parsed datetime unix_int: '{dt_str}' -> {parsed}")
            return parsed
        if "." in s:
            parsed = datetime.fromtimestamp(float(s), tz=timezone.utc)
            debug_logger.debug(f"[TRANSFORM] Parsed datetime unix_float: '{dt_str}' -> {parsed}")
            return parsed
    except Exception:
        pass
    
    debug_logger.warning(f"[TRANSFORM] Failed to parse datetime: '{dt_str}', using fallback={fallback}")
    return fallback

def _created_at(p: dict, row_record_time: Optional[datetime]) -> Optional[datetime]:
    primary = [
        "created_at", "date_created", "timestamp", "date", "created",
        "date_created_gmt", "order_date", "signup_date", "registered_date"
    ]
    fallback = ["date_paid", "date_completed", "date_paid_gmt", "date_completed_gmt"]
    updated_like = ["updated_at", "modified", "date_modified", "date_modified_gmt", "last_seen", "last_login"]

    for field in primary:
        if p.get(field):
            dt = _parse_dt(p[field], None)
            if dt:
                return dt
    for field in fallback:
        if p.get(field):
            dt = _parse_dt(p[field], None)
            if dt:
                return dt
    for field in updated_like:
        if p.get(field):
            dt = _parse_dt(p[field], None)
            if dt:
                return dt
    return row_record_time or _utc_now()

def _source_label(p: dict, t: str) -> str:
    # Respect is_organic if present
    if str(p.get("is_organic", "")).strip().lower() in {"1", "true", "yes"} or p.get("is_organic") is True:
        return "Organic"

    for field in [
        "utm_source", "source", "platform", "channel", "network",
        "referrer", "created_via", "medium", "campaign_source",
        "traffic_source", "attribution", "origin"
    ]:
        val = p.get(field)
        if val:
            s = str(val).strip()
            if s and s.lower() != "unknown":
                return _norm_label(s)

    if t == "lead":
        return "Marketing"
    if t == "order":
        return "E-commerce"
    if t == "customer":
        return "Direct"
    return "Unknown"

def _order_status(p: dict) -> str:
    for field in ["status", "order_status", "payment_status", "transaction_status", "state"]:
        if p.get(field):
            return str(p[field]).lower().strip()
    return ""

def _customer_status(p: dict) -> str:
    for field in ["activity_status", "account_status", "subscription_status", "status", "state"]:
        if p.get(field):
            return str(p[field]).lower().strip()
    return ""

def _lead_status(p: dict) -> str:
    for field in ["lead_status", "status", "campaign_status", "ad_status", "state"]:
        if p.get(field):
            return str(p[field]).lower().strip()
    return ""

def _ad_spend_cents(p: dict) -> int:
    for field in [
        "total_spend", "spend", "amount_spent", "cost", "ad_spend",
        "advertising_cost", "campaign_cost", "media_spend", "budget"
    ]:
        if field in p:
            c = _to_cents(p.get(field))
            if c > 0:
                return c
    return 0

def _extract_revenue_cents(p: dict) -> int:
    for field in [
        "total", "amount", "price", "value", "revenue", "order_total",
        "transaction_amount", "payment_amount", "gross", "subtotal"
    ]:
        if field in p:
            c = _to_cents(p.get(field))
            if c > 0:
                return c
    return 0

def _extract_email(p: dict) -> str:
    for field in ["email", "email_address", "user_email", "customer_email", "contact_email"]:
        v = p.get(field)
        if v:
            email = str(v).strip().lower()
            if "@" in email:
                return email
    return ""

def _detect_type(p: dict) -> str:
    order_fields = {"total", "amount", "price", "cost", "revenue", "payment", "order_id", "transaction_id", "number"}
    status_fields = {"status", "order_status", "payment_status", "transaction_status"}
    if any(f in p for f in order_fields) and any(f in p for f in status_fields):
        return "order"
    lead_fields = {"lead_status", "campaign", "ad_id", "utm_source", "utm_campaign", "source", "medium", "platform", "form_id"}
    if any(f in p for f in lead_fields):
        return "lead"
    customer_fields = {"email", "first_name", "last_name", "customer_id", "user_id"}
    activity_fields = {"activity_status", "subscription_status", "account_status", "last_login", "signup_date"}
    if any(f in p for f in customer_fields) and any(f in p for f in activity_fields):
        return "customer"
    if any(f in p for f in customer_fields):
        return "customer"
    if any(f in p for f in order_fields):
        return "order"
    if any(f in p for f in lead_fields):
        return "lead"
    return "interaction"

def _ymd(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date().isoformat()
    except Exception:
        return None

def _json_dump(obj: dict) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        try:
            return json.dumps(obj, ensure_ascii=False)
        except Exception:
            return "{}"

def _get_or_create_master_customer(email: str, payload: dict, user_id: int, raw_id: int, item_idx: int, created_dt: datetime, day_iso: str, label: str) -> Optional[int]:
    """
    Find or create master customer record using customer_id + email. Returns master_customer_id.
    Priority: 1) customer_id from payload, 2) email matching
    """
    customer_id_from_payload = payload.get("customer_id")
    
    # First try: Look up by customer_id (from original CRM customer relationship)
    if customer_id_from_payload:
        try:
            existing = db.session.query(CustomersClean).filter_by(customer_id=customer_id_from_payload).first()
            if existing:
                debug_logger.debug(f"[{JOB_NAME}] Found master customer by customer_id={customer_id_from_payload} -> id={existing.id}")
                return existing.id
        except Exception as e:
            debug_logger.warning(f"[{JOB_NAME}] Error querying master customer by customer_id {customer_id_from_payload}: {e}")
    
    # Second try: Look up by email if no customer_id match
    if email:
        try:
            existing = db.session.query(CustomersClean).filter_by(email=email).first()
            if existing:
                debug_logger.debug(f"[{JOB_NAME}] Found existing master customer by email={email} -> id={existing.id}")
                return existing.id
        except Exception as e:
            debug_logger.warning(f"[{JOB_NAME}] Error querying master customer by email {email}: {e}")
    
    # No existing customer found - need email to create new record
    if not email:
        debug_logger.warning(f"[{JOB_NAME}] Cannot create master customer: no email provided (customer_id={customer_id_from_payload})")
        return None
    
    # Create new master customer record
    try:
        master_customer = {
            "user_id": user_id,
            "raw_id": raw_id, 
            "item_idx": item_idx,
            "created_at": created_dt.astimezone(timezone.utc).replace(tzinfo=None),
            "day": day_iso,
            "source_label": label,
            "customer_id": payload.get("customer_id"),
            "email": email,
            "first_name": payload.get("first_name"),
            "last_name": payload.get("last_name"),
            "phone": payload.get("phone"),
            "city": payload.get("city"),
            "state": payload.get("state"),
            "country": payload.get("country"),
            "zipcode": payload.get("zipcode"),
            "address": payload.get("address"),
            "activity_status": _customer_status(payload) or None,
            "subscription_status": payload.get("subscription_status"),
            "unsubscribed_on": None,
            "last_login": _parse_dt(payload.get("last_login"), None),
            "signup_date": _parse_dt(payload.get("signup_date"), None).date() if _parse_dt(payload.get("signup_date"), None) else None,
            "total_spend_cents": _extract_revenue_cents(payload),
            "subscription_value_cents": 0,
            "raw_payload_json": _json_dump(payload),
        }
        
        # Normalize datetime to naive UTC
        if master_customer["last_login"]:
            master_customer["last_login"] = master_customer["last_login"].astimezone(timezone.utc).replace(tzinfo=None)
        
        # Insert master customer record with ON DUPLICATE KEY handling
        stmt = mysql_insert(CustomersClean.__table__).values(**master_customer)
        stmt = stmt.on_duplicate_key_update(
            # On duplicate email or customer_id, update key fields and keep existing record
            activity_status=stmt.inserted.activity_status,
            last_login=stmt.inserted.last_login,
            total_spend_cents=stmt.inserted.total_spend_cents,
            # Ensure customer_id is set if it wasn't before
            customer_id=stmt.inserted.customer_id
        )
        result = db.session.execute(stmt)
        db.session.flush()  # Get the ID without committing
        
        # For duplicate key updates, lastrowid might be 0, so query for the existing record
        if result.lastrowid:
            new_id = result.lastrowid
            debug_logger.info(f"[{JOB_NAME}] Created new master customer id={new_id} for email={email} customer_id={customer_id_from_payload}")
        else:
            # Duplicate key - find existing record by email or customer_id
            existing = None
            if customer_id_from_payload:
                existing = db.session.query(CustomersClean).filter_by(customer_id=customer_id_from_payload).first()
            if not existing and email:
                existing = db.session.query(CustomersClean).filter_by(email=email).first()
            
            new_id = existing.id if existing else None
            debug_logger.info(f"[{JOB_NAME}] Found existing master customer id={new_id} for email={email} customer_id={customer_id_from_payload}")
        
        return new_id
        
    except Exception as e:
        debug_logger.error(f"[{JOB_NAME}] Failed to create master customer for {email}: {e}")
        return None

# ------------------------------------------------------------------------------------
# Create clean staging tables using SQLAlchemy models
def _ensure_clean_tables() -> None:
    debug_logger.info("[DDL] Ensuring clean staging tables exist using SQLAlchemy models.")
    try:
        # Create tables using SQLAlchemy metadata
        LeadsClean.__table__.create(db.engine, checkfirst=True)
        CustomersClean.__table__.create(db.engine, checkfirst=True)
        OrdersClean.__table__.create(db.engine, checkfirst=True)
        debug_logger.info("[DDL] Clean staging tables created/verified successfully.")
    except Exception as e:
        debug_logger.error(f"[DDL] Failed to create clean staging tables: {e}")
        raise

# ------------------------------------------------------------------------------------
# Celery Task

@celery.task(
    name="app.tasks.transform_data.transform_data_task",
    bind=True,
    autoretry_for=(OperationalError,),
    retry_backoff=5,
    retry_backoff_max=60,
    retry_jitter=True,
)
def transform_data_task(self, _previous_result=None, **kwargs):
    """
    Normalize rows from user_dataset_raw into:
      - leads_clean       (advertising/marketing leads)
      - customers_clean   (contacts/accounts)
      - orders_clean      (transactions)

    No analytics here. Build metrics in a separate analyze task.

    kwargs:
        force_reprocess: bool
        user_ids: Optional[List[int]]
        since: Optional['YYYY-MM-DD'] inclusive lower bound (on created_at day)
        until: Optional['YYYY-MM-DD'] inclusive upper bound
        create_tables: bool (default True) -> run CREATE TABLE IF NOT EXISTS
    """
    force_reprocess: bool = bool(kwargs.get("force_reprocess", False))
    scope_user_ids: Optional[List[int]] = kwargs.get("user_ids")
    since_ymd: Optional[str] = _ymd(kwargs.get("since"))
    until_ymd: Optional[str] = _ymd(kwargs.get("until"))
    create_tables: bool = kwargs.get("create_tables", True)

    t0 = time.monotonic()
    debug_logger.info(f"[{JOB_NAME}] START task_id={self.request.id} force_reprocess={force_reprocess} "
                      f"user_ids={scope_user_ids} since={since_ymd} until={until_ymd} create_tables={create_tables}")
    
    # Initial progress
    self.update_state(state="PROGRESS", meta={
        "step": "initializing",
        "message": "Starting data transformation",
        "progress": 0
    })

    # Optional: ensure clean tables exist
    if create_tables:
        _ensure_clean_tables()

    # Acquire advisory lock
    try:
        got = db.session.execute(text("SELECT GET_LOCK(:k, 0)"), {"k": LOCK_KEY}).scalar()
        debug_logger.info(f"[{JOB_NAME}] GET_LOCK key={LOCK_KEY} got={got}")
    except Exception as e:
        debug_logger.exception(f"[{JOB_NAME}] FAILED to acquire DB lock: {e}")
        self.update_state(state="FAILURE", meta={"error": f"DB lock failure: {e}", "traceback": str(e)})
        raise
    if got != 1:
        debug_logger.warning(f"[{JOB_NAME}] SKIP: lock busy key={LOCK_KEY}")
        return {"skipped": True, "reason": "lock_busy"}

    def _unlock():
        try:
            db.session.execute(text("SELECT RELEASE_LOCK(:k)"), {"k": LOCK_KEY})
            db.session.commit()
            debug_logger.info(f"[{JOB_NAME}] Lock released key={LOCK_KEY}")
        except Exception:
            db.session.rollback()
            debug_logger.error(f"[{JOB_NAME}] FAILED to release lock key={LOCK_KEY}")

    try:
        # Clear existing clean data if force_reprocess is requested
        if force_reprocess:
            params: Dict[str, object] = {}
            where = []
            if scope_user_ids:
                where.append("user_id IN :uids")
                params["uids"] = tuple(scope_user_ids)
            if since_ymd:
                where.append("day >= :since")
                params["since"] = since_ymd
            if until_ymd:
                where.append("day <= :until")
                params["until"] = until_ymd
            where_sql = (" WHERE " + " AND ".join(where)) if where else ""

            for tbl in (LEADS_TBL, CUSTOMERS_TBL, ORDERS_TBL):
                sql = f"DELETE FROM {tbl}{where_sql}"
                debug_logger.warning(f"[{JOB_NAME}] Force reprocess clearing: {sql} params={params}")
                result = db.session.execute(text(sql), params)
                rows_deleted = result.rowcount if hasattr(result, 'rowcount') else 'unknown'
                debug_logger.info(f"[{JOB_NAME}] Deleted {rows_deleted} rows from {tbl}")
            db.session.commit()
            debug_logger.warning(f"[{JOB_NAME}] Clean tables cleared for reprocessing")

        totals = {
            "loops": 0,
            "batches": 0,
            "fetched": 0,
            "processed_payloads": 0,
            "skipped_no_time": 0,
            "upserts_leads": 0,
            "upserts_customers": 0,
            "upserts_orders": 0,
        }

        # Get total count for progress tracking
        total_raw_records = 0
        try:
            total_raw_records = db.session.query(db.func.count(UserDatasetRaw.id)).scalar() or 0
            debug_logger.info(f"[{JOB_NAME}] Total raw records to process: {total_raw_records}")
        except Exception as e:
            debug_logger.warning(f"[{JOB_NAME}] Could not get total count: {e}")

        self.update_state(state="PROGRESS", meta={
            "step": "processing",
            "message": f"Processing {total_raw_records:,} raw records",
            "progress": 1,
            "total_records": total_raw_records,
            "processed_records": 0
        })

        # Process ALL raw data in batches, let MySQL handle duplicates via UNIQUE constraints
        current_offset = 0
        
        while True:
            totals["loops"] += 1
            batch_start = time.monotonic()

            # Fetch a page of raw rows (no cursor filtering - process everything)
            try:
                rows: List[UserDatasetRaw] = (
                    db.session.query(UserDatasetRaw)
                    .order_by(UserDatasetRaw.id.asc())
                    .offset(current_offset)
                    .limit(BATCH_SIZE)
                    .all()
                )
            except Exception as e:
                debug_logger.exception(f"[{JOB_NAME}] FAILED to fetch raw rows at offset={current_offset}: {e}")
                raise

            if not rows:
                debug_logger.info(f"[{JOB_NAME}] No more rows at offset={current_offset}. Processing complete.")
                break

            totals["batches"] += 1
            totals["fetched"] += len(rows)
            min_id, max_id = rows[0].id, rows[-1].id
            debug_logger.info(f"[{JOB_NAME}] Batch {totals['batches']} fetched size={len(rows)} id_range=[{min_id},{max_id}] offset={current_offset}")

            # In-batch counters for logging
            leads_batch = customers_batch = orders_batch = 0

            for row in rows:
                # Log raw row envelope (not full payload yet)
                debug_logger.info(f"[{JOB_NAME}] raw_row id={row.id} user_id={row.user_id} record_time={getattr(row,'record_time',None)}")

                # Iterate payloads; maintain item index per raw row
                for item_idx, payload in enumerate(_iter_payloads(row.content)):
                    totals["processed_payloads"] += 1
                    # Log first 3 payloads verbosely; others summarized
                    if item_idx < 3:
                        debug_logger.info(f"[{JOB_NAME}] payload@{row.id}[{item_idx}] keys={list(payload.keys())[:15]}")
                    else:
                        debug_logger.debug(f"[{JOB_NAME}] payload@{row.id}[{item_idx}] keys={list(payload.keys())[:15]}")

                    t = _detect_type(payload)
                    created_dt = _created_at(payload, getattr(row, "record_time", None))
                    if not created_dt:
                        totals["skipped_no_time"] += 1
                        debug_logger.warning(f"[{JOB_NAME}] skip payload (no time) row_id={row.id} idx={item_idx}")
                        continue
                    if created_dt.tzinfo is None:
                        created_dt = created_dt.replace(tzinfo=timezone.utc)
                    day_iso = created_dt.astimezone(timezone.utc).date().isoformat()
                    label = _source_label(payload, t)
                    email = _extract_email(payload)

                    # Scope filter by day/user (only applies when force_reprocess scope used)
                    if since_ymd and day_iso < since_ymd:
                        debug_logger.debug(f"[{JOB_NAME}] scoped-out (before since) row_id={row.id} idx={item_idx} day={day_iso}")
                        continue
                    if until_ymd and day_iso > until_ymd:
                        debug_logger.debug(f"[{JOB_NAME}] scoped-out (after until) row_id={row.id} idx={item_idx} day={day_iso}")
                        continue
                    if scope_user_ids and row.user_id not in scope_user_ids:
                        debug_logger.debug(f"[{JOB_NAME}] scoped-out user row_id={row.id} idx={item_idx} user_id={row.user_id}")
                        continue

                    # Get or create master customer record for linking
                    master_customer_id = None
                    if email:
                        master_customer_id = _get_or_create_master_customer(
                            email, payload, row.user_id, row.id, item_idx, created_dt, day_iso, label
                        )
                        
                    # Common fields for all upserts
                    common = {
                        "user_id": row.user_id,
                        "raw_id": row.id,
                        "item_idx": item_idx,
                        "created_at": created_dt.astimezone(timezone.utc).replace(tzinfo=None),
                        "day": day_iso,
                        "source_label": label,
                        "raw_payload_json": _json_dump(payload),
                    }

                    # Dispatch by detected type
                    if t == "lead":
                        # Extract lead fields
                        rec = dict(common)
                        rec.update({
                            "is_organic": 1 if str(payload.get("is_organic", "")).lower() in {"1","true","yes"} or payload.get("is_organic") is True else 0,
                            "platform": payload.get("platform"),
                            "channel": payload.get("channel"),
                            "network": payload.get("network"),
                            "utm_source": payload.get("utm_source"),
                            "utm_medium": payload.get("utm_medium"),
                            "utm_campaign": payload.get("utm_campaign"),
                            "utm_term": payload.get("utm_term"),
                            "utm_content": payload.get("utm_content"),
                            "campaign_id": payload.get("campaign_id"),
                            "campaign_name": payload.get("campaign_name"),
                            "adset_id": payload.get("adset_id"),
                            "adset_name": payload.get("adset_name"),
                            "ad_id": payload.get("ad_id"),
                            "ad_name": payload.get("ad_name"),
                            "form_id": payload.get("form_id"),
                            "form_name": payload.get("form_name"),
                            "lead_status": _lead_status(payload) or None,
                            "email": email or None,
                            "first_name": payload.get("first_name"),
                            "last_name": payload.get("last_name"),
                            "phone": payload.get("phone"),
                            "city": payload.get("city"),
                            "state": payload.get("state"),
                            "country": payload.get("country"),
                            "zipcode": payload.get("zipcode"),
                            "referrer": payload.get("referrer") or payload.get("referral"),
                            "cost_cents": _ad_spend_cents(payload),
                            "master_customer_id": master_customer_id,
                        })
                        _upsert_row(LEADS_TBL, rec)
                        leads_batch += 1
                        debug_logger.debug(f"[{JOB_NAME}] UPSERT lead row_id={row.id} idx={item_idx} email={email} label={label} day={day_iso}")

                    elif t == "order":
                        # Extract order fields
                        rec = dict(common)
                        rec.update({
                            "order_number": str(payload.get("number") or payload.get("order_id") or "") or None,
                            "transaction_id": payload.get("transaction_id"),
                            "status": _order_status(payload) or None,
                            "customer_id": payload.get("customer_id"),
                            "email": email or None,
                            "currency": payload.get("currency"),
                            "payment_method": payload.get("payment_method") or payload.get("payment_method_title"),
                            "created_via": payload.get("created_via"),
                            "date_paid": _parse_dt(payload.get("date_paid") or payload.get("date_paid_gmt"), None),
                            "date_completed": _parse_dt(payload.get("date_completed") or payload.get("date_completed_gmt"), None),
                            "total_cents": _to_cents(payload.get("total")),
                            "subtotal_cents": _to_cents(payload.get("subtotal")),
                            "discount_total_cents": _to_cents(payload.get("discount_total") or payload.get("discount_tax")),
                            "shipping_total_cents": _to_cents(payload.get("shipping_total") or payload.get("shipping_tax")),
                            "tax_total_cents": _to_cents(payload.get("total_tax") or payload.get("cart_tax")),
                            "store_credit_cents": _to_cents(payload.get("store_credit_used")),
                            "subscription_value_cents": 0,
                            "line_items": str(payload.get("line_items") or payload.get("items") or payload.get("products") or "") or None,
                            "master_customer_id": master_customer_id,
                        })
                        # crude subscription detection
                        items_blob = (rec["line_items"] or "").lower()
                        if any(term in items_blob for term in ["subscription", "monthly", "yearly", "recurring", "plan"]):
                            rec["subscription_value_cents"] = rec.get("total_cents", 0)

                        # Normalize datetimes to naive UTC for MySQL DATETIME
                        if rec["date_paid"]:
                            rec["date_paid"] = rec["date_paid"].astimezone(timezone.utc).replace(tzinfo=None)
                        if rec["date_completed"]:
                            rec["date_completed"] = rec["date_completed"].astimezone(timezone.utc).replace(tzinfo=None)

                        _upsert_row(ORDERS_TBL, rec)
                        orders_batch += 1
                        debug_logger.debug(f"[{JOB_NAME}] UPSERT order row_id={row.id} idx={item_idx} num={rec['order_number']} status={rec['status']} day={day_iso}")

                    else:
                        # Customer records are now handled in _get_or_create_master_customer()
                        # This section handles any other unclassified data types
                        debug_logger.debug(f"[{JOB_NAME}] Skipping unclassified record type row_id={row.id} idx={item_idx} type={t}")

            # Commit once per batch for throughput
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                debug_logger.exception(f"[{JOB_NAME}] Commit failure after batch id_range=[{min_id},{max_id}]: {e}")
                raise

            # Advance offset for next batch
            current_offset += len(rows)
            
            batch_ms = int((time.monotonic() - batch_start) * 1000)
            totals["upserts_leads"] += leads_batch
            totals["upserts_customers"] += customers_batch
            totals["upserts_orders"] += orders_batch

            debug_logger.info(
                f"[{JOB_NAME}] Batch {totals['batches']} committed leads={leads_batch} customers={customers_batch} "
                f"orders={orders_batch} next_offset={current_offset} elapsed_ms={batch_ms}"
            )

            # Update progress every batch
            progress_pct = min(95, int((current_offset / max(total_raw_records, 1)) * 90) + 5)
            self.update_state(state="PROGRESS", meta={
                "step": "processing",
                "message": f"Processed {current_offset:,}/{total_raw_records:,} records",
                "progress": progress_pct,
                "total_records": total_raw_records,
                "processed_records": current_offset,
                "batch": totals["batches"],
                "leads": totals["upserts_leads"],
                "customers": len(set()),  # We don't track individual customers anymore
                "orders": totals["upserts_orders"]
            })

            # Continue processing until we've fetched fewer rows than BATCH_SIZE
            if len(rows) < BATCH_SIZE:
                debug_logger.info(f"[{JOB_NAME}] Last batch (size {len(rows)} < {BATCH_SIZE}), processing complete")
                break

        dur_ms = int((time.monotonic() - t0) * 1000)
        debug_logger.info(
            f"[{JOB_NAME}] COMPLETE loops={totals['loops']} batches={totals['batches']} fetched={totals['fetched']} "
            f"processed_payloads={totals['processed_payloads']} leads_upserts={totals['upserts_leads']} "
            f"customers_upserts={totals['upserts_customers']} orders_upserts={totals['upserts_orders']} "
            f"total_processed={current_offset} elapsed_ms={dur_ms}"
        )

        # Final success progress
        self.update_state(state="SUCCESS", meta={
            "step": "complete",
            "message": f"Transformation complete: {totals['upserts_leads']} leads, {totals['upserts_orders']} orders processed",
            "progress": 100,
            "total_records": total_raw_records,
            "processed_records": current_offset,
            "leads": totals["upserts_leads"],
            "orders": totals["upserts_orders"],
            "elapsed_ms": dur_ms
        })

        return {
            "status": "ok",
            "total_processed": current_offset,
            "counts": totals,
            "elapsed_ms": dur_ms,
        }

    except Exception as e:
        debug_logger.exception(f"[{JOB_NAME}] FATAL: {e}")
        raise
    finally:
        _unlock()

# ------------------------------------------------------------------------------------
# Internal: SQLAlchemy-based upsert into clean staging tables
def _upsert_row(table_name: str, rec: Dict[str, object]) -> None:
    # Map table names to SQLAlchemy models
    model_map = {
        LEADS_TBL: LeadsClean,
        CUSTOMERS_TBL: CustomersClean,
        ORDERS_TBL: OrdersClean,
    }
    
    model_class = model_map.get(table_name)
    if not model_class:
        raise ValueError(f"Unknown table name: {table_name}")
    
    # Use MySQL INSERT ... ON DUPLICATE KEY UPDATE with SQLAlchemy
    insert_stmt = mysql_insert(model_class.__table__).values(**rec)
    
    # Build update dict excluding unique constraint fields
    update_dict = {
        col: insert_stmt.inserted[col] 
        for col in rec.keys() 
        if col not in ("user_id", "raw_id", "item_idx")
    }
    
    upsert_stmt = insert_stmt.on_duplicate_key_update(**update_dict)
    db.session.execute(upsert_stmt)
    
    # Verbose single-line trace of key fields
    debug_logger.debug(f"UPSERT {table_name} key=(user_id={rec.get('user_id')}, raw_id={rec.get('raw_id')}, idx={rec.get('item_idx')})")
