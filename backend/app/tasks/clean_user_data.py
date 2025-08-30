# app/tasks/clean_user_data.py
# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# Cleans raw rows into source_metrics_daily with incremental, idempotent upserts.
# Extremely verbose logging and resilient error handling.
# Runs via Beat every 6 hours and can be chained after ingestion.
# ------------------------------------------------------------------------------------
import json
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.dialects.mysql import insert as mysql_insert

# Local Imports
from app.utils.logging import celery_logger
from app.extensions import celery, db
from app.models.data_sources import SourceMetricsDaily, AnalyticsEtlState, UserDatasetRaw

# ------------------------------------------------------------------------------------
# Consts
JOB_NAME = "source_metrics_daily"
BATCH_SIZE = 5000
LOCK_KEY = "etl:source_metrics_daily"

ORDER_OK = {"processing", "completed", "on-hold"}
ORDER_CANCEL_OR_EXIT = {"refunded", "cancelled", "canceled", "failed", "trash", "pending-cancel"}
CUSTOMER_EXIT_STATUSES = {"inactive", "cancelled", "canceled", "churned", "deleted"}

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
    "direct": "Direct",
    "billboard": "Billboard",
    "other": "Other",
    "unknown": "Unknown",
}

# ------------------------------------------------------------------------------------
# Helpers

def _norm_label(s: str | None) -> str:
    raw = (s or "").strip().lower()
    if not raw:
        return "Unknown"
    if raw in LABEL_MAP:
        return LABEL_MAP[raw]
    parts = [w.capitalize() for w in raw.replace("_", " ").replace("-", " ").split() if w]
    return " ".join(parts) if parts else "Unknown"

def _safe_obj(content) -> dict:
    if isinstance(content, dict):
        return content
    if isinstance(content, (bytes, bytearray)):
        try:
            return json.loads(content.decode("utf-8"))
        except Exception:
            return {}
    if isinstance(content, str):
        t = content.strip()
        if (t.startswith("{") and t.endswith("}")) or (t.startswith("[") and t.endswith("]")):
            try:
                obj = json.loads(t)
                return obj if isinstance(obj, dict) else {}
            except Exception:
                return {}
    return {}

def _to_cents(x) -> int:
    if x is None:
        return 0
    if isinstance(x, (int, float)):
        try:
            q = Decimal(str(x))
        except InvalidOperation:
            return 0
        return int((q * 100).quantize(Decimal("1")))
    if isinstance(x, str):
        digits = "".join(ch for ch in x if ch.isdigit() or ch in ".-")
        if digits in {"", ".", "-"}:
            return 0
        try:
            q = Decimal(digits)
        except InvalidOperation:
            return 0
        return int((q * 100).quantize(Decimal("1")))
    return 0

def _detect_type(p: dict) -> str:
    platform = str(p.get("platform") or "").lower()
    has_lead = "lead_status" in p or platform in {"meta", "facebook", "google"}
    has_woo = ("total" in p and "status" in p and "number" in p)
    has_customer = ("first_name" in p and "last_name" in p and "activity_status" in p)
    if has_woo:
        return "woo"
    if has_lead:
        return "meta"
    if has_customer:
        return "customer"
    return "unknown"

def _parse_dt(dt_str: str | None, fallback: datetime | None) -> datetime | None:
    if not dt_str:
        return fallback
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        pass
    try:
        return datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
    except Exception:
        return fallback

def _created_at(p: dict, row_record_time: datetime | None) -> datetime | None:
    t = _detect_type(p)
    if t == "woo":
        return _parse_dt(p.get("date_created") or p.get("date_created_gmt"), row_record_time)
    if t in {"meta", "customer"}:
        return _parse_dt(p.get("created_at"), row_record_time)
    return row_record_time

def _source_label(p: dict, t: str) -> str:
    if t == "meta":
        platform = str(p.get("platform") or "").lower() or "meta"
        return _norm_label(platform)
    if t == "customer":
        return _norm_label(str(p.get("referrer") or ""))
    if t == "woo":
        return _norm_label(str(p.get("created_via") or ""))
    return "Unknown"

def _order_status(p: dict) -> str:
    s = p.get("status")
    return str(s).lower() if isinstance(s, str) else ""

def _customer_status(p: dict) -> str:
    s = p.get("activity_status")
    return str(s).lower() if isinstance(s, str) else ""

def _lead_status(p: dict) -> str:
    s = p.get("lead_status")
    return str(s).lower() if isinstance(s, str) else ""

def _ad_spend_cents(p: dict) -> int:
    for k in ("total_spend", "spend", "amount_spent", "cost", "ad_spend"):
        if k in p:
            c = _to_cents(p.get(k))
            if c > 0:
                return c
    return 0

def _trim_for_log(obj, limit: int = 400) -> str:
    try:
        s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        s = str(obj)
    return s if len(s) <= limit else s[:limit] + "...(truncated)"

# ------------------------------------------------------------------------------------
# Task

@celery.task(
    name="app.tasks.clean_user_data.build_source_metrics_daily_task",
    bind=True,
    autoretry_for=(OperationalError,),
    retry_backoff=5,
    retry_backoff_max=60,
    retry_jitter=True,
)
def build_source_metrics_daily_task(self, _previous_result=None):
    """
    Incrementally processes new rows from user_dataset_raw into source_metrics_daily.
    - Cursor-based idempotency via analytics_etl_state.last_raw_id
    - Advisory lock to prevent concurrent cleaners
    - Very verbose logging at each stage
    - Accepts an optional prior result when used in a Celery chain.
    """
    t0 = time.monotonic()
    celery_logger.info(f"[{JOB_NAME}] START task_id={self.request.id}")

    # --- Acquire advisory lock (no wait). If unavailable, exit gracefully. ---
    try:
        got = db.session.execute(text("SELECT GET_LOCK(:k, 0)"), {"k": LOCK_KEY}).scalar()
    except Exception as e:
        celery_logger.exception(f"[{JOB_NAME}] FAILED to acquire DB lock due to DB error: {e}")
        raise

    if got != 1:
        celery_logger.warning(f"[{JOB_NAME}] SKIP: lock busy key={LOCK_KEY}")
        return {"skipped": True, "reason": "lock_busy"}

    # Ensure lock is released even on exceptions
    def _unlock():
        try:
            db.session.execute(text("SELECT RELEASE_LOCK(:k)"), {"k": LOCK_KEY})
            db.session.commit()
        except Exception:
            db.session.rollback()
            celery_logger.error(f"[{JOB_NAME}] FAILED to release lock key={LOCK_KEY}")

    try:
        # --- Load or create cursor state ---
        try:
            state = (
                db.session.query(AnalyticsEtlState)
                .filter_by(job=JOB_NAME)
                .with_for_update(nowait=False)
                .first()
            )
            if not state:
                state = AnalyticsEtlState(job=JOB_NAME, last_raw_id=0, last_run_at=datetime.now())
                db.session.add(state)
                db.session.commit()
            celery_logger.info(f"[{JOB_NAME}] Cursor loaded last_raw_id={state.last_raw_id}")
        except Exception as e:
            db.session.rollback()
            celery_logger.exception(f"[{JOB_NAME}] FAILED to load/create cursor: {e}")
            raise

        totals = {
            "loops": 0,
            "batches": 0,
            "fetched": 0,
            "processed": 0,
            "skipped_no_time": 0,
            "skipped_unknown": 0,
            "meta_rows": 0,
            "customer_rows": 0,
            "woo_rows": 0,
            "orders_ok": 0,
            "orders_cancel_or_exit": 0,
            "spend_rows": 0,
            "agg_keys_upserted": 0,
        }

        while True:
            totals["loops"] += 1
            batch_start = time.monotonic()

            # --- Pull next page of raw rows ---
            try:
                rows = (
                    db.session.query(UserDatasetRaw)
                    .filter(UserDatasetRaw.id > state.last_raw_id)
                    .order_by(UserDatasetRaw.id.asc())
                    .limit(BATCH_SIZE)
                    .all()
                )
            except Exception as e:
                celery_logger.exception(f"[{JOB_NAME}] FAILED to fetch raw rows after id={state.last_raw_id}: {e}")
                raise

            if not rows:
                celery_logger.info(f"[{JOB_NAME}] No new rows after id={state.last_raw_id}. Done.")
                break

            totals["batches"] += 1
            totals["fetched"] += len(rows)
            min_id = rows[0].id
            max_id = rows[-1].id
            celery_logger.info(f"[{JOB_NAME}] Batch fetched size={len(rows)} id_range=[{min_id},{max_id}]")

            # --- Aggregate in-memory ---
            agg: dict[tuple[int, str, str], dict[str, int]] = {}  # (user_id, day_iso, source_label) -> counters
            max_id_in_batch = state.last_raw_id

            for row in rows:
                max_id_in_batch = max(max_id_in_batch, row.id)
                payload = _safe_obj(row.content)
                t = _detect_type(payload)

                if t == "unknown":
                    totals["skipped_unknown"] += 1
                    continue

                created_dt = _created_at(payload, row.record_time or getattr(row, "ingested_at", None))
                if not created_dt:
                    totals["skipped_no_time"] += 1
                    continue

                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                day_iso = created_dt.astimezone(timezone.utc).date().isoformat()
                label = _source_label(payload, t)
                key = (row.user_id, day_iso, label)

                if key not in agg:
                    agg[key] = {
                        "leads": 0,
                        "customers": 0,
                        "orders": 0,
                        "revenue_cents": 0,
                        "cost_cents": 0,
                        "churn_customers": 0,
                        "total_customers": 0,
                        "exits_total": 0,
                        "new_customers": 0,
                        "repeat_customers": 0,
                        "subscription_revenue_cents": 0,
                        "average_order_value_cents": 0,
                        "high_value_orders": 0,  # orders > $100
                        "orders_value_sum_cents": 0,  # for AOV calculation
                        "customer_lifetime_days": 0,  # total days all customers active
                        "active_customers": 0,  # currently active
                        "reactivated_customers": 0,  # came back from churn
                        "at_risk_customers": 0,  # showing decline signs
                        "customer_emails": set(),  # track unique customers for LTV
                    }

                bucket = agg[key]

                if t == "meta":
                    totals["meta_rows"] += 1
                    bucket["leads"] += 1
                    cost_cents = _ad_spend_cents(payload)
                    if cost_cents > 0:
                        bucket["cost_cents"] += cost_cents
                        totals["spend_rows"] += 1
                    if _lead_status(payload) in {"unsubscribed", "disqualified", "invalid", "spam", "optout", "opt-out"}:
                        bucket["exits_total"] += 1

                elif t == "customer":
                    totals["customer_rows"] += 1
                    bucket["customers"] += 1
                    bucket["total_customers"] += 1
                    
                    # Customer lifecycle analysis
                    customer_email = payload.get("email")
                    customer_status = _customer_status(payload)
                    created_date = _parse_dt(payload.get("created_at"), created_dt)
                    unsub_date = _parse_dt(payload.get("unsubscribed_on"), None)
                    
                    if customer_email:
                        bucket["customer_emails"].add(customer_email)
                    
                    # Calculate customer lifetime if we have dates
                    if created_date and unsub_date:
                        lifetime_days = (unsub_date - created_date).days
                        bucket["customer_lifetime_days"] += max(0, lifetime_days)
                    elif created_date:
                        # Active customer - calculate days since signup
                        days_active = (created_dt - created_date).days
                        bucket["customer_lifetime_days"] += max(0, days_active)
                    
                    # Customer status categorization
                    if customer_status in {"inactive", "cancelled", "canceled", "churned", "deleted"}:
                        bucket["churn_customers"] += 1
                        bucket["exits_total"] += 1
                    elif customer_status in {"active", "subscribed"}:
                        bucket["active_customers"] += 1
                    elif customer_status in {"reactivated", "winback"}:
                        bucket["reactivated_customers"] += 1
                    elif customer_status in {"at-risk", "declining", "low-engagement"}:
                        bucket["at_risk_customers"] += 1
                    
                    # Check if this looks like a subscription customer
                    if any(term in str(payload.get("activity_status", "")).lower() for term in ["subscription", "recurring", "monthly", "yearly"]):
                        # Estimate subscription value
                        total_spend = _to_cents(payload.get("total_spend", 0))
                        bucket["subscription_revenue_cents"] += total_spend

                elif t == "woo":
                    totals["woo_rows"] += 1
                    st = _order_status(payload)
                    order_total_cents = _to_cents(payload.get("total", 0))
                    customer_id = payload.get("customer_id")
                    customer_email = None
                    
                    # Extract customer email from billing info
                    billing_info = payload.get("billing")
                    if isinstance(billing_info, dict):
                        customer_email = billing_info.get("email")
                    elif isinstance(billing_info, str):
                        try:
                            import json
                            billing_json = json.loads(billing_info)
                            customer_email = billing_json.get("email")
                        except:
                            pass
                    
                    if st in ORDER_OK:
                        bucket["orders"] += 1
                        bucket["revenue_cents"] += order_total_cents
                        bucket["orders_value_sum_cents"] += order_total_cents
                        totals["orders_ok"] += 1
                        
                        # High-value order analysis
                        if order_total_cents >= 10000:  # $100+
                            bucket["high_value_orders"] += 1
                        
                        # Customer repeat behavior analysis
                        if customer_email:
                            bucket["customer_emails"].add(customer_email)
                            # Check if this is a repeat customer by looking for multiple orders
                            # This is simplified - in reality you'd need to track across all time
                        
                        # Subscription detection in orders
                        line_items = payload.get("line_items", "")
                        if any(term in str(line_items).lower() for term in ["subscription", "monthly", "yearly", "recurring"]):
                            bucket["subscription_revenue_cents"] += order_total_cents
                        
                    if st in ORDER_CANCEL_OR_EXIT:
                        bucket["exits_total"] += 1
                        totals["orders_cancel_or_exit"] += 1

                totals["processed"] += 1

            celery_logger.info(
                f"[{JOB_NAME}] Batch aggregated keys={len(agg)} "
                f"meta={totals['meta_rows']} customers={totals['customer_rows']} woo={totals['woo_rows']} "
                f"processed={totals['processed']} skipped_no_time={totals['skipped_no_time']} skipped_unknown={totals['skipped_unknown']}"
            )

            # --- Calculate final metrics before upserting ---
            for (user_id, day_iso, source_label), vals in agg.items():
                # Calculate average order value
                if vals["orders"] > 0:
                    vals["average_order_value_cents"] = int(vals["orders_value_sum_cents"] / vals["orders"])
                else:
                    vals["average_order_value_cents"] = 0
                
                # Convert customer_emails set to count for unique customers
                unique_customers = len(vals["customer_emails"])
                vals["unique_customers"] = unique_customers
                
                # Calculate average customer lifetime
                if unique_customers > 0:
                    vals["avg_customer_lifetime_days"] = int(vals["customer_lifetime_days"] / unique_customers)
                else:
                    vals["avg_customer_lifetime_days"] = 0
                
                # Remove the set as it can't be stored in DB
                del vals["customer_emails"]
                
                # Add derived metrics
                vals["conversion_rate_pct"] = (vals["orders"] / vals["leads"] * 100) if vals["leads"] > 0 else 0
                vals["customer_retention_pct"] = ((vals["total_customers"] - vals["churn_customers"]) / vals["total_customers"] * 100) if vals["total_customers"] > 0 else 0
            
            # --- Upsert aggregated counters ---
            upserts = 0
            try:
                for (user_id, day_iso, source_label), vals in agg.items():
                    ins = mysql_insert(SourceMetricsDaily.__table__).values(
                        user_id=user_id,
                        day=day_iso,
                        source_label=source_label,
                        leads=vals["leads"],
                        customers=vals["customers"],
                        orders=vals["orders"],
                        revenue_cents=vals["revenue_cents"],
                        cost_cents=vals["cost_cents"],
                        churn_customers=vals["churn_customers"],
                        total_customers=vals["total_customers"],
                        exits_total=vals["exits_total"],
                        new_customers=vals["new_customers"],
                        repeat_customers=vals["repeat_customers"],
                        unique_customers=vals["unique_customers"],
                        active_customers=vals["active_customers"],
                        reactivated_customers=vals["reactivated_customers"],
                        at_risk_customers=vals["at_risk_customers"],
                        subscription_revenue_cents=vals["subscription_revenue_cents"],
                        average_order_value_cents=vals["average_order_value_cents"],
                        high_value_orders=vals["high_value_orders"],
                        avg_customer_lifetime_days=vals["avg_customer_lifetime_days"],
                        customer_lifetime_days=vals["customer_lifetime_days"],
                        conversion_rate_pct=vals["conversion_rate_pct"],
                        customer_retention_pct=vals["customer_retention_pct"],
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    ondup = ins.on_duplicate_key_update(
                        leads=SourceMetricsDaily.leads + ins.inserted.leads,
                        customers=SourceMetricsDaily.customers + ins.inserted.customers,
                        orders=SourceMetricsDaily.orders + ins.inserted.orders,
                        revenue_cents=SourceMetricsDaily.revenue_cents + ins.inserted.revenue_cents,
                        cost_cents=SourceMetricsDaily.cost_cents + ins.inserted.cost_cents,
                        churn_customers=SourceMetricsDaily.churn_customers + ins.inserted.churn_customers,
                        total_customers=SourceMetricsDaily.total_customers + ins.inserted.total_customers,
                        exits_total=SourceMetricsDaily.exits_total + ins.inserted.exits_total,
                        new_customers=SourceMetricsDaily.new_customers + ins.inserted.new_customers,
                        repeat_customers=SourceMetricsDaily.repeat_customers + ins.inserted.repeat_customers,
                        unique_customers=SourceMetricsDaily.unique_customers + ins.inserted.unique_customers,
                        active_customers=SourceMetricsDaily.active_customers + ins.inserted.active_customers,
                        reactivated_customers=SourceMetricsDaily.reactivated_customers + ins.inserted.reactivated_customers,
                        at_risk_customers=SourceMetricsDaily.at_risk_customers + ins.inserted.at_risk_customers,
                        subscription_revenue_cents=SourceMetricsDaily.subscription_revenue_cents + ins.inserted.subscription_revenue_cents,
                        average_order_value_cents=ins.inserted.average_order_value_cents,  # Replace rather than add for AOV
                        high_value_orders=SourceMetricsDaily.high_value_orders + ins.inserted.high_value_orders,
                        avg_customer_lifetime_days=ins.inserted.avg_customer_lifetime_days,  # Replace rather than add for average
                        customer_lifetime_days=SourceMetricsDaily.customer_lifetime_days + ins.inserted.customer_lifetime_days,
                        conversion_rate_pct=ins.inserted.conversion_rate_pct,  # Replace rather than add for percentage
                        customer_retention_pct=ins.inserted.customer_retention_pct,  # Replace rather than add for percentage
                        updated_at=datetime.now(),
                    )
                    db.session.execute(ondup)
                    upserts += 1
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                celery_logger.exception(f"[{JOB_NAME}] Integrity error during upsert: {e}")
                raise
            except OperationalError as e:
                db.session.rollback()
                celery_logger.exception(f"[{JOB_NAME}] DB operational error during upsert: {e}")
                raise
            except Exception as e:
                db.session.rollback()
                celery_logger.exception(f"[{JOB_NAME}] Unexpected error during upsert: {e}")
                raise

            totals["agg_keys_upserted"] += upserts

            # --- Advance cursor and commit ---
            try:
                state.last_raw_id = max_id_in_batch
                state.last_run_at = datetime.now()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                celery_logger.exception(f"[{JOB_NAME}] FAILED to advance cursor to id={max_id_in_batch}: {e}")
                raise

            batch_ms = int((time.monotonic() - batch_start) * 1000)
            celery_logger.info(
                f"[{JOB_NAME}] Batch committed upserts={upserts} new_cursor={state.last_raw_id} "
                f"elapsed_ms={batch_ms}"
            )

            if len(rows) < BATCH_SIZE:
                break

        dur_ms = int((time.monotonic() - t0) * 1000)
        celery_logger.info(
            f"[{JOB_NAME}] DONE loops={totals['loops']} batches={totals['batches']} "
            f"fetched={totals['fetched']} processed={totals['processed']} "
            f"upserted_keys={totals['agg_keys_upserted']} cursor={state.last_raw_id} elapsed_ms={dur_ms}"
        )
        return {
            "status": "ok",
            "cursor": state.last_raw_id,
            "metrics": totals,
            "elapsed_ms": dur_ms,
        }

    except Exception as e:
        celery_logger.exception(f"[{JOB_NAME}] FATAL: {e}")
        raise
    finally:
        _unlock()
        celery_logger.info(f"[{JOB_NAME}] Lock released key={LOCK_KEY}")
