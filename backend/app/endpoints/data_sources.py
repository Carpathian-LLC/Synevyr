# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Open data sources (no auth, no CSRF)
# ------------------------------------------------------------------------------------
# Imports:
from __future__ import annotations
from datetime import datetime, timedelta, date
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from decimal import Decimal

# Local Imports
from app.extensions import db, csrf
from app.models.data_sources import DataSource
from app.models.analysis import SourceMetricsDaily
from app.models.clean_staging import CustomersClean
from app.utils.security import authorizeUser

from app.utils.logging import debug_logger
# ------------------------------------------------------------------------------------
# Vars
data_sources_bp = Blueprint("data_sources", __name__)

# ------------------------------------------------------------------------------------
# Helpers
def _parse_date(name: str, val: str | None):
    if not val:
        return None, f"{name} is required (YYYY-MM-DD)"
    try:
        return date.fromisoformat(val), None
    except Exception:
        return None, f"{name} must be YYYY-MM-DD"

def _default_range():
    today = datetime.utcnow().date()
    return (today - timedelta(days=90), today)

def _as_int(x) -> int:
    try:
        return int(x or 0)
    except Exception:
        return 0

def _as_float(x) -> float:
    try:
        return float(x or 0)
    except Exception:
        return 0.0

def _D(x) -> Decimal:
    try:
        return Decimal(str(x or 0))
    except Exception:
        return Decimal(0)

def _to_ymd(s: str) -> str:
    return datetime.fromisoformat(s).date().isoformat()

# ------------------------------------------------------------------------------------
# Endpoints

# DEPRECIATED! (These return the full JSON content.)
@data_sources_bp.route("/datasets/sources", methods=["GET"])
def list_sources():
    user_id = authorizeUser()
    # Aggregate counts and bounds cheaply. LEFT JOIN so sources with 0 rows still show.
    sql = text("""
        SELECT
          ds.id AS source_id,
          ds.name,
          ds.source_type,
          ds.base_url,
          ds.last_updated,
          COALESCE(COUNT(udr.id), 0) AS record_count,
          MIN(udr.record_time) AS earliest_record,
          MAX(udr.record_time) AS latest_record
        FROM data_sources ds
        LEFT JOIN user_dataset_raw udr
          ON udr.source_id = ds.id AND udr.user_id = ds.user_id
        WHERE ds.user_id = :user_id
        GROUP BY ds.id
        ORDER BY ds.name ASC
    """)
    rows = db.session.execute(sql, {"user_id": user_id}).mappings().all()
    return jsonify({"items": [dict(r) for r in rows]})

@data_sources_bp.route("/datasets/raw", methods=["GET"])
def get_raw():
    user_id = authorizeUser()
    # query params: source_ids=1,2,3&since=2025-01-01&until=2025-08-14&limit=1000&offset=0
    source_ids_param = request.args.get("source_ids", "").strip()
    if not source_ids_param:
        return jsonify({"error": "source_ids is required"}), 400

    try:
        source_ids = [int(s) for s in source_ids_param.split(",") if s]
    except ValueError:
        return jsonify({"error": "source_ids must be integers"}), 400

    since = request.args.get("since")
    until = request.args.get("until")
    limit = min(int(request.args.get("limit", 500)), 5000)  # hard cap
    offset = int(request.args.get("offset", 0))

    # Build WHERE clauses safely
    clauses = ["udr.user_id = :user_id", "udr.source_id IN :source_ids"]
    params = {"user_id": user_id, "source_ids": tuple(source_ids)}
    if since:
        clauses.append("(udr.record_time IS NULL OR udr.record_time >= :since)")
        params["since"] = since
    if until:
        clauses.append("(udr.record_time IS NULL OR udr.record_time <= :until)")
        params["until"] = until

    where_sql = " AND ".join(clauses)
    sql = text(f"""
        SELECT
          udr.id,
          udr.source_id,
          udr.record_time,
          udr.ingested_at,
          udr.content_type,
          udr.schema_hint,
          udr.status,
          udr.error_message,
          JSON_EXTRACT(udr.content, '$') AS content  -- pass through
        FROM user_dataset_raw udr
        WHERE {where_sql}
        ORDER BY COALESCE(udr.record_time, udr.ingested_at) ASC, udr.id ASC
        LIMIT :limit OFFSET :offset
    """)
    params.update({"limit": limit, "offset": offset})
    rows = db.session.execute(sql, params).mappings().all()

    # Optional: include a total count for pagination UI
    count_sql = text(f"SELECT COUNT(*) AS total FROM user_dataset_raw udr WHERE {where_sql}")
    total = db.session.execute(count_sql, params).scalar()

    return jsonify({
        "items": [dict(r) for r in rows],
        "pagination": {"limit": limit, "offset": offset, "total": total}
    })

@data_sources_bp.route("/data-sources", methods=["POST"])
@csrf.exempt
def create_source():
    uid = authorizeUser()
    payload = request.get_json(force=True, silent=False) or {}

    name = (payload.get("name") or "").strip()
    source_type = (payload.get("source_type") or "api").strip().lower()
    base_url = (payload.get("base_url") or "").strip()
    api_key = payload.get("api_key") or None
    config = payload.get("config") or None
    notes = payload.get("notes") or None

    if not name:
        return jsonify({"error": "name is required"}), 400
    if source_type not in ("api", "manual", "file"):
        return jsonify({"error": "invalid source_type"}), 400
    if source_type == "api" and not base_url:
        return jsonify({"error": "base_url is required for API sources"}), 400

    ds = DataSource(
        user_id=uid,
        name=name,
        source_type=source_type,
        base_url=base_url if base_url else None,
        api_key=api_key,
        config=config,
        notes=notes
    )
    db.session.add(ds)
    db.session.commit()
    return jsonify({"id": ds.id, "source": ds.to_summary()}), 201

@data_sources_bp.route("/data-sources/<int:source_id>/touch", methods=["POST"])
@csrf.exempt
def touch_source(source_id: int):
    uid = authorizeUser()
    ds = db.session.get(DataSource, source_id)
    if not ds or ds.user_id != uid:
        return jsonify({"error": "not found"}), 404
    ds.last_updated = datetime.now()
    db.session.commit()
    return jsonify({"ok": True, "source": ds.to_summary()}), 200

@data_sources_bp.route("/data-sources/<int:source_id>", methods=["DELETE"])
@csrf.exempt
def delete_source(source_id: int):
    uid = authorizeUser()
    ds = db.session.get(DataSource, source_id)
    if not ds or ds.user_id != uid:
        return jsonify({"error": "not found"}), 404
    db.session.delete(ds)
    db.session.commit()
    return jsonify({"ok": True}), 200

# NEW PRIMARY data sources endpoint! Source metrics depreciating
@data_sources_bp.route("/analytics/source-metrics", methods=["GET"])
def source_metrics():
    """
    Returns SourceMetricsResponse:
      {
        range: { since, until },
        generated_at,
        items: [
          {
            source_label, leads, customers, orders, revenue_cents, cost_cents,
            churn_customers, total_customers, exits_total,
            new_customers, repeat_customers, unique_customers,
            active_customers, reactivated_customers, at_risk_customers,
            subscription_revenue_cents, high_value_orders,
            total_customer_lifetime_days, avg_customer_lifetime_days,
            roi_pct, churn_pct, avg_order_value_cents, conversion_rate_pct,
            customer_retention_pct, customer_ltv
          }, ...
        ],
        totals: { ... same numeric fields, plus *_pct summaries ... }
      }
    """
    uid = authorizeUser()
    since = request.args.get("since")
    until = request.args.get("until")
    if not since or not until:
        return jsonify({"error": "since and until are required YYYY-MM-DD"}), 400
    since = _to_ymd(since)
    until = _to_ymd(until)

    debug_logger.info(f"[analytics] uid={uid} range={since}..{until}")

    # ---------- Additive facts from the materialized daily rollup ----------
    from sqlalchemy import func, and_
    
    facts = db.session.query(
        SourceMetricsDaily.source_label,
        func.coalesce(func.sum(SourceMetricsDaily.leads), 0).label('leads'),
        func.coalesce(func.sum(SourceMetricsDaily.cost_cents), 0).label('cost_cents'),
        func.coalesce(func.sum(SourceMetricsDaily.orders_ok), 0).label('orders'),
        func.coalesce(func.sum(SourceMetricsDaily.revenue_cents), 0).label('revenue_cents'),
        func.coalesce(func.sum(SourceMetricsDaily.orders_value_sum_cents), 0).label('orders_value_sum_cents'),
        func.coalesce(func.sum(SourceMetricsDaily.high_value_orders), 0).label('high_value_orders'),
        func.coalesce(func.sum(SourceMetricsDaily.subscription_revenue_cents), 0).label('subscription_revenue_cents'),
        func.coalesce(func.sum(SourceMetricsDaily.new_customers), 0).label('new_customers'),
        func.coalesce(func.sum(SourceMetricsDaily.churn_events), 0).label('churn_customers')
    ).filter(
        and_(
            SourceMetricsDaily.user_id == uid,
            SourceMetricsDaily.day >= since,
            SourceMetricsDaily.day <= until
        )
    ).group_by(SourceMetricsDaily.source_label).all()

    # ---------- Distinct customers present in range, per source ----------
    # Customers "present in range" = distinct emails observed in customers_clean with day in range
    cx_present_rows = db.session.query(
        CustomersClean.source_label,
        func.count(func.distinct(CustomersClean.email)).label('unique_customers')
    ).filter(
        and_(
            CustomersClean.user_id == uid,
            CustomersClean.day >= since,
            CustomersClean.day <= until,
            CustomersClean.email.isnot(None)
        )
    ).group_by(CustomersClean.source_label).all()
    cx_present = {r.source_label or "Unknown": int(r.unique_customers or 0) for r in cx_present_rows}

    # ---------- Average lifetime (days) for customers present in range ----------
    # Lifetime days ~= (until - first_seen_day) per customer; averaged per source over customers present in range.
    lifetime_rows = db.session.execute(text("""
      WITH first_seen AS (
        SELECT user_id, source_label, email, MIN(day) AS first_day
        FROM customers_clean
        WHERE user_id = :uid AND email IS NOT NULL
        GROUP BY user_id, source_label, email
      ),
      present AS (
        SELECT DISTINCT source_label, email
        FROM customers_clean
        WHERE user_id = :uid AND day BETWEEN :since AND :until AND email IS NOT NULL
      )
      SELECT f.source_label,
             AVG(DATEDIFF(:until, f.first_day) + 1) AS avg_lifetime_days,
             SUM(DATEDIFF(:until, f.first_day) + 1) AS total_lifetime_days
      FROM first_seen f
      JOIN present p ON p.source_label = f.source_label AND p.email = f.email
      GROUP BY f.source_label
    """), {"uid": uid, "since": since, "until": until}).fetchall()
    avg_lifetime = {r.source_label or "Unknown": float(r.avg_lifetime_days or 0.0) for r in lifetime_rows}
    total_lifetime = {r.source_label or "Unknown": int(r.total_lifetime_days or 0) for r in lifetime_rows}

    # ---------- Assemble items ----------
    def _safe_pct(num: float, den: float) -> float:
        return 0.0 if den <= 0 else (num / den) * 100.0

    items = []
    totals_acc = {
        "leads": 0, "customers": 0, "orders": 0,
        "revenue_cents": 0, "cost_cents": 0,
        "churn_customers": 0, "total_customers": 0,
        "exits_total": 0,
        "new_customers": 0, "repeat_customers": 0,
        "unique_customers": 0, "active_customers": 0,
        "reactivated_customers": 0, "at_risk_customers": 0,
        "subscription_revenue_cents": 0, "high_value_orders": 0,
        "total_customer_lifetime_days": 0, "avg_order_value_cents": 0,
        "avg_customer_lifetime_days": 0, "customer_ltv": 0.0,
        "roi_pct": 0.0, "churn_pct": 0.0,
        "conversion_rate_pct": 0.0, "customer_retention_pct": 0.0,
    }

    for r in facts:
        src = r.source_label or "Unknown"
        leads = int(r.leads or 0)
        orders = int(r.orders or 0)
        rev = int(r.revenue_cents or 0)
        cost = int(r.cost_cents or 0)
        o_sum = int(r.orders_value_sum_cents or 0)
        hv = int(r.high_value_orders or 0)
        sub = int(r.subscription_revenue_cents or 0)
        new_cx = int(r.new_customers or 0)
        churn = int(r.churn_customers or 0)
        uniq = int(cx_present.get(src, 0))
        avg_life = float(avg_lifetime.get(src, 0.0))
        tot_life = int(total_lifetime.get(src, 0))

        avg_aov = int(o_sum / orders) if orders > 0 else 0
        roi_pct = 0.0 if cost <= 0 else ((rev - cost) / cost) * 100.0
        conv_pct = _safe_pct(orders, leads)
        churn_pct = _safe_pct(churn, uniq)
        retention_pct = 100.0 - churn_pct if uniq > 0 else 0.0
        # Customer LTV (displayed as dollars in the UI) -> revenue / unique_customers
        customer_ltv = (rev / 100.0 / uniq) if uniq > 0 else 0.0

        items.append({
            "source_label": src,
            "leads": leads,
            "customers": uniq,  # funnel uses customers present in range
            "orders": orders,
            "revenue_cents": rev,
            "cost_cents": cost,
            "churn_customers": churn,
            "total_customers": uniq,
            "exits_total": churn,  # align with prior semantics
            "new_customers": new_cx,
            "repeat_customers": max(0, uniq - new_cx),
            "unique_customers": uniq,
            "active_customers": 0,         # optional enhancements later
            "reactivated_customers": 0,    # optional enhancements later
            "at_risk_customers": 0,        # optional enhancements later
            "subscription_revenue_cents": sub,
            "high_value_orders": hv,
            "total_customer_lifetime_days": tot_life,
            "avg_customer_lifetime_days": avg_life,
            "roi_pct": roi_pct,
            "churn_pct": churn_pct,
            "avg_order_value_cents": avg_aov,
            "conversion_rate_pct": conv_pct,
            "customer_retention_pct": retention_pct,
            "customer_ltv": customer_ltv,
        })

        # accumulate for totals
        totals_acc["leads"] += leads
        totals_acc["customers"] += uniq
        totals_acc["orders"] += orders
        totals_acc["revenue_cents"] += rev
        totals_acc["cost_cents"] += cost
        totals_acc["churn_customers"] += churn
        totals_acc["total_customers"] += uniq
        totals_acc["new_customers"] += new_cx
        totals_acc["repeat_customers"] += max(0, uniq - new_cx)
        totals_acc["unique_customers"] += uniq
        totals_acc["subscription_revenue_cents"] += sub
        totals_acc["high_value_orders"] += hv
        totals_acc["total_customer_lifetime_days"] += tot_life

    # totals-level deriveds
    orders_t = totals_acc["orders"]
    leads_t = totals_acc["leads"]
    uniq_t = totals_acc["unique_customers"]
    cost_t = totals_acc["cost_cents"]
    rev_t = totals_acc["revenue_cents"]
    o_sum_t = db.session.execute(text("""
      SELECT COALESCE(SUM(orders_value_sum_cents),0)
      FROM source_metrics_daily_v2
      WHERE user_id = :uid AND day BETWEEN :since AND :until
    """), {"uid": uid, "since": since, "until": until}).scalar() or 0

    totals_acc["avg_order_value_cents"] = int(o_sum_t / orders_t) if orders_t > 0 else 0
    totals_acc["roi_pct"] = 0.0 if cost_t <= 0 else ((rev_t - cost_t) / cost_t) * 100.0
    totals_acc["conversion_rate_pct"] = (orders_t * 100.0 / leads_t) if leads_t > 0 else 0.0
    totals_acc["churn_pct"] = (totals_acc["churn_customers"] * 100.0 / uniq_t) if uniq_t > 0 else 0.0
    totals_acc["customer_retention_pct"] = 100.0 - totals_acc["churn_pct"] if uniq_t > 0 else 0.0
    totals_acc["avg_customer_lifetime_days"] = (
        totals_acc["total_customer_lifetime_days"] / uniq_t if uniq_t > 0 else 0.0
    )
    totals_acc["customer_ltv"] = (rev_t / 100.0 / uniq_t) if uniq_t > 0 else 0.0
    totals_acc["subscription_revenue_pct"] = (
        (totals_acc["subscription_revenue_cents"] * 100.0 / rev_t) if rev_t > 0 else 0.0
    )
    totals_acc["high_value_order_pct"] = (
        (totals_acc["high_value_orders"] * 100.0 / orders_t) if orders_t > 0 else 0.0
    )

    return jsonify({
        "range": {"since": since, "until": until},
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "items": items,
        "totals": totals_acc,
    }), 200


