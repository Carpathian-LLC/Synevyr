# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# ETL: leads_clean + customers_clean + orders_clean  -> source_metrics_daily_v2
#
# Facts per (user_id, day, source_label):
#   - leads
#   - cost_cents
#   - orders_ok
#   - revenue_cents
#   - orders_value_sum_cents
#   - high_value_orders
#   - subscription_revenue_cents
#   - new_customers          (first-seen events that day)
#   - churn_events           (first time we see an "inactive" status for a customer)
#
# All of the above are ADDITIVE across days and sources. Non-additive KPIs
# (AOV, ROI, conversion, churn %, retention %, LTV, lifetime) are computed
# by the read API for the requested date range.
# ------------------------------------------------------------------------------------
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, List

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.extensions import celery, db
from app.utils.logging import debug_logger
from app.models.data_sources import AnalyticsEtlState

JOB_NAME = "load_analytics"
LOCK_KEY = "etl:source_metrics_daily"
BATCH_DAYS = 30  # process in 30-day windows when no explicit range passed

OK_ORDER_STATUSES = {"completed", "processing", "paid", "shipped", "delivered", "success", "confirmed"}
CUSTOMER_INACTIVE = {"inactive", "cancelled", "canceled", "churned", "deleted", "suspended", "deactivated"}

# ------------------------------------------------------------------------------------
# Table DDL (IF NOT EXISTS)

def _utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _bind_set(params: Dict, key: str, values: Optional[List[int]]):
    if values:
        params[key] = tuple(values)

# ------------------------------------------------------------------------------------
@celery.task(
    name="app.tasks.load_analytics.load_analytics_task",
    bind=True,
    autoretry_for=(OperationalError,),
    retry_backoff=5,
    retry_backoff_max=60,
    retry_jitter=True,
)
def load_analytics_task(self, _prev=None, **kwargs):
    """
    Build additive daily facts per (user_id, day, source_label) from clean staging tables.

    kwargs:
      force_reprocess: bool      # delete existing rows in [since, until] (and optional users)
      user_ids: Optional[List[int]]
      since: Optional['YYYY-MM-DD'] inclusive
      until: Optional['YYYY-MM-DD'] inclusive
      create_table: bool = True
    """
    task_id = self.request.id
    t0 = time.monotonic()
    debug_logger.info(f"[LOAD] START task_id={task_id} build analytics from clean staging tables kwargs={kwargs}")
    
    # Initial progress
    self.update_state(state="PROGRESS", meta={
        "step": "initializing",
        "message": "Starting analytics load",
        "progress": 0
    })
    
    force_reprocess: bool = bool(kwargs.get("force_reprocess", False))
    user_ids: Optional[List[int]] = kwargs.get("user_ids")
    since: Optional[str] = kwargs.get("since")
    until: Optional[str] = kwargs.get("until")
    
    debug_logger.info(f"[LOAD] Parameters: force_reprocess={force_reprocess} user_ids={user_ids} since={since} until={until}")

    # Lock
    debug_logger.debug(f"[LOAD] Attempting to acquire database lock: {LOCK_KEY}")
    got = db.session.execute(text("SELECT GET_LOCK(:k, 0)"), {"k": LOCK_KEY}).scalar()
    debug_logger.info(f"[LOAD] GET_LOCK {LOCK_KEY} -> {got}")
    if got != 1:
        debug_logger.warning(f"[LOAD] SKIP: lock busy {LOCK_KEY}")
        return {"skipped": True, "reason": "lock_busy"}

    def _unlock():
        try:
            db.session.execute(text("SELECT RELEASE_LOCK(:k)"), {"k": LOCK_KEY})
            db.session.commit()
            debug_logger.info(f"[smd_v2] lock released {LOCK_KEY}")
        except Exception:
            db.session.rollback()
            debug_logger.error(f"[smd_v2] FAILED release lock {LOCK_KEY}")

    try:
        # State (cursor is optional for day-rolling mode; we also support explicit ranges)
        state = (
            db.session.query(AnalyticsEtlState)
            .filter_by(job=JOB_NAME)
            .with_for_update(nowait=False)
            .first()
        )
        if not state:
            state = AnalyticsEtlState(job=JOB_NAME, last_raw_id=0)  # reuse column as "last day ordinal" if you want
            db.session.add(state)
            db.session.commit()

        # If explicit range passed, operate strictly in that range; else derive a window (last 30 days)
        if not since or not until:
            debug_logger.info(f"[LOAD] No explicit date range provided, deriving window from clean staging tables")
            # Derive min/max days seen in clean tables; then process most recent BATCH_DAYS
            row = db.session.execute(text("""
                SELECT 
                  COALESCE(MIN(d), '2000-01-01') AS min_d,
                  COALESCE(MAX(d), '2000-01-01') AS max_d
                FROM (
                  SELECT MIN(day) AS d, MAX(day) AS d2 FROM leads_clean
                  UNION ALL
                  SELECT MIN(day) AS d, MAX(day) AS d2 FROM customers_clean
                  UNION ALL
                  SELECT MIN(day) AS d, MAX(day) AS d2 FROM orders_clean
                ) t
            """)).first()
            if row and row[0] and row[1]:
                min_d, max_d = row[0], row[1]
                debug_logger.debug(f"[LOAD] Clean tables date range: min_d={min_d} max_d={max_d}")
            else:
                min_d = max_d = None
                debug_logger.warning(f"[LOAD] No data found in clean staging tables")

            since = max_d
            until = max_d
            if max_d:
                # last BATCH_DAYS window
                since = db.session.execute(text("SELECT DATE_SUB(:mx, INTERVAL :nday DAY)"),
                                           {"mx": max_d, "nday": BATCH_DAYS-1}).scalar()
            debug_logger.info(f"[LOAD] Derived processing window: since={since} until={until} (batch_days={BATCH_DAYS})")

        # Scoped delete / rebuild
        if force_reprocess:
            debug_logger.info(f"[LOAD] Force reprocess enabled - clearing existing data")
            params = {"since": since, "until": until}
            where = ["day BETWEEN :since AND :until"]
            if user_ids:
                where.append("user_id IN :uids")
                params["uids"] = tuple(user_ids)
            sql = f"DELETE FROM source_metrics_daily_v2 WHERE {' AND '.join(where)}"
            debug_logger.warning(f"[LOAD] Clearing window {since}..{until} for rebuild; users={user_ids or 'ALL'}")
            result = db.session.execute(text(sql), params)
            rows_deleted = result.rowcount if hasattr(result, 'rowcount') else 'unknown'
            db.session.commit()
            debug_logger.info(f"[LOAD] Deleted {rows_deleted} existing metric rows for reprocessing")

        # Build and merge aggregates
        debug_logger.info(f"[LOAD] Starting analytics aggregation for window {since}..{until}")
        
        self.update_state(state="PROGRESS", meta={
            "step": "aggregating",
            "message": f"Building analytics for {since} to {until}",
            "progress": 10
        })

        # 1) Leads + cost
        debug_logger.info(f"[LOAD] Step 1/4: Querying leads metrics from leads_clean table")
        params = {"since": since, "until": until}
        _bind_set(params, "uids", user_ids)
        
        leads_sql = f"""
            SELECT user_id, day, source_label,
                   COUNT(*) AS leads,
                   COALESCE(SUM(cost_cents),0) AS cost_cents
            FROM leads_clean
            WHERE day BETWEEN :since AND :until
              {"AND user_id IN :uids" if user_ids else ""}
            GROUP BY user_id, day, source_label
        """
        debug_logger.debug(f"[LOAD] Leads query params: {params}")
        
        leads_rows = db.session.execute(text(leads_sql), params).fetchall()
        debug_logger.info(f"[LOAD] Step 1/4: Found {len(leads_rows)} lead metric groups")
        
        self.update_state(state="PROGRESS", meta={
            "step": "aggregating",
            "message": f"Step 1/4: Processed {len(leads_rows)} lead groups",
            "progress": 25
        })

        # 2) Orders OK + revenue + sums
        debug_logger.info(f"[LOAD] Step 2/4: Querying order metrics from orders_clean table")
        
        orders_sql = f"""
            SELECT user_id, day, source_label,
                   COUNT(*) AS orders_ok,
                   COALESCE(SUM(total_cents),0) AS revenue_cents,
                   COALESCE(SUM(total_cents),0) AS orders_value_sum_cents,
                   COALESCE(SUM(CASE WHEN total_cents >= 10000 THEN 1 ELSE 0 END),0) AS high_value_orders,
                   COALESCE(SUM(subscription_value_cents),0) AS subscription_revenue_cents
            FROM orders_clean
            WHERE day BETWEEN :since AND :until
              {"AND user_id IN :uids" if user_ids else ""}
              AND status IN :ok
            GROUP BY user_id, day, source_label
        """
        order_params = {**params, "ok": tuple(OK_ORDER_STATUSES)}
        debug_logger.debug(f"[LOAD] Orders query params: {order_params} ok_statuses={OK_ORDER_STATUSES}")
        
        orders_rows = db.session.execute(text(orders_sql), order_params).fetchall()
        debug_logger.info(f"[LOAD] Step 2/4: Found {len(orders_rows)} order metric groups")
        
        self.update_state(state="PROGRESS", meta={
            "step": "aggregating", 
            "message": f"Step 2/4: Processed {len(orders_rows)} order groups",
            "progress": 50
        })

        # 3) New customers (first-seen day)
        debug_logger.info(f"[LOAD] Step 3/4: Querying new customer metrics from customers_clean table")
        
        new_cx_sql = f"""
            WITH first_seen AS (
              SELECT user_id, source_label, email, MIN(day) AS first_day
              FROM customers_clean
              WHERE email IS NOT NULL
                {"AND user_id IN :uids" if user_ids else ""}
              GROUP BY user_id, source_label, email
            )
            SELECT user_id, first_day AS day, source_label, COUNT(*) AS new_customers
            FROM first_seen
            WHERE first_day BETWEEN :since AND :until
            GROUP BY user_id, first_day, source_label
        """
        debug_logger.debug(f"[LOAD] New customers query params: {params}")
        
        new_cx_rows = db.session.execute(text(new_cx_sql), params).fetchall()
        debug_logger.info(f"[LOAD] Step 3/4: Found {len(new_cx_rows)} new customer metric groups")
        
        self.update_state(state="PROGRESS", meta={
            "step": "aggregating",
            "message": f"Step 3/4: Processed {len(new_cx_rows)} customer groups",
            "progress": 75
        })

        # 4) Churn events (first inactive day)
        debug_logger.info(f"[LOAD] Step 4/4: Querying churn events from customers_clean table")
        
        churn_sql = f"""
            WITH churn_first AS (
              SELECT user_id, source_label, email, MIN(day) AS churn_day
              FROM customers_clean
              WHERE email IS NOT NULL
                {"AND user_id IN :uids" if user_ids else ""}
                AND LOWER(COALESCE(activity_status,'')) IN :inactive
              GROUP BY user_id, source_label, email
            )
            SELECT user_id, churn_day AS day, source_label, COUNT(*) AS churn_events
            FROM churn_first
            WHERE churn_day BETWEEN :since AND :until
            GROUP BY user_id, churn_day, source_label
        """
        churn_params = {**params, "inactive": tuple(s.lower() for s in CUSTOMER_INACTIVE)}
        debug_logger.debug(f"[LOAD] Churn query params: {churn_params} inactive_statuses={CUSTOMER_INACTIVE}")
        
        churn_rows = db.session.execute(text(churn_sql), churn_params).fetchall()
        debug_logger.info(f"[LOAD] Step 4/4: Found {len(churn_rows)} churn metric groups")
        
        self.update_state(state="PROGRESS", meta={
            "step": "merging",
            "message": "Step 4/4: Merging all metrics",
            "progress": 90
        })

        # Merge into a single dict
        # Use tuple type directly instead of creating a type alias variable
        agg: Dict[Tuple[int, str, str], Dict[str, int]] = {}  # (user_id, day, source_label) -> metrics

        def touch(k: Tuple[int, str, str]):
            if k not in agg:
                agg[k] = {
                    "leads": 0, "cost_cents": 0,
                    "orders_ok": 0, "revenue_cents": 0, "orders_value_sum_cents": 0,
                    "high_value_orders": 0, "subscription_revenue_cents": 0,
                    "new_customers": 0, "churn_events": 0,
                }

        for r in leads_rows:
            k = (r.user_id, str(r.day), r.source_label or "Unknown")
            touch(k); a = agg[k]
            a["leads"] += int(r.leads or 0)
            a["cost_cents"] += int(r.cost_cents or 0)

        for r in orders_rows:
            k = (r.user_id, str(r.day), r.source_label or "Unknown")
            touch(k); a = agg[k]
            a["orders_ok"] += int(r.orders_ok or 0)
            a["revenue_cents"] += int(r.revenue_cents or 0)
            a["orders_value_sum_cents"] += int(r.orders_value_sum_cents or 0)
            a["high_value_orders"] += int(r.high_value_orders or 0)
            a["subscription_revenue_cents"] += int(r.subscription_revenue_cents or 0)

        for r in new_cx_rows:
            k = (r.user_id, str(r.day), r.source_label or "Unknown")
            touch(k); a = agg[k]
            a["new_customers"] += int(r.new_customers or 0)

        for r in churn_rows:
            k = (r.user_id, str(r.day), r.source_label or "Unknown")
            touch(k); a = agg[k]
            a["churn_events"] += int(r.churn_events or 0)

        # Upsert rows
        now = _utcnow_naive()
        upserts = 0
        for (user_id, day, src), v in agg.items():
            sql = text("""
              INSERT INTO source_metrics_daily
                (user_id, day, source_label,
                 leads, cost_cents,
                 orders_ok, revenue_cents, orders_value_sum_cents,
                 high_value_orders, subscription_revenue_cents,
                 new_customers, churn_events,
                 created_at, updated_at)
              VALUES
                (:user_id, :day, :src,
                 :leads, :cost_cents,
                 :orders_ok, :revenue_cents, :orders_value_sum_cents,
                 :high_value_orders, :subscription_revenue_cents,
                 :new_customers, :churn_events,
                 :now, :now)
              ON DUPLICATE KEY UPDATE
                 leads = VALUES(leads),
                 cost_cents = VALUES(cost_cents),
                 orders_ok = VALUES(orders_ok),
                 revenue_cents = VALUES(revenue_cents),
                 orders_value_sum_cents = VALUES(orders_value_sum_cents),
                 high_value_orders = VALUES(high_value_orders),
                 subscription_revenue_cents = VALUES(subscription_revenue_cents),
                 new_customers = VALUES(new_customers),
                 churn_events = VALUES(churn_events),
                 updated_at = VALUES(updated_at)
            """)
            params = {
                "user_id": user_id, "day": day, "src": src,
                **v, "now": now
            }
            db.session.execute(sql, params)
            upserts += 1

        db.session.commit()
        dt_ms = int((time.monotonic() - t0) * 1000)
        # Final summary
        end_time = time.monotonic()
        elapsed_seconds = end_time - t0
        debug_logger.info(
            f"[LOAD] COMPLETE task_id={task_id} window={since}..{until} "
            f"merged_groups={len(agg)} upserts={upserts} elapsed={elapsed_seconds:.2f}s "
            f"force_reprocess={force_reprocess} user_ids={user_ids or 'ALL'}"
        )

        # Final success progress
        self.update_state(state="SUCCESS", meta={
            "step": "complete",
            "message": f"Analytics load complete: {upserts} metrics upserted",
            "progress": 100,
            "leads_groups": len(leads_rows),
            "orders_groups": len(orders_rows),
            "customers_groups": len(new_cx_rows),
            "churn_groups": len(churn_rows),
            "total_upserts": upserts,
            "elapsed_ms": dt_ms
        })

        return {"status": "ok", "since": str(since), "until": str(until), "rows": upserts, "elapsed_ms": dt_ms}

    except Exception as e:
        db.session.rollback()
        debug_logger.exception(f"[smd_v2] FATAL: {e}")
        raise
    finally:
        _unlock()
