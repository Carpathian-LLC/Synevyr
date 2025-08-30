# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Open data sources (no auth, no CSRF)
# ------------------------------------------------------------------------------------
# Imports:
from datetime import datetime, timedelta, date
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from decimal import Decimal

# Local Imports
from app.extensions import db, csrf
from app.models.data_sources import DataSource
from app.utils.security import authorizeUser

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

@data_sources_bp.route("/analytics/source-metrics", methods=["GET"])
def analytics_by_source():
    """
    Returns aggregated metrics by source_label for the current user over a date range.
    Query params:
      since=YYYY-MM-DD (optional; default: today-90d)
      until=YYYY-MM-DD (optional; default: today)
    """
    uid = authorizeUser()

    # dates
    since_s = request.args.get("since")
    until_s = request.args.get("until")
    if not since_s or not until_s:
        d0, d1 = _default_range()
    else:
        d0, err0 = _parse_date("since", since_s)
        d1, err1 = _parse_date("until", until_s)
        if err0 or err1:
            return jsonify({"error": err0 or err1}), 400

    if d0 > d1:
        return jsonify({"error": "since must be <= until"}), 400

    # aggregate by source
    sql = text("""
        SELECT
          smd.source_label AS source_label,
          SUM(smd.leads) AS leads,
          SUM(smd.customers) AS customers,
          SUM(smd.orders) AS orders,
          SUM(smd.revenue_cents) AS revenue_cents,
          SUM(smd.cost_cents) AS cost_cents,
          SUM(smd.churn_customers) AS churn_customers,
          SUM(smd.total_customers) AS total_customers,
          SUM(smd.exits_total) AS exits_total,
          SUM(smd.new_customers) AS new_customers,
          SUM(smd.repeat_customers) AS repeat_customers,
          SUM(smd.unique_customers) AS unique_customers,
          SUM(smd.active_customers) AS active_customers,
          SUM(smd.reactivated_customers) AS reactivated_customers,
          SUM(smd.at_risk_customers) AS at_risk_customers,
          SUM(smd.subscription_revenue_cents) AS subscription_revenue_cents,
          SUM(smd.high_value_orders) AS high_value_orders,
          SUM(smd.customer_lifetime_days) AS total_customer_lifetime_days,
          CASE
            WHEN SUM(smd.cost_cents) = 0 THEN 0.0
            ELSE ((SUM(smd.revenue_cents) - SUM(smd.cost_cents)) / SUM(smd.cost_cents)) * 100.0
          END AS roi_pct,
          CASE
            WHEN SUM(smd.total_customers) = 0 THEN 0.0
            ELSE (SUM(smd.churn_customers) / SUM(smd.total_customers)) * 100.0
          END AS churn_pct,
          CASE
            WHEN SUM(smd.orders) = 0 THEN 0
            ELSE SUM(smd.revenue_cents) / SUM(smd.orders)
          END AS avg_order_value_cents,
          CASE
            WHEN SUM(smd.leads) = 0 THEN 0.0
            ELSE (SUM(smd.orders) / SUM(smd.leads)) * 100.0
          END AS conversion_rate_pct,
          CASE
            WHEN SUM(smd.unique_customers) = 0 THEN 0
            ELSE SUM(smd.customer_lifetime_days) / SUM(smd.unique_customers)
          END AS avg_customer_lifetime_days,
          CASE
            WHEN SUM(smd.total_customers) = 0 THEN 0.0
            ELSE ((SUM(smd.total_customers) - SUM(smd.churn_customers)) / SUM(smd.total_customers)) * 100.0
          END AS customer_retention_pct,
          CASE
            WHEN SUM(smd.unique_customers) = 0 THEN 0.0
            ELSE (SUM(smd.revenue_cents) / 100.0) / SUM(smd.unique_customers)
          END AS customer_ltv
        FROM source_metrics_daily smd
        WHERE smd.user_id = :uid
          AND smd.day BETWEEN :since AND :until
        GROUP BY smd.source_label
        ORDER BY smd.source_label ASC
    """)
    rows = db.session.execute(sql, {"uid": uid, "since": d0, "until": d1}).mappings().all()

    # JSON-safe items
    items = []
    for r in rows:
        items.append({
            "source_label": str(r["source_label"] or "Unknown"),
            "leads": _as_int(r["leads"]),
            "customers": _as_int(r["customers"]),
            "orders": _as_int(r["orders"]),
            "revenue_cents": _as_int(r["revenue_cents"]),
            "cost_cents": _as_int(r["cost_cents"]),
            "churn_customers": _as_int(r["churn_customers"]),
            "total_customers": _as_int(r["total_customers"]),
            "exits_total": _as_int(r["exits_total"]),
            "new_customers": _as_int(r["new_customers"]),
            "repeat_customers": _as_int(r["repeat_customers"]),
            "unique_customers": _as_int(r["unique_customers"]),
            "active_customers": _as_int(r["active_customers"]),
            "reactivated_customers": _as_int(r["reactivated_customers"]),
            "at_risk_customers": _as_int(r["at_risk_customers"]),
            "subscription_revenue_cents": _as_int(r["subscription_revenue_cents"]),
            "high_value_orders": _as_int(r["high_value_orders"]),
            "total_customer_lifetime_days": _as_int(r["total_customer_lifetime_days"]),
            "avg_customer_lifetime_days": _as_int(r["avg_customer_lifetime_days"]),
            "roi_pct": _as_float(r["roi_pct"]),
            "churn_pct": _as_float(r["churn_pct"]),
            "avg_order_value_cents": _as_int(r["avg_order_value_cents"]),
            "conversion_rate_pct": _as_float(r["conversion_rate_pct"]),
            "customer_retention_pct": _as_float(r["customer_retention_pct"]),
            "customer_ltv": _as_float(r["customer_ltv"]),
        })

    # totals (then compute pct with Decimal -> float)
    tot_sql = text("""
        SELECT
          SUM(leads) AS leads,
          SUM(customers) AS customers,
          SUM(orders) AS orders,
          SUM(revenue_cents) AS revenue_cents,
          SUM(cost_cents) AS cost_cents,
          SUM(churn_customers) AS churn_customers,
          SUM(total_customers) AS total_customers,
          SUM(exits_total) AS exits_total,
          SUM(new_customers) AS new_customers,
          SUM(repeat_customers) AS repeat_customers,
          SUM(unique_customers) AS unique_customers,
          SUM(active_customers) AS active_customers,
          SUM(reactivated_customers) AS reactivated_customers,
          SUM(at_risk_customers) AS at_risk_customers,
          SUM(subscription_revenue_cents) AS subscription_revenue_cents,
          SUM(high_value_orders) AS high_value_orders,
          SUM(customer_lifetime_days) AS total_customer_lifetime_days,
          CASE
            WHEN SUM(orders) = 0 THEN 0
            ELSE SUM(revenue_cents) / SUM(orders)
          END AS avg_order_value_cents,
          CASE
            WHEN SUM(unique_customers) = 0 THEN 0
            ELSE SUM(customer_lifetime_days) / SUM(unique_customers)
          END AS avg_customer_lifetime_days,
          CASE
            WHEN SUM(unique_customers) = 0 THEN 0.0
            ELSE (SUM(revenue_cents) / 100.0) / SUM(unique_customers)
          END AS customer_ltv
        FROM source_metrics_daily
        WHERE user_id = :uid AND day BETWEEN :since AND :until
    """)
    t = db.session.execute(tot_sql, {"uid": uid, "since": d0, "until": d1}).mappings().first() or {}

    totals = {
        "leads": _as_int(t.get("leads")),
        "customers": _as_int(t.get("customers")),
        "orders": _as_int(t.get("orders")),
        "revenue_cents": _as_int(t.get("revenue_cents")),
        "cost_cents": _as_int(t.get("cost_cents")),
        "churn_customers": _as_int(t.get("churn_customers")),
        "total_customers": _as_int(t.get("total_customers")),
        "exits_total": _as_int(t.get("exits_total")),
        "new_customers": _as_int(t.get("new_customers")),
        "repeat_customers": _as_int(t.get("repeat_customers")),
        "unique_customers": _as_int(t.get("unique_customers")),
        "active_customers": _as_int(t.get("active_customers")),
        "reactivated_customers": _as_int(t.get("reactivated_customers")),
        "at_risk_customers": _as_int(t.get("at_risk_customers")),
        "subscription_revenue_cents": _as_int(t.get("subscription_revenue_cents")),
        "high_value_orders": _as_int(t.get("high_value_orders")),
        "total_customer_lifetime_days": _as_int(t.get("total_customer_lifetime_days")),
        "avg_order_value_cents": _as_int(t.get("avg_order_value_cents")),
        "avg_customer_lifetime_days": _as_int(t.get("avg_customer_lifetime_days")),
        "customer_ltv": _as_float(t.get("customer_ltv")),
    }

    rc = _D(totals["revenue_cents"])
    cc = _D(totals["cost_cents"])
    ch = _D(totals["churn_customers"])
    tc = _D(totals["total_customers"])
    ld = _D(totals["leads"])
    od = _D(totals["orders"])
    hundred = Decimal("100")

    totals["roi_pct"] = float(Decimal(0) if cc == 0 else ((rc - cc) * hundred) / cc)
    totals["churn_pct"] = float(Decimal(0) if tc == 0 else (ch * hundred) / tc)
    totals["conversion_rate_pct"] = float(Decimal(0) if ld == 0 else (od * hundred) / ld)
    totals["customer_retention_pct"] = float(hundred - _D(totals["churn_pct"]))
    
    # High-value order percentage
    total_orders = _D(totals["orders"])
    high_val_orders = _D(totals["high_value_orders"])
    totals["high_value_order_pct"] = float(Decimal(0) if total_orders == 0 else (high_val_orders * hundred) / total_orders)
    
    # Subscription revenue percentage
    totals["subscription_revenue_pct"] = float(Decimal(0) if rc == 0 else (_D(totals["subscription_revenue_cents"]) * hundred) / rc)

    return jsonify({
        "range": {"since": d0.isoformat(), "until": d1.isoformat()},
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "items": items,
        "totals": totals,
    })